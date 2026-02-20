"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os
from pathlib import Path
from pydantic import BaseModel, Field
from database import ActivityRepository

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

repository = ActivityRepository()
auth_scheme = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-secret-change-me-at-least-32-chars")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.on_event("startup")
def startup_event():
    repository.initialize(seed=True)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return repository.get_activities()


class SignupRequest(BaseModel):
    email: str = Field(example="student@mergington.edu")
    password: str = Field(min_length=8, example="StrongPass123!")


class LoginRequest(BaseModel):
    email: str = Field(example="student@mergington.edu")
    password: str = Field(example="StrongPass123!")


def hash_password(password: str, salt: str | None = None) -> str:
    effective_salt = salt or secrets.token_hex(16)
    hashed_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        effective_salt.encode("utf-8"),
        100_000,
    ).hex()
    return f"{effective_salt}${hashed_password}"


def verify_password(password: str, stored_hash: str) -> bool:
    if "$" not in stored_hash:
        return False
    salt, saved_hash = stored_hash.split("$", 1)
    computed_hash = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(saved_hash, computed_hash)


def create_access_token(email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {
        "sub": email,
        "exp": expiration,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user_email(credentials: HTTPAuthorizationCredentials = Security(auth_scheme)) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from error

    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return user_email


@app.post("/auth/signup", tags=["authentication"], summary="Register a user account")
def signup(request: SignupRequest):
    """Create a user with email/password. Passwords are stored only as secure hashes."""
    password_hash = hash_password(request.password)
    try:
        repository.create_user(email=request.email, password_hash=password_hash)
    except ValueError:
        raise HTTPException(status_code=400, detail="User already exists")

    return {"message": "User registered successfully"}


@app.post("/auth/login", tags=["authentication"], summary="Login and get JWT token")
def login(request: LoginRequest):
    """Authenticate user and return a JWT bearer token for protected endpoints."""
    user = repository.get_user_by_email(request.email)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["email"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_MINUTES * 60,
    }


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, current_user_email: str = Depends(get_current_user_email)):
    """Sign up a student for an activity"""
    if current_user_email != email:
        raise HTTPException(status_code=403, detail="You can only register your own email")

    try:
        repository.signup(activity_name=activity_name, email=email)
    except KeyError:
        raise HTTPException(status_code=404, detail="Activity not found")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, current_user_email: str = Depends(get_current_user_email)):
    """Unregister a student from an activity"""
    if current_user_email != email:
        raise HTTPException(status_code=403, detail="You can only unregister your own email")

    try:
        repository.unregister(activity_name=activity_name, email=email)
    except KeyError:
        raise HTTPException(status_code=404, detail="Activity not found")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    return {"message": f"Unregistered {email} from {activity_name}"}

# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- User authentication with email/password and JWT bearer tokens

## Getting Started

1. Install dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Initialize and seed the SQLite database (creates `src/data/school.db`):

   ```
   python seed_db.py
   ```

3. Run the API:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| POST   | `/auth/signup`                                                    | Register a new user account                                         |
| POST   | `/auth/login`                                                     | Login and receive a JWT token                                       |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity                                         |

## Authentication Flow

Use this sequence in `/docs` or any API client:

1. Create user account:

   ```
   POST /auth/signup
   {
     "email": "student@mergington.edu",
     "password": "StrongPass123!"
   }
   ```

2. Login to get token:

   ```
   POST /auth/login
   {
     "email": "student@mergington.edu",
     "password": "StrongPass123!"
   }
   ```

3. Call protected endpoints with bearer token:

   ```
   Authorization: Bearer <access_token>
   ```

Protected endpoints reject missing or invalid tokens.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Data is stored in SQLite (`src/data/school.db`), so core records survive server restarts.

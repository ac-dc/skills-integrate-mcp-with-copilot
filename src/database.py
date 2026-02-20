import sqlite3
from pathlib import Path
from typing import Dict, Any


DEFAULT_ACTIVITIES: Dict[str, Dict[str, Any]] = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


class ActivityRepository:
    def __init__(self, db_path: Path | None = None):
        base_dir = Path(__file__).parent
        self.db_path = db_path or (base_dir / "data" / "school.db")

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self, seed: bool = True) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    name TEXT,
                    role TEXT,
                    password_hash TEXT
                );

                CREATE TABLE IF NOT EXISTS clubs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    manager_user_id INTEGER,
                    FOREIGN KEY (manager_user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    club_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (club_id) REFERENCES clubs(id)
                );

                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    max_participants INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS activity_participants (
                    activity_id INTEGER NOT NULL,
                    email TEXT NOT NULL,
                    PRIMARY KEY (activity_id, email),
                    FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
                );
                """
            )

            self._ensure_schema_migrations(connection)

            if seed:
                self.seed_default_data(connection)

    def _ensure_schema_migrations(self, connection: sqlite3.Connection) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(users)")
        user_columns = {row["name"] for row in cursor.fetchall()}

        if "password_hash" not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

        connection.commit()

    def seed_default_data(self, connection: sqlite3.Connection | None = None) -> None:
        if connection is None:
            with self._connect() as conn:
                self.seed_default_data(conn)
                return

        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(1) AS count FROM activities")
        count = cursor.fetchone()["count"]
        if count > 0:
            return

        for activity_name, details in DEFAULT_ACTIVITIES.items():
            cursor.execute(
                """
                INSERT INTO activities (name, description, schedule, max_participants)
                VALUES (?, ?, ?, ?)
                """,
                (
                    activity_name,
                    details["description"],
                    details["schedule"],
                    details["max_participants"],
                ),
            )
            activity_id = cursor.lastrowid
            for participant_email in details["participants"]:
                cursor.execute(
                    """
                    INSERT INTO activity_participants (activity_id, email)
                    VALUES (?, ?)
                    """,
                    (activity_id, participant_email),
                )

        connection.commit()

    def get_activities(self) -> Dict[str, Dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id, name, description, schedule, max_participants
                FROM activities
                ORDER BY name
                """
            )
            activity_rows = cursor.fetchall()

            result: Dict[str, Dict[str, Any]] = {}
            for row in activity_rows:
                cursor.execute(
                    """
                    SELECT email
                    FROM activity_participants
                    WHERE activity_id = ?
                    ORDER BY email
                    """,
                    (row["id"],),
                )
                participants = [participant_row["email"] for participant_row in cursor.fetchall()]
                result[row["name"]] = {
                    "description": row["description"],
                    "schedule": row["schedule"],
                    "max_participants": row["max_participants"],
                    "participants": participants,
                }

            return result

    def signup(self, activity_name: str, email: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM activities WHERE name = ?", (activity_name,))
            activity_row = cursor.fetchone()
            if not activity_row:
                raise KeyError("Activity not found")

            try:
                cursor.execute(
                    """
                    INSERT INTO activity_participants (activity_id, email)
                    VALUES (?, ?)
                    """,
                    (activity_row["id"], email),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("Student is already signed up") from error

            connection.commit()

    def unregister(self, activity_name: str, email: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM activities WHERE name = ?", (activity_name,))
            activity_row = cursor.fetchone()
            if not activity_row:
                raise KeyError("Activity not found")

            cursor.execute(
                """
                DELETE FROM activity_participants
                WHERE activity_id = ? AND email = ?
                """,
                (activity_row["id"], email),
            )
            if cursor.rowcount == 0:
                raise ValueError("Student is not signed up for this activity")

            connection.commit()

    def create_user(self, email: str, password_hash: str, role: str = "student") -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO users (email, role, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (email, role, password_hash),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("User already exists") from error

            connection.commit()

    def get_user_by_email(self, email: str) -> Dict[str, Any] | None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id, email, name, role, password_hash
                FROM users
                WHERE email = ?
                """,
                (email,),
            )
            user = cursor.fetchone()
            if not user:
                return None

            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "password_hash": user["password_hash"],
            }

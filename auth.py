"""
auth.py - Quote & Job Management System

Handles user authentication for the Quote & Job Management System.
Implements the login logic from IPO 1 / pseudocode (Criterion 5).

@author ***Adam Healey***
"""

import hashlib
from database import DatabaseManager
from ui.validators import validate_username

MAX_LOGIN_ATTEMPTS = 5


def hash_password(password: str) -> str:
    """Return a SHA-256 hash of the given password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthManager:
    """
    Handles login, password verification and lockout tracking.
    Uses a DatabaseManager instance to read/update the Users table.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.current_user = None  # runtime variable, not stored in DB

    def login(self, username: str, password: str) -> dict:
        """
        Attempt to log a user in.

        Returns a dict with keys:
            success (bool)
            message (str)
            role (str or None)
        """
        password_hash = hash_password(password)

        rows = self.db.run_query(
            "SELECT user_id, username, password_hash, role, is_active, login_attempts "
            "FROM Users WHERE username = ?",
            (username,)
        )

        if not rows:
            return {"success": False, "message": "Invalid username or password", "role": None}

        user_id, db_username, db_hash, role, is_active, login_attempts = rows[0]

        if not is_active:
            return {"success": False, "message": "This account has been deactivated.", "role": None}

        if login_attempts >= MAX_LOGIN_ATTEMPTS:
            return {"success": False, "message": "Account locked. Contact an admin.", "role": None}

        if db_hash != password_hash:
            new_attempts = login_attempts + 1
            self.db.run_update(
                "UPDATE Users SET login_attempts = ? WHERE user_id = ?",
                (new_attempts, user_id)
            )
            if new_attempts >= MAX_LOGIN_ATTEMPTS:
                return {"success": False, "message": "Account locked.", "role": None}
            return {"success": False, "message": "Invalid username or password", "role": None}

        # Successful login
        self.db.run_update(
            "UPDATE Users SET login_attempts = 0 WHERE user_id = ?",
            (user_id,)
        )
        self.current_user = db_username
        return {"success": True, "message": f"Welcome, {db_username}!", "role": role}

    def logout(self):
        """Clear the current logged-in user."""
        self.current_user = None

    def create_user(self, username: str, password: str, role: str) -> bool:
        """
        Create a new user account (Admin function - FR13).
        role must be 'Staff' or 'Admin'.
        """
        if role not in ("Staff", "Admin"):
            raise ValueError("Role must be 'Staff' or 'Admin'")

        is_valid, message = validate_username(username)
        if not is_valid:
            raise ValueError(message)

        existing = self.db.run_query(
            "SELECT user_id FROM Users WHERE username = ?", (username,)
        )
        if existing:
            return False  # username already taken

        self.db.run_update(
            "INSERT INTO Users (username, password_hash, role, is_active, login_attempts) "
            "VALUES (?, ?, ?, 1, 0)",
            (username, hash_password(password), role)
        )
        return True

    def reset_password(self, user_id: int, new_password: str):
        """
        Admin password reset function (Criterion 5 scope addition,
        flagged in the Possible Errors table to prevent staff lockout
        with no recovery option). Also clears login_attempts so a
        previously-locked account can log in again immediately.
        """
        self.db.run_update(
            "UPDATE Users SET password_hash = ?, login_attempts = 0 WHERE user_id = ?",
            (hash_password(new_password), user_id)
        )

    def set_active(self, user_id: int, is_active: bool):
        """Activate or deactivate a user account (FR13)."""
        self.db.run_update(
            "UPDATE Users SET is_active = ? WHERE user_id = ?",
            (1 if is_active else 0, user_id)
        )

    def update_user(self, user_id: int, username: str, role: str) -> tuple:
        """
        Update a user's username and role (FR13: edit account details).

        Returns (success: bool, message: str). Fails if the new username
        is invalid or already taken by a different account.
        """
        if role not in ("Staff", "Admin"):
            raise ValueError("Role must be 'Staff' or 'Admin'")

        is_valid, message = validate_username(username)
        if not is_valid:
            return False, message

        existing = self.db.run_query(
            "SELECT user_id FROM Users WHERE username = ? AND user_id != ?",
            (username, user_id)
        )
        if existing:
            return False, "That username is already taken"

        self.db.run_update(
            "UPDATE Users SET username = ?, role = ? WHERE user_id = ?",
            (username, role, user_id)
        )
        return True, ""

    def get_all_users(self):
        """Return all users for the Admin user management screen."""
        return self.db.run_query(
            "SELECT user_id, username, role, is_active, login_attempts FROM Users ORDER BY username"
        )


if __name__ == "__main__":
    # Quick manual test: set up DB, create an admin user, then test login
    db = DatabaseManager()
    db.connect()
    db.create_tables()

    auth = AuthManager(db)

    if auth.create_user("todd", "changeme123", "Admin"):
        print("Created initial admin user: todd")
    else:
        print("User 'todd' already exists")

    result = auth.login("todd", "changeme123")
    print(result)

    db.close()
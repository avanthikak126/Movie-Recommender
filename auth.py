"""Authentication module for Recflix.

Handles user registration, login (with brute-force lockout),
and watchlist CRUD operations. All database access uses parameterised
queries via SQLAlchemy ``text()`` to prevent SQL injection.
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from sqlalchemy import text

from database import engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50       # Must match users.username VARCHAR(50)
MAX_EMAIL_LENGTH = 255         # Must match users.email VARCHAR(255)
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72        # bcrypt silently truncates beyond this

# Pre-computed dummy hash used to prevent timing-based user enumeration.
# When a login attempt targets a non-existent username we still run
# bcrypt.checkpw against this hash so the response time is comparable
# to a real lookup.
_DUMMY_HASH = bcrypt.hashpw(b"dummy_password", bcrypt.gensalt())

# Email regex breakdown:
#   local-part : one or more of  [a-zA-Z0-9._%+-]
#   @
#   domain     : one or more labels  [a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?
#                separated by dots
#   TLD        : 2+ ASCII letters
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+-]+"
    r"@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,}$"
)

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_username(username: str) -> None:
    """Ensure *username* contains only letters, digits, and underscores.

    Also enforces length limits that match the database column width.

    Raises:
        ValueError: If the username is invalid.
    """
    if len(username) < MIN_USERNAME_LENGTH:
        raise ValueError(
            f"Username must be at least {MIN_USERNAME_LENGTH} characters long."
        )
    if len(username) > MAX_USERNAME_LENGTH:
        raise ValueError(
            f"Username must be at most {MAX_USERNAME_LENGTH} characters long."
        )
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValueError(
            "Username can only contain letters, numbers, and underscores."
        )


def validate_email(email: str) -> None:
    """Validate that *email* is a well-formed email address.

    Raises:
        ValueError: If the email format is invalid.
    """
    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(
            f"Email must be at most {MAX_EMAIL_LENGTH} characters long."
        )
    if not _EMAIL_RE.match(email):
        raise ValueError("Invalid email format.")


def validate_password(password: str) -> None:
    """Enforce password-strength requirements.

    Rules:
    * At least 8 characters
    * At most 72 *bytes* (bcrypt truncation limit)
    * Contains uppercase, lowercase, digit, and special character

    Raises:
        ValueError: If the password does not meet requirements.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            "Password is too long. Please use 72 bytes or fewer."
        )
    if not any(char.isupper() for char in password):
        raise ValueError(
            "Password must contain at least one uppercase letter."
        )
    if not any(char.islower() for char in password):
        raise ValueError(
            "Password must contain at least one lowercase letter."
        )
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError(
            "Password must contain at least one special character."
        )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def create_user(username: str, email: str, password: str) -> None:
    """Register a new user account.

    Strips leading/trailing whitespace from *username* and *email*,
    validates all inputs, checks for duplicates, and stores the password
    as a bcrypt hash.

    Raises:
        ValueError: On validation failure or duplicate username/email.
    """
    username = username.strip()
    email = email.strip().lower()

    validate_username(username)
    validate_email(email)
    validate_password(password)

    with engine.connect() as conn:
        # Split duplicate checks for a specific error message.
        existing_username = conn.execute(
            text("SELECT 1 FROM users WHERE username = :username LIMIT 1"),
            {"username": username},
        ).fetchone()
        if existing_username:
            raise ValueError("Username already taken.")

        existing_email = conn.execute(
            text("SELECT 1 FROM users WHERE email = :email LIMIT 1"),
            {"email": email},
        ).fetchone()
        if existing_email:
            raise ValueError("Email already registered.")

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        conn.execute(
            text("""
                INSERT INTO users (username, email, password)
                VALUES (:username, :email, :password)
            """),
            {
                "username": username,
                "email": email,
                "password": hashed_password,
            },
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_user(username: str, password: str) -> Optional[Any]:
    """Authenticate a user by *username* and *password*.

    Returns a row-mapping on success or ``None`` on failure.
    Raises :class:`PermissionError` when the account is locked due to
    repeated failed attempts.

    Timing-safety: when the username does not exist a dummy bcrypt check
    is still performed so that response times do not leak whether the
    account exists.

    Raises:
        PermissionError: If the account is temporarily locked.
    """
    username = username.strip()

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, password, failed_login_attempts, locked_until
                FROM users
                WHERE username = :username
            """),
            {"username": username},
        )
        user = result.mappings().fetchone()

        if user is None:
            # Constant-time: still perform a bcrypt check so that an
            # attacker cannot distinguish "no such user" from "wrong
            # password" based on response time.
            bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
            return None

        # --- Account lockout check ---
        if user["locked_until"] and user["locked_until"] > datetime.now(timezone.utc):
            raise PermissionError(
                f"Account temporarily locked. Try again after "
                f"{user['locked_until'].strftime('%H:%M:%S')}."
            )

        # --- Password verification ---
        stored_hash: str = user["password"]

        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        ):
            # Successful login — reset the failure counter.
            conn.execute(
                text("""
                    UPDATE users
                    SET failed_login_attempts = 0, locked_until = NULL
                    WHERE id = :id
                """),
                {"id": user["id"]},
            )
            conn.commit()
            return user

        # --- Password mismatch — track failed attempts ---
        failed_attempts = (user["failed_login_attempts"] or 0) + 1
        locked_until = None
        if failed_attempts >= 5:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)

        conn.execute(
            text("""
                UPDATE users
                SET failed_login_attempts = :attempts,
                    locked_until = :locked_until
                WHERE id = :id
            """),
            {
                "attempts": failed_attempts,
                "locked_until": locked_until,
                "id": user["id"],
            },
        )
        conn.commit()

        if locked_until:
            raise PermissionError(
                "Account locked due to too many failed attempts. "
                "Try again after 15 minutes."
            )

        return None


# ---------------------------------------------------------------------------
# Watchlist helpers
# ---------------------------------------------------------------------------

def add_to_watchlist(username: str, movie_id: int, movie_title: str) -> bool:
    """Add a movie to the user's watchlist.

    Returns ``True`` if the movie was added, ``False`` if it was already
    present.
    """
    with engine.begin() as conn:
        existing = conn.execute(
            text("""
                SELECT 1
                FROM watchlist
                WHERE username = :username
                AND movie_id = :movie_id
                LIMIT 1
            """),
            {"username": username, "movie_id": movie_id},
        ).fetchone()

        if existing:
            return False

        conn.execute(
            text("""
                INSERT INTO watchlist (username, movie_id, movie_title)
                VALUES (:username, :movie_id, :movie_title)
            """),
            {
                "username": username,
                "movie_id": movie_id,
                "movie_title": movie_title,
            },
        )
        return True


def get_watchlist(username: str):
    """Return all watchlist entries for *username*, newest first."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT *
                FROM watchlist
                WHERE username = :username
                ORDER BY id DESC
            """),
            {"username": username},
        )
        return result.fetchall()


def remove_from_watchlist(watchlist_id: int) -> None:
    """Delete a watchlist entry by its primary key."""
    with engine.connect() as conn:
        conn.execute(
            text("""
                DELETE FROM watchlist
                WHERE id = :id
            """),
            {"id": watchlist_id},
        )
        conn.commit()
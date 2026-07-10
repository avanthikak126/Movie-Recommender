from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import bcrypt
import os
import re
from datetime import datetime, timedelta

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)


def validate_username(username):
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValueError("Username can only contain letters, numbers, and underscores.")

def validate_email(email):
    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        raise ValueError("Invalid email format.")

def validate_password(password):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(char.isupper() for char in password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not any(char.islower() for char in password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not any(char.isdigit() for char in password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character.")

def create_user(username, email, password):
    validate_username(username)
    validate_email(email)
    validate_password(password)

    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM users WHERE username = :username OR email = :email LIMIT 1"),
            {"username": username, "email": email}
        ).fetchone()
        
        if existing:
            raise ValueError("Username or email already exists.")

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        conn.execute(
            text("""
                INSERT INTO users (username, email, password)
                VALUES (:username, :email, :password)
            """),
            {
                "username": username,
                "email": email,
                "password": hashed_password
            }
        )

        conn.commit()


def login_user(username, password):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT *
                FROM users
                WHERE username = :username
            """),
            {
                "username": username
            }
        )

        user = result.fetchone()

        if user is None:
            return None

        if user.locked_until and user.locked_until > datetime.now():
            raise PermissionError(f"Account temporarily locked. Try again after {user.locked_until.strftime('%H:%M:%S')}.")

        stored_password = user.password

        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password.encode("utf-8")
        ):
            conn.execute(text("""
                UPDATE users SET failed_login_attempts = 0, locked_until = NULL
                WHERE id = :id
            """), {"id": user.id})
            conn.commit()
            return user

        failed_attempts = (user.failed_login_attempts or 0) + 1
        locked_until = None
        if failed_attempts >= 5:
            locked_until = datetime.now() + timedelta(minutes=15)
            
        conn.execute(text("""
            UPDATE users 
            SET failed_login_attempts = :attempts, locked_until = :locked_until
            WHERE id = :id
        """), {"attempts": failed_attempts, "locked_until": locked_until, "id": user.id})
        conn.commit()

        if locked_until:
            raise PermissionError("Account locked due to too many failed attempts. Try again after 15 minutes.")

        return None


def add_to_watchlist(username, movie_id, movie_title):
    with engine.begin() as conn:
        existing = conn.execute(
            text("""
                SELECT 1
                FROM watchlist
                WHERE username = :username
                AND movie_id = :movie_id
                LIMIT 1
            """),
            {
                "username": username,
                "movie_id": movie_id
            }
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
                "movie_title": movie_title
            }
        )

        return True


def get_watchlist(username):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT *
                FROM watchlist
                WHERE username = :username
                ORDER BY id DESC
            """),
            {
                "username": username
            }
        )

        return result.fetchall()


def remove_from_watchlist(watchlist_id):
    with engine.connect() as conn:
        conn.execute(
            text("""
                DELETE FROM watchlist
                WHERE id = :id
            """),
            {
                "id": watchlist_id
            }
        )

        conn.commit()
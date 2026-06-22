from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import bcrypt
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)


def create_user(username, email, password):
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    with engine.connect() as conn:
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

        stored_password = user.password

        if bcrypt.checkpw(
            password.encode("utf-8"),
            stored_password.encode("utf-8")
        ):
            return user

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
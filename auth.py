from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import bcrypt
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@"
    f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
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
                SELECT * FROM users
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
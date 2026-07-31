from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()

def get_secret(key):
    val = os.getenv(key)
    if val:
        return val
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, Exception):
        return None

DB_USER = get_secret('DB_USER')
DB_PASSWORD = get_secret('DB_PASSWORD')
DB_HOST = get_secret('DB_HOST')
DB_PORT = get_secret('DB_PORT')
DB_NAME = get_secret('DB_NAME')

from sqlalchemy.engine import URL

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    st.error("Database credentials are not set. Please add them to your Streamlit secrets.")
else:
    try:
        url_object = URL.create(
            "postgresql+pg8000",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        )
        engine = create_engine(url_object)
        
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """))

            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP"))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS watchlist (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50),
                    movie_id INTEGER,
                    movie_title VARCHAR(255)
                )
            """))

            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_user_movie_unique
                ON watchlist (username, movie_id)
            """))

            conn.commit()
            print("Watchlist table created!")
            
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        # We define a dummy engine so imports don't fail immediately, though queries will fail.
        DATABASE_URL = "sqlite:///:memory:"
        engine = create_engine(DATABASE_URL)
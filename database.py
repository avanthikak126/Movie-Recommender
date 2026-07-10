from sqlalchemy import create_engine, text
from config import get_database_url

engine = create_engine(get_database_url())

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
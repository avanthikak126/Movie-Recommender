from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50),
            movie_id INTEGER,
            movie_title VARCHAR(255)
        )
    """))

    conn.commit()

print("Watchlist table created!")
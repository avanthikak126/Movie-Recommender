from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:recflix123@localhost:5432/recflix_db"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """))

    conn.commit()

print("Users table created!")
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:recflix123@localhost:5432/recflix_db"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(
        text("""
            INSERT INTO users (username, email, password)
            VALUES (:username, :email, :password)
        """),
        {
            "username": "avanthika",
            "email": "avanthika@example.com",
            "password": "123456"
        }
    )

    conn.commit()

print("User inserted successfully!")
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:recflix123@localhost:5432/recflix_db"

engine = create_engine(DATABASE_URL)

def create_user(username, email, password):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO users (username, email, password)
                VALUES (:username, :email, :password)
            """),
            {
                "username": username,
                "email": email,
                "password": password
            }
        )
        conn.commit()


def login_user(username, password):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT * FROM users
                WHERE username = :username
                AND password = :password
            """),
            {
                "username": username,
                "password": password
            }
        )

        return result.fetchone()
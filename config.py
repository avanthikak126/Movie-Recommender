"""
Central place to read config/secrets so the app works the same way
locally (via a .env file) and on Streamlit Community Cloud (via st.secrets).

Locally: create a .env file (see .env.example) - python-dotenv loads it.
On Streamlit Cloud: paste the same key/value pairs into
    App settings -> Secrets
as TOML, e.g.:

    DB_USER = "postgres"
    DB_PASSWORD = "..."
    DB_HOST = "your-cloud-db-host.com"
    DB_PORT = "5432"
    DB_NAME = "recflix_db"
    TMDB_API_KEY = "..."
"""

import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def get_secret(key: str, default=None):
    """Look in st.secrets first (Streamlit Cloud), fall back to
    environment variables / .env (local dev)."""
    try:
        # st.secrets raises if no secrets.toml exists at all, so guard it
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


def get_database_url() -> str:
    user = get_secret("DB_USER")
    password = get_secret("DB_PASSWORD")
    host = get_secret("DB_HOST")
    port = get_secret("DB_PORT")
    name = get_secret("DB_NAME")

    missing = [k for k, v in {
        "DB_USER": user, "DB_PASSWORD": password, "DB_HOST": host,
        "DB_PORT": port, "DB_NAME": name
    }.items() if not v]

    if missing:
        raise RuntimeError(
            f"Missing required DB config: {', '.join(missing)}. "
            "Set these in your .env file (local) or in Streamlit Cloud's "
            "Secrets manager (deployed)."
        )

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def get_tmdb_api_key():
    return get_secret("TMDB_API_KEY")
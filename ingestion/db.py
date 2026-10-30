"""Database connection. Reads connection details from .env."""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]


def get_connection():
    """Return a connection to the PostgreSQL database.

    Stops with a clear error if any setting is missing from .env.
    """
    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing {', '.join(missing)} in .env")

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
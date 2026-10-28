"""Database connection. Reads connection details from .env."""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Return a connection to the PostgreSQL database."""
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
"""Create the raw schema. Safe to run more than once."""
from db import get_connection

with get_connection() as conn:
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")

print("raw schema is ready")
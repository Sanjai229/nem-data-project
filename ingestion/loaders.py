"""Shared code for loading data into the raw schema in PostgreSQL."""
from db import get_connection


def load_to_postgres(df, table_name, source_file):
    """Load a table into raw.<table_name>, creating the table if needed.

    Every column is stored as text. Two columns are added:
    source_file (which file the row came from) and loaded_at (when it was loaded).
    Any rows already loaded from the same file are deleted first, in the same
    transaction, so running a loader again replaces data instead of duplicating it.
    """
    df = df.copy()
    df["source_file"] = source_file
    columns = list(df.columns)

    column_defs = ", ".join(f'"{c}" text' for c in columns)
    column_list = ", ".join(f'"{c}"' for c in columns)

    with get_connection() as conn:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS raw.{table_name} "
            f"({column_defs}, loaded_at timestamptz DEFAULT now())"
        )
        # Sources sometimes add new columns. Add any the table doesn't have yet.
        for c in columns:
            conn.execute(f'ALTER TABLE raw.{table_name} ADD COLUMN IF NOT EXISTS "{c}" text')

        # Remove rows already loaded from this file, so a re-run replaces them
        deleted = conn.execute(
            f"DELETE FROM raw.{table_name} WHERE source_file = %s", (source_file,)
        ).rowcount
        if deleted:
            print(f"Replaced {deleted:,} existing rows from {source_file}")

        with (
            conn.cursor() as cur,
            cur.copy(f"COPY raw.{table_name} ({column_list}) FROM STDIN") as copy,
        ):
            for row in df.itertuples(index=False, name=None):
                copy.write_row(row)

    print(f"Loaded {len(df):,} rows into raw.{table_name}")
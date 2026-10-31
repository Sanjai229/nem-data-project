"""Download AEMO dispatch data from the MMSDM monthly archive and load it into PostgreSQL."""
import csv
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from db import get_connection

BASE_URL = "https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "aemo"


def file_url(table, year, month):
    """Build the download link for one table and one month."""
    folder = f"{BASE_URL}/{year}/MMSDM_{year}_{month:02d}/MMSDM_Historical_Data_SQLLoader/DATA"
    # '#' in the file name must be written as %23 in a link
    name = f"PUBLIC_ARCHIVE%23{table}%23FILE01%23{year}{month:02d}010000.zip"
    return f"{folder}/{name}"


def download(table, year, month):
    """Download one zip into data/aemo/ and return its path. Skips if already there."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{table}_{year}{month:02d}.zip"
    if path.exists():
        print(f"Already downloaded: {path.name}")
        return path

    print(f"Downloading {path.name} ...")
    response = requests.get(file_url(table, year, month), timeout=120)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def read_mms_csv(path):
    """Read an AEMO file: use the I row as column names and the D rows as data.

    C rows (file info) are skipped. Values are kept as text, exactly as AEMO
    wrote them. Types are set later in dbt.
    """
    header = None
    rows = []
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            for row in csv.reader(io.TextIOWrapper(f, encoding="utf-8")):
                if row[0] == "I":
                    header = row
                elif row[0] == "D":
                    rows.append(row)

    df = pd.DataFrame(rows, columns=header)
    # The first 4 columns are just the row type and table name, e.g. D, DISPATCH, PRICE, 5
    df = df.iloc[:, 4:]
    # Lowercase names so they're easy to use in PostgreSQL
    df.columns = [c.lower() for c in df.columns]
    return df


def load_to_postgres(df, table_name, source_file):
    """Load a table into raw.<table_name>, creating the table if needed.

    Every AEMO column is stored as text. Two columns are added:
    source_file (which zip the row came from) and loaded_at (when it was loaded).
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
        # AEMO sometimes adds new columns. Add any the table doesn't have yet.
        for c in columns:
            conn.execute(f'ALTER TABLE raw.{table_name} ADD COLUMN IF NOT EXISTS "{c}" text')

        with conn.cursor() as cur:
            with cur.copy(f"COPY raw.{table_name} ({column_list}) FROM STDIN") as copy:
                for row in df.itertuples(index=False, name=None):
                    copy.write_row(row)

    print(f"Loaded {len(df):,} rows into raw.{table_name}")


# AEMO table name -> our raw table name
TABLES = {
    "DISPATCHPRICE": "aemo_dispatch_price",
    "DISPATCHREGIONSUM": "aemo_dispatch_regionsum",
}

# Oct 2025 to Sep 2026
MONTHS = [(2025, m) for m in range(10, 13)] + [(2026, m) for m in range(1, 10)]


def main():
    """Download and load all 12 months for both tables (24 files)."""
    for aemo_table, raw_table in TABLES.items():
        for year, month in MONTHS:
            path = download(aemo_table, year, month)
            df = read_mms_csv(path)
            load_to_postgres(df, raw_table, path.name)


if __name__ == "__main__":
    main()
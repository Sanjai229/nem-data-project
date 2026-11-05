"""Load BOM daily weather files (downloaded by hand from Climate Data Online) into PostgreSQL."""
import re
from pathlib import Path

import pandas as pd
from load_aemo import load_to_postgres

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "bom"

# BOM product code (start of the file name) -> our raw table name
PRODUCTS = {
    "IDCJAC0009": "bom_rainfall",
    "IDCJAC0010": "bom_max_temp",
    "IDCJAC0011": "bom_min_temp",
    "IDCJAC0016": "bom_solar_exposure",
}

# One station per region (see docs/scope.md)
STATIONS = {"066214", "086338", "040913", "023000", "094029"}


def clean_name(name):
    """Turn a BOM column name into a simple lowercase name.

    e.g. 'Maximum temperature (Degree C)' -> 'maximum_temperature_degree_c'
    """
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def read_bom_csv(path):
    """Read one BOM _Data.csv file. All values are kept as text."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="latin-1")
    df.columns = [clean_name(c) for c in df.columns]
    return df


def main():
    """Load every BOM _Data.csv in data/bom/ into its raw table."""
    files = sorted(DATA_DIR.glob("IDCJAC*_Data.csv"))
    if not files:
        raise RuntimeError(f"No BOM data files found in {DATA_DIR}")

    for path in files:
        product, station = path.stem.split("_")[:2]
        if product not in PRODUCTS:
            raise RuntimeError(f"Unknown BOM product {product} in {path.name}")
        if station not in STATIONS:
            raise RuntimeError(f"Unexpected station {station} in {path.name}")

        df = read_bom_csv(path)
        load_to_postgres(df, PRODUCTS[product], path.name)


if __name__ == "__main__":
    main()
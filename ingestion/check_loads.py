"""Check the raw tables after loading and write a gap log to reports/gap_log.csv.

AEMO: every region should have 288 five-minute intervals per market day, with no duplicates.
BOM: every station should have one row per day. Blank values, values that cover
more than one day, and values BOM hasn't quality-checked yet (quality N) are reported.
"""
import csv
from datetime import date
from pathlib import Path

from db import get_connection

START, END = date(2025, 10, 1), date(2026, 9, 30)
REGIONS = ["NSW1", "QLD1", "SA1", "TAS1", "VIC1"]
STATIONS = ["023000", "040913", "066214", "086338", "094029"]
AEMO_TABLES = ["aemo_dispatch_price", "aemo_dispatch_regionsum"]
BOM_TABLES = ["bom_max_temp", "bom_min_temp", "bom_rainfall", "bom_solar_exposure"]
LOG_PATH = Path(__file__).resolve().parent.parent / "reports" / "gap_log.csv"


def check_aemo(conn, table, issues):
    """Every region should have 288 intervals per market day, with no duplicates."""
    # AEMO timestamps mark the END of an interval, so subtract 5 minutes to get its market day.
    # Only INTERVENTION = 0 rows count (decision 14).
    gaps = conn.execute(
        f"""
        WITH intervals AS (
            SELECT regionid,
                   (replace(settlementdate, '/', '-')::timestamp - interval '5 minutes')::date AS market_day
            FROM raw.{table}
            WHERE intervention = '0'
        ),
        expected AS (
            SELECT r AS regionid, d::date AS market_day
            FROM unnest(%s::text[]) AS r
            CROSS JOIN generate_series(%s::timestamp, %s::timestamp, interval '1 day') AS d
        )
        SELECT e.regionid, e.market_day, COUNT(i.regionid) AS n
        FROM expected e
        LEFT JOIN intervals i USING (regionid, market_day)
        GROUP BY e.regionid, e.market_day
        HAVING COUNT(i.regionid) <> 288
        ORDER BY 1, 2
        """,
        (REGIONS, START, END),
    ).fetchall()
    for region, day, n in gaps:
        issues.append(("aemo_intervals", table, f"{region} {day}", f"{n} intervals, expected 288"))

    dups = conn.execute(
        f"""
        SELECT regionid, settlementdate, COUNT(*)
        FROM raw.{table}
        WHERE intervention = '0'
        GROUP BY 1, 2
        HAVING COUNT(*) > 1
        """
    ).fetchall()
    for region, ts, n in dups:
        issues.append(("aemo_duplicate", table, f"{region} {ts}", f"{n} rows for one interval"))

    extra = conn.execute(f"SELECT COUNT(*) FROM raw.{table} WHERE intervention <> '0'").fetchone()[0]
    print(
        f"{table}: {len(gaps)} region-days not at 288, "
        f"{len(dups)} duplicate intervals, {extra} intervention rows"
    )


def check_bom(conn, table, issues):
    """Every station should have one row per day. Report blanks, multi-day values and quality N."""
    columns = [
        r[0]
        for r in conn.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'raw' AND table_name = %s ORDER BY ordinal_position",
            (table,),
        )
    ]
    value_col = columns[5]  # the 6th column is the measurement, e.g. maximum_temperature_degree_c
    accum_col = next(
        (c for c in columns if c.startswith(("days_of_accumulation", "period_over_which"))), None
    )
    quality_sql = '"quality"' if "quality" in columns else "''"
    accum_sql = f'"{accum_col}"' if accum_col else "''"
    obs_date = 'make_date("year"::int, "month"::int, "day"::int)'

    gaps = conn.execute(
        f"""
        WITH obs AS (
            SELECT bureau_of_meteorology_station_number AS station, {obs_date} AS obs_date
            FROM raw.{table}
        ),
        expected AS (
            SELECT s AS station, d::date AS obs_date
            FROM unnest(%s::text[]) AS s
            CROSS JOIN generate_series(%s::timestamp, %s::timestamp, interval '1 day') AS d
        )
        SELECT e.station, e.obs_date, COUNT(o.station) AS n
        FROM expected e
        LEFT JOIN obs o USING (station, obs_date)
        GROUP BY e.station, e.obs_date
        HAVING COUNT(o.station) <> 1
        ORDER BY 1, 2
        """,
        (STATIONS, START, END),
    ).fetchall()
    for station, day, n in gaps:
        issues.append(("bom_days", table, f"{station} {day}", f"{n} rows, expected 1"))

    rows = conn.execute(
        f"""
        SELECT bureau_of_meteorology_station_number, {obs_date}, "{value_col}",
               {quality_sql}, {accum_sql}
        FROM raw.{table}
        WHERE {obs_date} BETWEEN %s AND %s
        ORDER BY 1, 2
        """,
        (START, END),
    ).fetchall()

    blanks = multi_day = 0
    unchecked = {}
    for station, day, value, quality, accum in rows:
        key = f"{station} {day}"
        if value == "":
            blanks += 1
            issues.append(("bom_blank", table, key, f"blank {value_col}"))
        if accum not in ("", "1"):
            multi_day += 1
            issues.append(("bom_multi_day", table, key, f"value covers {accum} days"))
        if quality == "N":
            unchecked[station] = unchecked.get(station, 0) + 1
    for station, n in sorted(unchecked.items()):
        issues.append(("bom_quality_n", table, station, f"{n} days not yet quality checked by BOM"))

    print(
        f"{table}: {len(gaps)} missing or duplicate days, {blanks} blank values, "
        f"{multi_day} multi-day values, {sum(unchecked.values())} days with quality N"
    )


def main():
    """Run all checks and write the gap log."""
    issues = []
    with get_connection() as conn:
        for table in AEMO_TABLES:
            check_aemo(conn, table, issues)
        for table in BOM_TABLES:
            check_bom(conn, table, issues)

    LOG_PATH.parent.mkdir(exist_ok=True)
    with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["check", "table", "key", "detail"])
        writer.writerows(issues)
    print(f"Wrote {len(issues)} issues to {LOG_PATH}")


if __name__ == "__main__":
    main()
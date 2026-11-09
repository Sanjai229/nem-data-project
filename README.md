# NEM Electricity Demand and Price Pipeline

An end-to-end data pipeline using public Australian energy and weather data.

**Question:** How do weather and time of day affect electricity demand and prices across the five National Electricity Market (NEM) regions?

## Status

| Milestone | What | Status |
|---|---|---|
| M1 | Scope, star schema, decision log | Done |
| M2 | Load raw data into PostgreSQL | Done |
| M3 | Clean, model and test with dbt | Next |
| M4 | Power BI dashboard and write-up | |

## Stack

Python, PostgreSQL, dbt, Power BI, Git and GitHub, Jira

## Project structure

```
nem-data-project/
├── ingestion/          Python scripts that download and load data
│   ├── db.py           Database connection (reads .env)
│   ├── setup_db.py     Creates the raw schema
│   ├── loaders.py      Shared function that loads a table into raw
│   ├── load_aemo.py    Downloads and loads AEMO price and demand
│   ├── load_bom.py     Loads BOM daily weather
│   └── check_loads.py  Checks the raw data and writes the gap log
├── dbt/                dbt project (M3)
├── dashboard/          Power BI dashboard (M4)
├── docs/               Scope, star schema and decision log
├── reports/            Gap log from the load checks
├── data/               Downloaded files (not in Git)
├── .env.example        Template for database settings
└── requirements.txt    Python packages
```

## Data

| Source | What | How often | Period |
|---|---|---|---|
| AEMO (MMSDM monthly archive) | Price ($/MWh) and demand (MW) | Every 5 minutes | 1 Oct 2025 - 30 Sep 2026 |
| BOM (Climate Data Online) | Max temp, min temp, rainfall, solar exposure | Daily | 1 Oct 2025 - 30 Sep 2026 |

**Regions and weather stations:**

| Region | BOM station | Number |
|---|---|---|
| NSW1 | Sydney (Observatory Hill) | 066214 |
| VIC1 | Melbourne (Olympic Park) | 086338 |
| QLD1 | Brisbane | 040913 |
| SA1 | Adelaide (West Terrace) | 023000 |
| TAS1 | Hobart (Ellerslie Road) | 094029 |

## Setup

You need **Python 3.10+**, **PostgreSQL** and **Git**. Commands below are for Windows PowerShell. Mac and Linux differences are noted.

**1. Get the code**

```
git clone https://github.com/Sanjai229/nem-data-project.git
cd nem-data-project
```

**2. Create and activate a virtual environment**

```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Mac or Linux: `source .venv/bin/activate`

**3. Install the packages**

```
python -m pip install -r requirements.txt
```

**4. Create the database**

```
psql -U postgres -c "CREATE DATABASE nem_data;"
```

**5. Add your database settings**

```
Copy-Item .env.example .env
```

On Mac or Linux: `cp .env.example .env`

Open `.env` and set `DB_PASSWORD` to your PostgreSQL password. `.env` is in `.gitignore`, so it never goes to GitHub.

**6. Create the raw schema**

```
python ingestion/setup_db.py
```

You should see `raw schema is ready`.

## Run the ingestion

All scripts are safe to run more than once. A re-run replaces data instead of adding duplicates.

**1. AEMO price and demand (automatic)**

```
python ingestion/load_aemo.py
```

Downloads 24 files (12 months x 2 tables) into `data/aemo/` and loads them into:
- `raw.aemo_dispatch_price` - 525,600 rows
- `raw.aemo_dispatch_regionsum` - 525,600 rows

Takes a few minutes.

**2. BOM weather (download by hand, then load)**

Climate Data Online has no simple download links, so the 20 files are downloaded by hand:

1. Go to https://www.bom.gov.au/climate/data/
2. In **Text search**, choose **Data about** and **Type of data**:
   - Temperature > Daily > Maximum temperature
   - Temperature > Daily > Minimum temperature
   - Rainfall > Daily
   - Solar exposure > Daily
3. In **Station number**, enter a station from the table above and click **Get Data**
4. Check the station name on the page that opens, then click **All years of data**
5. Repeat for all 4 types and all 5 stations (20 zips)
6. Unzip each one into `data/bom/`. You should end up with 20 `_Data.csv` files and 20 `_Note.txt` files

Don't open the CSVs in Excel and save them. Excel changes station numbers like 066214 to 66214.

Then load them:

```
python ingestion/load_bom.py
```

This loads into `raw.bom_max_temp`, `raw.bom_min_temp`, `raw.bom_rainfall` and `raw.bom_solar_exposure`. Each file holds every year the station has data. dbt filters to the project's date range.

**3. Check the data**

```
python ingestion/check_loads.py
```

Checks that every region has 288 AEMO intervals per day with no duplicates, and every BOM station has one row per day. Blank values, multi-day values and unchecked (quality N) days are written to `reports/gap_log.csv`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `pip` is blocked by Windows | Use `python -m pip` instead of `pip` |
| `Missing DB_PASSWORD in .env` | Check `.env` exists in the main folder and every `DB_` line has a value |
| `password authentication failed` | The password in `.env` doesn't match your PostgreSQL password |
| `No BOM data files found` | The BOM `_Data.csv` files must be directly inside `data/bom/`, not in subfolders |

## Code quality

```
python -m ruff check ingestion
```

## Documentation

- [Scope](docs/scope.md) - question, data, what's in and out
- [Star schema](docs/star_schema.md) - table design
- [Decision log](docs/decision_log.md) - key choices, reasons and trade-offs
- [Gap log](reports/gap_log.csv) - results of the load checks

## Data credits

- Electricity data: Australian Energy Market Operator (AEMO), NEMweb
- Weather data: Bureau of Meteorology, Climate Data Online. © Commonwealth of Australia
# NEM Electricity Demand and Price Pipeline

An end-to-end data engineering project on Australian electricity data.

**Question:** How do weather and time of day drive electricity demand and prices across the NEM regions?

**Stack:** Python, PostgreSQL, dbt Core, Power BI, GitHub Actions, Azure

**Status:** In progress - Milestone 1 (setup and design)

## Structure
- ingestion/ - Python scripts that pull AEMO and BOM data into PostgreSQL
- dbt/ - SQL transformations and data tests
- dashboard/ - Power BI dashboard
- docs/ - scope, schema design and decision log

## Data
- AEMO NEMweb 5-minute price and demand data (source: AEMO)
- Bureau of Meteorology daily weather observations
# Star Schema Design

## Why a star schema

Raw AEMO and BOM files repeat the same details on every row, such as the region name. A star schema stores the numbers once, in fact tables, and the details once, in small dimension tables. Keys link them together.

This keeps the data small, avoids mistakes, and gives Power BI the shape it works best with.

## Diagram

```mermaid
erDiagram
    dim_region ||--o{ fact_price_demand : ""
    dim_date   ||--o{ fact_price_demand : ""
    dim_time   ||--o{ fact_price_demand : ""
    dim_region ||--o{ fact_daily_weather : ""
    dim_date   ||--o{ fact_daily_weather : ""

    fact_price_demand {
        int region_key FK
        int date_key FK
        int time_key FK
        timestamp interval_end_aest
        numeric price_aud_mwh
        numeric demand_mw
    }

    fact_daily_weather {
        int region_key FK
        int date_key FK
        numeric max_temp_c
        numeric min_temp_c
        numeric solar_exposure_mj_m2
        numeric rainfall_mm
    }

    dim_region {
        int region_key PK
        text region_code
        text state
        text capital_city
        text bom_station_name
        text bom_station_id
    }

    dim_date {
        int date_key PK
        date full_date
        text day_name
        boolean is_weekend
        int month
        text month_name
        text season
        int year
    }

    dim_time {
        int time_key PK
        time interval_start
        time interval_end
        int hour
        text time_band
    }
```

## Grain - what one row means

| Table | One row means | Expected rows |
|---|---|---|
| fact_price_demand | One region, one 5-minute interval | about 525,600 (288 x 5 x 365) |
| fact_daily_weather | One region, one day | about 1,825 (5 x 365) |
| dim_region | One NEM region | 5 |
| dim_date | One calendar day | 365 |
| dim_time | One 5-minute slot in a day | 288 |

## Fact tables

### fact_price_demand

The main table. Price and demand for each region, every 5 minutes.

**Key:** one row per (region_key, date_key, time_key).

| Column | Meaning |
|---|---|
| region_key | Links to dim_region |
| date_key | Links to dim_date, e.g. 20260115 |
| time_key | Links to dim_time, e.g. 1430 for the 14:30 to 14:35 slot |
| interval_end_aest | The original AEMO timestamp, kept for checking |
| price_aud_mwh | Dispatch price in $/MWh. Negative and very high prices are kept |
| demand_mw | Regional demand in MW, from AEMO's TOTALDEMAND field. This excludes rooftop solar (see below) |

### fact_daily_weather

Daily weather for each region, from one BOM station per region.

**Key:** one row per (region_key, date_key).

| Column | Meaning |
|---|---|
| region_key | Links to dim_region |
| date_key | Links to dim_date |
| max_temp_c | Daily maximum temperature (°C) |
| min_temp_c | Daily minimum temperature (°C) |
| solar_exposure_mj_m2 | Daily solar exposure (MJ/m²) |
| rainfall_mm | Daily rainfall (mm) |

## Dimension tables

### dim_region

| Column | Example |
|---|---|
| region_key | 1 |
| region_code | NSW1 |
| state | New South Wales |
| capital_city | Sydney |
| bom_station_name | Sydney (Observatory Hill) |
| bom_station_id | 066062 |

### dim_date

| Column | Example |
|---|---|
| date_key | 20260115 |
| full_date | 2026-01-15 |
| day_name | Thursday |
| is_weekend | false |
| month / month_name | 1 / January |
| season | Summer (Dec to Feb, Southern Hemisphere) |
| year | 2026 |

### dim_time

| Column | Example |
|---|---|
| time_key | 1430 |
| interval_start | 14:30 |
| interval_end | 14:35 |
| hour | 14 |
| time_band | Afternoon (Night 00-06, Morning 06-12, Afternoon 12-18, Evening 18-24) |

## Which demand measure

I use TOTALDEMAND from AEMO's 5-minute dispatch data. This is AEMO's standard regional demand. It only counts power supplied through the grid, so it does not include rooftop solar.

This matters for my results. On sunny days, rooftop solar covers part of household use, so grid demand drops around midday. A link between high solar exposure and lower demand will partly reflect rooftop solar, not people using less power. I will keep this in mind when I interpret the weather and demand results.

## How weather fits in

Prices are every 5 minutes. Weather is once a day. These are two different grains.

I chose to keep weather in its own daily fact table, rather than copying it onto every 5-minute row or shrinking prices down to daily.

- Copying weather onto every row would repeat each value 288 times and mix two grains in one table
- Shrinking prices to daily would lose time of day, which my first question needs
- A separate daily table keeps each table at one grain

Both fact tables share dim_region and dim_date. This lets them be compared on the same region and day.

## Daily roll-up model

To compare price and demand with weather, I will build the daily roll-up as its own dbt model, not as a calculation in Power BI. This keeps the logic in one place, makes it testable, and lets it be reused.

**mart_daily_region** - one row per region per day:

| Column | Meaning |
|---|---|
| region_key, date_key | Links to dim_region and dim_date |
| peak_demand_mw | Highest 5-minute demand that day |
| avg_price_aud_mwh | Average price that day |
| max_price_aud_mwh | Highest price that day |
| max_temp_c, min_temp_c, solar_exposure_mj_m2, rainfall_mm | That day's weather |

## Planned dbt tests

| Test | What it checks | Why |
|---|---|---|
| Unique (region_key, date_key, time_key) on fact_price_demand | No duplicate intervals | Duplicates would double count price and demand |
| 288 rows per region per day | No missing intervals | Detects and reports gaps, a success criterion in scope.md |
| Unique (region_key, date_key) on fact_daily_weather | One weather row per region per day | Stops weather being counted twice |
| Keys are not null and match a dimension row | Every fact row links to a real region, date and time | Rows with broken links would drop out of Power BI charts |

## Time rules

- **AEST all year.** AEMO uses market time (AEST, UTC+10) with no daylight saving. I use market days for all five regions. For SA and the daylight saving months, this is slightly different from the local calendar day. I accept this small offset and note it here
- **AEMO timestamps mark the end of an interval.** A row stamped 14:35 covers 14:30 to 14:35. I key each row by its interval start, so the row stamped 00:00 belongs to 23:55 on the previous day. This gives each day exactly 288 slots
- **BOM's 9am window.** BOM's daily values do not all cover midnight to midnight. Maximum temperature covers the 24 hours from 9am, so it mostly lines up with the same day's peak demand. Minimum temperature and rainfall cover the 24 hours to 9am, so they mostly describe the night and day before. I keep BOM's dates as published and will check whether this matters in M2

## What this design does not include

- Public holidays (could be added to dim_date later)
- Fuel mix, interconnectors and forecasts (out of scope, see scope.md)
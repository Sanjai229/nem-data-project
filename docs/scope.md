# Project Scope

## Business question
How do weather and time of day drive electricity demand and prices across the National Electricity Market (NEM)?

## Who it's for
An analyst at an energy retailer or network business who needs to know when demand and prices peak, and how much of that is driven by weather.

## Sub-questions
1. How does demand change across the day in each region, and does the pattern shift between seasons?
2. How much do temperature, sunshine and rain change daily peak demand?
3. When do price spikes happen, and how often do they line up with extreme temperatures?

## Data sources

| Source | What | Grain | How it's collected |
|---|---|---|---|
| AEMO NEMweb | Regional price ($/MWh) and demand (MW) | Every 5 minutes, per region | Python script, automated |
| BOM Climate Data Online | Daily max temperature, min temperature, solar exposure and rainfall | Daily, one station per region | Manual CSV download |

AEMO data is public. Source: Australian Energy Market Operator (AEMO).

### Regions and weather stations

| NEM region | Weather station | BOM station number |
|---|---|---|
| NSW1 | Sydney (Observatory Hill) | 066062 |
| VIC1 | Melbourne (Olympic Park) | 086338 |
| QLD1 | Brisbane | 040913 |
| SA1 | Adelaide (West Terrace) | 023000 |
| TAS1 | Hobart (Ellerslie Road) | 094029 |

## In scope
- Five NEM regions: NSW, VIC, QLD, SA and TAS
- 12 months of data: 1 October 2025 to 30 September 2026
- About 525,000 price and demand rows (288 intervals a day x 5 regions x 365 days)
- Automated AEMO ingestion, a star schema in PostgreSQL, dbt transformations and tests, and a Power BI dashboard

## Out of scope
- Generation by fuel type and the renewables mix (kept separate from my university coursework)
- Forecasting or machine learning
- Retail electricity bills - the wholesale price is not what households pay
- Interconnector flows between regions
- Real-time streaming - data is loaded in batches

## Assumptions and known challenges
- **Time zones.** NEM data uses Australian Eastern Standard Time all year, with no daylight saving. BOM daily data follows the local day. The two need lining up carefully.
- **Grain mismatch.** Prices come every 5 minutes, weather once a day. How I handle this is explained in the star schema design and the decision log.
- **One station per region.** A capital-city station doesn't represent a whole state's weather, but the capitals account for most of the demand.
- **Extreme prices.** Prices can spike to thousands of dollars per MWh, or go below zero. These are real market events, not errors, so they are kept.
- **BOM's daily window.** BOM's daily values run 9am to 9am. Rainfall covers the 24 hours to 9 am, and the max and min temperatures also use 9 am windows. This needs handling when joining weather to price data by date.

## Success criteria
- 12 months of data loaded for all five regions, with any missing intervals detected by dbt tests and reported
- dbt tests pass: no duplicates, gaps flagged, prices and demand within sensible ranges
- The dashboard answers all three sub-questions
- Anyone can rebuild the project by following the README

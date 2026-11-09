# Decision Log

These are the main choices I made in this project, why I made them, and what I gave up.

| # | Decision |
|---|---|
| 1 | Kanban instead of Scrum |
| 2 | dbt 1.12 instead of the 1.13 beta |
| 3 | No Docker for now |
| 4 | All five regions, 12 months |
| 5 | One weather station per region |
| 6 | Added rainfall |
| 7 | Kept negative and very high prices |
| 8 | Using TOTALDEMAND for demand |
| 9 | Weather in its own daily table |
| 10 | Labelling each interval by its start time |
| 11 | Using AEST for all regions |
| 12 | Keeping BOM dates as they are |
| 13 | Daily summary in dbt, not Power BI |
| 14 | Using AEMO's monthly archive for the data |
| 15 | Two PostgreSQL packages: psycopg and psycopg2-binary |
| 16 | Raw AEMO tables keep every column, as text |
| 17 | Blank AEMO values stay as '' in raw, turned into NULL in dbt |
| 18 | Re-runs replace data by source_file |
| 19 | BOM files downloaded by hand, raw keeps all years |
| 20 | Sydney weather station changed to 066214 |
| 21 | Load checks report problems instead of stopping |
| 22 | Keep quality N weather data and show the flag |

---

## 1. Kanban instead of Scrum

**What I chose:** A Kanban board with To Do, In Progress, In Review and Done.

**Why:** I'm working alone and the milestones already have set dates. Scrum sprints would just add extra planning. The In Review column makes it easy to hand work over for review.

**Downside:** There's no sprint to check my pace, so I use the milestone dates for that.

## 2. dbt 1.12 instead of the 1.13 beta

**What I chose:** dbt Core 1.12 with dbt-postgres.

**Why:** pip installed the 1.13 beta at first. A beta might have bugs, and most help online is for stable versions, so I went back to 1.12.

**Downside:** I don't get any new features from 1.13 until it's released properly.

## 3. No Docker for now

**What I chose:** I installed PostgreSQL, Python and dbt straight on my laptop.

**Why:** It's simpler for a one-person project, and I'd rather spend the time on the data. I can add Docker later if I need it.

**Downside:** It's harder for someone else to set up the same way. The README and requirements.txt help with that.

## 4. All five regions, 12 months

**What I chose:** NSW1, VIC1, QLD1, SA1 and TAS1, from 1 Oct 2025 to 30 Sep 2026.

**Why:** Having all five lets me compare states. Twelve months covers every season, which I need for my questions.

**Downside:** That's about 525,600 rows of price data, so I need a real database, not Excel.

## 5. One weather station per region

**What I chose:** One BOM station per region, in or near the capital city.

**Why:** Most people, and most demand, are in the capital, so its weather is a fair guide. It also keeps things simple.

**Downside:** Big states like QLD and NSW have very different weather in different places, so one station is only a rough guide.

## 6. Added rainfall

**What I chose:** Rainfall, along with max temp, min temp and solar exposure.

**Why:** I don't expect it to matter much, because rainy days are already cooler and cloudier. But it's easy to add and worth testing.

**Downside:** Rain overlaps with temperature and sunshine, so it might be hard to see its own effect.

## 7. Kept negative and very high prices

**What I chose:** I keep every price, even negative ones and big spikes.

**Why:** These are real. Prices go negative when there's too much solar, and spike in heatwaves. One of my questions is about spikes, so I can't remove them.

**Downside:** A few extreme prices can pull averages up or down. Where that matters, I'll use medians or caps in charts and say so.

## 8. Using TOTALDEMAND for demand

**What I chose:** TOTALDEMAND from AEMO's 5-minute data.

**Why:** It's AEMO's standard demand number and it comes in the same files as price.

**Downside:** It doesn't include rooftop solar. On sunny days, demand looks lower around midday because people's roofs are covering some of their power. I need to remember this when I look at the weather results. Behrouz agreed that noting this is enough for this project. Adding AEMO's rooftop solar estimates (30-minute data) is a stretch goal after M4.

## 9. Weather in its own daily table

**What I chose:** A separate daily weather table that shares the region and date tables with the price table.

**Other options I looked at:**
- Copying the daily weather onto every 5-minute row
- Turning prices into daily numbers

**Why:** Weather is daily but prices are every 5 minutes. Keeping them apart means each table has one grain. I don't repeat the same temperature 288 times, nobody can add up temperatures by mistake, and I keep the 5-minute detail for time-of-day questions.

**Downside:** Comparing price and weather takes an extra step. Decision 13 covers that.

## 10. Labelling each interval by its start time

**What I chose:** Each 5-minute row is labelled by when it starts, not AEMO's timestamp.

**Why:** AEMO's timestamp is the end of the interval. That means the 00:00 row is really the last slot of the day before. Using the start time gives every day exactly 288 slots, 00:00 to 23:55.

**Downside:** My label is different from AEMO's. I keep AEMO's original timestamp too, so I can check rows against the source.

## 11. Using AEST for all regions

**What I chose:** One clock for every region - AEMO's market time (AEST, no daylight saving).

**Why:** All AEMO data is in AEST, so using it everywhere keeps things consistent.

**Downside:** For SA, and during daylight saving, a "day" is a bit different from the local day. It's a small gap and I'm okay with it.

## 12. Keeping BOM dates as they are

**What I chose:** I use BOM's dates without moving them.

**Why:** BOM's max temperature is measured from 9am, so it mostly matches that day's peak demand. That's the main thing I'm comparing.

**Downside:** Min temperature and rainfall are measured to 9am, so they mostly describe the night and day before. I'll check if this matters in M2.

## 13. Daily summary in dbt, not Power BI

**What I chose:** A dbt model called mart_daily_region, with daily peak demand, average and max price, and that day's weather.

**Why:** If the maths is in dbt, I can test it and use it again. If it's inside Power BI, it's hidden and can't be tested. Behrouz suggested this in the NEM-11 review.

**Downside:** It's one more model to build and test in M3.

## 14. Using AEMO's monthly archive for the data

**What I chose:** The MMSDM monthly archive on NEMweb.

**Where:** `nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/<year>/MMSDM_<year>_<month>/MMSDM_Historical_Data_SQLLoader/DATA/`

**Files I need:** For each month, `DISPATCHPRICE` (price) and `DISPATCHREGIONSUM` (demand). Each file has all five regions. That's 24 files for 12 months.

**Other options I looked at:**
- Reports/Current - only keeps the last few days
- Reports/Archive/DispatchIS_Reports - one zip per day, but only keeps about 12 months. When I checked on 25 Oct 2026, the oldest file was 15 Oct 2025, so 1 to 14 Oct 2025 was already gone, and more drops off every day

**Why:** The monthly archive has all 12 months, it doesn't delete old data, and it's 24 files instead of 365.

**Downside:** Monthly files come out about two weeks after the month ends, so they don't work for very recent data. That's fine for my fixed date range.

**Things to remember for M2 and M3:**
- File names have `#` in them, which must be written as `%23` in a download link
- Keep only rows where INTERVENTION = 0 (the normal market run). Rows with INTERVENTION = 1 come from AEMO's intervention runs and would duplicate intervals. This keeps each region-day at 288 rows

## 15. Two PostgreSQL packages: psycopg and psycopg2-binary

**What I chose:** Keep both in requirements.txt.

**Why:** My Python scripts use psycopg (version 3), the current version. dbt-postgres installs psycopg2-binary (version 2) for its own use. Each tool needs its own package, so both stay.

**Downside:** It can look like a mistake in requirements.txt. This note explains it.

## 16. Raw AEMO tables keep every column, as text

**What I chose:** Load every column from the AEMO files into the raw tables, stored as text. I only drop the first four label columns (like D, DISPATCH, PRICE, 5), lowercase the column names, and add source_file and loaded_at.

**Why:** Raw should be a true copy of the source. Keeping every column means I don't need to download again if I need another column later. Keeping values as text means nothing gets changed or lost on the way in. dbt sets the proper types in M3.

**Downside:** The raw tables are wider than I need, and every value needs converting in dbt.

## 17. Blank AEMO values stay as '' in raw, turned into NULL in dbt

**What I chose:** Keep blank values as empty text ('') in the raw tables. In dbt, use NULLIF(column, '') before turning text into numbers or dates.

**Other option I looked at:** Turning '' into NULL while loading.

**Why:** It keeps raw a true copy of the source (decision 16). All changes to the data happen in one place, dbt, where they can be tested.

**Downside:** Every column that gets converted in dbt needs NULLIF. Without it, the conversion fails on blank values. My mentor flagged this in the NEM-15 review.

## 18. Re-runs replace data by source_file

**What I chose:** Before loading a file, delete any rows with the same source_file, then load it. Both happen in one transaction.

**Other option I looked at:** A separate table listing which files have been loaded, and skipping those.

**Why:** It uses the source_file column I already have, so there's no extra table. A re-run also picks up any fixes, because the data is replaced rather than skipped. If the load fails, the delete is undone too, so a month is never left empty. My mentor suggested this in the NEM-15 review.

**Downside:** A re-run reloads every file, which takes a few minutes. That's fine for 24 files.

## 19. BOM files downloaded by hand, raw keeps all years

**What I chose:** Download the 20 BOM files by hand from Climate Data Online (5 stations x max temp, min temp, rainfall, solar exposure), unzip them into data/bom/, then load the _Data.csv files with a script. Raw tables keep every year in each file, not just my date range.

**Why:** Climate Data Online doesn't offer simple download links, and it's only 20 files, once. The loading part is still a script, reuses load_to_postgres, and is safe to re-run. Keeping all years follows my rule that raw is a true copy of the source (decision 16). dbt filters to Oct 2025 to Sep 2026.

**Downside:** Anyone setting this up has to download the files by hand. The README will list the exact steps. The CSVs shouldn't be opened and saved in Excel, as it changes station numbers like 066214 to 66214.

## 20. Sydney weather station changed to 066214

**What I chose:** Use station 066214 Sydney (Observatory Hill) instead of 066062.

**Why:** When I downloaded the BOM files, 066062 showed "Year site closed: 31 Aug 2020", with no data after that. BOM's list of open stations showed 066214 at the same site, still open, with temperature and rainfall up to November 2026. So Sydney stays at Observatory Hill, just under a new number.

**Downside:** None for my date range. Anyone comparing with older studies should know the number changed in 2020.

**Also found:** All five stations have 365 days for Oct 2025 to Sep 2026, but a few max temp values are blank: Sydney 31 Mar 2026, Melbourne 11 Mar 2026, Brisbane 20 Jan 2026, Hobart 22 Oct 2025 and 31 Aug 2026. They stay blank in raw and will be reported in the gap checks.

## 21. Load checks report problems instead of stopping

**What I chose:** A separate script, check_loads.py, runs after loading. It checks every region-day has 288 AEMO intervals with no duplicates, and every BOM station has one row per day. It also reports blank values, values covering more than one day, and the number of days BOM hasn't quality-checked yet (quality N). Everything goes into reports/gap_log.csv.

**Why:** Gaps in source data are real and can't be fixed by reloading, so the checks report them rather than stopping the pipeline. The log shows exactly what is missing, which helps decide how to handle it in dbt. Quality N is counted per station rather than listed day by day, because recent months have hundreds of unchecked days.

**Results (Nov 2026):** AEMO is complete, with 288 intervals on every region-day and no duplicates. BOM has no missing days, but 11 blank values (5 max temp, 1 min temp, 5 rainfall) and no multi-day values. About a third of temperature days and over half of rainfall days are quality N. Solar files have no quality column.

**Downside:** The checks run on demand, not automatically after each load. They can be added to the pipeline later.

## 22. Keep quality N weather data and show the flag

**What I chose:** Keep BOM values marked quality N (not yet checked by BOM). Carry the quality flag through into the dbt models, and state the share of unchecked days in the dashboard and write-up.

**Why:** Quality N is normal for recent data, and it's the only data available for my date range. About 35% of temperature days and 57% of rainfall days are quality N. Dropping them would remove over a third of the weather data. Keeping the flag means anyone can filter or check results with only quality-checked days. My mentor suggested this in the NEM-18 review.

**Downside:** BOM may still adjust some of these values after checking. Results using weather should note this.
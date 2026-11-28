-- One row per region per day: weather from that region's BOM station.
-- Grain: region_key + date_key. Quality flags are kept (decision 22).

select
    r.region_key,
    to_char(w.obs_date, 'YYYYMMDD')::int as date_key,
    w.max_temp_c,
    w.max_temp_quality,
    w.min_temp_c,
    w.min_temp_quality,
    w.rainfall_mm,
    w.rainfall_period_days,
    w.rainfall_quality,
    w.solar_exposure_mj_m2
from {{ ref('stg_bom__daily_weather') }} as w
inner join {{ ref('dim_region') }} as r
    on r.bom_station_id = w.station_id
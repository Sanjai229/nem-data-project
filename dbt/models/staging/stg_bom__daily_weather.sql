with max_temp as (

    select
        bureau_of_meteorology_station_number as station_id,
        make_date("year"::int, "month"::int, "day"::int) as obs_date,
        nullif(maximum_temperature_degree_c, '')::numeric as max_temp_c,
        nullif(quality, '') as max_temp_quality
    from {{ source('raw', 'bom_max_temp') }}

),

min_temp as (

    select
        bureau_of_meteorology_station_number as station_id,
        make_date("year"::int, "month"::int, "day"::int) as obs_date,
        nullif(minimum_temperature_degree_c, '')::numeric as min_temp_c,
        nullif(quality, '') as min_temp_quality
    from {{ source('raw', 'bom_min_temp') }}

),

rainfall as (

    select
        bureau_of_meteorology_station_number as station_id,
        make_date("year"::int, "month"::int, "day"::int) as obs_date,
        nullif(rainfall_amount_millimetres, '')::numeric as rainfall_mm,
        nullif(period_over_which_rainfall_was_measured_days, '')::int as rainfall_period_days,
        nullif(quality, '') as rainfall_quality
    from {{ source('raw', 'bom_rainfall') }}

),

solar as (

    select
        bureau_of_meteorology_station_number as station_id,
        make_date("year"::int, "month"::int, "day"::int) as obs_date,
        -- Solar files have no quality column. Change this name if Step 2 showed a different one.
        nullif(daily_global_solar_exposure_mj_m_m, '')::numeric as solar_exposure_mj_m2
    from {{ source('raw', 'bom_solar_exposure') }}

),

-- Every station-day that appears in any of the four tables
station_days as (

    select station_id, obs_date from max_temp
    union
    select station_id, obs_date from min_temp
    union
    select station_id, obs_date from rainfall
    union
    select station_id, obs_date from solar

)

select
    d.station_id,
    d.obs_date,
    mx.max_temp_c,
    mx.max_temp_quality,
    mn.min_temp_c,
    mn.min_temp_quality,
    r.rainfall_mm,
    r.rainfall_period_days,
    r.rainfall_quality,
    s.solar_exposure_mj_m2
from station_days as d
left join max_temp as mx on mx.station_id = d.station_id and mx.obs_date = d.obs_date
left join min_temp as mn on mn.station_id = d.station_id and mn.obs_date = d.obs_date
left join rainfall as r on r.station_id = d.station_id and r.obs_date = d.obs_date
left join solar as s on s.station_id = d.station_id and s.obs_date = d.obs_date
where d.obs_date between '2025-10-01' and '2026-09-30'
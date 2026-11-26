with days as (

    select d::date as full_date
    from generate_series('2025-10-01'::timestamp, '2026-09-30'::timestamp, interval '1 day') as d

)

select
    to_char(full_date, 'YYYYMMDD')::int as date_key,
    full_date,
    trim(to_char(full_date, 'Day')) as day_name,
    extract(isodow from full_date)::int as day_of_week,
    extract(isodow from full_date) in (6, 7) as is_weekend,
    extract(month from full_date)::int as month,
    trim(to_char(full_date, 'Month')) as month_name,
    case
        when extract(month from full_date) in (12, 1, 2) then 'Summer'
        when extract(month from full_date) in (3, 4, 5) then 'Autumn'
        when extract(month from full_date) in (6, 7, 8) then 'Winter'
        else 'Spring'
    end as season,
    extract(year from full_date)::int as year
from days
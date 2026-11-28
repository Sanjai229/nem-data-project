-- One row per region per 5-minute interval: price and demand.
-- Grain: region_code + date_key + time_key (docs/star_schema.md).
-- A full outer join keeps an interval even if price or demand is ever missing for it.

with price as (

    select * from {{ ref('stg_aemo__price') }}

),

demand as (

    select * from {{ ref('stg_aemo__demand') }}

),

joined as (

    select
        coalesce(p.region_code, d.region_code) as region_code,
        coalesce(p.interval_start_aest, d.interval_start_aest) as interval_start_aest,
        coalesce(p.interval_end_aest, d.interval_end_aest) as interval_end_aest,
        p.price_aud_mwh,
        d.demand_mw
    from price as p
    full outer join demand as d
        on p.region_code = d.region_code
        and p.interval_start_aest = d.interval_start_aest

)

select
    region_code,
    to_char(interval_start_aest, 'YYYYMMDD')::int as date_key,
    to_char(interval_start_aest, 'HH24MI')::int as time_key,
    interval_start_aest,
    interval_end_aest,
    price_aud_mwh,
    demand_mw
from joined
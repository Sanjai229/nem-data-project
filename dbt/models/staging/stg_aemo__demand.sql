with source as (

    select * from {{ source('raw', 'aemo_dispatch_regionsum') }}

),

cleaned as (

    select
        regionid as region_code,
        replace(settlementdate, '/', '-')::timestamp - interval '5 minutes' as interval_start_aest,
        replace(settlementdate, '/', '-')::timestamp as interval_end_aest,
        nullif(totaldemand, '')::numeric as demand_mw,
        source_file
    from source
    where intervention = '0'

)

select
    region_code,
    interval_start_aest,
    interval_end_aest,
    interval_start_aest::date as market_date,
    demand_mw,
    source_file
from cleaned
where interval_start_aest >= '2025-10-01'
  and interval_start_aest < '2026-10-01'
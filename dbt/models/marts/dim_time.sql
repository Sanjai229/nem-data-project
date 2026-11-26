with slots as (

    select generate_series(0, 287) as slot_number

)

select
    ((slot_number * 5 / 60) * 100 + (slot_number * 5 % 60)) as time_key,
    time '00:00' + slot_number * interval '5 minutes' as interval_start,
    time '00:00' + (slot_number + 1) * interval '5 minutes' as interval_end,
    slot_number * 5 / 60 as hour,
    case
        when slot_number * 5 / 60 < 6 then 'Night'
        when slot_number * 5 / 60 < 12 then 'Morning'
        when slot_number * 5 / 60 < 18 then 'Afternoon'
        else 'Evening'
    end as time_band
from slots
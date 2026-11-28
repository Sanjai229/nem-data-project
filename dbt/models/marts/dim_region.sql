-- One row per NEM region, with the BOM weather station used for it.
-- region_code (e.g. NSW1) is the key. Stations from docs/scope.md.
-- Sydney uses 066214, as 066062 closed in 2020 (decision 20).

select *
from (
    values
        ('NSW1', 'New South Wales', 'Sydney', 'Sydney (Observatory Hill)', '066214'),
        ('VIC1', 'Victoria', 'Melbourne', 'Melbourne (Olympic Park)', '086338'),
        ('QLD1', 'Queensland', 'Brisbane', 'Brisbane', '040913'),
        ('SA1', 'South Australia', 'Adelaide', 'Adelaide (West Terrace)', '023000'),
        ('TAS1', 'Tasmania', 'Hobart', 'Hobart (Ellerslie Road)', '094029')
) as regions (region_code, state, capital_city, bom_station_name, bom_station_id)
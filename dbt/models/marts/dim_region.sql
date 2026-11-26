select *
from (
    values
        (1, 'NSW1', 'New South Wales', 'Sydney', 'Sydney (Observatory Hill)', '066214'),
        (2, 'VIC1', 'Victoria', 'Melbourne', 'Melbourne (Olympic Park)', '086338'),
        (3, 'QLD1', 'Queensland', 'Brisbane', 'Brisbane', '040913'),
        (4, 'SA1', 'South Australia', 'Adelaide', 'Adelaide (West Terrace)', '023000'),
        (5, 'TAS1', 'Tasmania', 'Hobart', 'Hobart (Ellerslie Road)', '094029')
) as regions (region_key, region_code, state, capital_city, bom_station_name, bom_station_id)
-- Cleaned store list, with the catchment radius from dbt_project.yml.

select
    store_id,
    store_name,
    latitude,
    longitude,
    location,
    {{ var('catchment_radius_m') }} as catchment_radius_m
from {{ source('raw', 'stores') }}

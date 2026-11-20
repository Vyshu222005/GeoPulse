-- Every ping that happened inside a store's catchment area (the circle around the store).
--
-- This is the spatial join: ST_DWITHIN checks if the ping is within the catchment radius
-- (500 m, set in dbt_project.yml) of the store. A ping inside two overlapping circles
-- appears once for each store.

select
    s.store_id,
    p.device_id,
    p.ping_ts,
    p.ping_date,
    p.ping_hour,
    p.is_weekend,
    round(st_distance(p.location, s.location)) as distance_m
from {{ ref('stg_pings') }} as p
inner join {{ ref('stg_stores') }} as s
    on st_dwithin(p.location, s.location, s.catchment_radius_m)

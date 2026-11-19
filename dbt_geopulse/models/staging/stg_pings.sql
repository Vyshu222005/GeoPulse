{{ config(materialized="table") }}

-- Cleaned pings.
-- The raw table can hold the same ping twice (same device, same second). Keep only the
-- first row of each pair, so that ping counts are not inflated.
-- Also adds the date, hour and weekday, which the footfall models need.

select
    device_id,
    ping_ts,
    latitude,
    longitude,
    location,
    to_date(ping_ts)               as ping_date,
    hour(ping_ts)                  as ping_hour,
    dayofweek(ping_ts) in (0, 6)   as is_weekend
from {{ source('raw', 'pings') }}
where location is not null
qualify row_number() over (
    partition by device_id, ping_ts
    order by latitude, longitude
) = 1

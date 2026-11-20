-- Footfall traffic: for every store, day and hour, how many different devices (unique
-- visitors) were inside the catchment area, and how many pings they sent.
-- One row for each store + date + hour.
--
-- Every combination is present, also when nobody visited: those rows have 0 visitors.
-- Without the zero rows, averages would only count the hours that had visitors and would
-- look too high for quiet hours.

with dates as (
    select distinct ping_date, is_weekend
    from {{ ref('stg_pings') }}
),

hours as (
    select seq4() as ping_hour
    from table(generator(rowcount => 24))
),

grid as (
    select
        s.store_id,
        s.store_name,
        d.ping_date,
        h.ping_hour,
        d.is_weekend
    from {{ ref('stg_stores') }} as s
    cross join dates as d
    cross join hours as h
),

visits as (
    select
        store_id,
        ping_date,
        ping_hour,
        count(distinct device_id) as unique_visitors,
        count(*)                  as pings
    from {{ ref('int_store_visits') }}
    group by store_id, ping_date, ping_hour
)

select
    g.store_id,
    g.store_name,
    g.ping_date,
    g.ping_hour,
    g.is_weekend,
    coalesce(v.unique_visitors, 0) as unique_visitors,
    coalesce(v.pings, 0)           as pings
from grid as g
left join visits as v
    on  v.store_id  = g.store_id
    and v.ping_date = g.ping_date
    and v.ping_hour = g.ping_hour

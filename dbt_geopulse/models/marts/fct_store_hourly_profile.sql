-- The typical day for each store: average unique visitors for each hour of the day,
-- shown separately for weekdays and weekends. This is the morning against evening view
-- that the dashboard time slider uses.

select
    store_id,
    store_name,
    is_weekend,
    ping_hour,
    round(avg(unique_visitors), 1)  as avg_unique_visitors,
    max(unique_visitors)            as peak_unique_visitors,
    count(*)                        as days_counted
from {{ ref('fct_store_hourly_visits') }}
group by store_id, store_name, is_weekend, ping_hour

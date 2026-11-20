-- Fails if a store has two rows for the same date and hour.
select store_id, ping_date, ping_hour, count(*) as copies
from {{ ref('fct_store_hourly_visits') }}
group by store_id, ping_date, ping_hour
having count(*) > 1

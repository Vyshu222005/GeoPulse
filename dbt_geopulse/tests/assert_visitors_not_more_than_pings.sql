-- Fails if a row has more unique visitors than pings (impossible).
select *
from {{ ref('fct_store_hourly_visits') }}
where unique_visitors > pings

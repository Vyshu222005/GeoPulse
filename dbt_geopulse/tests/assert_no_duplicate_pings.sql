-- This test fails if any device has two pings in the same second after cleaning.
select device_id, ping_ts, count(*) as copies
from {{ ref('stg_pings') }}
group by device_id, ping_ts
having count(*) > 1

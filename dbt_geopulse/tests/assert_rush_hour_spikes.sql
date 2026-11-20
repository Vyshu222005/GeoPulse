-- Data integrity check for the mid-project review: across all stores, the morning (8:00)
-- and evening (18:00) hours must have clearly more unique visitors than midday (13:00).
-- Fails (returns a row) if either peak is less than 1.5 times midday.
with hourly as (
    select
        avg(case when ping_hour = 8  then avg_unique_visitors end) as morning,
        avg(case when ping_hour = 18 then avg_unique_visitors end) as evening,
        avg(case when ping_hour = 13 then avg_unique_visitors end) as midday
    from {{ ref('fct_store_hourly_profile') }}
    where is_weekend = false
)
select *
from hourly
where morning < 1.5 * midday
   or evening < 1.5 * midday

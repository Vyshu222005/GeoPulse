-- Fails if fct_store_hourly_visits does not have exactly one row for every
-- store x date x hour (stores * dates * 24).
with expected as (
    select
        (select count(*) from {{ ref('stg_stores') }})
        * (select count(distinct ping_date) from {{ ref('stg_pings') }})
        * 24 as expected_rows
),
actual as (
    select count(*) as actual_rows from {{ ref('fct_store_hourly_visits') }}
)
select *
from expected, actual
where expected_rows <> actual_rows

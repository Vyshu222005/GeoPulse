-- Fails if any ping in a catchment is farther from the store than the radius.
select v.*
from {{ ref('int_store_visits') }} as v
inner join {{ ref('stg_stores') }} as s on s.store_id = v.store_id
where v.distance_m > s.catchment_radius_m + 1

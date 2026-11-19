# Week 1 Data Quality Report

Data: 7,628,295 synthetic GPS pings from 20,000 devices (2 to 8 Nov 2026) and 10 store
locations in Bengaluru, loaded into Snowflake (`GEOPULSE.RAW.PINGS` and `GEOPULSE.RAW.STORES`).

Checks are in `snowflake/03_check_load.sql` and `snowflake/04_data_quality.sql`.

## Results

| Check | Result | Status |
|---|---|---|
| Rows loaded (pings) | 7,628,295, same as the CSV file | Pass |
| Rows loaded (stores) | 10 | Pass |
| Unique devices | 20,000 | Pass |
| Pings without a GEOGRAPHY point | 0 | Pass |
| GEOGRAPHY point differs from latitude/longitude | 0 | Pass |
| Pings outside the city | 0 | Pass |
| Pings per device (min / average / max) | 250 / 381 / 521 | Pass |
| Duplicate pings (same device, same second) | 4,967 (about 0.07%) | Issue, see below |
| Rush hour peaks | morning 578,182 and evening 611,878 pings per hour, against 305,203 at midday (about 2x) | Pass |
| Peak hours | 8 am: 818,525 pings. 6 pm: 763,677 pings | Pass |

## Pings within 500 m of each store

| Store | Pings | Unique devices |
|---|---|---|
| S01 MG Road | 43,853 | 1,786 |
| S02 Indiranagar | 40,288 | 1,701 |
| S03 Koramangala | 39,904 | 1,641 |
| S04 Whitefield | 21,469 | 901 |
| S05 Electronic City | 19,828 | 874 |
| S06 Jayanagar | 25,160 | 718 |
| S07 Malleshwaram | 23,730 | 558 |
| S08 HSR Layout | 26,456 | 1,016 |
| S09 Hebbal | 14,376 | 445 |
| S10 Marathahalli | 18,305 | 1,144 |

These numbers match the Python distance check made before loading (Day 2). Two stores
(S06 and S07) differ by 1 ping, because Snowflake measures distance on a slightly different
Earth model than the Python formula. This is not a problem.

## Issue found: duplicate pings

4,967 pairs of rows have the same device and the same timestamp. The timestamps in the
data are only accurate to one second, so a device that gets two random ping times in the
same second creates a duplicate. This is 0.07% of the data.

Why it matters: duplicates would slightly raise the ping counts. They do not change the
unique visitor counts, which are the main footfall metric.

Plan: keep the raw table as it is (raw data should not be changed) and remove duplicates in
the dbt staging model in Week 2 with `ROW_NUMBER() OVER (PARTITION BY device_id, ping_ts)`.

Resolved (19 Nov): the dbt model `stg_pings` removes them. The raw table has 7,628,295 rows
and `stg_pings` has 7,623,252, so 5,043 duplicate rows were removed (some groups had more
than two copies). The dbt test `assert_no_duplicate_pings` passes.

## Other notes

- Weekdays and weekends have the same number of pings per day (about 1.09 million). This is
  a simplification in the data generator. Real data would have fewer commute pings on
  weekends.
- Everything in the data is synthetic. No real device data is used.

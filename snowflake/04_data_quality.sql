-- GeoPulse: Day 6 data quality checks on the loaded data
-- Run with:  python snowflake/run_sql.py snowflake/04_data_quality.sql

USE WAREHOUSE GEOPULSE_WH;
USE DATABASE GEOPULSE;
USE SCHEMA RAW;

-- 1. Duplicate pings (same device, same second). Should be a very small number.
SELECT COUNT(*) AS DUPLICATE_PING_ROWS
FROM (
    SELECT DEVICE_ID, PING_TS, COUNT(*) AS C
    FROM PINGS
    GROUP BY DEVICE_ID, PING_TS
    HAVING COUNT(*) > 1
);

-- 2. Pings outside the Bengaluru area (should be 0)
SELECT COUNT(*) AS PINGS_OUTSIDE_CITY
FROM PINGS
WHERE LATITUDE  NOT BETWEEN 12.70 AND 13.20
   OR LONGITUDE NOT BETWEEN 77.40 AND 77.90;

-- 3. Pings per device: smallest, average and biggest (no device should have 0 or be huge)
SELECT MIN(C) AS MIN_PINGS, ROUND(AVG(C)) AS AVG_PINGS, MAX(C) AS MAX_PINGS
FROM (SELECT DEVICE_ID, COUNT(*) AS C FROM PINGS GROUP BY DEVICE_ID);

-- 4. Weekday and weekend: weekends have no commute, so fewer rush hour pings.
--    DAYOFWEEK: 0 = Sunday, 6 = Saturday.
SELECT IFF(DAYOFWEEK(PING_TS) IN (0, 6), 'weekend', 'weekday') AS DAY_TYPE,
       COUNT(*) AS PINGS,
       COUNT(DISTINCT TO_DATE(PING_TS)) AS DAYS,
       ROUND(COUNT(*) / COUNT(DISTINCT TO_DATE(PING_TS))) AS PINGS_PER_DAY
FROM PINGS
GROUP BY DAY_TYPE
ORDER BY DAY_TYPE;

-- 5. Rush hour against normal hours (the peaks should be about 2x midday)
SELECT CASE WHEN HOUR(PING_TS) BETWEEN 7 AND 9   THEN '1 morning (7-9)'
            WHEN HOUR(PING_TS) BETWEEN 11 AND 15 THEN '2 midday (11-15)'
            WHEN HOUR(PING_TS) BETWEEN 17 AND 19 THEN '3 evening (17-19)'
       END AS PERIOD,
       ROUND(COUNT(*) / COUNT(DISTINCT HOUR(PING_TS))) AS AVG_PINGS_PER_HOUR
FROM PINGS
WHERE HOUR(PING_TS) BETWEEN 7 AND 9
   OR HOUR(PING_TS) BETWEEN 11 AND 15
   OR HOUR(PING_TS) BETWEEN 17 AND 19
GROUP BY PERIOD
ORDER BY PERIOD;

-- 6. Pings and unique devices within 500 m of each of the 10 stores.
--    (The same numbers from the Python check on Day 2 should appear.)
SELECT S.STORE_ID,
       S.STORE_NAME,
       COUNT(*)                    AS PINGS_WITHIN_500M,
       COUNT(DISTINCT P.DEVICE_ID) AS DEVICES_WITHIN_500M
FROM STORES S
JOIN PINGS P
  ON ST_DWITHIN(P.LOCATION, S.LOCATION, 500)
GROUP BY S.STORE_ID, S.STORE_NAME
ORDER BY S.STORE_ID;

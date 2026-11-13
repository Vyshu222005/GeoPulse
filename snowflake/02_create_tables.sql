-- GeoPulse: Day 4 create the raw tables with GEOGRAPHY columns
-- Run after 01_setup.sql, with:  python snowflake/run_sql.py snowflake/02_create_tables.sql

USE WAREHOUSE GEOPULSE_WH;
USE DATABASE GEOPULSE;
USE SCHEMA RAW;

-- 1. GPS pings from mobile devices.
--    latitude and longitude are kept as plain numbers, and LOCATION is a real
--    GEOGRAPHY point built from them when the data is loaded (Day 5).
CREATE OR REPLACE TABLE PINGS (
    DEVICE_ID   VARCHAR(20)   NOT NULL,   -- anonymized device id
    LATITUDE    FLOAT         NOT NULL,
    LONGITUDE   FLOAT         NOT NULL,
    PING_TS     TIMESTAMP_NTZ NOT NULL,   -- time of the ping
    LOCATION    GEOGRAPHY                 -- ST_MAKEPOINT(longitude, latitude)
)
COMMENT = 'Raw anonymized mobile GPS pings';

-- 2. Store locations, each with a point and its 500 m catchment area.
CREATE OR REPLACE TABLE STORES (
    STORE_ID    VARCHAR(10)   NOT NULL,
    STORE_NAME  VARCHAR(100)  NOT NULL,
    LATITUDE    FLOAT         NOT NULL,
    LONGITUDE   FLOAT         NOT NULL,
    LOCATION    GEOGRAPHY,                -- the store point
    CATCHMENT   GEOGRAPHY                 -- 500 m circle around the store
)
COMMENT = 'Store locations and catchment areas';

-- 3. Quick test: add one fake ping near Store A (MG Road), check it, then remove it.
INSERT INTO PINGS (DEVICE_ID, LATITUDE, LONGITUDE, PING_TS, LOCATION)
SELECT 'TEST', 12.9760, 77.6075, '2026-11-13 08:30:00',
       ST_MAKEPOINT(77.6075, 12.9760);

-- distance in meters between the test ping and Store A (should be about 78 m)
SELECT DEVICE_ID,
       ROUND(ST_DISTANCE(LOCATION, ST_MAKEPOINT(77.6070, 12.9755))) AS METERS_FROM_STORE_A,
       ST_DWITHIN(LOCATION, ST_MAKEPOINT(77.6070, 12.9755), 500)     AS INSIDE_500M
FROM PINGS
WHERE DEVICE_ID = 'TEST';

DELETE FROM PINGS WHERE DEVICE_ID = 'TEST';

-- 4. Check that both tables exist
SHOW TABLES IN SCHEMA GEOPULSE.RAW;
DESCRIBE TABLE PINGS;

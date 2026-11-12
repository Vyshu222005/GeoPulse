-- GeoPulse: Day 3 Snowflake setup
-- Run this once in a Snowflake worksheet (use the ACCOUNTADMIN role).

USE ROLE ACCOUNTADMIN;

-- 1. Small warehouse (compute). It stops by itself after 60 seconds so credits are saved.
CREATE WAREHOUSE IF NOT EXISTS GEOPULSE_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Compute for the GeoPulse project';

-- 2. Database for the project
CREATE DATABASE IF NOT EXISTS GEOPULSE
    COMMENT = 'GeoPulse hyper-local retail mobility analytics';

-- 3. Schemas, one for each stage of the pipeline
CREATE SCHEMA IF NOT EXISTS GEOPULSE.RAW
    COMMENT = 'Raw GPS pings and store locations, loaded as they are';
CREATE SCHEMA IF NOT EXISTS GEOPULSE.STAGING
    COMMENT = 'Cleaned data (dbt staging models)';
CREATE SCHEMA IF NOT EXISTS GEOPULSE.MARTS
    COMMENT = 'Final footfall and cannibalization tables for the dashboard';

-- 4. Use them
USE WAREHOUSE GEOPULSE_WH;
USE DATABASE GEOPULSE;

-- 5. Check that everything was created
SHOW WAREHOUSES LIKE 'GEOPULSE_WH';
SHOW SCHEMAS IN DATABASE GEOPULSE;

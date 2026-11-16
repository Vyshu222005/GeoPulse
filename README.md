# GeoPulse: Hyper-Local Retail Mobility Analytics

Retailers often guess where to open new stores. GeoPulse uses mobile GPS pings to show how
foot traffic really moves through a city by hour, and to estimate how much a new store would
cannibalize an existing one.

## Pipeline

| Stage | Tool |
|---|---|
| Data synthesis | Python (NumPy, pandas) |
| Data lakehouse | Snowflake (GEOGRAPHY type) |
| Spatial joins | Apache Sedona / PySpark |
| Modeling | dbt |
| Dashboard | Kepler.gl + React |
| Orchestration | Apache Airflow |

## Progress

- [x] Week 1: data synthesis and Snowflake loading (in progress)
- [ ] Week 2: spatial joins and dbt models, then mid-project review
- [ ] Week 3: cannibalization logic and map UI
- [ ] Week 4: Airflow automation, 3D H3 map, final review

## Week 1: generate mock GPS pings

```
pip install -r requirements.txt
python data_generation/generate_pings.py --devices 5000 --days 7
```

Output (not committed, see .gitignore):
- `data/pings.csv`: device_id, lat, lon, ts
- `data/stores.csv`: store_id, name, lat, lon (see `stores/stores.csv`)

### Check the data

```
python data_generation/validate_pings.py
```

This checks for missing values, pings outside the city, rush hour peaks (morning and
evening) and how many pings fall within 500 m of each store.

Test result with 20,000 devices over 7 days: 7.6 million pings, 0 missing values, 0 pings
outside the city. Morning and evening have about 2x the pings of midday.

## Week 1: Snowflake setup

1. Create a free Snowflake trial account.
2. Open a worksheet and run `snowflake/01_setup.sql`. It creates the warehouse
   `GEOPULSE_WH`, the database `GEOPULSE` and the schemas `RAW`, `STAGING` and `MARTS`.
3. Copy `.env.example` to `.env` and fill in your own account, user and password.
   The `.env` file is ignored by git, so the password is never pushed.
4. Test the connection:
   ```
   pip install -r requirements.txt
   python snowflake/test_connection.py
   ```

## Week 1: create the tables

`snowflake/02_create_tables.sql` creates two tables in `GEOPULSE.RAW`:

| Table | What it holds |
|---|---|
| `PINGS` | device_id, latitude, longitude, ping_ts and a `LOCATION` GEOGRAPHY point |
| `STORES` | store details, a `LOCATION` point and a 500 m `CATCHMENT` GEOGRAPHY area |

Run it (or any other SQL file) with:
```
python snowflake/run_sql.py snowflake/02_create_tables.sql
```
The file also inserts one test ping, checks it is about 78 m from Store A using
`ST_DISTANCE` and `ST_DWITHIN`, and then deletes it.

## Week 1: load the data into Snowflake

```
python snowflake/load_data.py
python snowflake/run_sql.py snowflake/03_check_load.sql
```

`load_data.py` uploads the CSV files to a Snowflake stage with `PUT`, then uses `COPY INTO`
to fill the `PINGS` and `STORES` tables. The `LOCATION` GEOGRAPHY column is built with
`ST_MAKEPOINT(longitude, latitude)` while loading. The tables are emptied first, so the
script can be run again without duplicates.

`03_check_load.sql` checks the row counts, missing points, that the GEOGRAPHY points match
the latitude and longitude, the rush hour peaks, and pings within 500 m of Store A.

The store `CATCHMENT` column stays empty for now. The 500 m circles are made in Week 2.

## Week 1: data quality checks

```
python snowflake/run_sql.py snowflake/04_data_quality.sql
```

Checks for duplicate pings, pings outside the city, pings per device, weekday against
weekend, rush hour against midday, and pings and devices within 500 m of all 10 stores.
The results are in `docs/week1_data_quality_report.md`. One issue was found (4,967
duplicate pings, 0.07%). It will be removed in the dbt staging model in Week 2.

## Week 2: PySpark and Apache Sedona

Spatial joins on millions of pings use Spark with Sedona. Setup guide:
`docs/week2_spark_setup.md` (install Java 17, then `pip install -r requirements-spark.txt`).

```
python spark/test_sedona.py
```

All data is synthetic. No real device data is used.

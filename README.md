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

## Week 2: 500 m catchment circles

A catchment area is the zone around a store where visitors are counted.

```
python spatial/make_catchments.py      # draws a 500 m circle around each store
python spatial/check_catchments.py     # counts pings inside each circle
python snowflake/load_catchments.py    # saves the circles in STORES.CATCHMENT
```

Each circle is a 64-point polygon saved as WKT in `stores/store_catchments.csv`. All corners
are exactly 500 m from the store. The pings inside the polygons are about 0.1% fewer than
the plain 500 m distance counts, because a 64-sided shape is slightly smaller than a perfect
circle.

## Week 2: spatial join with Sedona

```
python spark/spatial_join.py
```

Reads all pings, builds a point for each (`ST_Point`), and joins them to the store circles
with `ST_Contains`. It prints which join Spark used (it must be a spatial join and not a slow
nested loop), the pings and unique devices for each store, and saves
`data/pings_in_catchments.csv`. Use `--limit` and `--driver-memory` for the memory test.

Status: the code is written. Running it needs Java 17 and, on Windows, `winutils.exe`
(see `docs/week2_spark_setup.md`). The same polygon counts were already checked in plain
Python with `spatial/check_catchments.py`, which the Spark result should match.

## Week 2: dbt (data modeling inside Snowflake)

dbt runs in its own virtual environment so it does not clash with the other scripts:

```
python -m venv .venv-dbt
.venv-dbt\Scripts\pip install dbt-core==1.12.7 dbt-snowflake==1.12.5 "python-dotenv[cli]"
```

Run it from the `dbt_geopulse` folder. `dotenv` loads the login from the `.env` file:

```
cd dbt_geopulse
..\.venv-dbt\Scripts\dotenv -f ..\.env run -- ..\.venv-dbt\Scripts\dbt debug --profiles-dir .
..\.venv-dbt\Scripts\dotenv -f ..\.env run -- ..\.venv-dbt\Scripts\dbt run --profiles-dir .
..\.venv-dbt\Scripts\dotenv -f ..\.env run -- ..\.venv-dbt\Scripts\dbt test --profiles-dir .
```

| Model | Schema | What it does |
|---|---|---|
| `stg_pings` | STAGING (table) | Removes duplicate pings, adds date, hour and weekend columns |
| `stg_stores` | STAGING (view) | Store list with the 500 m catchment radius |

Result: `stg_pings` has 7,623,252 rows, which is 5,043 duplicate rows removed from the
7,628,295 raw rows. All 11 dbt tests pass (not null, unique, hours 0 to 23, no duplicates).

### Footfall models

| Model | Schema | What it does |
|---|---|---|
| `int_store_visits` | STAGING (table) | The spatial join: every ping within 500 m of a store (273,196 rows), using `ST_DWITHIN` |
| `fct_store_hourly_visits` | MARTS (table) | Unique visitors and pings for each store, date and hour. 1,680 rows (10 stores x 7 days x 24 hours), with 0 for hours without visitors |
| `fct_store_hourly_profile` | MARTS (table) | Average visitors for each store and hour, on weekdays and weekends (480 rows) |

Data integrity tests (24 in total, all passing) include: one row per store, date and hour; a
complete grid with no missing hours; unique visitors never above pings; no ping farther
than 500 m from its store; and the morning (8:00) and evening (18:00) peaks being at least
1.5x midday (13:00). Citywide on weekdays: 195 visitors per store at 8:00, 182 at 18:00,
98 at 13:00 and 53 at 3:00.

Store A (MG Road) shows the commuter pattern clearly: about 330 visitors per hour at midday,
but 633 at 9:00 and 650 at 17:00.

Lesson learned: a first version left out the hours with no visitors, which made midday look
busier than it was. The test for rush hour peaks caught it, and the model now includes zero rows.

All data is synthetic. No real device data is used.

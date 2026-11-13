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

All data is synthetic. No real device data is used.

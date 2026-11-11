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

All data is synthetic. No real device data is used.

"""Load the GPS pings and store locations into Snowflake.

Steps for each file:
  1. PUT   uploads the CSV file to a Snowflake stage (a temporary upload area).
  2. COPY  reads the file from the stage into the table and builds the
           GEOGRAPHY point from latitude and longitude with ST_MAKEPOINT.

Usage:
    python snowflake/load_data.py
    python snowflake/load_data.py --pings data/pings.csv --stores stores/stores.csv

The tables are emptied first, so running it twice does not create duplicates.
"""
import argparse
import os
import sys
import time
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

FILE_FORMAT_SQL = """
CREATE OR REPLACE FILE FORMAT GEOPULSE.RAW.CSV_FORMAT
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL')
"""

# $1.. are the columns of the CSV file in order.
COPY_PINGS_SQL = """
COPY INTO GEOPULSE.RAW.PINGS (DEVICE_ID, LATITUDE, LONGITUDE, PING_TS, LOCATION)
FROM (
    SELECT $1, $2::FLOAT, $3::FLOAT, $4::TIMESTAMP_NTZ,
           ST_MAKEPOINT($3::FLOAT, $2::FLOAT)   -- ST_MAKEPOINT takes (longitude, latitude)
    FROM @GEOPULSE.RAW.LOAD_STAGE/pings/
)
FILE_FORMAT = (FORMAT_NAME = 'GEOPULSE.RAW.CSV_FORMAT')
ON_ERROR = 'ABORT_STATEMENT'
"""

COPY_STORES_SQL = """
COPY INTO GEOPULSE.RAW.STORES (STORE_ID, STORE_NAME, LATITUDE, LONGITUDE, LOCATION)
FROM (
    SELECT $1, $2, $3::FLOAT, $4::FLOAT,
           ST_MAKEPOINT($4::FLOAT, $3::FLOAT)
    FROM @GEOPULSE.RAW.LOAD_STAGE/stores/
)
FILE_FORMAT = (FORMAT_NAME = 'GEOPULSE.RAW.CSV_FORMAT')
ON_ERROR = 'ABORT_STATEMENT'
"""


def connect():
    load_dotenv()
    missing = [k for k in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD")
               if not os.getenv(k) or os.getenv(k).startswith("your_")]
    if missing:
        sys.exit(
            "Missing Snowflake login: " + ", ".join(missing) + "\n"
            "Copy .env.example to .env and fill in your account, user and password."
        )
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "GEOPULSE_WH"),
        database="GEOPULSE",
        schema="RAW",
    )


def upload(cur, path, folder):
    """PUT a local file into the stage folder (the file is compressed on the way)."""
    uri = Path(path).resolve().as_posix()
    cur.execute(f"REMOVE @GEOPULSE.RAW.LOAD_STAGE/{folder}/")
    cur.execute(
        f"PUT 'file://{uri}' @GEOPULSE.RAW.LOAD_STAGE/{folder}/ "
        "AUTO_COMPRESS = TRUE OVERWRITE = TRUE"
    )


def count(cur, table):
    cur.execute(f"SELECT COUNT(*) FROM GEOPULSE.RAW.{table}")
    return cur.fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pings", default="data/pings.csv")
    ap.add_argument("--stores", default="stores/stores.csv")
    args = ap.parse_args()

    for p in (args.pings, args.stores):
        if not Path(p).exists():
            print(f"File not found: {p}")
            if p == args.pings:
                print("Create it first: python data_generation/generate_pings.py")
            return 1

    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("CREATE STAGE IF NOT EXISTS GEOPULSE.RAW.LOAD_STAGE")
        cur.execute(FILE_FORMAT_SQL)

        # Stores
        start = time.time()
        print("Loading stores...")
        upload(cur, args.stores, "stores")
        cur.execute("TRUNCATE TABLE GEOPULSE.RAW.STORES")
        cur.execute(COPY_STORES_SQL)
        print(f"  stores loaded: {count(cur, 'STORES')} rows ({time.time() - start:.0f}s)")

        # Pings (this can take a few minutes for millions of rows)
        start = time.time()
        print("Uploading pings (this can take a few minutes)...")
        upload(cur, args.pings, "pings")
        print(f"  uploaded in {time.time() - start:.0f}s. Copying into the table...")
        cur.execute("TRUNCATE TABLE GEOPULSE.RAW.PINGS")
        cur.execute(COPY_PINGS_SQL)
        print(f"  pings loaded: {count(cur, 'PINGS'):,} rows ({time.time() - start:.0f}s)")
    finally:
        conn.close()
    print("Done. Now run: python snowflake/run_sql.py snowflake/03_check_load.sql")
    return 0


if __name__ == "__main__":
    sys.exit(main())

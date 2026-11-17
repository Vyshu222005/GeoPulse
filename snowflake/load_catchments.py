"""Save the 500 m catchment polygons into the STORES table in Snowflake.

Fills the CATCHMENT GEOGRAPHY column from stores/store_catchments.csv, then checks that
each store point is inside its own polygon and prints the polygon area.

Usage:  python snowflake/load_catchments.py
Run spatial/make_catchments.py first.
"""
import os
import sys
import warnings
from pathlib import Path

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

# Hide a long harmless FutureWarning printed by the Snowflake connector
warnings.filterwarnings("ignore", category=FutureWarning)

CSV = "stores/store_catchments.csv"


def main():
    if not Path(CSV).exists():
        print(f"{CSV} not found. Run: python spatial/make_catchments.py")
        return 1

    load_dotenv()
    missing = [k for k in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD")
               if not os.getenv(k) or os.getenv(k).startswith("your_")]
    if missing:
        print("Missing Snowflake login:", ", ".join(missing))
        return 1

    catch = pd.read_csv(CSV)
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "GEOPULSE_WH"),
        database="GEOPULSE",
        schema="RAW",
    )
    try:
        cur = conn.cursor()
        for _, s in catch.iterrows():
            cur.execute(
                "UPDATE STORES SET CATCHMENT = TO_GEOGRAPHY(%s) WHERE STORE_ID = %s",
                (s.catchment_wkt, s.store_id),
            )
        print(f"Updated {len(catch)} stores")

        cur.execute(
            """
            SELECT STORE_ID,
                   ROUND(ST_AREA(CATCHMENT)) AS AREA_M2,
                   ST_CONTAINS(CATCHMENT, LOCATION) AS STORE_INSIDE_OWN_CIRCLE
            FROM STORES
            ORDER BY STORE_ID
            """
        )
        print(f"{'store':<6}{'area m2':>10}  store inside its circle")
        ok = True
        for store_id, area, inside in cur.fetchall():
            print(f"{store_id:<6}{area:>10,.0f}  {inside}")
            ok &= bool(inside) and area is not None
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

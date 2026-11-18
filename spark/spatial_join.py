"""Spatial join with Apache Sedona: which pings are inside which store catchment?

For every ping we check if its point is inside a store's 500 m circle (ST_Contains).
Sedona turns this into an indexed spatial join. Doing the same with a normal loop over
7.6 million pings x 10 stores would be very slow.

Usage:
    python spark/spatial_join.py                      # all pings
    python spark/spatial_join.py --limit 1000000      # only the first 1 million pings
    python spark/spatial_join.py --driver-memory 2g   # test with less memory

Output:
    data/pings_in_catchments.csv   one row for each (ping, store) pair
    (a ping that is inside two overlapping circles appears twice)
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spark_session import get_spark  # noqa: E402

from pyspark.sql import functions as F  # noqa: E402
from pyspark.sql.types import (  # noqa: E402
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

PING_SCHEMA = StructType(
    [
        StructField("device_id", StringType()),
        StructField("lat", DoubleType()),
        StructField("lon", DoubleType()),
        StructField("ts", TimestampType()),
    ]
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pings", default="data/pings.csv")
    ap.add_argument("--catchments", default="stores/store_catchments.csv")
    ap.add_argument("--out", default="data/pings_in_catchments.csv")
    ap.add_argument("--limit", type=int, default=0, help="use only the first N pings (0 = all)")
    ap.add_argument("--driver-memory", default="4g")
    args = ap.parse_args()

    spark = get_spark("GeoPulse-spatial-join", driver_memory=args.driver_memory)
    start = time.time()

    # 1. Read the pings and turn lat/lon into a point (ST_Point takes longitude first).
    pings = (
        spark.read.csv(
            args.pings, header=True, schema=PING_SCHEMA, timestampFormat="yyyy-MM-dd HH:mm:ss"
        )
        .withColumn("geom", F.expr("ST_Point(lon, lat)"))
    )
    if args.limit:
        pings = pings.limit(args.limit)

    # 2. Read the store circles (WKT text) and turn them into polygons.
    stores = (
        spark.read.csv(args.catchments, header=True)
        .withColumn("catchment", F.expr("ST_GeomFromWKT(catchment_wkt)"))
        .select("store_id", "store_name", "catchment")
    )

    # 3. The spatial join. A small table (10 stores) joined with a big one (pings).
    joined = pings.alias("p").join(
        F.broadcast(stores.alias("s")),
        F.expr("ST_Contains(s.catchment, p.geom)"),
    ).select("s.store_id", "s.store_name", "p.device_id", "p.ts", "p.lat", "p.lon")
    joined.cache()

    # Show that Sedona used its spatial join and not a slow nested loop.
    plan = joined._jdf.queryExecution().executedPlan().toString()
    spatial = [w for w in ("BroadcastIndexJoin", "RangeJoin", "DistanceJoin") if w in plan]
    print("Spatial join used by Spark:", spatial[0] if spatial else "NONE (slow plan!)")

    # 4. Summary for each store.
    total_pings = pings.count()
    summary = (
        joined.groupBy("store_id", "store_name")
        .agg(
            F.count("*").alias("pings_inside"),
            F.countDistinct("device_id").alias("unique_devices"),
        )
        .orderBy("store_id")
    )
    print(f"\nPings read: {total_pings:,}")
    summary.show(truncate=False)
    pairs = joined.count()
    print(f"Ping and store pairs found: {pairs:,}")

    # 5. Save the result. (toPandas is fine here: only the pings inside circles are kept.)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    joined.orderBy("store_id", "ts").toPandas().to_csv(args.out, index=False)
    print(f"Saved to {args.out}")
    print(f"Finished in {time.time() - start:.0f} seconds with driver memory {args.driver_memory}")
    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())

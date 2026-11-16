"""Test that Spark and Sedona work, with a tiny spatial join.

Run:  python spark/test_sedona.py
Expected: pings 1 and 2 are inside 500 m of Store A, ping 3 is not.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spark_session import get_spark  # noqa: E402


def main():
    spark = get_spark("GeoPulse-test")
    print("Spark version:", spark.version)

    # Three test pings. Store A (MG Road) is at lat 12.9755, lon 77.6070.
    spark.createDataFrame(
        [
            ("D1", 12.9760, 77.6075),  # about 78 m away
            ("D2", 12.9780, 77.6100),  # about 428 m away
            ("D3", 12.9900, 77.6300),  # about 3 km away
        ],
        ["device_id", "lat", "lon"],
    ).createOrReplaceTempView("pings")
    spark.createDataFrame(
        [("S01", "Store A - MG Road", 12.9755, 77.6070)],
        ["store_id", "store_name", "lat", "lon"],
    ).createOrReplaceTempView("stores")

    # ST_Point takes (longitude, latitude). ST_DistanceSphere gives meters.
    result = spark.sql(
        """
        SELECT p.device_id,
               s.store_id,
               ROUND(ST_DistanceSphere(ST_Point(p.lon, p.lat), ST_Point(s.lon, s.lat))) AS meters,
               ST_DistanceSphere(ST_Point(p.lon, p.lat), ST_Point(s.lon, s.lat)) <= 500 AS inside_500m
        FROM pings p CROSS JOIN stores s
        ORDER BY p.device_id
        """
    )
    result.show()

    rows = {r["device_id"]: r["inside_500m"] for r in result.collect()}
    ok = rows == {"D1": True, "D2": True, "D3": False}
    print("TEST", "PASSED" if ok else "FAILED")
    spark.stop()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

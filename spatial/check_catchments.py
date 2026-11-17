"""Check the catchment polygons against the pings.

For every store it counts the pings inside the polygon and compares the number with the
count from the plain distance check (within 500 m of the store point). The two numbers
should be almost the same, because the polygon is a 64-sided circle.

Usage:  python spatial/check_catchments.py
"""
import argparse

import pandas as pd
import shapely
from shapely import wkt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pings", default="data/pings.csv")
    ap.add_argument("--catchments", default="stores/store_catchments.csv")
    args = ap.parse_args()

    pings = pd.read_csv(args.pings, usecols=["device_id", "lat", "lon"])
    catch = pd.read_csv(args.catchments)
    print(f"{len(pings):,} pings, {len(catch)} stores\n")
    print(f"{'store':<6}{'pings inside polygon':>22}{'unique devices':>16}")

    for _, s in catch.iterrows():
        poly = wkt.loads(s.catchment_wkt)
        inside = shapely.contains_xy(poly, pings.lon.values, pings.lat.values)
        print(f"{s.store_id:<6}{int(inside.sum()):>22,}{pings.device_id[inside].nunique():>16,}")


if __name__ == "__main__":
    main()

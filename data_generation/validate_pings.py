"""Check the generated ping data and store locations.

Checks:
  1. Columns exist and there are no missing values.
  2. All pings are inside the Bengaluru area.
  3. Morning (7-10) and evening (17-20) have more pings than normal daytime.
  4. How many pings fall within 500 m of each store.
"""
import argparse

import numpy as np
import pandas as pd

BOUNDS = {"lat": (12.70, 13.20), "lon": (77.40, 77.90)}


def haversine_m(lat1, lon1, lat2, lon2):
    """Distance in meters between points (arrays) and one point."""
    r = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dlmb = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pings", default="data/pings.csv")
    ap.add_argument("--stores", default="stores/stores.csv")
    ap.add_argument("--radius", type=float, default=500.0)
    args = ap.parse_args()

    pings = pd.read_csv(args.pings, parse_dates=["ts"])
    stores = pd.read_csv(args.stores)
    ok = True

    # 1. columns and missing values
    need = {"device_id", "lat", "lon", "ts"}
    if not need.issubset(pings.columns):
        print("FAIL: missing columns", need - set(pings.columns))
        return 1
    nulls = int(pings[list(need)].isna().sum().sum())
    print(f"rows: {len(pings):,}  devices: {pings.device_id.nunique():,}  nulls: {nulls}")
    ok &= nulls == 0

    # 2. bounds
    out = ~(
        pings.lat.between(*BOUNDS["lat"]) & pings.lon.between(*BOUNDS["lon"])
    )
    print(f"pings outside city bounds: {int(out.sum())}")
    ok &= int(out.sum()) == 0

    # 3. rush hour peaks
    hourly = pings.groupby(pings.ts.dt.hour).size()
    morning = hourly.loc[7:9].sum() / 3
    evening = hourly.loc[17:19].sum() / 3
    midday = hourly.loc[11:15].sum() / 5
    print(f"avg pings/hour  morning: {morning:,.0f}  midday: {midday:,.0f}  evening: {evening:,.0f}")
    peak_ok = morning > 1.5 * midday and evening > 1.5 * midday
    print("rush hour peaks present:", "YES" if peak_ok else "NO")
    ok &= peak_ok

    # 4. pings near each store
    print(f"\npings within {args.radius:.0f} m of each store:")
    for _, s in stores.iterrows():
        d = haversine_m(pings.lat.values, pings.lon.values, s.lat, s.lon)
        near = pings[d <= args.radius]
        print(
            f"  {s.store_id} {s['name']:<28} pings: {len(near):>7,}  "
            f"devices: {near.device_id.nunique():>5,}"
        )

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

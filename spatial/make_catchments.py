"""Draw a 500 m "catchment area" circle around every store.

A catchment area is the zone around a store where we count visitors. Each circle is
saved as a polygon in WKT text (for example POLYGON((lon lat, lon lat, ...))), which both
Snowflake and Apache Sedona can read.

How a circle is built:
    1 degree of latitude is about 111,195 m everywhere.
    1 degree of longitude is about 111,195 m * cos(latitude), because the lines of longitude
    come closer together away from the equator.
    So a point at angle a and distance r meters is at:
        lat = center_lat + (r * sin a) / 111195
        lon = center_lon + (r * cos a) / (111195 * cos(center_lat))

Usage:
    python spatial/make_catchments.py
    python spatial/make_catchments.py --radius 750
Output: stores/store_catchments.csv
"""
import argparse
import math

import pandas as pd

EARTH_R = 6371000.0
M_PER_DEG_LAT = EARTH_R * math.pi / 180  # about 111,195 m, same Earth as haversine


def circle_ring(lat, lon, radius_m, n_points):
    """Return the circle as a list of (lon, lat), counter-clockwise, first point repeated."""
    pts = []
    for i in range(n_points):
        a = 2 * math.pi * i / n_points
        dlat = radius_m * math.sin(a) / M_PER_DEG_LAT
        dlon = radius_m * math.cos(a) / (M_PER_DEG_LAT * math.cos(math.radians(lat)))
        pts.append((round(lon + dlon, 7), round(lat + dlat, 7)))
    pts.append(pts[0])  # a polygon must end where it starts
    return pts


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R * math.asin(math.sqrt(a))


def ring_area_m2(ring, lat0):
    """Area of the ring in square meters (flat approximation, fine for small circles)."""
    kx = M_PER_DEG_LAT * math.cos(math.radians(lat0))
    ky = M_PER_DEG_LAT
    s = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        s += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky)
    return abs(s) / 2


def to_wkt(ring):
    return "POLYGON((" + ", ".join(f"{x} {y}" for x, y in ring) + "))"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stores", default="stores/stores.csv")
    ap.add_argument("--radius", type=float, default=500.0, help="radius in meters")
    ap.add_argument("--points", type=int, default=64, help="points on each circle")
    ap.add_argument("--out", default="stores/store_catchments.csv")
    args = ap.parse_args()

    stores = pd.read_csv(args.stores)
    rows = []
    ideal_area = math.pi * args.radius ** 2
    print(f"{'store':<6}{'min m':>8}{'max m':>8}{'area m2':>11}{'vs circle':>11}")
    for _, s in stores.iterrows():
        ring = circle_ring(s.lat, s.lon, args.radius, args.points)
        dists = [haversine_m(s.lat, s.lon, y, x) for x, y in ring[:-1]]
        area = ring_area_m2(ring, s.lat)
        print(f"{s.store_id:<6}{min(dists):>8.1f}{max(dists):>8.1f}{area:>11,.0f}"
              f"{area / ideal_area * 100:>10.1f}%")
        rows.append(
            {
                "store_id": s.store_id,
                "store_name": s["name"],
                "lat": s.lat,
                "lon": s.lon,
                "radius_m": args.radius,
                "catchment_wkt": to_wkt(ring),
            }
        )

    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"\nSaved {len(rows)} catchment polygons ({args.radius:.0f} m) to {args.out}")


if __name__ == "__main__":
    main()

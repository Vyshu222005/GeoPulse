"""Generate a mock dataset of anonymized mobile GPS pings that mimics city movement.

Each synthetic device has a home and a workplace. Over a day it:
  - sleeps at home (sparse pings),
  - commutes to work in the morning (07:00-10:00),
  - stays near work (10:00-17:00),
  - commutes home in the evening (17:00-20:00),
  - then stays near home, sometimes running an errand.

Output columns: device_id, lat, lon, ts
"""
import argparse
import os

import numpy as np
import pandas as pd

# Approximate Bengaluru. Residential and commercial hubs (lat, lon, spread in degrees).
HOME_HUBS = [
    (12.9250, 77.5938, 0.020),  # Jayanagar
    (12.9116, 77.6474, 0.020),  # HSR Layout
    (13.0035, 77.5643, 0.020),  # Malleshwaram
    (13.0358, 77.5970, 0.025),  # Hebbal
    (12.9352, 77.6245, 0.020),  # Koramangala
    (12.9569, 77.7011, 0.025),  # Marathahalli
]
WORK_HUBS = [
    (12.9755, 77.6070, 0.012),  # MG Road
    (12.9784, 77.6408, 0.012),  # Indiranagar
    (12.9698, 77.7500, 0.015),  # Whitefield
    (12.8452, 77.6602, 0.015),  # Electronic City
]
START_DATE = "2026-11-02"


def pick_points(rng, hubs, n):
    idx = rng.integers(0, len(hubs), n)
    h = np.array(hubs)[idx]
    lat = h[:, 0] + rng.normal(0, 1, n) * h[:, 2]
    lon = h[:, 1] + rng.normal(0, 1, n) * h[:, 2]
    return lat, lon


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def day_positions(hour, home, work, errand, jitter):
    """Position for each ping given the hour of day (float array)."""
    hlat, hlon = home
    wlat, wlon = work
    elat, elon = errand
    lat = np.empty_like(hour)
    lon = np.empty_like(hour)

    am = (hour >= 7) & (hour < 10)       # commute to work
    work_t = (hour >= 10) & (hour < 17)  # at work
    pm = (hour >= 17) & (hour < 20)      # commute home
    eve = (hour >= 20) & (hour < 22)     # errand near home
    night = ~(am | work_t | pm | eve)

    t = smoothstep((hour - 7) / 3.0)
    lat[am] = (hlat + (wlat - hlat) * t)[am]
    lon[am] = (hlon + (wlon - hlon) * t)[am]
    lat[work_t], lon[work_t] = wlat[work_t], wlon[work_t]
    t = smoothstep((hour - 17) / 3.0)
    lat[pm] = (wlat + (hlat - wlat) * t)[pm]
    lon[pm] = (wlon + (hlon - wlon) * t)[pm]
    lat[eve], lon[eve] = elat[eve], elon[eve]
    lat[night], lon[night] = hlat[night], hlon[night]

    return lat + jitter[0], lon + jitter[1]


def generate_day(rng, devices, day):
    n = len(devices["home_lat"])
    # Pings per device: dense during active hours, sparse at night.
    counts = rng.integers(30, 80, n)
    dev_idx = np.repeat(np.arange(n), counts)
    total = len(dev_idx)

    # Hour of day with more pings in commute hours.
    active = rng.random(total) < 0.8
    rush = rng.random(total) < 0.45  # extra pings during rush hours
    morning = rng.random(total) < 0.5
    rush_hour = np.where(morning, rng.normal(8.5, 0.7, total), rng.normal(18.5, 0.8, total))
    day_hour = np.where(rush, rush_hour, rng.uniform(7, 22, total))
    hour = np.where(active, np.clip(day_hour, 7, 21.99), rng.uniform(0, 7, total))
    # Weekday vs weekend: on weekends people mostly stay near home.
    weekend = day.weekday() >= 5
    if weekend:
        hour = rng.uniform(8, 23, total)

    home = (devices["home_lat"][dev_idx], devices["home_lon"][dev_idx])
    work = (devices["work_lat"][dev_idx], devices["work_lon"][dev_idx])
    if weekend:
        work = home
    errand = (
        home[0] + devices["err_dlat"][dev_idx],
        home[1] + devices["err_dlon"][dev_idx],
    )
    jitter = (rng.normal(0, 0.0004, total), rng.normal(0, 0.0004, total))
    lat, lon = day_positions(hour, home, work, errand, jitter)

    seconds = (hour * 3600).astype("int64")
    ts = pd.to_datetime(day.value, unit="ns") + pd.to_timedelta(seconds, unit="s")
    return pd.DataFrame(
        {
            "device_id": devices["device_id"][dev_idx],
            "lat": lat.round(6),
            "lon": lon.round(6),
            "ts": ts,
        }
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--devices", type=int, default=5000)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/pings.csv")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    n = args.devices
    hl, ho = pick_points(rng, HOME_HUBS, n)
    wl, wo = pick_points(rng, WORK_HUBS, n)
    devices = {
        "device_id": np.array([f"D{i:07d}" for i in range(n)]),
        "home_lat": hl, "home_lon": ho,
        "work_lat": wl, "work_lon": wo,
        "err_dlat": rng.normal(0, 0.006, n),
        "err_dlon": rng.normal(0, 0.006, n),
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    start = pd.Timestamp(START_DATE)
    total = 0
    for d in range(args.days):
        day = start + pd.Timedelta(days=d)
        df = generate_day(rng, devices, day)
        df.to_csv(args.out, mode="w" if d == 0 else "a", header=(d == 0), index=False)
        total += len(df)
        print(f"{day.date()}: {len(df):,} pings")
    print(f"Done. {total:,} pings for {n:,} devices -> {args.out}")


if __name__ == "__main__":
    main()

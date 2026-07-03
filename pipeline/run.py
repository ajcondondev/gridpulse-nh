"""Pipeline orchestrator: fetch -> interim -> processed.

Usage (from repo root, using the apps/api venv which has all deps):

    apps/api/.venv/Scripts/python -m pipeline.run            # full run
    apps/api/.venv/Scripts/python -m pipeline.run --offline  # skip downloads, rebuild from cache
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

import pandas as pd

from pipeline import build_processed, fetch_eia930, fetch_weather
from pipeline.config import INTERIM_DIR, RAW_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="GridPulse data pipeline")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip network fetches; rebuild processed artifacts from cached raw/interim files.",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=date.today().year - 1,
        help="First year of EIA-930 bulk files to include (default: last year).",
    )
    args = parser.parse_args()

    today = date.today()
    filenames = fetch_eia930.half_year_filenames(args.start_year, today.year)

    if not args.offline:
        print("Fetching EIA-930 bulk files (cached in data/raw)...")
        for name in filenames:
            ok = fetch_eia930.download_balance_file(name)
            print(f"  {name}: {'ok' if ok else 'not published yet (skipped)'}")

    available = [n for n in filenames if (RAW_DIR / n).exists()]
    if not available:
        print("ERROR: no EIA-930 bulk files available in data/raw.", file=sys.stderr)
        return 1

    print("Filtering to ISNE ->", INTERIM_DIR / "eia930_isne.csv")
    raw_isne = fetch_eia930.build_interim(available)
    print(f"  {len(raw_isne):,} ISNE hourly rows")

    # Weather range mirrors the demand range, padded a day each side.
    ts = pd.to_datetime(raw_isne["UTC Time at End of Hour"], errors="coerce", utc=True)
    w_start = (ts.min() - pd.Timedelta(days=1)).date()
    w_end = min((ts.max() + pd.Timedelta(days=1)).date(), today - timedelta(days=2))

    weather_path = INTERIM_DIR / "weather_concord_hourly.csv"
    if args.offline and weather_path.exists():
        weather = pd.read_csv(weather_path)
    else:
        print(f"Fetching Open-Meteo hourly temps {w_start} -> {w_end} ...")
        weather = fetch_weather.build_interim(w_start, w_end)
    print(f"  {len(weather):,} weather hours")

    print("Building processed artifacts -> data/processed/")
    counts = build_processed.build_all(raw_isne, weather)
    for key, value in counts.items():
        print(f"  {key}: {value:,}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

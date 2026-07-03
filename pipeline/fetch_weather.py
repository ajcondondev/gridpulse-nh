"""Fetch hourly temperature history for Concord, NH from Open-Meteo (ERA5).

No API key required. Output: data/interim/weather_concord_hourly.csv with
UTC hour-beginning timestamps and temperature in °F.
"""

from __future__ import annotations

from datetime import date

import httpx
import pandas as pd

from pipeline.config import (
    INTERIM_DIR,
    OPEN_METEO_ARCHIVE_URL,
    WEATHER_LAT,
    WEATHER_LON,
)


def fetch_hourly_temps(start: date, end: date) -> pd.DataFrame:
    """Return a DataFrame with columns [ts_utc, temp_f]."""
    resp = httpx.get(
        OPEN_METEO_ARCHIVE_URL,
        params={
            "latitude": WEATHER_LAT,
            "longitude": WEATHER_LON,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": "temperature_2m",
            "temperature_unit": "fahrenheit",
            "timezone": "UTC",
        },
        timeout=120,
    )
    resp.raise_for_status()
    payload = resp.json()
    hourly = payload.get("hourly", {})
    df = pd.DataFrame(
        {
            "ts_utc": pd.to_datetime(hourly.get("time", []), utc=True),
            "temp_f": pd.to_numeric(hourly.get("temperature_2m", []), errors="coerce"),
        }
    )
    df = df.dropna(subset=["ts_utc"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("Open-Meteo returned no hourly temperature data.")
    return df


def build_interim(start: date, end: date) -> pd.DataFrame:
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    df = fetch_hourly_temps(start, end)
    out = INTERIM_DIR / "weather_concord_hourly.csv"
    df.to_csv(out, index=False)
    return df

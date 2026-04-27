from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from app.config import settings
from app.schemas.dataset import Dataset
from app.services import dataset_service, storage_service


def _load_latest_cleaned(source_id: str) -> Optional[pd.DataFrame]:
    """Return the cleaned DataFrame for the most recently fetched dataset of a given source."""
    candidates = [
        d for d in dataset_service.list_datasets()
        if d.source_id == source_id and d.cleaned_path
    ]
    if not candidates:
        return None
    p = Path(candidates[0].cleaned_path)
    if not p.exists():
        return None
    return pd.read_csv(p)


def _aggregate_demand_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    daily = (
        df.groupby("date")
        .agg(
            daily_peak_mw=("demand_mw", "max"),
            region=("region", "first"),
            demand_source=("source", "first"),
        )
        .reset_index()
    )
    daily["daily_peak_mw"] = daily["daily_peak_mw"].round(1)
    return daily


def _synthetic_weather(dates: list) -> pd.DataFrame:
    """Generate plausible NH seasonal weather when no NOAA dataset is available."""
    rng = np.random.default_rng(42)
    rows = []
    for d in dates:
        doy = d.timetuple().tm_yday
        base = 50.0 + 20.0 * np.sin(2 * np.pi * (doy - 80) / 365)
        avg = round(float(base) + float(rng.normal(0, 5)), 1)
        rows.append({
            "date": d,
            "temp_avg_f": avg,
            "hdd": round(max(0.0, 65.0 - avg), 1),
            "cdd": round(max(0.0, avg - 65.0), 1),
            "weather_source": "Mock Weather",
        })
    return pd.DataFrame(rows)


def create_weather_demand_join() -> Dataset:
    now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)

    # Demand: prefer mock, fall back to EIA
    df_demand = _load_latest_cleaned("mock_demand")
    if df_demand is None:
        df_demand = _load_latest_cleaned("eia_isone_load")
    if df_demand is None:
        raise ValueError(
            "No demand dataset found. "
            "Fetch Mock Electricity Demand (or EIA ISO-NE Load) first."
        )

    daily = _aggregate_demand_to_daily(df_demand)

    # Weather: NOAA if available, otherwise synthetic
    df_weather = _load_latest_cleaned("noaa_weather")
    if df_weather is not None:
        df_weather["date"] = pd.to_datetime(df_weather["date"]).dt.date
        df_joined = daily.merge(
            df_weather[["date", "temp_avg_f", "hdd", "cdd", "source"]].rename(
                columns={"source": "weather_source"}
            ),
            on="date",
            how="left",
        )
    else:
        synthetic = _synthetic_weather(list(daily["date"]))
        df_joined = daily.merge(synthetic, on="date", how="left")

    df_joined["created_at"] = now.isoformat()

    out_cols = [
        "date", "region", "daily_peak_mw",
        "temp_avg_f", "hdd", "cdd",
        "demand_source", "weather_source", "created_at",
    ]
    for col in out_cols:
        if col not in df_joined.columns:
            df_joined[col] = None
    df_joined = df_joined[out_cols].sort_values("date").reset_index(drop=True)

    dataset_id = f"wd_join_{now.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    cleaned_p = storage_service.cleaned_path("weather_demand", filename)
    df_joined.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="weather_demand_analysis",
        name=f"Weather–Demand Analysis — {now.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=now,
        row_count=len(df_joined),
        columns=list(df_joined.columns),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset

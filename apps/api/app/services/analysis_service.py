from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from app.schemas.dataset import Dataset
from app.services import dataset_service, storage_service


def _load_latest_cleaned(source_id: str) -> Optional[pd.DataFrame]:
    """Return the cleaned DataFrame for the most recently fetched dataset of a given source."""
    dataset = dataset_service.latest_dataset(source_id, require_cleaned=True)
    if dataset is None or not dataset.cleaned_path:
        return None
    p = Path(dataset.cleaned_path)
    if not p.exists():
        return None
    return pd.read_csv(p)


def _aggregate_demand_to_daily(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["demand_mw"] = pd.to_numeric(df["demand_mw"], errors="coerce")
    df = df.dropna(subset=["timestamp", "demand_mw"])
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


def _load_latest_demand_dataset() -> tuple[Optional[pd.DataFrame], Optional[str]]:
    df_eia = _load_latest_cleaned("eia_isone_load")
    if df_eia is not None:
        return df_eia, "eia_isone_load"

    df_mock = _load_latest_cleaned("mock_demand")
    if df_mock is not None:
        return df_mock, "mock_demand"

    return None, None


def _prepare_weather_for_join(df_weather: pd.DataFrame) -> pd.DataFrame:
    weather = df_weather.copy()
    weather["date"] = pd.to_datetime(weather["date"], errors="coerce").dt.date
    for col in ["temp_avg_f", "hdd", "cdd"]:
        weather[col] = pd.to_numeric(weather[col], errors="coerce")
    weather = weather.dropna(subset=["date"])
    weather = weather.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    return weather[["date", "temp_avg_f", "hdd", "cdd", "source"]].rename(
        columns={"source": "weather_source"}
    )


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

    df_demand, demand_source_id = _load_latest_demand_dataset()
    if df_demand is None or demand_source_id is None:
        raise ValueError(
            "No demand dataset found. "
            "Fetch Mock Electricity Demand (or EIA ISO-NE Load) first."
        )

    daily = _aggregate_demand_to_daily(df_demand)
    if daily.empty:
        raise ValueError("Demand dataset could not be aggregated into daily peaks.")

    df_weather = _load_latest_cleaned("noaa_weather")
    if df_weather is not None:
        weather = _prepare_weather_for_join(df_weather)
        df_joined = daily.merge(weather, on="date", how="inner")
        if df_joined.empty:
            raise ValueError(
                "NOAA weather data does not overlap with the latest demand dataset. "
                "Fetch more recent EIA/NOAA data and try again."
            )
    else:
        if demand_source_id != "mock_demand":
            raise ValueError(
                "NOAA weather dataset not found. Fetch NOAA Weather before generating a live weather-demand join."
            )
        synthetic = _synthetic_weather(list(daily["date"]))
        df_joined = daily.merge(synthetic, on="date", how="left")

    if df_joined.empty:
        raise ValueError("Weather-demand join produced no rows.")

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

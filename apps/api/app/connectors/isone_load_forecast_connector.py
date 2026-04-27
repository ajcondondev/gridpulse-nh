from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

_FORECAST_COLUMN_PREFIXES = (
    "Net Load Forecast",
    "Load Forecast",
    "Total Load Forecast",
    "Forecast",
)


class ISONELoadForecastConnector(BaseConnector):
    """ISO-NE hourly load forecast — public transform/csv endpoint."""

    source_id = "isone_load_forecast"
    BASE_URL = "https://www.iso-ne.com/transform/csv/hourlyloadforecast"
    DAYS_BACK = 7

    DATE_COLUMN_CANDIDATES = ("Date", "DATE", "date", "Local Date", "BeginDate")
    HOUR_COLUMN_CANDIDATES = ("Hour Ending", "HE", "Hour", "HourEnding", "hour_ending")

    def fetch(self) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
        end_date = now.date()
        start_date = end_date - timedelta(days=self.DAYS_BACK - 1)

        params = {
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
        }

        response = httpx.get(self.BASE_URL, params=params, timeout=30.0)
        response.raise_for_status()

        text = response.text.strip()
        if not text:
            raise ValueError(
                f"ISO-NE load forecast CSV returned an empty response. URL: {self.BASE_URL}"
            )

        df = pd.read_csv(StringIO(text))
        if df.empty:
            raise ValueError("ISO-NE load forecast CSV returned no rows.")

        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)

        date_col = _find_column(df, self.DATE_COLUMN_CANDIDATES)
        hour_col = _find_column(df, self.HOUR_COLUMN_CANDIDATES)

        if not date_col or not hour_col:
            raise ValueError(
                "ISO-NE load forecast CSV missing date or hour column. "
                f"Columns found: {list(df.columns)}."
            )

        forecast_col = next(
            (
                c for c in df.columns
                if c not in (date_col, hour_col)
                and any(c.strip().startswith(prefix) for prefix in _FORECAST_COLUMN_PREFIXES)
            ),
            None,
        )
        if forecast_col is None:
            forecast_col = next(
                (
                    c for c in df.columns
                    if c not in (date_col, hour_col)
                    and pd.to_numeric(df[c], errors="coerce").notna().sum() > 0
                ),
                None,
            )

        if forecast_col is None:
            raise ValueError(
                "ISO-NE load forecast CSV: could not identify a forecast column. "
                f"Columns found: {list(df.columns)}."
            )

        date_series = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
        hour_series = df[hour_col].apply(_normalize_hour_ending)
        forecast_mw = pd.to_numeric(df[forecast_col], errors="coerce")

        out = pd.DataFrame({
            "date": date_series,
            "hour_ending": hour_series,
            "load_forecast_mw": forecast_mw,
        })
        out = out.dropna(subset=["date", "hour_ending", "load_forecast_mw"])
        out = out[out["load_forecast_mw"] > 0]

        out["timestamp"] = out.apply(
            lambda row: row["date"] + timedelta(hours=int(row["hour_ending"]) - 1),
            axis=1,
        )
        out["source"] = "ISO-NE Load Forecast"
        out = out.sort_values("timestamp").reset_index(drop=True)

        if out.empty:
            raise ValueError("ISO-NE load forecast cleaned dataset is empty after validation.")

        return out[["timestamp", "date", "hour_ending", "load_forecast_mw", "source"]]


def _find_column(df: pd.DataFrame, candidates: tuple) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _normalize_hour_ending(value) -> int | None:
    if pd.isna(value):
        return None
    text = str(value).strip().upper()
    if text.startswith("HE"):
        text = text[2:]
    try:
        hour = int(float(text))
    except ValueError:
        return None
    return hour if 1 <= hour <= 24 else None

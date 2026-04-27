from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

_FUEL_COLUMN_PREFIXES = (
    "Natural Gas", "Nuclear", "Hydro", "Solar", "Wind",
    "Oil", "Coal", "Other", "Imports", "Refuse", "Wood",
    "Landfill Gas", "Biomass",
)


class ISONEFuelMixConnector(BaseConnector):
    """ISO-NE hourly generation by fuel type — public transform/csv endpoint."""

    source_id = "isone_fuel_mix"
    BASE_URL = "https://www.iso-ne.com/transform/csv/genfuelmix"
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
                f"ISO-NE fuel mix CSV returned an empty response. URL: {self.BASE_URL}"
            )

        df = pd.read_csv(StringIO(text))
        if df.empty:
            raise ValueError("ISO-NE fuel mix CSV returned no rows.")

        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)

        date_col = _find_column(df, self.DATE_COLUMN_CANDIDATES)
        hour_col = _find_column(df, self.HOUR_COLUMN_CANDIDATES)

        if not date_col or not hour_col:
            raise ValueError(
                "ISO-NE fuel mix CSV missing date or hour column. "
                f"Columns found: {list(df.columns)}."
            )

        fuel_cols = [
            c for c in df.columns
            if c not in (date_col, hour_col)
            and any(c.strip().startswith(prefix) for prefix in _FUEL_COLUMN_PREFIXES)
        ]
        if not fuel_cols:
            # fall back: treat all numeric columns except date/hour as fuel types
            fuel_cols = [
                c for c in df.columns
                if c not in (date_col, hour_col)
                and pd.to_numeric(df[c], errors="coerce").notna().sum() > 0
            ]

        if not fuel_cols:
            raise ValueError(
                "ISO-NE fuel mix CSV: could not identify any fuel type columns. "
                f"Columns found: {list(df.columns)}."
            )

        date_series = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
        hour_series = df[hour_col].apply(_normalize_hour_ending)

        rows = []
        for fuel in fuel_cols:
            mw = pd.to_numeric(df[fuel], errors="coerce")
            chunk = pd.DataFrame({
                "date": date_series,
                "hour_ending": hour_series,
                "fuel_type": fuel.strip(),
                "value": mw,
                "unit": "MW",
            })
            rows.append(chunk)

        out = pd.concat(rows, ignore_index=True)
        out = out.dropna(subset=["date", "hour_ending", "value"])
        out = out[out["value"] >= 0]

        out["timestamp"] = out.apply(
            lambda row: row["date"] + timedelta(hours=int(row["hour_ending"]) - 1),
            axis=1,
        )
        out["source"] = "ISO-NE Gen Fuel Mix"
        out = out.sort_values(["timestamp", "fuel_type"]).reset_index(drop=True)

        if out.empty:
            raise ValueError("ISO-NE fuel mix cleaned dataset is empty after validation.")

        return out[["timestamp", "date", "hour_ending", "fuel_type", "value", "unit", "source"]]


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

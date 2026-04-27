from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector


class ISONECSVConnector(BaseConnector):
    """Public ISO-NE hourly real-time system demand CSV connector."""

    source_id = "isone_csv"
    BASE_URL = "https://www.iso-ne.com/transform/csv/hourlysystemdemand"
    DAYS_BACK = 7

    DATE_COLUMN_CANDIDATES = ("Date", "DATE", "date", "Local Date")
    HOUR_COLUMN_CANDIDATES = ("Hour Ending", "Hour", "HE", "HourEnding")
    DEMAND_COLUMN_CANDIDATES = (
        "Native Demand",
        "System Demand",
        "Demand",
        "Load",
        "MWh",
        "Mw",
    )

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
            raise ValueError("ISO-NE CSV download returned an empty response body.")

        df = pd.read_csv(StringIO(text))
        if df.empty:
            raise ValueError("ISO-NE CSV download returned no rows.")

        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)

        date_col = self._find_column(df, self.DATE_COLUMN_CANDIDATES)
        hour_col = self._find_column(df, self.HOUR_COLUMN_CANDIDATES)
        demand_col = self._find_column(df, self.DEMAND_COLUMN_CANDIDATES)

        missing = [
            name
            for name, col in {
                "date": date_col,
                "hour": hour_col,
                "demand": demand_col,
            }.items()
            if col is None
        ]
        if missing:
            raise ValueError(
                "ISO-NE CSV missing expected columns. "
                f"Missing logical fields: {missing}. Columns found: {list(df.columns)}."
            )

        out = pd.DataFrame(
            {
                "date": pd.to_datetime(df[date_col], errors="coerce", format="mixed"),
                "hour_ending": df[hour_col],
                "demand_mw": pd.to_numeric(df[demand_col], errors="coerce"),
            }
        )
        out["hour_ending"] = out["hour_ending"].apply(self._normalize_hour_ending)
        out = out.dropna(subset=["date", "hour_ending", "demand_mw"])
        out = out[out["demand_mw"] > 0]

        out["timestamp"] = out.apply(
            lambda row: row["date"] + timedelta(hours=int(row["hour_ending"]) - 1),
            axis=1,
        )
        out["region"] = "ISO-NE"
        out["source"] = "ISO-NE CSV"

        out = out.drop_duplicates(subset=["timestamp"], keep="last")
        out = out.sort_values("timestamp").reset_index(drop=True)

        if out.empty:
            raise ValueError("ISO-NE cleaned dataset is empty after validation.")

        return out[["timestamp", "region", "demand_mw", "source"]]

    @staticmethod
    def _find_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
        return None

    @staticmethod
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
        if hour < 1 or hour > 24:
            return None
        return hour

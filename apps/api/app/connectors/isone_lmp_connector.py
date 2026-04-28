"""
ISO-NE Hourly Zone LMP (Locational Marginal Price) connector.

Fetches 7 days of real-time hourly LMP for all ISO-NE load zones and hubs
from the public transform/csv endpoint — no API key required.

TODO: Confirm that https://www.iso-ne.com/transform/csv/hourlylmp accepts the
      same start/end query parameters as the system-demand and fuel-mix endpoints.
      Verify column names against a live response before relying on the long-form
      zone format assumed below (columns: Date, Hour Ending, Location ID,
      Location Name, Locational Marginal Price, Energy Component,
      Congestion Component, Loss Component).
"""

from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

_DATE_CANDIDATES = ("Date", "DATE", "date", "Local Date", "BeginDate")
_HOUR_CANDIDATES = ("Hour Ending", "HE", "Hour", "HourEnding", "hour_ending")
_ZONE_ID_CANDIDATES = (
    "Location ID", "LocationID", "Zone ID", "Zone", "Location",
    "Node ID", "NodeID", "Pnode ID",
)
_ZONE_NAME_CANDIDATES = (
    "Location Name", "LocationName", "Zone Name", "ZoneName",
    "Location Type", "Node Name",
)
_LMP_CANDIDATES = (
    "Locational Marginal Price", "LMP", "Total LMP", "LMP ($/MWh)",
    "LMP_Total", "lmp",
)
_ENERGY_CANDIDATES = ("Energy Component", "Energy", "ECO", "Energy_Component")
_CONGESTION_CANDIDATES = ("Congestion Component", "Congestion", "MCC", "Congestion_Component")
_LOSS_CANDIDATES = ("Loss Component", "Loss", "MLC", "Loss_Component")


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


class ISONELMPConnector(BaseConnector):
    """
    ISO-NE hourly zone LMP prices — public transform/csv endpoint.

    Returns all load zones and hubs in long format: one row per hour per location.
    The New Hampshire zone is identified as '.Z.NEWHAMPSHIRE' in the Location ID column.
    """

    source_id = "isone_lmp"
    BASE_URL = "https://www.iso-ne.com/transform/csv/hourlylmp"
    DAYS_BACK = 7

    def fetch(self) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
        end_date = now.date()
        start_date = end_date - timedelta(days=self.DAYS_BACK - 1)

        params = {
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
        }

        response = httpx.get(self.BASE_URL, params=params, timeout=45.0)
        response.raise_for_status()

        text = response.text.strip()
        if not text:
            raise ValueError(
                f"ISO-NE LMP CSV returned an empty response. "
                f"URL: {self.BASE_URL} — verify the endpoint path is correct."
            )

        df = pd.read_csv(StringIO(text))
        if df.empty:
            raise ValueError(
                "ISO-NE LMP CSV parsed successfully but returned no rows. "
                "Check the date range and endpoint parameters."
            )

        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)

        date_col = _find_column(df, _DATE_CANDIDATES)
        hour_col = _find_column(df, _HOUR_CANDIDATES)
        zone_id_col = _find_column(df, _ZONE_ID_CANDIDATES)
        zone_name_col = _find_column(df, _ZONE_NAME_CANDIDATES)
        lmp_col = _find_column(df, _LMP_CANDIDATES)
        energy_col = _find_column(df, _ENERGY_CANDIDATES)
        congestion_col = _find_column(df, _CONGESTION_CANDIDATES)
        loss_col = _find_column(df, _LOSS_CANDIDATES)

        missing = [
            label
            for label, col in [
                ("date", date_col),
                ("hour_ending", hour_col),
                ("lmp", lmp_col),
            ]
            if col is None
        ]
        if missing:
            raise ValueError(
                f"ISO-NE LMP CSV missing required columns: {missing}. "
                f"Columns found: {list(df.columns)}. "
                "Verify the transform/csv endpoint response and update column candidates."
            )

        date_series = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
        hour_series = df[hour_col].apply(_normalize_hour_ending)
        lmp_series = pd.to_numeric(df[lmp_col], errors="coerce")

        out = pd.DataFrame({
            "date": date_series,
            "hour_ending": hour_series,
            "lmp_per_mwh": lmp_series,
        })

        if zone_id_col:
            out["zone_id"] = df[zone_id_col].astype(str).str.strip()
        else:
            out["zone_id"] = pd.NA

        if zone_name_col:
            out["zone_name"] = df[zone_name_col].astype(str).str.strip()
        else:
            out["zone_name"] = pd.NA

        out["energy_component"] = (
            pd.to_numeric(df[energy_col], errors="coerce") if energy_col else pd.NA
        )
        out["congestion_component"] = (
            pd.to_numeric(df[congestion_col], errors="coerce") if congestion_col else pd.NA
        )
        out["loss_component"] = (
            pd.to_numeric(df[loss_col], errors="coerce") if loss_col else pd.NA
        )

        out = out.dropna(subset=["date", "hour_ending", "lmp_per_mwh"])
        out = out[out["hour_ending"].between(1, 24)]

        out["timestamp"] = out.apply(
            lambda row: row["date"] + timedelta(hours=int(row["hour_ending"]) - 1),
            axis=1,
        )
        out["source"] = "ISO-NE LMP"
        out = out.sort_values(["timestamp", "zone_id"]).reset_index(drop=True)

        if out.empty:
            raise ValueError("ISO-NE LMP cleaned dataset is empty after validation.")

        cols = [
            "timestamp", "date", "hour_ending",
            "zone_id", "zone_name",
            "lmp_per_mwh", "energy_component", "congestion_component", "loss_component",
            "source",
        ]
        return out[[c for c in cols if c in out.columns]]

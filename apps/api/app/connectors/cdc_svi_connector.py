import io
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

SVI_YEAR = 2022
_SVI_URL = f"https://svi.cdc.gov/Documents/Data/{SVI_YEAR}/csv/states/NewHampshire.csv"

_NODATA = -999.0

_REQUIRED = {"FIPS", "COUNTY", "LOCATION", "RPL_THEMES", "RPL_THEME1", "RPL_THEME2", "RPL_THEME3", "RPL_THEME4"}


class CDCSVIConnector(BaseConnector):
    """CDC/ATSDR Social Vulnerability Index connector — NH census tracts."""

    source_id = "cdc_svi"

    def fetch(self) -> dict:
        response = httpx.get(_SVI_URL, follow_redirects=True, timeout=30.0)
        response.raise_for_status()

        df = pd.read_csv(io.BytesIO(response.content), dtype=str)
        if df.empty:
            raise ValueError("CDC SVI returned an empty dataset.")

        missing = _REQUIRED - set(df.columns)
        if missing:
            raise ValueError(
                f"CDC SVI CSV missing expected columns: {sorted(missing)}. "
                f"Columns found: {list(df.columns)[:20]}."
            )

        return {
            "dataframe": df,
            "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0),
            "row_count": len(df),
        }

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path, dtype=str)

        missing = _REQUIRED - set(df.columns)
        if missing:
            raise ValueError(
                f"CDC SVI raw file missing expected columns: {sorted(missing)}."
            )

        out = pd.DataFrame()
        out["year"] = SVI_YEAR
        out["state"] = df["STATE"] if "STATE" in df.columns else "New Hampshire"
        out["county"] = df["COUNTY"]
        out["fips"] = df["FIPS"]
        out["location_name"] = df["LOCATION"]
        out["svi_overall_percentile"] = pd.to_numeric(df["RPL_THEMES"], errors="coerce")
        out["socioeconomic_percentile"] = pd.to_numeric(df["RPL_THEME1"], errors="coerce")
        out["household_characteristics_percentile"] = pd.to_numeric(df["RPL_THEME2"], errors="coerce")
        out["racial_ethnic_minority_percentile"] = pd.to_numeric(df["RPL_THEME3"], errors="coerce")
        out["housing_transportation_percentile"] = pd.to_numeric(df["RPL_THEME4"], errors="coerce")
        if "E_TOTPOP" in df.columns:
            out["population"] = pd.to_numeric(df["E_TOTPOP"], errors="coerce")

        percentile_cols = [
            "svi_overall_percentile",
            "socioeconomic_percentile",
            "household_characteristics_percentile",
            "racial_ethnic_minority_percentile",
            "housing_transportation_percentile",
        ]
        for col in percentile_cols:
            out[col] = out[col].where(out[col] != _NODATA)

        out["source"] = "CDC/ATSDR SVI 2022"

        out = out.dropna(subset=["fips", "county"])
        out = out.reset_index(drop=True)

        if out.empty:
            raise ValueError("CDC SVI cleaned dataset is empty after validation.")

        return out

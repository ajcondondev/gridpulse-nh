from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

# US Census 2020 Decennial — NH county subdivisions (towns and cities)
_CENSUS_URL = "https://api.census.gov/data/2020/dec/pl"
_NH_STATE_FIPS = "33"


class NHGeodataConnector(BaseConnector):
    """NH municipal geography connector — NH towns from US Census 2020."""

    source_id = "nh_geodata"

    def fetch(self) -> dict:
        params = {
            "get": "NAME,P1_001N",
            "for": "county subdivision:*",
            "in": f"state:{_NH_STATE_FIPS}",
        }

        response = httpx.get(_CENSUS_URL, params=params, timeout=30.0)
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, list) or len(payload) < 1 or not isinstance(payload[0], list):
            raise ValueError("Census API returned an unexpected response for NH county subdivisions.")

        headers = payload[0]
        rows = payload[1:]
        df = pd.DataFrame(rows, columns=headers)

        if df.empty:
            raise ValueError("Census API returned no NH county subdivisions.")

        return {
            "dataframe": df,
            "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0),
            "row_count": len(df),
        }

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path, dtype=str)

        if "NAME" not in df.columns:
            raise ValueError(
                f"NH Geodata raw file missing NAME column. "
                f"Columns found: {list(df.columns)}."
            )

        parts = df["NAME"].str.split(",", expand=True)
        town_name = parts[0].str.strip()

        # Name format: "Acworth town, Sullivan County, New Hampshire"
        county_raw = parts[1].str.strip() if parts.shape[1] > 1 else pd.Series([""] * len(df))
        county_name = county_raw.str.replace(" County", "", regex=False).str.strip()

        state_col = df["state"] if "state" in df.columns else pd.Series([_NH_STATE_FIPS] * len(df))
        county_col = df["county"] if "county" in df.columns else pd.Series([""] * len(df))
        subdiv_col = df["county subdivision"] if "county subdivision" in df.columns else pd.Series([""] * len(df))

        out = pd.DataFrame()
        out["town_name"] = town_name
        out["county_name"] = county_name
        out["state"] = "NH"
        out["state_fips"] = state_col.str.zfill(2)
        out["county_fips"] = (state_col.str.zfill(2) + county_col.str.zfill(3))
        out["town_fips"] = (
            state_col.str.zfill(2) + county_col.str.zfill(3) + subdiv_col.str.zfill(5)
        )
        out["population_2020"] = pd.to_numeric(
            df["P1_001N"] if "P1_001N" in df.columns else pd.Series([None] * len(df)),
            errors="coerce",
        ).astype("Int64")
        out["source"] = "US Census Bureau 2020 Decennial"

        out = out.dropna(subset=["town_name"])
        out = out[out["town_name"].str.strip() != ""]
        out = out.reset_index(drop=True)

        if out.empty:
            raise ValueError("NH Geodata cleaned dataset is empty after validation.")

        return out

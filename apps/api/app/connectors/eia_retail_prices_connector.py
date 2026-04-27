"""
EIA average retail electricity prices — NH residential, commercial, industrial.

Requires EIA_API_KEY environment variable.
Register free at: https://www.eia.gov/opendata/

TODO: Verify column names and response schema against a live EIA_API_KEY.
      Endpoint and field mappings are based on EIA v2 API documentation
      reviewed 2026-04-27 but have NOT been confirmed against a live response.
"""

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector

_SECTOR_RENAME = {
    "RES": "residential",
    "COM": "commercial",
    "IND": "industrial",
    "TRA": "transportation",
    "OTH": "other",
    "ALL": "all_sectors",
}


class EIARetailPricesConnector(BaseConnector):
    """Monthly average retail electricity prices for NH by sector."""

    source_id = "eia_retail_prices"
    BASE_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"
    STATE = "NH"
    MONTHS_BACK = 48

    def fetch(self) -> dict:
        if not settings.eia_api_key:
            raise ValueError(
                "EIA_API_KEY is not configured. "
                "Register at https://www.eia.gov/opendata/ and set EIA_API_KEY in .env."
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)

        params = {
            "api_key": settings.eia_api_key,
            "frequency": "monthly",
            "data[0]": "price",
            "facets[stateid][]": self.STATE,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": self.MONTHS_BACK,
        }

        response = httpx.get(self.BASE_URL, params=params, timeout=30.0)
        response.raise_for_status()

        payload = response.json()
        response_data = payload.get("response")
        if not isinstance(response_data, dict):
            raise ValueError("EIA retail prices response missing 'response' object.")

        records = response_data.get("data", [])
        if not isinstance(records, list) or not records:
            raise ValueError(
                "EIA retail prices API returned no data. "
                "Verify the endpoint, state code, and query parameters are correct."
            )

        df = pd.DataFrame(records)
        if df.empty:
            raise ValueError("EIA retail prices API returned an empty dataset after parsing.")

        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        # TODO: Confirm EIA v2 retail-sales column names against a live response.
        # Expected: period, stateid, stateDescription, sectorid, sectorName, price, price-units
        df = pd.read_csv(raw_path)

        rename: dict[str, str] = {}
        if "period" in df.columns:
            rename["period"] = "period"
        if "stateid" in df.columns:
            rename["stateid"] = "state"
        elif "stateDescription" in df.columns:
            rename["stateDescription"] = "state"
        if "sectorid" in df.columns:
            rename["sectorid"] = "sector_id"
        if "sectorName" in df.columns:
            rename["sectorName"] = "sector_name"
        if "price" in df.columns:
            rename["price"] = "price_cents_per_kwh"

        df = df.rename(columns=rename)

        required = ["period", "price_cents_per_kwh"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(
                "EIA retail prices response missing expected columns after renaming. "
                f"Missing: {missing}. Columns found: {list(df.columns)}. "
                "Verify EIA API response schema."
            )

        if "state" not in df.columns:
            df["state"] = self.STATE

        if "sector_id" not in df.columns:
            df["sector_id"] = "UNK"

        if "sector_name" not in df.columns:
            df["sector_name"] = df["sector_id"].map(_SECTOR_RENAME).fillna(df["sector_id"])

        df["price_cents_per_kwh"] = pd.to_numeric(df["price_cents_per_kwh"], errors="coerce")
        df = df.dropna(subset=["period", "price_cents_per_kwh"])
        df = df[df["price_cents_per_kwh"] > 0]
        df = df.sort_values(["period", "sector_id"]).reset_index(drop=True)
        df["source"] = "EIA Retail Sales"

        if df.empty:
            raise ValueError("EIA retail prices cleaned dataset is empty after validation.")

        return df[["period", "state", "sector_id", "sector_name", "price_cents_per_kwh", "source"]]

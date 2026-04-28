"""
EIA monthly natural gas retail prices for New Hampshire by sector.

Natural gas is the dominant fuel for ISO-NE electricity generation and the
primary driver of NH retail electricity price volatility. This connector
provides the residential, commercial, and industrial NG price context needed
to interpret electricity price movements.

Requires EIA_API_KEY — same key used by eia_retail_prices and eia_isone_load.
Free registration: https://www.eia.gov/opendata/

Endpoint: https://api.eia.gov/v2/natural-gas/pri/sum/data/
Source: EIA Natural Gas Prices Summary (state-level retail prices in $/MCF)

NH EIA series codes (embedded in the 'series' field of each response record):
  N3010NH3 — Residential
  N3020NH3 — Commercial
  N3035NH3 — Industrial (excluding electric power plants)
  N3050NH3 — Delivered to all consumers (aggregate)

TODO: Verify response field names and series code format against a live EIA_API_KEY.
      Endpoint and field mappings are based on EIA v2 API documentation reviewed
      2026-04-28 but have NOT been confirmed against a live response.
"""

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector

_SECTOR_FROM_SERIES_PREFIX = {
    "N3010": "residential",
    "N3020": "commercial",
    "N3035": "industrial",
    "N3050": "all_sectors",
}


def _sector_from_series(series_id: str) -> str:
    """Map an EIA series ID (e.g. 'N3010NH3') to a human-readable sector name."""
    s = str(series_id).upper().strip()
    for prefix, label in _SECTOR_FROM_SERIES_PREFIX.items():
        if s.startswith(prefix):
            return label
    return "other"


class EIANGPricesConnector(BaseConnector):
    """Monthly retail natural gas prices for NH by sector — EIA v2 API."""

    source_id = "eia_ng_prices"
    BASE_URL = "https://api.eia.gov/v2/natural-gas/pri/sum/data/"
    STATE = "NH"
    MONTHS_BACK = 60  # 5 years of monthly context

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
            raise ValueError(
                "EIA natural gas prices response missing 'response' object. "
                "Verify the endpoint and API key."
            )

        records = response_data.get("data", [])
        if not isinstance(records, list) or not records:
            raise ValueError(
                "EIA natural gas prices API returned no data. "
                "Verify the endpoint, state code, and query parameters."
            )

        df = pd.DataFrame(records)
        if df.empty:
            raise ValueError("EIA natural gas prices API returned an empty dataset after parsing.")

        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        # TODO: Confirm EIA v2 natural-gas/pri/sum column names against a live response.
        # Expected: period, stateid, duoarea, series, series-description, price, price-units
        df = pd.read_csv(raw_path)

        # Normalize field names — EIA sometimes uses hyphens in keys
        df.columns = [c.replace("-", "_") for c in df.columns]

        rename: dict[str, str] = {}
        if "period" in df.columns:
            rename["period"] = "period"
        if "stateid" in df.columns:
            rename["stateid"] = "state"
        if "series" in df.columns:
            rename["series"] = "series_id"
        if "series_description" in df.columns:
            rename["series_description"] = "series_description"
        if "price" in df.columns:
            rename["price"] = "price_per_mcf"
        if "price_units" in df.columns:
            rename["price_units"] = "price_units"

        df = df.rename(columns=rename)

        required = ["period", "price_per_mcf"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(
                "EIA natural gas prices response missing expected columns after renaming. "
                f"Missing: {missing}. Columns found: {list(df.columns)}. "
                "Verify EIA API response schema — see connector TODO."
            )

        if "state" not in df.columns:
            df["state"] = self.STATE

        if "series_id" in df.columns:
            df["sector"] = df["series_id"].apply(_sector_from_series)
        else:
            df["sector"] = "unknown"

        df["price_per_mcf"] = pd.to_numeric(df["price_per_mcf"], errors="coerce")
        df = df.dropna(subset=["period", "price_per_mcf"])
        df = df[df["price_per_mcf"] > 0]

        # Keep only retail sectors (exclude electric power plant purchases)
        retail_sectors = {"residential", "commercial", "industrial", "all_sectors"}
        df = df[df["sector"].isin(retail_sectors)]

        df = df.sort_values(["period", "sector"]).reset_index(drop=True)
        df["source"] = "EIA Natural Gas Prices"

        if df.empty:
            raise ValueError(
                "EIA natural gas prices cleaned dataset is empty after validation. "
                "Verify sector filtering and price column."
            )

        cols = ["period", "state", "sector", "price_per_mcf", "source"]
        if "series_id" in df.columns:
            cols.insert(cols.index("sector") + 1, "series_id")
        if "price_units" in df.columns:
            cols.append("price_units")

        return df[[c for c in cols if c in df.columns]]

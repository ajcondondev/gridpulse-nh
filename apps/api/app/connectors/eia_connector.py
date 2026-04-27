"""
EIA ISO-NE hourly electricity load connector.

Requires EIA_API_KEY environment variable.
Register free at: https://www.eia.gov/opendata/

TODO: Verify endpoint URL, query parameters, and response schema with a real EIA_API_KEY.
      The endpoint and field mappings below are based on EIA v2 API documentation reviewed
      2026-04-27 but have NOT been confirmed against a live response.
"""

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector


class EIAConnector(BaseConnector):
    source_id = "eia_isone_load"

    # TODO: Confirm this is the correct ISO-NE respondent code in the EIA v2 RTO dataset.
    REGION_CODE = "ISNE"
    BASE_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
    REQUIRED_FETCH_COLUMNS = {"period", "value"}

    def fetch(self) -> dict:
        if not settings.eia_api_key:
            raise ValueError(
                "EIA_API_KEY is not configured. "
                "Register at https://www.eia.gov/opendata/ and set EIA_API_KEY in your .env file."
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)

        # TODO: Verify these parameters produce correct ISO-NE hourly demand data.
        # Reference: https://api.eia.gov/v2/electricity/rto/region-data/data/?api_key=DEMO
        params = {
            "api_key": settings.eia_api_key,
            "frequency": "hourly",
            "data[0]": "value",
            "facets[respondent][]": self.REGION_CODE,
            "facets[type][]": "D",  # D = Demand
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 168,  # one week of hourly data
        }

        response = httpx.get(self.BASE_URL, params=params, timeout=30.0)
        response.raise_for_status()

        payload = response.json()
        response_payload = payload.get("response")
        if not isinstance(response_payload, dict):
            raise ValueError("EIA response missing 'response' object.")

        records = response_payload.get("data", [])
        if not isinstance(records, list) or not records:
            raise ValueError(
                "EIA API returned no data. "
                "Verify the endpoint, region code, and query parameters are correct."
            )

        df = pd.DataFrame(records)
        missing = self.REQUIRED_FETCH_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(
                f"EIA response missing expected columns: {sorted(missing)}. "
                f"Columns found: {list(df.columns)}."
            )

        if df.empty:
            raise ValueError("EIA API returned an empty dataset after parsing.")

        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        # TODO: Confirm EIA v2 RTO region-data column names against a live response.
        # Expected columns: period, respondent, respondent-name, type, type-name,
        #                   value, value-units
        df = pd.read_csv(raw_path)

        rename: dict[str, str] = {}
        if "period" in df.columns:
            rename["period"] = "timestamp"
        if "respondent-name" in df.columns:
            rename["respondent-name"] = "region"
        elif "respondent" in df.columns:
            rename["respondent"] = "region"
        if "value" in df.columns:
            rename["value"] = "demand_mw"

        df = df.rename(columns=rename)

        if "timestamp" not in df.columns or "demand_mw" not in df.columns:
            raise ValueError(
                "EIA response does not contain expected columns after renaming. "
                f"Columns found: {list(df.columns)}. "
                "Verify EIA API response schema."
            )

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
        df["timestamp"] = df["timestamp"].dt.tz_localize(None)
        df["demand_mw"] = pd.to_numeric(df["demand_mw"], errors="coerce")
        df["source"] = "EIA"

        if "region" not in df.columns:
            df["region"] = "ISO-NE"

        df = df.dropna(subset=["timestamp", "demand_mw"])
        df = df[df["demand_mw"] > 0]
        df = df.drop_duplicates(subset=["timestamp"], keep="last")
        df = df.sort_values("timestamp").reset_index(drop=True)

        if df.empty:
            raise ValueError("EIA cleaned dataset is empty after validation.")

        return df[["timestamp", "region", "demand_mw", "source"]]

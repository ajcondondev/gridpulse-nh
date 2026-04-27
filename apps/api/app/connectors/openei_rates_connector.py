import ast
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector


class OpenEIRatesConnector(BaseConnector):
    """OpenEI utility rates connector focused on NH residential price context."""

    source_id = "openei_rates"
    BASE_URL = "https://api.openei.org/utility_rates"
    SEARCH_ADDRESS = "Manchester, NH"
    SEARCH_RADIUS_MILES = 100

    def fetch(self) -> dict:
        params = {
            "version": "latest",
            "format": "json",
            "limit": 25,
            "detail": "full",
            "approved": "true",
            "is_default": "true",
            "sector": "Residential",
            "address": self.SEARCH_ADDRESS,
            "radius": self.SEARCH_RADIUS_MILES,
            "co_limit": 10,
        }
        if settings.openei_api_key:
            params["api_key"] = settings.openei_api_key

        response = httpx.get(self.BASE_URL, params=params, timeout=30.0)
        response.raise_for_status()

        payload = response.json()
        if isinstance(payload, dict):
            error = payload.get("error") or payload.get("errors")
            if error:
                if not settings.openei_api_key:
                    raise ValueError(
                        "OpenEI utility rates request was rejected. "
                        "Public access may be unavailable for this query. "
                        "Set OPENEI_API_KEY in .env and try again."
                    )
                raise ValueError(f"OpenEI utility rates error: {error}")

        items = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(items, list) or not items:
            raise ValueError("OpenEI utility rates returned no rate records.")

        df = pd.DataFrame(items)
        if df.empty:
            raise ValueError("OpenEI utility rates returned an empty dataset after parsing.")

        return {
            "dataframe": df,
            "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0),
            "row_count": len(df),
        }

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)
        required = {"label", "utility", "name", "sector"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"OpenEI utility rates missing expected columns: {sorted(missing)}. "
                f"Columns found: {list(df.columns)}."
            )

        out = pd.DataFrame()
        out["rate_id"] = df["label"]
        out["utility_name"] = df["utility"]
        out["rate_name"] = df["name"]
        out["sector"] = df["sector"]
        out["service_type"] = df["servicetype"] if "servicetype" in df.columns else None
        out["approved"] = self._to_bool_series(df["approved"]) if "approved" in df.columns else None
        out["is_default"] = self._to_bool_series(df["is_default"]) if "is_default" in df.columns else None
        out["start_date"] = self._parse_epoch_series(df["startdate"]) if "startdate" in df.columns else None
        out["end_date"] = self._parse_epoch_series(df["enddate"]) if "enddate" in df.columns else None
        out["fixed_charge"] = pd.to_numeric(df["fixedchargefirstmeter"], errors="coerce") if "fixedchargefirstmeter" in df.columns else None
        out["fixed_charge_units"] = df["fixedchargeunits"] if "fixedchargeunits" in df.columns else None
        out["min_charge"] = pd.to_numeric(df["mincharge"], errors="coerce") if "mincharge" in df.columns else None
        out["min_charge_units"] = df["minchargeunits"] if "minchargeunits" in df.columns else None
        out["energy_rate_kwh"] = df["energyratestructure"].apply(self._extract_first_energy_rate) if "energyratestructure" in df.columns else None
        out["description"] = df["description"] if "description" in df.columns else None
        out["rate_uri"] = df["uri"] if "uri" in df.columns else None
        out["source"] = "OpenEI Utility Rates"

        out = out.dropna(subset=["rate_id", "utility_name", "rate_name"])
        out = out.drop_duplicates(subset=["rate_id"], keep="last").reset_index(drop=True)

        if out.empty:
            raise ValueError("OpenEI cleaned dataset is empty after validation.")

        return out

    @staticmethod
    def _to_bool_series(series: pd.Series) -> pd.Series:
        return series.astype(str).str.lower().map({"true": True, "false": False})

    @staticmethod
    def _parse_epoch_series(series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors="coerce")
        parsed = pd.to_datetime(numeric, unit="s", errors="coerce", utc=True)
        return parsed.dt.tz_localize(None).dt.date

    @staticmethod
    def _extract_first_energy_rate(value) -> float | None:
        if pd.isna(value):
            return None
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                value = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                return None
        if not isinstance(value, list) or not value:
            return None
        first_period = value[0]
        if not isinstance(first_period, list) or not first_period:
            return None
        first_tier = first_period[0]
        if not isinstance(first_tier, dict):
            return None
        rate = first_tier.get("rate")
        try:
            return float(rate) if rate is not None else None
        except (TypeError, ValueError):
            return None

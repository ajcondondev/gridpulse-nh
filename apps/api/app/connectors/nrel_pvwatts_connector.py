from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector

_NH_LOCATIONS = [
    ("Manchester", 43.0481, -71.4637),
    ("Concord", 43.2081, -71.5376),
    ("Portsmouth", 43.0718, -70.7626),
    ("Keene", 42.9339, -72.2779),
]

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# 4 kW DC residential system, fixed roof mount, south-facing 20° tilt, 14% losses
_SYSTEM_CAPACITY_KW = 4.0
_DEFAULT_PARAMS = {
    "system_capacity": _SYSTEM_CAPACITY_KW,
    "losses": 14,
    "array_type": 1,
    "tilt": 20,
    "azimuth": 180,
    "timeframe": "monthly",
    "dataset": "nsrdb",
}


class NRELPVWattsConnector(BaseConnector):
    """NREL PVWatts v8 monthly solar output estimates for key NH locations."""

    source_id = "nrel_pvwatts"
    BASE_URL = "https://developer.nrel.gov/api/pvwatts/v8.json"

    def fetch(self) -> dict:
        api_key = settings.nrel_api_key or "DEMO_KEY"
        now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)

        rows = []
        for location_name, lat, lon in _NH_LOCATIONS:
            params = {
                "api_key": api_key,
                "lat": lat,
                "lon": lon,
                **_DEFAULT_PARAMS,
            }
            response = httpx.get(self.BASE_URL, params=params, timeout=30.0)
            response.raise_for_status()
            payload = response.json()

            errors = payload.get("errors")
            if errors:
                raise ValueError(
                    f"PVWatts API error for {location_name}: {errors}"
                )

            outputs = payload.get("outputs")
            if not outputs:
                raise ValueError(
                    f"PVWatts response missing 'outputs' for {location_name}."
                )

            ac_monthly = outputs.get("ac_monthly", [])
            solrad_monthly = outputs.get("solrad_monthly", [])
            if len(ac_monthly) != 12:
                raise ValueError(
                    f"PVWatts returned {len(ac_monthly)} months (expected 12) for {location_name}."
                )

            for month_idx, (ac, solrad) in enumerate(
                zip(ac_monthly, solrad_monthly if len(solrad_monthly) == 12 else [None] * 12)
            ):
                rows.append({
                    "location_name": location_name,
                    "latitude": lat,
                    "longitude": lon,
                    "month": month_idx + 1,
                    "month_name": _MONTH_NAMES[month_idx],
                    "ac_kwh": ac,
                    "solar_radiation_kwh_m2_day": solrad,
                    "system_capacity_kw": _SYSTEM_CAPACITY_KW,
                })

        if not rows:
            raise ValueError("PVWatts returned no data for any NH location.")

        df = pd.DataFrame(rows)
        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)

        required = ["location_name", "month", "ac_kwh"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(
                f"PVWatts cleaned data missing required columns: {missing}. "
                f"Columns found: {list(df.columns)}."
            )

        df["ac_kwh"] = pd.to_numeric(df["ac_kwh"], errors="coerce")
        df["solar_radiation_kwh_m2_day"] = pd.to_numeric(
            df.get("solar_radiation_kwh_m2_day"), errors="coerce"
        )
        df["month"] = pd.to_numeric(df["month"], errors="coerce").astype("Int64")
        df = df.dropna(subset=["location_name", "month", "ac_kwh"])
        df = df[df["ac_kwh"] >= 0]
        df = df.sort_values(["location_name", "month"]).reset_index(drop=True)
        df["source"] = "NREL PVWatts v8"

        if df.empty:
            raise ValueError("PVWatts cleaned dataset is empty after validation.")

        cols = [
            "location_name", "latitude", "longitude",
            "month", "month_name",
            "ac_kwh", "solar_radiation_kwh_m2_day",
            "system_capacity_kw", "source",
        ]
        return df[[c for c in cols if c in df.columns]]

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector


class AFDCConnector(BaseConnector):
    """NREL Alternative Fuels Data Center EV charging stations in NH."""

    source_id = "afdc_ev"
    ENDPOINT = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"
    REQUIRED_FETCH_COLUMNS = {"station_name", "latitude", "longitude"}

    _CLEAN_COLS = {
        "id": "station_id",
        "station_name": "station_name",
        "city": "city",
        "state": "state",
        "zip": "zip",
        "latitude": "latitude",
        "longitude": "longitude",
        "fuel_type_code": "fuel_type",
        "access_code": "access_code",
        "ev_level1_evse_num": "level1_ports",
        "ev_level2_evse_num": "level2_ports",
        "ev_dc_fast_num": "dc_fast_ports",
    }

    def fetch(self) -> dict:
        api_key = settings.nrel_api_key or "DEMO_KEY"
        params = {
            "api_key": api_key,
            "fuel_type": "ELEC",
            "state": "NH",
            "status": "E",
            "limit": 200,
        }

        response = httpx.get(self.ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        stations = data.get("fuel_stations", [])
        if not isinstance(stations, list):
            raise ValueError("AFDC response missing 'fuel_stations' list.")
        if not stations:
            raise ValueError("AFDC API returned no charging stations for the current query.")

        df = pd.DataFrame(stations)
        missing = self.REQUIRED_FETCH_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(
                f"AFDC response missing expected columns: {sorted(missing)}. "
                f"Columns found: {list(df.columns)}."
            )

        return {
            "dataframe": df,
            "fetched_at": datetime.now(timezone.utc),
            "row_count": len(df),
        }

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path, low_memory=False)

        available = {k: v for k, v in self._CLEAN_COLS.items() if k in df.columns}
        df = df[list(available.keys())].rename(columns=available)

        for port_col in ("level1_ports", "level2_ports", "dc_fast_ports"):
            if port_col in df.columns:
                df[port_col] = df[port_col].fillna(0).astype(int)

        df = df.dropna(subset=["station_name", "latitude", "longitude"])
        if "station_id" in df.columns:
            df = df.drop_duplicates(subset=["station_id"], keep="last")
        else:
            df = df.drop_duplicates(
                subset=["station_name", "city", "state", "latitude", "longitude"],
                keep="last",
            )
        df["source"] = "AFDC NREL"

        df = df.reset_index(drop=True)
        if df.empty:
            raise ValueError("AFDC cleaned dataset is empty after validation.")
        return df

from pathlib import Path
from datetime import datetime, timezone

import httpx
import pandas as pd

from app.connectors.base import BaseConnector
from app.config import settings


class AFDCConnector(BaseConnector):
    """NREL Alternative Fuels Data Center — EV charging stations in NH.

    Uses DEMO_KEY by default (30 req/day). Set NREL_API_KEY for higher limits.
    """

    source_id = "afdc_ev"
    ENDPOINT = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"

    _CLEAN_COLS = {
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
        api_key = settings.nrel_api_key
        if not api_key:
            raise ValueError(
                "NREL_API_KEY is not configured. "
                "Set it in .env — free registration at developer.nrel.gov. "
                "DEMO_KEY also works for low-volume testing."
            )

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
        df = pd.DataFrame(stations) if stations else pd.DataFrame()

        return {"dataframe": df, "fetched_at": datetime.now(timezone.utc)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path, low_memory=False)

        available = {k: v for k, v in self._CLEAN_COLS.items() if k in df.columns}
        df = df[list(available.keys())].rename(columns=available)

        # Port counts arrive as float (NaN for absent) — fill with 0 and cast to int
        for port_col in ("level1_ports", "level2_ports", "dc_fast_ports"):
            if port_col in df.columns:
                df[port_col] = df[port_col].fillna(0).astype(int)

        df = df.dropna(subset=["station_name", "latitude", "longitude"])
        df["source"] = "AFDC NREL"

        return df.reset_index(drop=True)

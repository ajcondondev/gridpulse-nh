"""
NOAA Climate Data Online (CDO) connector for Manchester, NH.

Requires NOAA_TOKEN environment variable.
Request a free token at: https://www.ncdc.noaa.gov/cdo-web/token

TODO: Verify station ID, endpoint, and response schema with a real NOAA_TOKEN.
      Endpoint and field mappings are based on NOAA CDO API v2 documentation reviewed
      2026-04-27 but have NOT been confirmed against a live response.
"""

from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pandas as pd

from app.config import settings
from app.connectors.base import BaseConnector


class NOAAConnector(BaseConnector):
    source_id = "noaa_weather"

    BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
    DATASET_ID = "GHCND"

    # TODO: Confirm this is the correct NOAA GHCND station ID for Manchester, NH.
    # Manchester-Boston Regional Airport — closest high-quality GHCND station.
    STATION_ID = "GHCND:USW00014745"

    DAYS_BACK = 30

    def fetch(self) -> dict:
        if not settings.noaa_token:
            raise ValueError(
                "NOAA_TOKEN is not configured. "
                "Request a free token at https://www.ncdc.noaa.gov/cdo-web/token "
                "and set NOAA_TOKEN in your .env file."
            )

        now = datetime.utcnow().replace(second=0, microsecond=0)
        end_date = now.date()
        start_date = end_date - timedelta(days=self.DAYS_BACK)

        # TODO: Confirm datatypeid values and that units=standard returns Fahrenheit
        #       for GHCND temperature fields (TMAX, TMIN, TAVG).
        params = {
            "datasetid": self.DATASET_ID,
            "stationid": self.STATION_ID,
            "datatypeid": "TMAX,TMIN,TAVG",
            "startdate": str(start_date),
            "enddate": str(end_date),
            "limit": 1000,
            "units": "standard",
        }
        headers = {"token": settings.noaa_token}

        response = httpx.get(self.BASE_URL, params=params, headers=headers, timeout=30.0)
        response.raise_for_status()

        payload = response.json()

        # TODO: Confirm response structure. Expected key: payload["results"]
        results = payload.get("results", [])
        if not results:
            raise ValueError(
                "NOAA API returned no data. "
                "Verify the station ID, date range, and token are correct. "
                f"Station: {self.STATION_ID}, range: {start_date} to {end_date}."
            )

        df = pd.DataFrame(results)
        return {"dataframe": df, "fetched_at": now, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        # TODO: Confirm NOAA CDO GHCND column names match: date, datatype, station, value.
        # Response is long-format (one row per datatype per date).
        # We pivot to wide format and calculate HDD/CDD from TAVG (base 65°F).
        df = pd.read_csv(raw_path)

        required = {"date", "datatype", "station", "value"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"NOAA response missing expected columns: {missing}. "
                f"Columns found: {list(df.columns)}. "
                "Verify NOAA CDO API response schema."
            )

        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        # Pivot long → wide: one row per (date, station), columns per datatype.
        pivot = (
            df.pivot_table(
                index=["date", "station"],
                columns="datatype",
                values="value",
                aggfunc="first",
            )
            .reset_index()
        )
        pivot.columns.name = None

        rename: dict[str, str] = {}
        if "TMAX" in pivot.columns:
            rename["TMAX"] = "temp_max_f"
        if "TMIN" in pivot.columns:
            rename["TMIN"] = "temp_min_f"
        if "TAVG" in pivot.columns:
            rename["TAVG"] = "temp_avg_f"
        pivot = pivot.rename(columns=rename)

        # Estimate temp_avg_f from TMAX/TMIN when TAVG is not reported by the station.
        if "temp_avg_f" not in pivot.columns:
            if "temp_max_f" in pivot.columns and "temp_min_f" in pivot.columns:
                pivot["temp_avg_f"] = (
                    (pivot["temp_max_f"] + pivot["temp_min_f"]) / 2
                ).round(1)
            else:
                pivot["temp_avg_f"] = None

        # Heating/cooling degree days, base 65°F — standard utility planning metric.
        def _hdd(t: float) -> float | None:
            return round(max(0.0, 65.0 - t), 1) if pd.notna(t) else None

        def _cdd(t: float) -> float | None:
            return round(max(0.0, t - 65.0), 1) if pd.notna(t) else None

        pivot["hdd"] = pivot["temp_avg_f"].apply(_hdd)
        pivot["cdd"] = pivot["temp_avg_f"].apply(_cdd)
        pivot["source"] = "NOAA GHCND"

        out_cols = [
            "date", "station",
            "temp_avg_f", "temp_min_f", "temp_max_f",
            "hdd", "cdd", "source",
        ]
        for col in out_cols:
            if col not in pivot.columns:
                pivot[col] = None

        return pivot[out_cols].sort_values("date").reset_index(drop=True)

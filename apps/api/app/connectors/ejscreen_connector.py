"""
EPA EJScreen block-group level environmental justice data for New Hampshire.

Queries the EPA EJScreen ArcGIS Feature Service — same pattern as FEMA flood maps.
No API key required.

Source: U.S. EPA EJScreen 2023
Service: https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/EJScreen_StateBG_2023/FeatureServer/0

TODO: If the ArcGIS Online service URL above changes, check
      https://www.epa.gov/ejscreen/download-ejscreen-data for the current
      hosted service item ID, or fall back to the geoplatform.gov mirror.
      EJScreen field names are stable across 2022-2023; verify after each
      annual data release.
"""

from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

# NH bounding box (WGS84) — same as used by the FEMA connector
_NH_BBOX = "-72.56,42.70,-70.61,45.31"

# EPA ArcGIS Online — EJScreen 2023 block-group feature layer
_QUERY_URL = (
    "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services"
    "/EJScreen_StateBG_2023/FeatureServer/0/query"
)

# Focused field list: block-group identity + key environmental + demographic indicators.
# Full EJScreen has 200+ columns; this subset covers utility-relevant EJ analysis.
_OUT_FIELDS = ",".join([
    "ID",           # 12-digit block group FIPS
    "ST_ABBREV",    # state abbreviation
    "COUNTY",       # county name
    "ACSTOTPOP",    # total population (ACS)
    # Environmental burden percentiles (within-state)
    "P_PM25",       # PM2.5 concentration percentile
    "P_OZONE",      # ozone concentration percentile
    "P_DSLPM",      # diesel particulate matter percentile
    "P_CANCR",      # cancer risk percentile
    "P_RESP",       # respiratory hazard index percentile
    "P_PTRAF",      # traffic proximity percentile
    "P_LDPNT",      # lead paint indicator percentile
    "P_PNPL",       # Superfund site proximity percentile
    "P_PRMP",       # RMP facility proximity percentile
    "P_PTSDF",      # TSD facility proximity percentile
    "P_UST",        # underground storage tanks percentile
    "P_PWDIS",      # wastewater discharge percentile
    # Demographic percentiles (within-state)
    "D_MINORPCT",   # people of color %
    "D_LOWINCPCT",  # low-income %
    "D_LINGISO",    # linguistic isolation %
    "D_UNEMPPCT",   # unemployment %
    "D_UNDER5PCT",  # under-5 population %
    "D_OVER64PCT",  # over-64 population %
])

# Rename map: ArcGIS field → clean column name
_RENAME = {
    "ID": "block_group_fips",
    "ST_ABBREV": "state",
    "COUNTY": "county",
    "ACSTOTPOP": "population",
    "P_PM25": "pm25_pctile",
    "P_OZONE": "ozone_pctile",
    "P_DSLPM": "diesel_pm_pctile",
    "P_CANCR": "cancer_risk_pctile",
    "P_RESP": "resp_hazard_pctile",
    "P_PTRAF": "traffic_pctile",
    "P_LDPNT": "lead_paint_pctile",
    "P_PNPL": "superfund_pctile",
    "P_PRMP": "rmp_facility_pctile",
    "P_PTSDF": "tsd_facility_pctile",
    "P_UST": "storage_tanks_pctile",
    "P_PWDIS": "wastewater_pctile",
    "D_MINORPCT": "people_of_color_pct",
    "D_LOWINCPCT": "low_income_pct",
    "D_LINGISO": "linguistic_isolation_pct",
    "D_UNEMPPCT": "unemployment_pct",
    "D_UNDER5PCT": "under_5_pct",
    "D_OVER64PCT": "over_64_pct",
}

_PCTILE_COLS = [v for v in _RENAME.values() if v.endswith("_pctile")]
_PCT_COLS = [v for v in _RENAME.values() if v.endswith("_pct")]


class EJScreenConnector(BaseConnector):
    """EPA EJScreen 2023 block-group EJ data for New Hampshire."""

    source_id = "epa_ejscreen"

    def fetch(self) -> dict:
        params = {
            "geometry": _NH_BBOX,
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "where": "ST_ABBREV='NH'",
            "outFields": _OUT_FIELDS,
            "returnGeometry": "false",
            "resultRecordCount": "2000",
            "f": "json",
        }

        response = httpx.get(_QUERY_URL, params=params, timeout=60.0)
        response.raise_for_status()

        payload = response.json()

        error = payload.get("error")
        if error:
            raise ValueError(
                f"EPA EJScreen ArcGIS error: {error.get('message', error)}. "
                "If the service URL has changed, update _QUERY_URL in ejscreen_connector.py."
            )

        features = payload.get("features", [])
        if not features:
            raise ValueError(
                "EPA EJScreen returned no block-group features for New Hampshire. "
                "The service may be temporarily unavailable or the URL may need updating."
            )

        records = [f["attributes"] for f in features]
        df = pd.DataFrame(records)

        exceeded = payload.get("exceededTransferLimit", False)

        return {
            "dataframe": df,
            "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0),
            "row_count": len(df),
            "exceeded_transfer_limit": exceeded,
        }

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path, dtype=str)

        if "ID" not in df.columns and "block_group_fips" not in df.columns:
            raise ValueError(
                f"EPA EJScreen raw file missing block group ID column. "
                f"Columns found: {list(df.columns)}. "
                "Verify that the ArcGIS service returned the expected fields."
            )

        # Accept either original ArcGIS field names or already-renamed names
        rename = {k: v for k, v in _RENAME.items() if k in df.columns}
        df = df.rename(columns=rename)

        # Numeric coercion for all indicator columns
        numeric_cols = ["population"] + _PCTILE_COLS + _PCT_COLS
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Clamp percentiles to [0, 100] — EJScreen uses 0–100 scale
        for col in _PCTILE_COLS:
            if col in df.columns:
                df[col] = df[col].clip(0, 100)

        if "state" in df.columns:
            df["state"] = df["state"].astype(str).str.upper().str.strip()

        df["source"] = "EPA EJScreen 2023"
        df["data_year"] = 2023

        df = df.dropna(subset=["block_group_fips"]).reset_index(drop=True)
        df = df[df["block_group_fips"].astype(str).str.strip() != "nan"]

        if df.empty:
            raise ValueError("EPA EJScreen cleaned dataset is empty after validation.")

        ordered = [
            "block_group_fips", "state", "county", "population",
            "pm25_pctile", "ozone_pctile", "diesel_pm_pctile",
            "cancer_risk_pctile", "resp_hazard_pctile",
            "traffic_pctile", "lead_paint_pctile",
            "superfund_pctile", "rmp_facility_pctile", "tsd_facility_pctile",
            "storage_tanks_pctile", "wastewater_pctile",
            "people_of_color_pct", "low_income_pct",
            "linguistic_isolation_pct", "unemployment_pct",
            "under_5_pct", "over_64_pct",
            "source", "data_year",
        ]
        return df[[c for c in ordered if c in df.columns]].sort_values("block_group_fips").reset_index(drop=True)

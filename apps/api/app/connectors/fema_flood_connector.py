from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

# NH bounding box (WGS84)
_NH_BBOX = "-72.56,42.70,-70.61,45.31"

_QUERY_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)

_NH_COUNTY_NAMES = {
    "33001": "Belknap",
    "33003": "Carroll",
    "33005": "Cheshire",
    "33007": "Coos",
    "33009": "Grafton",
    "33011": "Hillsborough",
    "33013": "Merrimack",
    "33015": "Rockingham",
    "33017": "Strafford",
    "33019": "Sullivan",
}


class FEMAFloodConnector(BaseConnector):
    """FEMA National Flood Hazard Layer connector — NH flood zones."""

    source_id = "fema_flood"

    def fetch(self) -> dict:
        params = {
            "geometry": _NH_BBOX,
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "OBJECTID,FLD_ZONE,ZONE_SUBTY,DFIRM_ID,SOURCE_CIT,SFHA_TF",
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": "2000",
        }

        response = httpx.get(_QUERY_URL, params=params, timeout=45.0)
        response.raise_for_status()

        payload = response.json()

        error = payload.get("error")
        if error:
            raise ValueError(f"FEMA NFHL API error: {error.get('message', error)}")

        features = payload.get("features", [])
        if not features:
            raise ValueError(
                "FEMA NFHL returned no flood zone features for New Hampshire. "
                "The service may be temporarily unavailable."
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

        if "FLD_ZONE" not in df.columns:
            raise ValueError(
                f"FEMA flood raw file missing FLD_ZONE column. "
                f"Columns found: {list(df.columns)}."
            )

        out = pd.DataFrame()
        out["feature_id"] = pd.to_numeric(df.get("OBJECTID"), errors="coerce").astype("Int64")
        out["flood_zone"] = df["FLD_ZONE"].str.strip()
        out["zone_subtype"] = df["ZONE_SUBTY"].where(
            df["ZONE_SUBTY"].notna() & (df["ZONE_SUBTY"].str.strip() != ""), other=None
        ) if "ZONE_SUBTY" in df.columns else None
        out["panel_id"] = df["DFIRM_ID"] if "DFIRM_ID" in df.columns else None
        out["county_fips"] = out["panel_id"].str[:5].where(
            out["panel_id"].notna(), other=None
        )
        out["county"] = out["county_fips"].map(_NH_COUNTY_NAMES)
        out["state"] = "NH"
        out["is_sfha"] = (
            df["SFHA_TF"].str.strip().str.upper() == "T"
        ) if "SFHA_TF" in df.columns else None
        out["geometry_type"] = "Polygon"
        out["source"] = "FEMA NFHL"

        out = out.dropna(subset=["flood_zone"])
        out = out.reset_index(drop=True)

        if out.empty:
            raise ValueError("FEMA flood cleaned dataset is empty after validation.")

        return out

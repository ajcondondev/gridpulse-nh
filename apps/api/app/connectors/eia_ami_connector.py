"""
EIA Form 861 Advanced Metering Infrastructure (AMI) data.

Public annual survey of smart meter deployment by utility and state.
No API key required. Downloads a ZIP from EIA and parses the AMI Excel file.

Source: U.S. Energy Information Administration — Form EIA-861
URL: https://www.eia.gov/electricity/data/eia861/

TODO: Verify column names and header-row offset against the downloaded Excel for
      each survey year. EIA 861 column layout shifts slightly between releases.
"""

from datetime import datetime, timezone
import io
import zipfile
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector

_FORM_861_BASE = "https://www.eia.gov/electricity/data/eia861/zip"
_TRY_YEARS = [2024, 2023, 2022]


def _normalize_col(col: str) -> str:
    return col.strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def _find_col(df: pd.DataFrame, keywords: list[str], exclude: list[str] | None = None) -> str | None:
    """Return the first column whose normalized name contains ALL keywords."""
    for col in df.columns:
        norm = col.lower()
        if all(kw in norm for kw in keywords):
            if exclude and any(ex in norm for ex in exclude):
                continue
            return col
    return None


def _parse_ami_excel(xls_bytes: bytes, year: int) -> pd.DataFrame:
    """
    Parse the Advanced_Meters Excel file. Tries header rows 0, 1, and 2
    to handle EIA 861 files that include a title row before column headers.
    """
    for header_row in (0, 1, 2):
        try:
            df = pd.read_excel(
                io.BytesIO(xls_bytes),
                engine="openpyxl",
                header=header_row,
                dtype=str,
            )
            cols_lower = [str(c).lower() for c in df.columns]
            if any("utility" in c or "state" in c or "customer" in c for c in cols_lower):
                df.columns = [str(c) for c in df.columns]
                return df
        except Exception:
            continue
    raise ValueError(
        f"Could not parse Advanced_Meters_{year}.xlsx — "
        "unrecognized column structure. Inspect the file and update header_row."
    )


class EIAAMIConnector(BaseConnector):
    """
    EIA Form 861 AMI deployment data for NH utilities.

    Tries survey years 2024 → 2023 → 2022. Returns NH rows only.
    Requires openpyxl (already in requirements).
    """

    source_id = "eia_ami"

    def fetch(self) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
        last_err: Exception | None = None

        for year in _TRY_YEARS:
            url = f"{_FORM_861_BASE}/f861{year}.zip"
            try:
                response = httpx.get(url, timeout=90.0, follow_redirects=True)
                response.raise_for_status()
            except Exception as exc:
                last_err = exc
                continue

            try:
                with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                    ami_candidates = [
                        name for name in zf.namelist()
                        if "advanced_meters" in name.lower() and name.lower().endswith(".xlsx")
                    ]
                    if not ami_candidates:
                        last_err = ValueError(
                            f"EIA 861 {year} ZIP has no Advanced_Meters Excel file. "
                            f"Files found: {zf.namelist()[:20]}"
                        )
                        continue

                    with zf.open(ami_candidates[0]) as f:
                        xls_bytes = f.read()

                df = _parse_ami_excel(xls_bytes, year)

                state_col = _find_col(df, ["state"])
                if state_col:
                    df_nh = df[df[state_col].astype(str).str.upper() == "NH"].copy()
                else:
                    df_nh = df.copy()

                if df_nh.empty:
                    last_err = ValueError(
                        f"EIA 861 {year} AMI parsed but no NH rows found "
                        f"(state column detected as: {state_col!r}). "
                        "Verify the state column name in the Excel file."
                    )
                    continue

                df_nh["_data_year"] = str(year)
                return {
                    "dataframe": df_nh,
                    "fetched_at": now,
                    "row_count": len(df_nh),
                    "data_year": year,
                }

            except Exception as exc:
                last_err = exc
                continue

        raise ValueError(
            f"EIA Form 861 AMI fetch failed for all years {_TRY_YEARS}. "
            f"Last error: {last_err}"
        )

    def clean(self, raw_path: Path) -> pd.DataFrame:
        # TODO: Verify column discovery against a live downloaded file.
        # EIA 861 column names shift between survey years; keyword matching
        # below handles known variants but may need updating for new releases.
        df = pd.read_csv(raw_path, low_memory=False, dtype=str)
        df.columns = [_normalize_col(str(c)) for c in df.columns]

        utility_name_col = _find_col(df, ["utility", "name"])
        state_col = _find_col(df, ["state"])
        ownership_col = _find_col(df, ["ownership"]) or _find_col(df, ["owner"])
        service_type_col = _find_col(df, ["service"])
        year_col = (
            _find_col(df, ["data_year"])
            or _find_col(df, ["year"])
            or ("_data_year" if "_data_year" in df.columns else None)
        )

        # AMI customer count: prefer a column containing both "ami" and "customer"
        ami_cust_col = _find_col(df, ["ami", "customer"])
        if ami_cust_col is None:
            ami_cust_col = _find_col(df, ["advanced", "meter"])

        # Total customers: find a column with "customer" that is NOT the AMI one
        total_cust_col = _find_col(df, ["customer", "total"])
        if total_cust_col is None:
            for col in df.columns:
                if "customer" in col and "ami" not in col and "advanced" not in col:
                    total_cust_col = col
                    break

        missing = [
            label for label, col in [("utility_name", utility_name_col), ("state", state_col)]
            if col is None
        ]
        if missing:
            raise ValueError(
                f"EIA 861 AMI cleaned data missing required columns: {missing}. "
                f"Columns found: {list(df.columns)}. "
                "Verify the Advanced_Meters Excel file layout and update column keyword mappings."
            )

        out = pd.DataFrame()
        out["utility_name"] = df[utility_name_col].astype(str).str.strip()
        out["state"] = df[state_col].astype(str).str.upper().str.strip()

        if year_col and year_col in df.columns:
            out["data_year"] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
        else:
            out["data_year"] = pd.NA

        out["ownership"] = df[ownership_col].astype(str).str.strip() if ownership_col else pd.NA
        out["service_type"] = df[service_type_col].astype(str).str.strip() if service_type_col else pd.NA

        out["total_customers"] = (
            pd.to_numeric(df[total_cust_col], errors="coerce").astype("Int64")
            if total_cust_col else pd.NA
        )
        out["ami_customers"] = (
            pd.to_numeric(df[ami_cust_col], errors="coerce").astype("Int64")
            if ami_cust_col else pd.NA
        )

        if total_cust_col and ami_cust_col:
            with pd.option_context("mode.use_inf_as_na", True):
                out["ami_pct"] = (
                    out["ami_customers"].astype(float) / out["total_customers"].astype(float) * 100
                ).round(2)
        else:
            out["ami_pct"] = pd.NA

        out["source"] = "EIA Form 861"

        out = out[out["state"] == "NH"].copy()
        out = out[out["utility_name"].str.lower() != "nan"].dropna(subset=["utility_name"])
        out = out.reset_index(drop=True)

        if out.empty:
            raise ValueError(
                "EIA 861 AMI cleaned dataset is empty after NH filter and validation. "
                "Verify state column mapping and that NH utility rows are present."
            )

        return out.sort_values("utility_name").reset_index(drop=True)

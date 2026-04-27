import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx
import pandas as pd

from app.connectors.base import BaseConnector


class EGridConnector(BaseConnector):
    """EPA eGRID emissions connector using the public summary data table."""

    source_id = "epa_egrid"
    BASE_URL = "https://www.epa.gov/egrid/summary-data"

    def fetch(self) -> dict:
        response = httpx.get(self.BASE_URL, timeout=30.0)
        response.raise_for_status()

        html = response.text
        if not html.strip():
            raise ValueError("EPA eGRID summary data returned an empty response body.")

        table = self._extract_subregion_table(html)
        year_match = re.search(r"eGRID with (\d{4}) Data", html)
        table["data_year"] = int(year_match.group(1)) if year_match else None

        if table.empty:
            raise ValueError("EPA eGRID summary data returned no rows after parsing.")

        return {
            "dataframe": table,
            "fetched_at": datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0),
            "row_count": len(table),
        }

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)
        required = {
            "eGRID Subregion",
            "CO2",
            "CH4",
            "N2O",
            "CO2e",
            "Annual NOX",
            "Ozone Season NOX",
            "SO2",
        }
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"EPA eGRID summary data missing expected columns: {sorted(missing)}. "
                f"Columns found: {list(df.columns)}."
            )

        out = pd.DataFrame()
        out["subregion"] = df["eGRID Subregion"]
        out["co2_lb_per_mwh"] = pd.to_numeric(df["CO2"], errors="coerce")
        out["ch4_lb_per_mwh"] = pd.to_numeric(df["CH4"], errors="coerce")
        out["n2o_lb_per_mwh"] = pd.to_numeric(df["N2O"], errors="coerce")
        out["co2e_lb_per_mwh"] = pd.to_numeric(df["CO2e"], errors="coerce")
        out["annual_nox_lb_per_mwh"] = pd.to_numeric(df["Annual NOX"], errors="coerce")
        out["ozone_season_nox_lb_per_mwh"] = pd.to_numeric(df["Ozone Season NOX"], errors="coerce")
        out["so2_lb_per_mwh"] = pd.to_numeric(df["SO2"], errors="coerce")
        out["data_year"] = pd.to_numeric(df["data_year"], errors="coerce") if "data_year" in df.columns else None
        out["source"] = "EPA eGRID"

        out = out.dropna(subset=["subregion", "co2e_lb_per_mwh"])
        out = out.drop_duplicates(subset=["subregion"], keep="last").reset_index(drop=True)

        if out.empty:
            raise ValueError("EPA eGRID cleaned dataset is empty after validation.")

        return out

    @staticmethod
    def _extract_subregion_table(html: str) -> pd.DataFrame:
        parser = _HTMLTableParser()
        parser.feed(html)
        for rows in parser.tables:
            if not rows:
                continue
            headers = [str(cell).strip() for cell in rows[0]]
            if "eGRID Subregion" in headers and "CO2e" in headers:
                data_rows = [row for row in rows[1:] if len(row) == len(headers)]
                return pd.DataFrame(data_rows, columns=headers)
        raise ValueError("EPA eGRID summary page did not contain the expected subregion emissions table.")


class _HTMLTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._current_table = []
        elif tag == "tr" and self._current_table is not None:
            self._current_row = []
        elif tag in {"th", "td"} and self._current_row is not None:
            self._current_cell = []

    def handle_data(self, data):
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"th", "td"} and self._current_row is not None and self._current_cell is not None:
            value = "".join(self._current_cell).strip()
            self._current_row.append(value)
            self._current_cell = None
        elif tag == "tr" and self._current_table is not None and self._current_row is not None:
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = None
        elif tag == "table" and self._current_table is not None:
            self.tables.append(self._current_table)
            self._current_table = None

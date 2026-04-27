"""Tests for the CDC SVI connector and its fetch route."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.connectors.cdc_svi_connector import CDCSVIConnector
from app.main import app

client = TestClient(app)

_CSV_HEADER = (
    "ST,STATE,ST_ABBR,STCNTY,COUNTY,FIPS,LOCATION,"
    "RPL_THEMES,RPL_THEME1,RPL_THEME2,RPL_THEME3,RPL_THEME4,E_TOTPOP"
)
_CSV_ROW1 = "33,New Hampshire,NH,33011,Hillsborough,33011010100,Tract 101,0.45,0.30,0.55,0.20,0.60,4200"
_CSV_ROW2 = "33,New Hampshire,NH,33013,Merrimack,33013020100,Tract 201,0.72,0.80,0.65,0.40,0.85,3100"
_CSV_NODATA = "33,New Hampshire,NH,33007,Coos,33007030100,Tract 301,-999,-999,-999,-999,-999,0"

_CSV_CONTENT = "\n".join([_CSV_HEADER, _CSV_ROW1, _CSV_ROW2, _CSV_NODATA])


def _mock_response(text: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.content = text.encode("utf-8")
    return mock


def test_fetch_returns_dataframe():
    with patch("app.connectors.cdc_svi_connector.httpx.get", return_value=_mock_response(_CSV_CONTENT)):
        result = CDCSVIConnector().fetch()

    assert result["row_count"] == 3
    assert "FIPS" in result["dataframe"].columns
    assert "RPL_THEMES" in result["dataframe"].columns


def test_fetch_raises_on_empty_response():
    with patch(
        "app.connectors.cdc_svi_connector.httpx.get",
        return_value=_mock_response(_CSV_HEADER),
    ):
        with pytest.raises(ValueError, match="empty dataset"):
            CDCSVIConnector().fetch()


def test_fetch_raises_on_missing_columns():
    bad_csv = "COL_A,COL_B\n1,2\n"
    with patch(
        "app.connectors.cdc_svi_connector.httpx.get",
        return_value=_mock_response(bad_csv),
    ):
        with pytest.raises(ValueError, match="missing expected columns"):
            CDCSVIConnector().fetch()


def test_clean_column_mapping(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text(_CSV_CONTENT)

    df = CDCSVIConnector().clean(raw_csv)

    assert set(df.columns) >= {
        "year",
        "state",
        "county",
        "fips",
        "location_name",
        "svi_overall_percentile",
        "socioeconomic_percentile",
        "household_characteristics_percentile",
        "racial_ethnic_minority_percentile",
        "housing_transportation_percentile",
        "source",
    }
    assert df.loc[0, "county"] == "Hillsborough"
    assert df.loc[0, "fips"] == "33011010100"


def test_clean_replaces_nodata_with_nan(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text(_CSV_CONTENT)

    df = CDCSVIConnector().clean(raw_csv)

    nodata_row = df[df["fips"] == "33007030100"]
    assert len(nodata_row) == 1
    assert pd.isna(nodata_row.iloc[0]["svi_overall_percentile"])
    assert pd.isna(nodata_row.iloc[0]["socioeconomic_percentile"])


def test_clean_normal_percentiles_preserved(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text(_CSV_CONTENT)

    df = CDCSVIConnector().clean(raw_csv)

    row = df[df["fips"] == "33011010100"].iloc[0]
    assert abs(row["svi_overall_percentile"] - 0.45) < 1e-6
    assert abs(row["housing_transportation_percentile"] - 0.60) < 1e-6


def test_clean_source_label(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    raw_csv.write_text(_CSV_CONTENT)

    df = CDCSVIConnector().clean(raw_csv)

    assert df["source"].iloc[0] == "CDC/ATSDR SVI 2022"


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.cdc_svi_connector.httpx.get",
        return_value=_mock_response(_CSV_CONTENT),
    ):
        response = client.post("/sources/cdc_svi/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "cdc_svi"
    assert data["row_count"] == 3
    assert "fips" in data["columns"]
    assert "svi_overall_percentile" in data["columns"]


def test_fetch_route_returns_502_on_http_error(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    import httpx as _httpx

    mock = MagicMock()
    mock.raise_for_status.side_effect = _httpx.HTTPStatusError(
        "503", request=MagicMock(), response=MagicMock()
    )
    with patch("app.connectors.cdc_svi_connector.httpx.get", return_value=mock):
        response = client.post("/sources/cdc_svi/fetch")

    assert response.status_code == 502

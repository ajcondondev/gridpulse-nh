"""Tests for the NH Geodata connector and its fetch route."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.connectors.nh_geodata_connector import NHGeodataConnector
from app.main import app

client = TestClient(app)

_CENSUS_RESPONSE = [
    ["NAME", "P1_001N", "state", "county", "county subdivision"],
    ["Manchester city, Hillsborough County, New Hampshire", "115644", "33", "011", "46140"],
    ["Concord city, Merrimack County, New Hampshire", "43976", "33", "013", "14200"],
    ["Nashua city, Hillsborough County, New Hampshire", "91322", "33", "011", "50260"],
]


def _mock_response(payload) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = payload
    return mock


def test_fetch_returns_dataframe():
    with patch(
        "app.connectors.nh_geodata_connector.httpx.get",
        return_value=_mock_response(_CENSUS_RESPONSE),
    ):
        result = NHGeodataConnector().fetch()

    assert result["row_count"] == 3
    assert "NAME" in result["dataframe"].columns
    assert "P1_001N" in result["dataframe"].columns


def test_fetch_raises_on_non_list_response():
    with patch(
        "app.connectors.nh_geodata_connector.httpx.get",
        return_value=_mock_response({"error": "bad"}),
    ):
        with pytest.raises(ValueError, match="unexpected response"):
            NHGeodataConnector().fetch()


def test_fetch_raises_on_empty_rows():
    headers = ["NAME", "P1_001N", "state", "county", "county subdivision"]
    with patch(
        "app.connectors.nh_geodata_connector.httpx.get",
        return_value=_mock_response([headers]),
    ):
        with pytest.raises(ValueError, match="no NH county subdivisions"):
            NHGeodataConnector().fetch()


def test_clean_column_mapping(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    headers = _CENSUS_RESPONSE[0]
    rows = _CENSUS_RESPONSE[1:]
    pd.DataFrame(rows, columns=headers).to_csv(raw_csv, index=False)

    df = NHGeodataConnector().clean(raw_csv)

    assert set(df.columns) >= {
        "town_name",
        "county_name",
        "state",
        "state_fips",
        "county_fips",
        "town_fips",
        "population_2020",
        "source",
    }
    assert df.loc[0, "town_name"] == "Manchester city"
    assert df.loc[0, "county_name"] == "Hillsborough"
    assert df.loc[0, "state"] == "NH"
    assert df.loc[0, "county_fips"] == "33011"


def test_clean_population_is_int(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    headers = _CENSUS_RESPONSE[0]
    pd.DataFrame(_CENSUS_RESPONSE[1:], columns=headers).to_csv(raw_csv, index=False)

    df = NHGeodataConnector().clean(raw_csv)

    assert df.loc[0, "population_2020"] == 115644
    assert df.loc[1, "population_2020"] == 43976


def test_clean_town_fips_format(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_CENSUS_RESPONSE[1:], columns=_CENSUS_RESPONSE[0]).to_csv(raw_csv, index=False)

    df = NHGeodataConnector().clean(raw_csv)

    # state(2) + county(3) + subdivision(5) = 10 chars
    assert len(df.loc[0, "town_fips"]) == 10
    assert df.loc[0, "town_fips"] == "3301146140"


def test_clean_source_label(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_CENSUS_RESPONSE[1:], columns=_CENSUS_RESPONSE[0]).to_csv(raw_csv, index=False)

    df = NHGeodataConnector().clean(raw_csv)

    assert df["source"].iloc[0] == "US Census Bureau 2020 Decennial"


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.nh_geodata_connector.httpx.get",
        return_value=_mock_response(_CENSUS_RESPONSE),
    ):
        response = client.post("/sources/nh_geodata/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "nh_geodata"
    assert data["row_count"] == 3
    assert "town_name" in data["columns"]
    assert "population_2020" in data["columns"]


def test_fetch_route_returns_422_on_bad_response(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.nh_geodata_connector.httpx.get",
        return_value=_mock_response({"error": "bad"}),
    ):
        response = client.post("/sources/nh_geodata/fetch")

    assert response.status_code == 422
    assert "unexpected response" in response.json()["detail"]

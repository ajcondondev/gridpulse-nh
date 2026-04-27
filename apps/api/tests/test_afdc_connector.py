"""Tests for the AFDC EV connector and its fetch route."""
import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.afdc_connector import AFDCConnector
from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Minimal station fixture — keys match the AFDC API response schema
# ---------------------------------------------------------------------------
_STATION = {
    "station_name": "Concord Fast Charge",
    "city": "Concord",
    "state": "NH",
    "zip": "03301",
    "latitude": 43.2081,
    "longitude": -71.5376,
    "fuel_type_code": "ELEC",
    "access_code": "public",
    "ev_level1_evse_num": None,
    "ev_level2_evse_num": 4.0,
    "ev_dc_fast_num": 2.0,
}


def _mock_response(stations: list[dict]) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {"fuel_stations": stations}
    return mock


# ---------------------------------------------------------------------------
# Unit tests — connector
# ---------------------------------------------------------------------------


def test_missing_nrel_key_raises_value_error(monkeypatch):
    monkeypatch.setattr(config.settings, "nrel_api_key", "")
    with pytest.raises(ValueError, match="NREL_API_KEY"):
        AFDCConnector().fetch()


def test_fetch_returns_dataframe(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "nrel_api_key", "DEMO_KEY")
    with patch("app.connectors.afdc_connector.httpx.get", return_value=_mock_response([_STATION])):
        result = AFDCConnector().fetch()
    assert "dataframe" in result
    assert "fetched_at" in result
    df = result["dataframe"]
    assert len(df) == 1
    assert "station_name" in df.columns


def test_clean_column_mapping(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_STATION]).to_csv(raw_csv, index=False)

    df = AFDCConnector().clean(raw_csv)
    expected = {"station_name", "city", "state", "latitude", "longitude",
                "fuel_type", "access_code", "level2_ports", "dc_fast_ports", "source"}
    assert expected.issubset(set(df.columns))
    assert df.loc[0, "fuel_type"] == "ELEC"
    assert df.loc[0, "source"] == "AFDC NREL"


def test_clean_port_counts_are_int(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_STATION]).to_csv(raw_csv, index=False)
    df = AFDCConnector().clean(raw_csv)
    assert df.loc[0, "level2_ports"] == 4
    assert df.loc[0, "dc_fast_ports"] == 2
    assert df.loc[0, "level1_ports"] == 0


def test_clean_drops_missing_coords(tmp_path):
    bad = {**_STATION, "latitude": None, "longitude": None}
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_STATION, bad]).to_csv(raw_csv, index=False)
    df = AFDCConnector().clean(raw_csv)
    assert len(df) == 1


def test_clean_drops_missing_station_name(tmp_path):
    bad = {**_STATION, "station_name": None}
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_STATION, bad]).to_csv(raw_csv, index=False)
    df = AFDCConnector().clean(raw_csv)
    assert len(df) == 1


# ---------------------------------------------------------------------------
# Route-level tests
# ---------------------------------------------------------------------------


def test_fetch_route_missing_key_returns_422(monkeypatch):
    monkeypatch.setattr(config.settings, "nrel_api_key", "")
    response = client.post("/sources/afdc_ev/fetch")
    assert response.status_code == 422
    assert "NREL_API_KEY" in response.json()["detail"]


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "nrel_api_key", "DEMO_KEY")
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch("app.connectors.afdc_connector.httpx.get", return_value=_mock_response([_STATION])):
        response = client.post("/sources/afdc_ev/fetch")
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "afdc_ev"
    assert data["row_count"] == 1
    assert "station_name" in data["columns"]

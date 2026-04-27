"""Tests for the AFDC EV connector and its fetch route."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.afdc_connector import AFDCConnector
from app.main import app

client = TestClient(app)

_STATION = {
    "id": 101,
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


def _mock_response(stations) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {"fuel_stations": stations}
    return mock


def test_fetch_uses_demo_key_when_setting_blank(monkeypatch):
    monkeypatch.setattr(config.settings, "nrel_api_key", "")
    captured = {}

    def _fake_get(url, params, timeout):
        captured["params"] = params
        return _mock_response([_STATION])

    with patch("app.connectors.afdc_connector.httpx.get", side_effect=_fake_get):
        result = AFDCConnector().fetch()

    assert result["row_count"] == 1
    assert captured["params"]["api_key"] == "DEMO_KEY"


def test_fetch_raises_on_empty_station_list(monkeypatch):
    monkeypatch.setattr(config.settings, "nrel_api_key", "DEMO_KEY")
    with patch("app.connectors.afdc_connector.httpx.get", return_value=_mock_response([])):
        with pytest.raises(ValueError, match="returned no charging stations"):
            AFDCConnector().fetch()


def test_clean_column_mapping(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_STATION]).to_csv(raw_csv, index=False)

    df = AFDCConnector().clean(raw_csv)
    expected = {
        "station_id",
        "station_name",
        "city",
        "state",
        "latitude",
        "longitude",
        "fuel_type",
        "access_code",
        "level2_ports",
        "dc_fast_ports",
        "source",
    }
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


def test_clean_deduplicates_station_id(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    updated = {**_STATION, "station_name": "Concord Fast Charge Updated"}
    pd.DataFrame([_STATION, updated]).to_csv(raw_csv, index=False)

    df = AFDCConnector().clean(raw_csv)

    assert len(df) == 1
    assert df.loc[0, "station_name"] == "Concord Fast Charge Updated"


def test_clean_drops_missing_station_name(tmp_path):
    bad = {**_STATION, "station_name": None}
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_STATION, bad]).to_csv(raw_csv, index=False)
    df = AFDCConnector().clean(raw_csv)
    assert len(df) == 1


def test_fetch_route_uses_demo_key_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "nrel_api_key", "")
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch("app.connectors.afdc_connector.httpx.get", return_value=_mock_response([_STATION])):
        response = client.post("/sources/afdc_ev/fetch")
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "afdc_ev"
    assert data["row_count"] == 1
    assert "station_name" in data["columns"]


def test_fetch_route_returns_422_for_empty_station_list(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "nrel_api_key", "DEMO_KEY")
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch("app.connectors.afdc_connector.httpx.get", return_value=_mock_response([])):
        response = client.post("/sources/afdc_ev/fetch")
    assert response.status_code == 422
    assert "charging stations" in response.json()["detail"]

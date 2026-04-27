from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.nrel_pvwatts_connector import NRELPVWattsConnector
from app.main import app

client = TestClient(app)

_AC_MONTHLY = [300, 350, 500, 600, 680, 700, 710, 680, 580, 460, 300, 260]
_SOLRAD_MONTHLY = [2.5, 3.1, 4.2, 5.0, 5.6, 5.8, 5.9, 5.5, 4.6, 3.5, 2.4, 2.1]

_PVWATTS_RESPONSE = {
    "outputs": {
        "ac_monthly": _AC_MONTHLY,
        "solrad_monthly": _SOLRAD_MONTHLY,
        "ac_annual": sum(_AC_MONTHLY),
        "solrad_annual": 4.3,
        "capacity_factor": 15.2,
    },
    "station_info": {"lat": 43.05, "lon": -71.46, "elev": 55},
    "errors": [],
}


def _mock_response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = payload
    return mock


def test_connector_has_correct_source_id():
    assert NRELPVWattsConnector.source_id == "nrel_pvwatts"


def test_fetch_returns_dataframe_with_all_locations():
    with patch(
        "app.connectors.nrel_pvwatts_connector.httpx.get",
        return_value=_mock_response(_PVWATTS_RESPONSE),
    ):
        result = NRELPVWattsConnector().fetch()

    assert "dataframe" in result
    # 4 locations × 12 months = 48 rows
    assert result["row_count"] == 48
    df = result["dataframe"]
    assert "location_name" in df.columns
    assert "ac_kwh" in df.columns
    assert set(df["location_name"].unique()) == {"Manchester", "Concord", "Portsmouth", "Keene"}


def test_fetch_raises_on_api_error():
    error_response = {"outputs": {}, "errors": ["Invalid API key"]}
    with patch(
        "app.connectors.nrel_pvwatts_connector.httpx.get",
        return_value=_mock_response(error_response),
    ):
        with pytest.raises(ValueError, match="PVWatts API error"):
            NRELPVWattsConnector().fetch()


def test_fetch_raises_on_missing_outputs():
    with patch(
        "app.connectors.nrel_pvwatts_connector.httpx.get",
        return_value=_mock_response({}),
    ):
        with pytest.raises(ValueError, match="missing 'outputs'"):
            NRELPVWattsConnector().fetch()


def test_fetch_raises_on_wrong_month_count():
    bad_response = {
        "outputs": {"ac_monthly": [100, 200], "solrad_monthly": [3.0, 4.0]},
        "errors": [],
    }
    with patch(
        "app.connectors.nrel_pvwatts_connector.httpx.get",
        return_value=_mock_response(bad_response),
    ):
        with pytest.raises(ValueError, match="12"):
            NRELPVWattsConnector().fetch()


def test_clean_output_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    rows = [
        {
            "location_name": "Manchester", "latitude": 43.05, "longitude": -71.46,
            "month": m + 1, "month_name": f"Month{m+1}",
            "ac_kwh": _AC_MONTHLY[m], "solar_radiation_kwh_m2_day": _SOLRAD_MONTHLY[m],
            "system_capacity_kw": 4.0,
        }
        for m in range(12)
    ]
    pd.DataFrame(rows).to_csv(raw_csv, index=False)

    df = NRELPVWattsConnector().clean(raw_csv)

    assert "location_name" in df.columns
    assert "month" in df.columns
    assert "ac_kwh" in df.columns
    assert "source" in df.columns
    assert len(df) == 12


def test_clean_source_label(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    rows = [
        {"location_name": "Concord", "month": m + 1, "month_name": "M",
         "ac_kwh": 400.0, "system_capacity_kw": 4.0}
        for m in range(12)
    ]
    pd.DataFrame(rows).to_csv(raw_csv, index=False)

    df = NRELPVWattsConnector().clean(raw_csv)
    assert (df["source"] == "NREL PVWatts v8").all()


def test_clean_raises_on_missing_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"foo": 1}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        NRELPVWattsConnector().clean(raw_csv)


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.nrel_pvwatts_connector.httpx.get",
        return_value=_mock_response(_PVWATTS_RESPONSE),
    ):
        response = client.post("/sources/nrel_pvwatts/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "nrel_pvwatts"
    assert data["row_count"] == 48
    assert "ac_kwh" in data["columns"]
    assert "location_name" in data["columns"]


def test_fetch_route_returns_502_on_api_error(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    error_response = {"outputs": {}, "errors": ["Invalid key"]}
    with patch(
        "app.connectors.nrel_pvwatts_connector.httpx.get",
        return_value=_mock_response(error_response),
    ):
        response = client.post("/sources/nrel_pvwatts/fetch")

    assert response.status_code == 422

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.openei_rates_connector import OpenEIRatesConnector
from app.main import app

client = TestClient(app)

_ITEM = {
    "label": "rate-1",
    "utility": "Public Service Company of New Hampshire",
    "name": "Residential Default Service",
    "sector": "Residential",
    "servicetype": "Bundled",
    "approved": True,
    "is_default": True,
    "startdate": 1704067200,
    "enddate": 1735689600,
    "fixedchargefirstmeter": 15.25,
    "fixedchargeunits": "$/month",
    "mincharge": 10.00,
    "minchargeunits": "$/month",
    "energyratestructure": [[{"rate": 0.1423}]],
    "description": "Sample default rate",
    "uri": "https://apps.openei.org/USURDB/rate/view/rate-1",
}


def _mock_json_response(payload) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = payload
    return mock


def test_connector_has_correct_source_id():
    assert OpenEIRatesConnector.source_id == "openei_rates"


def test_fetch_returns_dataframe(monkeypatch):
    monkeypatch.setattr(config.settings, "openei_api_key", "")
    with patch(
        "app.connectors.openei_rates_connector.httpx.get",
        return_value=_mock_json_response({"items": [_ITEM]}),
    ):
        result = OpenEIRatesConnector().fetch()

    assert result["row_count"] == 1
    assert "utility" in result["dataframe"].columns


def test_fetch_raises_clear_error_when_service_demands_key(monkeypatch):
    monkeypatch.setattr(config.settings, "openei_api_key", "")
    with patch(
        "app.connectors.openei_rates_connector.httpx.get",
        return_value=_mock_json_response({"error": "api_key required"}),
    ):
        with pytest.raises(ValueError, match="OPENEI_API_KEY"):
            OpenEIRatesConnector().fetch()


def test_fetch_raises_on_empty_items(monkeypatch):
    monkeypatch.setattr(config.settings, "openei_api_key", "key")
    with patch(
        "app.connectors.openei_rates_connector.httpx.get",
        return_value=_mock_json_response({"items": []}),
    ):
        with pytest.raises(ValueError, match="returned no rate records"):
            OpenEIRatesConnector().fetch()


def test_clean_maps_price_context_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_ITEM]).to_csv(raw_csv, index=False)

    df = OpenEIRatesConnector().clean(raw_csv)

    assert "utility_name" in df.columns
    assert df.loc[0, "energy_rate_kwh"] == 0.1423
    assert df.loc[0, "fixed_charge"] == 15.25
    assert df.loc[0, "source"] == "OpenEI Utility Rates"


def test_clean_raises_on_missing_expected_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"utility": "Foo"}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="missing expected columns"):
        OpenEIRatesConnector().clean(raw_csv)


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    monkeypatch.setattr(config.settings, "openei_api_key", "")
    with patch(
        "app.connectors.openei_rates_connector.httpx.get",
        return_value=_mock_json_response({"items": [_ITEM]}),
    ):
        response = client.post("/sources/openei_rates/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "openei_rates"
    assert data["row_count"] == 1
    assert "energy_rate_kwh" in data["columns"]


def test_fetch_route_returns_422_for_rejected_request(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    monkeypatch.setattr(config.settings, "openei_api_key", "")
    with patch(
        "app.connectors.openei_rates_connector.httpx.get",
        return_value=_mock_json_response({"error": "api_key required"}),
    ):
        response = client.post("/sources/openei_rates/fetch")

    assert response.status_code == 422
    assert "OPENEI_API_KEY" in response.json()["detail"]

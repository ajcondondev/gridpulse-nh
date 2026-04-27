from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.eia_retail_prices_connector import EIARetailPricesConnector
from app.main import app

client = TestClient(app)

_API_RESPONSE = {
    "response": {
        "total": 4,
        "data": [
            {"period": "2024-01", "stateid": "NH", "stateDescription": "New Hampshire",
             "sectorid": "RES", "sectorName": "residential", "price": 21.12,
             "price-units": "cents per kilowatthour"},
            {"period": "2024-01", "stateid": "NH", "stateDescription": "New Hampshire",
             "sectorid": "COM", "sectorName": "commercial", "price": 17.45,
             "price-units": "cents per kilowatthour"},
            {"period": "2023-12", "stateid": "NH", "stateDescription": "New Hampshire",
             "sectorid": "RES", "sectorName": "residential", "price": 20.88,
             "price-units": "cents per kilowatthour"},
            {"period": "2023-12", "stateid": "NH", "stateDescription": "New Hampshire",
             "sectorid": "IND", "sectorName": "industrial", "price": 13.02,
             "price-units": "cents per kilowatthour"},
        ],
    }
}

_RAW_ROWS = [
    {"period": "2024-01", "stateid": "NH", "stateDescription": "New Hampshire",
     "sectorid": "RES", "sectorName": "residential", "price": 21.12},
    {"period": "2024-01", "stateid": "NH", "stateDescription": "New Hampshire",
     "sectorid": "COM", "sectorName": "commercial", "price": 17.45},
    {"period": "2023-12", "stateid": "NH", "stateDescription": "New Hampshire",
     "sectorid": "IND", "sectorName": "industrial", "price": 13.02},
]


def _mock_response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = payload
    return mock


def test_connector_has_correct_source_id():
    assert EIARetailPricesConnector.source_id == "eia_retail_prices"


def test_fetch_raises_without_api_key(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "")
    with pytest.raises(ValueError, match="EIA_API_KEY is not configured"):
        EIARetailPricesConnector().fetch()


def test_fetch_returns_dataframe(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "test_key")
    with patch(
        "app.connectors.eia_retail_prices_connector.httpx.get",
        return_value=_mock_response(_API_RESPONSE),
    ):
        result = EIARetailPricesConnector().fetch()

    assert "dataframe" in result
    assert result["row_count"] == 4
    assert "period" in result["dataframe"].columns


def test_fetch_raises_on_missing_response_key(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "test_key")
    with patch(
        "app.connectors.eia_retail_prices_connector.httpx.get",
        return_value=_mock_response({"bad": "payload"}),
    ):
        with pytest.raises(ValueError, match="missing 'response'"):
            EIARetailPricesConnector().fetch()


def test_fetch_raises_on_empty_data(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "test_key")
    with patch(
        "app.connectors.eia_retail_prices_connector.httpx.get",
        return_value=_mock_response({"response": {"data": []}}),
    ):
        with pytest.raises(ValueError, match="returned no data"):
            EIARetailPricesConnector().fetch()


def test_clean_output_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = EIARetailPricesConnector().clean(raw_csv)

    assert list(df.columns) == [
        "period", "state", "sector_id", "sector_name", "price_cents_per_kwh", "source"
    ]


def test_clean_renames_stateid(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = EIARetailPricesConnector().clean(raw_csv)
    assert (df["state"] == "NH").all()


def test_clean_renames_sectorid(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = EIARetailPricesConnector().clean(raw_csv)
    assert "RES" in df["sector_id"].values
    assert "COM" in df["sector_id"].values


def test_clean_source_label(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = EIARetailPricesConnector().clean(raw_csv)
    assert (df["source"] == "EIA Retail Sales").all()


def test_clean_drops_zero_prices(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([
        {"period": "2024-01", "stateid": "NH", "sectorid": "RES",
         "sectorName": "residential", "price": 0.0},
        {"period": "2024-01", "stateid": "NH", "sectorid": "COM",
         "sectorName": "commercial", "price": 17.45},
    ]).to_csv(raw_csv, index=False)

    df = EIARetailPricesConnector().clean(raw_csv)
    assert len(df) == 1
    assert df.iloc[0]["sector_id"] == "COM"


def test_clean_raises_on_missing_price_column(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"period": "2024-01", "stateid": "NH"}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="missing expected columns"):
        EIARetailPricesConnector().clean(raw_csv)


def test_fetch_route_returns_422_without_key(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "eia_api_key", "")
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    response = client.post("/sources/eia_retail_prices/fetch")
    assert response.status_code == 422
    assert "EIA_API_KEY" in response.json()["detail"]


def test_fetch_route_returns_dataset_with_key(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "eia_api_key", "test_key")
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.eia_retail_prices_connector.httpx.get",
        return_value=_mock_response(_API_RESPONSE),
    ):
        response = client.post("/sources/eia_retail_prices/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "eia_retail_prices"
    assert data["row_count"] == 4
    assert "price_cents_per_kwh" in data["columns"]

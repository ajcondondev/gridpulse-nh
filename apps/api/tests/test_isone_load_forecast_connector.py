from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.isone_load_forecast_connector import ISONELoadForecastConnector
from app.main import app

client = TestClient(app)

_FORECAST_CSV = (
    "Date,Hour Ending,Net Load Forecast (MW)\n"
    "2026-04-26,1,13500\n"
    "2026-04-26,2,13200\n"
    "2026-04-26,3,13100\n"
)

_RAW_ROWS = [
    {"Date": "2026-04-26", "Hour Ending": "1", "Net Load Forecast (MW)": "13500"},
    {"Date": "2026-04-26", "Hour Ending": "2", "Net Load Forecast (MW)": "13200"},
]


def _mock_response(body: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.text = body
    return mock


def test_connector_has_correct_source_id():
    assert ISONELoadForecastConnector.source_id == "isone_load_forecast"


def test_fetch_returns_dataframe():
    with patch(
        "app.connectors.isone_load_forecast_connector.httpx.get",
        return_value=_mock_response(_FORECAST_CSV),
    ):
        result = ISONELoadForecastConnector().fetch()

    assert "dataframe" in result
    assert result["row_count"] == 3
    assert "Date" in result["dataframe"].columns


def test_fetch_raises_on_empty_body():
    with patch(
        "app.connectors.isone_load_forecast_connector.httpx.get",
        return_value=_mock_response(""),
    ):
        with pytest.raises(ValueError, match="empty response"):
            ISONELoadForecastConnector().fetch()


def test_clean_output_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONELoadForecastConnector().clean(raw_csv)

    assert list(df.columns) == ["timestamp", "date", "hour_ending", "load_forecast_mw", "source"]


def test_clean_row_count(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONELoadForecastConnector().clean(raw_csv)
    assert len(df) == 2


def test_clean_timestamp_offset(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONELoadForecastConnector().clean(raw_csv)
    assert df.iloc[0]["timestamp"].hour == 0
    assert df.iloc[1]["timestamp"].hour == 1


def test_clean_source_label(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONELoadForecastConnector().clean(raw_csv)
    assert (df["source"] == "ISO-NE Load Forecast").all()


def test_clean_handles_he_prefix(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([
        {"Date": "2026-04-26", "HE": "HE4", "Forecast": "14000"},
    ]).to_csv(raw_csv, index=False)

    df = ISONELoadForecastConnector().clean(raw_csv)
    assert len(df) == 1
    assert df.iloc[0]["hour_ending"] == 4
    assert df.iloc[0]["load_forecast_mw"] == 14000.0


def test_clean_drops_zero_values(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([
        {"Date": "2026-04-26", "Hour Ending": "1", "Net Load Forecast (MW)": "0"},
        {"Date": "2026-04-26", "Hour Ending": "2", "Net Load Forecast (MW)": "13200"},
    ]).to_csv(raw_csv, index=False)

    df = ISONELoadForecastConnector().clean(raw_csv)
    assert len(df) == 1
    assert df.iloc[0]["load_forecast_mw"] == 13200.0


def test_clean_raises_on_missing_date_or_hour_column(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"Forecast": "13000"}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="missing date or hour"):
        ISONELoadForecastConnector().clean(raw_csv)


def test_clean_raises_on_no_forecast_column(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"Date": "2026-04-26", "Hour Ending": "1"}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="could not identify a forecast"):
        ISONELoadForecastConnector().clean(raw_csv)


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.isone_load_forecast_connector.httpx.get",
        return_value=_mock_response(_FORECAST_CSV),
    ):
        response = client.post("/sources/isone_load_forecast/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "isone_load_forecast"
    assert data["row_count"] == 3
    assert "timestamp" in data["columns"]
    assert "load_forecast_mw" in data["columns"]


def test_fetch_route_returns_422_on_bad_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.isone_load_forecast_connector.httpx.get",
        return_value=_mock_response("foo,bar\n1,2\n"),
    ):
        response = client.post("/sources/isone_load_forecast/fetch")

    assert response.status_code == 422

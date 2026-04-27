from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.isone_csv_connector import ISONECSVConnector
from app.main import app

client = TestClient(app)

_RAW_ROWS = [
    {"Date": "2026-04-26", "Hour Ending": "1", "Native Demand": "10000"},
    {"Date": "2026-04-26", "Hour Ending": "2", "Native Demand": "10100"},
]


def _mock_csv_response(body: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.text = body
    return mock


def test_connector_has_correct_source_id():
    assert ISONECSVConnector.source_id == "isone_csv"


def test_fetch_returns_dataframe():
    csv_text = "Date,Hour Ending,Native Demand\n2026-04-26,1,10000\n2026-04-26,2,10100\n"
    with patch(
        "app.connectors.isone_csv_connector.httpx.get",
        return_value=_mock_csv_response(csv_text),
    ):
        result = ISONECSVConnector().fetch()

    assert "dataframe" in result
    assert result["row_count"] == 2
    assert "Date" in result["dataframe"].columns


def test_fetch_raises_on_empty_body():
    with patch(
        "app.connectors.isone_csv_connector.httpx.get",
        return_value=_mock_csv_response(""),
    ):
        with pytest.raises(ValueError, match="empty response body"):
            ISONECSVConnector().fetch()


def test_clean_maps_columns_and_hour_ending(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONECSVConnector().clean(raw_csv)

    assert list(df.columns) == ["timestamp", "region", "demand_mw", "source"]
    assert df.loc[0, "region"] == "ISO-NE"
    assert df.loc[0, "source"] == "ISO-NE CSV"
    assert df.loc[0, "timestamp"].hour == 0
    assert df.loc[1, "timestamp"].hour == 1


def test_clean_deduplicates_timestamp_and_drops_invalid_rows(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(
        [
            {"Date": "2026-04-26", "Hour Ending": "HE1", "Native Demand": "10000"},
            {"Date": "2026-04-26", "Hour Ending": "1", "Native Demand": "10100"},
            {"Date": "bad-date", "Hour Ending": "2", "Native Demand": "10050"},
            {"Date": "2026-04-26", "Hour Ending": "25", "Native Demand": "10025"},
        ]
    ).to_csv(raw_csv, index=False)

    df = ISONECSVConnector().clean(raw_csv)

    assert len(df) == 1
    assert df.loc[0, "demand_mw"] == 10100


def test_clean_raises_on_missing_expected_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"foo": 1, "bar": 2}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="missing expected columns"):
        ISONECSVConnector().clean(raw_csv)


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    csv_text = "Date,Hour Ending,Native Demand\n2026-04-26,1,10000\n2026-04-26,2,10100\n"
    with patch(
        "app.connectors.isone_csv_connector.httpx.get",
        return_value=_mock_csv_response(csv_text),
    ):
        response = client.post("/sources/isone_csv/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "isone_csv"
    assert data["row_count"] == 2
    assert "timestamp" in data["columns"]


def test_fetch_route_returns_422_on_bad_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    csv_text = "foo,bar\n1,2\n"
    with patch(
        "app.connectors.isone_csv_connector.httpx.get",
        return_value=_mock_csv_response(csv_text),
    ):
        response = client.post("/sources/isone_csv/fetch")

    assert response.status_code == 422
    assert "missing expected columns" in response.json()["detail"]

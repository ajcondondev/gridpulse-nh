from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.isone_fuel_mix_connector import ISONEFuelMixConnector
from app.main import app

client = TestClient(app)

_FUEL_MIX_CSV = (
    "Date,Hour Ending,Natural Gas,Nuclear,Hydro,Wind,Solar\n"
    "2026-04-26,1,4000,2500,300,200,0\n"
    "2026-04-26,2,4100,2500,310,210,0\n"
)

_RAW_ROWS = [
    {"Date": "2026-04-26", "Hour Ending": "1", "Natural Gas": "4000", "Nuclear": "2500"},
    {"Date": "2026-04-26", "Hour Ending": "2", "Natural Gas": "4100", "Nuclear": "2500"},
]


def _mock_response(body: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.text = body
    return mock


def test_connector_has_correct_source_id():
    assert ISONEFuelMixConnector.source_id == "isone_fuel_mix"


def test_fetch_returns_dataframe():
    with patch(
        "app.connectors.isone_fuel_mix_connector.httpx.get",
        return_value=_mock_response(_FUEL_MIX_CSV),
    ):
        result = ISONEFuelMixConnector().fetch()

    assert "dataframe" in result
    assert result["row_count"] == 2
    assert "Date" in result["dataframe"].columns


def test_fetch_raises_on_empty_body():
    with patch(
        "app.connectors.isone_fuel_mix_connector.httpx.get",
        return_value=_mock_response(""),
    ):
        with pytest.raises(ValueError, match="empty response"):
            ISONEFuelMixConnector().fetch()


def test_clean_produces_long_format(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONEFuelMixConnector().clean(raw_csv)

    assert list(df.columns) == ["timestamp", "date", "hour_ending", "fuel_type", "value", "unit", "source"]
    fuel_types = df["fuel_type"].unique().tolist()
    assert "Natural Gas" in fuel_types
    assert "Nuclear" in fuel_types
    # 2 hours × 2 fuel types = 4 rows
    assert len(df) == 4


def test_clean_timestamp_offset(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONEFuelMixConnector().clean(raw_csv)
    # Hour Ending 1 → timestamp hour = 0 (midnight)
    # Hour Ending 2 → timestamp hour = 1
    he1 = df[df["hour_ending"] == 1].iloc[0]
    he2 = df[df["hour_ending"] == 2].iloc[0]
    assert he1["timestamp"].hour == 0
    assert he2["timestamp"].hour == 1


def test_clean_unit_is_mw(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONEFuelMixConnector().clean(raw_csv)
    assert (df["unit"] == "MW").all()


def test_clean_source_label(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(_RAW_ROWS).to_csv(raw_csv, index=False)

    df = ISONEFuelMixConnector().clean(raw_csv)
    assert (df["source"] == "ISO-NE Gen Fuel Mix").all()


def test_clean_drops_negative_values(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([
        {"Date": "2026-04-26", "Hour Ending": "1", "Natural Gas": "-100"},
        {"Date": "2026-04-26", "Hour Ending": "2", "Natural Gas": "4000"},
    ]).to_csv(raw_csv, index=False)

    df = ISONEFuelMixConnector().clean(raw_csv)
    assert (df["value"] >= 0).all()
    assert len(df) == 1


def test_clean_handles_he_prefix_hour(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([
        {"Date": "2026-04-26", "Hour Ending": "HE3", "Natural Gas": "4200"},
    ]).to_csv(raw_csv, index=False)

    df = ISONEFuelMixConnector().clean(raw_csv)
    assert len(df) == 1
    assert df.iloc[0]["hour_ending"] == 3


def test_clean_raises_on_missing_date_or_hour_column(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"Natural Gas": "4000", "Nuclear": "2500"}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="missing date or hour"):
        ISONEFuelMixConnector().clean(raw_csv)


def test_clean_raises_on_no_fuel_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"Date": "2026-04-26", "Hour Ending": "1"}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="could not identify any fuel"):
        ISONEFuelMixConnector().clean(raw_csv)


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.isone_fuel_mix_connector.httpx.get",
        return_value=_mock_response(_FUEL_MIX_CSV),
    ):
        response = client.post("/sources/isone_fuel_mix/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "isone_fuel_mix"
    assert data["row_count"] > 0
    assert "timestamp" in data["columns"]
    assert "fuel_type" in data["columns"]


def test_fetch_route_returns_422_on_bad_csv(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.isone_fuel_mix_connector.httpx.get",
        return_value=_mock_response("foo,bar\n1,2\n"),
    ):
        response = client.post("/sources/isone_fuel_mix/fetch")

    assert response.status_code == 422

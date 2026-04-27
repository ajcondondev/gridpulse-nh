"""Tests for the FEMA Flood connector and its fetch route."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.connectors.fema_flood_connector import FEMAFloodConnector
from app.main import app

client = TestClient(app)

_FEATURE_AE = {
    "OBJECTID": 1001,
    "FLD_ZONE": "AE",
    "ZONE_SUBTY": "FLOODWAY",
    "DFIRM_ID": "33011C0001A",
    "SOURCE_CIT": "STUDY1",
    "SFHA_TF": "T",
}
_FEATURE_X = {
    "OBJECTID": 1002,
    "FLD_ZONE": "X",
    "ZONE_SUBTY": "",
    "DFIRM_ID": "33015C0002B",
    "SOURCE_CIT": "STUDY2",
    "SFHA_TF": "F",
}


def _mock_response(features, exceeded=False) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {
        "features": [{"attributes": f} for f in features],
        "exceededTransferLimit": exceeded,
    }
    return mock


def test_fetch_returns_dataframe():
    with patch(
        "app.connectors.fema_flood_connector.httpx.get",
        return_value=_mock_response([_FEATURE_AE, _FEATURE_X]),
    ):
        result = FEMAFloodConnector().fetch()

    assert result["row_count"] == 2
    assert "FLD_ZONE" in result["dataframe"].columns


def test_fetch_raises_on_empty_features():
    with patch(
        "app.connectors.fema_flood_connector.httpx.get",
        return_value=_mock_response([]),
    ):
        with pytest.raises(ValueError, match="no flood zone features"):
            FEMAFloodConnector().fetch()


def test_fetch_raises_on_api_error():
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {"error": {"message": "Service unavailable", "code": 503}}

    with patch("app.connectors.fema_flood_connector.httpx.get", return_value=mock):
        with pytest.raises(ValueError, match="FEMA NFHL API error"):
            FEMAFloodConnector().fetch()


def test_fetch_records_exceeded_transfer_limit():
    with patch(
        "app.connectors.fema_flood_connector.httpx.get",
        return_value=_mock_response([_FEATURE_AE], exceeded=True),
    ):
        result = FEMAFloodConnector().fetch()

    assert result["exceeded_transfer_limit"] is True


def test_clean_column_mapping(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_FEATURE_AE, _FEATURE_X]).to_csv(raw_csv, index=False)

    df = FEMAFloodConnector().clean(raw_csv)

    assert set(df.columns) >= {
        "feature_id",
        "flood_zone",
        "zone_subtype",
        "county_fips",
        "county",
        "state",
        "is_sfha",
        "geometry_type",
        "source",
    }
    assert df.loc[0, "flood_zone"] == "AE"
    assert df.loc[0, "county"] == "Hillsborough"
    assert df.loc[0, "state"] == "NH"
    assert df.loc[0, "geometry_type"] == "Polygon"
    assert df.loc[0, "source"] == "FEMA NFHL"


def test_clean_sfha_flag(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_FEATURE_AE, _FEATURE_X]).to_csv(raw_csv, index=False)

    df = FEMAFloodConnector().clean(raw_csv)

    assert df.loc[0, "is_sfha"] == True  # noqa: E712 — numpy bool comparison
    assert df.loc[1, "is_sfha"] == False  # noqa: E712


def test_clean_county_lookup(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_FEATURE_X]).to_csv(raw_csv, index=False)

    df = FEMAFloodConnector().clean(raw_csv)

    assert df.loc[0, "county_fips"] == "33015"
    assert df.loc[0, "county"] == "Rockingham"


def test_clean_empty_zone_subtype_becomes_none(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([_FEATURE_X]).to_csv(raw_csv, index=False)

    df = FEMAFloodConnector().clean(raw_csv)

    assert df.loc[0, "zone_subtype"] is None or pd.isna(df.loc[0, "zone_subtype"])


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.fema_flood_connector.httpx.get",
        return_value=_mock_response([_FEATURE_AE, _FEATURE_X]),
    ):
        response = client.post("/sources/fema_flood/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "fema_flood"
    assert data["row_count"] == 2
    assert "flood_zone" in data["columns"]
    assert "county" in data["columns"]


def test_fetch_route_returns_422_on_empty_features(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.fema_flood_connector.httpx.get",
        return_value=_mock_response([]),
    ):
        response = client.post("/sources/fema_flood/fetch")

    assert response.status_code == 422
    assert "flood zone features" in response.json()["detail"]

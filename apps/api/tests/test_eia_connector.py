import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app import config
from app.connectors.eia_connector import EIAConnector


def test_connector_has_correct_source_id():
    assert EIAConnector.source_id == "eia_isone_load"


def test_fetch_raises_value_error_when_no_api_key(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "")
    connector = EIAConnector()
    with pytest.raises(ValueError, match="EIA_API_KEY"):
        connector.fetch()


def test_fetch_error_message_includes_registration_url(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "")
    connector = EIAConnector()
    with pytest.raises(ValueError) as exc:
        connector.fetch()
    assert "eia.gov" in str(exc.value).lower()


def test_fetch_source_endpoint_returns_422_without_key(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setattr(config.settings, "eia_api_key", "")
    client = TestClient(app)
    res = client.post("/sources/eia_isone_load/fetch")
    assert res.status_code == 422
    assert "EIA_API_KEY" in res.json()["detail"]


def test_clean_raises_on_missing_expected_columns(tmp_path):
    connector = EIAConnector()
    bad_csv = tmp_path / "bad.csv"
    pd.DataFrame({"unknown_col_a": [1, 2], "unknown_col_b": [3, 4]}).to_csv(bad_csv, index=False)
    with pytest.raises(ValueError, match="expected columns"):
        connector.clean(bad_csv)


def test_clean_maps_eia_columns_correctly(tmp_path):
    connector = EIAConnector()
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(
        {
            "period": ["2026-04-27T00", "2026-04-27T01"],
            "respondent": ["ISNE", "ISNE"],
            "respondent-name": ["ISO New England", "ISO New England"],
            "type": ["D", "D"],
            "type-name": ["Demand", "Demand"],
            "value": [12000, 11500],
            "value-units": ["megawatthours", "megawatthours"],
        }
    ).to_csv(raw_csv, index=False)

    df = connector.clean(raw_csv)

    assert list(df.columns) == ["timestamp", "region", "demand_mw", "source"]
    assert df["source"].iloc[0] == "EIA"
    assert df["region"].iloc[0] == "ISO New England"
    assert df["demand_mw"].iloc[0] == 12000
    assert df["timestamp"].dtype.kind == "M"  # datetime


def test_clean_drops_zero_and_null_demand(tmp_path):
    connector = EIAConnector()
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(
        {
            "period": ["2026-04-27T00", "2026-04-27T01", "2026-04-27T02"],
            "respondent-name": ["ISO New England"] * 3,
            "value": [0, None, 12000],
        }
    ).to_csv(raw_csv, index=False)

    df = connector.clean(raw_csv)
    assert len(df) == 1
    assert df["demand_mw"].iloc[0] == 12000


def _mock_response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = payload
    return mock


def test_fetch_raises_on_missing_records(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "test-key")
    with patch(
        "app.connectors.eia_connector.httpx.get",
        return_value=_mock_response({"response": {"data": []}}),
    ):
        with pytest.raises(ValueError, match="returned no data"):
            EIAConnector().fetch()


def test_fetch_raises_on_missing_columns(monkeypatch):
    monkeypatch.setattr(config.settings, "eia_api_key", "test-key")
    with patch(
        "app.connectors.eia_connector.httpx.get",
        return_value=_mock_response({"response": {"data": [{"period": "2026-04-27T00"}]}}),
    ):
        with pytest.raises(ValueError, match="missing expected columns"):
            EIAConnector().fetch()


def test_clean_deduplicates_duplicate_timestamps(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(
        {
            "period": ["2026-04-27T00", "2026-04-27T00", "bad-timestamp"],
            "respondent-name": ["ISO New England", "ISO New England", "ISO New England"],
            "value": [11000, 12000, 13000],
        }
    ).to_csv(raw_csv, index=False)

    df = EIAConnector().clean(raw_csv)

    assert len(df) == 1
    assert df["demand_mw"].iloc[0] == 12000

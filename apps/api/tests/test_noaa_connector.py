import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app import config
from app.connectors.noaa_connector import NOAAConnector


def test_connector_has_correct_source_id():
    assert NOAAConnector.source_id == "noaa_weather"


def test_fetch_raises_value_error_when_no_token(monkeypatch):
    monkeypatch.setattr(config.settings, "noaa_token", "")
    connector = NOAAConnector()
    with pytest.raises(ValueError, match="NOAA_TOKEN"):
        connector.fetch()


def test_fetch_error_message_includes_token_url(monkeypatch):
    monkeypatch.setattr(config.settings, "noaa_token", "")
    connector = NOAAConnector()
    with pytest.raises(ValueError) as exc:
        connector.fetch()
    assert "ncdc.noaa.gov" in str(exc.value).lower()


def test_fetch_source_endpoint_returns_422_without_token(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setattr(config.settings, "noaa_token", "")
    client = TestClient(app)
    res = client.post("/sources/noaa_weather/fetch")
    assert res.status_code == 422
    assert "NOAA_TOKEN" in res.json()["detail"]


def test_clean_raises_on_missing_columns(tmp_path):
    connector = NOAAConnector()
    bad_csv = tmp_path / "bad.csv"
    pd.DataFrame({"col_a": [1, 2], "col_b": [3, 4]}).to_csv(bad_csv, index=False)
    with pytest.raises(ValueError, match="missing expected columns"):
        connector.clean(bad_csv)


def _write_raw(tmp_path, rows: list[dict]) -> object:
    p = tmp_path / "raw.csv"
    pd.DataFrame(rows).to_csv(p, index=False)
    return p


def test_clean_pivots_and_maps_columns(tmp_path):
    raw = _write_raw(tmp_path, [
        {"date": "2026-04-26T00:00:00", "datatype": "TMAX", "station": "GHCND:USW00014745", "attributes": ",,S,", "value": 72},
        {"date": "2026-04-26T00:00:00", "datatype": "TMIN", "station": "GHCND:USW00014745", "attributes": ",,S,", "value": 54},
        {"date": "2026-04-26T00:00:00", "datatype": "TAVG", "station": "GHCND:USW00014745", "attributes": ",,S,", "value": 63},
    ])

    df = NOAAConnector().clean(raw)

    assert list(df.columns) == [
        "date", "station", "temp_avg_f", "temp_min_f", "temp_max_f", "hdd", "cdd", "source"
    ]
    assert df["temp_avg_f"].iloc[0] == 63
    assert df["temp_min_f"].iloc[0] == 54
    assert df["temp_max_f"].iloc[0] == 72
    assert df["source"].iloc[0] == "NOAA GHCND"


def test_clean_calculates_hdd_and_cdd(tmp_path):
    raw = _write_raw(tmp_path, [
        {"date": "2026-01-15T00:00:00", "datatype": "TAVG", "station": "GHCND:USW00014745", "attributes": "", "value": 30},
        {"date": "2026-07-15T00:00:00", "datatype": "TAVG", "station": "GHCND:USW00014745", "attributes": "", "value": 80},
    ])

    df = NOAAConnector().clean(raw).reset_index(drop=True)

    # 30°F avg → HDD = 35, CDD = 0
    assert df["hdd"].iloc[0] == 35.0
    assert df["cdd"].iloc[0] == 0.0

    # 80°F avg → HDD = 0, CDD = 15
    assert df["hdd"].iloc[1] == 0.0
    assert df["cdd"].iloc[1] == 15.0


def test_clean_estimates_avg_from_tmax_tmin_when_tavg_missing(tmp_path):
    raw = _write_raw(tmp_path, [
        {"date": "2026-04-26T00:00:00", "datatype": "TMAX", "station": "GHCND:USW00014745", "attributes": "", "value": 70},
        {"date": "2026-04-26T00:00:00", "datatype": "TMIN", "station": "GHCND:USW00014745", "attributes": "", "value": 50},
    ])

    df = NOAAConnector().clean(raw)

    assert df["temp_avg_f"].iloc[0] == 60.0


def test_clean_multiple_days_sorted(tmp_path):
    raw = _write_raw(tmp_path, [
        {"date": "2026-04-27T00:00:00", "datatype": "TAVG", "station": "GHCND:USW00014745", "attributes": "", "value": 68},
        {"date": "2026-04-26T00:00:00", "datatype": "TAVG", "station": "GHCND:USW00014745", "attributes": "", "value": 55},
    ])

    df = NOAAConnector().clean(raw)

    dates = list(df["date"])
    assert dates == sorted(dates)
    assert len(df) == 2


def _mock_response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = payload
    return mock


def test_fetch_raises_on_empty_results(monkeypatch):
    monkeypatch.setattr(config.settings, "noaa_token", "token")
    with patch(
        "app.connectors.noaa_connector.httpx.get",
        return_value=_mock_response({"results": []}),
    ):
        with pytest.raises(ValueError, match="returned no data"):
            NOAAConnector().fetch()


def test_fetch_raises_on_missing_columns(monkeypatch):
    monkeypatch.setattr(config.settings, "noaa_token", "token")
    with patch(
        "app.connectors.noaa_connector.httpx.get",
        return_value=_mock_response({"results": [{"date": "2026-04-26"}]}),
    ):
        with pytest.raises(ValueError, match="missing expected columns"):
            NOAAConnector().fetch()


def test_clean_drops_invalid_rows_and_deduplicates(tmp_path):
    raw = _write_raw(tmp_path, [
        {"date": "bad-date", "datatype": "TAVG", "station": "GHCND:USW00014745", "value": 50},
        {"date": "2026-04-26T00:00:00", "datatype": "TAVG", "station": "GHCND:USW00014745", "value": 60},
        {"date": "2026-04-26T00:00:00", "datatype": "TAVG", "station": "GHCND:USW00014745", "value": 61},
    ])

    df = NOAAConnector().clean(raw)

    assert len(df) == 1
    assert df["temp_avg_f"].iloc[0] == 60

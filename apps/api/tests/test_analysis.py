from datetime import datetime

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dataset import Dataset
from app.services import dataset_service, storage_service

client = TestClient(app)


def _configure_temp_data(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))


def _write_dataset(source_id: str, dataset_id: str, fetched_at: datetime, df: pd.DataFrame):
    filename = f"{dataset_id}.csv"
    cleaned_path = storage_service.cleaned_path(source_id, filename)
    df.to_csv(cleaned_path, index=False)
    dataset_service.save_dataset(
        Dataset(
            id=dataset_id,
            source_id=source_id,
            name=dataset_id,
            fetched_at=fetched_at,
            row_count=len(df),
            columns=list(df.columns),
            cleaned_path=str(cleaned_path),
            status="ready",
        )
    )


def test_create_join_returns_dataset_for_mock_fallback(monkeypatch, tmp_path):
    _configure_temp_data(monkeypatch, tmp_path)
    res = client.post("/sources/mock_demand/fetch")
    assert res.status_code == 200

    join_res = client.post("/analysis/weather-demand/join")
    assert join_res.status_code == 200
    data = join_res.json()
    assert data["source_id"] == "weather_demand_analysis"
    assert data["status"] == "ready"
    assert data["row_count"] == 7


def test_join_prefers_latest_eia_over_mock(monkeypatch, tmp_path):
    _configure_temp_data(monkeypatch, tmp_path)
    _write_dataset(
        "mock_demand",
        "mock_old",
        datetime(2026, 4, 20, 12, 0, 0),
        pd.DataFrame(
            {
                "timestamp": ["2026-04-20T00:00:00", "2026-04-20T01:00:00"],
                "region": ["ISO-NE Mock", "ISO-NE Mock"],
                "demand_mw": [1000, 1100],
                "source": ["Mock", "Mock"],
                "pulled_at": ["2026-04-20T12:00:00", "2026-04-20T12:00:00"],
            }
        ),
    )
    _write_dataset(
        "eia_isone_load",
        "eia_new",
        datetime(2026, 4, 21, 12, 0, 0),
        pd.DataFrame(
            {
                "timestamp": ["2026-04-21T00:00:00", "2026-04-21T01:00:00"],
                "region": ["ISO New England", "ISO New England"],
                "demand_mw": [12000, 12100],
                "source": ["EIA", "EIA"],
                "pulled_at": ["2026-04-21T12:00:00", "2026-04-21T12:00:00"],
            }
        ),
    )
    _write_dataset(
        "noaa_weather",
        "noaa_new",
        datetime(2026, 4, 21, 13, 0, 0),
        pd.DataFrame(
            {
                "date": ["2026-04-21"],
                "station": ["GHCND:USW00014745"],
                "temp_avg_f": [58.0],
                "temp_min_f": [48.0],
                "temp_max_f": [68.0],
                "hdd": [7.0],
                "cdd": [0.0],
                "source": ["NOAA GHCND"],
                "pulled_at": ["2026-04-21T13:00:00"],
            }
        ),
    )

    join_res = client.post("/analysis/weather-demand/join")
    assert join_res.status_code == 200

    join_id = join_res.json()["id"]
    preview = client.get(f"/datasets/{join_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["rows"][0]["demand_source"] == "EIA"


def test_join_prefers_isone_csv_over_eia(monkeypatch, tmp_path):
    _configure_temp_data(monkeypatch, tmp_path)
    _write_dataset(
        "eia_isone_load",
        "eia_new",
        datetime(2026, 4, 21, 12, 0, 0),
        pd.DataFrame(
            {
                "timestamp": ["2026-04-21T00:00:00"],
                "region": ["ISO New England"],
                "demand_mw": [12000],
                "source": ["EIA"],
                "pulled_at": ["2026-04-21T12:00:00"],
            }
        ),
    )
    _write_dataset(
        "isone_csv",
        "isone_new",
        datetime(2026, 4, 21, 12, 30, 0),
        pd.DataFrame(
            {
                "timestamp": ["2026-04-21T00:00:00"],
                "region": ["ISO-NE"],
                "demand_mw": [12500],
                "source": ["ISO-NE CSV"],
                "pulled_at": ["2026-04-21T12:30:00"],
            }
        ),
    )
    _write_dataset(
        "noaa_weather",
        "noaa_new",
        datetime(2026, 4, 21, 13, 0, 0),
        pd.DataFrame(
            {
                "date": ["2026-04-21"],
                "station": ["GHCND:USW00014745"],
                "temp_avg_f": [58.0],
                "temp_min_f": [48.0],
                "temp_max_f": [68.0],
                "hdd": [7.0],
                "cdd": [0.0],
                "source": ["NOAA GHCND"],
                "pulled_at": ["2026-04-21T13:00:00"],
            }
        ),
    )

    join_res = client.post("/analysis/weather-demand/join")
    assert join_res.status_code == 200

    join_id = join_res.json()["id"]
    preview = client.get(f"/datasets/{join_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["rows"][0]["demand_source"] == "ISO-NE CSV"


def test_live_join_requires_noaa_when_using_eia(monkeypatch, tmp_path):
    _configure_temp_data(monkeypatch, tmp_path)
    _write_dataset(
        "eia_isone_load",
        "eia_only",
        datetime(2026, 4, 21, 12, 0, 0),
        pd.DataFrame(
            {
                "timestamp": ["2026-04-21T00:00:00"],
                "region": ["ISO New England"],
                "demand_mw": [12000],
                "source": ["EIA"],
                "pulled_at": ["2026-04-21T12:00:00"],
            }
        ),
    )

    res = client.post("/analysis/weather-demand/join")
    assert res.status_code == 422
    assert "Fetch NOAA Weather" in res.json()["detail"]


def test_live_join_fails_when_no_date_overlap(monkeypatch, tmp_path):
    _configure_temp_data(monkeypatch, tmp_path)
    _write_dataset(
        "eia_isone_load",
        "eia_only",
        datetime(2026, 4, 21, 12, 0, 0),
        pd.DataFrame(
            {
                "timestamp": ["2026-04-21T00:00:00"],
                "region": ["ISO New England"],
                "demand_mw": [12000],
                "source": ["EIA"],
                "pulled_at": ["2026-04-21T12:00:00"],
            }
        ),
    )
    _write_dataset(
        "noaa_weather",
        "noaa_other_day",
        datetime(2026, 4, 21, 13, 0, 0),
        pd.DataFrame(
            {
                "date": ["2026-04-22"],
                "station": ["GHCND:USW00014745"],
                "temp_avg_f": [58.0],
                "temp_min_f": [48.0],
                "temp_max_f": [68.0],
                "hdd": [7.0],
                "cdd": [0.0],
                "source": ["NOAA GHCND"],
                "pulled_at": ["2026-04-21T13:00:00"],
            }
        ),
    )

    res = client.post("/analysis/weather-demand/join")
    assert res.status_code == 422
    assert "does not overlap" in res.json()["detail"]


def test_get_latest_join_uses_fetched_at_not_filename(monkeypatch, tmp_path):
    _configure_temp_data(monkeypatch, tmp_path)
    base_df = pd.DataFrame(
        {
            "date": ["2026-04-21"],
            "region": ["ISO New England"],
            "daily_peak_mw": [12000],
            "temp_avg_f": [58.0],
            "hdd": [7.0],
            "cdd": [0.0],
            "demand_source": ["EIA"],
            "weather_source": ["NOAA GHCND"],
            "created_at": ["2026-04-21T13:00:00"],
        }
    )
    _write_dataset("weather_demand_analysis", "wd_join_z", datetime(2026, 4, 20, 13, 0, 0), base_df)
    _write_dataset("weather_demand_analysis", "wd_join_a", datetime(2026, 4, 21, 13, 0, 0), base_df)

    res = client.get("/analysis/weather-demand/latest")
    assert res.status_code == 200
    assert res.json()["id"] == "wd_join_a"


def test_download_unknown_join_returns_404():
    res = client.get("/analysis/weather-demand/does_not_exist/download")
    assert res.status_code == 404

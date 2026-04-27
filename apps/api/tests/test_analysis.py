from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _ensure_mock_demand() -> str:
    res = client.post("/sources/mock_demand/fetch")
    assert res.status_code == 200
    return res.json()["id"]


def test_create_join_returns_dataset():
    _ensure_mock_demand()
    res = client.post("/analysis/weather-demand/join")
    assert res.status_code == 200
    data = res.json()
    assert data["source_id"] == "weather_demand_analysis"
    assert data["status"] == "ready"
    assert data["row_count"] > 0


def test_join_has_required_columns():
    _ensure_mock_demand()
    res = client.post("/analysis/weather-demand/join")
    cols = res.json()["columns"]
    for expected in ["date", "region", "daily_peak_mw", "temp_avg_f", "hdd", "cdd",
                     "demand_source", "weather_source", "created_at"]:
        assert expected in cols, f"Missing column: {expected}"


def test_get_latest_join_returns_most_recent():
    _ensure_mock_demand()
    client.post("/analysis/weather-demand/join")
    res = client.get("/analysis/weather-demand/latest")
    assert res.status_code == 200
    assert res.json()["source_id"] == "weather_demand_analysis"


def test_join_row_count_matches_days_of_demand():
    _ensure_mock_demand()
    res = client.post("/analysis/weather-demand/join")
    # 168 hours of mock data = 7 complete days
    assert res.json()["row_count"] == 7


def test_download_joined_csv():
    _ensure_mock_demand()
    join_res = client.post("/analysis/weather-demand/join")
    join_id = join_res.json()["id"]

    dl = client.get(f"/analysis/weather-demand/{join_id}/download")
    assert dl.status_code == 200
    assert "text/csv" in dl.headers["content-type"]
    header = dl.text.strip().splitlines()[0]
    assert "date" in header
    assert "daily_peak_mw" in header
    assert "temp_avg_f" in header


def test_join_preview_via_datasets_endpoint():
    _ensure_mock_demand()
    join_res = client.post("/analysis/weather-demand/join")
    join_id = join_res.json()["id"]

    preview = client.get(f"/datasets/{join_id}/preview")
    assert preview.status_code == 200
    data = preview.json()
    assert "daily_peak_mw" in data["columns"]
    assert len(data["rows"]) == 7


def test_download_unknown_join_returns_404():
    res = client.get("/analysis/weather-demand/does_not_exist/download")
    assert res.status_code == 404

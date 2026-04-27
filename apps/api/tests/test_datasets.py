from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _fetch_mock() -> dict:
    res = client.post("/sources/mock_demand/fetch")
    assert res.status_code == 200
    return res.json()


def test_list_datasets_returns_list():
    res = client.get("/datasets")
    assert res.status_code == 200
    data = res.json()
    assert "datasets" in data
    assert "total" in data
    assert data["total"] == len(data["datasets"])


def test_fetch_mock_returns_dataset():
    data = _fetch_mock()
    assert data["source_id"] == "mock_demand"
    assert data["status"] == "ready"
    assert data["row_count"] == 168
    assert "id" in data


def test_fetch_mock_appears_in_list():
    data = _fetch_mock()
    dataset_id = data["id"]
    res = client.get("/datasets")
    ids = [d["id"] for d in res.json()["datasets"]]
    assert dataset_id in ids


def test_get_dataset_detail():
    data = _fetch_mock()
    dataset_id = data["id"]
    res = client.get(f"/datasets/{dataset_id}")
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == dataset_id
    assert detail["row_count"] == 168
    assert "timestamp" in detail["columns"]
    assert "demand_mw" in detail["columns"]
    assert "region" in detail["columns"]


def test_get_dataset_not_found():
    res = client.get("/datasets/does_not_exist")
    assert res.status_code == 404


def test_preview_dataset():
    data = _fetch_mock()
    dataset_id = data["id"]
    res = client.get(f"/datasets/{dataset_id}/preview")
    assert res.status_code == 200
    preview = res.json()
    assert "columns" in preview
    assert "rows" in preview
    assert preview["total_row_count"] == 168
    assert len(preview["rows"]) <= 50
    assert set(["timestamp", "region", "demand_mw", "source", "pulled_at"]).issubset(
        set(preview["columns"])
    )


def test_download_cleaned_returns_csv():
    data = _fetch_mock()
    dataset_id = data["id"]
    res = client.get(f"/datasets/{dataset_id}/download/cleaned")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    lines = res.text.strip().splitlines()
    assert lines[0] == "timestamp,region,demand_mw,source,pulled_at"
    assert len(lines) > 1


def test_download_raw_returns_csv():
    data = _fetch_mock()
    dataset_id = data["id"]
    res = client.get(f"/datasets/{dataset_id}/download/raw")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]

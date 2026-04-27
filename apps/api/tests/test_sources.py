from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_sources_returns_all():
    res = client.get("/sources")
    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    assert data["total"] == len(data["sources"])
    assert data["total"] > 0


def test_list_sources_includes_mock():
    res = client.get("/sources")
    ids = [s["id"] for s in res.json()["sources"]]
    assert "mock_demand" in ids


def test_get_source_mock_demand():
    res = client.get("/sources/mock_demand")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "mock_demand"
    assert data["status"] == "mock"
    assert data["category"] == "electricity"


def test_get_source_not_found():
    res = client.get("/sources/does_not_exist")
    assert res.status_code == 404


def test_get_source_isone_csv_is_active():
    res = client.get("/sources/isone_csv")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "isone_csv"
    assert data["status"] == "active"
    assert data["data_format"] == "CSV"


def test_get_source_openei_rates_is_active():
    res = client.get("/sources/openei_rates")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "openei_rates"
    assert data["status"] == "active"


def test_get_source_epa_egrid_is_active():
    res = client.get("/sources/epa_egrid")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "epa_egrid"
    assert data["status"] == "active"


def test_fetch_source_returns_not_implemented_message():
    res = client.post("/sources/epa_ejscreen/fetch")
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert "source_id" in data


def test_fetch_source_unknown_returns_404():
    res = client.post("/sources/unknown_source/fetch")
    assert res.status_code == 404

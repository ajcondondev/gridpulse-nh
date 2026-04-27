from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app
from app import config

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


def _mock_isone_response(body: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.text = body
    return mock


def test_isone_dataset_preview_and_download(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    csv_text = "Date,Hour Ending,Native Demand\n2026-04-26,1,10000\n2026-04-26,2,10100\n"
    with patch(
        "app.connectors.isone_csv_connector.httpx.get",
        return_value=_mock_isone_response(csv_text),
    ):
        fetch_res = client.post("/sources/isone_csv/fetch")

    assert fetch_res.status_code == 200
    dataset_id = fetch_res.json()["id"]

    preview = client.get(f"/datasets/{dataset_id}/preview")
    assert preview.status_code == 200
    assert set(["timestamp", "region", "demand_mw", "source", "pulled_at"]).issubset(
        set(preview.json()["columns"])
    )
    assert len(preview.json()["rows"]) == 2

    cleaned = client.get(f"/datasets/{dataset_id}/download/cleaned")
    assert cleaned.status_code == 200
    assert "timestamp,region,demand_mw,source,pulled_at" in cleaned.text.splitlines()[0]

    raw = client.get(f"/datasets/{dataset_id}/download/raw")
    assert raw.status_code == 200
    assert "Date,Hour Ending,Native Demand" in raw.text.splitlines()[0]


def _mock_json_response(payload) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = payload
    return mock


def _mock_html_response(body: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.text = body
    return mock


def test_openei_dataset_preview_and_download(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    payload = {
        "items": [
            {
                "label": "rate-1",
                "utility": "PSNH",
                "name": "Residential Default",
                "sector": "Residential",
                "servicetype": "Bundled",
                "approved": True,
                "is_default": True,
                "fixedchargefirstmeter": 15.25,
                "fixedchargeunits": "$/month",
                "mincharge": 10.0,
                "minchargeunits": "$/month",
                "energyratestructure": [[{"rate": 0.1423}]],
                "uri": "https://apps.openei.org/USURDB/rate/view/rate-1",
            }
        ]
    }
    with patch(
        "app.connectors.openei_rates_connector.httpx.get",
        return_value=_mock_json_response(payload),
    ):
        fetch_res = client.post("/sources/openei_rates/fetch")

    assert fetch_res.status_code == 200
    dataset_id = fetch_res.json()["id"]

    preview = client.get(f"/datasets/{dataset_id}/preview")
    assert preview.status_code == 200
    assert "energy_rate_kwh" in preview.json()["columns"]

    cleaned = client.get(f"/datasets/{dataset_id}/download/cleaned")
    assert cleaned.status_code == 200
    assert "rate_id,utility_name,rate_name" in cleaned.text.splitlines()[0]

    raw = client.get(f"/datasets/{dataset_id}/download/raw")
    assert raw.status_code == 200
    assert "label,utility,name,sector" in raw.text.splitlines()[0]


def test_egrid_dataset_preview_and_download(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    html = """
    <html><body><h2>eGRID with 2023 Data</h2>
    <table>
      <tr><th>eGRID Subregion</th><th>CO2</th><th>CH4</th><th>N2O</th><th>CO2e</th><th>Annual NOX</th><th>Ozone Season NOX</th><th>SO2</th></tr>
      <tr><td>NEWE</td><td>582.125</td><td>0.020</td><td>0.003</td><td>583.500</td><td>0.241</td><td>0.260</td><td>0.104</td></tr>
    </table></body></html>
    """
    with patch(
        "app.connectors.egrid_connector.httpx.get",
        return_value=_mock_html_response(html),
    ):
        fetch_res = client.post("/sources/epa_egrid/fetch")

    assert fetch_res.status_code == 200
    dataset_id = fetch_res.json()["id"]

    preview = client.get(f"/datasets/{dataset_id}/preview")
    assert preview.status_code == 200
    assert "co2e_lb_per_mwh" in preview.json()["columns"]

    cleaned = client.get(f"/datasets/{dataset_id}/download/cleaned")
    assert cleaned.status_code == 200
    assert "subregion,co2_lb_per_mwh" in cleaned.text.splitlines()[0]

    raw = client.get(f"/datasets/{dataset_id}/download/raw")
    assert raw.status_code == 200
    assert "eGRID Subregion,CO2,CH4" in raw.text.splitlines()[0]

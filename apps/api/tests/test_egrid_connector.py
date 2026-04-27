from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app import config
from app.connectors.egrid_connector import EGridConnector
from app.main import app

client = TestClient(app)

_HTML = """
<html>
  <body>
    <h2>eGRID with 2023 Data</h2>
    <table>
      <thead>
        <tr>
          <th>eGRID Subregion</th>
          <th>CO2</th>
          <th>CH4</th>
          <th>N2O</th>
          <th>CO2e</th>
          <th>Annual NOX</th>
          <th>Ozone Season NOX</th>
          <th>SO2</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>NEWE</td>
          <td>582.125</td>
          <td>0.020</td>
          <td>0.003</td>
          <td>583.500</td>
          <td>0.241</td>
          <td>0.260</td>
          <td>0.104</td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
"""


def _mock_html_response(body: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.text = body
    return mock


def test_connector_has_correct_source_id():
    assert EGridConnector.source_id == "epa_egrid"


def test_fetch_returns_dataframe():
    with patch(
        "app.connectors.egrid_connector.httpx.get",
        return_value=_mock_html_response(_HTML),
    ):
        result = EGridConnector().fetch()

    assert result["row_count"] == 1
    assert "eGRID Subregion" in result["dataframe"].columns
    assert result["dataframe"]["data_year"].iloc[0] == 2023


def test_fetch_raises_on_missing_table():
    with patch(
        "app.connectors.egrid_connector.httpx.get",
        return_value=_mock_html_response("<html><body><p>No table</p></body></html>"),
    ):
        with pytest.raises(ValueError, match="expected subregion emissions table"):
            EGridConnector().fetch()


def test_clean_maps_emissions_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame(
        [
            {
                "eGRID Subregion": "NEWE",
                "CO2": 582.125,
                "CH4": 0.020,
                "N2O": 0.003,
                "CO2e": 583.5,
                "Annual NOX": 0.241,
                "Ozone Season NOX": 0.260,
                "SO2": 0.104,
                "data_year": 2023,
            }
        ]
    ).to_csv(raw_csv, index=False)

    df = EGridConnector().clean(raw_csv)

    assert list(df.columns) == [
        "subregion",
        "co2_lb_per_mwh",
        "ch4_lb_per_mwh",
        "n2o_lb_per_mwh",
        "co2e_lb_per_mwh",
        "annual_nox_lb_per_mwh",
        "ozone_season_nox_lb_per_mwh",
        "so2_lb_per_mwh",
        "data_year",
        "source",
    ]
    assert df.loc[0, "subregion"] == "NEWE"
    assert df.loc[0, "source"] == "EPA eGRID"


def test_clean_raises_on_missing_expected_columns(tmp_path):
    raw_csv = tmp_path / "raw.csv"
    pd.DataFrame([{"foo": 1}]).to_csv(raw_csv, index=False)

    with pytest.raises(ValueError, match="missing expected columns"):
        EGridConnector().clean(raw_csv)


def test_fetch_route_returns_dataset(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.egrid_connector.httpx.get",
        return_value=_mock_html_response(_HTML),
    ):
        response = client.post("/sources/epa_egrid/fetch")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "epa_egrid"
    assert data["row_count"] == 1
    assert "co2e_lb_per_mwh" in data["columns"]


def test_fetch_route_returns_422_on_bad_page(monkeypatch, tmp_path):
    monkeypatch.setattr(config.settings, "api_data_dir", str(tmp_path))
    with patch(
        "app.connectors.egrid_connector.httpx.get",
        return_value=_mock_html_response("<html><body><p>No table</p></body></html>"),
    ):
        response = client.post("/sources/epa_egrid/fetch")

    assert response.status_code == 422
    assert "subregion emissions table" in response.json()["detail"]

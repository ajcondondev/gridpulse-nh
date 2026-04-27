from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from app.config import settings
from app.services.fetch_service import fetch_eia_isone_load


def test_fetch_eia_does_not_publish_metadata_when_cleaned_empty(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    monkeypatch.setattr("app.config.settings.eia_api_key", "test-key")

    with patch(
        "app.connectors.eia_connector.EIAConnector.fetch",
        return_value={
            "dataframe": pd.DataFrame({"period": ["2026-04-27T00"], "value": [12000]}),
            "fetched_at": datetime(2026, 4, 27, 12, 0, 0),
        },
    ), patch(
        "app.connectors.eia_connector.EIAConnector.clean",
        return_value=pd.DataFrame(columns=["timestamp", "region", "demand_mw", "source"]),
    ):
        with pytest.raises(ValueError, match="empty after validation"):
            fetch_eia_isone_load()

    metadata_files = list((Path(settings.api_data_dir) / "metadata").glob("*.json"))
    assert metadata_files == []


def test_fetch_eia_does_not_publish_metadata_when_required_columns_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("app.config.settings.api_data_dir", str(tmp_path))
    monkeypatch.setattr("app.config.settings.eia_api_key", "test-key")

    with patch(
        "app.connectors.eia_connector.EIAConnector.fetch",
        return_value={
            "dataframe": pd.DataFrame({"period": ["2026-04-27T00"], "value": [12000]}),
            "fetched_at": datetime(2026, 4, 27, 12, 0, 0),
        },
    ), patch(
        "app.connectors.eia_connector.EIAConnector.clean",
        return_value=pd.DataFrame({"timestamp": ["2026-04-27T00:00:00"]}),
    ):
        with pytest.raises(ValueError, match="missing required columns"):
            fetch_eia_isone_load()

    metadata_files = list((Path(settings.api_data_dir) / "metadata").glob("*.json"))
    assert metadata_files == []

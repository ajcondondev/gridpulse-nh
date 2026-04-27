import pandas as pd

from app.connectors.mock_connector import MockConnector


def test_fetch_returns_dataframe():
    connector = MockConnector()
    result = connector.fetch()
    assert "dataframe" in result
    assert isinstance(result["dataframe"], pd.DataFrame)


def test_fetch_has_correct_columns():
    df = MockConnector().fetch()["dataframe"]
    assert "timestamp" in df.columns
    assert "demand_mw" in df.columns


def test_fetch_returns_correct_row_count():
    result = MockConnector().fetch()
    assert len(result["dataframe"]) == MockConnector.HOURS
    assert result["row_count"] == MockConnector.HOURS


def test_demand_values_are_positive():
    df = MockConnector().fetch()["dataframe"]
    assert (df["demand_mw"] > 0).all()


def test_timestamps_are_ascending():
    df = MockConnector().fetch()["dataframe"]
    timestamps = pd.to_datetime(df["timestamp"])
    assert timestamps.is_monotonic_increasing

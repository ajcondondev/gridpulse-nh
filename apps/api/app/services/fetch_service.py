from app.connectors.mock_connector import MockConnector
from app.schemas.dataset import Dataset
from app.services import dataset_service, storage_service


def fetch_mock_demand() -> Dataset:
    connector = MockConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"mock_demand_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("mock_demand", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["region"] = "ISO-NE Mock"
    df_clean["source"] = "Mock"
    df_clean["pulled_at"] = fetched_at.isoformat()
    df_clean = df_clean[["timestamp", "region", "demand_mw", "source", "pulled_at"]]

    cleaned_p = storage_service.cleaned_path("mock_demand", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="mock_demand",
        name=f"Mock Electricity Demand — {fetched_at.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_eia_isone_load() -> Dataset:
    from app.connectors.eia_connector import EIAConnector

    connector = EIAConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"eia_isone_load_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("eia_isone_load", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    df_clean = df_clean[["timestamp", "region", "demand_mw", "source", "pulled_at"]]

    cleaned_p = storage_service.cleaned_path("eia_isone_load", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="eia_isone_load",
        name=f"EIA ISO-NE Hourly Load — {fetched_at.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_noaa_weather() -> Dataset:
    from app.connectors.noaa_connector import NOAAConnector

    connector = NOAAConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"noaa_weather_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("noaa_weather", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()

    ordered_cols = [
        "date", "station",
        "temp_avg_f", "temp_min_f", "temp_max_f",
        "hdd", "cdd", "source", "pulled_at",
    ]
    df_clean = df_clean[[c for c in ordered_cols if c in df_clean.columns]]

    cleaned_p = storage_service.cleaned_path("noaa_weather", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="noaa_weather",
        name=f"NOAA Weather Manchester NH — {fetched_at.strftime('%Y-%m-%d')}",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_afdc_ev() -> Dataset:
    from app.connectors.afdc_connector import AFDCConnector

    connector = AFDCConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"afdc_ev_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("afdc_ev", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()

    ordered_cols = [
        "station_name", "city", "state", "zip",
        "latitude", "longitude",
        "fuel_type", "access_code",
        "level1_ports", "level2_ports", "dc_fast_ports",
        "source", "pulled_at",
    ]
    df_clean = df_clean[[c for c in ordered_cols if c in df_clean.columns]]

    cleaned_p = storage_service.cleaned_path("afdc_ev", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="afdc_ev",
        name=f"AFDC EV Stations NH — {fetched_at.strftime('%Y-%m-%d')}",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset

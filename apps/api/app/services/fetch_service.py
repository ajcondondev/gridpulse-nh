import pandas as pd

from app.connectors.mock_connector import MockConnector
from app.schemas.dataset import Dataset
from app.services import dataset_service, storage_service


def _require_columns(df: pd.DataFrame, required: list[str], source_name: str) -> pd.DataFrame:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{source_name} cleaned dataset missing required columns: {missing}.")
    return df[required]


def _require_non_empty(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    if df.empty:
        raise ValueError(f"{source_name} cleaned dataset is empty after validation.")
    return df


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
    df_clean = _require_columns(
        _require_non_empty(df_clean, "Mock demand"),
        ["timestamp", "region", "demand_mw", "source", "pulled_at"],
        "Mock demand",
    )

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
    df_clean = _require_columns(
        _require_non_empty(df_clean, "EIA"),
        ["timestamp", "region", "demand_mw", "source", "pulled_at"],
        "EIA",
    )

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


def fetch_isone_csv() -> Dataset:
    from app.connectors.isone_csv_connector import ISONECSVConnector

    connector = ISONECSVConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"isone_csv_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("isone_csv", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    df_clean = _require_columns(
        _require_non_empty(df_clean, "ISO-NE CSV"),
        ["timestamp", "region", "demand_mw", "source", "pulled_at"],
        "ISO-NE CSV",
    )

    cleaned_p = storage_service.cleaned_path("isone_csv", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="isone_csv",
        name=f"ISO-NE Hourly System Demand CSV - {fetched_at.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_openei_rates() -> Dataset:
    from app.connectors.openei_rates_connector import OpenEIRatesConnector

    connector = OpenEIRatesConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"openei_rates_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("openei_rates", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    ordered_cols = [
        "rate_id", "utility_name", "rate_name", "sector", "service_type",
        "approved", "is_default", "start_date", "end_date",
        "fixed_charge", "fixed_charge_units",
        "min_charge", "min_charge_units",
        "energy_rate_kwh", "description", "rate_uri",
        "source", "pulled_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "OpenEI utility rates"),
        ordered_cols,
        "OpenEI utility rates",
    )

    cleaned_p = storage_service.cleaned_path("openei_rates", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="openei_rates",
        name=f"OpenEI Utility Rates - {fetched_at.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_epa_egrid() -> Dataset:
    from app.connectors.egrid_connector import EGridConnector

    connector = EGridConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"epa_egrid_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("epa_egrid", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    ordered_cols = [
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
        "pulled_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "EPA eGRID"),
        ordered_cols,
        "EPA eGRID",
    )

    cleaned_p = storage_service.cleaned_path("epa_egrid", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="epa_egrid",
        name=f"EPA eGRID Subregion Emissions - {fetched_at.strftime('%Y-%m-%d')}",
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
    df_clean = _require_columns(
        _require_non_empty(df_clean, "NOAA"),
        ordered_cols,
        "NOAA",
    )

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
        "station_id",
        "station_name", "city", "state", "zip",
        "latitude", "longitude",
        "fuel_type", "access_code",
        "level1_ports", "level2_ports", "dc_fast_ports",
        "source", "pulled_at",
    ]
    df_clean = _require_non_empty(df_clean, "AFDC")
    required_cols = [
        "station_name", "city", "state", "zip",
        "latitude", "longitude",
        "fuel_type", "access_code",
        "level1_ports", "level2_ports", "dc_fast_ports",
        "source", "pulled_at",
    ]
    df_clean = _require_columns(
        df_clean,
        [c for c in ordered_cols if c in df_clean.columns or c in required_cols],
        "AFDC",
    )

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

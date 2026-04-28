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


def fetch_cdc_svi() -> Dataset:
    from app.connectors.cdc_svi_connector import CDCSVIConnector

    connector = CDCSVIConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"cdc_svi_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("cdc_svi", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["fetched_at"] = fetched_at.isoformat()
    ordered_cols = [
        "year", "state", "county", "fips", "location_name",
        "svi_overall_percentile",
        "socioeconomic_percentile",
        "household_characteristics_percentile",
        "racial_ethnic_minority_percentile",
        "housing_transportation_percentile",
        "source", "fetched_at",
    ]
    if "population" in df_clean.columns:
        ordered_cols.insert(ordered_cols.index("source"), "population")
    df_clean = _require_columns(
        _require_non_empty(df_clean, "CDC SVI"),
        [c for c in ordered_cols if c in df_clean.columns],
        "CDC SVI",
    )

    cleaned_p = storage_service.cleaned_path("cdc_svi", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="cdc_svi",
        name=f"CDC SVI NH — {fetched_at.strftime('%Y-%m-%d')}",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_fema_flood() -> Dataset:
    from app.connectors.fema_flood_connector import FEMAFloodConnector

    connector = FEMAFloodConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"fema_flood_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("fema_flood", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["fetched_at"] = fetched_at.isoformat()
    ordered_cols = [
        "feature_id", "flood_zone", "zone_subtype",
        "county_fips", "county", "state",
        "is_sfha", "panel_id", "geometry_type",
        "source", "fetched_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "FEMA Flood"),
        [c for c in ordered_cols if c in df_clean.columns],
        "FEMA Flood",
    )

    cleaned_p = storage_service.cleaned_path("fema_flood", filename)
    df_clean.to_csv(cleaned_p, index=False)

    exceeded = result.get("exceeded_transfer_limit", False)
    name = f"FEMA Flood Zones NH — {fetched_at.strftime('%Y-%m-%d')}"
    if exceeded:
        name += " (first 2000 records)"

    dataset = Dataset(
        id=dataset_id,
        source_id="fema_flood",
        name=name,
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_nh_geodata() -> Dataset:
    from app.connectors.nh_geodata_connector import NHGeodataConnector

    connector = NHGeodataConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"nh_geodata_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("nh_geodata", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["fetched_at"] = fetched_at.isoformat()
    ordered_cols = [
        "town_name", "county_name", "state",
        "state_fips", "county_fips", "town_fips",
        "population_2020", "source", "fetched_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "NH Geodata"),
        [c for c in ordered_cols if c in df_clean.columns],
        "NH Geodata",
    )

    cleaned_p = storage_service.cleaned_path("nh_geodata", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="nh_geodata",
        name=f"NH Municipal Geography (Census 2020) — {fetched_at.strftime('%Y-%m-%d')}",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_nrel_pvwatts() -> Dataset:
    from app.connectors.nrel_pvwatts_connector import NRELPVWattsConnector

    connector = NRELPVWattsConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"nrel_pvwatts_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("nrel_pvwatts", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    ordered_cols = [
        "location_name", "latitude", "longitude",
        "month", "month_name",
        "ac_kwh", "solar_radiation_kwh_m2_day",
        "system_capacity_kw", "source", "pulled_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "NREL PVWatts"),
        [c for c in ordered_cols if c in df_clean.columns],
        "NREL PVWatts",
    )

    cleaned_p = storage_service.cleaned_path("nrel_pvwatts", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="nrel_pvwatts",
        name=f"NREL PVWatts NH Solar Estimates — {fetched_at.strftime('%Y-%m-%d')}",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_eia_retail_prices() -> Dataset:
    from app.connectors.eia_retail_prices_connector import EIARetailPricesConnector

    connector = EIARetailPricesConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"eia_retail_prices_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("eia_retail_prices", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    df_clean = _require_columns(
        _require_non_empty(df_clean, "EIA Retail Prices"),
        ["period", "state", "sector_id", "sector_name", "price_cents_per_kwh", "source", "pulled_at"],
        "EIA Retail Prices",
    )

    cleaned_p = storage_service.cleaned_path("eia_retail_prices", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="eia_retail_prices",
        name=f"EIA NH Retail Electricity Prices — {fetched_at.strftime('%Y-%m-%d')}",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_isone_fuel_mix() -> Dataset:
    from app.connectors.isone_fuel_mix_connector import ISONEFuelMixConnector

    connector = ISONEFuelMixConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"isone_fuel_mix_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("isone_fuel_mix", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    df_clean = _require_columns(
        _require_non_empty(df_clean, "ISO-NE Fuel Mix"),
        ["timestamp", "date", "hour_ending", "fuel_type", "value", "unit", "source", "pulled_at"],
        "ISO-NE Fuel Mix",
    )

    cleaned_p = storage_service.cleaned_path("isone_fuel_mix", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="isone_fuel_mix",
        name=f"ISO-NE Generation Fuel Mix — {fetched_at.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_isone_load_forecast() -> Dataset:
    from app.connectors.isone_load_forecast_connector import ISONELoadForecastConnector

    connector = ISONELoadForecastConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"isone_load_forecast_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("isone_load_forecast", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    df_clean = _require_columns(
        _require_non_empty(df_clean, "ISO-NE Load Forecast"),
        ["timestamp", "date", "hour_ending", "load_forecast_mw", "source", "pulled_at"],
        "ISO-NE Load Forecast",
    )

    cleaned_p = storage_service.cleaned_path("isone_load_forecast", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="isone_load_forecast",
        name=f"ISO-NE Hourly Load Forecast — {fetched_at.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_eia_ng_prices() -> Dataset:
    from app.connectors.eia_ng_prices_connector import EIANGPricesConnector

    connector = EIANGPricesConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"eia_ng_prices_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("eia_ng_prices", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    ordered_cols = [
        "period", "state", "sector", "series_id",
        "price_per_mcf", "price_units", "source", "pulled_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "EIA Natural Gas Prices"),
        [c for c in ordered_cols if c in df_clean.columns],
        "EIA Natural Gas Prices",
    )

    cleaned_p = storage_service.cleaned_path("eia_ng_prices", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="eia_ng_prices",
        name=f"EIA NH Natural Gas Retail Prices — {fetched_at.strftime('%Y-%m-%d')}",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_epa_ejscreen() -> Dataset:
    from app.connectors.ejscreen_connector import EJScreenConnector

    connector = EJScreenConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"epa_ejscreen_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("epa_ejscreen", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["fetched_at"] = fetched_at.isoformat()
    ordered_cols = [
        "block_group_fips", "state", "county", "population",
        "pm25_pctile", "ozone_pctile", "diesel_pm_pctile",
        "cancer_risk_pctile", "resp_hazard_pctile",
        "traffic_pctile", "lead_paint_pctile",
        "superfund_pctile", "rmp_facility_pctile", "tsd_facility_pctile",
        "storage_tanks_pctile", "wastewater_pctile",
        "people_of_color_pct", "low_income_pct",
        "linguistic_isolation_pct", "unemployment_pct",
        "under_5_pct", "over_64_pct",
        "source", "data_year", "fetched_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "EPA EJScreen"),
        [c for c in ordered_cols if c in df_clean.columns],
        "EPA EJScreen",
    )

    cleaned_p = storage_service.cleaned_path("epa_ejscreen", filename)
    df_clean.to_csv(cleaned_p, index=False)

    exceeded = result.get("exceeded_transfer_limit", False)
    name = f"EPA EJScreen NH Block Groups — 2023"
    if exceeded:
        name += " (first 2000 records)"

    dataset = Dataset(
        id=dataset_id,
        source_id="epa_ejscreen",
        name=name,
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_isone_lmp() -> Dataset:
    from app.connectors.isone_lmp_connector import ISONELMPConnector

    connector = ISONELMPConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]

    dataset_id = f"isone_lmp_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("isone_lmp", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    ordered_cols = [
        "timestamp", "date", "hour_ending",
        "zone_id", "zone_name",
        "lmp_per_mwh", "energy_component", "congestion_component", "loss_component",
        "source", "pulled_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "ISO-NE LMP"),
        [c for c in ordered_cols if c in df_clean.columns],
        "ISO-NE LMP",
    )

    cleaned_p = storage_service.cleaned_path("isone_lmp", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="isone_lmp",
        name=f"ISO-NE Zone LMP — {fetched_at.strftime('%Y-%m-%d %H:%M')} UTC",
        fetched_at=fetched_at,
        row_count=len(df_clean),
        columns=list(df_clean.columns),
        raw_path=str(raw_p),
        cleaned_path=str(cleaned_p),
        status="ready",
    )
    dataset_service.save_dataset(dataset)
    return dataset


def fetch_eia_ami() -> Dataset:
    from app.connectors.eia_ami_connector import EIAAMIConnector

    connector = EIAAMIConnector()
    result = connector.fetch()
    df_raw = result["dataframe"]
    fetched_at = result["fetched_at"]
    data_year = result.get("data_year", "unknown")

    dataset_id = f"eia_ami_{fetched_at.strftime('%Y%m%d_%H%M%S')}"
    filename = f"{dataset_id}.csv"

    raw_p = storage_service.raw_path("eia_ami", filename)
    df_raw.to_csv(raw_p, index=False)

    df_clean = connector.clean(raw_p)
    df_clean["pulled_at"] = fetched_at.isoformat()
    ordered_cols = [
        "utility_name", "state", "data_year",
        "ownership", "service_type",
        "total_customers", "ami_customers", "ami_pct",
        "source", "pulled_at",
    ]
    df_clean = _require_columns(
        _require_non_empty(df_clean, "EIA AMI"),
        [c for c in ordered_cols if c in df_clean.columns],
        "EIA AMI",
    )

    cleaned_p = storage_service.cleaned_path("eia_ami", filename)
    df_clean.to_csv(cleaned_p, index=False)

    dataset = Dataset(
        id=dataset_id,
        source_id="eia_ami",
        name=f"EIA 861 AMI Smart Meters NH — {data_year}",
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

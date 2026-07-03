"""Shared configuration for the GridPulse data pipeline.

The pipeline turns raw public data into small, committed, app-ready artifacts
in ``data/processed`` — the contract consumed by both the web app and the
(future) Remotion video. See .local-plan/03-data-pipeline-plan.md.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

# EIA-930 bulk six-month balance files (no API key required).
EIA930_BASE_URL = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles"
BALANCING_AUTHORITY = "ISNE"  # ISO New England

# Weather: Open-Meteo ERA5 archive (no API key required). Concord, NH.
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_LAT = 43.2081
WEATHER_LON = -71.5376
WEATHER_STATION_LABEL = "Concord, NH (ERA5 reanalysis via Open-Meteo)"

# Degree-day base temperature (°F), standard convention.
DEGREE_DAY_BASE_F = 65.0

# Canonical fuel groups -> EIA-930 source column bases
# (column form: "Net Generation (MW) from {base}").
FUEL_GROUPS: dict[str, list[str]] = {
    "natural_gas": ["Natural Gas"],
    "nuclear": ["Nuclear"],
    "hydro": ["Hydropower Excluding Pumped Storage"],
    "solar": [
        "Solar without Integrated Battery Storage",
        "Solar with Integrated Battery Storage",
    ],
    "wind": [
        "Wind without Integrated Battery Storage",
        "Wind with Integrated Battery Storage",
    ],
    "oil": ["All Petroleum Products"],
    "coal": ["Coal"],
    "storage": [
        "Pumped Storage",
        "Battery Storage",
        "Other Energy Storage",
        "Unknown Energy Storage",
    ],
    "other": ["Geothermal", "Other Fuel Sources", "Unknown Fuel Sources"],
}

# Window sizes for artifacts (days).
HOURLY_WINDOW_DAYS = 30
EVENT_WINDOW_DAYS = 7

<div align="center">

# GridPulse NH

**Public utility, weather, EV, price, emissions, and resilience data in one workbench.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![pandas](https://img.shields.io/badge/pandas-2-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tests](https://img.shields.io/badge/tests-188_passing-22c55e?style=flat-square&logo=pytest&logoColor=white)](#testing)
[![License](https://img.shields.io/badge/license-MIT-64748b?style=flat-square)](LICENSE)

**[Getting Started](#getting-started) · [API Reference](#api-reference) · [Data Sources](#data-sources) · [API Keys](#api-keys)**

</div>

---

## Overview

GridPulse NH is a full-stack utility data engineering workbench focused on New Hampshire and ISO New England. The backend uses a connector-per-source pattern — each connector implements `fetch()` and `clean()` — and stores raw and cleaned files separately with dataset metadata so every fetch can be previewed or downloaded without re-running the source request.

The app supports live public connectors for electricity demand, fuel mix, wholesale prices, solar estimates, smart meter deployment, natural gas prices, weather, EV charging, utility rates, emissions, environmental justice, flood zones, social vulnerability, and municipal geography, alongside a synthetic demand generator and a weather × demand analysis workflow.

> **Disclaimer:** All data comes from publicly available APIs and government datasets. Not official Eversource software. Not affiliated with ISO New England or any utility.

---

## Features

- **22-source catalog** spanning electricity, gas, weather, EV, solar, environmental, resilience, GIS, and regulatory categories
- **18 implemented connectors** — 13 require no API key at all:
  - ISO-NE public hourly system demand CSV
  - ISO-NE hourly generation fuel mix (natural gas, nuclear, hydro, solar, wind, and more)
  - ISO-NE 7-day hourly load forecast
  - ISO-NE real-time hourly zone LMP wholesale prices
  - NREL PVWatts monthly solar output estimates for key NH cities (DEMO_KEY default)
  - AFDC EV charging station locations in NH (DEMO_KEY default)
  - OpenEI residential utility rates (NH service territory)
  - EPA eGRID subregion emission rates (CO2e, NOx, SO2)
  - EPA EJScreen 2023 block-group environmental justice indicators
  - EIA Form 861 AMI smart meter deployment (NH utilities, ZIP/Excel)
  - FEMA National Flood Hazard Layer (NH flood zones by county)
  - CDC/ATSDR Social Vulnerability Index (NH census tracts, 4 equity themes)
  - NH municipal geography (Census 2020 — all NH towns with FIPS and population)
  - Synthetic mock demand generator (pipeline testing)
- **Dataset pipeline** — raw save → clean → metadata → preview → CSV download
- **Weather × demand analysis** — joins daily peak MW with temperature, HDD, and CDD; dual-axis Recharts visualization
- **Source status model** — `active`, `requires_key`, `research`, `not_implemented`, and `test_fixture_only` clearly labeled in the UI

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Recharts |
| **Backend** | Python 3.11+, FastAPI, pandas, pydantic v2, uvicorn, httpx, openpyxl |
| **Storage** | Local filesystem — `/data/raw`, `/data/cleaned`, `/data/exports`, `/data/metadata` |
| **Testing** | pytest (188 passing), Playwright frontend smoke tests |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+

### Backend

```bash
cd apps/api
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| Interactive API docs | `http://localhost:8000/docs` |
| Web app | `http://localhost:5173` |

### Try It Without Any API Key

All of the following work immediately with no configuration:

| Source | What it fetches |
|---|---|
| **ISO-NE CSV Downloads** | Hourly real-time system demand for ISO New England |
| **ISO-NE Generation Fuel Mix** | Hourly MW by fuel type — gas, nuclear, hydro, solar, wind, and more |
| **ISO-NE Hourly Load Forecast** | 7-day ahead hourly system load forecast |
| **ISO-NE Zone LMP Prices** | Real-time hourly wholesale LMP for all ISO-NE zones including NH |
| **NREL PVWatts Solar Estimates** | Monthly solar output for Manchester, Concord, Portsmouth, Keene (DEMO_KEY) |
| **AFDC EV Charging Stations** | NH EV station locations, port counts, and access type (DEMO_KEY) |
| **OpenEI Utility Rates** | Residential utility rates near NH service territory |
| **EPA eGRID** | Subregion emission rates — CO2e, NOx, SO2 |
| **EPA EJScreen** | NH block-group EJ indicators — pollution burden and demographic percentiles |
| **EIA AMI Smart Meters** | NH utility smart meter deployment counts and penetration rates |
| **FEMA Flood Maps** | NH flood zone designations by county (AE, X, VE zones) |
| **CDC Social Vulnerability Index** | NH census tract SVI — 4 equity theme percentiles |
| **NH Geodata** | All NH towns and cities with FIPS codes and 2020 Census population |
| **Mock Electricity Demand** | Synthetic NH demand for pipeline testing |

Suggested path: fetch **ISO-NE CSV** → **ISO-NE Fuel Mix** → **EPA EJScreen** or **CDC SVI** → run **Weather & Demand** analysis.

---

## Testing

```bash
# Backend — 188 tests
cd apps/api
pytest

# Frontend smoke tests
cd apps/web
npx playwright test
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/sources` | List all 22 sources with full metadata |
| `GET` | `/sources/{id}` | Source detail — status, access method, key requirements |
| `POST` | `/sources/{id}/fetch` | Fetch, clean, and store latest data |
| `GET` | `/datasets` | List stored datasets |
| `GET` | `/datasets/{id}` | Dataset detail and column list |
| `GET` | `/datasets/{id}/preview?nrows=50` | Preview cleaned rows as JSON |
| `GET` | `/datasets/{id}/download/cleaned` | Download cleaned CSV |
| `GET` | `/datasets/{id}/download/raw` | Download raw CSV |
| `POST` | `/analysis/weather-demand/join` | Generate weather × demand join |
| `GET` | `/analysis/weather-demand/latest` | Latest join dataset |
| `GET` | `/analysis/weather-demand/{id}/download` | Download join CSV |

---

## Data Sources

### No API Key Required

| Source | Category | Notes |
|---|---|---|
| ISO-NE CSV Downloads | Electricity | 7-day hourly real-time system demand |
| ISO-NE Generation Fuel Mix | Electricity | 7-day hourly MW by fuel type |
| ISO-NE Hourly Load Forecast | Electricity | 7-day ahead hourly forecast |
| ISO-NE Zone LMP Prices | Electricity | Real-time hourly wholesale LMP, all zones |
| OpenEI Utility Rates | Electricity | NH territory rates (key optional) |
| EPA eGRID | Environmental | Subregion emission rates, annual |
| EPA EJScreen | Environmental | NH block-group EJ indicators (ArcGIS REST) |
| EIA AMI Smart Meters | Electricity | NH utility AMI deployment, EIA Form 861 ZIP |
| FEMA Flood Maps | Resilience | NH flood zones by county (ArcGIS REST) |
| CDC Social Vulnerability Index | Resilience | NH census tract SVI, 2022 |
| NH Geodata (GRANIT) | GIS | All NH towns, FIPS, 2020 Census population |
| NREL PVWatts Solar Estimates | Solar | Monthly solar output, key NH cities (DEMO_KEY) |
| AFDC EV Charging Stations | EV | NH station locations and port counts (DEMO_KEY) |
| Mock Electricity Demand | Electricity | Synthetic — pipeline testing only |

### Requires API Key

| Source | Category | Key | Notes |
|---|---|---|---|
| EIA ISO-NE Hourly Load | Electricity | `EIA_API_KEY` | Hourly load via EIA v2 API |
| EIA Retail Electricity Prices | Electricity | `EIA_API_KEY` | Monthly NH prices by sector (¢/kWh) |
| EIA Natural Gas Retail Prices | Gas | `EIA_API_KEY` | Monthly NH NG prices by sector ($/MCF) |
| NOAA Weather | Weather | `NOAA_TOKEN` | Daily observations, NH stations |

### Research / Not Yet Implemented

| Source | Category | Status |
|---|---|---|
| Manchester GIS | GIS | `research` — no confirmed stable public API |
| NHSaves | Regulatory | `not_implemented` — HTML/PDF, no structured API |
| NH Public Utilities Commission | Regulatory | `not_implemented` — PDF filings only |
| Eversource Sustainability Reports | Regulatory | `not_implemented` — annual PDFs only |

---

## API Keys

Keys go in `apps/api/.env` (gitignored — never committed).

```env
EIA_API_KEY=your_key_here         # EIA ISO-NE load + retail electricity + natural gas prices
NOAA_TOKEN=your_key_here
NREL_API_KEY=your_key_here        # optional — DEMO_KEY used by default for AFDC and PVWatts
OPENEI_API_KEY=your_key_here      # optional — public access attempted first
```

| Key | Source | Cost |
|---|---|---|
| `EIA_API_KEY` | [eia.gov/opendata](https://www.eia.gov/opendata/) | Free |
| `NOAA_TOKEN` | [ncdc.noaa.gov/cdo-web/token](https://www.ncdc.noaa.gov/cdo-web/token) | Free |
| `NREL_API_KEY` | [developer.nrel.gov](https://developer.nrel.gov/) | Free |
| `OPENEI_API_KEY` | [openei.org](https://openei.org/services/) | Free |

---

## Project Structure

```text
apps/
  api/
    app/
      connectors/
        base.py
        mock_connector.py
        eia_connector.py            # EIA ISO-NE hourly load
        eia_retail_prices_connector.py
        eia_ng_prices_connector.py  # EIA natural gas retail prices
        eia_ami_connector.py        # EIA Form 861 AMI smart meter deployment
        noaa_connector.py
        isone_csv_connector.py
        isone_fuel_mix_connector.py
        isone_load_forecast_connector.py
        isone_lmp_connector.py      # ISO-NE zone LMP wholesale prices
        nrel_pvwatts_connector.py
        afdc_connector.py
        openei_rates_connector.py
        egrid_connector.py
        ejscreen_connector.py       # EPA EJScreen EJ indicators
        fema_flood_connector.py
        cdc_svi_connector.py
        nh_geodata_connector.py
      routes/
        health.py
        sources.py
        datasets.py
        analysis.py
      schemas/
        source.py
        dataset.py
      services/
        fetch_service.py
        dataset_service.py
        storage_service.py
        analysis_service.py
    tests/         # 188 pytest tests
  web/
    src/
      routes/      # Dashboard, Sources, Datasets, WeatherDemand pages
      components/  # Layout, StatusBadge, DatasetTable, DownloadButton
      services/    # apiClient, sourcesApi, datasetsApi
      types/       # source.ts, dataset.ts
data/
  raw/             # gitignored — fetched source files
  cleaned/         # gitignored — cleaned CSVs
  exports/         # gitignored
  metadata/        # gitignored — dataset JSON records
```

---

## License

MIT

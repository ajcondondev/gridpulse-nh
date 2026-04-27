<div align="center">

# GridPulse NH

**Public utility, weather, EV, price, emissions, and resilience data in one workbench.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![pandas](https://img.shields.io/badge/pandas-2-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tests](https://img.shields.io/badge/tests-126_passing-22c55e?style=flat-square&logo=pytest&logoColor=white)](#testing)
[![License](https://img.shields.io/badge/license-MIT-64748b?style=flat-square)](LICENSE)

**[Getting Started](#getting-started) · [API Reference](#api-reference) · [Data Sources](#data-sources) · [API Keys](#api-keys)**

</div>

---

## Overview

GridPulse NH is a full-stack utility data engineering workbench focused on New Hampshire and ISO New England. The backend uses a connector-per-source pattern — each connector implements `fetch()` and `clean()` — and stores raw and cleaned files separately with dataset metadata so every fetch can be previewed or downloaded without re-running the source request.

The app supports live public connectors for electricity demand, weather, EV charging, utility rates, emissions, flood zones, social vulnerability, and municipal geography, alongside a synthetic demand generator and a weather × demand analysis workflow.

> **Disclaimer:** All data comes from publicly available APIs and government datasets.

---

## Features

- **15-source catalog** spanning electricity, weather, EV, environmental, resilience, GIS, and regulatory categories
- **10 fetchable connectors** — 8 require no API key at all:
  - ISO-NE public hourly demand CSV
  - AFDC EV charging stations (NH, DEMO_KEY default)
  - OpenEI residential utility rates (NH territory)
  - EPA eGRID subregion emissions
  - FEMA National Flood Hazard Layer (NH flood zones)
  - CDC/ATSDR Social Vulnerability Index (NH census tracts)
  - NH municipal geography (Census 2020 — all NH towns + population)
  - Synthetic mock demand generator
- **Dataset pipeline** — raw save → clean → metadata → preview → CSV download
- **Weather × demand analysis** — joins daily peak MW with temperature, HDD, and CDD; dual-axis Recharts plot
- **Source status model** — `active`, `requires_key`, `research`, `not_implemented`, and `mock` clearly labeled in the UI

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Recharts |
| **Backend** | Python 3.11+, FastAPI, pandas, pydantic v2, uvicorn, httpx |
| **Storage** | Local filesystem — `/data/raw`, `/data/cleaned`, `/data/exports`, `/data/metadata` |
| **Testing** | pytest (126 passing), Playwright frontend smoke tests |

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
| **EPA eGRID** | Subregion emission rates (CO2e, NOx, SO2) |
| **AFDC EV Charging Stations** | NH EV station locations and port counts |
| **OpenEI Utility Rates** | Residential utility rates near NH service territory |
| **FEMA Flood Maps** | NH flood zone designations by county |
| **CDC Social Vulnerability Index** | NH census tract SVI — 4 equity theme percentiles |
| **NH Geodata** | All NH towns and cities with FIPS codes and 2020 population |
| **Mock Electricity Demand** | Synthetic NH demand for pipeline testing |

Suggested path: fetch **ISO-NE CSV**, then **CDC SVI** or **FEMA Flood**, then run the **Weather & Demand** analysis.

---

## Testing

```bash
# Backend — 126 tests
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
| `GET` | `/sources` | List all 15 sources with full metadata |
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

| Source | Category | Status | Access |
|---|---|---|---|
| Mock Electricity Demand | Electricity | `mock` | No key — synthetic data |
| ISO-NE CSV Downloads | Electricity | `active` | No key — public CSV |
| OpenEI Utility Rates | Electricity | `active` | No key (key optional) |
| AFDC EV Charging Stations | EV | `active` | No key — DEMO_KEY default |
| EPA eGRID | Environmental | `active` | No key — web scrape |
| FEMA Flood Maps | Resilience | `active` | No key — ArcGIS REST |
| CDC Social Vulnerability Index | Resilience | `active` | No key — CSV download |
| NH Geodata (GRANIT) | GIS | `active` | No key — Census API |
| EIA ISO-NE Hourly Load | Electricity | `requires_key` | `EIA_API_KEY` — free at eia.gov/opendata |
| NOAA Weather | Weather | `requires_key` | `NOAA_TOKEN` — free at ncdc.noaa.gov/cdo-web/token |
| Manchester GIS | GIS | `research` | No stable public API confirmed |
| EPA EJScreen | Environmental | `not_implemented` | Connector not yet built |
| NHSaves | Regulatory | `not_implemented` | Connector not yet built |
| NH Public Utilities Commission | Regulatory | `not_implemented` | Connector not yet built |
| Eversource Sustainability Reports | Regulatory | `not_implemented` | Connector not yet built |

---

## API Keys

Keys go in `apps/api/.env` (gitignored — never committed).

```env
EIA_API_KEY=your_key_here
NOAA_TOKEN=your_key_here
NREL_API_KEY=your_key_here        # optional — DEMO_KEY used by default
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
        eia_connector.py
        noaa_connector.py
        isone_csv_connector.py
        afdc_connector.py
        openei_rates_connector.py
        egrid_connector.py
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
    tests/         # 126 pytest tests
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

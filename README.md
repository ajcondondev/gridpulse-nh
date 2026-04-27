<div align="center">

# GridPulse NH

**Public utility, weather, EV, and grid data in one workbench.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![pandas](https://img.shields.io/badge/pandas-2-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tests](https://img.shields.io/badge/tests-69_passing-22c55e?style=flat-square&logo=pytest&logoColor=white)](#testing)
[![License](https://img.shields.io/badge/license-MIT-64748b?style=flat-square)](LICENSE)

A full-stack data engineering portfolio project for pulling, cleaning, previewing, and exporting public utility-related datasets — focused on New Hampshire, ISO New England, EV infrastructure, weather-driven demand, and environmental data.

**[Getting Started](#getting-started) · [API Reference](#api-reference) · [Data Sources](#data-sources) · [API Keys](#api-keys)**

</div>

---

## Overview

GridPulse NH demonstrates real-world data engineering patterns against live public APIs in the energy and utility domain. The backend implements a connector-per-source architecture — each source has a `fetch()` and `clean()` method, raw and cleaned files are stored separately, and a metadata layer tracks every dataset. The frontend provides a workflow from source catalog → one-click fetch → dataset preview → CSV download.

The project connects to three live APIs out of the box, includes a synthetic demand generator for offline development, and produces a joined weather × electricity demand analysis with a dual-axis visualization.

> **Disclaimer:** All data is sourced from publicly available APIs and datasets.

---

## Features

- **14-source catalog** spanning electricity, weather, EV, environmental, resilience, GIS, and regulatory categories — each with status badges and metadata
- **Live API connectors** — NREL AFDC EV stations, EIA ISO-NE hourly load, NOAA GHCND weather
- **Synthetic demand generator** — reproducible 168-hour electricity demand with diurnal curves and weekend factors
- **Weather × demand analysis** — daily peak MW joined with average temperature, HDD, and CDD; dual-axis Recharts visualization
- **Dataset pipeline** — raw save → clean → metadata → preview → CSV download, all via REST
- **Source filtering** — category tabs, status badges, direct source → fetch → dataset navigation

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Recharts |
| **Backend** | Python 3.11+, FastAPI, pandas, pydantic v2, uvicorn, httpx |
| **Storage** | Local filesystem — `/data/raw`, `/data/cleaned`, `/data/exports`, `/data/metadata` |
| **Testing** | pytest (69 backend tests), Playwright (frontend smoke tests) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- *(Optional)* Free API keys for EIA and/or NOAA — see [API Keys](#api-keys)

### 1 — Clone

```bash
git clone https://github.com/ajcondondev/gridpulse-nh.git
cd gridpulse-nh
```

### 2 — Backend

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

| URL | Description |
|---|---|
| `http://localhost:8000` | REST API |
| `http://localhost:8000/docs` | Interactive Swagger UI |

### 3 — Frontend

Open a second terminal:

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

App available at **`http://localhost:5173`**

### 4 — Try it immediately (no API key required)

1. Open `http://localhost:5173`
2. Navigate to **Sources → Mock Electricity Demand**
3. Click **Fetch Latest Data** — 168 hours of synthetic demand is generated, cleaned, and stored
4. Follow the dataset link to preview the table and download the CSV
5. Navigate to **Weather & Demand → Generate Analysis** to produce a joined weather × demand dataset with a dual-axis chart

The **AFDC EV Charging Stations** connector also works with no configuration — NREL's public `DEMO_KEY` is used by default.

---

## Testing

```bash
# Backend — 51 pytest tests
cd apps/api
pytest

# Frontend smoke tests (requires both servers running)
cd apps/web
npx playwright test
```

---

## Architecture

Each data source follows a connector pattern with two responsibilities:

```
fetch()   →   pull raw data from the source API
clean()   →   read raw file, normalize columns, return a DataFrame
```

The fetch service orchestrates storage: raw CSV → cleaned CSV → dataset metadata JSON. Every dataset is independently addressable by ID and can be previewed or downloaded at any time without re-fetching.

```
POST /sources/{id}/fetch
        │
        ├─ connector.fetch()      → DataFrame + fetched_at
        ├─ save raw CSV           → /data/raw/{source_id}/{dataset_id}.csv
        ├─ connector.clean()      → normalized DataFrame
        ├─ save cleaned CSV       → /data/cleaned/{source_id}/{dataset_id}.csv
        └─ save metadata JSON     → /data/metadata/{dataset_id}.json
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/sources` | List all 14 sources |
| `GET` | `/sources/{id}` | Source detail and metadata |
| `POST` | `/sources/{id}/fetch` | Fetch, clean, and store latest data |
| `GET` | `/datasets` | List all stored datasets |
| `GET` | `/datasets/{id}` | Dataset detail |
| `GET` | `/datasets/{id}/preview?nrows=50` | First N rows as JSON |
| `GET` | `/datasets/{id}/download/cleaned` | Download cleaned CSV |
| `GET` | `/datasets/{id}/download/raw` | Download raw CSV |
| `POST` | `/analysis/weather-demand/join` | Generate weather × demand join |
| `GET` | `/analysis/weather-demand/latest` | Most recent join dataset |
| `GET` | `/analysis/weather-demand/{id}/download` | Download join CSV |

---

## Data Sources

| Source | Category | Status | Notes |
|---|---|---|---|
| Mock Electricity Demand | Electricity | `mock` | Synthetic — diurnal + weekend curves. No key required. |
| EIA ISO-NE Hourly Load | Electricity | `planned` | Connector built — requires `EIA_API_KEY` |
| NOAA Weather | Weather | `planned` | Connector built — requires `NOAA_TOKEN` |
| **ISO-NE CSV Downloads** | Electricity | **`active`** | Live public Hourly Real-Time System Demand CSV â€” no key required |
| **AFDC EV Charging Stations** | EV | **`active`** | Live — `DEMO_KEY` works out of the box |
| EPA eGRID | Environmental | `planned` | Annual emissions data |
| FEMA Flood Maps | Resilience | `planned` | GeoJSON flood zone boundaries |
| EPA EJScreen | Environmental | `planned` | Environmental justice indicators |
| CDC Social Vulnerability Index | Resilience | `planned` | Census-tract equity data |
| Manchester GIS | GIS | `planned` | City infrastructure layers |
| NH Geodata (GRANIT) | GIS | `planned` | UNH statewide GIS repository |
| NHSaves | Regulatory | `planned` | Energy efficiency programs |
| NH Public Utilities Commission | Regulatory | `planned` | Rate cases and regulatory filings |
| Eversource Sustainability Reports | Regulatory | `planned` | Public ESG and grid reports |

---

## API Keys

Keys go in `apps/api/.env`. The app **will not silently use fake data** when a key is missing — it returns a clear 422 error so you know exactly what is needed.

### EIA — Energy Information Administration

Required for `EIA ISO-NE Hourly Load`.

1. Register free at [eia.gov/opendata](https://www.eia.gov/opendata/)
2. Add to `apps/api/.env`:

```env
EIA_API_KEY=your_key_here
```

> The EIA connector is implemented against the v2 API documentation. Items unverified without a live key are marked with `TODO` in `eia_connector.py`.

### NOAA — National Oceanic and Atmospheric Administration

Required for `NOAA Weather` (Manchester-Boston Regional Airport station, GHCND).

1. Request a free token at [ncdc.noaa.gov/cdo-web/token](https://www.ncdc.noaa.gov/cdo-web/token)
2. Add to `apps/api/.env`:

```env
NOAA_TOKEN=your_token_here
```

### NREL / AFDC — EV Charging Stations

No key required for development. `DEMO_KEY` (the default) allows up to 30 requests/day against the live AFDC API. For higher limits:

1. Register free at [developer.nrel.gov/signup](https://developer.nrel.gov/signup/)
2. Add to `apps/api/.env`:

```env
NREL_API_KEY=your_key_here
```

---

## Project Structure

```
gridpulse-nh/
├── apps/
│   ├── api/                    FastAPI backend
│   │   ├── app/
│   │   │   ├── connectors/     One connector class per data source
│   │   │   │   ├── base.py     BaseConnector ABC (fetch + clean interface)
│   │   │   │   ├── mock_connector.py
│   │   │   │   ├── eia_connector.py
│   │   │   │   ├── noaa_connector.py
│   │   │   │   └── afdc_connector.py
│   │   │   ├── routes/         FastAPI routers (sources, datasets, analysis)
│   │   │   ├── schemas/        Pydantic models (Source, Dataset)
│   │   │   └── services/       Storage, dataset, fetch, and analysis logic
│   │   └── tests/              51 pytest tests
│   └── web/                    React + Vite frontend
│       ├── src/
│       │   ├── components/     Layout, cards, tables, badges, buttons
│       │   ├── routes/         One file per page (Dashboard, Sources, Datasets, Analysis)
│       │   ├── services/       Typed API client functions
│       │   └── types/          TypeScript interfaces (Source, Dataset, JoinedRow)
│       └── tests/              Playwright smoke tests
├── data/
│   ├── raw/                    Raw fetched data (gitignored)
│   ├── cleaned/                Cleaned CSVs (gitignored)
│   ├── exports/                User exports (gitignored)
│   └── metadata/               Dataset metadata JSON (gitignored)
└── docs/
    ├── architecture.md
    ├── data_sources.md
    └── roadmap.md
```

---

## Screenshots

> Run locally to explore the interface.

| Page | Description |
|---|---|
| **Dashboard** | Source count stats and quick-links to the top sources |
| **Sources** | 14 source cards with category filter tabs and status badges |
| **Source Detail** | Description, data format, API notes, one-click fetch, dataset link on success |
| **Datasets** | All fetched datasets with row counts, source IDs, and timestamps |
| **Dataset Detail** | Column tag list, scrollable preview table, raw and cleaned CSV downloads |
| **Weather & Demand** | Dual-axis chart — daily peak MW vs. average temperature; HDD/CDD data table |

---

## License

MIT

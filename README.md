<div align="center">

# GridPulse NH

**Weather runs the grid — an interactive public-data story about New England electricity.**

[![Live](https://img.shields.io/badge/live-ajcondondev.github.io%2Fgridpulse--nh-1d4ed8?style=flat-square)](https://ajcondondev.github.io/gridpulse-nh/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Observable Plot](https://img.shields.io/badge/Observable_Plot-charts-e0e0e0?style=flat-square)](https://observablehq.com/plot/)
[![pandas](https://img.shields.io/badge/pandas-pipeline-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tests](https://img.shields.io/badge/tests-197_passing-22c55e?style=flat-square&logo=pytest&logoColor=white)](#testing)
[![License](https://img.shields.io/badge/license-MIT-64748b?style=flat-square)](#license)

**[Live Story](https://ajcondondev.github.io/gridpulse-nh/) · [The Data Pipeline](#the-data-pipeline) · [Getting Started](#getting-started) · [Methodology](docs/methodology.md) · [Data Sources](#data-sources)**

</div>

---

## Overview

GridPulse turns 18 months of real public data — hourly ISO New England electricity demand, generation by fuel, and New Hampshire weather — into an interactive, scroll-through data story:

1. **The heartbeat** — 30 days of hourly demand and its daily double-peak rhythm
2. **The V-curve** — 546 days of temperature vs. peak demand, the signature shape of a weather-driven grid
3. **A year of peaks** — a calendar heatmap showing the hard days clustering in deep winter and high summer
4. **Event replay** — an hour-by-hour scrubbable replay of the June 2025 heat wave (25,898 MW peak, oil plants at 16% of the mix), with annotations computed from the data
5. **The fuel mix** — what actually generates New England's power, day by day

**The story runs with zero servers and zero API keys**: a Python pipeline fetches and normalizes the data into small, committed JSON artifacts, and the site is deployed statically to GitHub Pages. Every chart carries its source, caveats, and a freshness stamp.

The repo also contains the **data workbench** the project grew from — a FastAPI backend with 19 tested connectors to public energy/weather/resilience datasets, browsable under **Data Explorer** when running locally.

> **Disclaimer:** All data comes from publicly available APIs and government datasets. Educational/portfolio project — not affiliated with ISO New England, EIA, Eversource, or any utility. See [data source disclaimers](docs/data_source_disclaimers.md).

---

## The Data Pipeline

```
EIA-930 bulk files (hourly demand + fuel mix, keyless)   Open-Meteo / ERA5 (hourly temps, keyless)
        │                                                        │
        └──────────────► pipeline/ (Python + pandas) ◄───────────┘
                                   │
             data/raw (gitignored) → data/interim (gitignored)
                                   │
                    data/processed/*.json  ← committed, ~900 KB
                                   │
                 ┌─────────────────┴─────────────────┐
            apps/web story page                (future) Remotion video
```

Rebuild everything (fetch + process) or rebuild offline from cached raw files:

```bash
apps/api/.venv/Scripts/python -m pipeline.run              # full refresh
apps/api/.venv/Scripts/python -m pipeline.run --offline    # rebuild from cache
```

The event replay's featured week is **auto-selected** by `pipeline/pick_event.py`, which scores every day by demand percentile × temperature extremity — no hand-picking. Conventions, units, and honest limits are documented in [docs/methodology.md](docs/methodology.md).

---

## Features

- **22-source catalog** spanning electricity, gas, weather, EV, solar, environmental, resilience, GIS, and regulatory categories
- **18 implemented connectors**, 13 of which need no API key:
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
  - NH municipal geography (Census 2020, all NH towns with FIPS and population)
- **Dataset pipeline**: raw save, clean, metadata, preview, CSV download
- **Weather and demand analysis**: joins daily peak MW with temperature, HDD, and CDD; dual-axis Recharts visualization
- **Source status model**: `active`, `requires_key`, `research`, `not_implemented`, and `test_fixture_only` clearly labeled in the UI
- **Synthetic mock demand generator** for automated tests and offline pipeline development

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Story frontend** | React 18, TypeScript, Vite, Tailwind CSS, Observable Plot, Motion, React Router v6 |
| **Data pipeline** | Python 3.11+, pandas, httpx → committed JSON artifacts in `data/processed` |
| **Workbench backend** | FastAPI, pydantic v2, uvicorn, openpyxl (local dev; the story needs no backend) |
| **Storage** | Local filesystem: `data/raw`, `data/interim`, `data/cleaned`, `data/metadata` (gitignored); `data/processed` committed |
| **Testing & CI** | pytest (188 API + 9 pipeline), Playwright smoke tests, GitHub Actions CI + Pages deploy |

---

## Getting Started

**Just want the story?** It's live at [ajcondondev.github.io/gridpulse-nh](https://ajcondondev.github.io/gridpulse-nh/) — or run only Terminal 2 below and open `http://localhost:5173` (the story page reads committed data and needs no API).

**For the full workbench (Data Explorer, fetching new data)** you need two terminals running at the same time: one for the API, one for the web app.

### Prerequisites

- Python 3.11+
- Node.js 20+

---

### Terminal 1: API (FastAPI)

```bash
# From the repo root:
cd apps/api

# Create and activate a virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env (API keys are optional to start, see below)
cp .env.example .env

# Start the API server
uvicorn app.main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Verify it's working:** open `http://localhost:8000/health`. You should get `{"status":"ok"}`.

---

### Terminal 2: Web App (React + Vite)

Open a **new terminal** (keep Terminal 1 running):

```bash
# From the repo root:
cd apps/web

npm install
cp .env.example .env.local
npm run dev
```

You should see:

```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173` in your browser.

---

### URLs at a glance

| Service | URL |
|---|---|
| Web app | `http://localhost:5173` |
| API | `http://localhost:8000` |
| Interactive API docs (Swagger) | `http://localhost:8000/docs` |

---

### Your first fetch (no API key needed)

1. Open the web app at `http://localhost:5173`
2. Click **Sources** in the nav
3. Click **ISO-NE CSV Downloads**, then **Fetch Latest Data**
4. Click **Datasets** in the nav; the fetched data appears there
5. Click the dataset, then **Preview** to see the cleaned rows, or **Download CSV**

All 13 sources in the [no-key table below](#no-api-key-required) work the same way.

### Try It Without Any API Key

All of the following work with no configuration:

| Source | What it fetches |
|---|---|
| **ISO-NE CSV Downloads** | Hourly real-time system demand for ISO New England |
| **ISO-NE Generation Fuel Mix** | Hourly MW by fuel type: gas, nuclear, hydro, solar, wind, and more |
| **ISO-NE Hourly Load Forecast** | 7-day ahead hourly system load forecast |
| **ISO-NE Zone LMP Prices** | Real-time hourly wholesale LMP for all ISO-NE zones including NH |
| **NREL PVWatts Solar Estimates** | Monthly solar output for Manchester, Concord, Portsmouth, Keene (DEMO_KEY) |
| **AFDC EV Charging Stations** | NH EV station locations, port counts, and access type (DEMO_KEY) |
| **OpenEI Utility Rates** | Residential utility rates near NH service territory |
| **EPA eGRID** | Subregion emission rates: CO2e, NOx, SO2 |
| **EPA EJScreen** | NH block-group EJ indicators: pollution burden and demographic percentiles |
| **EIA AMI Smart Meters** | NH utility smart meter deployment counts and penetration rates |
| **FEMA Flood Maps** | NH flood zone designations by county (AE, X, VE zones) |
| **CDC Social Vulnerability Index** | NH census tract SVI, 4 equity theme percentiles |
| **NH Geodata** | All NH towns and cities with FIPS codes and 2020 Census population |

Suggested path: fetch **ISO-NE CSV**, then **ISO-NE Fuel Mix**, then **EPA EJScreen** or **CDC SVI**, then run the **Weather & Demand** analysis.

---

## Testing

```bash
# Backend: 188 tests
cd apps/api
pytest

# Pipeline transforms: 9 tests (from the repo root)
apps/api/.venv/Scripts/python -m pytest pipeline/tests

# Frontend smoke tests (starts the Vite dev server itself;
# the API must already be running on port 8000)
cd apps/web
npx playwright test
```

CI runs the backend tests, pipeline tests, and the production web build on every push; a separate workflow deploys the story to GitHub Pages.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/sources` | List all sources with full metadata |
| `GET` | `/sources/{id}` | Source detail: status, access method, key requirements |
| `POST` | `/sources/{id}/fetch` | Fetch, clean, and store latest data |
| `GET` | `/datasets` | List stored datasets |
| `GET` | `/datasets/{id}` | Dataset detail and column list |
| `GET` | `/datasets/{id}/preview?nrows=50` | Preview cleaned rows as JSON |
| `GET` | `/datasets/{id}/download/cleaned` | Download cleaned CSV |
| `GET` | `/datasets/{id}/download/raw` | Download raw CSV |
| `POST` | `/analysis/weather-demand/join` | Generate weather and demand join |
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

There is also a synthetic **Mock Electricity Demand** generator used by the automated tests. It is hidden from the sources list by default (`GET /sources?include_mock=true` shows it).

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
| Manchester GIS | GIS | `research`: no confirmed stable public API |
| NHSaves | Regulatory | `not_implemented`: HTML/PDF, no structured API |
| NH Public Utilities Commission | Regulatory | `not_implemented`: PDF filings only |
| Eversource Sustainability Reports | Regulatory | `not_implemented`: annual PDFs only |

---

## API Keys

Keys go in `apps/api/.env` (gitignored, never committed). Connectors that need a key return a clear error if it is missing; nothing is hardcoded.

```env
EIA_API_KEY=your_key_here         # EIA ISO-NE load + retail electricity + natural gas prices
NOAA_TOKEN=your_key_here
NREL_API_KEY=your_key_here        # optional; DEMO_KEY used by default for AFDC and PVWatts
OPENEI_API_KEY=your_key_here      # optional; public access attempted first
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
pipeline/                       # public data -> committed artifacts
  fetch_eia930.py               # EIA-930 bulk six-month files (keyless)
  fetch_weather.py              # Open-Meteo / ERA5 hourly temps (keyless)
  transforms.py                 # pure, unit-tested tidy transforms
  pick_event.py                 # auto-selects the featured event window
  build_processed.py, run.py    # artifact builder + orchestrator
  tests/                        # 9 pytest tests
data/
  processed/                    # committed JSON artifacts (the app's data contract)
  raw/ interim/ metadata/       # gitignored working tiers
apps/
  web/src/story/                # the story page
    StoryPage.tsx
    ChartCard.tsx, chartTheme.ts
    charts/                     # HeartbeatChart, VCurveChart, CalendarHeatmap,
                                # EventReplay (scrubber), FuelMixChart
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
```

---

## Notes

- These connectors depend on external public endpoints (ISO-NE transform/csv exports, EPA ArcGIS services, agency download URLs) that can change without notice. Where a URL or response schema still needs live re-verification, the connector source is marked with a TODO comment. If a fetch starts failing, check the endpoint noted in that connector first.
- The connectors are tested against recorded fixtures; the EIA hourly load and NOAA connectors in particular should be verified against a live key before relying on their output.
- Fetched data is stored on the local filesystem only. There is no database or scheduler; fetches are on demand.

---

## License

MIT

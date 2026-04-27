<div align="center">

# GridPulse NH

**Public utility, weather, EV, price, and emissions data in one workbench.**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![pandas](https://img.shields.io/badge/pandas-2-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tests](https://img.shields.io/badge/tests-88_passing-22c55e?style=flat-square&logo=pytest&logoColor=white)](#testing)
[![License](https://img.shields.io/badge/license-MIT-64748b?style=flat-square)](LICENSE)

**[Getting Started](#getting-started) · [API Reference](#api-reference) · [Data Sources](#data-sources) · [API Keys](#api-keys)**

</div>

---

## Overview

GridPulse NH is a full-stack utility data engineering workbench focused on New Hampshire and ISO New England. The backend uses a connector-per-source pattern with `fetch()` and `clean()` methods, stores raw and cleaned files separately, and saves dataset metadata so every fetch can be previewed or downloaded later without re-running the source request.

The current app supports live public demand, weather, EV, price, and emissions context sources alongside a synthetic demand generator for offline development and a weather x demand analysis workflow.

> **Disclaimer:** All data is sourced from publicly available APIs and datasets.

---

## Features

- **15-source catalog** spanning electricity, weather, EV, environmental, resilience, GIS, and regulatory categories
- **Live source connectors** for ISO-NE public hourly demand CSV, OpenEI utility rates, EPA eGRID summary emissions, AFDC EV stations, EIA ISO-NE hourly load, and NOAA weather
- **Dataset pipeline** with raw save -> clean save -> metadata -> preview -> download
- **Synthetic demand generator** for local development and testing
- **Weather x demand analysis** joining daily peak demand with temperature, HDD, and CDD

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Recharts |
| **Backend** | Python 3.11+, FastAPI, pandas, pydantic v2, uvicorn, httpx |
| **Storage** | Local filesystem under `/data/raw`, `/data/cleaned`, `/data/exports`, `/data/metadata` |
| **Testing** | pytest backend suite, Playwright frontend smoke tests |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Optional free API keys for EIA and NOAA

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

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- App: `http://localhost:5173`

### Try It Immediately

No key is required for:

- `Mock Electricity Demand`
- `ISO-NE CSV Downloads`
- `EPA eGRID`
- `AFDC EV Charging Stations` using `DEMO_KEY`

Suggested quick path:

1. Fetch `ISO-NE CSV Downloads`
2. Fetch `EPA eGRID`
3. Fetch `NOAA Weather` if you have `NOAA_TOKEN`
4. Generate the Weather & Demand analysis

---

## Testing

```bash
# Backend
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
| `GET` | `/sources` | List all 15 sources |
| `GET` | `/sources/{id}` | Source detail and metadata |
| `POST` | `/sources/{id}/fetch` | Fetch, clean, and store latest data |
| `GET` | `/datasets` | List stored datasets |
| `GET` | `/datasets/{id}` | Dataset detail |
| `GET` | `/datasets/{id}/preview?nrows=50` | Preview cleaned rows as JSON |
| `GET` | `/datasets/{id}/download/cleaned` | Download cleaned CSV |
| `GET` | `/datasets/{id}/download/raw` | Download raw CSV |
| `POST` | `/analysis/weather-demand/join` | Generate weather x demand join |
| `GET` | `/analysis/weather-demand/latest` | Latest join dataset |
| `GET` | `/analysis/weather-demand/{id}/download` | Download join CSV |

---

## Data Sources

| Source | Category | Status | Notes |
|---|---|---|---|
| Mock Electricity Demand | Electricity | `mock` | Synthetic development data |
| EIA ISO-NE Hourly Load | Electricity | `planned` | Connector built, requires `EIA_API_KEY` |
| NOAA Weather | Weather | `planned` | Connector built, requires `NOAA_TOKEN` |
| ISO-NE CSV Downloads | Electricity | `active` | Public Hourly Real-Time System Demand CSV |
| OpenEI Utility Rates | Electricity | `active` | Residential utility rate context near NH service territory |
| AFDC EV Charging Stations | EV | `active` | Uses `DEMO_KEY` by default |
| EPA eGRID | Environmental | `active` | Public subregion emissions summary table |
| EPA EJScreen | Environmental | `planned` | Not implemented |
| FEMA Flood Maps | Resilience | `planned` | Not implemented |
| CDC Social Vulnerability Index | Resilience | `planned` | Not implemented |
| Manchester GIS | GIS | `planned` | Not implemented |
| NH Geodata (GRANIT) | GIS | `planned` | Not implemented |
| NHSaves | Regulatory | `planned` | Not implemented |
| NH Public Utilities Commission | Regulatory | `planned` | Not implemented |
| Eversource Sustainability Reports | Regulatory | `planned` | Not implemented |

---

## API Keys

Keys go in `apps/api/.env`.

```env
EIA_API_KEY=your_key_here
NOAA_TOKEN=your_key_here
NREL_API_KEY=your_key_here
OPENEI_API_KEY=your_key_here
```

Notes:

- `ISO-NE CSV Downloads` and `EPA eGRID` do not require a key.
- `AFDC EV Charging Stations` works without configuration using `DEMO_KEY`.
- `OpenEI Utility Rates` attempts public access first; set `OPENEI_API_KEY` only if OpenEI rejects unauthenticated requests.

---

## Project Structure

```text
apps/
  api/
    app/
      connectors/
        afdc_connector.py
        egrid_connector.py
        eia_connector.py
        isone_csv_connector.py
        mock_connector.py
        noaa_connector.py
        openei_rates_connector.py
      routes/
      schemas/
      services/
    tests/
  web/
    src/
    tests/
data/
docs/
```

---

## License

MIT

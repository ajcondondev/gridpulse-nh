# GridPulse NH

**Public utility, weather, EV, and grid data in one workbench.**

GridPulse NH is a portfolio application that pulls, cleans, previews, and exports public utility-related datasets for New Hampshire — ISO New England electricity load, NOAA weather, EV charging infrastructure, EPA emissions data, and more.

> Not official Eversource software. Public data relevant to New Hampshire utility analysis.

---

## Features

- Browse 14 public utility data sources across electricity, weather, EV, environmental, resilience, and GIS categories
- Fetch and clean live data from NREL AFDC (EV stations), EIA, and NOAA APIs
- Generate synthetic mock electricity demand for development and testing
- Preview cleaned datasets in a paginated table interface
- Download raw and cleaned CSVs for offline analysis
- Correlate weather and electricity demand with a dual-axis Recharts chart
- Filter sources by category; navigate directly from source → fetch → dataset

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router v6 |
| Backend | Python 3.11+, FastAPI, pandas, pydantic v2, uvicorn |
| Storage | Local filesystem (`/data/raw`, `/data/cleaned`, `/data/exports`) |
| Testing | pytest (backend), Playwright (frontend smoke tests) |

## Project Structure

```
utility-data-hub/
  apps/
    api/          FastAPI backend
    web/          React + Vite frontend
  data/
    raw/          Raw fetched data (gitignored)
    cleaned/      Cleaned CSVs (gitignored)
    exports/      User-downloadable exports (gitignored)
    metadata/     Dataset metadata JSON (gitignored)
  docs/
    architecture.md
    data_sources.md
    roadmap.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+

### Backend

```bash
cd apps/api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # add your API keys
uvicorn app.main:app --reload
```

API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### Frontend

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

App available at: `http://localhost:5173`

### Run Backend Tests

```bash
cd apps/api
pytest
```

## API Keys

### EIA (Energy Information Administration)

Required for `EIA ISO-NE Hourly Load` source.

1. Register free at https://www.eia.gov/opendata/
2. Copy your API key
3. Add it to `apps/api/.env`:

```
EIA_API_KEY=your_key_here
```

Without this key, fetching the EIA source returns a clear error message — it will not crash or return fake data.

> **Note:** The EIA connector endpoint and response schema are implemented based on EIA v2 API documentation but have not been verified against a live response. TODOs are marked in `eia_connector.py`.

### NOAA (National Oceanic and Atmospheric Administration)

Required for `NOAA Weather` source (Phase 4).

1. Request a token at https://www.ncdc.noaa.gov/cdo-web/token
2. Add it to `apps/api/.env`:

```
NOAA_TOKEN=your_token_here
```

### NREL / AFDC (EV Charging Stations)

The AFDC EV connector uses `DEMO_KEY` by default — no registration required for low-volume testing (30 requests/day). For production use, get a free key:

1. Register at https://developer.nrel.gov/signup/
2. Add it to `apps/api/.env`:

```
NREL_API_KEY=your_key_here
```

Without a real key, `DEMO_KEY` still fetches live AFDC data — it just has stricter rate limits.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/sources` | List all data sources |
| `GET` | `/sources/{id}` | Get source detail |
| `POST` | `/sources/{id}/fetch` | Fetch latest data |
| `GET` | `/datasets` | List fetched datasets |
| `GET` | `/datasets/{id}` | Get dataset detail |
| `GET` | `/datasets/{id}/download/cleaned` | Download cleaned CSV |
| `GET` | `/datasets/{id}/download/raw` | Download raw data |
| `GET` | `/datasets/{id}/preview` | First 50 rows as JSON |

## Data Sources

| Source | Category | Status |
|---|---|---|
| Mock Electricity Demand | Electricity | Mock (dev/test) |
| EIA ISO-NE Hourly Load | Electricity | Structured — requires `EIA_API_KEY` |
| NOAA Weather | Weather | Planned |
| ISO-NE CSV Downloads | Electricity | Planned |
| AFDC EV Charging Stations | EV | Active — uses `DEMO_KEY` by default |
| EPA eGRID | Environmental | Planned |
| FEMA Flood Maps | Resilience | Planned |
| EPA EJScreen | Environmental | Planned |
| CDC Social Vulnerability Index | Resilience | Planned |
| Manchester GIS | GIS | Planned |
| NH Geodata | GIS | Planned |
| NHSaves | Regulatory | Planned |
| NH Public Utilities Commission | Regulatory | Planned |
| Eversource Sustainability Reports | Regulatory | Planned |

## Screenshots

> Run the app locally to explore the interface (`npm run dev` + `uvicorn app.main:app --reload`).

| Page | Description |
|---|---|
| Dashboard | Source count overview + quick links |
| Sources | Category-filtered source grid with status badges |
| Source Detail | Fetch button, API key notes, dataset link on success |
| Datasets | List of fetched datasets with row counts |
| Dataset Detail | Column tags, preview table, cleaned + raw CSV downloads |
| Weather & Demand | Dual-axis chart: peak MW vs. average temperature |

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the full phased plan.

## License

MIT — See LICENSE for details.

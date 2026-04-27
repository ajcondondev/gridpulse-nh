# Roadmap

## Phase 0 — Repository Scaffold ✅
- Repo structure, README, docs, .gitignore
- Data directory layout with `.gitkeep` placeholders

## Phase 1 — Static API + Frontend Shell ✅
- FastAPI backend: `/health`, `/sources`, `/sources/{id}`
- Static source registry (14 sources, metadata only)
- React + Vite + Tailwind frontend
- All pages stubbed: Dashboard, Sources, Source Detail, Datasets, Dataset Detail, Weather & Demand
- Source cards with status badges
- Disabled fetch button placeholder

## Phase 2 — Mock Dataset Flow
- `POST /sources/mock_demand/fetch` generates synthetic demand data
- Raw CSV saved to `/data/raw/mock_demand/`
- Cleaned CSV saved to `/data/cleaned/mock_demand/`
- Dataset metadata saved to `/data/metadata/`
- `GET /datasets` returns real dataset records
- `GET /datasets/{id}/download/cleaned` streams file
- Frontend: Datasets page lists real datasets
- Frontend: Dataset detail shows preview table + download button

## Phase 3 — EIA Connector
- Implement `EIAConnector` with real API call to EIA v2 API
- Fetch ISO-NE region hourly load
- Clean: parse timestamps, normalize MW values, drop nulls
- Requires `EIA_API_KEY`

## Phase 4 — NOAA Connector
- Implement `NOAAConnector` for NH stations
- Fetch temperature, dew point, wind speed
- Clean: pivot to wide format, interpolate gaps
- Requires `NOAA_TOKEN`

## Phase 5 — Weather & Demand Analysis
- Join NOAA weather + EIA load by timestamp
- `/analysis/weather-demand` page: Recharts scatter plot
- Correlation coefficient display
- Date range selector

## Phase 6 — AFDC EV Connector
- Implement `AFDCConnector`
- Fetch NH EV charging stations
- Map view (Leaflet or similar) on a new `/analysis/ev-map` page

## Phase 7 — Polish & Portfolio
- Playwright smoke tests passing in CI
- GitHub Actions workflow
- Deployed preview (Railway / Render for API, Netlify / Vercel for frontend)
- README with screenshots

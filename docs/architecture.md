# Architecture

## Overview

GridPulse NH uses a simple two-tier architecture: a FastAPI backend serving data from local filesystem storage, and a React SPA frontend consuming it over HTTP.

```
┌─────────────────────────────────┐
│         React Frontend          │
│  (Vite, TypeScript, Tailwind)   │
│      http://localhost:5173      │
└────────────┬────────────────────┘
             │ HTTP / JSON
             ▼
┌─────────────────────────────────┐
│       FastAPI Backend           │
│   (Python, pydantic, pandas)    │
│      http://localhost:8000      │
└────────────┬────────────────────┘
             │ filesystem I/O
             ▼
┌─────────────────────────────────┐
│       Local Data Storage        │
│  /data/raw, /data/cleaned,      │
│  /data/exports, /data/metadata  │
└─────────────────────────────────┘
```

## Backend

### Entry Point

`apps/api/app/main.py` — creates the FastAPI app, registers CORS, includes routers, and ensures data directories exist on startup.

### Routers

- `routes/health.py` — `/health` liveness check
- `routes/sources.py` — source catalog CRUD + fetch trigger
- `routes/datasets.py` — dataset listing and file download

### Connectors

Each data source has a connector class implementing `BaseConnector`:

```python
class BaseConnector(ABC):
    source_id: str
    def fetch(self) -> dict: ...    # pull raw data
    def clean(self, raw_path) -> pd.DataFrame: ...  # clean it
```

Connectors live in `app/connectors/`. Only `MockConnector` is fully implemented in Phase 1–2.

### Source Registry

`app/registry.py` holds the static list of `Source` objects representing all 14 known data sources. This is metadata only — no live fetching.

### Services

- `storage_service.py` — resolves paths under `/data/`, ensures directories exist
- `dataset_service.py` — dataset lifecycle management (Phase 2+)

### Configuration

`app/config.py` uses `pydantic-settings` to load from environment variables / `.env` file.

## Frontend

### Routing

React Router v6 with `createBrowserRouter`. Layout wraps all routes via `<Outlet />`.

### Pages

- `/` — Dashboard: stats overview + recent sources list
- `/sources` — filterable source card grid
- `/sources/:id` — source detail with disabled fetch button (Phase 1)
- `/datasets` — dataset table (placeholder in Phase 1)
- `/datasets/:id` — dataset detail + download (Phase 2+)
- `/analysis/weather-demand` — weather vs. demand chart (Phase 5+)

### API Client

`src/services/apiClient.ts` wraps `fetch` with error handling. `sourcesApi.ts` and `datasetsApi.ts` call typed endpoints.

## Data Flow (Phase 2+)

```
User clicks "Fetch"
  → POST /sources/{id}/fetch
  → Connector.fetch() → saves to /data/raw/{id}/
  → Connector.clean() → saves to /data/cleaned/{id}/
  → Dataset metadata saved to /data/metadata/
  → GET /datasets returns new dataset
  → User previews table, downloads CSV
```

## Design Decisions

- **Local filesystem first** — no database until there's a clear need for querying across datasets.
- **Connector pattern** — isolates per-source fetch/clean logic; each source is independently replaceable.
- **No auth, no Docker** — keeps the portfolio demo runnable with a single `uvicorn` command.
- **Mock connector** — allows full UI/flow testing without real API keys.

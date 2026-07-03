# Source Catalog

_Generated from `apps/api/app/registry.py` — the registry is the source of truth. Regenerate with `python -m scripts.gen_source_catalog` from `apps/api`._

22 sources. Statuses: `active` (working connector), `requires_key` (works with a free key), `research` / `not_implemented` (no stable public API yet), `test_fixture_only` (synthetic, tests only).

| Source | Category | Status | API key | Format | Geography | Updates |
|---|---|---|---|---|---|---|
| ISO-NE CSV Downloads | electricity | `active` | none | CSV | iso_ne | Daily |
| AFDC EV Charging Stations | ev | `active` | `NREL_API_KEY` (optional) | JSON | nh | Weekly |
| OpenEI Utility Rates | electricity | `active` | `OPENEI_API_KEY` (optional) | JSON | nh | As updated |
| EPA eGRID | environmental | `active` | none | HTML/CSV | national | Annual |
| FEMA Flood Maps | resilience | `active` | none | JSON | nh | As updated |
| CDC Social Vulnerability Index | resilience | `active` | none | CSV | nh | Every 2 years |
| NH Geodata (GRANIT) | gis | `active` | none | JSON | nh | Decennial |
| EIA AMI Smart Meter Deployment | electricity | `active` | none | Excel (ZIP) | nh | Annual |
| NREL PVWatts Solar Estimates | solar | `active` | `NREL_API_KEY` (optional) | JSON | nh | On demand |
| ISO-NE Generation Fuel Mix | electricity | `active` | none | CSV | iso_ne | Hourly |
| ISO-NE Hourly Load Forecast | electricity | `active` | none | CSV | iso_ne | Hourly |
| EIA Natural Gas Retail Prices | gas | `requires_key` | `EIA_API_KEY` (required) | JSON | nh | Monthly |
| EIA Retail Electricity Prices | electricity | `requires_key` | `EIA_API_KEY` (required) | JSON | nh | Monthly |
| EIA ISO-NE Hourly Load | electricity | `requires_key` | `EIA_API_KEY` (required) | JSON | iso_ne | Hourly |
| NOAA Weather | weather | `requires_key` | `NOAA_TOKEN` (required) | JSON | nh | Daily |
| ISO-NE Wholesale LMP Prices | electricity | `active` | none | CSV | iso_ne | Hourly |
| Manchester GIS | gis | `research` | none | Shapefile/GeoJSON | nh | As updated |
| EPA EJScreen | environmental | `active` | none | JSON | nh | Annual |
| NHSaves | regulatory | `not_implemented` | none | HTML/PDF | nh | As published |
| NH Public Utilities Commission | regulatory | `not_implemented` | none | PDF/HTML | nh | As filed |
| Eversource Sustainability Reports | regulatory | `not_implemented` | none | PDF | nh | Annual |
| Mock Electricity Demand | electricity | `test_fixture_only` | none | CSV | nh | On demand |

Per-source URLs, notes, and last-verified dates are available in the app under **Sources**, or via `GET /sources`.

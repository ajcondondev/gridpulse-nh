# Data Sources

All data sources are public. GridPulse NH does not use private utility data or internal Eversource systems.

---

## Electricity

### Mock Electricity Demand
- **ID:** `mock_demand`
- **Status:** Mock (development/testing only)
- **Description:** Synthetic hourly demand data with realistic diurnal and weekly patterns. Generated in-process — no external call.
- **Format:** CSV
- **Notes:** Clearly labeled as mock. Not real data.

### EIA ISO-NE Hourly Load
- **ID:** `eia_isone_load`
- **Status:** Planned
- **URL:** https://api.eia.gov/v2/electricity/rto/region-data/data/
- **Description:** U.S. Energy Information Administration API — ISO New England region hourly electricity demand.
- **Requires:** `EIA_API_KEY` environment variable (free registration at https://www.eia.gov/opendata/)
- **Format:** JSON → CSV

### ISO-NE CSV Downloads
- **ID:** `isone_csv`
- **Status:** Active
- **URL:** https://www.iso-ne.com/isoexpress/web/reports/load-and-demand/-/tree/dmnd-rt-hourly-sys
- **Description:** ISO New England public CSV download support. The current implementation fetches Hourly Real-Time System Demand directly from ISO-NE with no API key required.
- **Format:** CSV

---

## Weather

### NOAA Weather
- **ID:** `noaa_weather`
- **Status:** Planned
- **URL:** https://www.ncdc.noaa.gov/cdo-web/api/v2/data
- **Description:** Historical and recent observations from NOAA stations in New Hampshire (Manchester, Concord, Portsmouth).
- **Requires:** `NOAA_TOKEN` environment variable (free at https://www.ncdc.noaa.gov/cdo-web/token)
- **Format:** JSON → CSV

---

## EV / Transportation

### AFDC EV Charging Stations
- **ID:** `afdc_ev`
- **Status:** Planned
- **URL:** https://developer.nrel.gov/api/alt-fuel-stations/v1.json
- **Description:** Alternative Fuels Data Center — EVSE station locations in New Hampshire.
- **Requires:** NREL API key (free at https://developer.nrel.gov/signup/)
- **Format:** JSON → CSV

---

## Environmental

### EPA eGRID
- **ID:** `epa_egrid`
- **Status:** Planned
- **URL:** https://www.epa.gov/egrid/download-data
- **Description:** Emissions & Generation Resource Integrated Database. Plant-level and subregion-level generation and emissions data. ISO-NE subregion: NEWE.
- **Format:** Excel/CSV (annual release)

### EPA EJScreen
- **ID:** `epa_ejscreen`
- **Status:** Planned
- **URL:** https://ejscreen.epa.gov/mapper/
- **Description:** Environmental justice screening data for NH census tracts — pollution burden, demographic indicators.
- **Format:** CSV (annual release)

---

## Resilience

### FEMA Flood Maps
- **ID:** `fema_flood`
- **Status:** Planned
- **URL:** https://msc.fema.gov/portal/home
- **Description:** National Flood Insurance Program flood zone boundaries for NH municipalities.
- **Format:** GeoJSON / Shapefile

### CDC Social Vulnerability Index
- **ID:** `cdc_svi`
- **Status:** Planned
- **URL:** https://www.atsdr.cdc.gov/placeandhealth/svi/data_documentation_download.html
- **Description:** CDC/ATSDR SVI for NH — 16 social factors grouped into four themes. Supports equity-aware utility planning analysis.
- **Format:** CSV (biennial release)

---

## GIS

### Manchester GIS
- **ID:** `manchester_gis`
- **Status:** Planned
- **URL:** https://www.manchesternh.gov/Departments/Information-Technology/GIS
- **Description:** City of Manchester, NH geographic data — infrastructure, parcels, zoning.
- **Format:** Shapefile / GeoJSON

### NH Geodata (GRANIT)
- **ID:** `nh_geodata`
- **Status:** Planned
- **URL:** https://www.granit.unh.edu/
- **Description:** UNH statewide NH GIS repository — roads, utilities, municipal boundaries, environmental layers.
- **Format:** Shapefile / GeoJSON

---

## Regulatory

### NHSaves
- **ID:** `nhsaves`
- **Status:** Planned
- **URL:** https://www.nhsaves.com/
- **Description:** Public program information for NH energy efficiency programs. Eversource-adjacent public data.
- **Format:** HTML / PDF
- **Notes:** Not official Eversource software.

### NH Public Utilities Commission
- **ID:** `nh_puc`
- **Status:** Planned
- **URL:** https://www.puc.nh.gov/
- **Description:** NH PUC regulatory filings, rate cases, dockets, and orders. Public record.
- **Format:** PDF / HTML

### Eversource Sustainability Reports
- **ID:** `eversource_sustainability`
- **Status:** Planned
- **URL:** https://www.eversource.com/content/general/about/sustainability
- **Description:** Publicly available ESG, sustainability, and grid modernization reports from Eversource Energy.
- **Format:** PDF (annual)
- **Notes:** Public data relevant to New Hampshire utility analysis. Not official Eversource software.

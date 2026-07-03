# Methodology & Data Notes

How GridPulse turns public data into the story charts, and what the numbers do and don't mean.

## Sources

| Source | What we use | Key | License |
|---|---|---|---|
| [EIA-930 Hourly Electric Grid Monitor](https://www.eia.gov/electricity/gridmonitor/about) — bulk six-month files | Hourly demand and net generation by fuel type for the **ISNE** (ISO New England) balancing authority | none | U.S. Government work, public domain |
| [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) (ERA5) | Hourly 2-meter temperature for Concord, NH (43.2081, −71.5376) | none | CC BY 4.0; underlying ERA5 © Copernicus |

The repository also contains a broader source workbench (`apps/api`) with connectors for 19+ public datasets; the story charts are built only from the two sources above. See `docs/source_catalog.md` and `docs/data_source_disclaimers.md`.

> **Note (2026-07):** ISO-NE's public `/transform/csv/*` export endpoints began returning HTTP 403 to non-browser clients, so the pipeline uses EIA-930 bulk files (the same hourly demand/fuel data, published by EIA) instead of fetching from ISO-NE directly.

## Pipeline

```
data/raw       untouched downloads (EIA-930 six-month CSVs, ~47 MB each)   [gitignored]
data/interim   ISNE-filtered rows, hourly Concord temps                    [gitignored]
data/processed small tidy JSON artifacts consumed by the app               [committed]
```

Rebuild everything with:

```bash
apps/api/.venv/Scripts/python -m pipeline.run          # fetch + rebuild
apps/api/.venv/Scripts/python -m pipeline.run --offline # rebuild from cache
```

Transforms are pure functions in `pipeline/transforms.py` with unit tests in `pipeline/tests/`.

## Conventions

- **Timestamps**: `ts_utc` is the hour-**beginning** timestamp in UTC. EIA-930 publishes hour-ending timestamps; we shift by −1 hour. Local dates use `America/New_York`.
- **Units in names**: `demand_mw`, `temp_f`, `gen_mw`. No unit-less values.
- **Missing data stays missing**: failed parses become null and are dropped with counts recorded in `meta.json` — never filled with zeros. Synthetic/mock data never enters `data/processed`.
- **Daily aggregation**: local-calendar days; partial days (< 23 hours) are dropped. DST days legitimately have 23/25 hours and are kept.
- **Degree days**: HDD = max(0, 65 − daily mean °F), CDD = max(0, mean − 65).
- **Fuel groups**: EIA's detailed columns are grouped (e.g., solar with + without storage → `solar`; pumped storage + batteries → `storage`). Fuel *shares* divide each fuel's positive generation by the day's total positive generation; negative values (storage charging, pumping) are kept in MW but excluded from share denominators.
- **Adjusted series preferred**: where EIA publishes both raw and "(Adjusted)" columns, the adjusted series is used.

## Event selection

`pipeline/pick_event.py` scores every day by demand percentile × temperature extremity (both cold and heat), picks the top-scoring day, and exports a 7-day hourly window around it plus annotations. **All annotation numbers are computed from the data** — peak MW, extreme temperature, maximum oil share. Nothing is hand-picked or generated.

## Honest limits

- EIA-930 hourly values include **imputed and later-corrected** data; real-time values are preliminary. Not settlement-quality.
- One weather point (Concord) is a **proxy** for regional weather; ISO-NE itself uses weighted multi-city composites. The temperature–demand relationship shown is illustrative, not a forecasting model.
- ERA5 is a **reanalysis** (model-blended), not raw station observations.
- Fuel mix covers generation **within** ISO-NE; imported power's upstream mix is excluded.
- This is an educational/portfolio project — not affiliated with ISO New England, EIA, or any utility.

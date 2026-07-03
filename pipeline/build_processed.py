"""Build the committed app-ready artifacts in data/processed.

Artifacts (the contract between pipeline ⇄ web app ⇄ video renderer):

- demand_hourly.json      recent HOURLY_WINDOW_DAYS of {ts, demand_mw}
- demand_daily.json       full range {date, peak_mw, avg_mw}
- temp_demand_daily.json  full range {date, temp_avg_f, hdd, cdd, peak_mw, ...}
- fuel_mix_daily.json     full range tidy {date, fuel, avg_mw, share}
- fuel_mix_hourly.json    recent HOURLY_WINDOW_DAYS tidy {ts, fuel, gen_mw}
- event_window.json       hourly slice + computed annotations for the picked event
- meta.json               generation stamp, sources, caveats, row counts
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from pipeline.config import (
    HOURLY_WINDOW_DAYS,
    PROCESSED_DIR,
    WEATHER_STATION_LABEL,
)
from pipeline import pick_event, transforms


def _write_json(name: str, payload) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / name
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def _records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].map(lambda t: t.isoformat())
        elif out[col].dtype == object:
            out[col] = out[col].map(
                lambda v: v.isoformat() if hasattr(v, "isoformat") else v
            )
    return json.loads(out.to_json(orient="records", date_format="iso"))


def build_all(
    raw_isne: pd.DataFrame,
    weather_hourly: pd.DataFrame,
) -> dict:
    """Run all transforms and write every artifact. Returns summary counts."""
    demand_hourly = transforms.tidy_demand_hourly(raw_isne)
    fuel_hourly = transforms.tidy_fuel_mix_hourly(raw_isne)
    demand_daily = transforms.aggregate_demand_daily(demand_hourly)
    weather_daily = transforms.aggregate_weather_daily(weather_hourly)
    temp_demand = transforms.join_temp_demand_daily(demand_daily, weather_daily)
    fuel_daily = transforms.fuel_mix_daily(fuel_hourly)

    last_ts = demand_hourly["ts_utc"].max()
    window_start = last_ts - pd.Timedelta(days=HOURLY_WINDOW_DAYS)
    recent_demand = demand_hourly[demand_hourly["ts_utc"] >= window_start]
    recent_fuel = fuel_hourly[fuel_hourly["ts_utc"] >= window_start]

    # Event window: hourly demand + temp + fuel shares for the picked days.
    window = pick_event.pick_event_window(temp_demand)
    weather = weather_hourly.copy()
    weather["ts_utc"] = pd.to_datetime(weather["ts_utc"], utc=True)
    ev_start = pd.Timestamp(window["start_date"], tz="UTC")
    ev_end = pd.Timestamp(window["end_date"], tz="UTC") + pd.Timedelta(days=1)

    ev = demand_hourly[
        (demand_hourly["ts_utc"] >= ev_start) & (demand_hourly["ts_utc"] < ev_end)
    ].merge(weather, on="ts_utc", how="left")

    ev_fuel = fuel_hourly[
        (fuel_hourly["ts_utc"] >= ev_start) & (fuel_hourly["ts_utc"] < ev_end)
    ].copy()
    if not ev_fuel.empty:
        positive = ev_fuel["gen_mw"].clip(lower=0)
        totals = positive.groupby(ev_fuel["ts_utc"]).transform("sum")
        ev_fuel["share"] = (positive / totals).where(totals > 0)
        shares = ev_fuel.pivot_table(index="ts_utc", columns="fuel", values="share")
        shares.columns = [f"share_{c}" for c in shares.columns]
        ev = ev.merge(shares.reset_index(), on="ts_utc", how="left")

    annotations = pick_event.build_event_annotations(ev, window["kind"])

    _write_json("demand_hourly.json", _records(recent_demand))
    _write_json("demand_daily.json", _records(demand_daily.drop(columns=["hours"])))
    _write_json("temp_demand_daily.json", _records(temp_demand.drop(columns=["hours"])))
    _write_json("fuel_mix_daily.json", _records(fuel_daily))
    _write_json("fuel_mix_hourly.json", _records(recent_fuel))
    _write_json(
        "event_window.json",
        {
            "kind": window["kind"],
            "start_date": window["start_date"].isoformat(),
            "end_date": window["end_date"].isoformat(),
            "center_date": window["center_date"].isoformat(),
            "hourly": _records(ev),
            "annotations": annotations,
        },
    )

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "region": "ISO New England (EIA-930 balancing authority ISNE)",
        "coverage": {
            "start": str(demand_daily["date"].min()),
            "end": str(demand_daily["date"].max()),
            "days": int(len(demand_daily)),
        },
        "sources": [
            {
                "id": "eia930_bulk",
                "name": "EIA-930 Hourly Electric Grid Monitor (bulk six-month files)",
                "url": "https://www.eia.gov/electricity/gridmonitor/about",
                "license_note": "U.S. Government work, public domain.",
                "caveat": "Hourly values include imputed and later-corrected data; real-time values are preliminary.",
            },
            {
                "id": "open_meteo_era5",
                "name": f"Open-Meteo historical weather — {WEATHER_STATION_LABEL}",
                "url": "https://open-meteo.com/en/docs/historical-weather-api",
                "license_note": "CC BY 4.0 (Open-Meteo), ERA5 (Copernicus).",
                "caveat": "ERA5 reanalysis, not station observations; one location is a proxy for regional weather.",
            },
        ],
        "conventions": {
            "timestamps": "ts_utc is hour-beginning UTC (EIA-930 hour-ending shifted by -1h).",
            "degree_day_base_f": 65.0,
            "local_timezone": "America/New_York",
        },
        "counts": {
            "demand_hourly_rows": int(len(recent_demand)),
            "demand_daily_rows": int(len(demand_daily)),
            "temp_demand_daily_rows": int(len(temp_demand)),
            "fuel_mix_daily_rows": int(len(fuel_daily)),
            "fuel_mix_hourly_rows": int(len(recent_fuel)),
            "event_window_rows": int(len(ev)),
        },
        "event": {
            "kind": window["kind"],
            "start_date": window["start_date"].isoformat(),
            "end_date": window["end_date"].isoformat(),
        },
        "disclaimer": (
            "Educational/portfolio project. Not affiliated with ISO New England, "
            "EIA, or any utility. Not operational data."
        ),
    }
    _write_json("meta.json", meta)
    return meta["counts"]

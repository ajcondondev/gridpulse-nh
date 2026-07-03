"""Pure transforms: raw EIA-930 / weather frames → tidy analysis tables.

All functions take and return pandas DataFrames and have no I/O, so they are
directly unit-testable. Conventions (see docs/methodology.md):

- ``ts_utc``: hour-BEGINNING timestamp, UTC. EIA-930 reports hour-ending UTC;
  we subtract one hour so the row labeled 00:00 covers 00:00–01:00.
- Units are explicit in column names (``_mw``, ``_f``).
- Missing values stay missing (NaN/null) — never filled with zeros.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from pipeline.config import DEGREE_DAY_BASE_F, FUEL_GROUPS

_GEN_PREFIX = "Net Generation (MW) from "


def _normalize(name: str) -> str:
    """Normalize an EIA-930 column name for matching.

    Handles the file's known quirks: doubled spaces and the 'witho'/'without'
    typo family ('Solar witho Integrated ...' appears in Adjusted columns).
    """
    text = re.sub(r"\s+", " ", name).strip()
    text = text.replace(" witho Integrated", " with Integrated")
    return text


def find_generation_column(
    columns: list[str], fuel_base: str, prefer_adjusted: bool = True
) -> str | None:
    """Find the raw column for one fuel base, preferring the Adjusted series."""
    target_adj = _normalize(f"{_GEN_PREFIX}{fuel_base} (Adjusted)")
    target_plain = _normalize(f"{_GEN_PREFIX}{fuel_base}")
    adjusted = None
    plain = None
    for col in columns:
        norm = _normalize(col)
        if norm == target_adj:
            adjusted = col
        elif norm == target_plain:
            plain = col
    if prefer_adjusted and adjusted is not None:
        return adjusted
    return plain if plain is not None else adjusted


def _to_numeric(series: pd.Series) -> pd.Series:
    """Parse EIA-930 numeric strings ('12,345' or '') into floats."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.astype("string").str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def _parse_hour_beginning_utc(df: pd.DataFrame) -> pd.Series:
    ends = pd.to_datetime(df["UTC Time at End of Hour"], errors="coerce", utc=True)
    return ends - pd.Timedelta(hours=1)


def tidy_demand_hourly(raw: pd.DataFrame) -> pd.DataFrame:
    """Raw ISNE EIA-930 rows → [ts_utc, demand_mw], deduped, sorted."""
    demand_col = "Demand (MW) (Adjusted)"
    if demand_col not in raw.columns:
        demand_col = "Demand (MW)"
    out = pd.DataFrame(
        {
            "ts_utc": _parse_hour_beginning_utc(raw),
            "demand_mw": _to_numeric(raw[demand_col]),
        }
    )
    out = out.dropna(subset=["ts_utc", "demand_mw"])
    out = out[out["demand_mw"] > 0]
    out = out.drop_duplicates(subset=["ts_utc"], keep="last")
    return out.sort_values("ts_utc").reset_index(drop=True)


def tidy_fuel_mix_hourly(raw: pd.DataFrame) -> pd.DataFrame:
    """Raw ISNE EIA-930 rows → long/tidy [ts_utc, fuel, gen_mw].

    Fuel groups per pipeline.config.FUEL_GROUPS; member columns are summed.
    Rows where every fuel is missing are dropped.
    """
    ts = _parse_hour_beginning_utc(raw)
    columns = list(raw.columns)
    data: dict[str, pd.Series] = {}
    for fuel, bases in FUEL_GROUPS.items():
        total = None
        for base in bases:
            col = find_generation_column(columns, base)
            if col is None:
                continue
            values = _to_numeric(raw[col])
            total = values if total is None else total.add(values, fill_value=0)
        if total is not None:
            data[fuel] = total

    wide = pd.DataFrame({"ts_utc": ts, **data}).dropna(subset=["ts_utc"])
    wide = wide.drop_duplicates(subset=["ts_utc"], keep="last")
    long = wide.melt(id_vars="ts_utc", var_name="fuel", value_name="gen_mw")
    long = long.dropna(subset=["gen_mw"])
    return long.sort_values(["ts_utc", "fuel"]).reset_index(drop=True)


def aggregate_demand_daily(demand_hourly: pd.DataFrame, tz: str = "America/New_York") -> pd.DataFrame:
    """[ts_utc, demand_mw] → per-local-date [date, peak_mw, avg_mw, hours]."""
    df = demand_hourly.copy()
    df["date"] = df["ts_utc"].dt.tz_convert(tz).dt.date
    daily = (
        df.groupby("date")
        .agg(peak_mw=("demand_mw", "max"), avg_mw=("demand_mw", "mean"), hours=("demand_mw", "size"))
        .reset_index()
    )
    daily["peak_mw"] = daily["peak_mw"].round(0)
    daily["avg_mw"] = daily["avg_mw"].round(0)
    # Drop partial days (DST days legitimately have 23/25 hours).
    daily = daily[daily["hours"] >= 23].reset_index(drop=True)
    return daily


def aggregate_weather_daily(weather_hourly: pd.DataFrame, tz: str = "America/New_York") -> pd.DataFrame:
    """[ts_utc, temp_f] → [date, temp_avg_f, temp_min_f, temp_max_f, hdd, cdd]."""
    df = weather_hourly.copy()
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df["date"] = df["ts_utc"].dt.tz_convert(tz).dt.date
    daily = (
        df.groupby("date")
        .agg(
            temp_avg_f=("temp_f", "mean"),
            temp_min_f=("temp_f", "min"),
            temp_max_f=("temp_f", "max"),
            hours=("temp_f", "size"),
        )
        .reset_index()
    )
    daily = daily[daily["hours"] >= 23].drop(columns="hours")
    base = DEGREE_DAY_BASE_F
    daily["hdd"] = (base - daily["temp_avg_f"]).clip(lower=0).round(1)
    daily["cdd"] = (daily["temp_avg_f"] - base).clip(lower=0).round(1)
    for col in ("temp_avg_f", "temp_min_f", "temp_max_f"):
        daily[col] = daily[col].round(1)
    return daily.reset_index(drop=True)


def join_temp_demand_daily(
    demand_daily: pd.DataFrame, weather_daily: pd.DataFrame
) -> pd.DataFrame:
    """Inner-join daily demand and weather on local date."""
    out = demand_daily.merge(weather_daily, on="date", how="inner")
    return out.sort_values("date").reset_index(drop=True)


def fuel_mix_daily(fuel_hourly: pd.DataFrame, tz: str = "America/New_York") -> pd.DataFrame:
    """Tidy hourly fuel mix → daily [date, fuel, avg_mw, share].

    ``share`` is the fuel's fraction of summed positive generation that day;
    negative values (storage charging, pumping) are excluded from the share
    denominator but preserved in avg_mw.
    """
    df = fuel_hourly.copy()
    df["date"] = df["ts_utc"].dt.tz_convert(tz).dt.date
    daily = df.groupby(["date", "fuel"]).agg(avg_mw=("gen_mw", "mean")).reset_index()
    positive = daily["avg_mw"].clip(lower=0)
    totals = positive.groupby(daily["date"]).transform("sum")
    daily["share"] = np.where(totals > 0, positive / totals, np.nan)
    daily["avg_mw"] = daily["avg_mw"].round(1)
    daily["share"] = daily["share"].round(4)
    return daily.sort_values(["date", "fuel"]).reset_index(drop=True)

"""Pick the most story-worthy weather/demand event in the covered range.

Scores each day by combining its demand percentile with its temperature
extremity (cold snaps and heat waves both qualify), then selects a
EVENT_WINDOW_DAYS window centered on the best day. Emits the hourly slice
plus computed (never invented) annotations.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from pipeline.config import EVENT_WINDOW_DAYS


def score_days(temp_demand_daily: pd.DataFrame) -> pd.DataFrame:
    """Add event_score / event_kind columns to the daily joined table."""
    df = temp_demand_daily.copy()
    demand_rank = df["peak_mw"].rank(pct=True)
    cold = (df["hdd"] - df["hdd"].mean()).clip(lower=0) / max(df["hdd"].std(), 1e-9)
    heat = (df["cdd"] - df["cdd"].mean()).clip(lower=0) / max(df["cdd"].std(), 1e-9)
    df["event_kind"] = pd.Series(
        ["cold_snap" if c >= h else "heat_wave" for c, h in zip(cold, heat)],
        index=df.index,
    )
    df["event_score"] = demand_rank * (1 + cold.combine(heat, max))
    return df


def pick_event_window(temp_demand_daily: pd.DataFrame) -> dict:
    """Return {start_date, end_date, center_date, kind} for the best window."""
    scored = score_days(temp_demand_daily)
    best = scored.loc[scored["event_score"].idxmax()]
    center = pd.Timestamp(best["date"])
    half = EVENT_WINDOW_DAYS // 2
    return {
        "center_date": center.date(),
        "start_date": (center - timedelta(days=half)).date(),
        "end_date": (center + timedelta(days=EVENT_WINDOW_DAYS - half - 1)).date(),
        "kind": str(best["event_kind"]),
    }


def build_event_annotations(
    window_hourly: pd.DataFrame, kind: str, tz: str = "America/New_York"
) -> list[dict]:
    """Computed, human-readable annotations for the event window.

    ``window_hourly`` columns: ts_utc, demand_mw, temp_f, and one column per
    fuel share (e.g. share_oil) — wide hourly frame from build_processed.
    """
    df = window_hourly.dropna(subset=["demand_mw"]).copy()
    if df.empty:
        return []
    local = df["ts_utc"].dt.tz_convert(tz)

    def _fmt_hour(ts: pd.Timestamp) -> str:
        # Cross-platform "6 PM on Jan 20" (no %-I on Windows).
        return f"{ts.strftime('%I').lstrip('0')} {ts.strftime('%p')} on {ts.strftime('%b')} {ts.day}"

    notes: list[dict] = []
    peak_i = df["demand_mw"].idxmax()
    notes.append(
        {
            "ts_utc": df.loc[peak_i, "ts_utc"].isoformat(),
            "title": "Demand peak",
            "text": (
                f"Demand peaked at {df.loc[peak_i, 'demand_mw']:,.0f} MW at "
                f"{_fmt_hour(local.loc[peak_i])}."
            ),
        }
    )
    temp = df.dropna(subset=["temp_f"])
    if not temp.empty:
        if kind == "cold_snap":
            ext_i = temp["temp_f"].idxmin()
            label = "Coldest hour"
        else:
            ext_i = temp["temp_f"].idxmax()
            label = "Hottest hour"
        notes.append(
            {
                "ts_utc": temp.loc[ext_i, "ts_utc"].isoformat(),
                "title": label,
                "text": f"{label}: {temp.loc[ext_i, 'temp_f']:.0f}°F in Concord.",
            }
        )
    if "share_oil" in df.columns and df["share_oil"].notna().any():
        oil_i = df["share_oil"].idxmax()
        oil_share = df.loc[oil_i, "share_oil"]
        if pd.notna(oil_share) and oil_share >= 0.02:
            stress = "cold snaps" if kind == "cold_snap" else "heat waves"
            notes.append(
                {
                    "ts_utc": df.loc[oil_i, "ts_utc"].isoformat(),
                    "title": "Oil on the margin",
                    "text": (
                        f"Oil-fired generation reached {oil_share:.0%} of the mix — "
                        f"a signature of a stressed grid during New England {stress}."
                    ),
                }
            )
    notes.sort(key=lambda n: n["ts_utc"])
    return notes

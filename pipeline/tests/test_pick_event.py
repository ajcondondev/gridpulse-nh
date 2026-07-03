from datetime import date, timedelta

import pandas as pd

from pipeline import pick_event


def _daily_year() -> pd.DataFrame:
    """A synthetic year where mid-January is an obvious cold snap."""
    rows = []
    start = date(2025, 7, 1)
    for i in range(365):
        d = start + timedelta(days=i)
        winter = d.month in (12, 1, 2)
        temp = 20.0 if winter else 60.0
        peak = 16_000.0 if winter else 13_000.0
        if date(2026, 1, 18) <= d <= date(2026, 1, 22):  # the event
            temp, peak = -5.0, 21_500.0
        rows.append(
            {
                "date": d,
                "peak_mw": peak,
                "avg_mw": peak * 0.8,
                "temp_avg_f": temp,
                "hdd": max(0.0, 65.0 - temp),
                "cdd": max(0.0, temp - 65.0),
            }
        )
    return pd.DataFrame(rows)


def test_picks_the_cold_snap():
    window = pick_event.pick_event_window(_daily_year())
    assert window["kind"] == "cold_snap"
    assert date(2026, 1, 15) <= window["center_date"] <= date(2026, 1, 25)
    assert (window["end_date"] - window["start_date"]).days == 6


def test_annotations_are_computed_from_data():
    times = pd.date_range("2026-01-19 00:00", periods=72, freq="h", tz="UTC")
    demand = [15_000 + (2_000 if t.hour == 18 else 0) for t in times]
    temps = [5.0 - (10 if t.hour == 6 else 0) for t in times]
    hourly = pd.DataFrame(
        {
            "ts_utc": times,
            "demand_mw": demand,
            "temp_f": temps,
            "share_oil": [0.01] * 40 + [0.09] + [0.01] * 31,
        }
    )
    notes = pick_event.build_event_annotations(hourly, "cold_snap")
    titles = {n["title"] for n in notes}
    assert "Demand peak" in titles
    assert "Coldest hour" in titles
    assert "Oil on the margin" in titles
    peak_note = next(n for n in notes if n["title"] == "Demand peak")
    assert "17,000" in peak_note["text"]

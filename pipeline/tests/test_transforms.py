import pandas as pd
import pytest

from pipeline import transforms


def _raw_isne(rows: int = 48) -> pd.DataFrame:
    """Synthetic EIA-930-shaped raw frame (string values, like dtype=str load)."""
    times = pd.date_range("2026-01-01 01:00", periods=rows, freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "Balancing Authority": ["ISNE"] * rows,
            "UTC Time at End of Hour": times.strftime("%m/%d/%Y %I:%M:%S %p"),
            "Demand (MW)": [f"{10_000 + i * 10:,}" for i in range(rows)],
            "Demand (MW) (Adjusted)": [f"{10_000 + i * 10:,}" for i in range(rows)],
            "Net Generation (MW) from Natural Gas": ["5,000"] * rows,
            "Net Generation (MW) from Natural Gas (Adjusted)": ["5,100"] * rows,
            "Net Generation (MW) from Nuclear": ["3,300"] * rows,
            "Net Generation (MW) from Solar without Integrated Battery Storage": ["200"] * rows,
            # EIA's real typo, present in Adjusted solar-with-storage column:
            "Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)": ["50"] * rows,
            "Net Generation (MW) from All Petroleum Products": ["100"] * rows,
        }
    )


def test_tidy_demand_parses_thousands_and_shifts_to_hour_beginning():
    out = transforms.tidy_demand_hourly(_raw_isne(3))
    assert list(out.columns) == ["ts_utc", "demand_mw"]
    assert out["demand_mw"].iloc[0] == 10_000
    # 01:00 hour-ending becomes 00:00 hour-beginning
    assert out["ts_utc"].iloc[0] == pd.Timestamp("2026-01-01 00:00", tz="UTC")


def test_tidy_demand_drops_nonpositive_and_duplicates():
    raw = _raw_isne(4)
    raw.loc[1, "Demand (MW) (Adjusted)"] = "0"
    raw.loc[2, "Demand (MW) (Adjusted)"] = ""
    dup = raw.iloc[[3]].copy()
    raw = pd.concat([raw, dup], ignore_index=True)
    out = transforms.tidy_demand_hourly(raw)
    assert len(out) == 2  # rows 0 and 3 survive; dup collapsed


def test_find_generation_column_prefers_adjusted_and_handles_typo():
    cols = list(_raw_isne(1).columns)
    assert (
        transforms.find_generation_column(cols, "Natural Gas")
        == "Net Generation (MW) from Natural Gas (Adjusted)"
    )
    # The 'witho' typo column is found for the canonical 'with' name.
    assert (
        transforms.find_generation_column(cols, "Solar with Integrated Battery Storage")
        == "Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)"
    )
    assert transforms.find_generation_column(cols, "Coal") is None


def test_tidy_fuel_mix_groups_and_sums():
    out = transforms.tidy_fuel_mix_hourly(_raw_isne(2))
    first_hour = out[out["ts_utc"] == out["ts_utc"].min()].set_index("fuel")["gen_mw"]
    assert first_hour["natural_gas"] == 5_100  # adjusted preferred
    assert first_hour["nuclear"] == 3_300
    assert first_hour["solar"] == 250  # 200 (without) + 50 (with, typo column)
    assert first_hour["oil"] == 100
    assert "coal" not in first_hour.index  # absent column -> no fabricated zeros


def test_daily_aggregation_drops_partial_days():
    times = pd.date_range("2026-01-01 05:00", periods=60, freq="h", tz="UTC")
    hourly = pd.DataFrame({"ts_utc": times, "demand_mw": range(60)})
    daily = transforms.aggregate_demand_daily(hourly)
    # 60 hours starting mid-day: first and last local days are partial
    assert (daily["hours"] >= 23).all()
    assert len(daily) >= 1


def test_weather_daily_hdd_cdd():
    times = pd.date_range("2026-06-01 04:00", periods=24, freq="h", tz="UTC")
    weather = pd.DataFrame({"ts_utc": times, "temp_f": [75.0] * 24})
    daily = transforms.aggregate_weather_daily(weather)
    row = daily.iloc[0]
    assert row["cdd"] == pytest.approx(10.0)
    assert row["hdd"] == 0.0


def test_fuel_mix_daily_shares_sum_to_one():
    times = pd.date_range("2026-01-01 00:00", periods=24, freq="h", tz="UTC")
    tidy = pd.concat(
        [
            pd.DataFrame({"ts_utc": times, "fuel": "natural_gas", "gen_mw": 6000.0}),
            pd.DataFrame({"ts_utc": times, "fuel": "nuclear", "gen_mw": 3000.0}),
            pd.DataFrame({"ts_utc": times, "fuel": "storage", "gen_mw": -500.0}),
        ],
        ignore_index=True,
    )
    daily = transforms.fuel_mix_daily(tidy)
    one_day = daily[daily["date"] == daily["date"].iloc[0]]
    # negative storage excluded from the share denominator
    assert one_day["share"].fillna(0).sum() == pytest.approx(1.0, abs=0.01)
    storage = one_day[one_day["fuel"] == "storage"].iloc[0]
    assert storage["avg_mw"] == -500.0
    assert storage["share"] == 0.0

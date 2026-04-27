from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from app.connectors.base import BaseConnector


class MockConnector(BaseConnector):
    """Generates synthetic hourly NH electricity demand. Not real data."""

    source_id = "mock_demand"
    HOURS = 168  # one week

    def fetch(self) -> dict:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        fetched_at = now.replace(second=0, microsecond=0)
        # Anchor to midnight so 168 h always produce exactly 7 calendar dates
        start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6)
        timestamps = [start + timedelta(hours=i) for i in range(self.HOURS)]

        rng = np.random.default_rng(seed=int(fetched_at.timestamp()) // 3600)
        demand = []
        for ts in timestamps:
            hour_factor = 1.0 + 0.25 * np.sin(2 * np.pi * (ts.hour - 6) / 24)
            day_factor = 0.88 if ts.weekday() >= 5 else 1.0
            noise = rng.normal(0, 25)
            demand.append(round(1200.0 * hour_factor * day_factor + noise, 1))

        df = pd.DataFrame({"timestamp": timestamps, "demand_mw": demand})
        return {"dataframe": df, "fetched_at": fetched_at, "row_count": len(df)}

    def clean(self, raw_path: Path) -> pd.DataFrame:
        df = pd.read_csv(raw_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.dropna()
        df = df[df["demand_mw"] > 0]
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

"""Fetch EIA-930 bulk six-month BALANCE files and reduce them to ISO-NE rows.

The bulk files (~47 MB each, all balancing authorities) are cached in
``data/raw`` and filtered to the ISNE balancing authority into
``data/interim/eia930_isne.csv``. No API key required.
"""

from __future__ import annotations

import httpx
import pandas as pd

from pipeline.config import (
    BALANCING_AUTHORITY,
    EIA930_BASE_URL,
    INTERIM_DIR,
    RAW_DIR,
)


def half_year_filenames(start_year: int, end_year: int) -> list[str]:
    """All six-month BALANCE filenames covering [start_year, end_year]."""
    names = []
    for year in range(start_year, end_year + 1):
        names.append(f"EIA930_BALANCE_{year}_Jan_Jun.csv")
        names.append(f"EIA930_BALANCE_{year}_Jul_Dec.csv")
    return names


def download_balance_file(filename: str, force: bool = False) -> bool:
    """Download one bulk file into data/raw if not already cached.

    Returns True if the file is available locally afterwards. A 404 (future
    half-year not yet published) is not an error — returns False.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / filename
    if dest.exists() and dest.stat().st_size > 1_000_000 and not force:
        return True

    url = f"{EIA930_BASE_URL}/{filename}"
    try:
        with httpx.stream("GET", url, timeout=180, follow_redirects=True) as resp:
            if resp.status_code == 404:
                return False
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes(1 << 20):
                    f.write(chunk)
    except httpx.HTTPError:
        if dest.exists():
            dest.unlink()
        raise
    return True


def filter_isne(filename: str) -> pd.DataFrame:
    """Load one cached bulk file and return only ISNE rows (raw columns)."""
    path = RAW_DIR / filename
    frames = []
    for chunk in pd.read_csv(
        path, chunksize=200_000, dtype=str, thousands=",", low_memory=False
    ):
        frames.append(chunk[chunk["Balancing Authority"] == BALANCING_AUTHORITY])
    return pd.concat(frames, ignore_index=True)


def build_interim(filenames: list[str]) -> pd.DataFrame:
    """Concatenate ISNE rows from all available files → data/interim CSV."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    frames = [filter_isne(f) for f in filenames if (RAW_DIR / f).exists()]
    if not frames:
        raise FileNotFoundError(
            "No EIA-930 bulk files found in data/raw. Run the fetch step first."
        )
    df = pd.concat(frames, ignore_index=True)
    out = INTERIM_DIR / "eia930_isne.csv"
    df.to_csv(out, index=False)
    return df

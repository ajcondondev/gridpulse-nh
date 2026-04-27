from pathlib import Path

from app.config import settings


def ensure_dirs() -> None:
    for d in [settings.raw_dir, settings.cleaned_dir, settings.exports_dir, settings.metadata_dir]:
        d.mkdir(parents=True, exist_ok=True)


def raw_path(source_id: str, filename: str) -> Path:
    p = settings.raw_dir / source_id
    p.mkdir(parents=True, exist_ok=True)
    return p / filename


def cleaned_path(source_id: str, filename: str) -> Path:
    p = settings.cleaned_dir / source_id
    p.mkdir(parents=True, exist_ok=True)
    return p / filename

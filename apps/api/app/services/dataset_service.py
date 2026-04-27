import json
from pathlib import Path
from typing import Optional

from app.config import settings
from app.schemas.dataset import Dataset


def _meta_path(dataset_id: str) -> Path:
    return settings.metadata_dir / f"{dataset_id}.json"


def save_dataset(dataset: Dataset) -> None:
    settings.metadata_dir.mkdir(parents=True, exist_ok=True)
    with open(_meta_path(dataset.id), "w") as f:
        json.dump(dataset.model_dump(mode="json"), f, indent=2, default=str)


def load_dataset(dataset_id: str) -> Optional[Dataset]:
    p = _meta_path(dataset_id)
    if not p.exists():
        return None
    with open(p) as f:
        return Dataset.model_validate(json.load(f))


def list_datasets() -> list[Dataset]:
    settings.metadata_dir.mkdir(parents=True, exist_ok=True)
    datasets: list[Dataset] = []
    for p in sorted(settings.metadata_dir.glob("*.json"), reverse=True):
        try:
            with open(p) as f:
                datasets.append(Dataset.model_validate(json.load(f)))
        except Exception:
            pass
    return datasets

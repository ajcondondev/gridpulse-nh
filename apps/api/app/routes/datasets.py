from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.schemas.dataset import Dataset, DatasetList
from app.services import dataset_service

router = APIRouter()


@router.get("/datasets", response_model=DatasetList)
def list_datasets() -> DatasetList:
    datasets = dataset_service.list_datasets()
    return DatasetList(datasets=datasets, total=len(datasets))


@router.get("/datasets/{dataset_id}/preview")
def preview_dataset(
    dataset_id: str,
    rows: int = Query(default=50, ge=1, le=500),
) -> dict:
    dataset = dataset_service.load_dataset(dataset_id)
    if not dataset or not dataset.cleaned_path:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    p = Path(dataset.cleaned_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Cleaned file not found on disk.")
    df = pd.read_csv(p, nrows=rows)
    return {
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
        "preview_row_count": len(df),
        "total_row_count": dataset.row_count,
    }


@router.get("/datasets/{dataset_id}/download/cleaned")
def download_cleaned(dataset_id: str) -> FileResponse:
    dataset = dataset_service.load_dataset(dataset_id)
    if not dataset or not dataset.cleaned_path:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    p = Path(dataset.cleaned_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Cleaned file not found on disk.")
    return FileResponse(p, media_type="text/csv", filename=f"{dataset_id}_cleaned.csv")


@router.get("/datasets/{dataset_id}/download/raw")
def download_raw(dataset_id: str) -> FileResponse:
    dataset = dataset_service.load_dataset(dataset_id)
    if not dataset or not dataset.raw_path:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    p = Path(dataset.raw_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Raw file not found on disk.")
    return FileResponse(p, media_type="text/csv", filename=f"{dataset_id}_raw.csv")


@router.get("/datasets/{dataset_id}", response_model=Dataset)
def get_dataset(dataset_id: str) -> Dataset:
    dataset = dataset_service.load_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.dataset import Dataset
from app.services import dataset_service

router = APIRouter(prefix="/analysis")


@router.post("/weather-demand/join", response_model=Dataset)
def create_join() -> Dataset:
    from app.services.analysis_service import create_weather_demand_join
    try:
        return create_weather_demand_join()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/weather-demand/latest", response_model=Dataset)
def get_latest_join() -> Dataset:
    joins = [
        d for d in dataset_service.list_datasets()
        if d.source_id == "weather_demand_analysis"
    ]
    if not joins:
        raise HTTPException(
            status_code=404,
            detail="No weather-demand analysis found. POST /analysis/weather-demand/join to create one.",
        )
    return joins[0]


@router.get("/weather-demand/{join_id}/download")
def download_join(join_id: str) -> FileResponse:
    dataset = dataset_service.load_dataset(join_id)
    if not dataset or not dataset.cleaned_path:
        raise HTTPException(status_code=404, detail="Joined dataset not found.")
    p = Path(dataset.cleaned_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Joined file not found on disk.")
    return FileResponse(p, media_type="text/csv", filename=f"{join_id}.csv")

from fastapi import APIRouter, HTTPException

from app.registry import SOURCES, SOURCES_BY_ID
from app.schemas.source import Source, SourceList

router = APIRouter()


@router.get("/sources", response_model=SourceList)
def list_sources() -> SourceList:
    return SourceList(sources=SOURCES, total=len(SOURCES))


@router.get("/sources/{source_id}", response_model=Source)
def get_source(source_id: str) -> Source:
    source = SOURCES_BY_ID.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
    return source


@router.post("/sources/{source_id}/fetch")
def fetch_source(source_id: str):
    source = SOURCES_BY_ID.get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")

    if source_id == "mock_demand":
        from app.services.fetch_service import fetch_mock_demand
        return fetch_mock_demand()

    if source_id == "eia_isone_load":
        from app.services.fetch_service import fetch_eia_isone_load
        try:
            return fetch_eia_isone_load()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"EIA API error: {e}")

    if source_id == "noaa_weather":
        from app.services.fetch_service import fetch_noaa_weather
        try:
            return fetch_noaa_weather()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"NOAA API error: {e}")

    if source_id == "afdc_ev":
        from app.services.fetch_service import fetch_afdc_ev
        try:
            return fetch_afdc_ev()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"AFDC API error: {e}")

    return {
        "message": "Fetch not yet implemented for this source.",
        "source_id": source_id,
        "status": source.status,
    }

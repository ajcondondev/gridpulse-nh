from fastapi import APIRouter, HTTPException

from app.registry import SOURCES, SOURCES_BY_ID
from app.schemas.source import Source, SourceList

router = APIRouter()


@router.get("/sources", response_model=SourceList)
def list_sources(include_mock: bool = False) -> SourceList:
    sources = [s for s in SOURCES if not s.is_mock_data or include_mock]
    return SourceList(sources=sources, total=len(sources))


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

    if source_id == "isone_csv":
        from app.services.fetch_service import fetch_isone_csv
        try:
            return fetch_isone_csv()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ISO-NE CSV error: {e}")

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

    if source_id == "openei_rates":
        from app.services.fetch_service import fetch_openei_rates
        try:
            return fetch_openei_rates()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"OpenEI utility rates error: {e}")

    if source_id == "epa_egrid":
        from app.services.fetch_service import fetch_epa_egrid
        try:
            return fetch_epa_egrid()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"EPA eGRID error: {e}")

    if source_id == "cdc_svi":
        from app.services.fetch_service import fetch_cdc_svi
        try:
            return fetch_cdc_svi()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"CDC SVI error: {e}")

    if source_id == "fema_flood":
        from app.services.fetch_service import fetch_fema_flood
        try:
            return fetch_fema_flood()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"FEMA flood error: {e}")

    if source_id == "nh_geodata":
        from app.services.fetch_service import fetch_nh_geodata
        try:
            return fetch_nh_geodata()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"NH Geodata error: {e}")

    if source_id == "nrel_pvwatts":
        from app.services.fetch_service import fetch_nrel_pvwatts
        try:
            return fetch_nrel_pvwatts()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"NREL PVWatts error: {e}")

    if source_id == "eia_retail_prices":
        from app.services.fetch_service import fetch_eia_retail_prices
        try:
            return fetch_eia_retail_prices()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"EIA retail prices error: {e}")

    if source_id == "isone_fuel_mix":
        from app.services.fetch_service import fetch_isone_fuel_mix
        try:
            return fetch_isone_fuel_mix()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ISO-NE fuel mix error: {e}")

    if source_id == "isone_load_forecast":
        from app.services.fetch_service import fetch_isone_load_forecast
        try:
            return fetch_isone_load_forecast()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ISO-NE load forecast error: {e}")

    if source_id == "eia_ng_prices":
        from app.services.fetch_service import fetch_eia_ng_prices
        try:
            return fetch_eia_ng_prices()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"EIA natural gas prices error: {e}")

    if source_id == "epa_ejscreen":
        from app.services.fetch_service import fetch_epa_ejscreen
        try:
            return fetch_epa_ejscreen()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"EPA EJScreen error: {e}")

    if source_id == "isone_lmp":
        from app.services.fetch_service import fetch_isone_lmp
        try:
            return fetch_isone_lmp()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ISO-NE LMP error: {e}")

    if source_id == "eia_ami":
        from app.services.fetch_service import fetch_eia_ami
        try:
            return fetch_eia_ami()
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"EIA AMI error: {e}")

    return {
        "message": "Fetch not yet implemented for this source.",
        "source_id": source_id,
        "status": source.status,
    }

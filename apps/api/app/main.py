from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import analysis, datasets, health, sources
from app.services.storage_service import ensure_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    from app.config import settings
    from app.registry import SOURCES
    from app.registry_validation import log_registry_warnings
    log_registry_warnings(SOURCES, settings)
    yield


app = FastAPI(
    title="GridPulse NH API",
    description="Public utility, weather, EV, and grid data workbench for New Hampshire.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sources.router)
app.include_router(datasets.router)
app.include_router(analysis.router)

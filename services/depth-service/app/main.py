from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_seed_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _seed_task
    logger.info("startup_event", service="depth-service", action="startup")
    if settings.POLYGON_SEED_ON_STARTUP:
        import asyncio
        from app.services.osm_polygon_importer import seed_polygons_if_empty

        _seed_task = asyncio.create_task(seed_polygons_if_empty())
    yield
    logger.info("shutdown_event", service="depth-service", action="shutdown")


app = FastAPI(
    title="Depth Service",
    description="Bathymetry depth data microservice for FishMap platform (GEBCO)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    logger.info("health_check", service="depth-service", action="health_check")
    return {
        "status": "healthy",
        "service": "depth-service",
        "version": "2.0.0",
        "data_source": "GEBCO + OSM + GVR",
    }

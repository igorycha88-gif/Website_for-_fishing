from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Depth Service",
    description="Bathymetry depth data microservice for FishMap platform (GEBCO)",
    version="1.0.0",
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
        "version": "1.0.0",
        "data_source": "GEBCO",
    }

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.seed_data import seed_all
from app.scheduler import start_scheduler, shutdown_scheduler

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting forecast-service", service="forecast-service")

    async for db in get_db():
        await seed_all()
        break

    start_scheduler()
    logger.info("Scheduler started", service="forecast-service")

    yield

    shutdown_scheduler()
    logger.info("Shutting down forecast-service", service="forecast-service")


app = FastAPI(
    title="Forecast Service",
    description="Fishing forecast microservice for FishMap platform",
    version="1.0.0",
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
    return {"status": "healthy", "service": "forecast-service", "version": "1.0.0"}

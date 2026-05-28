from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as v1_router
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.seed_data import seed_all
from app.scheduler import start_scheduler, shutdown_scheduler
from app.services.weather_collector import WeatherCollectorService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting forecast-service", service="forecast-service")

    async for db in get_db():
        await seed_all()
        break

    start_scheduler()
    logger.info("Scheduler started", service="forecast-service")

    await _collect_initial_weather()

    yield

    shutdown_scheduler()
    logger.info("Shutting down forecast-service", service="forecast-service")


async def _collect_initial_weather():
    logger.info(
        "Starting initial weather collection",
        service="forecast-service",
    )

    try:
        async for db in get_db():
            collector = WeatherCollectorService(db)
            result = await collector.collect_all_regions(days=4)

            logger.info(
                "Initial weather collection completed",
                service="forecast-service",
                status=result.get("status"),
                collected=result.get("collected", 0),
                total_records=result.get("total_records", 0),
            )
            break
    except Exception as e:
        logger.error(
            f"Initial weather collection failed (service will continue): {e}",
            service="forecast-service",
            error=str(e),
            exc_info=True,
        )


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

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
        try:
            from sqlalchemy import text
            result = await db.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'regions' AND column_name = 'climate_zone'"
            ))
            has_climate = result.fetchone() is not None
            logger.info(f"DB check: regions.climate_zone exists = {has_climate}", service="forecast-service")

            result = await db.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'fish_bite_settings' AND column_name = 'pre_spawn_days'"
            ))
            has_v5 = result.fetchone() is not None
            logger.info(f"DB check: fish_bite_settings.pre_spawn_days exists = {has_v5}", service="forecast-service")

            if not has_climate:
                logger.info("Adding missing climate_zone column", service="forecast-service")
                await db.execute(text(
                    "ALTER TABLE regions ADD COLUMN IF NOT EXISTS climate_zone VARCHAR(10) DEFAULT 'central'"
                ))
                await db.commit()
                logger.info("climate_zone column added", service="forecast-service")

            if not has_v5:
                logger.info("Adding missing v5 columns", service="forecast-service")
                await db.execute(text(
                    "ALTER TABLE fish_bite_settings ADD COLUMN IF NOT EXISTS pre_spawn_days INTEGER DEFAULT 14, "
                    "ADD COLUMN IF NOT EXISTS post_spawn_days INTEGER DEFAULT 5, "
                    "ADD COLUMN IF NOT EXISTS moon_phase_preference VARCHAR(20) DEFAULT 'neutral' "
                    "CHECK (moon_phase_preference IN ('new_moon', 'full_moon', 'both', 'neutral')), "
                    "ADD COLUMN IF NOT EXISTS turbidity_sensitive BOOLEAN DEFAULT false, "
                    "ADD COLUMN IF NOT EXISTS uv_sensitivity NUMERIC(3, 2) DEFAULT 0.3, "
                    "ADD COLUMN IF NOT EXISTS water_level_sensitivity NUMERIC(3, 2) DEFAULT 0.3"
                ))
                await db.execute(text(
                    "ALTER TABLE weather_data ADD COLUMN IF NOT EXISTS water_temperature NUMERIC(5, 2)"
                ))
                await db.commit()
                logger.info("v5 columns added", service="forecast-service")
        except Exception as e:
            logger.error(
                f"DB migration check failed: {e}",
                service="forecast-service",
                error=str(e),
                exc_info=True,
            )

        try:
            await seed_all()
        except Exception as e:
            logger.error(
                f"Seed failed (service will continue): {e}",
                service="forecast-service",
                error=str(e),
                exc_info=True,
            )
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

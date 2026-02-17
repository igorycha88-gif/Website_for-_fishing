from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

from app.core.logging_config import get_logger
from app.services.weather_collector import WeatherCollectorService
from app.core.database import get_db

logger = get_logger(__name__)

scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))


async def scheduled_weather_collection():
    logger.info(
        "Starting scheduled weather collection",
        service="forecast-service",
        timestamp=datetime.utcnow().isoformat(),
    )

    try:
        async for db in get_db():
            collector = WeatherCollectorService(db)
            result = await collector.collect_all_regions(days=4)

            logger.info(
                "Scheduled weather collection completed",
                service="forecast-service",
                result=result,
            )
            break
    except Exception as e:
        logger.error(
            f"Scheduled weather collection failed: {e}",
            service="forecast-service",
            error=str(e),
            exc_info=True,
        )


def setup_scheduler():
    scheduler.add_job(
        scheduled_weather_collection,
        CronTrigger(hour=1, minute=0, timezone=pytz.timezone("Europe/Moscow")),
        id="weather_collection",
        name="Daily weather collection at 01:00 MSK",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        scheduled_weather_collection,
        CronTrigger(hour=13, minute=0, timezone=pytz.timezone("Europe/Moscow")),
        id="weather_collection_afternoon",
        name="Daily weather collection at 13:00 MSK",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    logger.info(
        "Scheduler configured with jobs",
        service="forecast-service",
        jobs=[job.id for job in scheduler.get_jobs()],
    )


def start_scheduler():
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        logger.info(
            "Scheduler started", service="forecast-service", running=scheduler.running
        )


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown", service="forecast-service")

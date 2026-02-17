from datetime import date
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, redis_client
from app.models.forecast import Region
from app.schemas.forecast import (
    CurrentWeatherResponse,
    WeatherDataResponse,
    RegionResponse,
)
from app.services.weather import WeatherService
from app.services.weather_collector import WeatherCollectorService
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_service() -> WeatherService:
    return WeatherService(
        api_key=settings.OPENWEATHERMAP_API_KEY,
        base_url=settings.OPENWEATHERMAP_BASE_URL,
        redis=redis_client,
        cache_ttl=settings.WEATHER_CACHE_TTL,
    )


@router.get("/current/{region_id}", response_model=CurrentWeatherResponse)
async def get_current_weather(
    region_id: UUID,
    db: AsyncSession = Depends(get_db),
    weather_service: WeatherService = Depends(get_weather_service),
):
    result = await db.execute(
        select(Region).where(Region.id == region_id, Region.is_active == True)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    logger.info(
        f"Fetching weather for region: {region.name}",
        service="forecast-service",
        region_id=str(region_id),
        region_name=region.name,
    )

    weather_data = await weather_service.get_current_weather(
        lat=float(region.latitude), lon=float(region.longitude)
    )

    if not weather_data:
        raise HTTPException(status_code=503, detail="Weather service unavailable")

    return CurrentWeatherResponse(
        region=RegionResponse.model_validate(region),
        weather=WeatherDataResponse(
            temperature=weather_data.get("temperature"),
            feels_like=weather_data.get("feels_like"),
            pressure_hpa=weather_data.get("pressure_hpa"),
            humidity=weather_data.get("humidity"),
            wind_speed=weather_data.get("wind_speed"),
            wind_direction=weather_data.get("wind_direction"),
            cloudiness=weather_data.get("cloudiness"),
            precipitation_mm=weather_data.get("precipitation_mm"),
            weather_condition=weather_data.get("weather_condition"),
            weather_icon=weather_data.get("weather_icon"),
            uv_index=weather_data.get("uv_index"),
            moon_phase=weather_data.get("moon_phase"),
            sunrise=weather_data.get("sunrise"),
            sunset=weather_data.get("sunset"),
        ),
        forecast_date=date.today(),
    )


@router.get("/currentByCoords")
async def get_current_weather_by_coords(
    lat: float,
    lon: float,
    weather_service: WeatherService = Depends(get_weather_service),
):
    logger.info(
        f"Fetching weather by coordinates", service="forecast-service", lat=lat, lon=lon
    )

    weather_data = await weather_service.get_current_weather(lat=lat, lon=lon)

    if not weather_data:
        raise HTTPException(status_code=503, detail="Weather service unavailable")

    return weather_data


@router.post("/fetch")
async def fetch_weather_data(
    days: int = 4,
    region_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "Manual weather fetch triggered",
        service="forecast-service",
        days=days,
        region_id=str(region_id) if region_id else "all",
    )

    collector = WeatherCollectorService(db)

    if region_id:
        result = await collector.collect_single_region(region_id, days=days)
    else:
        result = await collector.collect_all_regions(days=days)

    if result.get("status") == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Weather collection failed"),
        )

    return result


@router.get("/jobs")
async def get_scheduler_jobs():
    from app.scheduler import scheduler

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
        )

    return {"jobs": jobs, "running": scheduler.running}

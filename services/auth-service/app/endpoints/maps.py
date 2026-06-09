import logging
from fastapi import APIRouter, Query, Depends, HTTPException, status
from redis.asyncio import Redis
from app.core.database import get_redis
from app.services.geocode import GeocodeService
from app.core.logging_config import get_logger
from app.core.config import settings
from typing import Optional

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(redis: Redis = Depends(get_redis)):
    geocode_service = GeocodeService(redis_client=redis)
    redis_status = await geocode_service.check_redis_connection()

    logger.info(
        "Maps health check", service=settings.SERVICE_NAME, redis_status=redis_status
    )

    return {
        "service": "maps",
        "redis": "ok" if redis_status else "error",
        "status": "healthy" if redis_status else "degraded",
    }


@router.get("/geocode")
async def geocode_city(
    city: str = Query(..., description="Название города для геокодирования"),
    redis: Redis = Depends(get_redis),
):
    logger.info("Received geocode request", service=settings.SERVICE_NAME, city=city)

    try:
        geocode_service = GeocodeService(redis_client=redis)

        logger.debug(
            "Initializing GeocodeService", service=settings.SERVICE_NAME, city=city
        )
        coordinates = await geocode_service.get_city_coordinates(city)

        if not coordinates:
            logger.warning(
                "No coordinates found, using default",
                service=settings.SERVICE_NAME,
                city=city,
            )
            coordinates = await geocode_service.get_default_coordinates()

        response_data = {"city": city, "coordinates": coordinates}

        logger.info(
            "Successfully geocoded city",
            service=settings.SERVICE_NAME,
            city=city,
            coordinates=coordinates,
        )
        return response_data

    except Exception as e:
        logger.error(
            "Error processing geocode request",
            service=settings.SERVICE_NAME,
            city=city,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while geocoding city",
        )

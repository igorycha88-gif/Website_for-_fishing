import json
import logging
from typing import Optional
import httpx
from redis.asyncio import Redis
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GeocodeService:
    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis_client = redis_client
        self.yandex_api_key = settings.YANDEX_MAPS_API_KEY
        self.cache_ttl = 3600

    async def get_city_coordinates(self, city: str) -> Optional[dict]:
        logger.info(
            "Geocode request for city", service=settings.SERVICE_NAME, city=city
        )

        if not city or not city.strip():
            logger.warning(
                "Empty city provided for geocoding", service=settings.SERVICE_NAME
            )
            return None

        city_normalized = city.strip().lower()
        cache_key = f"map:coordinates:{city_normalized}"

        try:
            logger.debug(
                "Checking cache for key",
                service=settings.SERVICE_NAME,
                cache_key=cache_key,
            )
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                logger.info(
                    "Cache hit for city",
                    service=settings.SERVICE_NAME,
                    city=city,
                    coordinates=cached_data,
                )
                return cached_data

            logger.info(
                "Cache miss for city, fetching from Yandex API",
                service=settings.SERVICE_NAME,
                city=city,
            )
            coordinates = await self._fetch_from_yandex(city)
            if coordinates:
                logger.info(
                    "Successfully geocoded city",
                    service=settings.SERVICE_NAME,
                    city=city,
                    coordinates=coordinates,
                )
                await self._save_to_cache(cache_key, coordinates)
                return coordinates

            logger.warning(
                "Failed to geocode city, using fallback",
                service=settings.SERVICE_NAME,
                city=city,
            )
            return await self.get_default_coordinates()
        except Exception as e:
            logger.error(
                "Error in get_city_coordinates",
                service=settings.SERVICE_NAME,
                city=city,
                error=str(e),
                exc_info=True,
            )
            return await self.get_default_coordinates()

    async def check_redis_connection(self) -> bool:
        try:
            if not self.redis_client:
                logger.warning(
                    "Redis client not configured", service=settings.SERVICE_NAME
                )
                return False
            await self.redis_client.ping()
            logger.info("Redis connection OK", service=settings.SERVICE_NAME)
            return True
        except Exception as e:
            logger.error(
                "Redis connection failed",
                service=settings.SERVICE_NAME,
                error=str(e),
                exc_info=True,
            )
            return False

    async def _get_from_cache(self, key: str) -> Optional[dict]:
        if not self.redis_client:
            logger.debug(
                "Redis client not configured, skipping cache read",
                service=settings.SERVICE_NAME,
            )
            return None

        try:
            cached = await self.redis_client.get(key)
            if cached:
                logger.debug(
                    "Cache data retrieved for key",
                    service=settings.SERVICE_NAME,
                    key=key,
                )
                return json.loads(cached)
            logger.debug(
                "No cache data found for key", service=settings.SERVICE_NAME, key=key
            )
        except Exception as e:
            logger.error(
                "Error reading from cache",
                service=settings.SERVICE_NAME,
                key=key,
                error=str(e),
                exc_info=True,
            )

        return None

    async def _save_to_cache(self, key: str, data: dict):
        if not self.redis_client:
            logger.debug(
                "Redis client not configured, skipping cache write",
                service=settings.SERVICE_NAME,
            )
            return

        try:
            logger.debug(
                "Saving to cache", service=settings.SERVICE_NAME, key=key, data=data
            )
            await self.redis_client.setex(key, self.cache_ttl, json.dumps(data))
            logger.info(
                "Successfully cached data",
                service=settings.SERVICE_NAME,
                key=key,
                ttl=self.cache_ttl,
            )
        except Exception as e:
            logger.error(
                "Error saving to cache",
                service=settings.SERVICE_NAME,
                key=key,
                error=str(e),
                exc_info=True,
            )

    async def _fetch_from_yandex(self, city: str) -> Optional[dict]:
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": self.yandex_api_key,
            "geocode": city,
            "format": "json",
            "results": 1,
        }

        logger.info(
            "Fetching coordinates from Yandex API",
            service=settings.SERVICE_NAME,
            city=city,
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                logger.debug(
                    "Yandex API response status",
                    service=settings.SERVICE_NAME,
                    status_code=response.status_code,
                )
                response.raise_for_status()

                data = response.json()
                geo_object = (
                    data.get("response", {})
                    .get("GeoObjectCollection", {})
                    .get("featureMember", [])
                )

                if not geo_object:
                    logger.warning(
                        "No geocoding results found",
                        service=settings.SERVICE_NAME,
                        city=city,
                    )
                    return None

                first_geo_object = geo_object[0].get("GeoObject", {})
                pos_str = first_geo_object.get("Point", {}).get("pos", "")

                if not pos_str:
                    logger.warning(
                        "No position data found",
                        service=settings.SERVICE_NAME,
                        city=city,
                    )
                    return None

                lon, lat = map(float, pos_str.split())
                coordinates = {"lat": lat, "lon": lon}

                logger.info(
                    "Successfully parsed coordinates",
                    service=settings.SERVICE_NAME,
                    city=city,
                    coordinates=coordinates,
                )
                return coordinates

        except httpx.HTTPError as e:
            logger.error(
                "HTTP error fetching from Yandex API",
                service=settings.SERVICE_NAME,
                city=city,
                error=str(e),
                exc_info=True,
            )
        except (ValueError, KeyError) as e:
            logger.error(
                "Error parsing Yandex API response",
                service=settings.SERVICE_NAME,
                city=city,
                error=str(e),
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching from Yandex API",
                service=settings.SERVICE_NAME,
                city=city,
                error=str(e),
                exc_info=True,
            )

        return None

    async def get_default_coordinates(self) -> dict:
        logger.info(
            "Returning default coordinates (Moscow)", service=settings.SERVICE_NAME
        )
        return {"lat": 55.7558, "lon": 37.6173}

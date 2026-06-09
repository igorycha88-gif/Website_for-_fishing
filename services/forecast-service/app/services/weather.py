import json
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import date, time, datetime, timezone

import httpx
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class WeatherService:
    def __init__(
        self, api_key: str, base_url: str, redis: Redis, cache_ttl: int = 3600
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.redis = redis
        self.cache_ttl = cache_ttl

    def _get_cache_key(self, lat: float, lon: float) -> str:
        return f"weather:{lat:.4f}:{lon:.4f}"

    async def get_current_weather(
        self, lat: float, lon: float, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        cache_key = self._get_cache_key(lat, lon)

        if use_cache:
            cached = await self._get_from_cache(cache_key)
            if cached:
                logger.info(
                    "Weather cache hit", service="forecast-service", lat=lat, lon=lon
                )
                return cached

        try:
            logger.info(
                "Fetching weather from OpenWeatherMap API",
                service="forecast-service",
                lat=lat,
                lon=lon,
            )

            weather_data = await self._fetch_from_api(lat, lon)

            if weather_data:
                await self._save_to_cache(cache_key, weather_data)
                logger.info(
                    "Weather data cached", service="forecast-service", lat=lat, lon=lon
                )

            return weather_data

        except Exception as e:
            logger.error(
                f"Error fetching weather: {e}",
                service="forecast-service",
                lat=lat,
                lon=lon,
                error=str(e),
                exc_info=True,
            )
            return None

    async def _fetch_from_api(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_weather_response(data)
                else:
                    logger.error(
                        f"OpenWeatherMap API error: {response.status_code}",
                        service="forecast-service",
                        status_code=response.status_code,
                        response=response.text,
                    )
                    return None
        except httpx.TimeoutException as e:
            logger.error(
                f"OpenWeatherMap API timeout: {e}",
                service="forecast-service",
                error=str(e),
            )
            return None
        except httpx.HTTPError as e:
            logger.error(
                f"OpenWeatherMap API HTTP error: {e}",
                service="forecast-service",
                error=str(e),
            )
            return None

    def _parse_weather_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        main = data.get("main", {})
        wind = data.get("wind", {})
        clouds = data.get("clouds", {})
        weather = data.get("weather", [{}])[0] if data.get("weather") else {}
        sys_data = data.get("sys", {})

        sunrise = None
        sunset = None
        if sys_data.get("sunrise"):
            sunrise_dt = datetime.fromtimestamp(sys_data["sunrise"], tz=timezone.utc)
            sunrise = sunrise_dt.time()
        if sys_data.get("sunset"):
            sunset_dt = datetime.fromtimestamp(sys_data["sunset"], tz=timezone.utc)
            sunset = sunset_dt.time()

        pressure_mmhg = None
        if main.get("pressure"):
            pressure_mmhg = round(main["pressure"] * 0.750062, 0)

        return {
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "pressure_hpa": main.get("pressure"),
            "pressure_mmhg": pressure_mmhg,
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "wind_direction": wind.get("deg"),
            "wind_gust": wind.get("gust"),
            "cloudiness": clouds.get("all"),
            "weather_condition": weather.get("main"),
            "weather_description": weather.get("description"),
            "weather_icon": weather.get("icon"),
            "visibility_m": data.get("visibility"),
            "sunrise": sunrise,
            "sunset": sunset,
            "city_name": data.get("name"),
        }

    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(
                f"Redis cache read error: {e}", service="forecast-service", key=key
            )
        return None

    async def _save_to_cache(self, key: str, data: Dict[str, Any]) -> None:
        try:
            await self.redis.setex(key, self.cache_ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.warning(
                f"Redis cache write error: {e}", service="forecast-service", key=key
            )

    async def get_forecast(
        self, lat: float, lon: float, days: int = 4
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru",
            "cnt": days * 8,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(
                        f"OpenWeatherMap forecast API error: {response.status_code}",
                        service="forecast-service",
                    )
                    return None
        except Exception as e:
            logger.error(
                f"Error fetching forecast: {e}",
                service="forecast-service",
                exc_info=True,
            )
            return None

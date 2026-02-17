import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.core.logging_config import get_logger
from app.models.forecast import Region, WeatherData

logger = get_logger(__name__)


class WeatherCollectorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = settings.OPENWEATHERMAP_API_KEY
        self.base_url = settings.OPENWEATHERMAP_BASE_URL
        self.batch_delay = 0.5

    async def collect_all_regions(self, days: int = 4) -> Dict[str, Any]:
        logger.info(
            "Starting weather collection for all regions",
            service="forecast-service",
            days=days,
        )

        result = await self.db.execute(
            select(Region).where(Region.is_active == True).order_by(Region.name)
        )
        regions = result.scalars().all()

        if not regions:
            logger.warning("No active regions found", service="forecast-service")
            return {"status": "error", "message": "No active regions", "collected": 0}

        logger.info(
            f"Found {len(regions)} active regions",
            service="forecast-service",
            regions_count=len(regions),
        )

        collected = 0
        errors = []
        total_records = 0

        for i, region in enumerate(regions):
            try:
                logger.info(
                    f"Collecting weather for region {i + 1}/{len(regions)}: {region.name}",
                    service="forecast-service",
                    region_id=str(region.id),
                    region_name=region.name,
                )

                records = await self._collect_region_weather(
                    region_id=region.id,
                    lat=float(region.latitude),
                    lon=float(region.longitude),
                    days=days,
                )
                total_records += records
                collected += 1

                if i < len(regions) - 1:
                    await asyncio.sleep(self.batch_delay)

            except Exception as e:
                error_msg = f"Error collecting weather for {region.name}: {str(e)}"
                logger.error(
                    error_msg,
                    service="forecast-service",
                    region_id=str(region.id),
                    region_name=region.name,
                    error=str(e),
                    exc_info=True,
                )
                errors.append({"region": region.name, "error": str(e)})

        logger.info(
            f"Weather collection completed: {collected}/{len(regions)} regions, {total_records} records",
            service="forecast-service",
            collected=collected,
            total_regions=len(regions),
            total_records=total_records,
            errors_count=len(errors),
        )

        return {
            "status": "success" if collected > 0 else "error",
            "collected": collected,
            "total_regions": len(regions),
            "total_records": total_records,
            "errors": errors,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    async def _collect_region_weather(
        self, region_id: UUID, lat: float, lon: float, days: int = 4
    ) -> int:
        forecast_data = await self._fetch_forecast_from_api(lat, lon, days)

        if not forecast_data:
            raise Exception("Failed to fetch forecast from API")

        return await self._save_weather_data(region_id, forecast_data)

    async def _fetch_forecast_from_api(
        self, lat: float, lon: float, days: int = 4
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "ru",
            "cnt": min(days * 8, 40),
        }

        logger.debug(
            f"Fetching forecast from OpenWeatherMap",
            service="forecast-service",
            lat=lat,
            lon=lon,
            days=days,
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.debug(
                    "Forecast fetched successfully",
                    service="forecast-service",
                    lat=lat,
                    lon=lon,
                    records_count=len(data.get("list", [])),
                )
                return data
            else:
                logger.error(
                    f"OpenWeatherMap API error: {response.status_code}",
                    service="forecast-service",
                    status_code=response.status_code,
                    response=response.text[:200],
                )
                return None

    async def _save_weather_data(
        self, region_id: UUID, forecast_data: Dict[str, Any]
    ) -> int:
        city_data = forecast_data.get("city", {})
        forecast_list = forecast_data.get("list", [])

        if not forecast_list:
            logger.warning(
                "Empty forecast list",
                service="forecast-service",
                region_id=str(region_id),
            )
            return 0

        sunrise = None
        sunset = None
        if city_data.get("sunrise"):
            sunrise = datetime.fromtimestamp(
                city_data["sunrise"], tz=timezone.utc
            ).time()
        if city_data.get("sunset"):
            sunset = datetime.fromtimestamp(city_data["sunset"], tz=timezone.utc).time()

        saved_count = 0
        today = date.today()

        cutoff_date = today + timedelta(days=4)
        await self.db.execute(
            delete(WeatherData).where(
                WeatherData.region_id == region_id,
                WeatherData.forecast_date >= cutoff_date,
            )
        )

        for item in forecast_list:
            dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            forecast_date = dt.date()
            forecast_hour = dt.hour

            if forecast_date >= cutoff_date:
                continue

            main = item.get("main", {})
            wind = item.get("wind", {})
            clouds = item.get("clouds", {})
            rain = item.get("rain", {})
            snow = item.get("snow", {})
            weather = item.get("weather", [{}])[0] if item.get("weather") else {}

            temperature = main.get("temp")
            feels_like = main.get("feels_like")
            pressure_hpa = main.get("pressure")
            humidity = main.get("humidity")
            wind_speed = wind.get("speed")
            wind_direction = wind.get("deg")
            wind_gust = wind.get("gust")
            cloudiness = clouds.get("all")

            precipitation_mm = rain.get("1h", 0) + snow.get("1h", 0)
            pop = item.get("pop", 0)
            precipitation_probability = int(pop * 100)

            weather_condition = weather.get("main")
            weather_icon = weather.get("icon")
            visibility_m = item.get("visibility")

            weather_record = WeatherData(
                region_id=region_id,
                forecast_date=forecast_date,
                forecast_hour=forecast_hour,
                temperature=Decimal(str(temperature)) if temperature else None,
                feels_like=Decimal(str(feels_like)) if feels_like else None,
                pressure_hpa=pressure_hpa,
                humidity=humidity,
                wind_speed=Decimal(str(wind_speed)) if wind_speed else None,
                wind_direction=wind_direction,
                wind_gust=Decimal(str(wind_gust)) if wind_gust else None,
                cloudiness=cloudiness,
                precipitation_mm=Decimal(str(precipitation_mm)),
                precipitation_probability=precipitation_probability,
                weather_condition=weather_condition,
                weather_icon=weather_icon,
                visibility_m=visibility_m,
                uv_index=None,
                moon_phase=None,
                sunrise=sunrise,
                sunset=sunset,
            )

            self.db.add(weather_record)
            saved_count += 1

        await self.db.commit()

        logger.info(
            f"Saved {saved_count} weather records for region",
            service="forecast-service",
            region_id=str(region_id),
            records=saved_count,
        )

        return saved_count

    async def collect_single_region(
        self, region_id: UUID, days: int = 4
    ) -> Dict[str, Any]:
        result = await self.db.execute(
            select(Region).where(Region.id == region_id, Region.is_active == True)
        )
        region = result.scalar_one_or_none()

        if not region:
            return {"status": "error", "message": "Region not found"}

        try:
            records = await self._collect_region_weather(
                region_id=region.id,
                lat=float(region.latitude),
                lon=float(region.longitude),
                days=days,
            )

            return {
                "status": "success",
                "region": region.name,
                "records_saved": records,
            }
        except Exception as e:
            logger.error(
                f"Error collecting weather for region {region.name}: {e}",
                service="forecast-service",
                region_id=str(region_id),
                error=str(e),
                exc_info=True,
            )
            return {"status": "error", "region": region.name, "error": str(e)}

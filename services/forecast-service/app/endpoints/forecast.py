import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from redis.asyncio import Redis

from app.core.database import get_db, redis_client
from app.core.logging_config import get_logger
from app.models.forecast import (
    Region,
    WeatherData,
    FishBiteSettings,
    FishingForecast,
    FishType,
)
from app.schemas.forecast import (
    RegionResponse,
    ForecastResponse,
    FishForecastResponse,
    FishTypeBrief,
    TimeOfDayForecast,
    WeatherSummaryResponse,
    MultiDayForecastItem,
)
from app.services.forecast_calculation import (
    calculate_bite_score,
    generate_recommendation,
    get_best_baits,
    get_best_depth,
    FishSettings,
    WeatherConditions,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/forecast", tags=["forecast"])

CACHE_TTL = 3600


def _get_season(month: int) -> str:
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "autumn"
    else:
        return "winter"


async def _get_cached_forecast(
    redis: Redis, region_id: UUID, forecast_date: date
) -> Optional[dict]:
    cache_key = f"forecast:{region_id}:{forecast_date}"
    try:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(
            f"Redis cache read error: {e}",
            service="forecast-service",
            key=cache_key,
        )
    return None


async def _set_cached_forecast(
    redis: Redis, region_id: UUID, forecast_date: date, data: dict
) -> None:
    cache_key = f"forecast:{region_id}:{forecast_date}"
    try:
        await redis.setex(cache_key, CACHE_TTL, json.dumps(data, default=str))
    except Exception as e:
        logger.warning(
            f"Redis cache write error: {e}",
            service="forecast-service",
            key=cache_key,
        )


@router.get("/{region_id}", response_model=ForecastResponse)
async def get_forecast(
    region_id: UUID,
    forecast_date: Optional[date] = Query(None, description="Date for forecast"),
    fish_type_id: Optional[UUID] = Query(None, description="Filter by fish type"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(lambda: redis_client),
):
    if forecast_date is None:
        forecast_date = date.today()

    logger.info(
        "Getting forecast for region",
        service="forecast-service",
        region_id=str(region_id),
        forecast_date=str(forecast_date),
        fish_type_id=str(fish_type_id) if fish_type_id else None,
    )

    result = await db.execute(
        select(Region).where(Region.id == region_id, Region.is_active == True)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    cached = await _get_cached_forecast(redis, region_id, forecast_date)
    if cached:
        logger.info(
            "Forecast cache hit",
            service="forecast-service",
            region_id=str(region_id),
            forecast_date=str(forecast_date),
        )
        cached["region"] = RegionResponse.model_validate(region)
        return ForecastResponse(**cached)

    weather_result = await db.execute(
        select(WeatherData)
        .where(
            WeatherData.region_id == region_id,
            WeatherData.forecast_date == forecast_date,
        )
        .order_by(WeatherData.forecast_hour)
    )
    weather_records = weather_result.scalars().all()

    if not weather_records:
        raise HTTPException(
            status_code=404,
            detail=f"No weather data available for {forecast_date}",
        )

    settings_query = select(FishBiteSettings).options()
    if fish_type_id:
        settings_query = settings_query.where(
            FishBiteSettings.fish_type_id == fish_type_id
        )

    settings_result = await db.execute(settings_query)
    fish_settings_list = settings_result.scalars().all()

    fish_types_result = await db.execute(select(FishType))
    fish_types_map = {ft.id: ft for ft in fish_types_result.scalars().all()}

    month = forecast_date.month
    season = _get_season(month)

    fish_forecasts = []

    for fish_settings in fish_settings_list:
        if fish_settings.region_ids and region_id not in fish_settings.region_ids:
            continue

        fish_result = await db.execute(
            select(FishingForecast).where(
                FishingForecast.region_id == region_id,
                FishingForecast.fish_type_id == fish_settings.fish_type_id,
                FishingForecast.forecast_date == forecast_date,
            )
        )
        existing_forecasts = {f.time_of_day: f for f in fish_result.scalars().all()}

        time_forecasts = []
        for tod in ["morning", "day", "evening", "night"]:
            if tod in existing_forecasts:
                ef = existing_forecasts[tod]
                time_forecasts.append(
                    TimeOfDayForecast(
                        time_of_day=ef.time_of_day,
                        bite_score=ef.bite_score,
                        is_spawn_period=ef.is_spawn_period or False,
                        spawn_message=ef.spawn_message,
                        temperature_score=ef.temperature_score,
                        pressure_score=ef.pressure_score,
                        wind_score=ef.wind_score,
                        moon_score=ef.moon_score,
                        precipitation_score=ef.precipitation_score,
                        recommendation=ef.recommendation,
                        best_baits=ef.best_baits,
                        best_depth=ef.best_depth,
                    )
                )
            else:
                hour_ranges = {
                    "morning": range(6, 10),
                    "day": range(10, 17),
                    "evening": range(17, 21),
                    "night": list(range(21, 24)) + list(range(0, 6)),
                }

                relevant_weather = [
                    w for w in weather_records if w.forecast_hour in hour_ranges[tod]
                ]

                if relevant_weather:
                    avg_weather = _get_average_weather(relevant_weather)

                    fish_settings_obj = FishSettings(
                        fish_type_id=fish_settings.fish_type_id,
                        fish_name="",
                        optimal_temp_min=fish_settings.optimal_temp_min,
                        optimal_temp_max=fish_settings.optimal_temp_max,
                        optimal_pressure_min=fish_settings.optimal_pressure_min,
                        optimal_pressure_max=fish_settings.optimal_pressure_max,
                        max_wind_speed=fish_settings.max_wind_speed,
                        prefer_morning=fish_settings.prefer_morning,
                        prefer_evening=fish_settings.prefer_evening,
                        prefer_overcast=fish_settings.prefer_overcast,
                        moon_sensitivity=fish_settings.moon_sensitivity,
                        active_in_winter=fish_settings.active_in_winter,
                        spawn_start_month=fish_settings.spawn_start_month,
                        spawn_end_month=fish_settings.spawn_end_month,
                        spawn_start_day=fish_settings.spawn_start_day or 1,
                        spawn_end_day=fish_settings.spawn_end_day or 31,
                    )

                    hour = list(hour_ranges[tod])[0]
                    calc_result = calculate_bite_score(
                        avg_weather, fish_settings_obj, hour, month, forecast_date
                    )

                    rec = None
                    if not calc_result["is_spawn_period"]:
                        rec = generate_recommendation(
                            calc_result["bite_score"], avg_weather, fish_settings_obj
                        )

                    fish_name_result = await db.execute(
                        select(FishBiteSettings.fish_type_id).where(
                            FishBiteSettings.id == fish_settings.id
                        )
                    )

                    time_forecasts.append(
                        TimeOfDayForecast(
                            time_of_day=tod,
                            bite_score=calc_result["bite_score"],
                            is_spawn_period=calc_result["is_spawn_period"],
                            spawn_message=calc_result["spawn_message"],
                            temperature_score=calc_result["temperature_score"],
                            pressure_score=calc_result["pressure_score"],
                            wind_score=calc_result["wind_score"],
                            moon_score=calc_result["moon_score"],
                            precipitation_score=calc_result["precipitation_score"],
                            recommendation=rec,
                            best_baits=get_best_baits("", season)
                            if not calc_result["is_spawn_period"]
                            else None,
                            best_depth=get_best_depth("", season),
                        )
                    )

        if time_forecasts:
            avg_score = sum(tf.bite_score for tf in time_forecasts) / len(
                time_forecasts
            )

            fish_type_id_val = fish_settings.fish_type_id
            fish_type_obj = fish_types_map.get(fish_type_id_val)

            fish_forecasts.append(
                FishForecastResponse(
                    fish_type=FishTypeBrief(
                        id=fish_type_id_val,
                        name=fish_type_obj.name if fish_type_obj else "",
                        icon=fish_type_obj.icon if fish_type_obj else None,
                    ),
                    forecasts=sorted(
                        time_forecasts,
                        key=lambda x: ["morning", "day", "evening", "night"].index(
                            x.time_of_day
                        ),
                    ),
                )
            )

    fish_forecasts.sort(
        key=lambda x: sum(f.bite_score for f in x.forecasts), reverse=True
    )

    first_weather = weather_records[0]
    pressure_mm = None
    if first_weather.pressure_hpa:
        pressure_mm = round(first_weather.pressure_hpa * 0.750062)

    weather_summary = WeatherSummaryResponse(
        temperature=float(first_weather.temperature)
        if first_weather.temperature
        else None,
        pressure=pressure_mm,
        wind_speed=float(first_weather.wind_speed)
        if first_weather.wind_speed
        else None,
        precipitation=float(first_weather.precipitation_mm)
        if first_weather.precipitation_mm
        else None,
        moon_phase=float(first_weather.moon_phase)
        if first_weather.moon_phase
        else None,
        sunrise=str(first_weather.sunrise) if first_weather.sunrise else None,
        sunset=str(first_weather.sunset) if first_weather.sunset else None,
    )

    multi_day = []
    for i in range(1, 4):
        future_date = forecast_date + timedelta(days=i)
        future_result = await db.execute(
            select(WeatherData)
            .where(
                WeatherData.region_id == region_id,
                WeatherData.forecast_date == future_date,
            )
            .limit(1)
        )
        if future_result.scalar_one_or_none():
            multi_day.append(
                MultiDayForecastItem(
                    date=future_date,
                    best_fish=[],
                )
            )

    response = ForecastResponse(
        region=RegionResponse.model_validate(region),
        forecast_date=forecast_date,
        weather=weather_summary,
        forecasts=fish_forecasts[:10],
        multi_day_forecast=multi_day if multi_day else None,
    )

    await _set_cached_forecast(
        redis,
        region_id,
        forecast_date,
        response.model_dump(mode="json"),
    )

    return response


def _get_average_weather(weather_records: List[WeatherData]) -> WeatherConditions:
    if not weather_records:
        return WeatherConditions(
            temperature=None,
            pressure_hpa=None,
            wind_speed=None,
            wind_direction=None,
            cloudiness=None,
            precipitation_mm=None,
            moon_phase=None,
            sunrise=None,
            sunset=None,
        )

    temps = [w.temperature for w in weather_records if w.temperature is not None]
    pressures = [w.pressure_hpa for w in weather_records if w.pressure_hpa is not None]
    winds = [w.wind_speed for w in weather_records if w.wind_speed is not None]
    directions = [
        w.wind_direction for w in weather_records if w.wind_direction is not None
    ]
    clouds = [w.cloudiness for w in weather_records if w.cloudiness is not None]
    precips = [
        w.precipitation_mm for w in weather_records if w.precipitation_mm is not None
    ]
    moons = [w.moon_phase for w in weather_records if w.moon_phase is not None]

    first = weather_records[0]

    return WeatherConditions(
        temperature=Decimal(str(sum(temps) / len(temps))) if temps else None,
        pressure_hpa=int(sum(pressures) / len(pressures)) if pressures else None,
        wind_speed=Decimal(str(sum(winds) / len(winds))) if winds else None,
        wind_direction=int(sum(directions) / len(directions)) if directions else None,
        cloudiness=int(sum(clouds) / len(clouds)) if clouds else None,
        precipitation_mm=Decimal(str(sum(precips))) if precips else Decimal("0"),
        moon_phase=Decimal(str(moons[0])) if moons else None,
        sunrise=first.sunrise,
        sunset=first.sunset,
    )

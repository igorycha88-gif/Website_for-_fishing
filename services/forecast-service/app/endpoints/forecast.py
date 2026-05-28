import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.core.database import get_db, redis_client
from app.core.logging_config import get_logger
from app.models.forecast import (
    Region,
    WeatherData,
    FishBiteSettings,
    FishingForecast,
    FishType,
    UserAddedFish,
)
from app.schemas.forecast import (
    RegionResponse,
    ForecastResponse,
    FishForecastResponse,
    FishTypeBrief,
    TimeOfDayForecast,
    WeatherSummaryResponse,
    MultiDayForecastItem,
    AvailableDatesResponse,
    DaySummaryResponse,
    SolunarPeriodSchema,
)
from app.services.forecast_calculation import (
    calculate_bite_score,
    generate_recommendation,
    get_best_baits,
    get_best_depth,
    get_seasonal_recommendations,
    calculate_pressure_trend,
    get_climate_zone,
    get_spawn_dates_for_zone,
    FishSettings,
    WeatherConditions,
    get_season,
)
from app.services.moon_calculation import (
    calculate_moon_phase,
    calculate_solunar_periods,
    get_solunar_periods_for_hour,
    is_time_in_solunar_period,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/forecast", tags=["forecast"])

CACHE_TTL = 3600
ALGORITHM_VERSION = "v4"


def _build_fish_settings(fish_settings, climate_zone: str) -> FishSettings:
    zone_spawn = get_spawn_dates_for_zone(
        fish_settings.spawn_periods_by_zone, climate_zone
    )
    if zone_spawn:
        spawn_start_month, spawn_end_month, spawn_start_day, spawn_end_day = zone_spawn
    else:
        spawn_start_month = fish_settings.spawn_start_month
        spawn_end_month = fish_settings.spawn_end_month
        spawn_start_day = fish_settings.spawn_start_day or 1
        spawn_end_day = fish_settings.spawn_end_day or 31

    return FishSettings(
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
        spawn_start_month=spawn_start_month,
        spawn_end_month=spawn_end_month,
        spawn_start_day=spawn_start_day,
        spawn_end_day=spawn_end_day,
    )


async def _get_user_id_from_token(
    authorization: str | None = Header(None),
) -> UUID | None:
    if not authorization:
        return None
    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "http://auth-service:8000/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return UUID(data["id"])
    except Exception as e:
        logger.debug(f"Failed to get user from token: {e}", service="forecast-service")
    return None


async def _get_cached_forecast(
    redis: Redis, region_id: UUID, forecast_date: date
) -> Optional[dict]:
    cache_key = f"forecast:{ALGORITHM_VERSION}:{region_id}:{forecast_date}"
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
    cache_key = f"forecast:{ALGORITHM_VERSION}:{region_id}:{forecast_date}"
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
    user_id: UUID | None = Depends(_get_user_id_from_token),
):
    if forecast_date is None:
        forecast_date = date.today()

    logger.info(
        "Getting forecast for region",
        service="forecast-service",
        region_id=str(region_id),
        forecast_date=str(forecast_date),
        fish_type_id=str(fish_type_id) if fish_type_id else None,
        user_id=str(user_id) if user_id else None,
    )

    result = await db.execute(
        select(Region).where(Region.id == region_id, Region.is_active == True)
    )
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    climate_zone = get_climate_zone(region.code)

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

    lat = float(region.latitude)
    lon = float(region.longitude)

    moon_data = None
    solunar_data = None
    try:
        moon_data = calculate_moon_phase(forecast_date, lat, lon)
        solunar_data = calculate_solunar_periods(forecast_date, lat, lon)
    except Exception as e:
        logger.warning(
            f"Failed to calculate moon/solunar data: {e}",
            service="forecast-service",
            region_id=str(region_id),
        )

    yesterday_result = await db.execute(
        select(WeatherData)
        .where(
            WeatherData.region_id == region_id,
            WeatherData.forecast_date == forecast_date - timedelta(days=1),
        )
        .order_by(WeatherData.forecast_hour)
    )
    yesterday_records = yesterday_result.scalars().all()

    all_pressure_records = []
    for w in yesterday_records:
        if w.pressure_hpa is not None:
            all_pressure_records.append((w.forecast_hour, w.pressure_hpa))
    for w in weather_records:
        if w.pressure_hpa is not None:
            all_pressure_records.append((w.forecast_hour + 24, w.pressure_hpa))

    pressure_trend_data = None
    if len(all_pressure_records) >= 2:
        pressure_trend_data = calculate_pressure_trend(all_pressure_records)

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
    season = get_season(month)

    solunar_schemas = []
    if solunar_data:
        for p in solunar_data.major_periods + solunar_data.minor_periods:
            solunar_schemas.append(
                SolunarPeriodSchema(
                    start=p.start.strftime("%H:%M"),
                    end=p.end.strftime("%H:%M"),
                    period_type=p.period_type,
                    strength=round(p.strength, 2),
                )
            )

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
        fish_settings_dict = {
            "bait_recommendations": fish_settings.bait_recommendations or {},
            "lure_recommendations": fish_settings.lure_recommendations or {},
        }
        for tod in ["morning", "day", "evening", "night"]:
            if tod in existing_forecasts:
                ef = existing_forecasts[tod]
                fish_category = fish_types_map.get(fish_settings.fish_type_id)
                category = fish_category.category if fish_category else None
                baits, lures = get_seasonal_recommendations(
                    fish_settings_dict, season, category or ""
                )
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
                        recommended_baits=baits,
                        recommended_lures=lures,
                        current_season=season,
                        solunar_periods=solunar_schemas if solunar_schemas else None,
                        pressure_trend_direction=pressure_trend_data.direction if pressure_trend_data else None,
                        pressure_stability=round(pressure_trend_data.stability, 2) if pressure_trend_data else None,
                        is_solunar_peak=False,
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
                    avg_weather = _get_average_weather(
                        relevant_weather,
                        pressure_trend_data,
                        solunar_data,
                        list(hour_ranges[tod]),
                    )

                    fish_settings_obj = _build_fish_settings(fish_settings, climate_zone)

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

                    fish_category = fish_types_map.get(fish_settings.fish_type_id)
                    category = fish_category.category if fish_category else None
                    baits, lures = get_seasonal_recommendations(
                        fish_settings_dict, season, category or ""
                    )

                    tod_solunar = []
                    if solunar_data:
                        tod_solunar = [
                            SolunarPeriodSchema(
                                start=p.start.strftime("%H:%M"),
                                end=p.end.strftime("%H:%M"),
                                period_type=p.period_type,
                                strength=round(p.strength, 2),
                            )
                            for p in get_solunar_periods_for_hour(solunar_data, hour)
                        ]

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
                            recommended_baits=baits,
                            recommended_lures=lures,
                            current_season=season,
                            solunar_periods=tod_solunar if tod_solunar else None,
                            pressure_trend_direction=pressure_trend_data.direction if pressure_trend_data else None,
                            pressure_stability=round(pressure_trend_data.stability, 2) if pressure_trend_data else None,
                            is_solunar_peak=avg_weather.is_solunar_major or avg_weather.is_solunar_minor,
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
                        category=fish_type_obj.category if fish_type_obj else None,
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

    typical_fish_ids = set()
    for fish_settings in fish_settings_list:
        if fish_settings.region_ids and region_id in fish_settings.region_ids:
            typical_fish_ids.add(fish_settings.fish_type_id)

    if user_id:
        custom_result = await db.execute(
            select(UserAddedFish).where(
                UserAddedFish.user_id == user_id,
                UserAddedFish.region_id == region_id,
            )
        )
        custom_fish_records = custom_result.scalars().all()
        custom_fish_type_ids = [cf.fish_type_id for cf in custom_fish_records]
        existing_fish_type_ids = {ff.fish_type.id for ff in fish_forecasts}

        for cf in custom_fish_records:
            if cf.fish_type_id in existing_fish_type_ids:
                continue

            custom_settings_result = await db.execute(
                select(FishBiteSettings).where(
                    FishBiteSettings.fish_type_id == cf.fish_type_id
                )
            )
            custom_settings = custom_settings_result.scalar_one_or_none()

            if not custom_settings:
                continue

            fish_type_obj = fish_types_map.get(cf.fish_type_id)
            if not fish_type_obj:
                continue

            time_forecasts = []
            fish_settings_dict = {
                "bait_recommendations": custom_settings.bait_recommendations or {},
                "lure_recommendations": custom_settings.lure_recommendations or {},
            }

            for tod in ["morning", "day", "evening", "night"]:
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
                    avg_weather = _get_average_weather(
                        relevant_weather,
                        pressure_trend_data,
                        solunar_data,
                        list(hour_ranges[tod]),
                    )

                    fish_settings_obj = _build_fish_settings(custom_settings, climate_zone)

                    hour = list(hour_ranges[tod])[0]
                    calc_result = calculate_bite_score(
                        avg_weather, fish_settings_obj, hour, month, forecast_date
                    )

                    rec = None
                    if not calc_result["is_spawn_period"]:
                        rec = generate_recommendation(
                            calc_result["bite_score"], avg_weather, fish_settings_obj
                        )

                    category = fish_type_obj.category
                    baits, lures = get_seasonal_recommendations(
                        fish_settings_dict, season, category or ""
                    )

                    tod_solunar = []
                    if solunar_data:
                        tod_solunar = [
                            SolunarPeriodSchema(
                                start=p.start.strftime("%H:%M"),
                                end=p.end.strftime("%H:%M"),
                                period_type=p.period_type,
                                strength=round(p.strength, 2),
                            )
                            for p in get_solunar_periods_for_hour(solunar_data, hour)
                        ]

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
                            recommended_baits=baits,
                            recommended_lures=lures,
                            current_season=season,
                            solunar_periods=tod_solunar if tod_solunar else None,
                            pressure_trend_direction=pressure_trend_data.direction if pressure_trend_data else None,
                            pressure_stability=round(pressure_trend_data.stability, 2) if pressure_trend_data else None,
                            is_solunar_peak=avg_weather.is_solunar_major or avg_weather.is_solunar_minor,
                        )
                    )

            if time_forecasts:
                fish_forecasts.append(
                    FishForecastResponse(
                        fish_type=FishTypeBrief(
                            id=cf.fish_type_id,
                            name=fish_type_obj.name,
                            icon=fish_type_obj.icon,
                            category=fish_type_obj.category,
                            is_typical_for_region=cf.fish_type_id in typical_fish_ids,
                        ),
                        forecasts=sorted(
                            time_forecasts,
                            key=lambda x: ["morning", "day", "evening", "night"].index(
                                x.time_of_day
                            ),
                        ),
                        is_custom=True,
                    )
                )

        fish_forecasts.sort(
            key=lambda x: sum(f.bite_score for f in x.forecasts), reverse=True
        )

    for ff in fish_forecasts:
        ff.fish_type.is_typical_for_region = ff.fish_type.id in typical_fish_ids

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
        else (moon_data.phase if moon_data else None),
        moon_phase_name=moon_data.phase_name if moon_data else None,
        moon_illumination=round(moon_data.illumination, 1) if moon_data else None,
        sunrise=str(first_weather.sunrise) if first_weather.sunrise else None,
        sunset=str(first_weather.sunset) if first_weather.sunset else None,
        timezone=region.timezone,
        solunar_periods=solunar_schemas if solunar_schemas else None,
        pressure_trend_direction=pressure_trend_data.direction if pressure_trend_data else None,
        pressure_stability=round(pressure_trend_data.stability, 2) if pressure_trend_data else None,
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


def _get_average_weather(
    weather_records: List[WeatherData],
    pressure_trend_data=None,
    solunar_data=None,
    hour_range: list = None,
) -> WeatherConditions:
    if not weather_records:
        return WeatherConditions()

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

    is_solunar_major = False
    is_solunar_minor = False
    solunar_strength = 0.0

    if solunar_data and hour_range:
        for h in hour_range:
            from datetime import time as dt_time

            check = dt_time(h, 30)
            in_period, ptype, strength = is_time_in_solunar_period(
                check,
                solunar_data.major_periods + solunar_data.minor_periods,
            )
            if in_period:
                if ptype == "major":
                    is_solunar_major = True
                    solunar_strength = max(solunar_strength, strength)
                elif ptype == "minor":
                    is_solunar_minor = True
                    solunar_strength = max(solunar_strength, strength)

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
        pressure_trend_data=pressure_trend_data,
        is_solunar_major=is_solunar_major,
        is_solunar_minor=is_solunar_minor,
        solunar_strength=solunar_strength,
    )


@router.get("/{region_id}/available-dates", response_model=AvailableDatesResponse)
async def get_available_dates(
    region_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "Getting available dates for region",
        service="forecast-service",
        region_id=str(region_id),
    )

    result = await db.execute(
        select(WeatherData.forecast_date)
        .where(WeatherData.region_id == region_id)
        .distinct()
        .order_by(WeatherData.forecast_date)
    )
    dates = [str(row[0]) for row in result.all()]

    logger.info(
        "Available dates retrieved",
        service="forecast-service",
        region_id=str(region_id),
        dates_count=len(dates),
    )

    return AvailableDatesResponse(region_id=region_id, dates=dates)


@router.get("/{region_id}/day-summary", response_model=DaySummaryResponse)
async def get_day_summary(
    region_id: UUID,
    forecast_date: date = Query(..., description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "Getting day summary for region",
        service="forecast-service",
        region_id=str(region_id),
        forecast_date=str(forecast_date),
    )

    result = await db.execute(
        select(WeatherData)
        .where(
            WeatherData.region_id == region_id,
            WeatherData.forecast_date == forecast_date,
        )
        .order_by(WeatherData.forecast_hour)
        .limit(1)
    )
    weather = result.scalar_one_or_none()

    if not weather:
        logger.warning(
            "Day not found",
            service="forecast-service",
            region_id=str(region_id),
            forecast_date=str(forecast_date),
        )
        raise HTTPException(status_code=404, detail="Day not found")

    logger.info(
        "Day summary retrieved",
        service="forecast-service",
        region_id=str(region_id),
        forecast_date=str(forecast_date),
    )

    return DaySummaryResponse(
        date=str(forecast_date),
        temperature=float(weather.temperature) if weather.temperature else None,
        weather_icon=weather.weather_icon,
        wind_speed=float(weather.wind_speed) if weather.wind_speed else None,
    )

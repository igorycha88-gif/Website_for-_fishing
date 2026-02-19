from uuid import UUID
from datetime import date, time
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel


class RegionBase(BaseModel):
    name: str
    code: str
    latitude: Decimal
    longitude: Decimal
    timezone: str = "Europe/Moscow"


class RegionCreate(RegionBase):
    pass


class RegionResponse(RegionBase):
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True


class RegionListResponse(BaseModel):
    regions: List[RegionResponse]
    total: int


class WeatherDataResponse(BaseModel):
    temperature: Optional[Decimal]
    feels_like: Optional[Decimal]
    pressure_hpa: Optional[int]
    humidity: Optional[int]
    wind_speed: Optional[Decimal]
    wind_direction: Optional[int]
    cloudiness: Optional[int]
    precipitation_mm: Optional[Decimal]
    weather_condition: Optional[str]
    weather_icon: Optional[str]
    uv_index: Optional[Decimal]
    moon_phase: Optional[Decimal]
    sunrise: Optional[time]
    sunset: Optional[time]


class CurrentWeatherResponse(BaseModel):
    region: RegionResponse
    weather: WeatherDataResponse
    forecast_date: date


class FishTypeBrief(BaseModel):
    id: UUID
    name: str
    icon: Optional[str]
    category: Optional[str] = None
    is_typical_for_region: bool = True


class TimeOfDayForecast(BaseModel):
    time_of_day: str
    bite_score: float
    is_spawn_period: bool = False
    spawn_message: Optional[str] = None
    temperature_score: Optional[float]
    pressure_score: Optional[float]
    wind_score: Optional[float]
    moon_score: Optional[float]
    precipitation_score: Optional[float]
    recommendation: Optional[str]
    best_baits: Optional[List[str]]
    best_depth: Optional[str]
    recommended_baits: Optional[List[str]] = None
    recommended_lures: Optional[List[str]] = None
    current_season: Optional[str] = None


class FishForecastResponse(BaseModel):
    fish_type: FishTypeBrief
    forecasts: List[TimeOfDayForecast]
    is_custom: bool = False


class WeatherSummaryResponse(BaseModel):
    temperature: Optional[float]
    pressure: Optional[int]
    wind_speed: Optional[float]
    precipitation: Optional[float]
    moon_phase: Optional[float]
    sunrise: Optional[str]
    sunset: Optional[str]
    timezone: Optional[str] = None


class MultiDayForecastItem(BaseModel):
    date: date
    best_fish: List[dict]


class ForecastResponse(BaseModel):
    region: RegionResponse
    forecast_date: date
    weather: WeatherSummaryResponse
    forecasts: List[FishForecastResponse]
    multi_day_forecast: Optional[List[MultiDayForecastItem]]


class MyPlaceForecast(BaseModel):
    place_id: UUID
    place_name: str
    region: Optional[str]
    forecast: dict


class MyPlacesForecastResponse(BaseModel):
    places: List[MyPlaceForecast]


class CustomFishCreate(BaseModel):
    fish_type_id: UUID


class CustomFishResponse(BaseModel):
    id: UUID
    fish_type: FishTypeBrief
    created_at: Optional[str] = None


class CustomFishListResponse(BaseModel):
    fish_types: List[CustomFishResponse]
    total: int


class AllFishTypesResponse(BaseModel):
    fish_types: List[FishTypeBrief]
    total: int


class AvailableDatesResponse(BaseModel):
    region_id: UUID
    dates: List[str]


class DaySummaryResponse(BaseModel):
    date: str
    temperature: Optional[float]
    weather_icon: Optional[str]
    wind_speed: Optional[float]

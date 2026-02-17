from uuid import UUID, uuid4
from datetime import date, time
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Date,
    Time,
    Integer,
    Numeric,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base


class FishType(Base):
    __tablename__ = "fish_types"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False)
    icon = Column(String(50))
    category = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


class Region(Base):
    __tablename__ = "regions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    timezone = Column(String(50), nullable=False, default="Europe/Moscow")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    region_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecast_date = Column(Date, nullable=False)
    forecast_hour = Column(Integer, nullable=False)
    temperature = Column(Numeric(5, 2))
    feels_like = Column(Numeric(5, 2))
    pressure_hpa = Column(Integer)
    humidity = Column(Integer)
    wind_speed = Column(Numeric(5, 2))
    wind_direction = Column(Integer)
    wind_gust = Column(Numeric(5, 2))
    cloudiness = Column(Integer)
    precipitation_mm = Column(Numeric(5, 2))
    precipitation_probability = Column(Integer)
    weather_condition = Column(String(50))
    weather_icon = Column(String(20))
    visibility_m = Column(Integer)
    uv_index = Column(Numeric(3, 1))
    moon_phase = Column(Numeric(3, 2))
    sunrise = Column(Time)
    sunset = Column(Time)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "forecast_date",
            "forecast_hour",
            name="uq_weather_region_date_hour",
        ),
        CheckConstraint(
            "forecast_hour >= 0 AND forecast_hour <= 23", name="ck_weather_hour"
        ),
    )


class FishBiteSettings(Base):
    __tablename__ = "fish_bite_settings"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    fish_type_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("fish_types.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    optimal_temp_min = Column(Numeric(5, 2), nullable=False, default=10)
    optimal_temp_max = Column(Numeric(5, 2), nullable=False, default=25)
    optimal_pressure_min = Column(Integer, nullable=False, default=750)
    optimal_pressure_max = Column(Integer, nullable=False, default=770)
    max_wind_speed = Column(Numeric(5, 2), nullable=False, default=8)
    precipitation_tolerance = Column(Integer, nullable=False, default=2)
    prefer_morning = Column(Boolean, default=True)
    prefer_evening = Column(Boolean, default=True)
    prefer_overcast = Column(Boolean, default=False)
    active_in_winter = Column(Boolean, default=False)
    moon_sensitivity = Column(Numeric(3, 2), default=0.5)
    season_start_month = Column(Integer, default=4)
    season_end_month = Column(Integer, default=10)
    region_ids = Column(ARRAY(PG_UUID(as_uuid=True)), default=[])
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FishingForecast(Base):
    __tablename__ = "fishing_forecasts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    region_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
    )
    fish_type_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("fish_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecast_date = Column(Date, nullable=False)
    time_of_day = Column(String(20), nullable=False)
    bite_score = Column(Integer, nullable=False)
    temperature_score = Column(Integer)
    pressure_score = Column(Integer)
    wind_score = Column(Integer)
    moon_score = Column(Integer)
    precipitation_score = Column(Integer)
    recommendation = Column(Text)
    best_baits = Column(ARRAY(Text))
    best_depth = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "fish_type_id",
            "forecast_date",
            "time_of_day",
            name="uq_forecast_region_fish_date_time",
        ),
        CheckConstraint(
            "time_of_day IN ('morning', 'day', 'evening', 'night')",
            name="ck_forecast_time_of_day",
        ),
        CheckConstraint(
            "bite_score >= 0 AND bite_score <= 100", name="ck_forecast_bite_score"
        ),
    )

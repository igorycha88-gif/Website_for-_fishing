import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.models.forecast import Region, WeatherData, FishBiteSettings, FishingForecast
from app.schemas.forecast import RegionResponse, WeatherDataResponse


class TestRegionModel:
    def test_region_creation(self):
        region = Region(
            id=uuid4(),
            name="Москва",
            code="MOW",
            latitude=55.7558,
            longitude=37.6173,
            timezone="Europe/Moscow",
            is_active=True,
        )

        assert region.name == "Москва"
        assert region.code == "MOW"
        assert str(region.latitude) == "55.7558"
        assert str(region.longitude) == "37.6173"
        assert region.timezone == "Europe/Moscow"
        assert region.is_active is True


class TestWeatherDataModel:
    def test_weather_data_creation(self):
        region_id = uuid4()
        weather = WeatherData(
            id=uuid4(),
            region_id=region_id,
            forecast_date="2025-02-17",
            forecast_hour=12,
            temperature=15.5,
            feels_like=14.0,
            pressure_hpa=1013,
            humidity=75,
            wind_speed=3.5,
            wind_direction=180,
            cloudiness=50,
            weather_condition="Clouds",
            weather_icon="03d",
        )

        assert weather.region_id == region_id
        assert weather.forecast_hour == 12
        assert str(weather.temperature) == "15.5"
        assert weather.weather_condition == "Clouds"


class TestFishBiteSettingsModel:
    def test_fish_bite_settings_creation(self):
        fish_type_id = uuid4()
        settings = FishBiteSettings(
            id=uuid4(),
            fish_type_id=fish_type_id,
            optimal_temp_min=10,
            optimal_temp_max=25,
            optimal_pressure_min=755,
            optimal_pressure_max=770,
            max_wind_speed=8,
            prefer_morning=True,
            prefer_evening=True,
            active_in_winter=False,
            moon_sensitivity=0.5,
            region_ids=[],
        )

        assert settings.fish_type_id == fish_type_id
        assert settings.optimal_temp_min == 10
        assert settings.optimal_temp_max == 25
        assert settings.prefer_morning is True
        assert settings.region_ids == []


class TestFishingForecastModel:
    def test_fishing_forecast_creation(self):
        region_id = uuid4()
        fish_type_id = uuid4()
        forecast = FishingForecast(
            id=uuid4(),
            region_id=region_id,
            fish_type_id=fish_type_id,
            forecast_date="2025-02-17",
            time_of_day="morning",
            bite_score=75,
            temperature_score=80,
            pressure_score=90,
            recommendation="Хороший клев",
        )

        assert forecast.region_id == region_id
        assert forecast.fish_type_id == fish_type_id
        assert forecast.time_of_day == "morning"
        assert forecast.bite_score == 75
        assert forecast.recommendation == "Хороший клев"


class TestSchemas:
    def test_region_response_schema(self):
        region_id = uuid4()
        region = Region(
            id=region_id,
            name="Москва",
            code="MOW",
            latitude=55.7558,
            longitude=37.6173,
            timezone="Europe/Moscow",
            is_active=True,
        )

        response = RegionResponse.model_validate(region)

        assert response.id == region_id
        assert response.name == "Москва"
        assert response.code == "MOW"

    def test_weather_data_response_schema(self):
        from datetime import time

        weather = {
            "temperature": 15.5,
            "feels_like": 14.0,
            "pressure_hpa": 1013,
            "humidity": 75,
            "wind_speed": 3.5,
            "wind_direction": 180,
            "cloudiness": 50,
            "precipitation_mm": 0,
            "weather_condition": "Clouds",
            "weather_icon": "03d",
            "uv_index": 3.5,
            "moon_phase": 0.75,
            "sunrise": time(7, 45),
            "sunset": time(17, 30),
        }

        response = WeatherDataResponse(**weather)

        assert response.temperature == 15.5
        assert response.humidity == 75
        assert response.weather_condition == "Clouds"

import pytest
from datetime import time
from decimal import Decimal
from uuid import uuid4

from app.services.forecast_calculation import (
    TimeOfDay,
    WeatherConditions,
    FishSettings,
    get_time_of_day,
    calculate_temperature_score,
    calculate_pressure_score,
    calculate_wind_score,
    calculate_moon_score,
    calculate_precipitation_score,
    calculate_time_score,
    get_season_multiplier,
    calculate_bite_score,
    generate_recommendation,
    get_best_baits,
    get_best_depth,
)


@pytest.fixture
def fish_settings():
    return FishSettings(
        fish_type_id=uuid4(),
        fish_name="Щука",
        optimal_temp_min=Decimal("4"),
        optimal_temp_max=Decimal("22"),
        optimal_pressure_min=755,
        optimal_pressure_max=765,
        max_wind_speed=Decimal("8"),
        prefer_morning=True,
        prefer_evening=True,
        prefer_overcast=True,
        moon_sensitivity=Decimal("0.4"),
        active_in_winter=True,
    )


@pytest.fixture
def winter_fish_settings():
    return FishSettings(
        fish_type_id=uuid4(),
        fish_name="Налим",
        optimal_temp_min=Decimal("-2"),
        optimal_temp_max=Decimal("12"),
        optimal_pressure_min=750,
        optimal_pressure_max=760,
        max_wind_speed=Decimal("8"),
        prefer_morning=False,
        prefer_evening=False,
        prefer_overcast=True,
        moon_sensitivity=Decimal("0.7"),
        active_in_winter=True,
    )


@pytest.fixture
def summer_fish_settings():
    return FishSettings(
        fish_type_id=uuid4(),
        fish_name="Карп",
        optimal_temp_min=Decimal("15"),
        optimal_temp_max=Decimal("28"),
        optimal_pressure_min=758,
        optimal_pressure_max=768,
        max_wind_speed=Decimal("5"),
        prefer_morning=True,
        prefer_evening=True,
        prefer_overcast=True,
        moon_sensitivity=Decimal("0.6"),
        active_in_winter=False,
    )


class TestGetTimeOfDay:
    def test_morning(self):
        assert get_time_of_day(6) == TimeOfDay.MORNING
        assert get_time_of_day(8) == TimeOfDay.MORNING
        assert get_time_of_day(9) == TimeOfDay.MORNING

    def test_day(self):
        assert get_time_of_day(10) == TimeOfDay.DAY
        assert get_time_of_day(14) == TimeOfDay.DAY
        assert get_time_of_day(16) == TimeOfDay.DAY

    def test_evening(self):
        assert get_time_of_day(17) == TimeOfDay.EVENING
        assert get_time_of_day(19) == TimeOfDay.EVENING
        assert get_time_of_day(20) == TimeOfDay.EVENING

    def test_night(self):
        assert get_time_of_day(21) == TimeOfDay.NIGHT
        assert get_time_of_day(23) == TimeOfDay.NIGHT
        assert get_time_of_day(0) == TimeOfDay.NIGHT
        assert get_time_of_day(4) == TimeOfDay.NIGHT
        assert get_time_of_day(5) == TimeOfDay.NIGHT


class TestCalculateTemperatureScore:
    def test_optimal_temperature(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_temperature_score(weather, fish_settings)
        assert score == 100.0

    def test_temperature_below_optimal(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("-5"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_temperature_score(weather, fish_settings)
        assert 0 <= score < 100

    def test_temperature_above_optimal(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("30"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_temperature_score(weather, fish_settings)
        assert 0 <= score < 100

    def test_none_temperature(self, fish_settings):
        weather = WeatherConditions(
            temperature=None,
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_temperature_score(weather, fish_settings)
        assert score == 50.0


class TestCalculatePressureScore:
    def test_optimal_pressure(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=1013,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_pressure_score(weather, fish_settings)
        assert score >= 90

    def test_pressure_with_rising_trend(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=1015,
            pressure_trend=Decimal("5"),
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_pressure_score(weather, fish_settings)
        assert score >= 100

    def test_pressure_with_falling_trend(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=1010,
            pressure_trend=Decimal("-5"),
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_pressure_score(weather, fish_settings)
        assert score < 100

    def test_none_pressure(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=None,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_pressure_score(weather, fish_settings)
        assert score == 50.0


class TestCalculateWindScore:
    def test_calm_wind(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("2"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_wind_score(weather, fish_settings)
        assert score == 100.0

    def test_moderate_wind(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("6"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_wind_score(weather, fish_settings)
        assert 60 < score < 100

    def test_strong_wind(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("12"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_wind_score(weather, fish_settings)
        assert score < 50

    def test_southern_wind_bonus(self, fish_settings):
        weather_south = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("5"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        weather_north = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("5"),
            wind_direction=0,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score_south = calculate_wind_score(weather_south, fish_settings)
        score_north = calculate_wind_score(weather_north, fish_settings)
        assert score_south > score_north


class TestCalculateMoonScore:
    def test_new_moon(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.0"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_moon_score(weather, fish_settings)
        assert score >= 50

    def test_full_moon(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.5"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_moon_score(weather, fish_settings)
        assert score >= 50

    def test_quarter_moon(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_moon_score(weather, fish_settings)
        assert score < 80


class TestCalculatePrecipitationScore:
    def test_clear_weather(self):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=30,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_precipitation_score(weather)
        assert score == 80.0

    def test_overcast(self):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=80,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_precipitation_score(weather)
        assert score == 90.0

    def test_light_rain(self):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=80,
            precipitation_mm=Decimal("2"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_precipitation_score(weather)
        assert score == 75.0

    def test_heavy_rain(self):
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=760,
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=100,
            precipitation_mm=Decimal("15"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        score = calculate_precipitation_score(weather)
        assert score == 30.0


class TestCalculateTimeScore:
    def test_morning_with_preference(self, fish_settings):
        score = calculate_time_score(TimeOfDay.MORNING, fish_settings)
        assert score == 100.0

    def test_evening_with_preference(self, fish_settings):
        score = calculate_time_score(TimeOfDay.EVENING, fish_settings)
        assert score == 100.0

    def test_day_time(self, fish_settings):
        score = calculate_time_score(TimeOfDay.DAY, fish_settings)
        assert score == 65.0

    def test_night_time(self, fish_settings):
        score = calculate_time_score(TimeOfDay.NIGHT, fish_settings)
        assert score == 40.0

    def test_morning_without_preference(self, winter_fish_settings):
        score = calculate_time_score(TimeOfDay.MORNING, winter_fish_settings)
        assert score == 60.0


class TestGetSeasonMultiplier:
    def test_winter_active_fish(self, fish_settings):
        assert get_season_multiplier(fish_settings, 12) == 1.2
        assert get_season_multiplier(fish_settings, 1) == 1.2
        assert get_season_multiplier(fish_settings, 2) == 1.2

    def test_winter_inactive_fish(self, summer_fish_settings):
        assert get_season_multiplier(summer_fish_settings, 12) == 0.3
        assert get_season_multiplier(summer_fish_settings, 1) == 0.3
        assert get_season_multiplier(summer_fish_settings, 2) == 0.3

    def test_spring(self, fish_settings):
        assert get_season_multiplier(fish_settings, 3) == 1.0
        assert get_season_multiplier(fish_settings, 4) == 1.0
        assert get_season_multiplier(fish_settings, 5) == 1.0

    def test_summer(self, fish_settings):
        assert get_season_multiplier(fish_settings, 6) == 1.0
        assert get_season_multiplier(fish_settings, 7) == 1.0
        assert get_season_multiplier(fish_settings, 8) == 1.0

    def test_autumn(self, fish_settings):
        assert get_season_multiplier(fish_settings, 9) == 1.0
        assert get_season_multiplier(fish_settings, 10) == 1.0
        assert get_season_multiplier(fish_settings, 11) == 1.0


class TestCalculateBiteScore:
    def test_good_conditions(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            pressure_trend=Decimal("2"),
            wind_speed=Decimal("3"),
            wind_direction=200,
            cloudiness=60,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.0"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        result = calculate_bite_score(weather, fish_settings, hour=8, month=5)

        assert "bite_score" in result
        assert 0 <= result["bite_score"] <= 100
        assert result["time_of_day"] == "morning"
        assert result["season_multiplier"] == 1.0
        assert result["bite_score"] >= 60

    def test_poor_conditions(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("35"),
            pressure_hpa=980,
            pressure_trend=Decimal("-10"),
            wind_speed=Decimal("15"),
            wind_direction=0,
            cloudiness=100,
            precipitation_mm=Decimal("20"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        result = calculate_bite_score(weather, fish_settings, hour=14, month=1)

        assert "bite_score" in result
        assert 0 <= result["bite_score"] <= 100
        assert result["time_of_day"] == "day"

    def test_winter_inactive_fish(self, summer_fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("-5"),
            pressure_hpa=1013,
            pressure_trend=Decimal("0"),
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.5"),
            sunrise=time(8, 0),
            sunset=time(17, 0),
        )
        result = calculate_bite_score(weather, summer_fish_settings, hour=8, month=1)

        assert result["season_multiplier"] == 0.3
        assert result["bite_score"] < 50


class TestGenerateRecommendation:
    def test_excellent_bite(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            pressure_trend=Decimal("5"),
            wind_speed=Decimal("2"),
            wind_direction=200,
            cloudiness=60,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.0"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        rec = generate_recommendation(90, weather, fish_settings)
        assert "Отличный клев" in rec

    def test_good_bite(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            pressure_trend=Decimal("0"),
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        rec = generate_recommendation(70, weather, fish_settings)
        assert "Хороший клев" in rec

    def test_poor_bite(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("-5"),
            pressure_hpa=980,
            pressure_trend=Decimal("-5"),
            wind_speed=Decimal("10"),
            wind_direction=0,
            cloudiness=100,
            precipitation_mm=Decimal("5"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        rec = generate_recommendation(25, weather, fish_settings)
        assert "Клев маловероятен" in rec

    def test_includes_wind_advice(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            pressure_trend=Decimal("0"),
            wind_speed=Decimal("8"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        rec = generate_recommendation(70, weather, fish_settings)
        assert "тяжелые приманки" in rec

    def test_includes_pressure_advice(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            pressure_trend=Decimal("5"),
            wind_speed=Decimal("3"),
            wind_direction=180,
            cloudiness=50,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.25"),
            sunrise=time(7, 0),
            sunset=time(18, 0),
        )
        rec = generate_recommendation(70, weather, fish_settings)
        assert "Давление растет" in rec


class TestGetBestBaits:
    def test_pike_spring(self):
        baits = get_best_baits("Щука", "spring")
        assert "джиг" in baits
        assert "воблер" in baits

    def test_carp_winter(self):
        baits = get_best_baits("Карп", "winter")
        assert baits == []

    def test_unknown_fish(self):
        baits = get_best_baits("Неизвестная рыба", "summer")
        assert "универсальная приманка" in baits


class TestGetBestDepth:
    def test_pike_depth(self):
        depth = get_best_depth("Щука", "spring")
        assert depth == "1-3 м"

    def test_unknown_fish_depth(self):
        depth = get_best_depth("Неизвестная рыба", "summer")
        assert depth == "2-4 м"

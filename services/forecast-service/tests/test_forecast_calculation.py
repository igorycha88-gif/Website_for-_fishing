import pytest
from datetime import time, date
from decimal import Decimal
from uuid import uuid4

from app.services.forecast_calculation import (
    TimeOfDay,
    WeatherConditions,
    FishSettings,
    PressureTrend,
    get_time_of_day,
    get_season,
    calculate_temperature_score,
    calculate_pressure_score,
    calculate_pressure_trend,
    calculate_wind_score,
    calculate_moon_score,
    calculate_precipitation_score,
    calculate_time_score,
    get_season_multiplier,
    is_in_spawn_period,
    calculate_bite_score,
    generate_recommendation,
    get_best_baits,
    get_best_depth,
    get_seasonal_recommendations,
    get_climate_zone,
    get_spawn_dates_for_zone,
    REGION_CODE_TO_ZONE,
    WINTER_MONTHLY_MULTIPLIERS,
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
        spawn_start_month=3,
        spawn_end_month=4,
        spawn_start_day=1,
        spawn_end_day=30,
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
        spawn_start_month=12,
        spawn_end_month=2,
        spawn_start_day=15,
        spawn_end_day=28,
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
        spawn_start_month=5,
        spawn_end_month=6,
        spawn_start_day=15,
        spawn_end_day=15,
    )


@pytest.fixture
def fish_no_spawn():
    return FishSettings(
        fish_type_id=uuid4(),
        fish_name="Лосось",
        optimal_temp_min=Decimal("4"),
        optimal_temp_max=Decimal("16"),
        optimal_pressure_min=758,
        optimal_pressure_max=770,
        max_wind_speed=Decimal("5"),
        prefer_morning=True,
        prefer_evening=True,
        prefer_overcast=True,
        moon_sensitivity=Decimal("0.6"),
        active_in_winter=False,
        spawn_start_month=None,
        spawn_end_month=None,
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
        from app.services.forecast_calculation import PressureTrend

        trend_data = PressureTrend(
            trend_3h=-3.0,
            trend_6h=-5.0,
            trend_12h=-8.0,
            trend_24h=-12.0,
            stability=0.2,
            rate_of_change=-1.0,
            direction="falling",
        )
        weather = WeatherConditions(
            temperature=Decimal("10"),
            pressure_hpa=1010,
            pressure_trend=Decimal("-5"),
            pressure_trend_data=trend_data,
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


class TestGetSeasonMultiplierV2:
    def test_december_active_fish(self, fish_settings):
        assert get_season_multiplier(fish_settings, 12) == 0.9

    def test_december_inactive_fish(self, summer_fish_settings):
        assert get_season_multiplier(summer_fish_settings, 12) == 0.2

    def test_january_active_fish(self, fish_settings):
        assert get_season_multiplier(fish_settings, 1) == 0.7

    def test_january_inactive_fish(self, summer_fish_settings):
        assert get_season_multiplier(summer_fish_settings, 1) == 0.1

    def test_february_active_fish(self, fish_settings):
        assert get_season_multiplier(fish_settings, 2) == 1.0

    def test_february_inactive_fish(self, summer_fish_settings):
        assert get_season_multiplier(summer_fish_settings, 2) == 0.15

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


class TestIsInSpawnPeriod:
    def test_in_spawn_period_start_month(self, fish_settings):
        check_date = date(2025, 3, 15)
        is_spawn, message = is_in_spawn_period(fish_settings, check_date)
        assert is_spawn is True
        assert "Нерестовый период" in message

    def test_in_spawn_period_end_month(self, fish_settings):
        check_date = date(2025, 4, 15)
        is_spawn, message = is_in_spawn_period(fish_settings, check_date)
        assert is_spawn is True
        assert "Нерестовый период" in message

    def test_not_in_spawn_period(self, fish_settings):
        check_date = date(2025, 5, 15)
        is_spawn, message = is_in_spawn_period(fish_settings, check_date)
        assert is_spawn is False
        assert message == ""

    def test_spawn_crosses_year_boundary(self, winter_fish_settings):
        check_date = date(2025, 1, 15)
        is_spawn, message = is_in_spawn_period(winter_fish_settings, check_date)
        assert is_spawn is True
        assert "декабря" in message
        assert "февраля" in message

    def test_spawn_crosses_year_boundary_december(self, winter_fish_settings):
        check_date = date(2025, 12, 20)
        is_spawn, message = is_in_spawn_period(winter_fish_settings, check_date)
        assert is_spawn is True

    def test_spawn_crosses_year_boundary_february(self, winter_fish_settings):
        check_date = date(2025, 2, 15)
        is_spawn, message = is_in_spawn_period(winter_fish_settings, check_date)
        assert is_spawn is True

    def test_spawn_crosses_year_boundary_march(self, winter_fish_settings):
        check_date = date(2025, 3, 15)
        is_spawn, message = is_in_spawn_period(winter_fish_settings, check_date)
        assert is_spawn is False

    def test_no_spawn_period(self, fish_no_spawn):
        check_date = date(2025, 3, 15)
        is_spawn, message = is_in_spawn_period(fish_no_spawn, check_date)
        assert is_spawn is False
        assert message == ""

    def test_spawn_specific_day_range(self, summer_fish_settings):
        check_date_in = date(2025, 6, 15)
        is_spawn, _ = is_in_spawn_period(summer_fish_settings, check_date_in)
        assert is_spawn is True

        check_date_before_in_range = date(2025, 6, 14)
        is_spawn, _ = is_in_spawn_period(
            summer_fish_settings, check_date_before_in_range
        )
        assert is_spawn is True

        check_date_after = date(2025, 6, 16)
        is_spawn, _ = is_in_spawn_period(summer_fish_settings, check_date_after)
        assert is_spawn is False

        check_date_before_start_month = date(2025, 5, 14)
        is_spawn, _ = is_in_spawn_period(
            summer_fish_settings, check_date_before_start_month
        )
        assert is_spawn is False

        check_date_start_month_in = date(2025, 5, 20)
        is_spawn, _ = is_in_spawn_period(
            summer_fish_settings, check_date_start_month_in
        )
        assert is_spawn is True


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
        result = calculate_bite_score(
            weather, fish_settings, hour=8, month=5, check_date=date(2025, 5, 15)
        )

        assert "bite_score" in result
        assert 0 <= result["bite_score"] <= 100
        assert result["time_of_day"] == "morning"
        assert result["season_multiplier"] == 1.0
        assert result["is_spawn_period"] is False
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
        result = calculate_bite_score(
            weather, fish_settings, hour=14, month=1, check_date=date(2025, 1, 15)
        )

        assert "bite_score" in result
        assert 0 <= result["bite_score"] <= 100
        assert result["time_of_day"] == "day"
        assert result["is_spawn_period"] is False

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
        result = calculate_bite_score(
            weather, summer_fish_settings, hour=8, month=1, check_date=date(2025, 1, 15)
        )

        assert result["season_multiplier"] == 0.1
        assert result["bite_score"] < 50
        assert result["is_spawn_period"] is False

    def test_spawn_period_returns_zero(self, fish_settings):
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
        result = calculate_bite_score(
            weather, fish_settings, hour=8, month=3, check_date=date(2025, 3, 15)
        )

        assert result["bite_score"] == 0
        assert result["is_spawn_period"] is True
        assert "Нерестовый период" in result["spawn_message"]
        assert result["season_multiplier"] == 0
        assert result["temperature_score"] is None

    def test_spawn_period_winter_fish(self, winter_fish_settings):
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
        result = calculate_bite_score(
            weather, winter_fish_settings, hour=8, month=1, check_date=date(2025, 1, 15)
        )

        assert result["bite_score"] == 0
        assert result["is_spawn_period"] is True
        assert "Нерестовый период" in result["spawn_message"]

    def test_graduated_winter_coefficients_december(self, fish_settings):
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
        result = calculate_bite_score(
            weather, fish_settings, hour=8, month=12, check_date=date(2025, 12, 15)
        )

        assert result["season_multiplier"] == 0.9
        assert result["is_spawn_period"] is False

    def test_graduated_winter_coefficients_january(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("-10"),
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
        result = calculate_bite_score(
            weather, fish_settings, hour=8, month=1, check_date=date(2025, 1, 20)
        )

        assert result["season_multiplier"] == 0.7
        assert result["is_spawn_period"] is False

    def test_graduated_winter_coefficients_february(self, fish_settings):
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
        result = calculate_bite_score(
            weather, fish_settings, hour=8, month=2, check_date=date(2025, 2, 15)
        )

        assert result["season_multiplier"] == 1.0
        assert result["is_spawn_period"] is False


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


class TestWinterMonthlyMultipliers:
    def test_december_multipliers(self):
        assert WINTER_MONTHLY_MULTIPLIERS[12]["active_fish"] == 0.9
        assert WINTER_MONTHLY_MULTIPLIERS[12]["inactive_fish"] == 0.2

    def test_january_multipliers(self):
        assert WINTER_MONTHLY_MULTIPLIERS[1]["active_fish"] == 0.7
        assert WINTER_MONTHLY_MULTIPLIERS[1]["inactive_fish"] == 0.1

    def test_february_multipliers(self):
        assert WINTER_MONTHLY_MULTIPLIERS[2]["active_fish"] == 1.0
        assert WINTER_MONTHLY_MULTIPLIERS[2]["inactive_fish"] == 0.15


class TestGetSeasonalRecommendations:
    def test_peaceful_fish_returns_baits(self):
        fish_settings = {
            "bait_recommendations": {
                "winter": ["мотыль", "опарыш"],
                "spring": ["червь", "перловка"],
                "summer": ["кукуруза", "горох"],
                "autumn": ["червь", "опарыш"],
            },
            "lure_recommendations": {},
        }
        baits, lures = get_seasonal_recommendations(fish_settings, "summer", "peaceful")
        assert baits == ["кукуруза", "горох"]
        assert lures is None

    def test_predatory_fish_returns_lures(self):
        fish_settings = {
            "bait_recommendations": {},
            "lure_recommendations": {
                "winter": ["балансир", "блесна"],
                "spring": ["джиг", "воблер"],
                "summer": ["воблер", "силикон"],
                "autumn": ["джиг", "блесна"],
            },
        }
        baits, lures = get_seasonal_recommendations(
            fish_settings, "winter", "predatory"
        )
        assert baits is None
        assert lures == ["балансир", "блесна"]

    def test_commercial_fish_returns_baits(self):
        fish_settings = {
            "bait_recommendations": {
                "summer": ["бойлы", "пеллетс"],
            },
            "lure_recommendations": {},
        }
        baits, lures = get_seasonal_recommendations(
            fish_settings, "summer", "commercial"
        )
        assert baits == ["бойлы", "пеллетс"]
        assert lures is None

    def test_sport_fish_returns_lures(self):
        fish_settings = {
            "bait_recommendations": {},
            "lure_recommendations": {
                "autumn": ["воблер", "стример"],
            },
        }
        baits, lures = get_seasonal_recommendations(fish_settings, "autumn", "sport")
        assert baits is None
        assert lures == ["воблер", "стример"]

    def test_empty_recommendations_returns_none(self):
        fish_settings = {
            "bait_recommendations": {},
            "lure_recommendations": {},
        }
        baits, lures = get_seasonal_recommendations(fish_settings, "summer", "peaceful")
        assert baits is None
        assert lures is None

    def test_none_fish_settings_returns_none(self):
        baits, lures = get_seasonal_recommendations(None, "summer", "peaceful")
        assert baits is None
        assert lures is None

    def test_empty_list_recommendations_returns_none(self):
        fish_settings = {
            "bait_recommendations": {
                "winter": [],
            },
            "lure_recommendations": {},
        }
        baits, lures = get_seasonal_recommendations(fish_settings, "winter", "peaceful")
        assert baits is None
        assert lures is None

    def test_unknown_category_returns_none(self):
        fish_settings = {
            "bait_recommendations": {
                "summer": ["кукуруза"],
            },
            "lure_recommendations": {
                "summer": ["воблер"],
            },
        }
        baits, lures = get_seasonal_recommendations(fish_settings, "summer", "unknown")
        assert baits is None
        assert lures is None

    def test_all_seasons_peaceful(self):
        fish_settings = {
            "bait_recommendations": {
                "winter": ["мотыль"],
                "spring": ["червь"],
                "summer": ["кукуруза"],
                "autumn": ["опарыш"],
            },
            "lure_recommendations": {},
        }
        for season, expected in [
            ("winter", ["мотыль"]),
            ("spring", ["червь"]),
            ("summer", ["кукуруза"]),
            ("autumn", ["опарыш"]),
        ]:
            baits, lures = get_seasonal_recommendations(
                fish_settings, season, "peaceful"
            )
            assert baits == expected

    def test_all_seasons_predatory(self):
        fish_settings = {
            "bait_recommendations": {},
            "lure_recommendations": {
                "winter": ["балансир"],
                "spring": ["джиг"],
                "summer": ["воблер"],
                "autumn": ["блесна"],
            },
        }
        for season, expected in [
            ("winter", ["балансир"]),
            ("spring", ["джиг"]),
            ("summer", ["воблер"]),
            ("autumn", ["блесна"]),
        ]:
            baits, lures = get_seasonal_recommendations(
                fish_settings, season, "predatory"
            )
            assert lures == expected


class TestCalculatePressureTrend:
    def test_stable_pressure(self):
        records = [(0, 1013), (3, 1013), (6, 1014), (9, 1013), (12, 1013), (15, 1013), (18, 1013), (21, 1013)]
        trend = calculate_pressure_trend(records)
        assert trend.direction == "stable"
        assert trend.stability > 0.8

    def test_rising_pressure(self):
        records = [(0, 1005), (3, 1007), (6, 1009), (9, 1011), (12, 1013), (15, 1015), (18, 1017), (21, 1019)]
        trend = calculate_pressure_trend(records)
        assert trend.direction == "rising"
        assert trend.rate_of_change > 0

    def test_falling_pressure(self):
        records = [(0, 1020), (3, 1018), (6, 1016), (9, 1014), (12, 1012), (15, 1010), (18, 1008), (21, 1006)]
        trend = calculate_pressure_trend(records)
        assert trend.direction == "falling"
        assert trend.rate_of_change < 0

    def test_unstable_pressure(self):
        records = [(0, 1013), (3, 1000), (6, 1025), (9, 995), (12, 1030)]
        trend = calculate_pressure_trend(records)
        assert trend.stability < 0.5

    def test_single_record_returns_default(self):
        records = [(12, 1013)]
        trend = calculate_pressure_trend(records)
        assert trend.direction == "stable"

    def test_empty_records_returns_default(self):
        trend = calculate_pressure_trend([])
        assert trend.direction == "stable"
        assert trend.stability == 1.0

    def test_trend_values_in_mmhg(self):
        records = [(0, 1013), (3, 1013), (6, 1020)]
        trend = calculate_pressure_trend(records)
        assert trend.trend_3h != 0


class TestGetSeason:
    def test_spring(self):
        assert get_season(3) == "spring"
        assert get_season(4) == "spring"
        assert get_season(5) == "spring"

    def test_summer(self):
        assert get_season(6) == "summer"
        assert get_season(7) == "summer"
        assert get_season(8) == "summer"

    def test_autumn(self):
        assert get_season(9) == "autumn"
        assert get_season(10) == "autumn"
        assert get_season(11) == "autumn"

    def test_winter(self):
        assert get_season(12) == "winter"
        assert get_season(1) == "winter"
        assert get_season(2) == "winter"


class TestMoonScoreV3:
    def test_moon_score_with_season(self, fish_settings):
        weather_summer = WeatherConditions(moon_phase=Decimal("0.0"))
        score_summer = calculate_moon_score(weather_summer, fish_settings, "summer")

        weather_winter = WeatherConditions(moon_phase=Decimal("0.0"))
        score_winter = calculate_moon_score(weather_winter, fish_settings, "winter")

        assert score_winter >= score_summer

    def test_moon_score_with_solunar_major(self, fish_settings):
        weather_no_solunar = WeatherConditions(
            moon_phase=Decimal("0.0"),
            is_solunar_major=False,
        )
        weather_solunar_major = WeatherConditions(
            moon_phase=Decimal("0.0"),
            is_solunar_major=True,
            solunar_strength=0.9,
        )
        score_normal = calculate_moon_score(weather_no_solunar, fish_settings, "spring")
        score_solunar = calculate_moon_score(weather_solunar_major, fish_settings, "spring")
        assert score_solunar > score_normal

    def test_moon_score_with_solunar_minor(self, fish_settings):
        weather_solunar_minor = WeatherConditions(
            moon_phase=Decimal("0.25"),
            is_solunar_minor=True,
            solunar_strength=0.6,
        )
        weather_normal = WeatherConditions(
            moon_phase=Decimal("0.25"),
        )
        score_minor = calculate_moon_score(weather_solunar_minor, fish_settings, "spring")
        score_normal = calculate_moon_score(weather_normal, fish_settings, "spring")
        assert score_minor > score_normal


class TestPressureScoreV3:
    def test_pressure_with_stable_trend(self, fish_settings):
        trend = PressureTrend(
            stability=0.9,
            rate_of_change=0.1,
            direction="stable",
        )
        weather = WeatherConditions(
            pressure_hpa=1013,
            pressure_trend_data=trend,
        )
        score = calculate_pressure_score(weather, fish_settings)
        assert score >= 100

    def test_pressure_with_rapid_change(self, fish_settings):
        trend = PressureTrend(
            stability=0.2,
            rate_of_change=3.0,
            direction="rising",
        )
        weather = WeatherConditions(
            pressure_hpa=1013,
            pressure_trend_data=trend,
        )
        score = calculate_pressure_score(weather, fish_settings)
        assert score < 100

    def test_pressure_without_trend_data(self, fish_settings):
        weather = WeatherConditions(
            pressure_hpa=1013,
            pressure_trend_data=None,
        )
        score = calculate_pressure_score(weather, fish_settings)
        assert score == 100.0


class TestMultiplicativeModel:
    def test_perfect_conditions_high_score(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            wind_direction=200,
            cloudiness=60,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.0"),
            is_solunar_major=True,
            solunar_strength=0.9,
        )
        result = calculate_bite_score(
            weather, fish_settings, hour=8, month=6, check_date=date(2025, 6, 15)
        )
        assert result["bite_score"] >= 60

    def test_one_bad_factor_reduces_score(self, fish_settings):
        weather_good = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            wind_direction=200,
            cloudiness=60,
            precipitation_mm=Decimal("0"),
            moon_phase=Decimal("0.5"),
        )
        weather_bad_wind = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("20"),
            wind_direction=0,
            cloudiness=100,
            precipitation_mm=Decimal("15"),
            moon_phase=Decimal("0.5"),
        )
        result_good = calculate_bite_score(
            weather_good, fish_settings, hour=8, month=6, check_date=date(2025, 6, 15)
        )
        result_bad = calculate_bite_score(
            weather_bad_wind, fish_settings, hour=14, month=6, check_date=date(2025, 6, 15)
        )
        assert result_good["bite_score"] > result_bad["bite_score"]

    def test_spawn_overrides_everything(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            is_solunar_major=True,
            solunar_strength=1.0,
        )
        result = calculate_bite_score(
            weather, fish_settings, hour=8, month=3, check_date=date(2025, 3, 15)
        )
        assert result["bite_score"] == 0
        assert result["is_spawn_period"] is True

    def test_score_always_in_range(self, fish_settings):
        for temp in [-20, 0, 15, 40]:
            for pressure in [950, 1013, 1050]:
                for wind in [0, 5, 20]:
                    weather = WeatherConditions(
                        temperature=Decimal(str(temp)),
                        pressure_hpa=pressure,
                        wind_speed=Decimal(str(wind)),
                    )
                    result = calculate_bite_score(
                        weather, fish_settings, hour=8, month=6, check_date=date(2025, 6, 15)
                    )
                    assert 0 <= result["bite_score"] <= 100, f"Score out of range for temp={temp}, pressure={pressure}, wind={wind}"


class TestGenerateRecommendationV3:
    def test_stable_pressure_recommendation(self, fish_settings):
        trend = PressureTrend(stability=0.9, rate_of_change=0.1, direction="stable")
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            pressure_trend_data=trend,
        )
        rec = generate_recommendation(85, weather, fish_settings)
        assert "Стабильное давление" in rec

    def test_unstable_pressure_recommendation(self, fish_settings):
        trend = PressureTrend(stability=0.1, rate_of_change=2.5, direction="falling")
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            pressure_trend_data=trend,
        )
        rec = generate_recommendation(40, weather, fish_settings)
        assert "нестабильно" in rec or "снижен" in rec

    def test_solunar_recommendation(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            is_solunar_major=True,
        )
        rec = generate_recommendation(80, weather, fish_settings)
        assert "Solunar major" in rec

    def test_new_moon_recommendation(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            moon_phase=Decimal("0.02"),
        )
        rec = generate_recommendation(80, weather, fish_settings)
        assert "Новолуние" in rec

    def test_full_moon_recommendation(self, fish_settings):
        weather = WeatherConditions(
            temperature=Decimal("15"),
            pressure_hpa=1013,
            wind_speed=Decimal("2"),
            moon_phase=Decimal("0.5"),
        )
        rec = generate_recommendation(80, weather, fish_settings)
        assert "Полнолуние" in rec


class TestGetClimateZone:
    def test_south_zone(self):
        assert get_climate_zone("KDA") == "south"
        assert get_climate_zone("AST") == "south"
        assert get_climate_zone("ROS") == "south"
        assert get_climate_zone("VGG") == "south"

    def test_central_zone(self):
        assert get_climate_zone("MOW") == "central"
        assert get_climate_zone("MOS") == "central"
        assert get_climate_zone("VLG") == "central"

    def test_north_zone(self):
        assert get_climate_zone("KR") == "north"
        assert get_climate_zone("KO") == "north"
        assert get_climate_zone("MUR") == "north"
        assert get_climate_zone("KYA") == "north"
        assert get_climate_zone("KAM") == "north"

    def test_unknown_code_returns_central(self):
        assert get_climate_zone("UNKNOWN") == "central"

    def test_all_codes_mapped(self):
        assert len(REGION_CODE_TO_ZONE) > 0
        for code, zone in REGION_CODE_TO_ZONE.items():
            assert zone in ("south", "central", "north"), f"Invalid zone for {code}: {zone}"


class TestGetSpawnDatesForZone:
    @pytest.fixture
    def pike_zones(self):
        return {
            "south": {"spawn_start_month": 2, "spawn_end_month": 3, "spawn_start_day": 15, "spawn_end_day": 25},
            "central": {"spawn_start_month": 3, "spawn_end_month": 4, "spawn_start_day": 1, "spawn_end_day": 20},
            "north": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 1, "spawn_end_day": 31},
        }

    def test_south_zone(self, pike_zones):
        result = get_spawn_dates_for_zone(pike_zones, "south")
        assert result == (2, 3, 15, 25)

    def test_central_zone(self, pike_zones):
        result = get_spawn_dates_for_zone(pike_zones, "central")
        assert result == (3, 4, 1, 20)

    def test_north_zone(self, pike_zones):
        result = get_spawn_dates_for_zone(pike_zones, "north")
        assert result == (4, 5, 1, 31)

    def test_unknown_zone_returns_none(self, pike_zones):
        result = get_spawn_dates_for_zone(pike_zones, "east")
        assert result is None

    def test_none_input_returns_none(self):
        result = get_spawn_dates_for_zone(None, "central")
        assert result is None

    def test_empty_dict_returns_none(self):
        result = get_spawn_dates_for_zone({}, "central")
        assert result is None


class TestIsInSpawnPeriodZoned:
    def test_pike_south_february_in_spawn(self):
        south_pike = FishSettings(
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
            spawn_start_month=2,
            spawn_end_month=3,
            spawn_start_day=15,
            spawn_end_day=25,
        )
        is_spawn, msg = is_in_spawn_period(south_pike, date(2026, 2, 20))
        assert is_spawn is True

    def test_pike_south_march_10_in_spawn(self):
        south_pike = FishSettings(
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
            spawn_start_month=2,
            spawn_end_month=3,
            spawn_start_day=15,
            spawn_end_day=25,
        )
        is_spawn, msg = is_in_spawn_period(south_pike, date(2026, 3, 10))
        assert is_spawn is True

    def test_pike_south_march_30_not_spawn(self):
        south_pike = FishSettings(
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
            spawn_start_month=2,
            spawn_end_month=3,
            spawn_start_day=15,
            spawn_end_day=25,
        )
        is_spawn, _ = is_in_spawn_period(south_pike, date(2026, 3, 30))
        assert is_spawn is False

    def test_pike_north_april_in_spawn(self):
        north_pike = FishSettings(
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
            spawn_start_month=4,
            spawn_end_month=5,
            spawn_start_day=1,
            spawn_end_day=31,
        )
        is_spawn, msg = is_in_spawn_period(north_pike, date(2026, 4, 15))
        assert is_spawn is True

    def test_pike_north_march_not_spawn(self):
        north_pike = FishSettings(
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
            spawn_start_month=4,
            spawn_end_month=5,
            spawn_start_day=1,
            spawn_end_day=31,
        )
        is_spawn, _ = is_in_spawn_period(north_pike, date(2026, 3, 15))
        assert is_spawn is False

    def test_nalim_south_november_in_spawn(self):
        south_nalim = FishSettings(
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
            spawn_start_month=11,
            spawn_end_month=12,
            spawn_start_day=15,
            spawn_end_day=31,
        )
        is_spawn, msg = is_in_spawn_period(south_nalim, date(2026, 11, 20))
        assert is_spawn is True

    def test_spawn_message_contains_zone_dates(self):
        zone_fish = FishSettings(
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
            spawn_start_month=4,
            spawn_end_month=5,
            spawn_start_day=1,
            spawn_end_day=31,
        )
        _, msg = is_in_spawn_period(zone_fish, date(2026, 4, 15))
        assert "1 апреля" in msg
        assert "31 мая" in msg


class TestIsInSpawnPeriodYearBoundaryDays:
    @pytest.fixture
    def nalim_central(self):
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
            spawn_start_month=12,
            spawn_end_month=2,
            spawn_start_day=1,
            spawn_end_day=15,
        )

    def test_year_boundary_dec_1_is_spawn(self, nalim_central):
        is_spawn, _ = is_in_spawn_period(nalim_central, date(2026, 12, 1))
        assert is_spawn is True

    def test_year_boundary_nov_30_not_spawn(self, nalim_central):
        is_spawn, _ = is_in_spawn_period(nalim_central, date(2026, 11, 30))
        assert is_spawn is False

    def test_year_boundary_feb_15_is_spawn(self, nalim_central):
        is_spawn, _ = is_in_spawn_period(nalim_central, date(2026, 2, 15))
        assert is_spawn is True

    def test_year_boundary_feb_16_not_spawn(self, nalim_central):
        is_spawn, _ = is_in_spawn_period(nalim_central, date(2026, 2, 16))
        assert is_spawn is False

    def test_year_boundary_jan_mid_is_spawn(self, nalim_central):
        is_spawn, _ = is_in_spawn_period(nalim_central, date(2026, 1, 15))
        assert is_spawn is True

    def test_year_boundary_dec_31_is_spawn(self, nalim_central):
        is_spawn, _ = is_in_spawn_period(nalim_central, date(2026, 12, 31))
        assert is_spawn is True

    @pytest.fixture
    def nalim_south(self):
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
            spawn_start_month=11,
            spawn_end_month=12,
            spawn_start_day=15,
            spawn_end_day=31,
        )

    def test_nalim_south_nov_14_not_spawn(self, nalim_south):
        is_spawn, _ = is_in_spawn_period(nalim_south, date(2026, 11, 14))
        assert is_spawn is False

    def test_nalim_south_nov_15_is_spawn(self, nalim_south):
        is_spawn, _ = is_in_spawn_period(nalim_south, date(2026, 11, 15))
        assert is_spawn is True

    def test_nalim_south_dec_31_is_spawn(self, nalim_south):
        is_spawn, _ = is_in_spawn_period(nalim_south, date(2026, 12, 31))
        assert is_spawn is True

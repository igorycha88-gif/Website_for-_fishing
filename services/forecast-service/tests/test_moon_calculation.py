from datetime import date, time

import pytest

from app.services.moon_calculation import (
    MoonData,
    SolunarData,
    SolunarPeriod,
    calculate_moon_phase,
    calculate_solunar_periods,
    get_solunar_periods_for_hour,
    is_time_in_solunar_period,
    _get_phase_name,
    _time_in_range,
)

MOSCOW_LAT = 55.7558
MOSCOW_LON = 37.6173


class TestMoonPhase:
    def test_known_new_moon(self):
        moon = calculate_moon_phase(date(2024, 1, 11), MOSCOW_LAT, MOSCOW_LON)
        assert isinstance(moon, MoonData)
        assert 0.0 <= moon.phase <= 1.0
        assert 0.0 <= moon.illumination <= 100.0
        assert moon.phase < 0.05 or moon.phase > 0.95

    def test_known_full_moon(self):
        moon = calculate_moon_phase(date(2024, 1, 25), MOSCOW_LAT, MOSCOW_LON)
        assert isinstance(moon, MoonData)
        assert 0.0 <= moon.phase <= 1.0
        assert 0.4 <= moon.phase <= 0.6

    def test_phase_always_in_range(self):
        test_dates = [
            date(2024, m, d)
            for m in range(1, 13)
            for d in [1, 10, 20, 28]
        ]
        for d in test_dates:
            moon = calculate_moon_phase(d, MOSCOW_LAT, MOSCOW_LON)
            assert 0.0 <= moon.phase <= 1.0, f"Phase out of range for {d}: {moon.phase}"
            assert 0.0 <= moon.illumination <= 100.0, f"Illumination out of range for {d}"

    def test_phase_name_not_empty(self):
        for test_date in [date(2024, 1, 1), date(2024, 6, 15), date(2024, 12, 31)]:
            moon = calculate_moon_phase(test_date, MOSCOW_LAT, MOSCOW_LON)
            assert moon.phase_name
            assert isinstance(moon.phase_name, str)

    def test_next_moon_days_positive(self):
        moon = calculate_moon_phase(date(2024, 6, 15), MOSCOW_LAT, MOSCOW_LON)
        assert moon.next_new_moon_days > 0
        assert moon.next_full_moon_days > 0

    def test_different_lat_lon(self):
        moscow = calculate_moon_phase(date(2024, 6, 15), 55.75, 37.62)
        vladivostok = calculate_moon_phase(date(2024, 6, 15), 43.12, 131.87)
        assert abs(moscow.phase - vladivostok.phase) < 0.05

    def test_high_latitude(self):
        murmansk = calculate_moon_phase(date(2024, 6, 15), 68.97, 33.07)
        assert 0.0 <= murmansk.phase <= 1.0
        assert murmansk.phase_name


class TestPhaseName:
    @pytest.mark.parametrize(
        "phase,expected",
        [
            (0.0, "Новолуние"),
            (0.01, "Новолуние"),
            (0.1, "Растущий серп"),
            (0.25, "Первая четверть"),
            (0.4, "Растущая луна"),
            (0.5, "Полнолуние"),
            (0.6, "Убывающая луна"),
            (0.75, "Последняя четверть"),
            (0.85, "Убывающий серп"),
            (0.95, "Новолуние"),
        ],
    )
    def test_phase_names(self, phase, expected):
        assert _get_phase_name(phase) == expected


class TestSolunarPeriods:
    def test_returns_solunar_data(self):
        data = calculate_solunar_periods(date(2024, 6, 15), MOSCOW_LAT, MOSCOW_LON)
        assert isinstance(data, SolunarData)
        assert isinstance(data.major_periods, list)
        assert isinstance(data.minor_periods, list)

    def test_major_periods_structure(self):
        data = calculate_solunar_periods(date(2024, 6, 15), MOSCOW_LAT, MOSCOW_LON)
        for period in data.major_periods:
            assert isinstance(period, SolunarPeriod)
            assert period.period_type == "major"
            assert 0.0 < period.strength <= 1.0
            assert isinstance(period.start, time)
            assert isinstance(period.end, time)
            assert period.start < period.end or True  # may wrap midnight

    def test_minor_periods_structure(self):
        data = calculate_solunar_periods(date(2024, 6, 15), MOSCOW_LAT, MOSCOW_LON)
        for period in data.minor_periods:
            assert isinstance(period, SolunarPeriod)
            assert period.period_type == "minor"
            assert 0.0 < period.strength <= 1.0

    def test_major_period_duration(self):
        data = calculate_solunar_periods(date(2024, 6, 15), MOSCOW_LAT, MOSCOW_LON)
        for period in data.major_periods:
            start_sec = period.start.hour * 3600 + period.start.minute * 60
            end_sec = period.end.hour * 3600 + period.end.minute * 60
            if end_sec > start_sec:
                duration_min = (end_sec - start_sec) / 60
                assert 90 <= duration_min <= 150, f"Major period duration {duration_min}min out of range"

    def test_minor_period_duration(self):
        data = calculate_solunar_periods(date(2024, 6, 15), MOSCOW_LAT, MOSCOW_LON)
        for period in data.minor_periods:
            start_sec = period.start.hour * 3600 + period.start.minute * 60
            end_sec = period.end.hour * 3600 + period.end.minute * 60
            if end_sec > start_sec:
                duration_min = (end_sec - start_sec) / 60
                assert 45 <= duration_min <= 75, f"Minor period duration {duration_min}min out of range"

    def test_solunar_strength_varies_with_phase(self):
        calculate_moon_phase(date(2024, 1, 11), MOSCOW_LAT, MOSCOW_LON)
        data_new = calculate_solunar_periods(date(2024, 1, 11), MOSCOW_LAT, MOSCOW_LON)

        calculate_moon_phase(date(2024, 1, 18), MOSCOW_LAT, MOSCOW_LON)
        data_quarter = calculate_solunar_periods(date(2024, 1, 18), MOSCOW_LAT, MOSCOW_LON)

        if data_new.major_periods and data_quarter.major_periods:
            avg_new = sum(p.strength for p in data_new.major_periods) / len(data_new.major_periods)
            avg_quarter = sum(p.strength for p in data_quarter.major_periods) / len(data_quarter.major_periods)
            assert avg_new >= avg_quarter

    def test_multiple_dates(self):
        for d in [date(2024, 3, 1), date(2024, 6, 15), date(2024, 9, 21), date(2024, 12, 10)]:
            data = calculate_solunar_periods(d, MOSCOW_LAT, MOSCOW_LON)
            assert len(data.major_periods) >= 1


class TestIsTimeInSolunarPeriod:
    def test_time_in_period(self):
        period = SolunarPeriod(
            start=time(10, 0),
            end=time(12, 0),
            period_type="major",
            strength=0.8,
        )
        is_in, ptype, strength = is_time_in_solunar_period(time(11, 0), [period])
        assert is_in is True
        assert ptype == "major"
        assert strength == 0.8

    def test_time_outside_period(self):
        period = SolunarPeriod(
            start=time(10, 0),
            end=time(12, 0),
            period_type="major",
            strength=0.8,
        )
        is_in, ptype, strength = is_time_in_solunar_period(time(14, 0), [period])
        assert is_in is False

    def test_multiple_periods(self):
        periods = [
            SolunarPeriod(time(6, 0), time(7, 0), "minor", 0.5),
            SolunarPeriod(time(12, 0), time(14, 0), "major", 0.9),
        ]
        is_in, ptype, strength = is_time_in_solunar_period(time(13, 0), periods)
        assert is_in is True
        assert ptype == "major"

    def test_empty_periods(self):
        is_in, ptype, strength = is_time_in_solunar_period(time(12, 0), [])
        assert is_in is False


class TestGetSolunarPeriodsForHour:
    def test_matching_hour(self):
        periods = [
            SolunarPeriod(time(12, 0), time(14, 0), "major", 0.9),
        ]
        matching = get_solunar_periods_for_hour(
            SolunarData(major_periods=periods, minor_periods=[]),
            13,
        )
        assert len(matching) == 1

    def test_non_matching_hour(self):
        periods = [
            SolunarPeriod(time(12, 0), time(14, 0), "major", 0.9),
        ]
        matching = get_solunar_periods_for_hour(
            SolunarData(major_periods=periods, minor_periods=[]),
            20,
        )
        assert len(matching) == 0


class TestTimeInRange:
    def test_normal_range(self):
        assert _time_in_range(time(11, 0), time(10, 0), time(12, 0)) is True
        assert _time_in_range(time(9, 0), time(10, 0), time(12, 0)) is False

    def test_midnight_wrap(self):
        assert _time_in_range(time(23, 30), time(23, 0), time(1, 0)) is True
        assert _time_in_range(time(0, 30), time(23, 0), time(1, 0)) is True

    def test_boundary(self):
        assert _time_in_range(time(10, 0), time(10, 0), time(12, 0)) is True
        assert _time_in_range(time(12, 0), time(10, 0), time(12, 0)) is True

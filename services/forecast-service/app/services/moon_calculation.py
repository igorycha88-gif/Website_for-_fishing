from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple

import ephem

from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class MoonData:
    phase: float
    phase_name: str
    illumination: float
    next_new_moon_days: float
    next_full_moon_days: float


@dataclass
class SolunarPeriod:
    start: time
    end: time
    period_type: str
    strength: float


@dataclass
class SolunarData:
    major_periods: List[SolunarPeriod]
    minor_periods: List[SolunarPeriod]


MOON_PHASE_NAMES = [
    (0.00, 0.0625, "Новолуние"),
    (0.0625, 0.1875, "Растущий серп"),
    (0.1875, 0.3125, "Первая четверть"),
    (0.3125, 0.4375, "Растущая луна"),
    (0.4375, 0.5625, "Полнолуние"),
    (0.5625, 0.6875, "Убывающая луна"),
    (0.6875, 0.8125, "Последняя четверть"),
    (0.8125, 0.9375, "Убывающий серп"),
    (0.9375, 1.001, "Новолуние"),
]

SYNODIC_DAYS = 29.53


def _get_phase_name(phase: float) -> str:
    for low, high, name in MOON_PHASE_NAMES:
        if low <= phase < high:
            return name
    return "Новолуние"


def classify_moon_phase(phase: float) -> str:
    p = float(phase) % 1.0
    if p < 0.125 or p >= 0.875:
        return "new"
    if p < 0.375:
        return "waxing"
    if p < 0.625:
        return "full"
    return "waning"


def days_to_nearest_transition(
    next_new_moon_days: float,
    next_full_moon_days: float,
    synodic: float = SYNODIC_DAYS,
) -> float:
    to_new = min(max(0.0, next_new_moon_days), max(0.0, synodic - next_new_moon_days))
    to_full = min(
        max(0.0, next_full_moon_days), max(0.0, synodic - next_full_moon_days)
    )
    return max(0.0, min(to_new, to_full))


def calculate_moon_phase(target_date: date, lat: float, lon: float) -> MoonData:
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = 0
    observer.date = ephem.Date(
        datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0)
    )

    moon = ephem.Moon(observer)
    illumination = moon.phase

    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    synodic_period = next_new - prev_new
    current_age = observer.date - prev_new
    phase = float(current_age / synodic_period) if synodic_period > 0 else 0.0
    phase = max(0.0, min(1.0, phase))

    next_full = ephem.next_full_moon(observer.date)
    next_new_days = float((next_new - observer.date))
    next_full_days = float((next_full - observer.date))

    phase_name = _get_phase_name(phase)

    return MoonData(
        phase=phase,
        phase_name=phase_name,
        illumination=illumination,
        next_new_moon_days=next_new_days,
        next_full_moon_days=next_full_days,
    )


def calculate_solunar_periods(
    target_date: date, lat: float, lon: float
) -> SolunarData:
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = 0
    observer.horizon = "-0:34"
    observer.pressure = 0

    day_start = datetime(
        target_date.year, target_date.month, target_date.day, 0, 0, 0
    )
    observer.date = ephem.Date(day_start)

    moon = ephem.Moon(observer)

    phase_data = calculate_moon_phase(target_date, lat, lon)
    distances = [
        abs(phase_data.phase - 0.0),
        abs(phase_data.phase - 0.5),
        abs(phase_data.phase - 1.0),
    ]
    min_distance = min(distances)
    base_strength = max(0.3, 1.0 - min_distance * 2.0)

    major_periods: List[SolunarPeriod] = []
    minor_periods: List[SolunarPeriod] = []

    try:
        transit1 = _compute_upper_culmination(observer, moon, day_start)
        if transit1:
            start_t = _subtract_minutes(transit1, 60)
            end_t = _add_minutes(transit1, 60)
            major_periods.append(
                SolunarPeriod(
                    start=start_t,
                    end=end_t,
                    period_type="major",
                    strength=base_strength,
                )
            )
    except Exception:
        pass

    try:
        transit2 = _compute_lower_culmination(observer, moon, day_start)
        if transit2:
            start_t = _subtract_minutes(transit2, 60)
            end_t = _add_minutes(transit2, 60)
            major_periods.append(
                SolunarPeriod(
                    start=start_t,
                    end=end_t,
                    period_type="major",
                    strength=base_strength * 0.9,
                )
            )
    except Exception:
        pass

    try:
        rising = observer.next_rising(moon).datetime()
        rising_time = _datetime_to_time(rising, day_start)
        if rising_time:
            minor_periods.append(
                SolunarPeriod(
                    start=_subtract_minutes(rising_time, 30),
                    end=_add_minutes(rising_time, 30),
                    period_type="minor",
                    strength=base_strength * 0.7,
                )
            )
    except Exception:
        pass

    try:
        setting = observer.next_setting(moon).datetime()
        setting_time = _datetime_to_time(setting, day_start)
        if setting_time:
            minor_periods.append(
                SolunarPeriod(
                    start=_subtract_minutes(setting_time, 30),
                    end=_add_minutes(setting_time, 30),
                    period_type="minor",
                    strength=base_strength * 0.7,
                )
            )
    except Exception:
        pass

    if not major_periods:
        major_periods = _compute_solunar_from_phase(phase_data.phase, day_start, base_strength)

    return SolunarData(
        major_periods=major_periods,
        minor_periods=minor_periods,
    )


def _compute_upper_culmination(
    observer: ephem.Observer, moon: ephem.Moon, day_start: datetime
) -> Optional[time]:
    try:
        rising_dt = observer.next_rising(moon).datetime()
        observer_after_rise = ephem.Observer()
        observer_after_rise.lat = observer.lat
        observer_after_rise.lon = observer.lon
        observer_after_rise.elevation = observer.elevation
        observer_after_rise.date = ephem.Date(rising_dt)

        setting_dt = observer_after_rise.next_setting(moon).datetime()

        transit_dt = rising_dt + (setting_dt - rising_dt) / 2
        return _datetime_to_time(transit_dt, day_start)
    except Exception:
        return None


def _compute_lower_culmination(
    observer: ephem.Observer, moon: ephem.Moon, day_start: datetime
) -> Optional[time]:
    try:
        setting_dt = observer.next_setting(moon).datetime()
        observer_after_set = ephem.Observer()
        observer_after_set.lat = observer.lat
        observer_after_set.lon = observer.lon
        observer_after_set.elevation = observer.elevation
        observer_after_set.date = ephem.Date(setting_dt)

        next_rising_dt = observer_after_set.next_rising(moon).datetime()

        antitransit_dt = setting_dt + (next_rising_dt - setting_dt) / 2
        return _datetime_to_time(antitransit_dt, day_start)
    except Exception:
        return None


def _compute_solunar_from_phase(
    phase: float, day_start: datetime, base_strength: float
) -> List[SolunarPeriod]:
    cycle_position = phase * 24.0

    major1_hour = cycle_position % 24
    major2_hour = (cycle_position + 12.0) % 24

    periods = []
    for h in [major1_hour, major2_hour]:
        start_t = _hour_to_time(h - 1.0)
        end_t = _hour_to_time(h + 1.0)
        periods.append(
            SolunarPeriod(
                start=start_t,
                end=end_t,
                period_type="major",
                strength=base_strength * 0.8,
            )
        )

    return periods


def _hour_to_time(hour: float) -> time:
    hour = hour % 24
    h = int(hour)
    m = int((hour - h) * 60)
    s = int(((hour - h) * 60 - m) * 60)
    return time(h % 24, m, s)


def _datetime_to_time(dt: datetime, day_start: datetime) -> Optional[time]:
    day_end = day_start + timedelta(days=1)
    if day_start <= dt < day_end:
        return dt.time()
    elif day_start - timedelta(hours=1) <= dt < day_start:
        return None
    elif day_end <= dt < day_end + timedelta(hours=1):
        return dt.time()
    return None


def _add_minutes(t: time, minutes: int) -> time:
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.time()


def _subtract_minutes(t: time, minutes: int) -> time:
    dt = datetime.combine(date.today(), t) - timedelta(minutes=minutes)
    return dt.time()


def is_time_in_solunar_period(
    check_time: time, periods: List[SolunarPeriod]
) -> Tuple[bool, str, float]:
    for period in periods:
        if _time_in_range(check_time, period.start, period.end):
            return True, period.period_type, period.strength
    return False, "", 0.0


def _time_in_range(check: time, start: time, end: time) -> bool:
    check_seconds = check.hour * 3600 + check.minute * 60 + check.second
    start_seconds = start.hour * 3600 + start.minute * 60 + start.second
    end_seconds = end.hour * 3600 + end.minute * 60 + end.second

    if start_seconds <= end_seconds:
        return start_seconds <= check_seconds <= end_seconds
    else:
        return check_seconds >= start_seconds or check_seconds <= end_seconds


def get_solunar_periods_for_hour(
    solunar_data: SolunarData, target_hour: int
) -> List[SolunarPeriod]:
    matching = []
    check_time = time(target_hour, 30)
    for period in solunar_data.major_periods + solunar_data.minor_periods:
        if _time_in_range(check_time, period.start, period.end):
            matching.append(period)
    return matching

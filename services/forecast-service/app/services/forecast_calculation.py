import math
from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TimeOfDay(Enum):
    MORNING = "morning"
    DAY = "day"
    EVENING = "evening"
    NIGHT = "night"


@dataclass
class PressureTrend:
    trend_3h: float = 0.0
    trend_6h: float = 0.0
    trend_12h: float = 0.0
    trend_24h: float = 0.0
    stability: float = 1.0
    rate_of_change: float = 0.0
    direction: str = "stable"


@dataclass
class WeatherConditions:
    temperature: Optional[Decimal] = None
    pressure_hpa: Optional[int] = None
    wind_speed: Optional[Decimal] = None
    wind_direction: Optional[int] = None
    cloudiness: Optional[int] = None
    precipitation_mm: Optional[Decimal] = None
    moon_phase: Optional[Decimal] = None
    sunrise: Optional[time] = None
    sunset: Optional[time] = None
    pressure_trend: Decimal = Decimal("0")
    pressure_trend_data: Optional[PressureTrend] = None
    is_solunar_major: bool = False
    is_solunar_minor: bool = False
    solunar_strength: float = 0.0


@dataclass
class FishSettings:
    fish_type_id: UUID
    fish_name: str
    optimal_temp_min: Decimal
    optimal_temp_max: Decimal
    optimal_pressure_min: int
    optimal_pressure_max: int
    max_wind_speed: Decimal
    prefer_morning: bool
    prefer_evening: bool
    prefer_overcast: bool
    moon_sensitivity: Decimal
    active_in_winter: bool
    spawn_start_month: Optional[int] = None
    spawn_end_month: Optional[int] = None
    spawn_start_day: int = 1
    spawn_end_day: int = 31


WINTER_MONTHLY_MULTIPLIERS = {
    12: {"active_fish": 0.9, "inactive_fish": 0.2},
    1: {"active_fish": 0.7, "inactive_fish": 0.1},
    2: {"active_fish": 1.0, "inactive_fish": 0.15},
}

MONTH_NAMES = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

REGION_CODE_TO_ZONE = {
    "KDA": "south", "AST": "south", "ROS": "south", "VOR": "south",
    "VGG": "south", "SAR": "south", "SAM": "south",
    "KB": "south", "KC": "south", "SE": "south",
    "PRI": "south", "KHA": "south",
    "MOW": "central", "MOS": "central", "VLG": "central", "KIR": "central",
    "KR": "north", "KO": "north", "MUR": "north", "ARK": "north",
    "NEN": "north", "SVE": "north", "KHM": "north", "YAN": "north",
    "PER": "north", "TOM": "north", "NVS": "north", "KYA": "north",
    "IRK": "north", "KEM": "north", "ALT": "north", "BU": "north",
    "ZAB": "north", "AMU": "north", "YEV": "north", "SA": "north",
    "KAM": "north", "SAK": "north",
}


def get_climate_zone(region_code: str) -> str:
    return REGION_CODE_TO_ZONE.get(region_code, "central")


def get_spawn_dates_for_zone(
    spawn_periods_by_zone: Optional[dict],
    zone: str,
) -> Optional[Tuple[int, int, int, int]]:
    if not spawn_periods_by_zone:
        return None
    zone_data = spawn_periods_by_zone.get(zone)
    if not zone_data:
        return None
    try:
        return (
            zone_data["spawn_start_month"],
            zone_data["spawn_end_month"],
            zone_data.get("spawn_start_day", 1),
            zone_data.get("spawn_end_day", 31),
        )
    except (KeyError, TypeError):
        return None


def get_time_of_day(hour: int) -> TimeOfDay:
    if 6 <= hour < 10:
        return TimeOfDay.MORNING
    elif 10 <= hour < 17:
        return TimeOfDay.DAY
    elif 17 <= hour < 21:
        return TimeOfDay.EVENING
    else:
        return TimeOfDay.NIGHT


def get_season(month: int) -> str:
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "autumn"
    else:
        return "winter"


def calculate_pressure_trend(
    pressure_records: List[Tuple[int, int]],
) -> PressureTrend:
    if len(pressure_records) < 2:
        return PressureTrend()

    sorted_records = sorted(pressure_records, key=lambda x: x[0])
    hours = [r[0] for r in sorted_records]
    pressures_hpa = [r[1] for r in sorted_records]
    pressures_mmhg = [p * 0.750062 for p in pressures_hpa]

    current_hour = hours[-1]
    current_pressure = pressures_mmhg[-1]

    def _trend_for_hours(target_hours_back: float) -> float:
        target_hour = current_hour - target_hours_back
        closest_idx = 0
        closest_dist = abs(hours[0] - target_hour)
        for i, h in enumerate(hours):
            dist = abs(h - target_hour)
            if dist < closest_dist:
                closest_dist = dist
                closest_idx = i
        return current_pressure - pressures_mmhg[closest_idx]

    trend_3h = _trend_for_hours(3)
    trend_6h = _trend_for_hours(6)
    trend_12h = _trend_for_hours(12)
    trend_24h = _trend_for_hours(24)

    if len(pressures_mmhg) >= 2:
        mean = sum(pressures_mmhg) / len(pressures_mmhg)
        variance = sum((p - mean) ** 2 for p in pressures_mmhg) / len(pressures_mmhg)
        std_dev = math.sqrt(variance)
        stability = max(0.0, min(1.0, 1.0 - std_dev / 5.0))
    else:
        stability = 0.5

    rate_of_change = trend_3h / 3.0 if trend_3h != 0 else 0.0

    if abs(rate_of_change) < 0.5:
        direction = "stable"
    elif rate_of_change > 0:
        direction = "rising"
    else:
        direction = "falling"

    return PressureTrend(
        trend_3h=round(trend_3h, 2),
        trend_6h=round(trend_6h, 2),
        trend_12h=round(trend_12h, 2),
        trend_24h=round(trend_24h, 2),
        stability=round(stability, 3),
        rate_of_change=round(rate_of_change, 3),
        direction=direction,
    )


def calculate_temperature_score(
    weather: WeatherConditions, fish: FishSettings
) -> float:
    if weather.temperature is None:
        return 50.0

    temp = float(weather.temperature)
    opt_min = float(fish.optimal_temp_min)
    opt_max = float(fish.optimal_temp_max)

    if opt_min <= temp <= opt_max:
        return 100.0

    deviation = 0
    if temp < opt_min:
        deviation = opt_min - temp
    else:
        deviation = temp - opt_max

    optimal_range = opt_max - opt_min
    if optimal_range == 0:
        optimal_range = 10

    penalty = (deviation / optimal_range) * 50
    return max(0.0, 100.0 - penalty)


def calculate_pressure_score(
    weather: WeatherConditions, fish: FishSettings
) -> float:
    if weather.pressure_hpa is None:
        return 50.0

    pressure_mmhg = weather.pressure_hpa * 0.750062
    pressure = float(pressure_mmhg)
    opt_min = fish.optimal_pressure_min
    opt_max = fish.optimal_pressure_max

    if opt_min <= pressure <= opt_max:
        base_score = 100.0
    else:
        deviation = min(abs(pressure - opt_min), abs(pressure - opt_max))
        base_score = max(0.0, 100.0 - deviation * 3)

    trend_data = weather.pressure_trend_data
    if trend_data:
        rate = abs(trend_data.rate_of_change)
        if rate > 2.0:
            base_score *= 0.7
        elif rate > 1.0:
            base_score *= 0.9

        if trend_data.stability >= 0.8:
            base_score *= 1.1
        elif trend_data.stability < 0.3:
            base_score *= 0.8

        if trend_data.direction == "stable":
            base_score *= 1.05

    return max(0.0, min(100.0, base_score))


def calculate_wind_score(weather: WeatherConditions, fish: FishSettings) -> float:
    if weather.wind_speed is None:
        return 50.0

    speed = float(weather.wind_speed)
    max_wind = float(fish.max_wind_speed)

    if speed <= max_wind * 0.5:
        base_score = 100.0
    elif speed <= max_wind:
        base_score = 100.0 - (speed / max_wind) * 30
    else:
        excess = speed - max_wind
        base_score = max(0.0, 70.0 - excess * 10)

    if weather.wind_direction is not None:
        direction = weather.wind_direction
        if 157.5 <= direction <= 292.5:
            base_score += 10
        elif 0 <= direction <= 67.5 or 337.5 <= direction <= 360:
            base_score -= 10

    return max(0.0, min(100.0, base_score))


def calculate_moon_score(
    weather: WeatherConditions, fish: FishSettings, season: str = "summer"
) -> float:
    if weather.moon_phase is None:
        return 50.0

    phase = float(weather.moon_phase)
    sensitivity = float(fish.moon_sensitivity)

    distances = [
        abs(phase - 0.0),
        abs(phase - 0.5),
        abs(phase - 1.0),
    ]
    min_distance = min(distances)

    phase_score = 100.0 - min_distance * 300
    phase_score = max(10.0, min(100.0, phase_score))

    season_mult = {
        "spring": 1.0,
        "summer": 0.8,
        "autumn": 1.2,
        "winter": 1.3,
    }.get(season, 1.0)

    effective_sensitivity = min(1.0, sensitivity * season_mult)

    base = 50.0 + (phase_score - 50.0) * effective_sensitivity

    if weather.is_solunar_major:
        base = min(100.0, base + 20 * weather.solunar_strength)
    elif weather.is_solunar_minor:
        base = min(100.0, base + 10 * weather.solunar_strength)

    return max(0.0, min(100.0, base))


def calculate_precipitation_score(weather: WeatherConditions) -> float:
    if weather.precipitation_mm is None:
        precip = Decimal("0")
    else:
        precip = weather.precipitation_mm

    precip_val = float(precip)

    if precip_val > 10:
        return 30.0
    elif precip_val > 5:
        return 50.0
    elif precip_val > 0:
        return 75.0
    elif weather.cloudiness is not None and weather.cloudiness > 70:
        return 90.0
    else:
        return 80.0


def calculate_time_score(time_of_day: TimeOfDay, fish: FishSettings) -> float:
    scores = {
        TimeOfDay.MORNING: 100.0 if fish.prefer_morning else 60.0,
        TimeOfDay.DAY: 65.0,
        TimeOfDay.EVENING: 100.0 if fish.prefer_evening else 60.0,
        TimeOfDay.NIGHT: 40.0,
    }
    return scores[time_of_day]


def get_season_multiplier(fish: FishSettings, month: int) -> float:
    if month in [12, 1, 2]:
        multipliers = WINTER_MONTHLY_MULTIPLIERS[month]
        return (
            multipliers["active_fish"]
            if fish.active_in_winter
            else multipliers["inactive_fish"]
        )
    return 1.0


def _geometric_mean(*scores: float) -> float:
    clamped = [max(1.0, s) for s in scores]
    return math.exp(sum(math.log(s) for s in clamped) / len(clamped))


def is_in_spawn_period(fish: FishSettings, check_date: date) -> Tuple[bool, str]:
    if fish.spawn_start_month is None or fish.spawn_end_month is None:
        return False, ""

    month = check_date.month
    day = check_date.day

    start_month = fish.spawn_start_month
    end_month = fish.spawn_end_month

    is_spawn = False

    if start_month <= end_month:
        if start_month == end_month:
            is_spawn = (
                start_month == month
                and fish.spawn_start_day <= day <= fish.spawn_end_day
            )
        else:
            is_spawn = (
                (start_month == month and day >= fish.spawn_start_day)
                or (end_month == month and day <= fish.spawn_end_day)
                or (start_month < month < end_month)
            )
    else:
        is_spawn = (
            (start_month == month and day >= fish.spawn_start_day)
            or (end_month == month and day <= fish.spawn_end_day)
            or (month > start_month)
            or (month < end_month)
        )

    if is_spawn:
        message = f"Нерестовый период ({fish.spawn_start_day} {MONTH_NAMES[start_month]} - {fish.spawn_end_day} {MONTH_NAMES[end_month]}) — вылов запрещен"
        return True, message

    return False, ""


def calculate_bite_score(
    weather: WeatherConditions,
    fish: FishSettings,
    hour: int,
    month: int,
    check_date: Optional[date] = None,
) -> Dict[str, Any]:
    if check_date is None:
        check_date = date.today()

    is_spawn, spawn_message = is_in_spawn_period(fish, check_date)
    if is_spawn:
        return {
            "bite_score": 0,
            "is_spawn_period": True,
            "spawn_message": spawn_message,
            "time_of_day": get_time_of_day(hour).value,
            "temperature_score": None,
            "pressure_score": None,
            "wind_score": None,
            "moon_score": None,
            "precipitation_score": None,
            "season_multiplier": 0,
        }

    time_of_day = get_time_of_day(hour)
    season = get_season(month)

    temp_score = calculate_temperature_score(weather, fish)
    pressure_score = calculate_pressure_score(weather, fish)
    wind_score = calculate_wind_score(weather, fish)
    moon_score = calculate_moon_score(weather, fish, season)
    precip_score = calculate_precipitation_score(weather)
    time_score = calculate_time_score(time_of_day, fish)

    base = _geometric_mean(temp_score, pressure_score)

    solunar_synergy = 1.0 + 0.15 * (moon_score / 100.0) * (pressure_score / 100.0)

    temp_pressure_synergy = 1.0
    if pressure_score >= 70 and temp_score >= 70:
        temp_pressure_synergy = 1.10
    elif pressure_score < 40 or temp_score < 40:
        temp_pressure_synergy = 0.85

    time_adjusted = time_score
    if weather.is_solunar_major:
        time_adjusted = min(100.0, time_score * 1.25)
    elif weather.is_solunar_minor:
        time_adjusted = min(100.0, time_score * 1.10)

    trend_data = weather.pressure_trend_data
    if trend_data:
        stability_mult = 0.85 + 0.15 * trend_data.stability
    else:
        stability_mult = 1.0

    wind_cap = wind_score / 100.0
    precip_cap = precip_score / 100.0

    bite_score = base * solunar_synergy * temp_pressure_synergy * stability_mult
    bite_score = bite_score * (time_adjusted / 100.0) * wind_cap * precip_cap

    season_mult = get_season_multiplier(fish, month)
    bite_score *= season_mult

    bite_score = max(0, min(100, bite_score))

    return {
        "bite_score": round(bite_score, 1),
        "is_spawn_period": False,
        "spawn_message": None,
        "time_of_day": time_of_day.value,
        "temperature_score": round(temp_score, 1),
        "pressure_score": round(pressure_score, 1),
        "wind_score": round(wind_score, 1),
        "moon_score": round(moon_score, 1),
        "precipitation_score": round(precip_score, 1),
        "season_multiplier": season_mult,
    }


def generate_recommendation(
    score: float, weather: WeatherConditions, fish: FishSettings
) -> str:
    recommendations = []

    if score >= 80:
        base = "Отличный клев! Идеальное время для рыбалки."
    elif score >= 65:
        base = "Хороший клев. Рекомендуется выйти на воду."
    elif score >= 50:
        base = "Умеренный клев. Можно рассчитывать на улов."
    elif score >= 35:
        base = "Слабый клев. Потребуется терпение и правильная тактика."
    else:
        base = "Клев маловероятен. Лучше перенести рыбалку."

    recommendations.append(base)

    if weather.wind_speed is not None and float(weather.wind_speed) > 6:
        recommendations.append("Ветреная погода — используйте тяжелые приманки.")

    trend_data = weather.pressure_trend_data
    if trend_data:
        if trend_data.stability >= 0.8:
            recommendations.append("Стабильное давление — отличные условия.")
        elif trend_data.stability < 0.3:
            recommendations.append("Давление нестабильно — рыба может быть осторожной.")
        if abs(trend_data.rate_of_change) > 2.0:
            recommendations.append("Резкое изменение давления — клёв снижен.")
        elif trend_data.direction == "rising" and trend_data.rate_of_change > 0.5:
            recommendations.append("Давление растёт — клев должен улучшаться.")
        elif trend_data.direction == "falling" and trend_data.rate_of_change < -0.5:
            recommendations.append("Давление падает — рыба пассивна.")
    else:
        if float(weather.pressure_trend) < -3:
            recommendations.append("Давление падает — рыба пассивна.")
        elif float(weather.pressure_trend) > 3:
            recommendations.append("Давление растет — клев должен улучшаться.")

    if weather.temperature is not None:
        temp = float(weather.temperature)
        if temp < float(fish.optimal_temp_min):
            recommendations.append("Холодная вода — проводка должна быть медленной.")
        elif temp > float(fish.optimal_temp_max):
            recommendations.append("Теплая вода — рыба держится на глубине.")

    if weather.moon_phase is not None:
        phase = float(weather.moon_phase)
        if phase < 0.1 or phase > 0.9:
            recommendations.append("Новолуние — ночная рыбалка может быть очень удачной.")
        elif 0.4 < phase < 0.6:
            recommendations.append("Полнолуние — рыба может кормиться всю ночь.")

    if weather.is_solunar_major:
        recommendations.append("Solunar major period — пиковая активность рыбы.")
    elif weather.is_solunar_minor:
        recommendations.append("Solunar minor period — умеренная активность.")

    return " ".join(recommendations)


def get_best_baits(fish_name: str, time_of_year: str) -> List[str]:
    baits_map = {
        "Щука": {
            "spring": ["джиг", "воблер", "колебалка"],
            "summer": ["воблер", "вертушка", "силикон"],
            "autumn": ["джиг", "воблер", "поролон"],
            "winter": ["балансир", "блесна", "живец"],
        },
        "Судак": {
            "spring": ["джиг", "твистер", "виброхвост"],
            "summer": ["воблер", "джиг", "поролон"],
            "autumn": ["джиг", "твистер", "воблер"],
            "winter": ["балансир", "блесна"],
        },
        "Окунь": {
            "spring": ["вертушка", "микроджиг", "воблер"],
            "summer": ["вертушка", "воблер", "силикон"],
            "autumn": ["джиг", "вертушка", "воблер"],
            "winter": ["мормышка", "балансир", "блесна"],
        },
        "Карп": {
            "spring": ["бойлы", "кукуруза", "пеллетс"],
            "summer": ["бойлы", "кукуруза", "червь"],
            "autumn": ["бойлы", "пеллетс", "кукуруза"],
            "winter": [],
        },
        "Лещ": {
            "spring": ["червь", "опарыш", "мотыль"],
            "summer": ["кукуруза", "червь", "перловка"],
            "autumn": ["червь", "опарыш", "мотыль"],
            "winter": ["мотыль", "червь", "опарыш"],
        },
        "Карась": {
            "spring": ["червь", "опарыш", "перловка"],
            "summer": ["червь", "хлеб", "тест"],
            "autumn": ["червь", "опарыш", "мотыль"],
            "winter": ["мотыль", "червь", "опарыш"],
        },
        "Плотва": {
            "spring": ["мотыль", "опарыш", "червь"],
            "summer": ["перловка", "кукуруза", "опарыш"],
            "autumn": ["мотыль", "опарыш", "червь"],
            "winter": ["мотыль", "опарыш"],
        },
        "Налим": {
            "spring": ["живец", "червь", "кусок рыбы"],
            "summer": [],
            "autumn": ["живец", "червь", "кусок рыбы"],
            "winter": ["живец", "кусок рыбы", "червь"],
        },
        "Сом": {
            "spring": ["живец", "лягушка", "червь"],
            "summer": ["живец", "лягушка", "перепелка"],
            "autumn": ["живец", "кусок рыбы"],
            "winter": [],
        },
    }

    return baits_map.get(fish_name, {}).get(time_of_year, ["универсальная приманка"])


def get_best_depth(fish_name: str, season: str) -> str:
    depths = {
        "Щука": {
            "spring": "1-3 м",
            "summer": "2-5 м",
            "autumn": "2-4 м",
            "winter": "3-6 м",
        },
        "Судак": {
            "spring": "3-6 м",
            "summer": "4-8 м",
            "autumn": "4-7 м",
            "winter": "5-10 м",
        },
        "Окунь": {
            "spring": "1-3 м",
            "summer": "2-4 м",
            "autumn": "2-5 м",
            "winter": "3-8 м",
        },
        "Карп": {
            "spring": "1-2 м",
            "summer": "2-4 м",
            "autumn": "2-3 м",
            "winter": "глубина",
        },
        "Лещ": {
            "spring": "3-5 м",
            "summer": "4-7 м",
            "autumn": "4-6 м",
            "winter": "5-10 м",
        },
        "Карась": {
            "spring": "0.5-2 м",
            "summer": "1-3 м",
            "autumn": "1-2 м",
            "winter": "2-4 м",
        },
        "Плотва": {
            "spring": "1-3 м",
            "summer": "2-4 м",
            "autumn": "2-4 м",
            "winter": "3-6 м",
        },
        "Налим": {
            "spring": "3-6 м",
            "summer": "5-10 м",
            "autumn": "3-5 м",
            "winter": "2-5 м",
        },
        "Сом": {
            "spring": "2-4 м",
            "summer": "3-6 м",
            "autumn": "3-5 м",
            "winter": "глубина",
        },
    }

    return depths.get(fish_name, {}).get(season, "2-4 м")


def get_seasonal_recommendations(
    fish_settings: dict, season: str, category: str
) -> tuple[list[str] | None, list[str] | None]:
    bait_recs = fish_settings.get("bait_recommendations", {}) if fish_settings else {}
    lure_recs = fish_settings.get("lure_recommendations", {}) if fish_settings else {}

    baits = bait_recs.get(season, []) if bait_recs else []
    lures = lure_recs.get(season, []) if lure_recs else []

    if category in ("peaceful", "commercial"):
        return baits if baits else None, None
    elif category in ("predatory", "sport"):
        return None, lures if lures else None

    return None, None

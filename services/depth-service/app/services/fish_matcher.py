FISH_DEPTH_TABLE = {
    "Щука": {"spring": (1, 3), "summer": (2, 5), "autumn": (2, 4), "winter": (3, 6), "icon": "🐟"},
    "Судак": {"spring": (3, 6), "summer": (4, 8), "autumn": (4, 7), "winter": (5, 10), "icon": "🐠"},
    "Окунь": {"spring": (1, 3), "summer": (2, 4), "autumn": (2, 5), "winter": (3, 8), "icon": "🐟"},
    "Карп": {"spring": (1, 2), "summer": (2, 4), "autumn": (2, 3), "winter": None, "icon": "🐡"},
    "Лещ": {"spring": (3, 5), "summer": (4, 7), "autumn": (4, 6), "winter": (5, 10), "icon": "🐟"},
    "Карась": {"spring": (0.5, 2), "summer": (1, 3), "autumn": (1, 2), "winter": (2, 4), "icon": "🐟"},
    "Плотва": {"spring": (1, 3), "summer": (2, 4), "autumn": (2, 4), "winter": (3, 6), "icon": "🐟"},
    "Налим": {"spring": (3, 6), "summer": (5, 10), "autumn": (3, 5), "winter": (2, 5), "icon": "🐟"},
    "Сом": {"spring": (2, 4), "summer": (3, 6), "autumn": (3, 5), "winter": None, "icon": "🐙"},
}

SEASON_MAP = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
}


def get_season(month: int | None = None) -> str:
    from datetime import datetime, timezone
    if month is None:
        month = datetime.now(timezone.utc).month
    return SEASON_MAP.get(month, "summer")


def match_fish_by_depth(depth: float, season: str | None = None) -> list[dict]:
    if depth is None or depth < 0:
        return []

    if season is None:
        season = get_season()

    matches = []
    abs_depth = abs(depth)

    for fish_name, seasons in FISH_DEPTH_TABLE.items():
        depth_range = seasons.get(season)
        if depth_range is None:
            continue
        d_min, d_max = depth_range
        if d_min <= abs_depth <= d_max:
            matches.append({
                "name": fish_name,
                "icon": seasons.get("icon", "🐟"),
                "depth_range": f"{d_min}-{d_max} м",
                "season": season,
            })

    return matches


def get_depth_category(depth: float) -> str:
    abs_d = abs(depth)
    if abs_d < 2:
        return "Очень мелко"
    elif abs_d < 5:
        return "Мелководье"
    elif abs_d < 10:
        return "Средняя глубина"
    elif abs_d < 20:
        return "Глубоко"
    else:
        return "Очень глубоко"

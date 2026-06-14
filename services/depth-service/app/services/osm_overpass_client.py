import httpx

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_WATER_TAG_MAP = {
    "lake": "lake",
    "reservoir": "reservoir",
    "pond": "pond",
    "river": "river",
    "stream": "river",
    "canal": "river",
    "lagoon": "lake",
}

_WATERWAY_MAP = {
    "riverbank": "river",
    "river": "river",
    "stream": "river",
    "canal": "river",
}


def _parse_water_type(tags: dict) -> str | None:
    water = tags.get("water")
    if water and water in _WATER_TAG_MAP:
        return _WATER_TAG_MAP[water]
    waterway = tags.get("waterway")
    if waterway and waterway in _WATERWAY_MAP:
        return _WATERWAY_MAP[waterway]
    natural = tags.get("natural")
    if natural == "water":
        return "lake"
    return None


def _parse_depth(tags: dict) -> tuple[float | None, str | None]:
    depth = tags.get("depth")
    max_depth = tags.get("depth:max") or tags.get("max_depth")

    if depth:
        try:
            return abs(float(depth)), "avg"
        except (ValueError, TypeError):
            pass

    if max_depth:
        try:
            return abs(float(max_depth)), "max"
        except (ValueError, TypeError):
            pass

    return None, None


def _build_query(lat: float, lon: float, radius: int) -> str:
    return (
        f"[out:json][timeout:{settings.OVERPASS_TIMEOUT}];\n"
        f"(\n"
        f'  way(around:{radius},{lat},{lon})["natural"="water"];\n'
        f'  way(around:{radius},{lat},{lon})["waterway"="riverbank"];\n'
        f'  relation(around:{radius},{lat},{lon})["natural"="water"];\n'
        f"  relation(around:{radius},{lat},{lon})[\"boundary\"=\"water_management\"];\n"
        f");\n"
        f"out tags center;"
    )


def _pick_best_element(elements: list[dict]) -> dict | None:
    if not elements:
        return None

    with_depth = [e for e in elements if "depth" in e.get("tags", {}) or "depth:max" in e.get("tags", {}) or "max_depth" in e.get("tags", {})]
    if with_depth:
        largest = max(with_depth, key=lambda e: e.get("tags", {}).get("area", "0"))
        return largest.get("tags", {})

    with_name = [e for e in elements if "name" in e.get("tags", {})]
    if with_name:
        largest = max(with_name, key=lambda e: e.get("tags", {}).get("area", "0"))
        return largest.get("tags", {})

    if elements:
        return elements[0].get("tags", {})

    return None


async def query_water_body(lat: float, lon: float) -> dict | None:
    logger.info(
        "osm_query_start",
        service="depth-service",
        action="osm_query",
        lat=lat,
        lon=lon,
        radius=settings.OVERPASS_SEARCH_RADIUS_M,
    )

    query = _build_query(lat, lon, settings.OVERPASS_SEARCH_RADIUS_M)

    try:
        async with httpx.AsyncClient(timeout=settings.OVERPASS_TIMEOUT + 5) as client:
            resp = await client.post(
                settings.OVERPASS_API_URL,
                data={"data": query},
            )

            if resp.status_code == 429:
                logger.warning(
                    "osm_rate_limited",
                    service="depth-service",
                    action="osm_query",
                    lat=lat,
                    lon=lon,
                    status_code=429,
                )
                return None

            if resp.status_code != 200:
                logger.warning(
                    "osm_http_error",
                    service="depth-service",
                    action="osm_query",
                    lat=lat,
                    lon=lon,
                    status_code=resp.status_code,
                )
                return None

            data = resp.json()
            elements = data.get("elements", [])
            tags = _pick_best_element(elements)

            if tags is None:
                logger.info(
                    "osm_no_water_body",
                    service="depth-service",
                    action="osm_query",
                    lat=lat,
                    lon=lon,
                )
                return None

            name = tags.get("name")
            water_type = _parse_water_type(tags)
            depth, depth_type = _parse_depth(tags)

            result = {
                "name": name,
                "water_type": water_type,
                "depth": depth,
                "depth_type": depth_type,
                "source": "OSM",
                "accuracy_m": settings.OVERPASS_SEARCH_RADIUS_M,
                "has_data": depth is not None,
            }

            logger.info(
                "osm_query_result",
                service="depth-service",
                action="osm_query",
                lat=lat,
                lon=lon,
                name=name,
                water_type=water_type,
                depth=depth,
                has_data=result["has_data"],
            )
            return result

    except httpx.TimeoutException:
        logger.warning(
            "osm_timeout",
            service="depth-service",
            action="osm_query",
            lat=lat,
            lon=lon,
        )
        return None
    except Exception as e:
        logger.warning(
            "osm_error",
            service="depth-service",
            action="osm_query",
            lat=lat,
            lon=lon,
            error=str(e),
        )
        return None

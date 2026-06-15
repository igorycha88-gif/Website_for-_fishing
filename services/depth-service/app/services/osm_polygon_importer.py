import asyncio
import json

import httpx
from sqlalchemy import text

from app.core.config import settings
from app.core.database import async_session
from app.core.logging_config import get_logger
from app.seed.seed_water_bodies import WATER_BODIES

logger = get_logger(__name__)

_OVERPASS_DELAY_SEC = 2
_MAX_RETRIES = 3


def _build_overpass_query(
    name: str, lat_min: float, lon_min: float, lat_max: float, lon_max: float
) -> str:
    bbox = f"{lat_min},{lon_min},{lat_max},{lon_max}"
    return (
        f"[out:json][timeout:60];\n"
        f"(\n"
        f'  way({bbox})["natural"="water"]["name"="{name}"];\n'
        f'  relation({bbox})["natural"="water"]["name"="{name}"];\n'
        f'  way({bbox})["waterway"="riverbank"]["name"="{name}"];\n'
        f'  relation({bbox})["waterway"="riverbank"]["name"="{name}"];\n'
        f");\n"
        f"out geom;"
    )


def _parse_polygon_from_overpass(data: dict) -> list[list[list[float]]] | None:
    elements = data.get("elements", [])

    ways = [e for e in elements if e.get("type") == "way" and "geometry" in e]
    if ways:
        ways_sorted = sorted(ways, key=lambda w: len(w["geometry"]), reverse=True)
        rings = []
        for way in ways_sorted[:5]:
            coords = [[node["lon"], node["lat"]] for node in way.get("geometry", [])]
            if len(coords) >= 3:
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                rings.append(coords)
        if rings:
            return rings

    relations = [e for e in elements if e.get("type") == "relation" and "members" in e]
    if relations:
        rings = []
        for rel in relations:
            outer_members = [
                m
                for m in rel.get("members", [])
                if m.get("role") == "outer" and "geometry" in m
            ]
            for member in outer_members[:10]:
                coords = [[n["lon"], n["lat"]] for n in member.get("geometry", [])]
                if len(coords) >= 3:
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])
                    rings.append(coords)
        if rings:
            return rings

    return None


def _compute_bbox_and_centroid(
    rings: list[list[list[float]]],
) -> tuple[float, float, float, float, float, float]:
    all_coords = [c for ring in rings for c in ring]
    lons = [c[0] for c in all_coords]
    lats = [c[1] for c in all_coords]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    centroid_lat = sum(lats) / len(lats)
    centroid_lon = sum(lons) / len(lons)
    return lat_min, lat_max, lon_min, lon_max, centroid_lat, centroid_lon


async def _fetch_overpass(query: str) -> dict | None:
    for attempt in range(_MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    settings.OVERPASS_API_URL, data={"data": query}
                )
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 429:
                    logger.warning(
                        "overpass_rate_limited",
                        service="depth-service",
                        action="polygon_import",
                        attempt=attempt + 1,
                    )
                    await asyncio.sleep(5)
                    continue
                logger.warning(
                    "overpass_http_error",
                    service="depth-service",
                    action="polygon_import",
                    status_code=resp.status_code,
                )
                return None
        except httpx.TimeoutException:
            logger.warning(
                "overpass_timeout",
                service="depth-service",
                action="polygon_import",
                attempt=attempt + 1,
            )
            await asyncio.sleep(3)
        except Exception as e:
            logger.warning(
                "overpass_error",
                service="depth-service",
                action="polygon_import",
                error=str(e),
                attempt=attempt + 1,
            )
            await asyncio.sleep(3)
    return None


async def import_single_water_body(wb: dict) -> bool:
    name = wb["name"]
    logger.info(
        "polygon_import_start",
        service="depth-service",
        action="polygon_import",
        name=name,
    )

    query = _build_overpass_query(
        name, wb["lat_min"], wb["lon_min"], wb["lat_max"], wb["lon_max"]
    )
    data = await _fetch_overpass(query)

    if data is None:
        logger.warning(
            "polygon_import_no_data",
            service="depth-service",
            action="polygon_import",
            name=name,
        )
        return False

    rings = _parse_polygon_from_overpass(data)
    if rings is None:
        logger.warning(
            "polygon_import_parse_fail",
            service="depth-service",
            action="polygon_import",
            name=name,
        )
        return False

    lat_min, lat_max, lon_min, lon_max, centroid_lat, centroid_lon = (
        _compute_bbox_and_centroid(rings)
    )

    async with async_session() as session:
        await session.execute(
            text(
                """
                INSERT INTO water_body_polygons
                    (name, water_type, coordinates, lat_min, lat_max, lon_min, lon_max,
                     centroid_lat, centroid_lon, max_depth, avg_depth, area_km2,
                     source, region)
                VALUES
                    (:name, :water_type, CAST(:coordinates AS JSONB),
                     :lat_min, :lat_max, :lon_min, :lon_max,
                     :centroid_lat, :centroid_lon, :max_depth, :avg_depth,
                     :area_km2, 'OSM', :region)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "name": name,
                "water_type": wb.get("water_type", "lake"),
                "coordinates": json.dumps(rings),
                "lat_min": lat_min,
                "lat_max": lat_max,
                "lon_min": lon_min,
                "lon_max": lon_max,
                "centroid_lat": centroid_lat,
                "centroid_lon": centroid_lon,
                "max_depth": wb.get("max_depth"),
                "avg_depth": wb.get("avg_depth"),
                "area_km2": wb.get("area_km2"),
                "region": wb.get("region"),
            },
        )
        await session.commit()

    logger.info(
        "polygon_import_success",
        service="depth-service",
        action="polygon_import",
        name=name,
        rings=len(rings),
    )
    return True


async def seed_polygons_if_empty():
    try:
        async with async_session() as session:
            result = await session.execute(
                text("SELECT COUNT(*) FROM water_body_polygons")
            )
            count = result.scalar()
            if count and count > 0:
                logger.info(
                    "polygon_seed_skip",
                    service="depth-service",
                    action="polygon_seed",
                    existing=count,
                )
                return

        logger.info(
            "polygon_seed_start",
            service="depth-service",
            action="polygon_seed",
            total=len(WATER_BODIES),
        )

        imported = 0
        for wb in WATER_BODIES:
            success = await import_single_water_body(wb)
            if success:
                imported += 1
            await asyncio.sleep(_OVERPASS_DELAY_SEC)

        logger.info(
            "polygon_seed_completed",
            service="depth-service",
            action="polygon_seed",
            imported=imported,
            total=len(WATER_BODIES),
        )
    except Exception as e:
        logger.error(
            "polygon_seed_error",
            service="depth-service",
            action="polygon_seed",
            error=str(e),
            exc_info=True,
        )

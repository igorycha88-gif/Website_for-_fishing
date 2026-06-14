import math

from sqlalchemy import text

from app.core.database import async_session
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def query_water_body(lat: float, lon: float) -> dict | None:
    logger.info(
        "gvr_query_start",
        service="depth-service",
        action="gvr_query",
        lat=lat,
        lon=lon,
    )

    try:
        async with async_session() as session:
            query = text(
                """
                SELECT name, water_type, avg_depth, max_depth,
                       centroid_lat, centroid_lon, area_km2, gvr_id
                FROM ru_water_bodies
                WHERE lat_min <= :lat AND lat_max >= :lat
                  AND lon_min <= :lon AND lon_max >= :lon
                ORDER BY area_km2 DESC NULLS LAST
                LIMIT 5
                """
            )
            result = await session.execute(query, {"lat": lat, "lon": lon})
            rows = result.fetchall()

            if not rows:
                logger.info(
                    "gvr_no_match",
                    service="depth-service",
                    action="gvr_query",
                    lat=lat,
                    lon=lon,
                )
                return None

            best = min(
                rows,
                key=lambda r: _haversine_km(
                    lat, lon, r.centroid_lat, r.centroid_lon
                ),
            )

            depth = None
            depth_type = None

            if best.max_depth is not None:
                depth = float(best.max_depth)
                depth_type = "max"
            elif best.avg_depth is not None:
                depth = float(best.avg_depth)
                depth_type = "avg"

            result_dict = {
                "name": best.name,
                "water_type": best.water_type,
                "depth": depth,
                "depth_type": depth_type,
                "source": "GVR",
                "accuracy_m": 100,
                "has_data": depth is not None,
                "area_km2": float(best.area_km2) if best.area_km2 else None,
                "gvr_id": best.gvr_id,
            }

            logger.info(
                "gvr_query_result",
                service="depth-service",
                action="gvr_query",
                lat=lat,
                lon=lon,
                name=best.name,
                water_type=best.water_type,
                depth=depth,
                has_data=result_dict["has_data"],
            )
            return result_dict

    except Exception as e:
        logger.warning(
            "gvr_query_error",
            service="depth-service",
            action="gvr_query",
            lat=lat,
            lon=lon,
            error=str(e),
        )
        return None


async def query_water_body_by_name(name: str) -> dict | None:
    logger.info(
        "gvr_name_lookup_start",
        service="depth-service",
        action="gvr_name_lookup",
        name=name,
    )

    try:
        async with async_session() as session:
            query = text(
                """
                SELECT name, water_type, avg_depth, max_depth,
                       centroid_lat, centroid_lon, area_km2, gvr_id
                FROM ru_water_bodies
                WHERE name ILIKE :name
                ORDER BY area_km2 DESC NULLS LAST
                LIMIT 1
                """
            )
            result = await session.execute(query, {"name": f"%{name}%"})
            row = result.fetchone()

            if row is None:
                logger.info(
                    "gvr_name_not_found",
                    service="depth-service",
                    action="gvr_name_lookup",
                    name=name,
                )
                return None

            depth = None
            depth_type = None

            if row.max_depth is not None:
                depth = float(row.max_depth)
                depth_type = "max"
            elif row.avg_depth is not None:
                depth = float(row.avg_depth)
                depth_type = "avg"

            result_dict = {
                "name": row.name,
                "water_type": row.water_type,
                "depth": depth,
                "depth_type": depth_type,
                "source": "GVR",
                "accuracy_m": 100,
                "has_data": depth is not None,
                "area_km2": float(row.area_km2) if row.area_km2 else None,
                "gvr_id": row.gvr_id,
            }

            logger.info(
                "gvr_name_lookup_result",
                service="depth-service",
                action="gvr_name_lookup",
                name=row.name,
                depth=depth,
                has_data=result_dict["has_data"],
            )
            return result_dict

    except Exception as e:
        logger.warning(
            "gvr_name_lookup_error",
            service="depth-service",
            action="gvr_name_lookup",
            name=name,
            error=str(e),
        )
        return None

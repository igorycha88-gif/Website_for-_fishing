import json

from sqlalchemy import text

from app.core.database import async_session
from app.core.logging_config import get_logger
from app.services.depth_colors import depth_to_color, depth_category_label

logger = get_logger(__name__)

_MAX_FEATURES = 200


async def get_depth_areas(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    scheme: str = "navionics",
) -> dict:
    logger.info(
        "depth_areas_start",
        service="depth-service",
        action="depth_areas",
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        scheme=scheme,
    )

    features = []

    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT name, water_type, coordinates, max_depth, avg_depth,
                           centroid_lat, centroid_lon, area_km2, region
                    FROM water_body_polygons
                    WHERE lat_min <= :max_lat AND lat_max >= :min_lat
                      AND lon_min <= :max_lon AND lon_max >= :min_lon
                    ORDER BY area_km2 DESC NULLS LAST
                    LIMIT :limit
                    """
                ),
                {
                    "min_lat": min_lat,
                    "min_lon": min_lon,
                    "max_lat": max_lat,
                    "max_lon": max_lon,
                    "limit": _MAX_FEATURES,
                },
            )
            rows = result.fetchall()

            for row in rows:
                coords = row.coordinates if isinstance(row.coordinates, list) else json.loads(row.coordinates)
                depth = row.max_depth if row.max_depth is not None else row.avg_depth
                color = depth_to_color(depth, scheme) if depth else "#888888"

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": coords,
                    },
                    "properties": {
                        "name": row.name,
                        "water_type": row.water_type,
                        "max_depth": row.max_depth,
                        "avg_depth": row.avg_depth,
                        "depth": depth,
                        "color": color,
                        "category": depth_category_label(depth) if depth else None,
                        "region": row.region,
                    },
                }
                features.append(feature)

            logger.info(
                "depth_areas_polygons",
                service="depth-service",
                action="depth_areas",
                count=len(features),
            )

            if len(features) < _MAX_FEATURES:
                bbox_features = await _get_bbox_fallback(
                    session, min_lat, min_lon, max_lat, max_lon, scheme, features
                )
                features.extend(bbox_features)

    except Exception as e:
        logger.error(
            "depth_areas_error",
            service="depth-service",
            action="depth_areas",
            error=str(e),
            exc_info=True,
        )

    logger.info(
        "depth_areas_completed",
        service="depth-service",
        action="depth_areas",
        total=len(features),
    )

    return {"type": "FeatureCollection", "features": features}


async def _get_bbox_fallback(
    session,
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    scheme: str,
    existing_features: list,
) -> list:
    existing_names = {
        f["properties"]["name"] for f in existing_features if f["properties"].get("name")
    }

    result = await session.execute(
        text(
            """
            SELECT name, water_type, lat_min, lat_max, lon_min, lon_max,
                   centroid_lat, centroid_lon, max_depth, avg_depth, area_km2, region
            FROM ru_water_bodies
            WHERE lat_min <= :max_lat AND lat_max >= :min_lat
              AND lon_min <= :max_lon AND lon_max >= :min_lon
            ORDER BY area_km2 DESC NULLS LAST
            LIMIT :limit
            """
        ),
        {
            "min_lat": min_lat,
            "min_lon": min_lon,
            "max_lat": max_lat,
            "max_lon": max_lon,
            "limit": _MAX_FEATURES - len(existing_features),
        },
    )
    rows = result.fetchall()

    features = []
    for row in rows:
        if row.name in existing_names:
            continue

        depth = row.max_depth if row.max_depth is not None else row.avg_depth
        color = depth_to_color(depth, scheme) if depth else "#888888"

        ring = [
            [row.lon_min, row.lat_min],
            [row.lon_max, row.lat_min],
            [row.lon_max, row.lat_max],
            [row.lon_min, row.lat_max],
            [row.lon_min, row.lat_min],
        ]

        feature = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {
                "name": row.name,
                "water_type": row.water_type,
                "max_depth": row.max_depth,
                "avg_depth": row.avg_depth,
                "depth": depth,
                "color": color,
                "category": depth_category_label(depth) if depth else None,
                "region": row.region,
                "fallback_bbox": True,
            },
        }
        features.append(feature)

    return features

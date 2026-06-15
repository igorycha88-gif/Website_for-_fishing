from sqlalchemy import text

from app.core.database import async_session
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_MIN_ZOOM_FOR_LABELS = 7


async def get_depth_labels(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    zoom: int = 10,
) -> dict:
    logger.info(
        "depth_labels_start",
        service="depth-service",
        action="depth_labels",
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        zoom=zoom,
    )

    if zoom < _MIN_ZOOM_FOR_LABELS:
        logger.info(
            "depth_labels_skip_low_zoom",
            service="depth-service",
            action="depth_labels",
            zoom=zoom,
        )
        return {"type": "FeatureCollection", "features": []}

    features = []
    seen_names = set()

    try:
        async with async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT name, water_type, centroid_lat, centroid_lon,
                           max_depth, avg_depth, area_km2
                    FROM water_body_polygons
                    WHERE lat_min <= :max_lat AND lat_max >= :min_lat
                      AND lon_min <= :max_lon AND lon_max >= :min_lon
                    ORDER BY area_km2 DESC NULLS LAST
                    LIMIT 100
                    """
                ),
                {
                    "min_lat": min_lat,
                    "min_lon": min_lon,
                    "max_lat": max_lat,
                    "max_lon": max_lon,
                },
            )
            rows = result.fetchall()

            for row in rows:
                if row.name in seen_names:
                    continue
                seen_names.add(row.name)

                depth = row.max_depth if row.max_depth is not None else row.avg_depth
                if depth is None:
                    continue

                label = f"{depth:g}\u043c"

                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [row.centroid_lon, row.centroid_lat],
                        },
                        "properties": {
                            "name": row.name,
                            "depth": depth,
                            "label": label,
                            "water_type": row.water_type,
                        },
                    }
                )

            if len(features) < 50:
                bbox_result = await session.execute(
                    text(
                        """
                        SELECT name, water_type, centroid_lat, centroid_lon,
                               max_depth, avg_depth, area_km2
                        FROM ru_water_bodies
                        WHERE lat_min <= :max_lat AND lat_max >= :min_lat
                          AND lon_min <= :max_lon AND lon_max >= :min_lon
                        ORDER BY area_km2 DESC NULLS LAST
                        LIMIT 50
                        """
                    ),
                    {
                        "min_lat": min_lat,
                        "min_lon": min_lon,
                        "max_lat": max_lat,
                        "max_lon": max_lon,
                    },
                )
                bbox_rows = bbox_result.fetchall()

                for row in bbox_rows:
                    if row.name in seen_names:
                        continue
                    seen_names.add(row.name)

                    depth = row.max_depth if row.max_depth is not None else row.avg_depth
                    if depth is None:
                        continue

                    label = f"{depth:g}\u043c"

                    features.append(
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [row.centroid_lon, row.centroid_lat],
                            },
                            "properties": {
                                "name": row.name,
                                "depth": depth,
                                "label": label,
                                "water_type": row.water_type,
                            },
                        }
                    )

    except Exception as e:
        logger.error(
            "depth_labels_error",
            service="depth-service",
            action="depth_labels",
            error=str(e),
            exc_info=True,
        )

    logger.info(
        "depth_labels_completed",
        service="depth-service",
        action="depth_labels",
        count=len(features),
    )

    return {"type": "FeatureCollection", "features": features}

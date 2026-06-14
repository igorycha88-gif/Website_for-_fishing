from fastapi import APIRouter, Query

from app.core.logging_config import get_logger
from app.services.depth_resolver import resolve_depth
from app.services.fish_matcher import match_fish_by_depth, get_depth_category, get_season

router = APIRouter(prefix="/depth", tags=["depth"])
logger = get_logger(__name__)


@router.get("/point")
async def get_depth_at_point(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    logger.info(
        "request_started",
        service="depth-service",
        action="get_depth_at_point",
        lat=lat,
        lon=lon,
    )

    result = await resolve_depth(lat, lon)

    depth = result.get("depth")
    has_data = result.get("has_data", False)
    category = None
    fish_match = []

    if has_data and depth is not None:
        category = get_depth_category(depth)
        fish_match = match_fish_by_depth(depth)

    response = {
        "depth": depth,
        "depth_display": result.get("depth_display"),
        "category": category,
        "source": result.get("source"),
        "accuracy_m": result.get("accuracy_m"),
        "has_data": has_data,
        "lat": lat,
        "lon": lon,
        "season": get_season(),
        "fish_match": fish_match,
        "water_body_name": result.get("water_body_name"),
        "water_body_type": result.get("water_body_type"),
        "depth_type": result.get("depth_type"),
    }

    logger.info(
        "request_completed",
        service="depth-service",
        action="get_depth_at_point",
        lat=lat,
        lon=lon,
        depth=response["depth"],
        has_data=has_data,
        source=response["source"],
        water_body=response["water_body_name"],
        fish_count=len(fish_match),
    )

    return response

from fastapi import APIRouter, Query, HTTPException

from app.core.logging_config import get_logger
from app.services.depth_areas import get_depth_areas

router = APIRouter(prefix="/depth", tags=["depth-areas"])
logger = get_logger(__name__)

_VALID_SCHEMES = {"navionics", "contrast", "sport"}


@router.get("/areas")
async def get_areas(
    minLat: float = Query(..., ge=-90, le=90, description="Minimum latitude"),
    minLon: float = Query(..., ge=-180, le=180, description="Minimum longitude"),
    maxLat: float = Query(..., ge=-90, le=90, description="Maximum latitude"),
    maxLon: float = Query(..., ge=-180, le=180, description="Maximum longitude"),
    scheme: str = Query("navionics", description="Color scheme: navionics, contrast, sport"),
):
    if scheme not in _VALID_SCHEMES:
        raise HTTPException(status_code=400, detail=f"Invalid scheme. Must be one of: {_VALID_SCHEMES}")

    logger.info(
        "request_started",
        service="depth-service",
        action="get_areas",
        minLat=minLat,
        minLon=minLon,
        maxLat=maxLat,
        maxLon=maxLon,
        scheme=scheme,
    )

    result = await get_depth_areas(minLat, minLon, maxLat, maxLon, scheme)

    logger.info(
        "request_completed",
        service="depth-service",
        action="get_areas",
        features=len(result.get("features", [])),
    )

    return result

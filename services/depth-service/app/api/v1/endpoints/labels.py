from fastapi import APIRouter, Query

from app.core.logging_config import get_logger
from app.services.depth_labels import get_depth_labels

router = APIRouter(prefix="/depth", tags=["depth-labels"])
logger = get_logger(__name__)


@router.get("/labels")
async def get_labels(
    minLat: float = Query(..., ge=-90, le=90, description="Minimum latitude"),
    minLon: float = Query(..., ge=-180, le=180, description="Minimum longitude"),
    maxLat: float = Query(..., ge=-90, le=90, description="Maximum latitude"),
    maxLon: float = Query(..., ge=-180, le=180, description="Maximum longitude"),
    zoom: int = Query(10, ge=0, le=20, description="Current map zoom level"),
):
    logger.info(
        "request_started",
        service="depth-service",
        action="get_labels",
        minLat=minLat,
        minLon=minLon,
        maxLat=maxLat,
        maxLon=maxLon,
        zoom=zoom,
    )

    result = await get_depth_labels(minLat, minLon, maxLat, maxLon, zoom)

    logger.info(
        "request_completed",
        service="depth-service",
        action="get_labels",
        features=len(result.get("features", [])),
    )

    return result

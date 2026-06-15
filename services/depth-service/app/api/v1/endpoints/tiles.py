from fastapi import APIRouter, Path, Query, HTTPException
from fastapi.responses import Response

from app.core.logging_config import get_logger
from app.services.depth_reader import fetch_tile

router = APIRouter(prefix="/depth/tiles", tags=["depth-tiles"])
logger = get_logger(__name__)

_VALID_SCHEMES = {"navionics", "contrast", "sport"}

_TRANSPARENT_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c63600100000005000156fed98a0000000049454e44ae426082"
)


@router.get("/{z}/{x}/{y}.png")
async def get_tile(
    z: int = Path(..., ge=0, le=18),
    x: int = Path(..., ge=0),
    y: int = Path(..., ge=0),
    scheme: str = Query("navionics", description="Color scheme"),
):
    if scheme not in _VALID_SCHEMES:
        raise HTTPException(status_code=400, detail=f"Invalid scheme. Must be one of: {_VALID_SCHEMES}")

    logger.info(
        "request_started",
        service="depth-service",
        action="get_tile",
        z=z,
        x=x,
        y=y,
        scheme=scheme,
    )

    tile_data = await fetch_tile(z, x, y, scheme=scheme)

    if tile_data is None:
        return Response(content=_TRANSPARENT_PNG, media_type="image/png")

    logger.info(
        "request_completed",
        service="depth-service",
        action="get_tile",
        z=z,
        x=x,
        y=y,
        size=len(tile_data),
    )

    return Response(content=tile_data, media_type="image/png")

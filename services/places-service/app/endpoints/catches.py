from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.schemas.catch_point import (
    CatchPointResponse,
    CatchPointListResponse,
)
from app.crud.catch_point import crud_catch_point

logger = get_logger(__name__)
router = APIRouter()


@router.get("/catches", response_model=CatchPointListResponse)
async def get_catch_points(
    river: Optional[str] = None,
    fish_type_id: Optional[UUID] = None,
    min_lat: Optional[float] = None,
    min_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    page: int = 1,
    page_size: int = 200,
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "request_started",
        action="get_catch_points",
        service="places-service",
        filters={
            "river": river,
            "fish_type_id": str(fish_type_id) if fish_type_id else None,
            "bbox": [min_lat, min_lon, max_lat, max_lon],
        },
        page=page,
        page_size=page_size,
    )

    if river is not None and river not in ("volga", "oka"):
        logger.warning(
            "request_failed",
            action="get_catch_points",
            service="places-service",
            error="river must be one of: volga, oka",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="river must be one of: volga, oka",
        )

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 500:
        page_size = 200

    skip = (page - 1) * page_size

    catches = await crud_catch_point.get_list(
        db=db,
        river=river,
        fish_type_id=fish_type_id,
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
        skip=skip,
        limit=page_size,
    )

    total = await crud_catch_point.count(
        db=db,
        river=river,
        fish_type_id=fish_type_id,
        min_lat=min_lat,
        min_lon=min_lon,
        max_lat=max_lat,
        max_lon=max_lon,
    )

    logger.info(
        "request_completed",
        action="get_catch_points",
        service="places-service",
        result_count=len(catches),
        total=total,
    )

    return CatchPointListResponse(
        catches=[CatchPointResponse(**c) for c in catches],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/catches/{catch_id}", response_model=CatchPointResponse)
async def get_catch_point(
    catch_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    logger.info(
        "request_started",
        action="get_catch_point",
        service="places-service",
        catch_point_id=str(catch_id),
    )

    catch_point = await crud_catch_point.get(db=db, catch_id=catch_id)

    if not catch_point:
        logger.warning(
            "request_failed",
            action="get_catch_point",
            service="places-service",
            catch_point_id=str(catch_id),
            error="Catch point not found",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catch point not found",
        )

    logger.info(
        "request_completed",
        action="get_catch_point",
        service="places-service",
        catch_point_id=str(catch_id),
    )

    return CatchPointResponse(**catch_point)

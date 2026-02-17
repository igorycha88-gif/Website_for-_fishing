from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.forecast import Region
from app.schemas.forecast import RegionResponse, RegionListResponse

router = APIRouter(prefix="/regions", tags=["regions"])


@router.get("", response_model=RegionListResponse)
async def get_regions(is_active: bool = True, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Region).where(Region.is_active == is_active).order_by(Region.name)
    )
    regions = result.scalars().all()

    return RegionListResponse(
        regions=[RegionResponse.model_validate(r) for r in regions], total=len(regions)
    )


@router.get("/{region_id}", response_model=RegionResponse)
async def get_region(region_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Region).where(Region.id == region_id))
    region = result.scalar_one_or_none()

    if not region:
        raise HTTPException(status_code=404, detail="Region not found")

    return RegionResponse.model_validate(region)

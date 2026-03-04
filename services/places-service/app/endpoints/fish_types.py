from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_redis
from app.core.logging_config import get_logger
from app.schemas.fish_type import FishTypeCreate, FishTypeUpdate, FishTypeResponse
from app.crud import crud_fish_type

logger = get_logger(__name__)
router = APIRouter()


@router.get("/places/fish-types", response_model=List[FishTypeResponse])
async def get_fish_types(
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    logger.info(
        "GET /fish-types",
        service="places-service",
        category=category,
        is_active=is_active,
    )

    fish_types = await crud_fish_type.get_all(
        db=db, category=category, is_active=is_active, skip=skip, limit=limit
    )

    return fish_types


@router.get("/places/fish-types/{fish_type_id}", response_model=FishTypeResponse)
async def get_fish_type(fish_type_id: UUID, db: AsyncSession = Depends(get_db)):
    logger.info(
        "GET /fish-types/{fish_type_id}",
        service="places-service",
        fish_type_id=str(fish_type_id),
    )

    fish_type = await crud_fish_type.get(db=db, fish_type_id=fish_type_id)

    if not fish_type:
        logger.warning(
            "Fish type not found",
            service="places-service",
            fish_type_id=str(fish_type_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fish type not found"
        )

    return fish_type

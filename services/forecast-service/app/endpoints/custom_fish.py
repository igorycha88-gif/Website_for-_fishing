from typing import List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.forecast import UserAddedFish, FishType, FishBiteSettings, Region
from app.schemas.forecast import (
    CustomFishCreate,
    CustomFishResponse,
    CustomFishListResponse,
    FishTypeBrief,
    AllFishTypesResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/forecast", tags=["custom-fish"])

MAX_CUSTOM_FISH_PER_REGION = 3


async def get_current_user_id(authorization: str | None = Header(None)) -> UUID | None:
    if not authorization:
        return None
    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            import httpx

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "http://auth-service:8000/api/v1/users/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return UUID(data["id"])
    except Exception as e:
        logger.warning(
            f"Failed to get user from token: {e}", service="forecast-service"
        )
    return None


@router.get("/{region_id}/custom-fish", response_model=CustomFishListResponse)
async def get_custom_fish(
    region_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID | None = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    result = await db.execute(
        select(Region).where(Region.id == region_id, Region.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Region not found")

    result = await db.execute(
        select(UserAddedFish)
        .where(UserAddedFish.user_id == user_id, UserAddedFish.region_id == region_id)
        .order_by(UserAddedFish.created_at)
    )
    custom_fish = result.scalars().all()

    fish_type_ids = [cf.fish_type_id for cf in custom_fish]
    if fish_type_ids:
        result = await db.execute(
            select(FishType).where(FishType.id.in_(fish_type_ids))
        )
        fish_types = {ft.id: ft for ft in result.scalars().all()}
    else:
        fish_types = {}

    typical_fish_ids = await _get_typical_fish_ids(db, region_id)

    response_fish = []
    for cf in custom_fish:
        ft = fish_types.get(cf.fish_type_id)
        if ft:
            response_fish.append(
                CustomFishResponse(
                    id=cf.id,
                    fish_type=FishTypeBrief(
                        id=ft.id,
                        name=ft.name,
                        icon=ft.icon,
                        category=ft.category,
                        is_typical_for_region=cf.fish_type_id in typical_fish_ids,
                    ),
                    created_at=cf.created_at.isoformat() if cf.created_at else None,
                )
            )

    return CustomFishListResponse(fish_types=response_fish, total=len(response_fish))


@router.post("/{region_id}/custom-fish")
async def add_custom_fish(
    region_id: UUID,
    data: CustomFishCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID | None = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    result = await db.execute(
        select(Region).where(Region.id == region_id, Region.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Region not found")

    result = await db.execute(
        select(FishType).where(
            FishType.id == data.fish_type_id, FishType.is_active == True
        )
    )
    fish_type = result.scalar_one_or_none()
    if not fish_type:
        raise HTTPException(status_code=404, detail="Fish type not found")

    count_result = await db.execute(
        select(func.count())
        .select_from(UserAddedFish)
        .where(UserAddedFish.user_id == user_id, UserAddedFish.region_id == region_id)
    )
    current_count = count_result.scalar() or 0

    if current_count >= MAX_CUSTOM_FISH_PER_REGION:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "LIMIT_EXCEEDED",
                "message": "Максимум 3 дополнительных рыбы для региона",
            },
        )

    existing_result = await db.execute(
        select(UserAddedFish).where(
            UserAddedFish.user_id == user_id,
            UserAddedFish.fish_type_id == data.fish_type_id,
            UserAddedFish.region_id == region_id,
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Fish already added to this region")

    custom_fish = UserAddedFish(
        user_id=user_id,
        fish_type_id=data.fish_type_id,
        region_id=region_id,
    )
    db.add(custom_fish)
    await db.commit()

    logger.info(
        f"Added custom fish for user",
        service="forecast-service",
        user_id=str(user_id),
        fish_type_id=str(data.fish_type_id),
        region_id=str(region_id),
    )

    return {
        "success": True,
        "fish_type": {
            "id": str(fish_type.id),
            "name": fish_type.name,
            "icon": fish_type.icon,
        },
    }


@router.delete("/{region_id}/custom-fish/{fish_type_id}")
async def remove_custom_fish(
    region_id: UUID,
    fish_type_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID | None = Depends(get_current_user_id),
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    result = await db.execute(
        select(UserAddedFish).where(
            UserAddedFish.user_id == user_id,
            UserAddedFish.fish_type_id == fish_type_id,
            UserAddedFish.region_id == region_id,
        )
    )
    custom_fish = result.scalar_one_or_none()

    if not custom_fish:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Рыба не найдена в вашем списке"},
        )

    await db.delete(custom_fish)
    await db.commit()

    logger.info(
        f"Removed custom fish for user",
        service="forecast-service",
        user_id=str(user_id),
        fish_type_id=str(fish_type_id),
        region_id=str(region_id),
    )

    return {"success": True}


@router.get("/{region_id}/all-fish-types", response_model=AllFishTypesResponse)
async def get_all_fish_types(
    region_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID | None = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Region).where(Region.id == region_id, Region.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Region not found")

    result = await db.execute(
        select(FishType).where(FishType.is_active == True).order_by(FishType.name)
    )
    all_fish_types = result.scalars().all()

    typical_fish_ids = await _get_typical_fish_ids(db, region_id)

    custom_fish_ids = set()
    if user_id:
        result = await db.execute(
            select(UserAddedFish.fish_type_id).where(
                UserAddedFish.user_id == user_id, UserAddedFish.region_id == region_id
            )
        )
        custom_fish_ids = {row[0] for row in result.fetchall()}

    response_fish = []
    for ft in all_fish_types:
        response_fish.append(
            FishTypeBrief(
                id=ft.id,
                name=ft.name,
                icon=ft.icon,
                category=ft.category,
                is_typical_for_region=ft.id in typical_fish_ids,
            )
        )

    return AllFishTypesResponse(fish_types=response_fish, total=len(response_fish))


async def _get_typical_fish_ids(db: AsyncSession, region_id: UUID) -> set:
    result = await db.execute(select(FishBiteSettings))
    settings = result.scalars().all()

    typical_ids = set()
    for s in settings:
        if s.region_ids and region_id in s.region_ids:
            typical_ids.add(s.fish_type_id)

    return typical_ids


async def get_user_custom_fish(
    db: AsyncSession, user_id: UUID | None, region_id: UUID
) -> List[UUID]:
    if not user_id:
        return []

    result = await db.execute(
        select(UserAddedFish.fish_type_id).where(
            UserAddedFish.user_id == user_id, UserAddedFish.region_id == region_id
        )
    )
    return [row[0] for row in result.fetchall()]

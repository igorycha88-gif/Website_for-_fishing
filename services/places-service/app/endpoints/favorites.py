from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_redis
from app.core.logging_config import get_logger
from app.schemas.place import PlaceResponse, PlaceListResponse
from app.crud import crud_favorite_place, crud_place
from app.endpoints.places import get_current_user_id

logger = get_logger(__name__)
router = APIRouter()


@router.post("/places/favorites/{place_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    place_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "POST /places/favorites/{place_id}",
        service="places-service",
        place_id=str(place_id),
        user_id=str(current_user_id),
    )

    place = await crud_place.get(db=db, place_id=place_id)

    if not place:
        logger.warning(
            "Place not found", service="places-service", place_id=str(place_id)
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
        )

    is_already_favorite = await crud_favorite_place.is_favorite(
        db=db, user_id=current_user_id, place_id=place_id
    )

    if is_already_favorite:
        logger.warning(
            "Place already in favorites",
            service="places-service",
            place_id=str(place_id),
            user_id=str(current_user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Place already in favorites"
        )

    await crud_favorite_place.create(db=db, user_id=current_user_id, place_id=place_id)

    return {"message": "Place added to favorites"}


@router.delete("/places/favorites/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    place_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "DELETE /places/favorites/{place_id}",
        service="places-service",
        place_id=str(place_id),
        user_id=str(current_user_id),
    )

    success = await crud_favorite_place.delete(
        db=db, user_id=current_user_id, place_id=place_id
    )

    if not success:
        logger.warning(
            "Favorite place not found",
            service="places-service",
            place_id=str(place_id),
            user_id=str(current_user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Favorite place not found"
        )

    return None


@router.get("/places/favorites", response_model=PlaceListResponse)
async def get_favorites(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "GET /places/favorites",
        service="places-service",
        user_id=str(current_user_id),
        page=page,
        page_size=page_size,
    )

    skip = (page - 1) * page_size

    favorite_places = await crud_favorite_place.get_by_user(
        db=db, user_id=current_user_id, skip=skip, limit=page_size
    )

    places = [fp.place for fp in favorite_places if fp.place is not None]

    total = len(
        await crud_favorite_place.get_by_user(
            db=db, user_id=current_user_id, skip=0, limit=999999
        )
    )

    return PlaceListResponse(places=places, total=total, page=page, page_size=page_size)

from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, get_redis
from app.core.logging_config import get_logger
from app.schemas.place import (
    PlaceCreate,
    PlaceUpdate,
    PlaceResponse,
    PlaceListResponse,
    FishTypeInPlace,
)
from app.crud import crud_place, crud_favorite_place
from app.schemas.fish_type import FishTypeResponse
from app.crud import crud_fish_type
from app.models.fish_type import FishType

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


async def _enrich_place_with_fish_types(
    db: AsyncSession, place: Any, is_favorite: bool = False
) -> Dict[str, Any]:
    fish_type_ids = place.fish_types or []
    fish_types_data = []

    if fish_type_ids:
        result = await db.execute(
            select(FishType).where(FishType.id.in_(fish_type_ids))
        )
        fish_types_models = result.scalars().all()
        fish_types_data = [
            FishTypeInPlace(id=ft.id, name=ft.name, icon=ft.icon, category=ft.category)
            for ft in fish_types_models
        ]

    return {
        "id": place.id,
        "owner_id": place.owner_id,
        "name": place.name,
        "description": place.description,
        "latitude": float(place.latitude),
        "longitude": float(place.longitude),
        "address": place.address,
        "place_type": place.place_type,
        "access_type": place.access_type,
        "water_type": place.water_type,
        "fish_types": fish_types_data,
        "seasonality": place.seasonality,
        "visibility": place.visibility,
        "images": place.images,
        "rating_avg": float(place.rating_avg) if place.rating_avg else 0.0,
        "reviews_count": place.reviews_count or 0,
        "is_active": place.is_active,
        "created_at": place.created_at,
        "updated_at": place.updated_at,
        "is_favorite": is_favorite,
    }


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        import jwt
        from app.core.config import settings

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub")

        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return UUID(user_id_str)

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


@router.post(
    "/places/my", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED
)
async def create_place(
    place_in: PlaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "POST /places/my",
        service="places-service",
        place_name=place_in.name,
        user_id=str(current_user_id),
        fish_types=[str(ft) for ft in place_in.fish_types],
    )

    try:
        place = await crud_place.create(
            db=db, place_in=place_in, user_id=current_user_id
        )
        enriched_place = await _enrich_place_with_fish_types(db, place)
        return PlaceResponse(**enriched_place)
    except ValueError as e:
        logger.warning(
            "Validation error creating place",
            service="places-service",
            place_name=place_in.name,
            user_id=str(current_user_id),
            error=str(e),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Unexpected error creating place",
            service="places-service",
            place_name=place_in.name,
            user_id=str(current_user_id),
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error. Please try again later.",
        )


@router.get("/places/my", response_model=PlaceListResponse)
async def get_places(
    visibility: Optional[str] = None,
    place_type: Optional[str] = None,
    access_type: Optional[str] = None,
    fish_type_id: Optional[UUID] = None,
    seasonality: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort: str = "created_at",
    order: str = "desc",
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "GET /places/my",
        service="places-service",
        user_id=str(current_user_id),
        filters={
            "visibility": visibility,
            "place_type": place_type,
            "access_type": access_type,
            "fish_type_id": str(fish_type_id) if fish_type_id else None,
            "seasonality": seasonality,
            "search": search,
        },
        page=page,
        page_size=page_size,
    )

    skip = (page - 1) * page_size

    places = await crud_place.get_by_user(
        db=db,
        user_id=current_user_id,
        visibility=visibility,
        place_type=place_type,
        access_type=access_type,
        fish_type_id=fish_type_id,
        seasonality=seasonality,
        search=search,
        skip=skip,
        limit=page_size,
        sort_by=sort,
        order=order,
    )

    total = await crud_place.count_by_user(
        db=db,
        user_id=current_user_id,
        visibility=visibility,
        place_type=place_type,
        access_type=access_type,
        fish_type_id=fish_type_id,
        seasonality=seasonality,
        search=search,
    )

    enriched_places = []
    for place in places:
        enriched = await _enrich_place_with_fish_types(db, place)
        enriched_places.append(PlaceResponse(**enriched))

    return PlaceListResponse(
        places=enriched_places, total=total, page=page, page_size=page_size
    )


@router.get("/places/my/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "GET /places/my/{place_id}",
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

    if place.owner_id != current_user_id:
        logger.warning(
            "User not authorized to view place",
            service="places-service",
            place_id=str(place_id),
            user_id=str(current_user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this place",
        )

    is_favorite = await crud_favorite_place.is_favorite(
        db=db, user_id=current_user_id, place_id=place_id
    )

    enriched_place = await _enrich_place_with_fish_types(db, place, is_favorite)
    return PlaceResponse(**enriched_place)


@router.put("/places/my/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: UUID,
    place_in: PlaceUpdate,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "PUT /places/my/{place_id}",
        service="places-service",
        place_id=str(place_id),
        user_id=str(current_user_id),
        place_data=place_in.model_dump(),
    )

    place = await crud_place.update(
        db=db, place_id=place_id, place_in=place_in, user_id=current_user_id
    )

    if not place:
        logger.warning(
            "Place not found or not authorized",
            service="places-service",
            place_id=str(place_id),
            user_id=str(current_user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found or you don't have permission to update it",
        )

    enriched_place = await _enrich_place_with_fish_types(db, place)
    return PlaceResponse(**enriched_place)


@router.delete("/places/my/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    place_id: UUID,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
    current_user_id: UUID = Depends(get_current_user_id),
):
    logger.info(
        "DELETE /places/my/{place_id}",
        service="places-service",
        place_id=str(place_id),
        user_id=str(current_user_id),
    )

    success = await crud_place.delete(db=db, place_id=place_id, user_id=current_user_id)

    if not success:
        logger.warning(
            "Place not found or not authorized",
            service="places-service",
            place_id=str(place_id),
            user_id=str(current_user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found or you don't have permission to delete it",
        )

    return None

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.security import get_current_user_id, require_role
from app.crud.place import PlaceCRUD
from app.schemas.place import (
    PlaceCreate,
    PlaceUpdate,
    PlaceResponse,
    PlaceWithOwnerResponse,
    PlaceListResponse,
    ModerationRequest,
    PlaceStatisticsResponse,
    FishTypeResponse,
    FacilityResponse,
    MessageResponse,
    ReverseGeocodeRequest,
    ReverseGeocodeResponse,
)
from app.core.constants import FISH_TYPES, FACILITIES
from app.services.yandex_geocoder import yandex_geocoder

router = APIRouter()


@router.post("/places", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
async def create_place(
    place_data: PlaceCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    crud = PlaceCRUD(db)
    try:
        place = await crud.create(user_id, place_data)
        return PlaceResponse.model_validate(place)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to create place"
            }
        )


@router.get("/places/fish-types", response_model=List[FishTypeResponse])
async def get_fish_types():
    return [
        FishTypeResponse(**fish_type)
        for fish_type in FISH_TYPES
    ]


@router.get("/places/facilities", response_model=List[FacilityResponse])
async def get_facilities():
    return [
        FacilityResponse(**facility)
        for facility in FACILITIES
    ]


@router.post("/places/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode(request: ReverseGeocodeRequest):
    result = await yandex_geocoder.reverse_geocode_detailed(request.latitude, request.longitude)
    
    if not result:
        return ReverseGeocodeResponse(address=None, city=None, region=None, country=None)
    
    return ReverseGeocodeResponse(**result)


@router.get("/places", response_model=PlaceListResponse)
async def get_places(
    owner_id: Optional[str] = Query(None, description="Filter by owner ID or 'me'"),
    is_public: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None, description="Format: min_lat,min_lng,max_lat,max_lng"),
    fish_types: Optional[str] = Query(None, description="Comma-separated list"),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lng: Optional[float] = Query(None, ge=-180, le=180),
    radius: Optional[float] = Query(None, ge=1, le=500),
    facilities: Optional[str] = Query(None, description="Comma-separated list"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    crud = PlaceCRUD(db)

    if owner_id == "me":
        owner_id = user_id

    bbox_coords = None
    if bbox:
        try:
            bbox_coords = tuple(map(float, bbox.split(",")))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_BBOX",
                    "message": "Invalid bbox format. Use: min_lat,min_lng,max_lat,max_lng"
                }
            )

    fish_types_list = None
    if fish_types:
        fish_types_list = fish_types.split(",")

    facilities_list = None
    if facilities:
        facilities_list = facilities.split(",")

    places, total = await crud.get_many(
        owner_id=owner_id,
        is_public=is_public,
        status=status,
        bbox=bbox_coords,
        fish_types=fish_types_list,
        min_rating=min_rating,
        center_lat=lat,
        center_lng=lng,
        radius=radius,
        facilities=facilities_list,
        page=page,
        limit=limit,
        sort=sort,
        order=order
    )

    return PlaceListResponse(
        items=[PlaceResponse.model_validate(p) for p in places],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/places/{place_id}", response_model=PlaceWithOwnerResponse)
async def get_place(
    place_id: str,
    db: AsyncSession = Depends(get_db)
):
    crud = PlaceCRUD(db)
    place = await crud.get_by_id(place_id)

    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PLACE_NOT_FOUND",
                "message": f"Place with id '{place_id}' not found"
            }
        )

    return PlaceWithOwnerResponse.model_validate(place)


@router.put("/places/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: str,
    place_data: PlaceUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    crud = PlaceCRUD(db)
    place = await crud.get_by_id(place_id)

    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PLACE_NOT_FOUND",
                "message": f"Place with id '{place_id}' not found"
            }
        )

    if str(place.owner_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You can only edit your own places"
            }
        )

    try:
        updated_place = await crud.update(place_id, place_data)
        return PlaceResponse.model_validate(updated_place)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Failed to update place"
            }
        )


@router.delete("/places/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    place_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    crud = PlaceCRUD(db)
    place = await crud.get_by_id(place_id)

    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PLACE_NOT_FOUND",
                "message": f"Place with id '{place_id}' not found"
            }
        )

    if str(place.owner_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You can only delete your own places"
            }
        )

    await crud.delete(place_id)
    return None


@router.get("/places/nearby", response_model=List[PlaceResponse])
async def get_nearby_places(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(50, ge=1, le=500),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    crud = PlaceCRUD(db)
    places = await crud.get_nearby(lat, lng, radius, limit)
    return [PlaceResponse.model_validate(p) for p in places]


@router.post("/places/{place_id}/moderate", response_model=PlaceResponse)
async def moderate_place(
    place_id: str,
    moderation_data: ModerationRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    is_admin = await require_role(user_id, ["admin", "moderator"])
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Only admins and moderators can moderate places"
            }
        )

    crud = PlaceCRUD(db)
    place = await crud.get_by_id(place_id)

    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PLACE_NOT_FOUND",
                "message": f"Place with id '{place_id}' not found"
            }
        )

    updated_place = await crud.moderate(
        place_id,
        moderation_data.action,
        moderation_data.reason
    )

    return PlaceResponse.model_validate(updated_place)


@router.get("/places/{place_id}/statistics", response_model=PlaceStatisticsResponse)
async def get_place_statistics(
    place_id: str,
    db: AsyncSession = Depends(get_db)
):
    crud = PlaceCRUD(db)
    place = await crud.get_by_id(place_id)

    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PLACE_NOT_FOUND",
                "message": f"Place with id '{place_id}' not found"
            }
        )

    statistics = await crud.get_statistics(place_id)
    return PlaceStatisticsResponse(**statistics)



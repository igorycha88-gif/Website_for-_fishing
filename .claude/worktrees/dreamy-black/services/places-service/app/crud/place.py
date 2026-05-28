from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import ARRAY
from decimal import Decimal
import math

from app.models.place import Place
from app.schemas.place import PlaceCreate, PlaceUpdate
from app.core.constants import FORBIDDEN_WORDS


class PlaceCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _check_forbidden_words(self, text: str) -> bool:
        text_lower = text.lower()
        return any(word in text_lower for word in FORBIDDEN_WORDS)

    async def create(
        self,
        owner_id: str,
        place_data: PlaceCreate
    ) -> Place:
        if self._check_forbidden_words(place_data.title):
            raise ValueError("Title contains forbidden words")
        if self._check_forbidden_words(place_data.description):
            raise ValueError("Description contains forbidden words")

        status = "active"
        if place_data.is_public:
            status = "pending_moderation"

        place = Place(
            owner_id=owner_id,
            title=place_data.title,
            description=place_data.description,
            latitude=place_data.latitude,
            longitude=place_data.longitude,
            address=place_data.address,
            city=place_data.city,
            region=place_data.region,
            price_per_day=place_data.price_per_day,
            max_people=place_data.max_people,
            facilities=place_data.facilities,
            fish_types=place_data.fish_types,
            images=place_data.images or [],
            is_public=place_data.is_public,
            status=status,
            visit_date=place_data.visit_date,
            place_type=place_data.place_type or "wild_place",
            seasonality=place_data.seasonality,
            water_depth=place_data.water_depth,
            water_type=place_data.water_type,
            access_type=place_data.access_type,
            fishing_permission=place_data.fishing_permission,
        )

        self.db.add(place)
        await self.db.commit()
        await self.db.refresh(place)
        return place

    async def get_by_id(self, place_id: str) -> Optional[Place]:
        result = await self.db.execute(
            select(Place).where(Place.id == place_id)
        )
        return result.scalar_one_or_none()

    async def get_many(
        self,
        owner_id: Optional[str] = None,
        is_public: Optional[bool] = None,
        status: Optional[str] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        fish_types: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        radius: Optional[float] = None,
        facilities: Optional[List[str]] = None,
        place_type: Optional[str] = None,
        water_type: Optional[str] = None,
        access_type: Optional[str] = None,
        fishing_permission: Optional[str] = None,
        page: int =1,
        limit: int = 20,
        sort: str = "created_at",
        order: str = "desc"
    ) -> Tuple[List[Place], int]:
        query = select(Place).where(Place.is_active == True)

        if owner_id:
            if owner_id == "me":
                pass
            else:
                query = query.where(Place.owner_id == owner_id)

        if is_public is not None:
            query = query.where(Place.is_public == is_public)

        if status:
            query = query.where(Place.status == status)

        if bbox:
            min_lat, min_lng, max_lat, max_lng = bbox
            query = query.where(
                and_(
                    Place.latitude >= min_lat,
                    Place.latitude <= max_lat,
                    Place.longitude >= min_lng,
                    Place.longitude <= max_lng
                )
            )

        if fish_types:
            fish_conditions = [Place.fish_types.op('?')(ft) for ft in fish_types]
            query = query.where(or_(*fish_conditions))

        if min_rating is not None:
            query = query.where(Place.rating_avg >= min_rating)

        if center_lat is not None and center_lng is not None and radius is not None:
            radius_deg = radius / 111.0
            query = query.where(
                and_(
                    Place.latitude >= center_lat - radius_deg,
                    Place.latitude <= center_lat + radius_deg,
                    Place.longitude >= center_lng - radius_deg,
                    Place.longitude <= center_lng + radius_deg
                )
            )

        if facilities:
            for facility in facilities:
                query = query.where(Place.facilities.op('?')(facility))

        if place_type:
            query = query.where(Place.place_type == place_type)

        if water_type:
            query = query.where(Place.water_type == water_type)

        if access_type:
            query = query.where(Place.access_type == access_type)

        if fishing_permission:
            query = query.where(Place.fishing_permission == fishing_permission)

        total_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        order_column = getattr(Place, sort, Place.created_at)
        if order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        places = result.scalars().all()

        return list(places), total

    async def update(
        self,
        place_id: str,
        place_data: PlaceUpdate
    ) -> Optional[Place]:
        place = await self.get_by_id(place_id)
        if not place:
            return None

        update_data = place_data.model_dump(exclude_unset=True)

        if place_data.is_public is not None and place_data.is_public != place.is_public:
            update_data["status"] = "pending_moderation"

        for field, value in update_data.items():
            setattr(place, field, value)

        await self.db.commit()
        await self.db.refresh(place)
        return place

    async def delete(self, place_id: str) -> bool:
        place = await self.get_by_id(place_id)
        if not place:
            return False

        await self.db.delete(place)
        await self.db.commit()
        return True

    async def get_nearby(
        self,
        lat: float,
        lng: float,
        radius: float = 50,
        limit: int = 20
    ) -> List[Place]:
        radius_deg = radius / 111.0

        query = select(Place).where(
            and_(
                Place.is_active == True,
                Place.latitude >= lat - radius_deg,
                Place.latitude <= lat + radius_deg,
                Place.longitude >= lng - radius_deg,
                Place.longitude <= lng + radius_deg
            )
        ).limit(limit)

        result = await self.db.execute(query)
        places = result.scalars().all()
        return list(places)

    async def moderate(
        self,
        place_id: str,
        action: str,
        reason: Optional[str] = None
    ) -> Optional[Place]:
        place = await self.get_by_id(place_id)
        if not place:
            return None

        if action == "approve":
            setattr(place, "status", "active")
        elif action == "reject":
            setattr(place, "status", str(reason or ""))

        self.db.add(place)
        await self.db.commit()
        await self.db.refresh(place)
        return place

    async def get_by_owner(
        self,
        owner_id: str,
        include_private: bool = True,
        include_public: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Place], int]:
        query = select(Place).where(Place.owner_id == owner_id)

        if not include_private:
            query = query.where(Place.is_public == True)
        if not include_public:
            query = query.where(Place.is_public == False)

        total_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        query = query.order_by(Place.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        places = result.scalars().all()

        return list(places), total

    async def get_statistics(self, place_id: str) -> Optional[dict]:
        return {
            "reports_count": 0,
            "avg_rating": 0.0,
            "top_fish": [],
            "seasonality": {},
            "last_report": None
        }

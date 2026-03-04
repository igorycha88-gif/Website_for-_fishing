from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.models.place import Place
from app.models.fish_type import FishType
from app.schemas.place import PlaceCreate, PlaceUpdate, FishTypeInPlace
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CRUDPlace:
    async def _get_fish_types_by_ids(
        self, db: AsyncSession, fish_type_ids: List[UUID]
    ) -> List[FishTypeInPlace]:
        if not fish_type_ids:
            return []

        result = await db.execute(
            select(FishType).where(FishType.id.in_(fish_type_ids))
        )
        fish_types = result.scalars().all()
        return [
            FishTypeInPlace(id=ft.id, name=ft.name, icon=ft.icon, category=ft.category)
            for ft in fish_types
        ]

    async def _enrich_place_with_fish_types(
        self, db: AsyncSession, place: Place
    ) -> Dict[str, Any]:
        fish_types = await self._get_fish_types_by_ids(db, place.fish_types or [])
        place_dict = {
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
            "fish_types": fish_types,
            "seasonality": place.seasonality,
            "visibility": place.visibility,
            "images": place.images,
            "rating_avg": float(place.rating_avg) if place.rating_avg else 0.0,
            "reviews_count": place.reviews_count or 0,
            "is_active": place.is_active,
            "created_at": place.created_at,
            "updated_at": place.updated_at,
            "is_favorite": False,
        }
        return place_dict

    async def _enrich_places_with_fish_types(
        self, db: AsyncSession, places: List[Place]
    ) -> List[Dict[str, Any]]:
        result = []
        for place in places:
            enriched = await self._enrich_place_with_fish_types(db, place)
            result.append(enriched)
        return result

    async def _validate_fish_types(
        self, db: AsyncSession, fish_type_ids: List[UUID]
    ) -> None:
        for fish_type_id in fish_type_ids:
            result = await db.execute(
                select(FishType).where(FishType.id == fish_type_id)
            )
            fish_type = result.scalar_one_or_none()
            if not fish_type:
                logger.warning(
                    "Fish type not found",
                    service="places-service",
                    fish_type_id=str(fish_type_id),
                )
                raise ValueError(f"Fish type with id {fish_type_id} not found")

    async def create(
        self, db: AsyncSession, place_in: PlaceCreate, user_id: UUID
    ) -> Place:
        logger.info(
            "Creating place",
            service=settings.SERVICE_NAME,
            place_name=place_in.name,
            user_id=str(user_id),
            fish_types=[str(ft) for ft in place_in.fish_types],
        )

        try:
            await self._validate_fish_types(db, place_in.fish_types)
            place_dict = place_in.model_dump()
            place_dict["owner_id"] = user_id
            place_dict["latitude"] = float(place_dict["latitude"])
            place_dict["longitude"] = float(place_dict["longitude"])

            db_place = Place(**place_dict)
            db.add(db_place)
            await db.commit()
            await db.refresh(db_place)

            logger.info(
                "Place created successfully",
                service=settings.SERVICE_NAME,
                place_id=str(db_place.id),
                place_name=db_place.name,
            )

            return db_place

        except Exception as e:
            logger.error(
                "Error creating place",
                service=settings.SERVICE_NAME,
                place_name=place_in.name,
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def get(self, db: AsyncSession, place_id: UUID) -> Optional[Place]:
        logger.debug(
            "Getting place by ID", service=settings.SERVICE_NAME, place_id=str(place_id)
        )

        try:
            result = await db.execute(select(Place).where(Place.id == place_id))
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                "Error getting place",
                service=settings.SERVICE_NAME,
                place_id=str(place_id),
                error=str(e),
                exc_info=True,
            )
            return None

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        visibility: Optional[str] = None,
        place_type: Optional[str] = None,
        access_type: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        seasonality: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[Place]:
        logger.debug(
            "Getting places by user",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
            filters={
                "visibility": visibility,
                "place_type": place_type,
                "access_type": access_type,
                "fish_type_id": str(fish_type_id) if fish_type_id else None,
                "seasonality": seasonality,
                "search": search,
            },
        )

        try:
            query = select(Place).where(Place.owner_id == user_id)

            if visibility:
                if visibility == "all":
                    pass
                else:
                    query = query.where(Place.visibility == visibility)

            if place_type:
                query = query.where(Place.place_type == place_type)

            if access_type:
                query = query.where(Place.access_type == access_type)

            if fish_type_id:
                query = query.where(Place.fish_types.contains([fish_type_id]))

            if seasonality:
                query = query.where(Place.seasonality.any(seasonality))

            if search:
                search_pattern = f"%{search}%"
                query = query.where(Place.name.ilike(search_pattern))

            if sort_by == "name":
                order_column = Place.name
            else:
                order_column = Place.created_at

            if order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            places = result.scalars().all()

            logger.info(
                "Retrieved places", service=settings.SERVICE_NAME, count=len(places)
            )

            return places

        except Exception as e:
            logger.error(
                "Error getting places",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            return []

    async def count_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        visibility: Optional[str] = None,
        place_type: Optional[str] = None,
        access_type: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        seasonality: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        logger.debug(
            "Counting places by user",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
        )

        try:
            query = (
                select(func.count()).select_from(Place).where(Place.owner_id == user_id)
            )

            if visibility:
                if visibility == "all":
                    pass
                else:
                    query = query.where(Place.visibility == visibility)

            if place_type:
                query = query.where(Place.place_type == place_type)

            if access_type:
                query = query.where(Place.access_type == access_type)

            if fish_type_id:
                query = query.where(Place.fish_types.contains([fish_type_id]))

            if seasonality:
                query = query.where(Place.seasonality.any(seasonality))

            if search:
                search_pattern = f"%{search}%"
                query = query.where(Place.name.ilike(search_pattern))

            result = await db.execute(query)
            count = result.scalar()

            return count or 0

        except Exception as e:
            logger.error(
                "Error counting places",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            return 0

    async def update(
        self, db: AsyncSession, place_id: UUID, place_in: PlaceUpdate, user_id: UUID
    ) -> Optional[Place]:
        logger.info(
            "Updating place",
            service=settings.SERVICE_NAME,
            place_id=str(place_id),
            user_id=str(user_id),
        )

        try:
            db_place = await self.get(db, place_id)
            if not db_place:
                logger.warning(
                    "Place not found for update",
                    service=settings.SERVICE_NAME,
                    place_id=str(place_id),
                )
                return None

            if db_place.owner_id != user_id:
                logger.warning(
                    "User not authorized to update place",
                    service=settings.SERVICE_NAME,
                    place_id=str(place_id),
                    user_id=str(user_id),
                    owner_id=str(db_place.owner_id),
                )
                return None

            update_data = place_in.model_dump(exclude_unset=True)

            if "latitude" in update_data:
                update_data["latitude"] = float(update_data["latitude"])

            if "longitude" in update_data:
                update_data["longitude"] = float(update_data["longitude"])

            for field, value in update_data.items():
                setattr(db_place, field, value)

            await db.commit()
            await db.refresh(db_place)

            logger.info(
                "Place updated successfully",
                service=settings.SERVICE_NAME,
                place_id=str(place_id),
            )

            return db_place

        except Exception as e:
            logger.error(
                "Error updating place",
                service=settings.SERVICE_NAME,
                place_id=str(place_id),
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, place_id: UUID, user_id: UUID) -> bool:
        logger.info(
            "Deleting place",
            service=settings.SERVICE_NAME,
            place_id=str(place_id),
            user_id=str(user_id),
        )

        try:
            db_place = await self.get(db, place_id)
            if not db_place:
                logger.warning(
                    "Place not found for deletion",
                    service=settings.SERVICE_NAME,
                    place_id=str(place_id),
                )
                return False

            if db_place.owner_id != user_id:
                logger.warning(
                    "User not authorized to delete place",
                    service=settings.SERVICE_NAME,
                    place_id=str(place_id),
                    user_id=str(user_id),
                    owner_id=str(db_place.owner_id),
                )
                return False

            await db.delete(db_place)
            await db.commit()

            logger.info(
                "Place deleted successfully",
                service=settings.SERVICE_NAME,
                place_id=str(place_id),
            )

            return True

        except Exception as e:
            logger.error(
                "Error deleting place",
                service=settings.SERVICE_NAME,
                place_id=str(place_id),
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def get_public_places(
        self,
        db: AsyncSession,
        place_type: Optional[str] = None,
        access_type: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        seasonality: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[Place]:
        logger.debug(
            "Getting public places",
            service=settings.SERVICE_NAME,
            filters={
                "place_type": place_type,
                "access_type": access_type,
                "fish_type_id": str(fish_type_id) if fish_type_id else None,
                "seasonality": seasonality,
                "search": search,
            },
        )

        try:
            query = (
                select(Place)
                .where(Place.visibility == "public")
                .where(Place.is_active == True)
            )

            if place_type:
                query = query.where(Place.place_type == place_type)

            if access_type:
                query = query.where(Place.access_type == access_type)

            if fish_type_id:
                query = query.where(Place.fish_types.contains([fish_type_id]))

            if seasonality:
                query = query.where(Place.seasonality.any(seasonality))

            if search:
                search_pattern = f"%{search}%"
                query = query.where(Place.name.ilike(search_pattern))

            if sort_by == "name":
                order_column = Place.name
            else:
                order_column = Place.created_at

            if order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            places = result.scalars().all()

            logger.info(
                "Retrieved public places",
                service=settings.SERVICE_NAME,
                count=len(places),
            )

            return places

        except Exception as e:
            logger.error(
                "Error getting public places",
                service=settings.SERVICE_NAME,
                error=str(e),
                exc_info=True,
            )
            return []

    async def count_public_places(
        self,
        db: AsyncSession,
        place_type: Optional[str] = None,
        access_type: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        seasonality: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        logger.debug(
            "Counting public places",
            service=settings.SERVICE_NAME,
        )

        try:
            query = (
                select(func.count())
                .select_from(Place)
                .where(Place.visibility == "public")
                .where(Place.is_active == True)
            )

            if place_type:
                query = query.where(Place.place_type == place_type)

            if access_type:
                query = query.where(Place.access_type == access_type)

            if fish_type_id:
                query = query.where(Place.fish_types.contains([fish_type_id]))

            if seasonality:
                query = query.where(Place.seasonality.any(seasonality))

            if search:
                search_pattern = f"%{search}%"
                query = query.where(Place.name.ilike(search_pattern))

            result = await db.execute(query)
            count = result.scalar()

            return count or 0

        except Exception as e:
            logger.error(
                "Error counting public places",
                service=settings.SERVICE_NAME,
                error=str(e),
                exc_info=True,
            )
            return 0

    async def get_public_and_user_places(
        self,
        db: AsyncSession,
        user_id: UUID,
        place_type: Optional[str] = None,
        access_type: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        seasonality: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[Place]:
        logger.debug(
            "Getting public and user places",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
            filters={
                "place_type": place_type,
                "access_type": access_type,
                "fish_type_id": str(fish_type_id) if fish_type_id else None,
                "seasonality": seasonality,
                "search": search,
            },
        )

        try:
            query = (
                select(Place)
                .where(or_(Place.visibility == "public", Place.owner_id == user_id))
                .where(Place.is_active == True)
            )

            if place_type:
                query = query.where(Place.place_type == place_type)

            if access_type:
                query = query.where(Place.access_type == access_type)

            if fish_type_id:
                query = query.where(Place.fish_types.contains([fish_type_id]))

            if seasonality:
                query = query.where(Place.seasonality.any(seasonality))

            if search:
                search_pattern = f"%{search}%"
                query = query.where(Place.name.ilike(search_pattern))

            if sort_by == "name":
                order_column = Place.name
            else:
                order_column = Place.created_at

            if order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            places = result.scalars().all()

            logger.info(
                "Retrieved public and user places",
                service=settings.SERVICE_NAME,
                count=len(places),
            )

            return places

        except Exception as e:
            logger.error(
                "Error getting public and user places",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            return []

    async def count_public_and_user_places(
        self,
        db: AsyncSession,
        user_id: UUID,
        place_type: Optional[str] = None,
        access_type: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        seasonality: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        logger.debug(
            "Counting public and user places",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
        )

        try:
            query = (
                select(func.count())
                .select_from(Place)
                .where(or_(Place.visibility == "public", Place.owner_id == user_id))
                .where(Place.is_active == True)
            )

            if place_type:
                query = query.where(Place.place_type == place_type)

            if access_type:
                query = query.where(Place.access_type == access_type)

            if fish_type_id:
                query = query.where(Place.fish_types.contains([fish_type_id]))

            if seasonality:
                query = query.where(Place.seasonality.any(seasonality))

            if search:
                search_pattern = f"%{search}%"
                query = query.where(Place.name.ilike(search_pattern))

            result = await db.execute(query)
            count = result.scalar()

            return count or 0

        except Exception as e:
            logger.error(
                "Error counting public and user places",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            return 0


crud_place = CRUDPlace()

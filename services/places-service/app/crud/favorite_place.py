from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.favorite_place import FavoritePlace
from app.models.place import Place
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CRUDFavoritePlace:
    async def create(
        self, db: AsyncSession, user_id: UUID, place_id: UUID
    ) -> Optional[FavoritePlace]:
        logger.info(
            "Creating favorite place",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
            place_id=str(place_id),
        )

        try:
            db_favorite = FavoritePlace(user_id=user_id, place_id=place_id)
            db.add(db_favorite)
            await db.commit()
            await db.refresh(db_favorite)

            logger.info(
                "Favorite place created successfully",
                service=settings.SERVICE_NAME,
                favorite_id=str(db_favorite.id),
            )

            return db_favorite

        except Exception as e:
            logger.error(
                "Error creating favorite place",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                place_id=str(place_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, user_id: UUID, place_id: UUID) -> bool:
        logger.info(
            "Deleting favorite place",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
            place_id=str(place_id),
        )

        try:
            result = await db.execute(
                select(FavoritePlace).where(
                    and_(
                        FavoritePlace.user_id == user_id,
                        FavoritePlace.place_id == place_id,
                    )
                )
            )
            db_favorite = result.scalar_one_or_none()

            if not db_favorite:
                logger.warning(
                    "Favorite place not found",
                    service=settings.SERVICE_NAME,
                    user_id=str(user_id),
                    place_id=str(place_id),
                )
                return False

            await db.delete(db_favorite)
            await db.commit()

            logger.info(
                "Favorite place deleted successfully",
                service=settings.SERVICE_NAME,
                favorite_id=str(db_favorite.id),
            )

            return True

        except Exception as e:
            logger.error(
                "Error deleting favorite place",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                place_id=str(place_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def get_by_user(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> List[FavoritePlace]:
        logger.debug(
            "Getting favorite places by user",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
        )

        try:
            result = await db.execute(
                select(FavoritePlace)
                .where(FavoritePlace.user_id == user_id)
                .options(selectinload(FavoritePlace.place))
                .order_by(FavoritePlace.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()

        except Exception as e:
            logger.error(
                "Error getting favorite places",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                error=str(e),
                exc_info=True,
            )
            return []

    async def is_favorite(
        self, db: AsyncSession, user_id: UUID, place_id: UUID
    ) -> bool:
        logger.debug(
            "Checking if place is favorite",
            service=settings.SERVICE_NAME,
            user_id=str(user_id),
            place_id=str(place_id),
        )

        try:
            result = await db.execute(
                select(FavoritePlace).where(
                    and_(
                        FavoritePlace.user_id == user_id,
                        FavoritePlace.place_id == place_id,
                    )
                )
            )
            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(
                "Error checking favorite place",
                service=settings.SERVICE_NAME,
                user_id=str(user_id),
                place_id=str(place_id),
                error=str(e),
                exc_info=True,
            )
            return False


crud_favorite_place = CRUDFavoritePlace()

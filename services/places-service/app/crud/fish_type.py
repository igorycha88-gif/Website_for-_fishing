from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import json

from app.models.fish_type import FishType
from app.schemas.fish_type import FishTypeCreate, FishTypeUpdate
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CRUDFishType:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.cache_ttl = 3600

    async def create(self, db: AsyncSession, fish_type_in: FishTypeCreate) -> FishType:
        logger.info(
            "Creating fish type",
            service=settings.SERVICE_NAME,
            fish_type_name=fish_type_in.name,
        )

        try:
            db_fish_type = FishType(**fish_type_in.model_dump())
            db.add(db_fish_type)
            await db.commit()
            await db.refresh(db_fish_type)

            logger.info(
                "Fish type created successfully",
                service=settings.SERVICE_NAME,
                fish_type_id=str(db_fish_type.id),
                fish_type_name=db_fish_type.name,
            )

            await self._invalidate_cache()
            return db_fish_type

        except Exception as e:
            logger.error(
                "Error creating fish type",
                service=settings.SERVICE_NAME,
                fish_type_name=fish_type_in.name,
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def get(self, db: AsyncSession, fish_type_id: UUID) -> Optional[FishType]:
        logger.debug(
            "Getting fish type by ID",
            service=settings.SERVICE_NAME,
            fish_type_id=str(fish_type_id),
        )

        result = await db.execute(select(FishType).where(FishType.id == fish_type_id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FishType]:
        logger.debug(
            "Getting all fish types",
            service=settings.SERVICE_NAME,
            category=category,
            is_active=is_active,
        )

        cache_key = (
            f"fish_types:{category or 'all'}:{is_active or 'all'}:{skip}:{limit}"
        )

        try:
            cached = await self._get_from_cache(cache_key)
            if cached:
                logger.info(
                    "Cache hit for fish types",
                    service=settings.SERVICE_NAME,
                    cache_key=cache_key,
                )
                return [FishType(**ft) for ft in cached]
        except Exception as e:
            logger.warning(
                "Error reading from cache",
                service=settings.SERVICE_NAME,
                cache_key=cache_key,
                error=str(e),
            )

        try:
            query = select(FishType)

            if category:
                query = query.where(FishType.category == category)
            if is_active is not None:
                query = query.where(FishType.is_active == is_active)

            query = query.offset(skip).limit(limit)
            query = query.order_by(FishType.name)

            result = await db.execute(query)
            fish_types = result.scalars().all()

            try:
                fish_types_dict = [self._fish_type_to_dict(ft) for ft in fish_types]
                await self._save_to_cache(cache_key, fish_types_dict)
                logger.info(
                    "Cached fish types",
                    service=settings.SERVICE_NAME,
                    cache_key=cache_key,
                    count=len(fish_types),
                )
            except Exception as e:
                logger.warning(
                    "Error caching fish types",
                    service=settings.SERVICE_NAME,
                    cache_key=cache_key,
                    error=str(e),
                )

            return fish_types

        except Exception as e:
            logger.error(
                "Error getting fish types from database",
                service=settings.SERVICE_NAME,
                error=str(e),
                exc_info=True,
            )
            return []

    async def update(
        self, db: AsyncSession, fish_type_id: UUID, fish_type_in: FishTypeUpdate
    ) -> Optional[FishType]:
        logger.info(
            "Updating fish type",
            service=settings.SERVICE_NAME,
            fish_type_id=str(fish_type_id),
        )

        try:
            db_fish_type = await self.get(db, fish_type_id)
            if not db_fish_type:
                logger.warning(
                    "Fish type not found for update",
                    service=settings.SERVICE_NAME,
                    fish_type_id=str(fish_type_id),
                )
                return None

            update_data = fish_type_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_fish_type, field, value)

            await db.commit()
            await db.refresh(db_fish_type)

            logger.info(
                "Fish type updated successfully",
                service=settings.SERVICE_NAME,
                fish_type_id=str(fish_type_id),
                fish_type_name=db_fish_type.name,
            )

            await self._invalidate_cache()
            return db_fish_type

        except Exception as e:
            logger.error(
                "Error updating fish type",
                service=settings.SERVICE_NAME,
                fish_type_id=str(fish_type_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, fish_type_id: UUID) -> bool:
        logger.info(
            "Deleting fish type",
            service=settings.SERVICE_NAME,
            fish_type_id=str(fish_type_id),
        )

        try:
            db_fish_type = await self.get(db, fish_type_id)
            if not db_fish_type:
                logger.warning(
                    "Fish type not found for deletion",
                    service=settings.SERVICE_NAME,
                    fish_type_id=str(fish_type_id),
                )
                return False

            await db.delete(db_fish_type)
            await db.commit()

            logger.info(
                "Fish type deleted successfully",
                service=settings.SERVICE_NAME,
                fish_type_id=str(fish_type_id),
                fish_type_name=db_fish_type.name,
            )

            await self._invalidate_cache()
            return True

        except Exception as e:
            logger.error(
                "Error deleting fish type",
                service=settings.SERVICE_NAME,
                fish_type_id=str(fish_type_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    def _fish_type_to_dict(self, fish_type: FishType) -> dict:
        return {
            "id": str(fish_type.id),
            "name": fish_type.name,
            "icon": fish_type.icon,
            "category": fish_type.category,
            "is_active": fish_type.is_active,
            "created_at": fish_type.created_at.isoformat()
            if fish_type.created_at
            else None,
            "updated_at": fish_type.updated_at.isoformat()
            if fish_type.updated_at
            else None,
        }

    async def _get_from_cache(self, key: str) -> Optional[List[dict]]:
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(
                "Error reading from cache",
                service=settings.SERVICE_NAME,
                key=key,
                error=str(e),
            )

        return None

    async def _save_to_cache(self, key: str, data: List[dict]):
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(key, self.cache_ttl, json.dumps(data))
        except Exception as e:
            logger.error(
                "Error saving to cache",
                service=settings.SERVICE_NAME,
                key=key,
                error=str(e),
            )

    async def _invalidate_cache(self):
        if not self.redis_client:
            return

        try:
            pattern = "fish_types:*"
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)
                logger.info(
                    "Cache invalidated for fish types",
                    service=settings.SERVICE_NAME,
                    keys_deleted=len(keys),
                )
        except Exception as e:
            logger.error(
                "Error invalidating cache", service=settings.SERVICE_NAME, error=str(e)
            )


crud_fish_type = CRUDFishType()

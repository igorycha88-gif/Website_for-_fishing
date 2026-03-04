from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.models.equipment_type import EquipmentType
from app.schemas.equipment_type import EquipmentTypeCreate, EquipmentTypeUpdate
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CRUDEquipmentType:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.cache_ttl = 3600

    async def create(
        self, db: AsyncSession, equipment_type_in: EquipmentTypeCreate
    ) -> EquipmentType:
        logger.info(
            "Creating equipment type",
            service=settings.SERVICE_NAME,
            equipment_type_name=equipment_type_in.name,
        )

        try:
            db_equipment_type = EquipmentType(**equipment_type_in.model_dump())
            db.add(db_equipment_type)
            await db.commit()
            await db.refresh(db_equipment_type)

            logger.info(
                "Equipment type created successfully",
                service=settings.SERVICE_NAME,
                equipment_type_id=str(db_equipment_type.id),
                equipment_type_name=db_equipment_type.name,
            )

            await self._invalidate_cache()
            return db_equipment_type

        except Exception as e:
            logger.error(
                "Error creating equipment type",
                service=settings.SERVICE_NAME,
                equipment_type_name=equipment_type_in.name,
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def get(
        self, db: AsyncSession, equipment_type_id: UUID
    ) -> Optional[EquipmentType]:
        logger.debug(
            "Getting equipment type by ID",
            service=settings.SERVICE_NAME,
            equipment_type_id=str(equipment_type_id),
        )

        result = await db.execute(
            select(EquipmentType).where(EquipmentType.id == equipment_type_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EquipmentType]:
        logger.debug(
            "Getting all equipment types",
            service=settings.SERVICE_NAME,
            category=category,
            is_active=is_active,
        )

        cache_key = (
            f"equipment_types:{category or 'all'}:{is_active or 'all'}:{skip}:{limit}"
        )

        try:
            cached = await self._get_from_cache(cache_key)
            if cached:
                logger.info(
                    "Cache hit for equipment types",
                    service=settings.SERVICE_NAME,
                    cache_key=cache_key,
                )
                return [EquipmentType(**et) for et in cached]
        except Exception as e:
            logger.warning(
                "Error reading from cache",
                service=settings.SERVICE_NAME,
                cache_key=cache_key,
                error=str(e),
            )

        try:
            query = select(EquipmentType)

            if category:
                query = query.where(EquipmentType.category == category)
            if is_active is not None:
                query = query.where(EquipmentType.is_active == is_active)

            query = query.offset(skip).limit(limit)
            query = query.order_by(EquipmentType.name)

            result = await db.execute(query)
            equipment_types = result.scalars().all()

            try:
                equipment_types_dict = [
                    self._equipment_type_to_dict(et) for et in equipment_types
                ]
                await self._save_to_cache(cache_key, equipment_types_dict)
                logger.info(
                    "Cached equipment types",
                    service=settings.SERVICE_NAME,
                    cache_key=cache_key,
                    count=len(equipment_types),
                )
            except Exception as e:
                logger.warning(
                    "Error caching equipment types",
                    service=settings.SERVICE_NAME,
                    cache_key=cache_key,
                    error=str(e),
                )

            return equipment_types

        except Exception as e:
            logger.error(
                "Error getting equipment types from database",
                service=settings.SERVICE_NAME,
                error=str(e),
                exc_info=True,
            )
            return []

    async def update(
        self,
        db: AsyncSession,
        equipment_type_id: UUID,
        equipment_type_in: EquipmentTypeUpdate,
    ) -> Optional[EquipmentType]:
        logger.info(
            "Updating equipment type",
            service=settings.SERVICE_NAME,
            equipment_type_id=str(equipment_type_id),
        )

        try:
            db_equipment_type = await self.get(db, equipment_type_id)
            if not db_equipment_type:
                logger.warning(
                    "Equipment type not found for update",
                    service=settings.SERVICE_NAME,
                    equipment_type_id=str(equipment_type_id),
                )
                return None

            update_data = equipment_type_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_equipment_type, field, value)

            await db.commit()
            await db.refresh(db_equipment_type)

            logger.info(
                "Equipment type updated successfully",
                service=settings.SERVICE_NAME,
                equipment_type_id=str(equipment_type_id),
                equipment_type_name=db_equipment_type.name,
            )

            await self._invalidate_cache()
            return db_equipment_type

        except Exception as e:
            logger.error(
                "Error updating equipment type",
                service=settings.SERVICE_NAME,
                equipment_type_id=str(equipment_type_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, equipment_type_id: UUID) -> bool:
        logger.info(
            "Deleting equipment type",
            service=settings.SERVICE_NAME,
            equipment_type_id=str(equipment_type_id),
        )

        try:
            db_equipment_type = await self.get(db, equipment_type_id)
            if not db_equipment_type:
                logger.warning(
                    "Equipment type not found for deletion",
                    service=settings.SERVICE_NAME,
                    equipment_type_id=str(equipment_type_id),
                )
                return False

            await db.delete(db_equipment_type)
            await db.commit()

            logger.info(
                "Equipment type deleted successfully",
                service=settings.SERVICE_NAME,
                equipment_type_id=str(equipment_type_id),
                equipment_type_name=db_equipment_type.name,
            )

            await self._invalidate_cache()
            return True

        except Exception as e:
            logger.error(
                "Error deleting equipment type",
                service=settings.SERVICE_NAME,
                equipment_type_id=str(equipment_type_id),
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            raise

    def _equipment_type_to_dict(self, equipment_type: EquipmentType) -> dict:
        return {
            "id": str(equipment_type.id),
            "name": equipment_type.name,
            "category": equipment_type.category,
            "is_active": equipment_type.is_active,
            "created_at": equipment_type.created_at.isoformat()
            if equipment_type.created_at
            else None,
            "updated_at": equipment_type.updated_at.isoformat()
            if equipment_type.updated_at
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
            pattern = "equipment_types:*"
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)
                logger.info(
                    "Cache invalidated for equipment types",
                    service=settings.SERVICE_NAME,
                    keys_deleted=len(keys),
                )
        except Exception as e:
            logger.error(
                "Error invalidating cache", service=settings.SERVICE_NAME, error=str(e)
            )


crud_equipment_type = CRUDEquipmentType()

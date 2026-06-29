from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.catch_point import CatchPoint
from app.models.fish_type import FishType
from app.schemas.place import FishTypeInPlace
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class CRUDCatchPoint:
    async def _enrich_with_fish_type(
        self, db: AsyncSession, catch_point: CatchPoint
    ) -> Optional[Dict[str, Any]]:
        if not catch_point:
            return None

        fish_type = None
        if catch_point.fish_type_id:
            result = await db.execute(
                select(FishType).where(FishType.id == catch_point.fish_type_id)
            )
            ft = result.scalar_one_or_none()
            if ft:
                fish_type = FishTypeInPlace(
                    id=ft.id, name=ft.name, icon=ft.icon, category=ft.category
                )

        if not fish_type:
            logger.warning(
                "Fish type not found for catch point",
                service=settings.SERVICE_NAME,
                catch_point_id=str(catch_point.id),
                fish_type_id=str(catch_point.fish_type_id),
            )
            return None

        return {
            "id": catch_point.id,
            "latitude": catch_point.latitude,
            "longitude": catch_point.longitude,
            "fish_type": fish_type,
            "river": catch_point.river,
            "name": catch_point.name,
            "description": catch_point.description,
            "season": catch_point.season,
            "depth": catch_point.depth,
            "bait": catch_point.bait,
            "weight_avg": catch_point.weight_avg,
            "is_demo": catch_point.is_demo,
            "source_label": catch_point.source_label,
            "created_at": catch_point.created_at,
        }

    async def get_list(
        self,
        db: AsyncSession,
        river: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        min_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lat: Optional[float] = None,
        max_lon: Optional[float] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        logger.debug(
            "Getting catch points",
            service=settings.SERVICE_NAME,
            filters={
                "river": river,
                "fish_type_id": str(fish_type_id) if fish_type_id else None,
                "bbox": [min_lat, min_lon, max_lat, max_lon],
            },
        )

        try:
            query = select(CatchPoint).where(CatchPoint.is_active)

            if river:
                query = query.where(CatchPoint.river == river)

            if fish_type_id:
                query = query.where(CatchPoint.fish_type_id == fish_type_id)

            if min_lat is not None:
                query = query.where(CatchPoint.latitude >= Decimal(str(min_lat)))
            if max_lat is not None:
                query = query.where(CatchPoint.latitude <= Decimal(str(max_lat)))
            if min_lon is not None:
                query = query.where(CatchPoint.longitude >= Decimal(str(min_lon)))
            if max_lon is not None:
                query = query.where(CatchPoint.longitude <= Decimal(str(max_lon)))

            query = query.order_by(CatchPoint.created_at.desc()).offset(skip).limit(limit)

            result = await db.execute(query)
            catch_points = result.scalars().all()

            enriched = []
            for cp in catch_points:
                e = await self._enrich_with_fish_type(db, cp)
                if e:
                    enriched.append(e)

            logger.info(
                "Retrieved catch points",
                service=settings.SERVICE_NAME,
                count=len(enriched),
            )
            return enriched

        except Exception as e:
            logger.error(
                "Error getting catch points",
                service=settings.SERVICE_NAME,
                error=str(e),
                exc_info=True,
            )
            return []

    async def count(
        self,
        db: AsyncSession,
        river: Optional[str] = None,
        fish_type_id: Optional[UUID] = None,
        min_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lat: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> int:
        try:
            query = (
                select(func.count()).select_from(CatchPoint).where(CatchPoint.is_active)
            )

            if river:
                query = query.where(CatchPoint.river == river)

            if fish_type_id:
                query = query.where(CatchPoint.fish_type_id == fish_type_id)

            if min_lat is not None:
                query = query.where(CatchPoint.latitude >= Decimal(str(min_lat)))
            if max_lat is not None:
                query = query.where(CatchPoint.latitude <= Decimal(str(max_lat)))
            if min_lon is not None:
                query = query.where(CatchPoint.longitude >= Decimal(str(min_lon)))
            if max_lon is not None:
                query = query.where(CatchPoint.longitude <= Decimal(str(max_lon)))

            result = await db.execute(query)
            count = result.scalar()
            return count or 0

        except Exception as e:
            logger.error(
                "Error counting catch points",
                service=settings.SERVICE_NAME,
                error=str(e),
                exc_info=True,
            )
            return 0

    async def get(self, db: AsyncSession, catch_id: UUID) -> Optional[Dict[str, Any]]:
        logger.debug(
            "Getting catch point by ID",
            service=settings.SERVICE_NAME,
            catch_point_id=str(catch_id),
        )

        try:
            result = await db.execute(
                select(CatchPoint).where(CatchPoint.id == catch_id)
            )
            cp = result.scalar_one_or_none()
            if not cp:
                return None
            return await self._enrich_with_fish_type(db, cp)
        except Exception as e:
            logger.error(
                "Error getting catch point",
                service=settings.SERVICE_NAME,
                catch_point_id=str(catch_id),
                error=str(e),
                exc_info=True,
            )
            return None


crud_catch_point = CRUDCatchPoint()

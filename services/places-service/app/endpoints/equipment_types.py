from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_redis
from app.core.logging_config import get_logger
from app.schemas.equipment_type import (
    EquipmentTypeCreate,
    EquipmentTypeUpdate,
    EquipmentTypeResponse,
)
from app.crud import crud_equipment_type

logger = get_logger(__name__)
router = APIRouter()


@router.get("/equipment-types", response_model=List[EquipmentTypeResponse])
async def get_equipment_types(
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    redis_client=Depends(get_redis),
):
    logger.info(
        "GET /equipment-types",
        service="places-service",
        category=category,
        is_active=is_active,
    )

    equipment_types = await crud_equipment_type.get_all(
        db=db, category=category, is_active=is_active, skip=skip, limit=limit
    )

    return equipment_types


@router.get(
    "/equipment-types/{equipment_type_id}", response_model=EquipmentTypeResponse
)
async def get_equipment_type(
    equipment_type_id: UUID, db: AsyncSession = Depends(get_db)
):
    logger.info(
        "GET /equipment-types/{equipment_type_id}",
        service="places-service",
        equipment_type_id=str(equipment_type_id),
    )

    equipment_type = await crud_equipment_type.get(
        db=db, equipment_type_id=equipment_type_id
    )

    if not equipment_type:
        logger.warning(
            "Equipment type not found",
            service="places-service",
            equipment_type_id=str(equipment_type_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Equipment type not found"
        )

    return equipment_type

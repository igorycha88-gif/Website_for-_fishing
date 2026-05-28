from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class EquipmentTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название снасти")
    category: str = Field(..., description="Категория: rod, reel, bait, accessories")
    is_active: bool = Field(True, description="Активен")


class EquipmentTypeCreate(EquipmentTypeBase):
    pass


class EquipmentTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = None
    is_active: Optional[bool] = None


class EquipmentTypeResponse(EquipmentTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

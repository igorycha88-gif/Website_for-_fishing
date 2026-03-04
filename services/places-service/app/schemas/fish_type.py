from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class FishTypeBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Название вида рыбы"
    )
    icon: Optional[str] = Field(None, max_length=50, description="Иконка/эмодзи")
    category: str = Field(
        ..., description="Категория: predatory, peaceful, sport, commercial"
    )
    is_active: bool = Field(True, description="Активен")


class FishTypeCreate(FishTypeBase):
    pass


class FishTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = None
    is_active: Optional[bool] = None


class FishTypeResponse(FishTypeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

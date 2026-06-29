from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal

from app.schemas.place import FishTypeInPlace


class CatchPointResponse(BaseModel):
    id: UUID
    latitude: Decimal
    longitude: Decimal
    fish_type: FishTypeInPlace
    river: str
    name: str
    description: Optional[str] = None
    season: Optional[List[str]] = None
    depth: Optional[Decimal] = None
    bait: Optional[str] = None
    weight_avg: Optional[Decimal] = None
    is_demo: bool
    source_label: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CatchPointListResponse(BaseModel):
    catches: List[CatchPointResponse]
    total: int
    page: int
    page_size: int

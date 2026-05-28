from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


class PlaceBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    address: str = Field(..., max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    price_per_day: Optional[Decimal] = Field(None, ge=0)
    max_people: Optional[int] = Field(None, ge=1)
    facilities: Optional[List[str]] = None
    fish_types: Optional[List[str]] = None
    images: Optional[List[str]] = Field(None, max_length=5)
    is_public: bool = False
    visit_date: Optional[datetime] = None
    place_type: Optional[str] = Field(None, pattern="^(resort|wild_place|camping)$")
    seasonality: Optional[List[str]] = None
    water_depth: Optional[Dict[str, int]] = None
    water_type: Optional[str] = Field(None, pattern="^(river|lake|pond|reservoir|sea|other)$")
    access_type: Optional[str] = Field(None, pattern="^(car|walking|boat_only|car_boat)$")
    fishing_permission: Optional[str] = Field(None, pattern="^(free|paid|license|prohibited)$")

    @field_validator('fish_types')
    @classmethod
    def validate_fish_types(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('At least one fish type must be specified')
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 fish types allowed')
        return v

    @field_validator('images')
    @classmethod
    def validate_images(cls, v):
        if v is not None and len(v) > 5:
            raise ValueError('Maximum 5 images allowed')
        return v


class PlaceCreate(PlaceBase):
    pass

    @field_validator('is_public')
    @classmethod
    def validate_public_images(cls, v, info):
        if v:
            images = info.data.get('images')
            if not images or len(images) == 0:
                raise ValueError('Public places must have at least one image')
        return v


class PlaceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    price_per_day: Optional[Decimal] = Field(None, ge=0)
    max_people: Optional[int] = Field(None, ge=1)
    facilities: Optional[List[str]] = None
    fish_types: Optional[List[str]] = None
    images: Optional[List[str]] = Field(None, max_length=5)
    is_public: Optional[bool] = None
    visit_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(active|pending_moderation|rejected)$")
    place_type: Optional[str] = Field(None, pattern="^(resort|wild_place|camping)$")
    seasonality: Optional[List[str]] = None
    water_depth: Optional[Dict[str, int]] = None
    water_type: Optional[str] = Field(None, pattern="^(river|lake|pond|reservoir|sea|other)$")
    access_type: Optional[str] = Field(None, pattern="^(car|walking|boat_only|car_boat)$")
    fishing_permission: Optional[str] = Field(None, pattern="^(free|paid|license|prohibited)$")


class PlaceResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    description: str
    latitude: float
    longitude: float
    address: str
    city: Optional[str]
    region: Optional[str]
    price_per_day: Optional[float]
    max_people: Optional[int]
    facilities: Optional[List[str]]
    fish_types: Optional[List[str]]
    images: Optional[List[str]]
    rating_avg: float
    reviews_count: int
    is_active: bool
    is_public: bool
    status: str
    visit_date: Optional[datetime]
    place_type: Optional[str]
    seasonality: Optional[List[str]]
    water_depth: Optional[Dict[str, int]]
    water_type: Optional[str]
    access_type: Optional[str]
    fishing_permission: Optional[str]
    created_at: datetime
    updated_at: datetime

    @field_validator('id', 'owner_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    @field_validator('latitude', 'longitude', mode='before')
    @classmethod
    def convert_decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v

    @field_validator('rating_avg', mode='before')
    @classmethod
    def convert_rating_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        if v is None:
            return 0.0
        return v

    class Config:
        from_attributes = True


class PlaceWithOwnerResponse(PlaceResponse):
    owner_username: Optional[str]
    owner_first_name: Optional[str]
    owner_last_name: Optional[str]
    owner_avatar_url: Optional[str]


class PlaceListResponse(BaseModel):
    items: List[PlaceResponse]
    total: int
    page: int
    limit: int
    pages: int


class ModerationRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = Field(None, max_length=1000)

    @field_validator('reason')
    @classmethod
    def validate_reason_for_reject(cls, v, info):
        if info.data.get('action') == 'reject' and not v:
            raise ValueError('Reason is required for rejection')
        return v


class PlaceStatisticsResponse(BaseModel):
    reports_count: int
    avg_rating: float
    top_fish: List[dict]
    seasonality: dict
    last_report: Optional[dict]


class FishTypeResponse(BaseModel):
    id: str
    name: str
    name_en: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None


class FacilityResponse(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: dict


class ReverseGeocodeRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class ReverseGeocodeResponse(BaseModel):
    address: Optional[str]
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]

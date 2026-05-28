from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from decimal import Decimal


class FishTypeInPlace(BaseModel):
    id: UUID
    name: str
    icon: Optional[str]
    category: str

    class Config:
        from_attributes = True


class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Название места")
    description: Optional[str] = Field(None, description="Описание места")
    latitude: Decimal = Field(..., ge=-90, le=90, description="Широта")
    longitude: Decimal = Field(..., ge=-180, le=180, description="Долгота")
    address: str = Field(..., min_length=1, max_length=500, description="Адрес")
    place_type: str = Field(..., description="Тип места: wild, camping, resort")
    access_type: str = Field(..., description="Тип подъезда: car, boat, foot")
    water_type: str = Field("lake", description="Тип водоема: river, lake, sea")
    fish_types: List[UUID] = Field(
        ..., min_length=1, description="Виды рыбы (минимум 1)"
    )
    seasonality: Optional[List[str]] = Field(
        None, description="Сезонность: spring, summer, autumn, winter"
    )
    visibility: str = Field("private", description="Видимость: private, public")
    images: List[str] = Field(
        default_factory=list, max_length=4, description="URL фото (максимум 4)"
    )


class PlaceBaseForResponse(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Название места")
    description: Optional[str] = Field(None, description="Описание места")
    latitude: Decimal = Field(..., ge=-90, le=90, description="Широта")
    longitude: Decimal = Field(..., ge=-180, le=180, description="Долгота")
    address: str = Field(..., min_length=1, max_length=500, description="Адрес")
    place_type: str = Field(..., description="Тип места: wild, camping, resort")
    access_type: str = Field(..., description="Тип подъезда: car, boat, foot")
    water_type: str = Field("lake", description="Тип водоема: river, lake, sea")
    fish_types: List[FishTypeInPlace] = Field(
        ..., min_length=1, description="Виды рыбы (минимум 1)"
    )
    seasonality: Optional[List[str]] = Field(
        None, description="Сезонность: spring, summer, autumn, winter"
    )
    visibility: str = Field("private", description="Видимость: private, public")
    images: List[str] = Field(
        default_factory=list, max_length=4, description="URL фото (максимум 4)"
    )

    @field_validator("place_type")
    @classmethod
    def validate_place_type(cls, v):
        valid_types = ["wild", "camping", "resort"]
        if v not in valid_types:
            raise ValueError(f"place_type must be one of {valid_types}")
        return v

    @field_validator("access_type")
    @classmethod
    def validate_access_type(cls, v):
        valid_types = ["car", "boat", "foot"]
        if v not in valid_types:
            raise ValueError(f"access_type must be one of {valid_types}")
        return v

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v):
        valid_types = ["private", "public"]
        if v not in valid_types:
            raise ValueError(f"visibility must be one of {valid_types}")
        return v

    @field_validator("seasonality")
    @classmethod
    def validate_seasonality(cls, v):
        if v:
            valid_seasons = ["spring", "summer", "autumn", "winter"]
            for season in v:
                if season not in valid_seasons:
                    raise ValueError(
                        f"Invalid season: {season}. Must be one of {valid_seasons}"
                    )
        return v

    @field_validator("water_type")
    @classmethod
    def validate_water_type(cls, v):
        valid_types = ["river", "lake", "sea"]
        if v not in valid_types:
            raise ValueError(f"water_type must be one of {valid_types}")
        return v


class PlaceCreate(PlaceBase):
    pass


class PlaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    place_type: Optional[str] = None
    access_type: Optional[str] = None
    water_type: Optional[str] = None
    fish_types: Optional[List[UUID]] = None
    seasonality: Optional[List[str]] = None
    visibility: Optional[str] = None
    images: Optional[List[str]] = Field(None, max_length=4)

    @field_validator("place_type")
    @classmethod
    def validate_place_type(cls, v):
        if v is not None:
            valid_types = ["wild", "camping", "resort"]
            if v not in valid_types:
                raise ValueError(f"place_type must be one of {valid_types}")
        return v

    @field_validator("access_type")
    @classmethod
    def validate_access_type(cls, v):
        if v is not None:
            valid_types = ["car", "boat", "foot"]
            if v not in valid_types:
                raise ValueError(f"access_type must be one of {valid_types}")
        return v

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v):
        if v is not None:
            valid_types = ["private", "public"]
            if v not in valid_types:
                raise ValueError(f"visibility must be one of {valid_types}")
        return v

    @field_validator("seasonality")
    @classmethod
    def validate_seasonality(cls, v):
        if v:
            valid_seasons = ["spring", "summer", "autumn", "winter"]
            for season in v:
                if season not in valid_seasons:
                    raise ValueError(
                        f"Invalid season: {season}. Must be one of {valid_seasons}"
                    )
        return v

    @field_validator("water_type")
    @classmethod
    def validate_water_type(cls, v):
        if v is not None:
            valid_types = ["river", "lake", "sea"]
            if v not in valid_types:
                raise ValueError(f"water_type must be one of {valid_types}")
        return v


class PlaceResponse(PlaceBaseForResponse):
    id: UUID
    owner_id: UUID
    rating_avg: Decimal
    reviews_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_favorite: Optional[bool] = False

    class Config:
        from_attributes = True


class PlaceListResponse(BaseModel):
    places: List[PlaceResponse]
    total: int
    page: int
    page_size: int

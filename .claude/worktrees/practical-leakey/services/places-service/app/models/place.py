from sqlalchemy import Column, String, Numeric, Text, Boolean, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Place(Base):
    __tablename__ = "places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    address = Column(String(500), nullable=False)
    city = Column(String(100))
    region = Column(String(100))
    price_per_day = Column(Numeric(10, 2))
    max_people = Column(Integer)
    facilities = Column(JSON)
    fish_types = Column(JSON)
    images = Column(JSON)
    rating_avg = Column(Numeric(3, 2), default=0)
    reviews_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    status = Column(String(30), default="active")
    visit_date = Column(DateTime)
    place_type = Column(String(20), default="wild_place")
    seasonality = Column(JSONB)
    water_depth = Column(JSONB)
    water_type = Column(String(20))
    access_type = Column(String(20))
    fishing_permission = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

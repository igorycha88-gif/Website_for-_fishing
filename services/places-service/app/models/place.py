from sqlalchemy import (
    Column,
    String,
    Text,
    Numeric,
    Boolean,
    DateTime,
    Integer,
    ARRAY,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), nullable=False)

    name = Column(String(200), nullable=False)
    description = Column(Text)

    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    address = Column(String(500), nullable=False)

    place_type = Column(String(20), nullable=False)
    access_type = Column(String(20), nullable=False)
    water_type = Column(String(20), nullable=False, default="lake")

    fish_types = Column(PG_ARRAY(UUID(as_uuid=True)), nullable=False)
    seasonality = Column(ARRAY(String))

    visibility = Column(String(20), default="private", nullable=False)
    images = Column(ARRAY(String))

    rating_avg = Column(Numeric(3, 2), default=0)
    reviews_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    favorites = relationship(
        "FavoritePlace", back_populates="place", cascade="all, delete-orphan"
    )

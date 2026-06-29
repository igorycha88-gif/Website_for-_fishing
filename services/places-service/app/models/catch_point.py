from sqlalchemy import (
    Column,
    String,
    Text,
    Numeric,
    Boolean,
    DateTime,
    ARRAY,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class CatchPoint(Base):
    __tablename__ = "catch_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    fish_type_id = Column(UUID(as_uuid=True), nullable=False)
    river = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    season = Column(ARRAY(String))
    depth = Column(Numeric(6, 2))
    bait = Column(String(200))
    weight_avg = Column(Numeric(6, 2))
    is_demo = Column(Boolean, default=True)
    source_label = Column(String(100), default="Демонстрационные данные")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

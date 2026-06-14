from sqlalchemy import Column, Float, Integer, String, TIMESTAMP, text

from app.core.database import Base


class RuWaterBody(Base):
    __tablename__ = "ru_water_bodies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    gvr_id = Column(String(50))
    name = Column(String(500), nullable=False, index=True)
    name_alt = Column(String(500))
    water_type = Column(String(20), nullable=False, default="lake")
    lat_min = Column(Float, nullable=False)
    lat_max = Column(Float, nullable=False)
    lon_min = Column(Float, nullable=False)
    lon_max = Column(Float, nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    avg_depth = Column(Float)
    max_depth = Column(Float)
    area_km2 = Column(Float)
    region = Column(String(100))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

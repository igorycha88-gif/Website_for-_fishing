-- Migration 010: Create ru_water_bodies table
-- For Russian hydrographic data (GVR + curated dataset)

CREATE TABLE IF NOT EXISTS ru_water_bodies (
    id SERIAL PRIMARY KEY,
    gvr_id VARCHAR(50),
    name VARCHAR(500) NOT NULL,
    name_alt VARCHAR(500),
    water_type VARCHAR(20) NOT NULL DEFAULT 'lake',
    lat_min FLOAT NOT NULL,
    lat_max FLOAT NOT NULL,
    lon_min FLOAT NOT NULL,
    lon_max FLOAT NOT NULL,
    centroid_lat FLOAT NOT NULL,
    centroid_lon FLOAT NOT NULL,
    avg_depth FLOAT,
    max_depth FLOAT,
    area_km2 FLOAT,
    region VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ru_water_bodies_lat ON ru_water_bodies (lat_min, lat_max);
CREATE INDEX IF NOT EXISTS idx_ru_water_bodies_lon ON ru_water_bodies (lon_min, lon_max);
CREATE INDEX IF NOT EXISTS idx_ru_water_bodies_centroid ON ru_water_bodies (centroid_lat, centroid_lon);
CREATE INDEX IF NOT EXISTS idx_ru_water_bodies_name ON ru_water_bodies (name);

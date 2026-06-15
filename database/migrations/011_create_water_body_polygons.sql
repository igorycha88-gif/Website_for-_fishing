-- Migration 011: Create water_body_polygons table
-- For storing actual polygon geometries from OSM (OpenStreetMap)
-- Used by Navionics-style depth layer visualization

CREATE TABLE IF NOT EXISTS water_body_polygons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL UNIQUE,
    water_type VARCHAR(20) NOT NULL DEFAULT 'lake',
    coordinates JSONB NOT NULL,
    lat_min FLOAT NOT NULL,
    lat_max FLOAT NOT NULL,
    lon_min FLOAT NOT NULL,
    lon_max FLOAT NOT NULL,
    centroid_lat FLOAT NOT NULL,
    centroid_lon FLOAT NOT NULL,
    max_depth FLOAT,
    avg_depth FLOAT,
    area_km2 FLOAT,
    source VARCHAR(20) NOT NULL DEFAULT 'OSM',
    region VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wbp_lat ON water_body_polygons (lat_min, lat_max);
CREATE INDEX IF NOT EXISTS idx_wbp_lon ON water_body_polygons (lon_min, lon_max);
CREATE INDEX IF NOT EXISTS idx_wbp_centroid ON water_body_polygons (centroid_lat, centroid_lon);
CREATE INDEX IF NOT EXISTS idx_wbp_name ON water_body_polygons (name);

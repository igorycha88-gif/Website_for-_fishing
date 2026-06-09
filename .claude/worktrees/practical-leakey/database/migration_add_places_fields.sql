-- Migration: Add new fields to places table for "My Places" functionality
-- Created: 2025-02-09
-- Description: Add place_type, seasonality, water_depth, water_type, access_type, fishing_permission fields

-- Add new columns to places table
ALTER TABLE places
    ADD COLUMN place_type VARCHAR(20) DEFAULT 'wild_place' CHECK (place_type IN ('resort', 'wild_place', 'camping'));

ALTER TABLE places
    ADD COLUMN seasonality JSONB;

ALTER TABLE places
    ADD COLUMN water_depth JSONB;

ALTER TABLE places
    ADD COLUMN water_type VARCHAR(20) CHECK (water_type IN ('river', 'lake', 'pond', 'reservoir', 'sea', 'other'));

ALTER TABLE places
    ADD COLUMN access_type VARCHAR(20) CHECK (access_type IN ('car', 'walking', 'boat_only', 'car_boat'));

ALTER TABLE places
    ADD COLUMN fishing_permission VARCHAR(20) CHECK (fishing_permission IN ('free', 'paid', 'license', 'prohibited'));

-- Add indexes for new fields
CREATE INDEX idx_places_type ON places(place_type);
CREATE INDEX idx_places_water_type ON places(water_type);
CREATE INDEX idx_places_access_type ON places(access_type);
CREATE INDEX idx_places_fishing_permission ON places(fishing_permission);

-- Add JSONB GIN indexes for JSONB fields
CREATE INDEX idx_places_seasonality ON places USING GIN(seasonality);
CREATE INDEX idx_places_water_depth ON places USING GIN(water_depth);

-- Add comment on new columns
COMMENT ON COLUMN places.place_type IS 'Type of place: resort (База отдыха), wild_place (Дикое место), camping (Кемпинг)';
COMMENT ON COLUMN places.seasonality IS 'Best season for fishing: ["spring", "summer", "autumn", "winter", "all_year"]';
COMMENT ON COLUMN places.water_depth IS 'Water depth in meters: {"min": 2, "max": 5}';
COMMENT ON COLUMN places.water_type IS 'Type of water body: river (Река), lake (Озеро), pond (Пруд), reservoir (Водохранилище), sea (Море), other (Другое)';
COMMENT ON COLUMN places.access_type IS 'How to access the water: car (Авто), walking (Пешком), boat_only (Только лодка), car_boat (Авто + лодка)';
COMMENT ON COLUMN places.fishing_permission IS 'Fishing permission required: free (Бесплатно), paid (Платно), license (По лицензии), prohibited (Запрещено)';

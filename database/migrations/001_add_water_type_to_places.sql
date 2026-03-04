-- Migration: add_water_type_to_places
-- Date: 2024-02-12
-- Description: Add water_type column to places table

BEGIN;

-- Add water_type column with default value
ALTER TABLE places
ADD COLUMN IF NOT EXISTS water_type VARCHAR(20) NOT NULL DEFAULT 'lake';

-- Add check constraint for valid water_type values
ALTER TABLE places
ADD CONSTRAINT chk_water_type_valid
CHECK (water_type IN ('river', 'lake', 'sea'));

-- Create index for filtering by water_type
CREATE INDEX IF NOT EXISTS idx_places_water_type ON places(water_type);

-- Add comment
COMMENT ON COLUMN places.water_type IS 'Тип водоема: river - река, lake - озеро, sea - море';

COMMIT;

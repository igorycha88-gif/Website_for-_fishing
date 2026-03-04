-- Rollback: add_water_type_to_places
-- Date: 2024-02-12

BEGIN;

-- Drop index
DROP INDEX IF EXISTS idx_places_water_type;

-- Drop constraint
ALTER TABLE places
DROP CONSTRAINT IF EXISTS chk_water_type_valid;

-- Drop column
ALTER TABLE places
DROP COLUMN IF EXISTS water_type;

COMMIT;

-- Migration: 003_add_user_added_fish
-- Date: 2026-02-18
-- Description: Add user_added_fish table for custom fish per region

BEGIN;

CREATE TABLE IF NOT EXISTS user_added_fish (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_user_fish_region UNIQUE(user_id, fish_type_id, region_id)
);

CREATE INDEX IF NOT EXISTS idx_user_added_fish_user_region ON user_added_fish(user_id, region_id);
CREATE INDEX IF NOT EXISTS idx_user_added_fish_fish_type ON user_added_fish(fish_type_id);

COMMIT;

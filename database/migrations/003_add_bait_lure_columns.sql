-- Migration: Add bait and lure recommendations columns to fish_bite_settings table
-- Date: 2026-03-04
-- Issue: forecast-service crash - missing columns

-- Add bait_recommendations column
ALTER TABLE fish_bite_settings
ADD COLUMN IF NOT EXISTS bait_recommendations JSONB DEFAULT '{}';

-- Add lure_recommendations column
ALTER TABLE fish_bite_settings
ADD COLUMN IF NOT EXISTS lure_recommendations JSONB DEFAULT '{}';

-- Comments
COMMENT ON COLUMN fish_bite_settings.bait_recommendations IS 'JSON object with bait recommendations by season/month';
COMMENT ON COLUMN fish_bite_settings.lure_recommendations IS 'JSON object with lure recommendations by season/month';

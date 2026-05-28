-- Migration: Add spawn period fields to fish_bite_settings table
-- Version: 002
-- Date: 2025-02-17
-- Description: US-FORECAST-WINTER-001 - Add spawn period fields for winter algorithm v2.0

-- Add spawn fields to fish_bite_settings
ALTER TABLE fish_bite_settings
ADD COLUMN IF NOT EXISTS spawn_start_month INTEGER,
ADD COLUMN IF NOT EXISTS spawn_end_month INTEGER,
ADD COLUMN IF NOT EXISTS spawn_start_day INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS spawn_end_day INTEGER DEFAULT 31;

COMMENT ON COLUMN fish_bite_settings.spawn_start_month IS 'Month when spawn period starts (1-12), NULL if not applicable';
COMMENT ON COLUMN fish_bite_settings.spawn_end_month IS 'Month when spawn period ends (1-12), NULL if not applicable';
COMMENT ON COLUMN fish_bite_settings.spawn_start_day IS 'Day of month when spawn period starts (1-31)';
COMMENT ON COLUMN fish_bite_settings.spawn_end_day IS 'Day of month when spawn period ends (1-31)';

-- Add spawn fields to fishing_forecasts
ALTER TABLE fishing_forecasts
ADD COLUMN IF NOT EXISTS is_spawn_period BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS spawn_message TEXT,
ADD COLUMN IF NOT EXISTS season_multiplier NUMERIC(3, 2);

COMMENT ON COLUMN fishing_forecasts.is_spawn_period IS 'Whether this forecast date is during spawn period';
COMMENT ON COLUMN fishing_forecasts.spawn_message IS 'Warning message if in spawn period';
COMMENT ON COLUMN fishing_forecasts.season_multiplier IS 'Season multiplier applied to the bite score';

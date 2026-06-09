-- Migration 008: Algorithm v5 — new fields for improved forecast accuracy
-- Adds: water_temperature, spawn phases, moon preferences, UV, turbidity, feedback

-- ============================================
-- 1. Weather Data: add water_temperature column
-- ============================================
ALTER TABLE weather_data
    ADD COLUMN IF NOT EXISTS water_temperature NUMERIC(5, 2);

-- ============================================
-- 2. Fish Bite Settings: add v5 fields
-- ============================================
ALTER TABLE fish_bite_settings
    ADD COLUMN IF NOT EXISTS pre_spawn_days INTEGER DEFAULT 14,
    ADD COLUMN IF NOT EXISTS post_spawn_days INTEGER DEFAULT 5,
    ADD COLUMN IF NOT EXISTS moon_phase_preference VARCHAR(20) DEFAULT 'neutral'
        CHECK (moon_phase_preference IN ('new_moon', 'full_moon', 'both', 'neutral')),
    ADD COLUMN IF NOT EXISTS turbidity_sensitive BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS uv_sensitivity NUMERIC(3, 2) DEFAULT 0.3,
    ADD COLUMN IF NOT EXISTS water_level_sensitivity NUMERIC(3, 2) DEFAULT 0.3;

-- ============================================
-- 3. User Catch Reports (feedback table)
-- ============================================
CREATE TABLE IF NOT EXISTS user_catch_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    time_of_day VARCHAR(20) NOT NULL CHECK (time_of_day IN ('morning', 'day', 'evening', 'night')),
    actual_bite BOOLEAN NOT NULL,
    bite_count INTEGER,
    predicted_score INTEGER,
    weather_temperature NUMERIC(5, 2),
    weather_pressure INTEGER,
    weather_wind_speed NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- 4. Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_weather_water_temp ON weather_data(region_id, forecast_date) WHERE water_temperature IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_catch_reports_user ON user_catch_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_catch_reports_region_fish ON user_catch_reports(region_id, fish_type_id);
CREATE INDEX IF NOT EXISTS idx_catch_reports_date ON user_catch_reports(forecast_date);
CREATE INDEX IF NOT EXISTS idx_catch_reports_created ON user_catch_reports(created_at);

-- Fishing Platform Database Schema (Minimal for Auth Service)
-- PostgreSQL 16+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- AUTH SERVICE TABLES
-- ============================================

-- Users table (Auth Service)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    city VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'moderator', 'admin')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Refresh tokens table (Auth Service)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Email verification codes table (Auth Service)
CREATE TABLE email_verification_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    code VARCHAR(6) NOT NULL,
    attempts INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_email_verification_codes_email ON email_verification_codes(email);
CREATE INDEX idx_email_verification_codes_expires_at ON email_verification_codes(expires_at);

-- ============================================
-- PLACES SERVICE TABLES
-- ============================================

-- Fish types table (Places Service)
CREATE TABLE fish_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    icon VARCHAR(50),
    category VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Places table (Places Service)
CREATE TABLE places (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    address VARCHAR(500) NOT NULL,
    place_type VARCHAR(20) NOT NULL,
    access_type VARCHAR(20) NOT NULL,
    water_type VARCHAR(20) NOT NULL DEFAULT 'lake',
    fish_types UUID[] NOT NULL,
    seasonality VARCHAR(20)[],
    visibility VARCHAR(20) NOT NULL DEFAULT 'private',
    images VARCHAR(500)[],
    rating_avg NUMERIC(3, 2) DEFAULT 0,
    reviews_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Favorite places table (Places Service)
CREATE TABLE favorite_places (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    place_id UUID NOT NULL REFERENCES places(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, place_id)
);

-- Equipment types table (Places Service)
CREATE TABLE equipment_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- PLACES SERVICE INDEXES
-- ============================================

CREATE INDEX idx_fish_types_name ON fish_types(name);
CREATE INDEX idx_fish_types_category ON fish_types(category);
CREATE INDEX idx_places_owner_id ON places(owner_id);
CREATE INDEX idx_places_visibility ON places(visibility);
CREATE INDEX idx_places_place_type ON places(place_type);
CREATE INDEX idx_favorite_places_user_id ON favorite_places(user_id);
CREATE INDEX idx_favorite_places_place_id ON favorite_places(place_id);

-- ============================================
-- FORECAST SERVICE TABLES
-- ============================================

-- Regions table (Forecast Service)
CREATE TABLE regions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE,
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'Europe/Moscow',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Weather data table (Forecast Service)
CREATE TABLE weather_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    forecast_hour INTEGER NOT NULL CHECK (forecast_hour >= 0 AND forecast_hour <= 23),
    temperature NUMERIC(5, 2),
    feels_like NUMERIC(5, 2),
    pressure_hpa INTEGER,
    humidity INTEGER,
    wind_speed NUMERIC(5, 2),
    wind_direction INTEGER,
    wind_gust NUMERIC(5, 2),
    cloudiness INTEGER,
    precipitation_mm NUMERIC(5, 2),
    precipitation_probability INTEGER,
    weather_condition VARCHAR(50),
    weather_icon VARCHAR(20),
    visibility_m INTEGER,
    uv_index NUMERIC(3, 1),
    moon_phase NUMERIC(3, 2),
    sunrise TIME,
    sunset TIME,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(region_id, forecast_date, forecast_hour)
);

-- Fish bite settings table (Forecast Service)
CREATE TABLE fish_bite_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fish_type_id UUID NOT NULL UNIQUE REFERENCES fish_types(id) ON DELETE CASCADE,
    optimal_temp_min NUMERIC(5, 2) NOT NULL DEFAULT 10,
    optimal_temp_max NUMERIC(5, 2) NOT NULL DEFAULT 25,
    optimal_pressure_min INTEGER NOT NULL DEFAULT 750,
    optimal_pressure_max INTEGER NOT NULL DEFAULT 770,
    max_wind_speed NUMERIC(5, 2) NOT NULL DEFAULT 8,
    precipitation_tolerance INTEGER NOT NULL DEFAULT 2,
    prefer_morning BOOLEAN DEFAULT true,
    prefer_evening BOOLEAN DEFAULT true,
    prefer_overcast BOOLEAN DEFAULT false,
    active_in_winter BOOLEAN DEFAULT false,
    moon_sensitivity NUMERIC(3, 2) DEFAULT 0.5,
    season_start_month INTEGER DEFAULT 4,
    season_end_month INTEGER DEFAULT 10,
    spawn_start_month INTEGER,
    spawn_end_month INTEGER,
    spawn_start_day INTEGER DEFAULT 1,
    spawn_end_day INTEGER DEFAULT 31,
    region_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Fishing forecasts table (Forecast Service)
CREATE TABLE fishing_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    time_of_day VARCHAR(20) NOT NULL CHECK (time_of_day IN ('morning', 'day', 'evening', 'night')),
    bite_score INTEGER NOT NULL CHECK (bite_score >= 0 AND bite_score <= 100),
    is_spawn_period BOOLEAN DEFAULT false,
    spawn_message TEXT,
    season_multiplier NUMERIC(3, 2),
    temperature_score INTEGER,
    pressure_score INTEGER,
    wind_score INTEGER,
    moon_score INTEGER,
    precipitation_score INTEGER,
    recommendation TEXT,
    best_baits TEXT[],
    best_depth VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(region_id, fish_type_id, forecast_date, time_of_day)
);

-- ============================================
-- FORECAST SERVICE INDEXES
-- ============================================

CREATE INDEX idx_regions_code ON regions(code);
CREATE INDEX idx_regions_active ON regions(is_active);
CREATE INDEX idx_weather_region_date ON weather_data(region_id, forecast_date);
CREATE INDEX idx_weather_date ON weather_data(forecast_date);
CREATE INDEX idx_fish_bite_settings_regions ON fish_bite_settings USING GIN(region_ids);
CREATE INDEX idx_forecast_region_date ON fishing_forecasts(region_id, forecast_date);
CREATE INDEX idx_forecast_fish ON fishing_forecasts(fish_type_id);
CREATE INDEX idx_forecast_date_score ON fishing_forecasts(forecast_date, bite_score DESC);

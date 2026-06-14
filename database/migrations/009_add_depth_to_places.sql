-- Migration 009: Add depth columns to places table
-- For GEBCO bathymetry integration

ALTER TABLE places
    ADD COLUMN IF NOT EXISTS depth NUMERIC(6,2);

ALTER TABLE places
    ADD COLUMN IF NOT EXISTS depth_source VARCHAR(10) DEFAULT 'auto';

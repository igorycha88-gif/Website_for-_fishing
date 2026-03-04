-- Migration 006: Add birth_date and bio to users table
-- Bug fix: these fields were present in the frontend form but missing from the DB schema

ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;

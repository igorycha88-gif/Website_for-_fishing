-- Migration 004: Add JWT Blacklist / Token Invalidation fields (SEC-006)
-- Date: 2026-03-02
-- Description: Add token_version to users, add revoked/revoked_at/replaced_by/jti to refresh_tokens

-- Add token_version to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER DEFAULT 1;

-- Add new fields to refresh_tokens table
ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS jti VARCHAR(36) UNIQUE;
ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS revoked BOOLEAN DEFAULT false;
ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP;
ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS replaced_by VARCHAR(36);

-- Create index for jti
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_jti ON refresh_tokens(jti);

-- Update existing refresh_tokens with random jti (for migration compatibility)
-- Note: This is only for existing tokens during migration
UPDATE refresh_tokens SET jti = gen_random_uuid()::text WHERE jti IS NULL;

-- Make jti NOT NULL after populating
ALTER TABLE refresh_tokens ALTER COLUMN jti SET NOT NULL;

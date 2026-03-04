-- Migration 005: Create password_reset_tokens table (SEC-008)
-- Date: 2026-03-03
-- Description: Database-based password reset tokens with guaranteed invalidation

-- Create password_reset_tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires ON password_reset_tokens(expires_at) WHERE used = FALSE;

-- Add foreign key constraint
ALTER TABLE password_reset_tokens
ADD CONSTRAINT fk_password_reset_tokens_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

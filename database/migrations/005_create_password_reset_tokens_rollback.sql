-- Rollback Migration 005: Drop password_reset_tokens table
-- Date: 2026-03-03

BEGIN;

DROP TABLE IF EXISTS password_reset_tokens CASCADE;

COMMIT;

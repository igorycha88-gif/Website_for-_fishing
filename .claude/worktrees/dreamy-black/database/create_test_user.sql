INSERT INTO users (email, username, password_hash, is_verified, is_active)
VALUES ('test@example.com', 'testuser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWzJmTLa.1e', true, true)
ON CONFLICT (email) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    is_verified = true,
    is_active = true
WHERE users.email = EXCLUDED.email;

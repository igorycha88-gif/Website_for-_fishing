-- Seed данные для тестовой базы данных
-- Используйте для наполнения базы тестовыми пользователями и местами

-- Вставка тестовых пользователей
INSERT INTO users (email, username, password_hash, is_verified, created_at) VALUES
('test@example.com', 'testuser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWzJmTLa.1e', true, NOW()),
('verified@example.com', 'verifieduser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWzJmTLa.1e', true, NOW()),
('unverified@example.com', 'unverifieduser', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWzJmTLa.1e', false, NOW())
ON CONFLICT (email) DO NOTHING;

-- Вставка тестовых мест
INSERT INTO places (
    title,
    description,
    latitude,
    longitude,
    address,
    city,
    region,
    price_per_day,
    max_people,
    facilities,
    fish_types,
    images,
    is_public,
    user_id,
    created_at
) VALUES
(
    'Озеро Карасиное',
    'Уютное озеро в лесу, много карася',
    55.7558,
    37.6173,
    'Москва, Россия',
    'Москва',
    'Московская область',
    1000.00,
    5,
    ARRAY['parking', 'toilet', 'shower']::text[],
    ARRAY['carp', 'bream']::text[],
    ARRAY['https://example.com/place1.jpg']::text[],
    true,
    (SELECT id FROM users WHERE email = 'test@example.com' LIMIT 1),
    NOW()
),
(
    'Река Волга - Рыбалка',
    'Отличное место для рыбалки на реке Волга',
    55.7558,
    37.6173,
    'Нижний Новгород, Россия',
    'Нижний Новгород',
    'Нижегородская область',
    1500.00,
    10,
    ARRAY['parking', 'toilet', 'cafe']::text[],
    ARRAY['pike', 'perch', 'zander']::text[],
    ARRAY['https://example.com/place2.jpg']::text[],
    false,
    (SELECT id FROM users WHERE email = 'test@example.com' LIMIT 1),
    NOW()
),
(
    'Лесное озеро',
    'Спокойное озеро в лесной зоне',
    55.7558,
    37.6173,
    'Тверь, Россия',
    'Тверь',
    'Тверская область',
    800.00,
    3,
    ARRAY['parking']::text[],
    ARRAY['carp', 'roach']::text[],
    ARRAY['https://example.com/place3.jpg']::text[],
    false,
    (SELECT id FROM users WHERE email = 'verified@example.com' LIMIT 1),
    NOW()
)
ON CONFLICT DO NOTHING;

-- Вставка кодов верификации email
INSERT INTO email_verification_codes (email, code, expires_at, created_at) VALUES
('unverified@example.com', '123456', NOW() + INTERVAL '1 day', NOW())
ON CONFLICT (email) DO NOTHING;

-- Вставка кодов сброса пароля
INSERT INTO password_reset_codes (email, code, expires_at, attempts, created_at) VALUES
('test@example.com', '654321', NOW() + INTERVAL '1 hour', 0, NOW())
ON CONFLICT (email) DO NOTHING;

-- Создание индексов для быстрого поиска (если их нет)
CREATE INDEX IF NOT EXISTS idx_places_user_id ON places(user_id);
CREATE INDEX IF NOT EXISTS idx_places_city ON places(city);
CREATE INDEX IF NOT EXISTS idx_places_is_public ON places(is_public);

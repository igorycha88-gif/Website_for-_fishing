-- Добавление тестовых мест в БД

-- Удаление существующих мест (для чистоты теста)
DELETE FROM places;

-- Вставка тестовых мест (все публичные)
INSERT INTO places (id, name, description, latitude, longitude, image_url, rating, tags, amenities, user_id, is_public, created_at, updated_at)
VALUES 
  (
    '11111111-1111-1111-1111-1111',  -- id
    'Красивое озеро',  -- name
    'Отличное место для рыбалки с карасями, лещом и сазаном',  -- description
    55.7558,  -- latitude
    37.6173, -- longitude
    'https://images.unsplash.com/photo-15294384891-ea0e9be668d9b1fb5f5?w=800&q=80&auto=format&fit=crop',  -- image_url
    4.8,  -- rating
    ARRAY['Спиннинг', 'Карась', 'Лещ', 'Сазан'],  -- tags
    ARRAY['Парковка', 'Доступность', 'Удобные места'],  -- amenities
    DEFAULT ARRAY[]::text,  -- amenities (default empty array)
    '11111111-1111-1111-1111',  -- user_id (тестовый user)
    true, -- is_public
    NOW(),  -- created_at
    NOW()  -- updated_at
    NOW()  -- updated_at
    true,  -- is_public (по умолчанию все публичные)
    
    -- Тестовое место 2
    '22222222-2222-2222-2222',  
    'Рыбинское водохранилище',  
    'Горная река для спиннинга и леща',  
    55.6813,  
    37.5963,  
    'https://images.unsplash.com/photo-15294384891-ea0e9be668d9b1fb5f5?w=800&q=80&auto=format&fit=crop',  
    4.9,  
    ARRAY['Спиннинг', 'Фидер', 'Щука', 'Судак'],  
    ARRAY['Барка', 'Палатка', 'Парковка'],  
    DEFAULT ARRAY[]::text,  
    '11111111-1111-1111-1111',  
    DEFAULT ARRAY[]::text,  
    '22222222-2222-2222-2222',  
    true
    
    -- Тестовое место 3
    '33333333-3333-3333-3333',  
    'Озеро Баскунчак',  
    'Огромное место для карповой рыбаки с щукой, сазаном и лещью',  
    55.6541,  
    38.5048,  
    'https://images.unsplash.com/photo-15294384891-ea0e9be668d9b1fb5f5?w=800&q=80&auto=format&fit=crop',  
    5.0,  
    ARRAY['Карповая рыбка', 'Сазан', 'Амур'],  
    ARRAY['Парковка', 'Барка', 'Палатка'],  
    DEFAULT ARRAY[]::text,  
    '33333333-3333-3333-3333',  
    DEFAULT ARRAY[]::text,  
    '33333333-3333-3333-3333',  
    true
);

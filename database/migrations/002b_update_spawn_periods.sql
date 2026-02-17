-- Migration: Update spawn periods for fish species
-- Version: 002b
-- Date: 2025-02-17
-- Description: US-FORECAST-WINTER-001 - Seed spawn period data for fish species

-- ХИЩНЫЕ РЫБЫ

-- Щука: март - апрель (ранний нерест)
UPDATE fish_bite_settings
SET spawn_start_month = 3, spawn_end_month = 4, spawn_start_day = 1, spawn_end_day = 30
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Щука');

-- Судак: апрель - май
UPDATE fish_bite_settings
SET spawn_start_month = 4, spawn_end_month = 5, spawn_start_day = 10, spawn_end_day = 20
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Судак');

-- Окунь: апрель - май
UPDATE fish_bite_settings
SET spawn_start_month = 4, spawn_end_month = 5, spawn_start_day = 1, spawn_end_day = 31
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Окунь');

-- Налим: декабрь - февраль (зимний нерест!)
UPDATE fish_bite_settings
SET spawn_start_month = 12, spawn_end_month = 2, spawn_start_day = 15, spawn_end_day = 28
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Налим');

-- МИРНЫЕ РЫБЫ

-- Карп: май - июнь (при температуре воды 18-20°C)
UPDATE fish_bite_settings
SET spawn_start_month = 5, spawn_end_month = 6, spawn_start_day = 15, spawn_end_day = 15
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Карп');

-- Лещ: апрель - май
UPDATE fish_bite_settings
SET spawn_start_month = 4, spawn_end_month = 5, spawn_start_day = 15, spawn_end_day = 31
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Лещ');

-- Карась: май - июнь
UPDATE fish_bite_settings
SET spawn_start_month = 5, spawn_end_month = 6, spawn_start_day = 1, spawn_end_day = 30
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Карась');

-- Плотва: апрель - май
UPDATE fish_bite_settings
SET spawn_start_month = 4, spawn_end_month = 5, spawn_start_day = 1, spawn_end_day = 20
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Плотва');

-- Язь: апрель - май
UPDATE fish_bite_settings
SET spawn_start_month = 4, spawn_end_month = 5, spawn_start_day = 10, spawn_end_day = 25
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Язь');

-- Сазан: май - июнь
UPDATE fish_bite_settings
SET spawn_start_month = 5, spawn_end_month = 6, spawn_start_day = 15, spawn_end_day = 30
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Сазан');

-- Амур: май - июль
UPDATE fish_bite_settings
SET spawn_start_month = 5, spawn_end_month = 7, spawn_start_day = 1, spawn_end_day = 31
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Амур');

-- Голавль: апрель - май
UPDATE fish_bite_settings
SET spawn_start_month = 4, spawn_end_month = 5, spawn_start_day = 20, spawn_end_day = 31
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Голавль');

-- Жерех: апрель - май
UPDATE fish_bite_settings
SET spawn_start_month = 4, spawn_end_month = 5, spawn_start_day = 15, spawn_end_day = 31
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Жерех');

-- СПОРТИВНЫЕ РЫБЫ

-- Форель речная: октябрь - ноябрь (осенний нерест)
UPDATE fish_bite_settings
SET spawn_start_month = 10, spawn_end_month = 11, spawn_start_day = 1, spawn_end_day = 30
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Форель речная');

-- Форель озерная: октябрь - ноябрь
UPDATE fish_bite_settings
SET spawn_start_month = 10, spawn_end_month = 11, spawn_start_day = 1, spawn_end_day = 30
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Форель озерная');

-- Хариус: май - июнь
UPDATE fish_bite_settings
SET spawn_start_month = 5, spawn_end_month = 6, spawn_start_day = 1, spawn_end_day = 30
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Хариус');

-- ПРОЧИЕ

-- Сом: май - июнь
UPDATE fish_bite_settings
SET spawn_start_month = 5, spawn_end_month = 6, spawn_start_day = 15, spawn_end_day = 30
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Сом');

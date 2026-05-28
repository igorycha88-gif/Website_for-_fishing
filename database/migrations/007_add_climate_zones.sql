-- Migration: Add climate zones for regional spawn periods
-- Version: 007
-- Date: 2026-05-28
-- Description: US-SPAWN-ZONES-001 - Add climate_zone to regions and spawn_periods_by_zone to fish_bite_settings

-- 1. Add climate_zone column to regions
ALTER TABLE regions ADD COLUMN IF NOT EXISTS climate_zone VARCHAR(10) DEFAULT 'central';

-- 2. Add spawn_periods_by_zone JSONB column to fish_bite_settings
ALTER TABLE fish_bite_settings
  ADD COLUMN IF NOT EXISTS spawn_periods_by_zone JSONB DEFAULT '{}';

-- 3. Update regions with climate zone based on region code

-- Юг (South)
UPDATE regions SET climate_zone = 'south'
WHERE code IN ('KDA', 'AST', 'ROS', 'VOR', 'VGG', 'SAR', 'SAM', 'KB', 'KC', 'SE', 'PRI', 'KHA');

-- Центр (Central)
UPDATE regions SET climate_zone = 'central'
WHERE code IN ('MOW', 'MOS', 'VLG', 'KIR');

-- Север/Сибирь (North)
UPDATE regions SET climate_zone = 'north'
WHERE code IN ('KR', 'KO', 'MUR', 'ARK', 'NEN', 'SVE', 'KHM', 'YAN', 'PER', 'TOM', 'NVS', 'KYA', 'IRK', 'KEM', 'ALT', 'BU', 'ZAB', 'AMU', 'YEV', 'SA', 'KAM', 'SAK');

-- 4. Update spawn_periods_by_zone for each fish species (2026 realistic dates)

-- Щука: Юг 15.02-25.03, Центр 1.03-20.04, Север 1.04-30.05
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 2, "spawn_end_month": 3, "spawn_start_day": 15, "spawn_end_day": 25}, "central": {"spawn_start_month": 3, "spawn_end_month": 4, "spawn_start_day": 1, "spawn_end_day": 20}, "north": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 1, "spawn_end_day": 31}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Щука');

-- Судак: Юг 1.03-15.04, Центр 10.04-20.05, Север 1.05-15.06
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 3, "spawn_end_month": 4, "spawn_start_day": 1, "spawn_end_day": 15}, "central": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 10, "spawn_end_day": 20}, "north": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 1, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Судак');

-- Окунь: Юг 15.03-20.04, Центр 1.04-20.05, Север 25.04-15.06
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 3, "spawn_end_month": 4, "spawn_start_day": 15, "spawn_end_day": 20}, "central": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 1, "spawn_end_day": 20}, "north": {"spawn_start_month": 4, "spawn_end_month": 6, "spawn_start_day": 25, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Окунь');

-- Налим: Юг 15.11-31.12, Центр 1.12-15.02, Север 15.12-28.02
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 11, "spawn_end_month": 12, "spawn_start_day": 15, "spawn_end_day": 31}, "central": {"spawn_start_month": 12, "spawn_end_month": 2, "spawn_start_day": 1, "spawn_end_day": 15}, "north": {"spawn_start_month": 12, "spawn_end_month": 2, "spawn_start_day": 15, "spawn_end_day": 28}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Налим');

-- Жерех: Юг 20.03-20.04, Центр 15.04-25.05, Север 1.05-31.05
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 3, "spawn_end_month": 4, "spawn_start_day": 20, "spawn_end_day": 20}, "central": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 15, "spawn_end_day": 25}, "north": {"spawn_start_month": 5, "spawn_end_month": 5, "spawn_start_day": 1, "spawn_end_day": 31}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Жерех');

-- Голавль: Юг 1.04-25.04, Центр 20.04-25.05, Север 5.05-31.05
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 4, "spawn_end_month": 4, "spawn_start_day": 1, "spawn_end_day": 25}, "central": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 20, "spawn_end_day": 25}, "north": {"spawn_start_month": 5, "spawn_end_month": 5, "spawn_start_day": 5, "spawn_end_day": 31}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Голавль');

-- Карп: Юг 1.05-31.05, Центр 15.05-20.06, Север 1.06-15.07
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 5, "spawn_end_month": 5, "spawn_start_day": 1, "spawn_end_day": 31}, "central": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 15, "spawn_end_day": 20}, "north": {"spawn_start_month": 6, "spawn_end_month": 7, "spawn_start_day": 1, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Карп');

-- Лещ: Юг 1.04-25.04, Центр 15.04-25.05, Север 1.05-15.06
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 4, "spawn_end_month": 4, "spawn_start_day": 1, "spawn_end_day": 25}, "central": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 15, "spawn_end_day": 25}, "north": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 1, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Лещ');

-- Карась: Юг 25.04-31.05, Центр 10.05-20.06, Север 1.06-15.07
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 25, "spawn_end_day": 31}, "central": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 10, "spawn_end_day": 20}, "north": {"spawn_start_month": 6, "spawn_end_month": 7, "spawn_start_day": 1, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Карась');

-- Плотва: Юг 10.03-10.04, Центр 1.04-20.05, Север 20.04-10.06
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 3, "spawn_end_month": 4, "spawn_start_day": 10, "spawn_end_day": 10}, "central": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 1, "spawn_end_day": 20}, "north": {"spawn_start_month": 4, "spawn_end_month": 6, "spawn_start_day": 20, "spawn_end_day": 10}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Плотва');

-- Язь: Юг 20.03-15.04, Центр 10.04-25.05, Север 1.05-10.06
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 3, "spawn_end_month": 4, "spawn_start_day": 20, "spawn_end_day": 15}, "central": {"spawn_start_month": 4, "spawn_end_month": 5, "spawn_start_day": 10, "spawn_end_day": 25}, "north": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 1, "spawn_end_day": 10}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Язь');

-- Сазан: Юг 25.04-5.06, Центр 15.05-25.06, Север 1.06-15.07
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 4, "spawn_end_month": 6, "spawn_start_day": 25, "spawn_end_day": 5}, "central": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 15, "spawn_end_day": 25}, "north": {"spawn_start_month": 6, "spawn_end_month": 7, "spawn_start_day": 1, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Сазан');

-- Амур: Юг 1.05-31.07, Центр 1.06-31.07, Север NULL (нет данных)
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 5, "spawn_end_month": 7, "spawn_start_day": 1, "spawn_end_day": 31}, "central": {"spawn_start_month": 6, "spawn_end_month": 7, "spawn_start_day": 1, "spawn_end_day": 31}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Амур');

-- Форель речная: Юг 1.10-15.11, Центр 15.10-30.11, Север 1.10-30.11
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 10, "spawn_end_month": 11, "spawn_start_day": 1, "spawn_end_day": 15}, "central": {"spawn_start_month": 10, "spawn_end_month": 11, "spawn_start_day": 15, "spawn_end_day": 30}, "north": {"spawn_start_month": 10, "spawn_end_month": 11, "spawn_start_day": 1, "spawn_end_day": 30}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Форель речная');

-- Форель озерная: Юг 1.10-15.11, Центр 15.10-30.11, Север 1.10-30.11
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 10, "spawn_end_month": 11, "spawn_start_day": 1, "spawn_end_day": 15}, "central": {"spawn_start_month": 10, "spawn_end_month": 11, "spawn_start_day": 15, "spawn_end_day": 30}, "north": {"spawn_start_month": 10, "spawn_end_month": 11, "spawn_start_day": 1, "spawn_end_day": 30}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Форель озерная');

-- Хариус: Юг 1.05-31.05, Центр 15.05-20.06, Север 1.06-15.07
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 5, "spawn_end_month": 5, "spawn_start_day": 1, "spawn_end_day": 31}, "central": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 15, "spawn_end_day": 20}, "north": {"spawn_start_month": 6, "spawn_end_month": 7, "spawn_start_day": 1, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Хариус');

-- Сом: Юг 1.05-10.06, Центр 20.05-25.06, Север 1.06-15.07
UPDATE fish_bite_settings SET spawn_periods_by_zone = '{"south": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 1, "spawn_end_day": 10}, "central": {"spawn_start_month": 5, "spawn_end_month": 6, "spawn_start_day": 20, "spawn_end_day": 25}, "north": {"spawn_start_month": 6, "spawn_end_month": 7, "spawn_start_day": 1, "spawn_end_day": 15}}'
WHERE fish_type_id = (SELECT id FROM fish_types WHERE name = 'Сом');

# ЧТЗ: Региональные сроки нереста по 3 климатическим зонам

## Версия: 1.0
## Дата: 2026-05-28
## Приоритет: High
## Статус: Согласовано

---

## Маршрутизация

**Архитектор:** ТРЕБУЕТСЯ (изменение схемы БД, затрагивает >5 файлов)
**Исполнитель:** Разработчик
**Обоснование:** Добавление климатических зон требует изменений в БД (2 новые колонки), ORM модели, seed данных, логике endpoint'а. Архитектурное решение: JSONB-подход (Вариант B из ADR).

---

## 1. Цели и задачи

### 1.1 Бизнес-цель
Обновить нерестовые сроки рыб на реалистичные для 2026 года с учётом 3 климатических зон России (Юг, Центр, Север/Сибирь), вместо единой даты для всех регионов.

### 1.2 Пользовательская ценность
Пользователи из южных регионов не будут видеть ложный запрет на рыбалку в те даты, когда в их регионе нерест давно закончился. И наоборот — северяне увидят реальные сроки запрета.

### 1.3 Метрики успеха
- Все 16 рыб с spawn-периодами имеют zone-specific даты в `spawn_periods_by_zone`
- API корректно возвращает spawn-статус в зависимости от региона
- Все существующие тесты проходят

---

## 2. Функциональные требования

### 2.1 User Story

**Given** пользователь запрашивает прогноз для региона "Краснодар" (Юг)
**When** дата попадает в зональный нерестовый период Щуки (1 марта - 25 марта для Юга)
**Then** bite_score = 0, spawn_message содержит зональные даты

**Given** пользователь запрашивает прогноз для региона "Карелия" (Север)
**When** дата 15 апреля — в нерестовом периоде Щуки для Севера (1 апреля - 30 мая)
**Then** bite_score = 0, spawn_message содержит северные даты

**Given** регион не имеет зональных данных (fallback)
**When** `spawn_periods_by_zone` пустой или зона не найдена
**Then** используются стандартные spawn-колонки как fallback

---

## 3. Техническая архитектура

### 3.1 Изменения в БД

#### Migration 003: `003_add_climate_zones.sql`

```sql
-- Добавить климатическую зону в regions
ALTER TABLE regions ADD COLUMN IF NOT EXISTS climate_zone VARCHAR(10) DEFAULT 'central';

-- Добавить зональные периоды нереста в fish_bite_settings
ALTER TABLE fish_bite_settings
  ADD COLUMN IF NOT EXISTS spawn_periods_by_zone JSONB DEFAULT '{}';
```

#### Обновление schema.sql
Добавить колонку `climate_zone` в `regions` и `spawn_periods_by_zone` в `fish_bite_settings`.

### 3.2 Структура JSONB `spawn_periods_by_zone`

```json
{
  "south": {
    "spawn_start_month": 3,
    "spawn_end_month": 3,
    "spawn_start_day": 1,
    "spawn_end_day": 25
  },
  "central": {
    "spawn_start_month": 3,
    "spawn_end_month": 4,
    "spawn_start_day": 5,
    "spawn_end_day": 30
  },
  "north": {
    "spawn_start_month": 4,
    "spawn_end_month": 5,
    "spawn_start_day": 1,
    "spawn_end_day": 31
  }
}
```

### 3.3 Маппинг климатических зон

```
REGION_CODE_TO_ZONE = {
    # Юг
    "KDA": "south", "AST": "south", "ROS": "south", "VOR": "south",
    "VGG": "south", "SAR": "south", "SAM": "south",
    "KB": "south", "KC": "south", "SE": "south",
    "PRI": "south", "KHA": "south",
    # Центр
    "MOW": "central", "MOS": "central", "VLG": "central", "KIR": "central",
    # Север/Сибирь
    "KR": "north", "KO": "north", "MUR": "north", "ARK": "north",
    "NEN": "north", "SVE": "north", "KHM": "north", "YAN": "north",
    "PER": "north", "TOM": "north", "NVS": "north", "KYA": "north",
    "IRK": "north", "KEM": "north", "ALT": "north", "BU": "north",
    "ZAB": "north", "AMU": "north", "YEV": "north", "SA": "north",
    "KAM": "north", "SAK": "north",
}
```

### 3.4 Зональные сроки нереста на 2026 год (реалистичные данные)

#### ХИЩНЫЕ РЫБЫ

| Рыба | Юг (start - end) | Центр (start - end) | Север/Сибирь (start - end) |
|------|------------------|---------------------|----------------------------|
| Щука | 15.02 - 25.03 | 1.03 - 20.04 | 1.04 - 30.05 |
| Судак | 1.03 - 15.04 | 10.04 - 20.05 | 1.05 - 15.06 |
| Окунь | 15.03 - 20.04 | 1.04 - 20.05 | 25.04 - 15.06 |
| Налим | 15.11 - 31.12 | 1.12 - 15.02 | 15.12 - 28.02 |
| Жерех | 20.03 - 20.04 | 15.04 - 25.05 | 1.05 - 31.05 |
| Голавль | 1.04 - 25.04 | 20.04 - 25.05 | 5.05 - 31.05 |

#### МИРНЫЕ РЫБЫ

| Рыба | Юг (start - end) | Центр (start - end) | Север/Сибирь (start - end) |
|------|------------------|---------------------|----------------------------|
| Карп | 1.05 - 31.05 | 15.05 - 20.06 | 1.06 - 15.07 |
| Лещ | 1.04 - 25.04 | 15.04 - 25.05 | 1.05 - 15.06 |
| Карась | 25.04 - 31.05 | 10.05 - 20.06 | 1.06 - 15.07 |
| Плотва | 10.03 - 10.04 | 1.04 - 20.05 | 20.04 - 10.06 |
| Язь | 20.03 - 15.04 | 10.04 - 25.05 | 1.05 - 10.06 |
| Сазан | 25.04 - 5.06 | 15.05 - 25.06 | 1.06 - 15.07 |
| Амур | 1.05 - 31.07 | 1.06 - 31.07 | (нет данных — NULL) |

#### СПОРТИВНЫЕ РЫБЫ

| Рыба | Юг (start - end) | Центр (start - end) | Север/Сибирь (start - end) |
|------|------------------|---------------------|----------------------------|
| Форель речная | 1.10 - 15.11 | 15.10 - 30.11 | 1.10 - 30.11 |
| Форель озерная | 1.10 - 15.11 | 15.10 - 30.11 | 1.10 - 30.11 |
| Хариус | 1.05 - 31.05 | 15.05 - 20.06 | 1.06 - 15.07 |

#### ПРОЧИЕ

| Рыба | Юг (start - end) | Центр (start - end) | Север/Сибирь (start - end) |
|------|------------------|---------------------|----------------------------|
| Сом | 1.05 - 10.06 | 20.05 - 25.06 | 1.06 - 15.07 |

#### БЕЗ ИЗМЕНЕНИЙ (NULL spawn)

| Рыба | Примечание |
|------|------------|
| Лосось | spawn_months = NULL (остаётся) |
| Таймень | spawn_months = NULL (остаётся) |

### 3.5 Изменения файлов

| Файл | Изменение |
|------|-----------|
| `database/schema.sql` | Добавить `climate_zone` в `regions`, `spawn_periods_by_zone` в `fish_bite_settings` |
| `database/migrations/003_add_climate_zones.sql` | Новая миграция (ALTER TABLE + UPDATE spawn data) |
| `services/forecast-service/app/models/forecast.py` | Добавить `climate_zone` в `Region`, `spawn_periods_by_zone` в `FishBiteSettings` |
| `services/forecast-service/app/services/forecast_calculation.py` | Добавить `get_spawn_dates_for_zone()`, обновить `REGION_CODE_TO_ZONE` |
| `services/forecast-service/app/endpoints/forecast.py` | Определять зону региона, подставлять zone-specific spawn dates в `FishSettings` |
| `services/forecast-service/app/seed_fish_settings.py` | Обновить seed data с `spawn_periods_by_zone` |
| `services/forecast-service/tests/test_forecast_calculation.py` | Добавить тесты для зональных spawn-периодов |

---

## 4. Декомпозиция на задачи

### TASK-INF-001: Миграция БД и обновление schema.sql
**Приоритет**: High
**Зависимости**: нет

- Добавить `climate_zone VARCHAR(10) DEFAULT 'central'` в `regions` (schema.sql)
- Добавить `spawn_periods_by_zone JSONB DEFAULT '{}'` в `fish_bite_settings` (schema.sql)
- Создать `database/migrations/003_add_climate_zones.sql` с ALTER TABLE

**Критерии приемки**:
- [ ] `schema.sql` содержит новые колонки
- [ ] Миграция 003 корректно добавляет колонки
- [ ] Миграция обновляет `regions.climate_zone` по region code

### TASK-BCK-001: Обновить ORM модели
**Приоритет**: High
**Зависимости**: TASK-INF-001

- Добавить `climate_zone` в `Region` model
- Добавить `spawn_periods_by_zone` в `FishBiteSettings` model

**Критерии приемки**:
- [ ] `Region` имеет `climate_zone = Column(String(10), default="central")`
- [ ] `FishBiteSettings` имеет `spawn_periods_by_zone = Column(JSONB, default={})`

### TASK-BCK-002: Добавить зональную логику в forecast_calculation.py
**Приоритет**: High
**Зависимости**: TASK-BCK-001

- Добавить `REGION_CODE_TO_ZONE` словарь
- Добавить `get_spawn_dates_for_zone(spawn_periods_by_zone, zone)` — возвращает `(start_month, end_month, start_day, end_day)` или None
- Добавить `get_climate_zone(region_code)` — возвращает 'south'/'central'/'north'

**Критерии приемки**:
- [ ] Функция `get_spawn_dates_for_zone` корректно извлекает зональные данные из JSONB
- [ ] Fallback на дефолтные spawn-колонки при отсутствии зональных данных
- [ ] `is_in_spawn_period()` НЕ изменяется — только входные данные

### TASK-BCK-003: Обновить seed_fish_settings.py
**Приоритет**: High
**Зависимости**: TASK-BCK-002

- Добавить `spawn_periods_by_zone` в каждый элемент `FISH_BITE_SETTINGS_DATA`
- Значения согласно таблице в разделе 3.4

**Критерии приемки**:
- [ ] Все 16 рыб с spawn имеют `spawn_periods_by_zone` с 3 зонами
- [ ] Лосось и Таймень имеют пустой `spawn_periods_by_zone`
- [ ] Seed корректно записывает JSONB в БД

### TASK-BCK-004: Обновить endpoint прогноза
**Приоритет**: High
**Зависимости**: TASK-BCK-002, TASK-BCK-003

- В `get_forecast()`: определить `climate_zone` региона (через region.code → zone)
- При создании `FishSettings`: использовать `get_spawn_dates_for_zone()` для подстановки зональных spawn-дат
- Реализовать fallback на стандартные spawn-колонки

**Критерии приемки**:
- [ ] Endpoint определяет зону региона по region.code
- [ ] `FishSettings` заполняется zone-specific spawn датами
- [ ] Если зона не найдена — fallback на дефолтные spawn-колонки
- [ ] `spawn_message` отражает зональные даты

### TASK-TST-001: Обновить тесты
**Приоритет**: High
**Зависимости**: TASK-BCK-002

- Добавить тесты `TestGetClimateZone` для маппинга region → zone
- Добавить тесты `TestGetSpawnDatesForZone` для извлечения зональных данных
- Добавить параметризованные тесты `TestIsInSpawnPeriodZoned` — для разных зон
- Обновить spawn_message проверки на зональные даты

**Критерии приемки**:
- [ ] Все новые функции покрыты тестами
- [ ] Все существующие тесты проходят
- [ ] `pytest services/forecast-service/tests/ -v` — зелёный

---

## 5. Риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Неточные зональные данные | Medium | Low | Легко обновить JSONB, не меняя код |
| Регион без climate_zone | Low | Medium | Fallback на дефолтные spawn-колонки |
| Версия кэша прогнозов не обновлена | Low | Medium | Обновить `ALGORITHM_VERSION` в endpoint |

---

## 6. Согласование

- [x] Заказчик
- [ ] Техлид

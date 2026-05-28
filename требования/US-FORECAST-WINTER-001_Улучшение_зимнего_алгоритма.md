# User Story: Улучшение зимнего алгоритма прогноза клева

**ID**: US-FORECAST-WINTER-001
**Version**: 1.0
**Author**: Business Analyst
**Date**: 2025-02-17
**Status**: Согласовано
**Priority**: High

---

## 1. Обзор

### 1.1. Описание

Улучшение алгоритма прогноза клева для более точного учета зимних условий и нерестовых периодов рыбы.

### 1.2. Проблема

Текущий алгоритм использует **бинарный зимний множитель** (1.2 или 0.3), который:
- Не различает периоды декабря, января, февраля
- Игнорирует фазы: первый лед → глухозимье → последний лед
- Не учитывает нерестовые периоды (когда клев минимальный)

### 1.3. Предлагаемое решение

1. **Градуированные зимние коэффициенты** по месяцам
2. **Учет нерестовых периодов** для каждого вида рыбы
3. **Предупреждения пользователя** о неблагоприятных периодах

---

## 2. User Story

**As a** рыболов,
**I want to** видеть точный прогноз клева с учетом зимних условий и нереста,
**So that** я могу планировать рыбалку в оптимальное время и не ехать зря в нерестовый период.

---

## 3. Actors

- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель
- [ ] Moderator
- [ ] Admin
- [x] System (автоматизированные процессы)

---

## 4. Acceptance Criteria

### AC1: Градуированные зимние коэффициенты

**Given** сегодня зимний месяц (декабрь/январь/февраль)
**When** система рассчитывает прогноз клева
**Then** применяется соответствующий месячный коэффициент:
- Декабрь (первый лед): 0.9 для активных рыб, 0.2 для неактивных
- Январь (глухозимье): 0.7 для активных рыб, 0.1 для неактивных
- Февраль (последний лед): 1.0 для активных рыб, 0.15 для неактивных

### AC2: Учет нерестовых периодов

**Given** сегодня период нереста для конкретного вида рыбы
**When** система рассчитывает прогноз клева
**Then** bite_score = 0 и отображается предупреждение "Нерестовый период — вылов запрещен"

### AC3: Отображение нерестового предупреждения в UI

**Given** пользователь просматривает прогноз на дату, совпадающую с нерестом
**When** отображается прогноз для рыбы в нересте
**Then** показывается:
- Иконка предупреждения (⚠️)
- Текст: "Нерест: [даты нереста] — вылов запрещен"
- bite_score заблокирован (0 или серый)

### AC4: Обратная совместимость

**Given** существующие настройки рыб без spawn периодов
**When** система рассчитывает прогноз
**Then** используется поведение по умолчанию (нерест не учитывается)

---

## 5. Database Schema Change

### 5.1. Изменение таблицы fish_bite_settings

```sql
-- Добавить поля для нерестового периода
ALTER TABLE fish_bite_settings
ADD COLUMN spawn_start_month INTEGER,
ADD COLUMN spawn_end_month INTEGER,
ADD COLUMN spawn_start_day INTEGER DEFAULT 1,
ADD COLUMN spawn_end_day INTEGER DEFAULT 31;

COMMENT ON COLUMN fish_bite_settings.spawn_start_month IS 'Месяц начала нереста (1-12), NULL если не применимо';
COMMENT ON COLUMN fish_bite_settings.spawn_end_month IS 'Месяц окончания нереста (1-12), NULL если не применимо';
COMMENT ON COLUMN fish_bite_settings.spawn_start_day IS 'День начала нереста (1-31)';
COMMENT ON COLUMN fish_bite_settings.spawn_end_day IS 'День окончания нереста (1-31)';
```

### 5.2. Rollback Script

```sql
ALTER TABLE fish_bite_settings
DROP COLUMN IF EXISTS spawn_start_month,
DROP COLUMN IF EXISTS spawn_end_month,
DROP COLUMN IF EXISTS spawn_start_day,
DROP COLUMN IF EXISTS spawn_end_day;
```

---

## 6. Seed Data: Нерестовые периоды по видам рыб

```sql
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
```

---

## 7. Обновленный алгоритм

### 7.1. Градуированные зимние коэффициенты

```python
WINTER_MONTHLY_MULTIPLIERS = {
    12: {'active_fish': 0.9, 'inactive_fish': 0.2},   # Декабрь - первый лед
    1:  {'active_fish': 0.7, 'inactive_fin': 0.1},    # Январь - глухозимье
    2:  {'active_fish': 1.0, 'inactive_fish': 0.15},  # Февраль - последний лед
}

def get_season_multiplier(fish: FishSettings, month: int) -> float:
    if month in [12, 1, 2]:
        multipliers = WINTER_MONTHLY_MULTIPLIERS[month]
        return multipliers['active_fish'] if fish.active_in_winter else multipliers['inactive_fish']
    return 1.0
```

### 7.2. Проверка нерестового периода

```python
def is_in_spawn_period(fish: FishSettings, date: date) -> bool:
    if fish.spawn_start_month is None or fish.spawn_end_month is None:
        return False
    
    month = date.month
    day = date.day
    
    start_month = fish.spawn_start_month
    end_month = fish.spawn_end_month
    
    if start_month <= end_month:
        return start_month == month and day >= fish.spawn_start_day or \
               end_month == month and day <= fish.spawn_end_day or \
               start_month < month < end_month
    else:
        return month >= start_month or month <= end_month


def calculate_bite_score(weather, fish, hour, month, date) -> dict:
    if is_in_spawn_period(fish, date):
        return {
            'bite_score': 0,
            'is_spawn_period': True,
            'spawn_message': f"Нерестовый период — вылов запрещен",
            'components': {},
        }
    
    # ... остальной расчет
```

### 7.3. Обновленная формула

```
bite_score = (
    temperature_score × 0.25 +
    pressure_score × 0.25 +
    time_of_day_score × 0.20 +
    wind_score × 0.15 +
    moon_score × 0.10 +
    precipitation_score × 0.05
) × season_multiplier × spawn_multiplier

где:
- season_multiplier = WINTER_MONTHLY_MULTIPLIERS[month] или 1.0
- spawn_multiplier = 0 если in_spawn_period, иначе 1.0
```

---

## 8. API Changes

### 8.1. Обновление ответа GET /api/v1/forecast/:region_id

```json
{
  "forecasts": [
    {
      "fish_type": {
        "id": "uuid",
        "name": "Щука"
      },
      "forecasts": [
        {
          "time_of_day": "morning",
          "bite_score": 0,
          "is_spawn_period": true,
          "spawn_period": {
            "start": "2025-03-01",
            "end": "2025-04-30",
            "message": "Нерестовый период — вылов запрещен"
          }
        }
      ]
    }
  ]
}
```

---

## 9. UI Requirements

### 9.1. Отображение нерестового периода

```
┌─────────────────────────────────────────────────────────────┐
│  🐟 Щука                                                    │
├─────────────────────────────────────────────────────────────┤
│  ⚠️ Нерестовый период                                       │
│  Период: 1 марта - 30 апреля                               │
│  Вылов запрещен                                             │
├─────────────────────────────────────────────────────────────┤
│  Оценка клева: — (нерест)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 9.2. Цветовая индикация

| Состояние | Цвет | Описание |
|-----------|------|----------|
| Нерест | 🔴 Красный фон | Вылов запрещен |
| Зима, неактивная рыба | ⚫ Серый | Клев маловероятен |
| Глухозимье (январь) | 🔵 Синий | Слабый клев |

---

## 10. Non-Functional Requirements

### 10.1. Performance
- Расчет spawn_multiplier: < 1ms (простая проверка дат)
- Общее время расчета: не увеличивается

### 10.2. Reliability
- Обратная совместимость: рыбы без spawn периодов работают как раньше
- NULL в spawn_start_month/end_month = нерест не учитывается

---

## 11. Dependencies

- Зависит от: `Требования_Прогноз_Клева_v1.0.md`
- Блокирует: нет

---

## 12. Definition of Done

- [ ] Database migration выполнена
- [ ] Seed данные добавлены
- [ ] Алгоритм обновлен (градуированные коэффициенты)
- [ ] Функция is_in_spawn_period реализована
- [ ] API возвращает spawn_period в ответе
- [ ] UI отображает нерестовые предупреждения
- [ ] Unit тесты написаны (покрытие ≥80%)
- [ ] Документация обновлена

---

## 13. Риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Неточные даты нереста | Medium | Medium | Добавить возможность настройки дат по регионам (Phase 2) |
| Региональные различия | High | Low | Документировать, что даты приблизительные |
| Breaking change в API | Low | Low | spawn_period опциональное поле |

---

## 14. Acceptance

**Согласовано**: 
- Заказчик: ✅ 2025-02-17
- Аналитик: ✅ 2025-02-17

**Комментарии**: Градуированный подход к зимним коэффициентам принят. Учет нерестовых периодов обязателен.

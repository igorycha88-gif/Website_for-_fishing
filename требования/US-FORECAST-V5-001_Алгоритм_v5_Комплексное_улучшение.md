# ЧТЗ: Алгоритм прогноза клёва v5 — Комплексное улучшение точности

**ID:** US-FORECAST-V5-001
**Версия:** 1.0
**Дата:** 2026-05-28
**Маршрут:** АНАЛИТИК → АРХИТЕКТОР → АНАЛИТИК → РАЗРАБОТЧИК → ТЕСТИРОВЩИК → DEVOPS
**Исполнитель:** Разработчик

---

## 1. Описание задачи

Комплексное улучшение алгоритма прогноза клёва FishMap (переход с v4 на v5) для повышения точности прогноза. Реализация 9 улучшений со средним и высоким приоритетом.

---

## 2. Источники данных

| # | Улучшение | Источник данных | Как подключаем |
|---|-----------|----------------|----------------|
| 1 | Температура воды | **Open-Meteo API** — бесплатный, без ключа. Endpoint: `https://api.open-meteo.com/v1/forecast?latitude=...&longitude=...&hourly=lake_mix_layer_temperature,soil_temperature_0_to_7cm` | Новый метод в `WeatherCollectorService._fetch_water_temperature()` |
| 2 | Обратная связь пользователей | **Собственные данные** — таблица `UserCatchReports` | Новый endpoint `POST /forecast/feedback` |
| 3 | Динамические границы времени суток | **Уже есть** — `sunrise`/`sunset` в `WeatherData` | Модификация `get_time_of_day()` |
| 4 | Pre/Post-spawn фазы | **Собственные данные** — расширение `FishBiteSettings` | Новые поля + модификация `is_in_spawn_period()` |
| 5 | Fish-specific moon preferences | **Собственные данные** — новое поле `moon_phase_preference` | Модификация `calculate_moon_score()` |
| 6 | Wind gust + turbidity | **Уже есть** — `wind_gust` в `WeatherData` (сохраняется, не используется) | Модификация `calculate_wind_score()` |
| 7 | UV-индекс | **Open-Meteo API** — `uv_index` в hourly данных | Модификация `weather_collector.py` |
| 8 | Тип осадков | **Уже есть** — `weather_condition` в `WeatherData` | Модификация `calculate_precipitation_score()` |
| 9 | Гидрология (оценка уровня воды) | **Эмпирическая модель** — на основе накопленных осадков за 7 дней из `weather_data` | Новый метод `calculate_water_level_score()` |

---

## 3. Детальные требования по каждому улучшению

### 3.1. Температура воды (оценка)

**Проблема:** Используется температура воздуха. Рыба реагирует на температуру ВОДЫ, которая отличается на 3-10°C.

**Решение:**
- Запрос к Open-Meteo API для получения `lake_mix_layer_temperature` (температура поверхностного слоя воды)
- Если Open-Meteo недоступен — использовать эмпирическую формулу:
  ```python
  water_temp = air_temp_avg_3d * 0.6 + air_temp * 0.4 - seasonal_offset
  # seasonal_offset: spring=3, summer=2, autumn=2, winter=5
  ```
- Добавить колонку `water_temperature` в `WeatherData`
- Модифицировать `calculate_temperature_score()` — использовать water_temperature вместо air temperature
- Сохранять air temperature для отображения пользователю

**Файлы:** `weather_collector.py`, `forecast_calculation.py`, `models/forecast.py`, `database/schema.sql`

**Внешний API:** Open-Meteo (бесплатный, 10000 запросов/день)
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude=55.75&longitude=37.62
  &hourly=lake_mix_layer_temperature,soil_temperature_0_to_7cm
  &forecast_days=4
```

---

### 3.2. Обратная связь пользователей (ML feedback loop)

**Проблема:** Алгоритм чисто эвристический, нет проверки реальной точности.

**Решение:**
- Новая таблица `user_catch_reports`:
  ```sql
  CREATE TABLE user_catch_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    time_of_day VARCHAR(20) NOT NULL,
    actual_bite BOOLEAN NOT NULL,        -- клевало или нет
    bite_count INTEGER,                  -- сколько поймал (опционально)
    predicted_score INTEGER,             -- какой прогноз был
    weather_temperature DECIMAL(5,2),    -- зафиксировать погоду на момент
    weather_pressure INTEGER,
    weather_wind_speed DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```
- Новый endpoint: `POST /forecast/feedback` — принимает отчёт пользователя
- Новый endpoint: `GET /forecast/accuracy` — возвращает статистику точности (для аналитики)
- Лёгкая корректировка: `accuracy_adjustment` — множитель, рассчитываемый из отношения predicted_score к actual_bite по последним 100 отчётам для каждой рыбы в регионе
- В `calculate_bite_score()` — добавить финальный шаг: `bite_score *= accuracy_adjustment`

**Файлы:** `models/forecast.py`, `endpoints/forecast.py`, `forecast_calculation.py`, `schemas/forecast.py`

**Данные:** Собственные (пользователи отправляют через UI)

---

### 3.3. Динамические границы времени суток

**Проблема:** Фиксированные границы (6-10, 10-17, 17-21, 21-6) не учитывают реальный sunrise/sunset.

**Решение:**
- Модифицировать `get_time_of_day()` → `get_time_of_day_dynamic(hour, sunrise, sunset)`:
  ```python
  morning:  sunrise - 1h  →  sunrise + 2h
  day:      sunrise + 2h  →  sunset - 2h
  evening:  sunset - 2h   →  sunset + 1h
  night:    всё остальное
  ```
- Если sunrise/sunset = None — fallback на текущие фиксированные границы
- Использовать `weather.sunrise` / `weather.sunset` из `WeatherConditions`

**Файлы:** `forecast_calculation.py`, `endpoints/forecast.py` (передача sunrise/sunset)

---

### 3.4. Pre-spawn / Post-spawn фазы

**Проблема:** Только spawn ban (score=0). Нет учёта преднерестового жора (peak activity) и посленерестового восстановления (low activity).

**Решение:**
- Расширить `FishBiteSettings`:
  - `pre_spawn_days` (INTEGER, default=14) — за сколько дней до нереста начинается жор
  - `post_spawn_days` (INTEGER, default=5) — сколько дней после нереста рыба болеет
- Новая функция `get_spawn_phase()` → возвращает: `pre_spawn`, `spawn`, `post_spawn`, `normal`
- В `calculate_bite_score()`:
  - `pre_spawn` → `bite_score *= 1.3` (жор, максимальная активность)
  - `spawn` → `bite_score = 0` (запрет)
  - `post_spawn` → `bite_score *= 0.5` (рыба восстанавливается)
  - `normal` → без изменений

**Файлы:** `models/forecast.py`, `seed_fish_settings.py`, `forecast_calculation.py`

---

### 3.5. Fish-specific moon preferences

**Проблема:** Все рыбы одинаково реагируют на луну. Но хищники активнее в полнолуние, мирная рыба — в новолуние.

**Решение:**
- Добавить поле `moon_phase_preference` в `FishBiteSettings`:
  - `'new_moon'` — рыба активнее при новолунии (лещ, плотва, карась, налим)
  - `'full_moon'` — рыба активнее при полнолунии (щука, судак, окунь, сом, жерех)
  - `'both'` — оба экстремума дают активность
  - `'neutral'` — луна не влияет дополнительно (default)
- Модифицировать `calculate_moon_score()`:
  ```python
  if preference == 'new_moon':
      # Бонус при фазе ближе к 0.0 (новолуние)
      bonus = (1.0 - min_distance_from_new_moon) * 20
  elif preference == 'full_moon':
      # Бонус при фазе ближе к 0.5 (полнолуние)
      bonus = (1.0 - min_distance_from_full_moon) * 20
  elif preference == 'both':
      bonus = (1.0 - min_distance_from_either) * 15
  ```

**Файлы:** `models/forecast.py`, `seed_fish_settings.py`, `forecast_calculation.py`

---

### 3.6. Wind gust + turbidity

**Проблема:** `wind_gust` сохраняется в БД, но не используется. Нет учёта порывов и мути воды.

**Решение:**
- Добавить `wind_gust` в `WeatherConditions`
- Модифицировать `calculate_wind_score()`:
  ```python
  # Учитываем порывы
  if wind_gust:
      gust_ratio = wind_gust / max_wind
      if gust_ratio > 2.0:
          base_score *= 0.6  # Очень сильные порывы
      elif gust_ratio > 1.5:
          base_score *= 0.8
  ```
- Добавить `calculate_turbidity_score()`:
  ```python
  # Мутность воды = f(wind_speed, wind_direction, precipitation)
  # Ветер с берега → больше мути в прибрежной зоне
  turbidity = wind_speed * (1 + precipitation_factor)
  if turbidity > 15:
      # Мутная вода — бонус для сома, налима, леща
      # Штраф для форели, хариуса (видовых рыб)
  ```
- Добавить поле `turbidity_sensitive` в `FishBiteSettings` (bool)

**Файлы:** `forecast_calculation.py`, `models/forecast.py`, `seed_fish_settings.py`, `endpoints/forecast.py`

---

### 3.7. UV-индекс

**Проблема:** `uv_index` в модели = всегда None. Не собирается, не используется.

**Решение:**
- Добавить запрос UV в Open-Meteo (вместе с температурой воды):
  ```
  &hourly=uv_index
  ```
- Сохранять в `WeatherData.uv_index`
- Новый метод `calculate_uv_score()`:
  ```python
  # Высокий UV → рыба уходит на глубину
  if uv > 8:  score = 30   # Очень высокий — плохо для поверхности
  elif uv > 6: score = 50
  elif uv > 3: score = 75  # Умеренный — нормально
  else:        score = 90  # Низкий — отлично (пасмурно/рассвет/закат)
  ```
- Добавить `uv_sensitivity` в `FishBiteSettings` (Decimal, 0.0-1.0)
- UV score как множитель: `bite_score *= (uv_score / 100) ^ uv_sensitivity`

**Файлы:** `weather_collector.py`, `forecast_calculation.py`

---

### 3.8. Тип осадков

**Проблема:** `calculate_precipitation_score()` учитывает только mm осадков, но не тип (дождь/снег/гроза/град).

**Решение:**
- Модифицировать `calculate_precipitation_score()`:
  ```python
  weather_condition_modifiers = {
      'Thunderstorm': 0.3,    # Гроза — рыба уходит на глубину
      'Snow':          0.6,   # Снег — средний клёв
      'Rain':          0.9,   # Дождь — хороший клёв (насыщает кислородом)
      'Drizzle':       0.95,  # Мелкий дождь — отличный клёв
      'Clear':         0.85,  # Ясно — нормальный
      'Clouds':        0.9,   # Облачно — хорошо
      'Mist':          0.8,   # Туман — снижает видимость приманок
      'Fog':           0.75,
  }
  ```
- Принимать `weather_condition` в `WeatherConditions` и `calculate_precipitation_score()`

**Файлы:** `forecast_calculation.py`, `endpoints/forecast.py`

---

### 3.9. Гидрология — оценка уровня воды

**Проблема:** Нет учёта уровня воды. Паводок = слабый клёв, стабильный уровень = нормальный.

**Решение:**
- Эмпирическая модель на основе накопленных осадков:
  ```python
  # Собрать осадки за последние 7 дней для региона
  total_precip_7d = sum(precipitation_mm for last 7 days)
  
  # Уровень воды (оценка)
  # Весенний паводок: March-May → выше baseline
  # Осенний паводок: September-November → выше baseline
  
  seasonal_factor = {
      'spring': 2.5,   # Таяние снега + дожди
      'summer': 1.0,
      'autumn': 1.8,   # Осенние дожди
      'winter': 0.5,   # Лёд, мало осадков
  }
  
  water_level_index = total_precip_7d * seasonal_factor
  
  if water_level_index > 50:  score = 30   # Паводок — плохо
  elif water_level_index > 30: score = 50  # Высокий уровень — средне
  elif water_level_index > 10: score = 80  # Нормальный — хорошо
  else:                        score = 90  # Стабильный — отлично
  ```
- Новый метод `calculate_water_level_score()`
- Добавить `water_level_sensitivity` в `FishBiteSettings`
- Water level score как множитель

**Файлы:** `forecast_calculation.py`, `endpoints/forecast.py`, `models/forecast.py`

---

## 4. Декомпозиция задач

### TASK-V5-001 — Модель данных (BCK)
- Добавить колонки в `WeatherData`: `water_temperature`
- Добавить поля в `FishBiteSettings`: `pre_spawn_days`, `post_spawn_days`, `moon_phase_preference`, `turbidity_sensitive`, `uv_sensitivity`, `water_level_sensitivity`
- Создать таблицу `user_catch_reports`
- Обновить `seed_fish_settings.py` со значениями для всех 19 рыб
- Обновить `database/schema.sql`

### TASK-V5-002 — Температура воды (BCK)
- Добавить `_fetch_water_temperature()` в `weather_collector.py` (Open-Meteo API)
- Сохранять `water_temperature` в `WeatherData`
- Модифицировать `calculate_temperature_score()` — использовать water_temperature
- Fallback на эмпирическую формулу при недоступности API

### TASK-V5-003 — Динамические границы времени суток (BCK)
- Модифицировать `get_time_of_day()` → `get_time_of_day_dynamic(hour, sunrise, sunset)`
- Обновить вызовы в `forecast_calculation.py` и `endpoints/forecast.py`

### TASK-V5-004 — Pre/Post-spawn фазы (BCK)
- Добавить `get_spawn_phase()` в `forecast_calculation.py`
- Модифицировать `calculate_bite_score()` — множители для фаз

### TASK-V5-005 — Fish-specific moon preferences (BCK)
- Модифицировать `calculate_moon_score()` — учитывать `moon_phase_preference`

### TASK-V5-006 — Wind gust + turbidity (BCK)
- Модифицировать `calculate_wind_score()` — учитывать `wind_gust`
- Добавить `calculate_turbidity_score()`

### TASK-V5-007 — UV-индекс (BCK)
- Собирать UV из Open-Meteo в `weather_collector.py`
- Добавить `calculate_uv_score()` в `forecast_calculation.py`

### TASK-V5-008 — Тип осадков (BCK)
- Модифицировать `calculate_precipitation_score()` — учитывать `weather_condition`
- Передавать `weather_condition` в `WeatherConditions`

### TASK-V5-009 — Гидрология (BCK)
- Добавить `calculate_water_level_score()` в `forecast_calculation.py`
- Query осадков за 7 дней из `WeatherData`

### TASK-V5-010 — Обратная связь пользователей (BCK)
- Новый endpoint `POST /forecast/feedback`
- Новый endpoint `GET /forecast/accuracy`
- Расчёт `accuracy_adjustment` в `calculate_bite_score()`

### TASK-V5-011 — Интеграция всех факторов в итоговую формулу (BCK)
- Обновить `calculate_bite_score()` — итоговая формула v5:
  ```python
  # Core factors (geometric mean)
  base = geometric_mean(water_temp_score, pressure_score)
  
  # Synergy modifiers
  solunar_synergy, temp_pressure_synergy, stability_mult
  
  # Time modifier (dynamic boundaries)
  time_adjusted (with solunar bonus)
  
  # Environmental caps
  wind_cap = wind_score / 100 (with gust factor)
  precip_cap = precip_score / 100 (with weather_condition)
  uv_cap = uv_score / 100 (with fish sensitivity)
  turbidity_cap = turbidity_score / 100
  water_level_cap = water_level_score / 100
  
  # Phase modifier (pre-spawn boost / post-spawn penalty)
  phase_mult = get_phase_multiplier(spawn_phase)
  
  # Accuracy adjustment (ML feedback)
  accuracy_adj = get_accuracy_adjustment(fish_type_id, region_id)
  
  bite_score = base * solunar_synergy * temp_pressure_synergy * stability_mult
               * (time_adjusted / 100) * wind_cap * precip_cap * uv_cap
               * turbidity_cap * water_level_cap * phase_mult * accuracy_adj
  
  # Season
  bite_score *= season_mult
  ```
- Обновить `ALGORITHM_VERSION = "v5"`

### TASK-V5-012 — Frontend: UI для обратной связи (FRT)
- Добавить кнопку «Как прошёл клёв?» в карточку прогноза
- Модальное окно: клюёт/не клюёт, сколько поймано
- Отправка `POST /forecast/feedback`

### TASK-V5-013 — Unit-тесты (BCK)
- Тесты для каждого нового `calculate_*_score()`
- Тесты для `get_spawn_phase()`
- Тесты для `get_time_of_day_dynamic()`
- Тесты для feedback endpoint
- Тесты для Open-Meteo интеграции (mock)

### TASK-V5-014 — E2E-тесты (FRT)
- Playwright: пользователь отправляет feedback
- Playwright: прогноз отображает корректные данные v5

---

## 5. Критерии приёмки

1. ✅ Температура воды получается из Open-Meteo API, fallback на эмпирическую формулу
2. ✅ Границы времени суток динамические (на основе sunrise/sunset)
3. ✅ Pre-spawn даёт бонус ×1.3, post-spawn штраф ×0.5
4. ✅ Moon preferences: 19 рыб имеют корректный `moon_phase_preference`
5. ✅ Wind gust учитывается в wind_score
6. ✅ UV-индекс собирается и влияет на bite_score
7. ✅ Тип осадков (Thunderstorm/Rain/Drizzle/etc.) модифицирует precip_score
8. ✅ Уровень воды оценивается по осадкам за 7 дней
9. ✅ Endpoint `POST /forecast/feedback` работает и сохраняет отчёты
10. ✅ `ALGORITHM_VERSION = "v5"` — кэш инвалидируется
11. ✅ Все unit-тесты проходят (`pytest`)
12. ✅ Ruff lint чистый
13. ✅ E2E-тесты (Playwright) проходят
14. ✅ Structlog логи на всех новых endpoints

---

## 6. Влияние на файлы

### Backend (forecast-service):
- `app/models/forecast.py` — новые поля, новая таблица
- `app/services/forecast_calculation.py` — ядро алгоритма (основные изменения)
- `app/services/weather_collector.py` — Open-Meteo интеграция, UV, water temp
- `app/services/weather.py` — добавление water temp fetch
- `app/endpoints/forecast.py` — feedback endpoints, передача новых данных
- `app/schemas/forecast.py` — новые схемы
- `app/seed_fish_settings.py` — обновление сид-данных
- `app/core/config.py` — OPEN_METEO_BASE_URL

### Frontend:
- `frontend/types/forecast.ts` — новые типы
- Компонент формы обратной связи (новый)

### Infrastructure:
- `database/schema.sql` — новые колонки, новая таблица
- `docker-compose.dev.yml` — без изменений

---

## 7. Риски

| Риск | Митигация |
|------|-----------|
| Open-Meteo API недоступен | Fallback на эмпирическую формулу для water temp |
| Open-Meteo нет данных для региона | Использовать soil_temperature как approximation |
| Недостаточно feedback для ML | Минимум 10 отчётов для включения accuracy_adj, иначе = 1.0 |
| Регрессия текущих прогнозов | Сохранить v4 как fallback, A/B тестирование |

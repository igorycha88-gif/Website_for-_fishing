# ЧТЗ: Улучшение алгоритма прогноза клёва v3.0 — Луна, Давление, Нелинейная модель

**ID:** US-FORECAST-ALGORITHM-007
**Приоритет:** Высокий
**Маршрут:** Аналитик → Разработчик → Тестировщик → DevOps
**Исполнитель:** Разработчик (Fullstack)

---

## 1. Контекст и проблема

### Текущее состояние (v2.0)
Алгоритм прогноза клёва использует **линейную взвешенную модель** из 6 факторов:
- Температура (25%) + Давление (25%) + Время суток (20%) + Ветер (15%) + Луна (10%) + Осадки (5%)
- Базовый балл умножается на сезонный коэффициент (зима)

### Критические проблемы
1. **Фаза луны = мёртвый код** — OpenWeatherMap `/forecast` НЕ возвращает `moon_phase`. Коллектор ставит `None` → балл луны всегда 50/100. Вес 10% впустую.
2. **Тренд давления = мёртвый код** — `pressure_trend` всегда = 0, никто не вычисляет разницу между замерами. Бонусы/штрафы (+15/+8/-10/-20) не работают.
3. **Линейная модель** — факторы складываются, но в реальности взаимодействуют нелинейно (идеальное давление + полнолуние = синергия, а не сумма).
4. **Нет Solunar periods** — не учитываются major/minor периоды (время пикового клёва в течение дня).

---

## 2. Цель

Создать алгоритм v3.0, который:
- Реально считает фазу луны через астрономическую библиотеку `ephem`
- Вычисляет тренд и стабильность давления из исторических данных
- Определяет Solunar major/minor периоды (часы пикового клёва)
- Использует мультипликативную (нелинейную) модель взаимодействия факторов
- Учитывает сезонную адаптацию лунной чувствительности

---

## 3. Функциональные требования

### 3.1. Калькулятор фазы луны (библиотека `ephem`)

**FR-3.1.1** Добавить зависимость `ephem` в `requirements.txt`

**FR-3.1.2** Создать модуль `app/services/moon_calculation.py` с функциями:
- `calculate_moon_phase(date: date, lat: float, lon: float) -> MoonData`
  - Возвращает: `phase` (0.0-1.0), `phase_name` (str), `illumination` (0-100%)
- `calculate_solunar_periods(date: date, lat: float, lon: float) -> SolunarData`
  - Возвращает: список major periods (по 2 штуки, ~2ч каждый) и minor periods (по 2 штуки, ~1ч каждый)
  - Каждый период: `start: time`, `end: time`, `type: "major"|"minor"`, `strength: float (0-1)`

**FR-3.1.3** Алгоритм расчёта фазы через `ephem`:
```python
import ephem
observer = ephem.Observer()
observer.lat = str(lat)
observer.lon = str(lon)
observer.date = ephem.Date(datetime)
moon = ephem.Moon(observer)
phase = moon.moon_phase  # 0.0 - 1.0 (0=new, 0.5=full)
next_new = ephem.next_new_moon(observer.date)
next_full = ephem.next_full_moon(observer.date)
prev_new = ephem.previous_new_moon(observer.date)
prev_full = ephem.previous_full_moon(observer.date)
```

**FR-3.1.4** Расчёт Solunar periods через `ephem`:
- **Major period** = когда луна находится в верхней кульминации (транзит) или нижней кульминации (надир). Длительность ~2 часа (1ч до + 1ч после)
- **Minor period** = восход или заход луны. Длительность ~1 час (30мин до + 30мин после)
- Расчёт:
  - `moon_next_rising(observer)` / `moon_next_setting(observer)` → minor periods
  - `moon_transit_time` (вычисляется как среднее между rising и setting) → major period
  - `moon_antitransit_time` (середина между setting и следующим rising) → major period

**FR-3.1.5** Обновить `weather_collector.py` — при сохранении погодных данных вычислять `moon_phase` через `ephem` вместо `None`

### 3.2. Расчёт тренда давления

**FR-3.2.1** Создать функцию `calculate_pressure_trend(weather_records: List[WeatherData], current_hour: int) -> PressureTrend` в `app/services/forecast_calculation.py`

**FR-3.2.2** `PressureTrend` — dataclass с полями:
- `trend_3h: float` — изменение давления за последние 3 часа (мм рт.ст.)
- `trend_6h: float` — за 6 часов
- `trend_12h: float` — за 12 часов
- `trend_24h: float` — за 24 часа
- `stability: float` — стабильность (0-1), где 1 = идеально стабильное. Считается как `1.0 - min(1.0, std_deviation / 5.0)`
- `rate_of_change: float` — скорость изменения (мм рт.ст./час)
- `direction: str` — "rising" / "falling" / "stable"

**FR-3.2.2** Логика расчёта:
- Извлечь из `weather_data` записи за последние 24 часа для данного региона
- Для каждого интервала (3ч, 6ч, 12ч, 24ч): `trend = current_pressure - pressure_N_hours_ago`
- Перевести hPa → мм рт.ст. (коэффициент 0.750062)
- `stability` = `1.0 - min(1.0, standard_deviation(all_pressures_24h) / 5.0)`
- `rate_of_change` = `trend_3h / 3.0`
- `direction`: если `|rate_of_change| < 0.5` → "stable", иначе "rising"/"falling"

**FR-3.2.3** Обновить `WeatherConditions` dataclass:
- Добавить поле `pressure_trend_data: Optional[PressureTrend] = None`

### 3.3. Нелинейная (мультипликативная) модель

**FR-3.3.1** Заменить линейную формулу на мультипликативную:

**Старая формула (v2.0):**
```
bite = temp*0.25 + pressure*0.25 + time*0.20 + wind*0.15 + moon*0.10 + precip*0.05
bite *= season_multiplier
```

**Новая формула (v3.0):**
```
base = geometric_mean(temp_score, pressure_score)  # основные факторы

# Взаимодействие давления и луны (Solunar synergy)
solunar_synergy = 1.0 + 0.15 * (moon_score / 100) * (pressure_score / 100)

# Взаимодействие давления и температуры
temp_pressure_synergy = 1.0
if pressure_score >= 70 and temp_score >= 70:
    temp_pressure_synergy = 1.10  # бонус 10% за оба идеальных
elif pressure_score < 40 or temp_score < 40:
    temp_pressure_synergy = 0.85  # штраф если хотя бы один плохой

# Время суток с учётом Solunar periods
time_adjusted = time_score
if is_solunar_major_period:
    time_adjusted = min(100, time_score * 1.25)
elif is_solunar_minor_period:
    time_adjusted = min(100, time_score * 1.10)

# Стабильность давления — модификатор
stability_mult = 0.85 + 0.15 * stability  # 0.85 при нестабильном, 1.0 при стабильном

# Ветер и осадки — ограничивающие факторы (cap)
wind_cap = wind_score / 100  # 0-1
precip_cap = precip_score / 100  # 0-1

# Итоговая формула
bite = base * solunar_synergy * temp_pressure_synergy * stability_mult
bite = bite * (time_adjusted / 100) * wind_cap * precip_cap
bite *= season_multiplier
bite = clamp(0, 100)
```

**FR-3.3.2** Геометрическое среднее для основных факторов:
```python
import math
def geometric_mean(*scores: float) -> float:
    scores_clamped = [max(1.0, s) for s in scores]
    return math.exp(sum(math.log(s) for s in scores_clamped) / len(scores_clamped))
```

**FR-3.3.3** Пороговые функции для давления:
- Если `|rate_of_change| > 2.0 мм/ч` → `pressure_score *= 0.7` (резкий скачок = плохо)
- Если `stability >= 0.8` → `pressure_score *= 1.1` (стабильное = бонус)
- Если `stability < 0.3` → `pressure_score *= 0.8` (нестабильное = штраф)

### 3.4. Обновление функции лунного скоринга

**FR-3.4.1** Новая формула `calculate_moon_score_v3`:
```python
def calculate_moon_score_v3(
    moon_phase: float,
    moon_sensitivity: float,
    is_in_solunar_period: bool = False,
    solunar_strength: float = 0.0,
    season: str = "summer"
) -> float:
    # Базовый балл по фазе (бимодальный: новолуние и полнолуние — пики)
    distances = [abs(moon_phase - 0.0), abs(moon_phase - 0.5), abs(moon_phase - 1.0)]
    min_distance = min(distances)
    phase_score = 100.0 - min_distance * 300  # более плавная кривая
    phase_score = max(10.0, min(100.0, phase_score))

    # Сезонная адаптация чувствительности
    season_multiplier = {
        "spring": 1.0,
        "summer": 0.8,  # летом луна влияет меньше (длинный день)
        "autumn": 1.2,  # осенью влияние сильнее
        "winter": 1.3,  # зимой максимальное влияние (короткий день)
    }.get(season, 1.0)

    effective_sensitivity = min(1.0, moon_sensitivity * season_multiplier)

    # Базовый балл с учётом чувствительности
    base = 50.0 + (phase_score - 50.0) * effective_sensitivity

    # Бонус за попадание в Solunar period
    if is_in_solunar_period:
        base = min(100.0, base + 20 * solunar_strength)

    return max(0.0, min(100.0, base))
```

### 3.5. Обновление функции скоринга давления

**FR-3.5.1** Новая формула `calculate_pressure_score_v3`:
```python
def calculate_pressure_score_v3(
    pressure_hpa: Optional[int],
    fish: FishSettings,
    trend_data: Optional[PressureTrend] = None
) -> float:
    if pressure_hpa is None:
        return 50.0

    pressure_mmhg = pressure_hpa * 0.750062
    opt_min = fish.optimal_pressure_min
    opt_max = fish.optimal_pressure_max

    # Базовый балл за абсолютное значение
    if opt_min <= pressure_mmhg <= opt_max:
        base_score = 100.0
    else:
        deviation = min(abs(pressure_mmhg - opt_min), abs(pressure_mmhg - opt_max))
        base_score = max(0.0, 100.0 - deviation * 3)

    # Модификаторы тренда
    if trend_data:
        # Скорость изменения
        rate = trend_data.rate_of_change
        if abs(rate) > 2.0:  # резкий скачок
            base_score *= 0.7
        elif abs(rate) > 1.0:  # умеренное изменение
            base_score *= 0.9

        # Стабильность
        if trend_data.stability >= 0.8:
            base_score *= 1.1
        elif trend_data.stability < 0.3:
            base_score *= 0.8

        # Направление (плавный рост = хорошо для белой рыбы, падение = для хищников)
        if trend_data.direction == "stable":
            base_score *= 1.05

    return max(0.0, min(100.0, base_score))
```

### 3.6. Обновление API и структур данных

**FR-3.6.1** Новые поля в ответе прогноза (`TimeOfDayForecast`):
- `solunar_periods: Optional[List[SolunarPeriod]]` — Solunar периоды для данного времени суток
- `pressure_trend_direction: Optional[str]` — "rising" / "falling" / "stable"
- `pressure_stability: Optional[float]` — стабильность давления (0-1)
- `is_solunar_peak: Optional[bool]` — попадает ли период в Solunar peak

**FR-3.6.2** Новые поля в `WeatherSummaryResponse`:
- `moon_phase_name: Optional[str]` — название фазы луны ("Новолуние", "Полнолуние" и т.д.)
- `moon_illumination: Optional[float]` — освещённость луны (%)
- `solunar_periods: Optional[List[SolunarPeriod]]` — все Solunar периоды дня

**FR-3.6.3** Новая схема `SolunarPeriod`:
```python
class SolunarPeriod(BaseModel):
    start: str  # "HH:MM"
    end: str    # "HH:MM"
    type: str   # "major" | "minor"
    strength: float  # 0.0-1.0
```

**FR-3.6.4** Новая схема `WeatherConditions` (dataclass):
- Добавить `pressure_trend_data: Optional[PressureTrend] = None`
- Добавить `is_solunar_major: bool = False`
- Добавить `is_solunar_minor: bool = False`
- Добавить `solunar_strength: float = 0.0`

### 3.7. Обновление рекомендаций

**FR-3.7.1** Обновить `generate_recommendation()` с новыми факторами:
- Давление стабильное: "Стабильное давление — отличные условия"
- Давление нестабильное: "Давление нестабильно — рыба может быть осторожной"
- Резкий скачок: "Резкое изменение давления — клёв снижен"
- Solunar major period: "Solunar major period — пиковая активность в HH:MM-HH:MM"
- Solunar minor period: "Solunar minor period — умеренная активность в HH:MM-HH:MM"
- Новолуние: "Новолуние — ночная рыбалка может быть очень удачной"
- Полнолуние: "Полнолуние — рыба может кормиться всю ночь"

### 3.8. Обновление рекомендаций по фронтенду

**FR-3.8.1** Обновить типы в `frontend/types/forecast.ts`:
- Добавить интерфейс `SolunarPeriod`
- Добавить поля в `TimeOfDayForecast`: `solunar_periods`, `pressure_trend_direction`, `pressure_stability`, `is_solunar_peak`
- Добавить поля в `WeatherSummary`: `moon_phase_name`, `moon_illumination`, `solunar_periods`

**FR-3.8.2** Обновить UI в `FishingForecast.tsx`:
- Показывать Solunar периоды на временной шкале (визуальные маркеры)
- Обновить tooltip луны с названием фазы и освещённостью
- Показывать тренд давления (стрелка ↑/↓/—) рядом с давлением
- Показывать иконку Solunar пика рядом со временем суток

---

## 4. Структура файлов (изменения)

### Backend (`services/forecast-service/`)

| Файл | Действие | Описание |
|------|----------|----------|
| `requirements.txt` | Изменить | Добавить `ephem` |
| `app/services/moon_calculation.py` | **Создать** | Калькулятор луны + Solunar periods |
| `app/services/forecast_calculation.py` | Изменить | Новая мультипликативная модель v3.0 |
| `app/services/weather_collector.py` | Изменить | Заполнять `moon_phase` через `ephem` |
| `app/endpoints/forecast.py` | Изменить | Передавать тренд давления + Solunar данные |
| `app/schemas/forecast.py` | Изменить | Новые поля в ответах |
| `tests/test_moon_calculation.py` | **Создать** | Тесты лунного калькулятора |
| `tests/test_forecast_calculation.py` | Изменить | Обновить тесты под v3.0 |

### Frontend (`frontend/`)

| Файл | Действие | Описание |
|------|----------|----------|
| `types/forecast.ts` | Изменить | Новые типы для Solunar, давления |
| `components/FishingForecast.tsx` | Изменить | UI для Solunar, тренд давления |

### Database

| Объект | Действие | Описание |
|--------|----------|----------|
| `weather_data.moon_phase` | Без изменений | Заполняется через `ephem` вместо `None` |

---

## 5. Декомпозиция задач

### TASK-BCK-001: Модуль расчёта луны (`moon_calculation.py`)
- Установить `ephem`
- Реализовать `calculate_moon_phase()`
- Реализовать `calculate_solunar_periods()`
- Написать тесты `test_moon_calculation.py`

### TASK-BCK-002: Обновление коллектора погоды
- Заполнять `moon_phase` при сборе данных через `ephem`
- Передавать lat/lon региона

### TASK-BCK-003: Расчёт тренда давления
- Создать `PressureTrend` dataclass
- Реализовать `calculate_pressure_trend()`
- Обновить `_get_average_weather()` для передачи тренда

### TASK-BCK-004: Нелинейная модель v3.0
- Переписать `calculate_bite_score()` на мультипликативную формулу
- Обновить `calculate_moon_score()` → `calculate_moon_score_v3()`
- Обновить `calculate_pressure_score()` → `calculate_pressure_score_v3()`
- Обновить `generate_recommendation()`

### TASK-BCK-005: Обновление API схем и эндпоинтов
- Новые Pydantic схемы (`SolunarPeriod`, обновлённые `TimeOfDayForecast`, `WeatherSummaryResponse`)
- Передача Solunar данных и тренда давления в ответе
- Обновить кэш-ключи (добавить версию алгоритма)

### TASK-FRT-001: Обновление фронтенд типов и UI
- Обновить `types/forecast.ts`
- Показывать Solunar периоды в UI
- Показывать тренд давления
- Обновить tooltip луны

---

## 6. Критерии приёмки

### AC-1: Фаза луны работает
- [ ] `moon_phase` в `weather_data` заполняется реальными значениями (0.0-1.0)
- [ ] Проверка на известных датах: 2024-01-11 ≈ новолуние (0.0), 2024-01-25 ≈ полнолуние (0.5)
- [ ] `moon_score` в прогнозе отличен от 50.0 для всех видов рыб

### AC-2: Тренд давления работает
- [ ] При наличии данных за 24ч — `pressure_trend` содержит ненулевые значения
- [ ] При резком падении давления (>2 мм/ч) — `pressure_score` снижен на ≥25%
- [ ] При стабильном давлении (std < 2 мм) — `pressure_score` повышен на 10%

### AC-3: Solunar periods
- [ ] API возвращает 2 major и 2 minor периода для каждого дня
- [ ] Major периоды попадают в окно транзита/надира луны
- [ ] Minor периоды попадают в окно восхода/захода луны
- [ ] Длительность major: ~2ч, minor: ~1ч

### AC-4: Мультипликативная модель
- [ ] При идеальных условиях (все факторы ≥90) итоговый балл ≥85
- [ ] При одном плохом факторе (<30) итоговый балл снижен显著 (>30% от максимума)
- [ ] Синергия давление+луна: при обоих ≥80 балл на 15% выше чем при средних
- [ ] Нерестовый период: bite_score = 0 (без изменений)

### AC-5: Регрессия
- [ ] Все существующие тесты проходят (после адаптации под v3.0)
- [ ] API контракт обратно совместим (старые поля на месте, новые опциональны)
- [ ] Кэш инвалидирован (новые ключи с версией)

### AC-6: Качество кода
- [ ] `ruff check services/forecast-service/` — без ошибок
- [ ] `pytest services/forecast-service/tests/ -v` — все тесты зелёные
- [ ] Coverage ≥ 80% для новых модулей

---

## 7. Ограничения и риски

| Риск | Митигация |
|------|-----------|
| `ephem` может давать неточности для высоких широт (>65°) | Добавить проверку и fallback на аппроксимацию |
| Нет исторических данных давления для тренда | Если данных за 24ч нет — trend = None, модель деградирует до v2.0 |
| Мультипликативная модель может давать крайние значения | Жёсткий clamp [0, 100] + sanity-тесты |
| Изменение модели → другие баллы для тех же условий | Это ожидаемо, но нужно инвалидировать кэш |

---

## 8. Зависимости

- `ephem` — астрономическая библиотека (BSD лицензия, стабильная)
- Существующие данные в `weather_data` (нужны для расчёта тренда давления)
- Lat/Lon региона (уже есть в таблице `regions`)

---

## 9. Оценка трудозатрат

| Задача | Часы |
|--------|------|
| TASK-BCK-001: Лунный калькулятор | 3 |
| TASK-BCK-002: Обновление коллектора | 1 |
| TASK-BCK-003: Тренд давления | 2 |
| TASK-BCK-004: Мультипликативная модель | 4 |
| TASK-BCK-005: API схемы | 2 |
| TASK-FRT-001: Фронтенд | 3 |
| Тесты | 3 |
| **Итого** | **~18 часов** |

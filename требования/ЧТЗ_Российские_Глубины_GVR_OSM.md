# ЧТЗ: Интеграция российских гидрографических данных (ГВР + OSM)

## Версия: 1.0
## Дата: 2026-06-14
## Автор: AI Analyst
## Приоритет: High
## Статус: Согласовано

---

## Маршрутизация

**Архитектор:** ТРЕБУЕТСЯ (интеграция внешних сервисов, новая таблица БД, затрагивает >5 файлов)
**Исполнитель:** Разработчик
**Обоснование:** Задача включает интеграцию OSM Overpass API и ГВР данных, новую таблицу БД, многоисточниковый resolver, Redis кэширование, и обновление frontend. Архитектор создал ADR (`требования/ADR_Российские_Гидрографические_Данные.md`).

---

## 1. Цели и задачи

### 1.1 Бизнес-цель
Обеспечить покрытие глубин для внутренних водоёмов России (озёра, реки, водохранилища) через интеграцию с российскими гидрографическими источниками, дополнив существующий GEBCO.

### 1.2 Пользовательская ценность
- Клик по озеру/реке в России показывает глубину и название водоёма
- Источник данных виден пользователю (OSM, ГВР, GEBCO)
- Геометрия и тип водоёма определяются автоматически
- Покрытие расширяется без затрат на API-ключи

### 1.3 Метрики успеха
- Время ответа `/api/v1/depth/point` < 500ms (OSM без кэша), < 50ms (из кэша)
- Redis cache hit rate > 60% при повторных запросах
- Для известных озёр РФ (Сенеж, Плещеево, Валдай) глубина возвращается корректно
- Graceful fallback при недоступности Overpass API

---

## 2. Функциональные требования

### 2.1 User Stories

**US-RUDEPTH-001: Глубина внутреннего водоёма**
**Как** рыбак, **я хочу** кликнуть по озеру/реке в России и узнать глубину, **чтобы** оценить подходит ли место.
- Given: пользователь кликает по точке на внутреннем водоёме РФ
- When: depth-service обрабатывает запрос
- Then: опрашиваются источники в порядке: OSM → ГВР → GEBCO
- And: первый источник с данными возвращает результат
- And: ответ содержит `source` ("OSM" | "GVR" | "GEBCO")
- And: ответ содержит `water_body_name` (если определён)
- And: ответ содержит `water_body_type` (lake | river | reservoir | null)

**US-RUDEPTH-002: Название водоёма**
**Как** рыбак, **я хочу** видеть название водоёма в popup глубины, **чтобы** понимать где я нахожусь.
- Given: depth-service определил водоём
- When: popup отображается
- Then: в DepthPopup показывается название водоёма (если есть)
- And: под названием отображается тип (озеро, река, водохранилище)
- And: бейдж источника данных (OSM / ГВР / GEBCO) отображается рядом

**US-RUDEPTH-003: Кэширование запросов глубины**
**Как** система, **я хочу** кэшировать результаты depth queries в Redis, **чтобы** минимизировать обращения к внешним API.
- Given: повторный запрос глубины в той же точке (±11м)
- When: depth-service проверяет Redis
- Then: при cache hit результат возвращается из Redis (< 50ms)
- And: TTL кэша — 24 часа
- And: ключ кэша: `depth:{lat:.4f}:{lon:.4f}`

**US-RUDEPTH-004: Graceful fallback при недоступности OSM**
**Как** система, **я хочу** продолжать работать при недоступности Overpass API, **чтобы** пользователи всегда получали данные.
- Given: Overpass API возвращает ошибку/timeout (429, 503, timeout)
- When: depth_resolver обрабатывает ошибку
- Then: запрос продолжается к ГВР → GEBCО
- And: в логи записывается warning с описанием ошибки
- And: пользователь получает данные из доступного источника

---

## 3. Нефункциональные требования

### 3.1 Производительность
- OSM Overpass запрос: timeout 10 секунд
- Redis cache lookup: < 5ms
- ГВР PostgreSQL query: < 20ms (с B-tree индексами)
- Общий latency (cache miss): < 600ms (OSM primary path)
- Общий latency (cache hit): < 50ms

### 3.2 Безопасность
- Endpoint `/api/v1/depth/point` — публичный (без авторизации)
- Overpass API — без API-ключа (публичный сервис)
- Валидация lat/lon (Pydantic, ge=-90..90, le=-180..180)
- External API timeout: 10s для Overpass
- Error responses не раскрывают внутренние детали

### 3.3 Надёжность
- При недоступности OSM → fallback к ГВР → fallback к GEBCO
- При недоступности всех источников → `has_data=false`, `depth=null`
- structlog логирование на каждый источник (info на success, warning на failure)
- Redis недоступен → запрос выполняется без кэша (не блокирует)

---

## 4. Техническая архитектура

### 4.1 Изменения в БД

```sql
-- database/migrations/010_create_ru_water_bodies.sql
CREATE TABLE IF NOT EXISTS ru_water_bodies (
    id SERIAL PRIMARY KEY,
    gvr_id VARCHAR(50),
    name VARCHAR(500) NOT NULL,
    name_alt VARCHAR(500),
    water_type VARCHAR(20) NOT NULL DEFAULT 'lake',  -- lake, river, reservoir, pond, sea
    lat_min FLOAT NOT NULL,
    lat_max FLOAT NOT NULL,
    lon_min FLOAT NOT NULL,
    lon_max FLOAT NOT NULL,
    centroid_lat FLOAT NOT NULL,
    centroid_lon FLOAT NOT NULL,
    avg_depth FLOAT,
    max_depth FLOAT,
    area_km2 FLOAT,
    region VARCHAR(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ru_water_bodies_bbox_lat ON ru_water_bodies (lat_min, lat_max);
CREATE INDEX IF NOT EXISTS idx_ru_water_bodies_bbox_lon ON ru_water_bodies (lon_min, lon_max);
CREATE INDEX IF NOT EXISTS idx_ru_water_bodies_name ON ru_water_bodies USING gin (to_tsvector('russian', name));
```

### 4.2 Новые модули depth-service

#### `app/core/redis_client.py`
```python
# Redis async клиент для кэширования depth queries
# Connection pool, graceful degradation при недоступности
```

#### `app/services/osm_overpass_client.py`
```python
# OSM Overpass API клиент
# - query_water_body(lat, lon, radius=50) -> dict | None
#   Возвращает: { name, water_type, depth, max_depth, osm_id }
# - Timeout: 10s
# - Обработка 429 (rate limit): return None, log warning
# - Обработка timeout/network error: return None, log warning
```

Overpass QL:
```
[out:json][timeout:10];
(
  way(around:50,{lat},{lon})["natural"="water"];
  way(around:50,{lat},{lon})["waterway"];
  relation(around:50,{lat},{lon})["natural"="water"];
);
out tags center;
```

Парсинг тегов:
- `water=lake` → type="lake"
- `water=reservoir` → type="reservoir"
- `water=river` / `waterway=riverbank` → type="river"
- `water=pond` → type="pond"
- `depth` → средняя глубина (м)
- `depth:max` или `max_depth` → максимальная глубина (м)
- `name` → название водоёма

#### `app/services/gvr_cache.py`
```python
# ГВР PostgreSQL клиент
# - query_water_body(lat, lon) -> dict | None
#   Запрос: WHERE lat_min <= lat AND lat_max >= lat AND lon_min <= lon AND lon_max >= lon
#   Возвращает: { name, water_type, avg_depth, max_depth, gvr_id }
# - При множественных матчах: ближайший по центроиду
```

#### `app/services/depth_resolver.py`
```python
# Многоисточниковый resolver
# async def resolve_depth(lat, lon) -> dict:
#   1. Redis cache check
#   2. OSM Overpass query
#   3. ГВР database query (если OSM дал имя без глубины — cross-ref)
#   4. GEBCO WMS query (fallback)
#   5. Redis cache write (TTL 24h)
#   Returns unified dict with source attribution
```

### 4.3 API спецификация (расширенная)

**GET /api/v1/depth/point?lat=56.15&lon=37.05**

```json
// Response 200 — данные найдены через OSM
{
    "depth": 5.0,
    "depth_display": "5.0 м",
    "category": "Средняя глубина",
    "source": "OSM",
    "accuracy_m": 10,
    "has_data": true,
    "lat": 56.15,
    "lon": 37.05,
    "season": "summer",
    "fish_match": [
        { "name": "Щука", "icon": "🐟", "depth_range": "2-5 м", "season": "summer" }
    ],
    "water_body_name": "Озеро Сенеж",
    "water_body_type": "lake",
    "depth_type": "max"
}
```

```json
// Response 200 — данные найдены через ГВР
{
    "depth": 24.0,
    "depth_display": "24.0 м",
    "category": "Очень глубоко",
    "source": "GVR",
    "accuracy_m": 50,
    "has_data": true,
    "lat": 59.90,
    "lon": 33.30,
    "water_body_name": "Ладожское озеро",
    "water_body_type": "lake",
    "depth_type": "max"
}
```

```json
// Response 200 — данные не найдены
{
    "depth": null,
    "depth_display": null,
    "category": null,
    "source": null,
    "accuracy_m": null,
    "has_data": false,
    "lat": 56.15,
    "lon": 37.05,
    "water_body_name": null,
    "water_body_type": null,
    "depth_type": null
}
```

### 4.4 Конфигурация

```python
# app/core/config.py — новые настройки
OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT: int = 10
OVERPASS_SEARCH_RADIUS_M: int = 50
REDIS_URL: str = "redis://redis:6379/0"
DEPTH_CACHE_TTL: int = 86400  # 24 часа
DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres_password@postgres:5432/fishing_db"
```

```yaml
# docker-compose.dev.yml — новые env vars для depth-service
environment:
    OVERPASS_API_URL: https://overpass-api.de/api/interpreter
    OVERPASS_TIMEOUT: 10
    OVERPASS_SEARCH_RADIUS_M: 50
    DATABASE_URL: postgresql+asyncpg://postgres:${POSTGRES_PASSWORD:-postgres_password}@postgres:5432/${POSTGRES_DB:-fishing_db}
```

---

## 5. Frontend изменения

### 5.1 Типы

```typescript
// frontend/types/depth.ts — расширить DepthResponse
export interface DepthResponse {
    depth: number | null;
    depth_display: string | null;
    category: string | null;
    source: string | null;           // "OSM" | "GVR" | "GEBCO" | null
    accuracy_m: number | null;
    has_data: boolean;
    lat: number;
    lon: number;
    season: string;
    fish_match: FishMatch[];
    water_body_name: string | null;   // НОВОЕ
    water_body_type: string | null;   // НОВОЕ: lake|river|reservoir|null
    depth_type: string | null;        // НОВОЕ: avg|max|point|null
}
```

### 5.2 DepthPopup

- Под заголовком "Глубина" — название водоёма (если есть)
- Тип водоёма иконкой + текстом (озеро/река/водохранилище)
- Бейдж источника данных (маленький badge: "OSM", "ГВР", "GEBCO")

```
┌─────────────────────────────┐
│  🌊 Глубина          [OSM]  │  ← бейдж источника
├─────────────────────────────┤
│  📍 Озеро Сенеж             │  ← название + тип
│                             │
│       5.0 м                 │  ← глубина
│    Средняя глубина          │
│                             │
│  📍 56.150, 37.050          │
│                             │
│  🐟 На этой глубине:        │
│  [🐟 Щука] [🐟 Карась]      │
│                             │
│  [+ Добавить место]         │
└─────────────────────────────┘
```

---

## 6. Декомпозиция на задачи

### Backend

**TASK-BCK-010: Redis client + config**
- `app/core/redis_client.py` — async Redis connection с graceful degradation
- `app/core/config.py` — новые настройки (OVERPASS_*, DATABASE_URL, DEPTH_CACHE_TTL)
- Критерии: Redis клиент работает, при недоступности не падает

**TASK-BCK-011: OSM Overpass API client**
- `app/services/osm_overpass_client.py` — Overpass QL запрос, парсинг тегов
- Timeout 10s, обработка 429/503/timeout
- Возвращает стандартизированный dict
- Критерии: query_water_body() возвращает данные для известного озера; возвращает None при недоступности

**TASK-BCK-012: ГВР database model + migration**
- `database/migrations/010_create_ru_water_bodies.sql`
- `app/models/water_body.py` — SQLAlchemy async model
- B-tree индексы на bbox, GIN на полнотекстовый поиск по названию
- Критерии: таблица создаётся, индексы работают

**TASK-BCK-013: ГВР seed script**
- `app/seed/seed_water_bodies.py` — загружает топ-1000 водоёмов РФ
- Куратор: Ладожское, Онежское, Байкал, Плещеево, Сенеж, Валдай, Ильмень, К apiUrlные крупные
- Критерии: seed отрабатывает, данные в таблице

**TASK-BCK-014: ГВР cache client**
- `app/services/gvr_cache.py` — bbox запрос к PostgreSQL
- При множественных матчах — ближайший по центроиду
- Критерии: query_water_body() находит Ладожское озеро по координатам

**TASK-BCK-015: Multi-source depth resolver**
- `app/services/depth_resolver.py` — каскадный resolver
- Цепочка: Redis → OSM → ГВР → GEBCO
- Redis cache write (TTL 24h)
- Cross-reference: если OSM дал имя без глубины → ГВР lookup по имени
- structlog на каждом шаге
- Критерии: resolve_depth() возвращает данные из правильного источника

**TASK-BCK-016: Refactor depth.py endpoint**
- `app/api/v1/endpoints/depth.py` — использовать depth_resolver вместо прямого GEBCO
- Расширенный response (water_body_name, water_body_type, depth_type)
- Критерии: endpoint работает, backward-compatible

### Frontend

**TASK-FRT-010: Обновить типы depth.ts**
- Добавить `water_body_name`, `water_body_type`, `depth_type`
- Критерии: tsc --noEmit проходит

**TASK-FRT-011: Обновить DepthPopup.tsx**
- Название водоёма + тип + бейдж источника
- Адаптивные стили (mobile/desktop)
- Критерии: popup рендерится с новыми полями

### Infrastructure

**TASK-INF-010: docker-compose.dev.yml env vars**
- OVERPASS_API_URL, DATABASE_URL, DEPTH_CACHE_TTL для depth-service
- requirements.txt: добавить redis, SQLAlchemy, asyncpg
- Миграция 010 монтируется в postgres
- Критерии: контейнер запускается с новыми env vars

### Testing

**TASK-TST-010: pytest для OSM client**
- Mock Overpass API responses
- Test: lake with depth, river without depth, API error, timeout
- Критерии: все тесты проходят

**TASK-TST-011: pytest для ГВР cache**
- Mock PostgreSQL, test bbox query
- Критерии: тесты проходят

**TASK-TST-012: pytest для depth_resolver**
- Test fallback chain: OSM→ГВР→GEBCO
- Test Redis cache hit/miss
- Test all sources fail → no data
- Критерии: тесты проходят

**TASK-TST-013: pytest для endpoint (расширенный)**
- Test response structure with new fields
- Test backward compatibility
- Критерии: все существующие тесты + новые проходят

---

## 7. Тестирование

### 7.1 Unit-тесты (pytest)
- `test_osm_overpass_client.py` — mock Overpass API
- `test_gvr_cache.py` — mock PostgreSQL
- `test_depth_resolver.py` — mock всех источников
- `test_depth.py` — расширенные endpoint тесты

### 7.2 Тестовые координаты
| Место | Lat | Lon | Ожидаемый источник | Ожидаемая глубина |
|-------|-----|-----|---------------------|-------------------|
| Озеро Сенеж | 56.15 | 37.05 | OSM или ГВР | ~5-6м |
| Ладожское озеро | 60.00 | 31.00 | ГВР (max_depth ~230м) | large |
| Москва-река | 55.75 | 37.62 | OSM или ГВР | ~3-5м |
| Чёрное море | 44.6 | 33.5 | GEBCO | ~2000м |
| Поле (не вода) | 55.80 | 37.50 | — | no data |

### 7.3 Регрессия
- Существующие тесты depth-service должны проходить без изменений
- Существующий GEBCO tile endpoint `/api/v1/depth/tiles/*` не меняется

---

## 8. Риски и зависимости

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| OSM depth sparse coverage | Высокая | ГВР + GEBCO fallback |
| Overpass API rate limit | Средняя | Redis cache 24h; fallback |
| ГВР seed данные требуют парсинга | Высокая | Куратор топ-1000 водоёмов |
| Новый DATABASE_URL для depth-service | Низкая | Async SQLAlchemy, connection pool |
| asyncpg добавлен в requirements | Низкая | Стандартный пакет |

---

## 9. Согласование

- [x] Заказчик (согласовано: ГВР + OSM, расширить depth-service)
- [x] Архитектор (ADR создан)
- [x] Техническая реализуемость подтверждена

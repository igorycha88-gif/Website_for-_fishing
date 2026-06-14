# ADR: Интеграция российских гидрографических данных (ГВР + OSM)

## Статус: Accepted
## Дата: 2026-06-14
## Автор: AI Architect

---

## Контекст

Существующий `depth-service` использует только **GEBCO** (глобальный океанический батиметрический датасет). GEBCO покрывает моря и крупные водоёмы с разрешением ~463м, но **практически не содержит данных по внутренним водоёмам России** (озёра, реки, водохранилища), где рыбачит большинство пользователей.

Проблема: клик по карте по озеру/реке в России возвращает "Глубина неизвестна".

---

## Решение

### Многоисточниковый resolver глубин (Multi-Source Depth Resolver)

Добавить в `depth-service` каскадный опрос источников с fallback-цепочкой:

```
Запрос глубины (lat, lon)
  │
  ├─ 1. Redis cache (TTL 24h)
  │     └─ Hit → вернуть кэшированный результат
  │
  ├─ 2. OSM Overpass API (реальное время)
  │     └─ Найти водоём natural=water в радиусе 50м
  │     └─ Если есть depth/max_depth → вернуть
  │     └─ Если найден name → кросс-референс с ГВР
  │
  ├─ 3. ГВР PostgreSQL (локальный кэш)
  │     └─ Поиск по bbox: lat_min ≤ lat ≤ lat_max, lon_min ≤ lon ≤ lon_max
  │     └─ Если найден → вернуть avg_depth/max_depth
  │
  ├─ 4. GEBCO WMS (существующий fallback)
  │     └─ Для морей и крупных водоёмов
  │
  └─ 5. Нет данных → depth=null, has_data=false
```

### Источник 1: OpenStreetMap (Overpass API)

| Параметр | Значение |
|----------|----------|
| Endpoint | `https://overpass-api.de/api/interpreter` |
| Запрос | `[out:json][timeout:10]; (way(around:50,{lat},{lon})["natural"="water"]; relation(around:50,{lat},{lon})["natural"="water"]; ); out tags;` |
| Теги глубины | `depth` (средняя, м), `max_depth` (максимальная, м) |
| Теги типа | `water=lake`, `water=river`, `water=reservoir`, `water=pond` |
| Покрытие | ~410 пользователей в РФ редактируют depth-теги |
| Лимиты | Free, но rate-limited (обрабатывать 429) |
| Кэш | Redis, TTL 24h |

**Сценарий**: пользователь кликает по озеру → Overpass находит полигон водоёма → возвращает имя, тип, глубину (если есть).

### Источник 2: ГВР (Государственный водный реестр РФ)

| Параметр | Значение |
|----------|----------|
| Портал | `https://textual.ru/gvr/` (публичное зеркало) |
| Формат | HTML (требуется парсинг) или структурированный экспорт |
| Данные | Название, тип, координаты, средняя/максимальная глубина |
| Хранение | Локально в PostgreSQL (`ru_water_bodies`) |
| Обновление | Seed script (запускается вручную/по расписанию) |

**Таблица БД**: `ru_water_bodies`
- Без PostGIS (общая БД для всех сервисов, plain postgres:16-alpine)
- Гео-поиск через bounding box (lat_min/lat_max/lon_min/lon_max)
- B-tree индексы на bbox колонки

### Источник 3: GEBCO (существующий, без изменений)

Финальный fallback для морей и крупных водоёмов. Без изменений.

---

## Архитектурные решения

### 1. Без PostGIS (ОТКЛОНЕНО)

PostGIS требует смены образа на `postgis/postgis:16-3.4`. Так как PostgreSQL — общая БД для всех микросервисов, смена образа рискованна. Вместо этого:
- `ru_water_bodies`: bbox-запросы через простые `WHERE lat_min <= ? AND lat_max >= ?` с B-tree индексами
- OSM: точность обеспечивается Overpass API (серверная сторона)
- Приёмлемая точность для рыбацкого приложения

### 2. Redis как первичный кэш (ПРИНЯТО)

Глубины водоёмов меняются крайне редко. Redis-кэш с TTL 24h:
- Ключ: `depth:{lat:.4f}:{lon:.4f}` (округление до 4 знаков = ~11м точность)
- Значение: полный JSON ответ `/api/v1/depth/point`
- Hit rate: высокий (рыбаки часто кликают по одним и тем же местам)

### 3. OSM Overpass как первичный источник (ПРИНЯТО)

OSM Overpass API бесплатный, не требует API-ключа, предоставляет:
- Геометрию водоёмов (полигоны)
- Имена и типы (name, water)
- Глубину (depth, max_depth) — где данные есть

Скорость: 200-500ms на запрос (приемлемо для клика по карте).

### 4. ГВР как локальная БД (ПРИНЯТО)

ГВР не имеет REST API — данные доступны через веб-портал. Решение:
- Seed script загружает данные в PostgreSQL
- Таблица `ru_water_bodies` с bbox и глубинами
- Первый seed: топ-1000 крупнейших водоёмов РФ
- Будущее расширение: полный экспорт ГВР

### 5. Расширить существующий depth-service (ПРИНЯТО)

Вместо нового микросервиса — расширить `depth-service`:
- Минимум инфраструктурных изменений (порт 8008 уже настроен)
- Единая точка ответственности за данные о глубинах
- Единый API контракт (`/api/v1/depth/point`)

---

## Новые файлы

```
services/depth-service/app/
├── services/
│   ├── osm_overpass_client.py   # НОВЫЙ — OSM Overpass API клиент
│   ├── gvr_cache.py             # НОВЫЙ — ГВР PostgreSQL клиент
│   ├── depth_resolver.py        # НОВЫЙ — многоисточниковый resolver
│   └── depth_reader.py          # ИЗМЕНЁН — использует depth_resolver
├── core/
│   ├── config.py                # ИЗМЕНЁН — новые настройки (Overpass URL, Redis)
│   └── redis_client.py          # НОВЫЙ — Redis connection
├── models/
│   └── water_body.py            # НОВЫЙ — SQLAlchemy модель ru_water_bodies
└── seed/
    └── seed_water_bodies.py     # НОВЫЙ — загрузчик ГВР данных

database/migrations/
└── 010_create_ru_water_bodies.sql  # НОВАЯ миграция

frontend/
├── types/depth.ts               # ИЗМЕНЁН — новые поля
└── components/DepthPopup.tsx     # ИЗМЕНЁН — имя водоёма + бейдж источника
```

---

## API контракт (расширенный)

```json
// GET /api/v1/depth/point?lat=56.15&lon=37.05
{
    "depth": 4.2,
    "depth_display": "4.2 м",
    "source": "OSM",                     // "OSM" | "GVR" | "GEBCO" | "CACHE"
    "accuracy_m": 10,
    "has_data": true,
    "lat": 56.15,
    "lon": 37.05,
    "season": "summer",
    "fish_match": [...],
    "water_body_name": "Озеро Сенеж",    // НОВОЕ
    "water_body_type": "lake",           // НОВОЕ: lake | river | reservoir | sea | null
    "depth_type": "max"                  // НОВОЕ: avg | max | point
}
```

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| OSM depth sparse coverage | Высокая | Среднее | ГВР + GEBCO fallback; UX "нет данных" |
| Overpass API rate limit (429) | Средняя | Среднее | Redis cache 24h; retry с backoff; fallback к ГВР |
| ГВР данные требуют парсинга HTML | Высокая | Низкое | Seed script с regex-парсингом; куратор-1000 водоёмов |
| bbox-запрос без PostGIS неточен | Средняя | Низкое | Округление Redis-ключа до 4 знаков; приемлемо для рыбалки |
| ГВР портал недоступен при seed | Низкая | Низкое | Seed — одноразовая операция; retry логика |

---

## Будущее развитие (Phase 2)

1. **PostGIS** — добавить при росте нагрузки на bbox-запросы
2. **Полный ГВР экспорт** — загрузить все 500k+ водоёмов
3. **OSM depth contours** — парсить изобаты (contour=depth)
4. **User-generated depth** — рыбаки с эхолотами загружают измерения
5. **Bathymetric tiles** — генерация собственных тайлов из комбинированных данных

---

## Ссылки

- Существующий depth-service: `services/depth-service/`
- Предыдущее ЧТЗ: `требования/ЧТЗ_Карты_Глубин_GEBCO.md`
- OSM depth tag: https://wiki.openstreetmap.org/wiki/Key:depth
- OSM Overpass API: https://overpass-api.de/
- ГВР: https://textual.ru/gvr/
- Taginfo Россия: https://taginfo.geofabrik.de/russia/keys/depth

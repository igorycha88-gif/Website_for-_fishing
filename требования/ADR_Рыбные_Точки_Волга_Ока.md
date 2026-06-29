# ADR: Рыбные точки (catch_points) — Волга и Ока

> **Статус:** Принято
> **Связанное ЧТЗ:** `требования/ЧТЗ_Рыбные_Точки_Волга_Ока.md`

## Контекст

Нужен слой на карте с точками ловли рыбы по Волге и Оке. Существующая сущность `places` — это «места для рыбалки» (площадные объекты: базы, кэмпинги, дикие места) с владельцем и видимостью. Точки улова — это **точечные отметки**: где конкретно ловили конкретную рыбу. Семантически это другая сущность, поэтому отдельная таблица.

Существующая `user_catch_reports` привязана к **региону** (не к точке) и решает другую задачу (обратная связь по точности прогноза). Не подходит.

## Решение

### Новая таблица `catch_points`

```sql
CREATE TABLE catch_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    latitude NUMERIC(10, 8) NOT NULL,
    longitude NUMERIC(11, 8) NOT NULL,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    river VARCHAR(20) NOT NULL CHECK (river IN ('volga','oka')),
    name VARCHAR(200) NOT NULL,             -- краткое название точки/местности
    description TEXT,
    season VARCHAR(20)[] DEFAULT '{}',       -- spring/summer/autumn/winter
    depth NUMERIC(6, 2),                     -- глубина ловли, м
    bait VARCHAR(200),                       -- снасть/наживка
    weight_avg NUMERIC(6, 2),                -- средний вес, кг
    is_demo BOOLEAN DEFAULT true,            -- пометка демонстрационных данных
    source_label VARCHAR(100) DEFAULT 'Демонстрационные данные',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Индексы: GiST по координатам не заводим (объём небольшой, достаточно btree + bbox через BETWEEN); btree по `river`, `fish_type_id`.

### API (places-service, префикс `/api/v1`)
- `GET /catches` — список. Query: `river`, `fish_type_id`, `min_lat`, `min_lon`, `max_lat`, `max_lon`, `page`, `page_size`. Публичный (без авторизации).
- `GET /catches/{id}` — одна точка.

Ответ обогащается `fish_type` (id, name, icon, category) — аналогично `_enrich_place_with_fish_types`.

### Frontend
- `YandexMap` получает новый проп `catchPoints?: CatchPoint[]`. Рендерит отдельный `<Clusterer>` со своими placemark'ами: кастомный `iconLayout` (круг + emoji рыбы по виду), балун с деталями. Цвет/иконка берутся из `fish_type.icon`.
- Цвет кластера рыбных точек — оранжевый (`islands#orangeClusterIcons`), чтобы отличать от мест (фиолетовый).

### Seed демо-данных
Реальные координаты по течению рек (общедоступная география). Привязка к существующим `fish_types` по имени.

## Альтернативы

1. **Переиспользовать `places` с новым `place_type='catch'`** — отклонено: разная семантика, places требует owner_id (FK users), visibility, address; точки улова — публичные и без владельца.
2. **Расширить `user_catch_reports` координатами** — отклонено: та таблица под обратную связь прогноза (region + forecast_date).

## Последствия
- +1 таблица, +2 endpoint, +1 слой на карте.
- Миграция: добавить блок в `schema.sql`; places-service создаёт таблицу через существующий startup (create_all).

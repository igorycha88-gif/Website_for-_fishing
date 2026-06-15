# ADR: Слой глубин в стиле Navionics Marine Charts

## Статус: Принято
## Дата: 2026-06-14

---

## Контекст

Текущая реализация слоя глубин проксирует тайлы GEBCO WMS напрямую. Это создаёт три проблемы:
1. Цвета GEBCO не совпадают с легендой в LayersPanel
2. GEBCO покрывает только океаны — inland водоёмы России не визуализированы
3. Нет меток глубин и контуров (изобат) — toggle «Изобаты» мёртвый

Нужен слой в стиле Navionics: цветные полигоны водоёмов, метки глубин, контуры.

## Решение

### 1. Гибридная визуализация: вектор + растр

| Зона | Технология | Источник данных |
|------|-----------|----------------|
| Inland водоёмы (озёра, водохранилища) | **Векторные полигоны** (ymaps.Polygon) | OSM Overpass API → water_body_polygons |
| Моря/океаны | **Растерные тайлы** (ymaps.Layer) | GEBCO WMS → перекраска PIL |
| Метки глубин | **ymaps.Placemark** с HTML-лейблом | water_body_polygons centroids |

### 2. База данных: `water_body_polygons` (без PostGIS)

PostGIS не установлен в текущем образе PostgreSQL. Используем паттерн как в `ru_water_bodies`:
- `coordinates JSONB` — GeoJSON Polygon координаты
- `lat_min, lat_max, lon_min, lon_max` — bbox колонки с B-tree индексом для быстрой фильтрации
- Запрос: `WHERE lat_min <= :maxLat AND lat_max >= :minLat AND lon_min <= :maxLon AND lon_max >= :minLon`

### 3. OSM Polygon Importer (Overpass)

**Стратегия seed:** при старте depth-service проверяет `water_body_polygons` на пустоту. Если пусто — запускает импорт для всех 29 водоёмов из `seed_water_bodies.py`.

**Overpass запрос:**
```
[out:json][timeout:60];
(
  way(BBOX)["natural"="water"]["name"="{name}"];
  relation(BBOX)["natural"="water"]["name"="{name}"];
);
out geom;
```

**Парсинг:** для ways — geometry напрямую; для relations — объединение outer member ways.
**Fallback:** если Overpass недоступен → bbox из `ru_water_bodies`.
**Rate limiting:** задержка 2 сек между запросами, max 3 retry.

### 4. Новые API endpoints

| Endpoint | Метод | Назначение |
|----------|-------|-----------|
| `/api/v1/depth/areas` | GET | GeoJSON полигонов водоёмов по viewport bbox |
| `/api/v1/depth/labels` | GET | GeoJSON точечных меток глубин по viewport |

Прокси в `next.config.js` уже настроен (`/api/v1/depth/:path*`).

### 5. Перекраска тайлов GEBCO

В `depth_reader.py → fetch_tile()` добавлен шаг перекраски:
1. Скачать GEBCO тайл (256x256 PNG)
2. Для каждого пикселя: оценить глубину через `_estimate_depth_from_pixel()`
3. Если глубина есть → перекрасить пиксель в цвет из нашего `DEPTH_COLOR_RAMP`
4. Если суша → сделать прозрачным
5. Кэшировать в `TILE_CACHE_DIR`

### 6. Frontend рендеринг

**При включении слоя:**
1. Подписка на `boundschange` (debounce 300ms)
2. fetch `/depth/areas?bbox=viewport` → рендер `ymaps.Polygon`
3. fetch `/depth/labels?bbox=viewport&zoom=z` → рендер `ymaps.Placemark`
4. Координаты: GeoJSON [lon,lat] → Yandex [lat,lon]

**При выключении:** удаление всех geoObjects.

**LayersPanel:** добавлены селектор цветовой схемы, тумблер меток, wire up изобат.

### 7. Цветовые схемы

```python
COLOR_SCHEMES = {
    "navionics": [(0,2,"#B3E5FC"), (2,5,"#4FC3F7"), (5,10,"#0288D1"), (10,20,"#01579B"), (20,50,"#1A237E"), (50,9999,"#000C2E")],
    "contrast":  [(0,2,"#80DEEA"), (2,5,"#26C6DA"), (5,10,"#00ACC1"), (10,20,"#00838F"), (20,50,"#006064"), (50,9999,"#00363A")],
    "sport":     [(0,2,"#A5D6A7"), (2,5,"#66BB6A"), (5,10,"#43A047"), (10,20,"#2E7D32"), (20,50,"#1B5E20"), (50,9999,"#0D3811")],
}
```

## Последствия

- **+** Единая цветовая схема — тайлы и полигоны используют одни цвета
- **+** Inland водоёмы России визуализированы как у Navionics
- **+** Метки глубин видны без клика
- **+** Контролы: схема, прозрачность, метки, изобаты
- **−** Overpass API недоступен при seed → fallback на bbox (прямоугольники)
- **−** Перекраска тайлов добавляет ~50-100ms на первый запрос (кэшируется)

## Затронутые файлы

**Backend (depth-service):**
- `app/services/osm_polygon_importer.py` — НОВЫЙ
- `app/services/depth_areas.py` — НОВЫЙ
- `app/services/depth_labels.py` — НОВЫЙ
- `app/services/tile_recolor.py` — НОВЫЙ
- `app/api/v1/endpoints/areas.py` — НОВЫЙ
- `app/api/v1/endpoints/labels.py` — НОВЫЙ
- `app/api/v1/router.py` — ИЗМЕНЁН
- `app/services/depth_reader.py` — ИЗМЕНЁН (перекраска)
- `app/main.py` — ИЗМЕНЁН (seed trigger)
- `app/core/config.py` — ИЗМЕНЁН (новые настройки)

**БД:**
- `database/migrations/011_create_water_body_polygons.sql` — НОВЫЙ

**Frontend:**
- `frontend/types/depth.ts` — ИЗМЕНЁН
- `frontend/hooks/useDepthAreas.ts` — НОВЫЙ
- `frontend/hooks/useDepthLabels.ts` — НОВЫЙ
- `frontend/components/YandexMap.tsx` — ИЗМЕНЁН
- `frontend/components/LayersPanel.tsx` — ИЗМЕНЁН
- `frontend/app/map/page.tsx` — возможно ИЗМЕНЁН

**Docker:**
- `docker-compose.dev.yml` — ИЗМЕНЁН (миграция 011)

# ЧТЗ: Исправление запроса глубин по точке (depth-service)

## Версия: 1.0
## Дата: 2026-06-14
## Автор: AI Analyst
## Приоритет: Critical
## Статус: Согласовано

---

## Маршрутизация

**Архитектор:** НЕ ТРЕБУЕТСЯ (исправление бага в существующем коде, <5 файлов)
**Исполнитель:** Разработчик
**Маршрут:** Стандартный (Аналитик → Разработчик → Тестировщик → DevOps → Тестировщик)

---

## 1. Описание проблемы

Запрос глубины по точке (`GET /api/v1/depth/point`) **всегда возвращает `depth: null, has_data: false`**,
независимо от координат. Пользователь не может получить данные о глубине ни в одной точке мира.

### Корневые причины (3 бага):

1. **Устаревший URL GEBCO WMS** — сервис переехал:
   - Старый: `https://www.gebco.net/data_and_tools/gebco_web_services/web_map_service_tiles/mapserv` → **404**
   - Новый: `https://wms.gebco.net/mapserv` (подтверждено: GetCapabilities, GetMap работают)

2. **Функция `_query_gebco_api()` не парсит ответ** (depth_reader.py:118-124):
   - При HTTP 200 жёстко возвращает `depth: None, has_data: False`
   - Тело ответа полностью игнорируется
   - URL захардкожен в функции вместо использования `settings.GEBCO_WMS_URL`

3. **GEBCO WMS GetFeatureInfo не работает** для растровых слоёв:
   - Возвращает пустой ответ для всех слоёв
   - MapServer не сконфигурирован для отдачи значений растра через GetFeatureInfo

### Дополнительный контекст:
- GEBCO — это океанская батиметрия (разрешение ~463м), не покрывает внутренние воды России (Волга, озёра)
- В районе Калязина GEBCO видит сушу, не воду (RGB=(70,207,108) → зелёный = суша)
- Слой `GEBCO_LATEST` (shaded relief) не поддерживает GetFeatureInfo (queryable=0)
- Слой `GEBCO_LATEST_2` (flat map, color-coded) — queryable=1, но GetFeatureInfo всё равно пустой

---

## 2. Решение

### Подход: Цветовая оценка глубины через WMS GetMap

Поскольку GetFeatureInfo не работает, используем **GetMap с микро-тайлом (3×3 пикселя)** для запроса
цвета пикселя в целевой точке. Слой `GEBCO_LATEST_2` (flat map, color-coded for elevation) использует
градиент от тёмно-синего (глубоко) до светло-голубого (мелко) и зелёного (суша).

**Алгоритм:**
1. Запросить GeoTIFF 3×3 пикселя из `GEBCO_LATEST_2` в окрестности точки
2. Прочитать центральный пиксель (RGB) через Pillow (уже в requirements.txt)
3. Определить суша/вода по соотношению B/G:
   - B/G < 0.7 → суша → `has_data: false`
   - B/G ≥ 0.7 → вода → оценка глубины
4. Оценить глубину по яркости пикселя (калиброванная таблица)

### Калибровка цветовой палитры (из реальных запросов):

| Локация | RGB | Sum | B/G | Глубина |
|---------|-----|-----|-----|---------|
| Pacific deep | (0, 10, 59) | 69 | 5.9 | ~6000m |
| Atlantic deep | (23, 124, 191) | 338 | 1.5 | ~4000m |
| Atlantic mid | (32, 178, 219) | 429 | 1.2 | ~2000m |
| Med coast | (93, 228, 245) | 566 | 1.1 | ~200m |
| Baltic shallow | (162, 248, 236) | 646 | 0.95 | ~50m |
| North Sea | (211, 255, 237) | 703 | 0.93 | ~15m |
| Kalyazin (LAND) | (70, 207, 108) | 385 | 0.52 | суша |

---

## 3. Критерии приёмки

1. ✅ `GET /api/v1/depth/point?lat=43.0&lon=36.0` (Чёрное море) → `has_data: true, depth > 0`
2. ✅ `GET /api/v1/depth/point?lat=-30.0&lon=-40.0` (Атлантика) → `has_data: true, depth > 1000`
3. ✅ `GET /api/v1/depth/point?lat=57.22&lon=37.84` (Калязин, суша) → `has_data: false`
4. ✅ Слой тайлов глубин отображается на карте (WMS URL обновлён)
5. ✅ structlog-логи на endpoint (request_started, request_completed, error)
6. ✅ pytest проходит
7. ✅ ruff проходит

---

## 4. Файлы для изменения

| Файл | Изменение |
|------|-----------|
| `services/depth-service/app/core/config.py` | Обновить `GEBCO_WMS_URL`, добавить `GEBCO_QUERY_LAYER` |
| `services/depth-service/app/services/depth_reader.py` | Переписать `_query_gebco_api()`, добавить `_estimate_depth_from_pixel()` |
| `docker-compose.dev.yml` | Обновить `GEBCO_WMS_URL` env var |
| `services/depth-service/tests/test_depth.py` | Обновить тесты с mock GEBCO |

---

## 5. Декомпозиция

- TASK-BCK-001: Обновить config.py (URL + query layer)
- TASK-BCK-002: Переписать _query_gebco_api() с цветовой оценкой
- TASK-BCK-003: Обновить docker-compose.dev.yml
- TASK-BCK-004: Обновить тесты
- TASK-BCK-005: Запустить pytest + ruff

---

## 6. Ограничения

- GEBCO не покрывает внутренние воды России — это ограничение данных, не кода
- Оценка глубины по цвету приблизительна (точность ±30% для глубин > 1000м)
- Для内陆ных вод требуется отдельный источник данных (будущая задача)

# ЧТЗ: BUG-FORECAST-002 — Нет рыб в прогнозе клёва на проде

## Постановка задачи

На проде (VPS) в прогнозе клёва не отображается рыба. 
Логи: `fishCount: 0`, `GET /custom-fish → 401 Unauthorized`.

## Диагноз

### Корневая причина
**`places-service` отсутствует в `docker-compose.vps.yml`**. 

Цепочка:
1. `places-service` — единственный сервис, заполняющий таблицу `fish_types` (через `seed_fish_types()`)
2. Без `fish_types` → `forecast-service` не может засеять `fish_bite_settings` (seeder зависит от fish_types)
3. Без `fish_bite_settings` → прогноз возвращает `forecasts: []` → `fishCount: 0`

### Дополнительные проблемы в `docker-compose.vps.yml`
- Строка 159: `PLACES_SERVICE_URL: http://auth-service:8000` — опечатка, должен быть `places-service`
- Строки 160-162: `REPORTS_SERVICE_URL`, `BOOKING_SERVICE_URL`, `SHOP_SERVICE_URL` — все указывают на `auth-service`

## Маршрутизация

- **Маршрут:** Стандартный (баг-фикс)
- **Исполнитель:** Разработчик

## Задачи

### TASK-INF-001: Добавить places-service в docker-compose.vps.yml

**Файл:** `docker-compose.vps.yml`

**Что сделать:**
1. Добавить сервис `places-service` (скопировать из `docker-compose.dev.yml`, адаптировать для проды)
2. Исправить URL сервисов в `frontend`:
   - `PLACES_SERVICE_URL: http://places-service:8001` (или правильный порт)
   - Остальные (REPORTS, BOOKING, SHOP) оставить на `auth-service` (они ещё не реализованы)
3. `forecast-service` должен зависеть от `places-service` (condition: service_started)

**Критерии приёмки:**
- `docker-compose.vps.yml` содержит `places-service`
- `frontend` корректно ссылается на `places-service`
- `forecast-service` зависит от `places-service`

### TASK-INF-002: Обеспечить seed fish_types при старте на проде

**Проблема:** На проде `fish_types` могут быть уже пустые (places-service ранее не запускался).

**Варианты решения:**
1. places-service при старте автоматически вызывает `seed_fish_types()` (проверить)
2. Если нет — добавить вызов seed в lifespan places-service

**Критерии приёмки:**
- При старте контейнеров `fish_types` заполняются автоматически
- `fish_bite_settings` заполняются после fish_types

### TASK-INF-003: Проверить healthcheck и порты

**Что проверить:**
- Порт places-service совпадает в Dockerfile и docker-compose
- Healthcheck URL корректный
- Nginx не нужно обновлять (forecast ходит через Next.js middleware)

## Критерии приёмки (общие)

1. Прогноз клёва на проде показывает рыбу (fishCount > 0)
2. `/custom-fish` возвращает 200 для авторизованных (401 для неавторизованных — ок)
3. Все сервисы healthy после пересборки
4. Логи forecast-service не содержат ошибок seeding

## Затронутые файлы

- `docker-compose.vps.yml` — основные изменения
- (возможно) `services/places-service/app/main.py` — проверка seed на старте

## Риски

- После добавления places-service может потребоваться больше RAM на VPS
- Нужно убедиться что места на диске достаточно для дополнительных образов

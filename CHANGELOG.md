# Changelog

## [1.3.0] - 2026-06-29

### Добавлено
- feat(depth): интеграция российских гидрографических данных (ГВР + OSM) (a40cc26)
- feat(depth): слой глубин на карте — areas, labels, tiles + fix mapRef (21b84ac)
- feat(catches): точки улова на карте — модель/API places-service, хук useCatches, HomeCatchMap, e2e (0815822)
- feat(forecast): алгоритм клёва v6 — влияние Луны (фаза×время суток, окно активности ±3 дня) (b1c4edd)

### Безопасность
- fix(security): привязка Next.js к 127.0.0.1 — закрытие наружного порта 3000 (INC-SEC-001) (e627936)

### Исправлено
- fix(ci): исключить e2e/ из Jest testPathIgnorePatterns — Jest падал на Playwright-тестах (d1fd7f8)

## [1.2.5] - 2026-06-11

### Исправлено
- fix(forecast): автоматическая миграция недостающих колонок при старте (climate_zone, v5 fields)
- fix(forecast): логирование наличия колонок regions.climate_zone и fish_bite_settings.pre_spawn_days

## [1.2.4] - 2026-06-11

### Исправлено
- fix(prod): добавлен отсутствующий places-service в docker-compose.vps-host.yml (порт 8008)
- fix(prod): исправлен PLACES_SERVICE_URL — указывал на auth-service (8001) вместо places (8008)
- fix(prod): исправлены REPORTS/BOOKING/SHOP service URLs на корректные порты
- fix(forecast): seed_all() обёрнут в try/except — сервис не падает при ошибке сидирования

## [1.2.3] - 2026-06-11

### Добавлено
- feat(forecast): добавлено диагностическое логирование для отладки отображения рыб на проде (871e435)

## [1.2.2] - 2026-06-11

### Исправлено
- fix(lint): исправлены все ruff ошибки в 7 backend сервисах (неиспользуемые импорты, re-export алиасы)
- fix(lint): исправлены TypeScript ошибки в frontend тестах (type casts)
- fix(config): добавлены дефолтные значения Settings для CI (DATABASE_URL, REDIS_URL, SECRET_KEY)
- fix(tests): исправлены падающие unit-тесты auth (10), forecast (1), places (1)
- fix(places): добавлен pytest.ini с asyncio_mode=auto
- fix(places): интеграционные тесты пропускаются при отсутствии PostgreSQL в CI
- fix(forecast): добавлен places-service в docker-compose.vps.yml — fish_types не засевались на проде
- fix(ci): увеличен healthcheck таймаут до 300с для прод деплоя
- fix(ci): исправлен синтаксис deploy.yml — вложенные кавычки, порт фронтенда

## [1.2.1] - 2026-06-10

### Исправлено
- fix(forecast): заменена заглушка /forecast на рабочий компонент FishingForecast
- fix(forecast): главная страница подключена к API прогноза клёва вместо статических данных
- fix(home): удалены мок-данные «Популярные места», заменены на живой прогноз

## [1.2.0] - 2026-06-09

### Добавлено
- feat(ci): добавлены CI/CD pipeline для продакшн-деплоя (99d4b66)
- feat(forecast): SVG-иконка фазы луны в прогнозе клёва (12e19e0)
- feat(pipeline): полный конвейер разработки с набором скиллов (a0f209e)

### Исправлено
- fix(forecast): исправление сидирования рыб и прогноза клева (2034f01)

# Автотесты - Быстрый старт

## Быстрый запуск

```bash
# Запустить тестовую базу данных
make db-test-start

# Запустить все тесты
make test-all

# Остановить тестовую базу данных
make db-test-stop
```

## Полная документация

Подробная документация: [TESTING_GUIDE.md](TESTING_GUIDE.md)

## Доступные команды

| Команда | Описание |
|---------|----------|
| `make db-test-start` | Запустить тестовую базу данных |
| `make db-test-stop` | Остановить тестовую базу данных |
| `make test-backend` | Запустить backend тесты |
| `make test-e2e` | Запустить E2E тесты |
| `make test-e2e-ui` | E2E тесты с UI |
| `make test-e2e-debug` | E2E тесты в debug режиме |
| `make test-all` | Запустить все тесты |
| `make test-clean` | Очистить артефакты тестов |

## Структура тестов

- **Frontend**: `frontend/e2e/` (Playwright)
- **Backend**: `services/*/tests/` (Pytest)

## Требования

- Node.js 20+
- Python 3.12+
- Docker и Docker Compose

## CI/CD

Автоматический запуск тестов в GitHub Actions при push/PR.
Файл: `.github/workflows/e2e-tests.yml`

## Отчеты

- E2E: `frontend/playwright-report/`
- Backend coverage: `services/*/htmlcov/`

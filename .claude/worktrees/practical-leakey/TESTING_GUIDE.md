# Автотестирование

Этот документ описывает как запускать и работать с автотестами для проекта "Сайт для рыбалки".

## Требования

- Node.js 20+
- Python 3.12+
- Docker и Docker Compose
- npm

## Структура тестов

### Frontend (Playwright)
Файлы тестов находятся в `frontend/e2e/`:
- `homepage.spec.ts` - Тесты главной страницы
- `login.spec.ts` - Тесты страницы входа
- `register.spec.ts` - Тесты страницы регистрации
- `password-reset.spec.ts` - Тесты сброса пароля
- `profile.spec.ts` - Тесты страницы профиля
- `auth.setup.ts` - Setup для аутентификации в тестах

### Backend (Pytest)
Файлы тестов находятся в `services/*/tests/`:
- `services/auth-service/tests/` - Тесты сервиса аутентификации
- `services/places-service/tests/` - Тесты сервиса мест
- `services/email-service/tests/` - Тесты email сервиса

## Установка и запуск

### 1. Запуск тестовой базы данных

```bash
make db-test-start
```

Эта команда запускает:
- PostgreSQL на порту 5433
- Redis на порту 6380

### 2. Установка зависимостей

Frontend:
```bash
cd frontend
npm install
npx playwright install --with-deps
```

Backend:
```bash
pip install -r services/auth-service/requirements.txt
pip install -r services/places-service/requirements.txt
pip install -r services/email-service/requirements.txt
```

### 3. Запуск E2E тестов

Запустить все E2E тесты:
```bash
make test-e2e
```

Запустить с UI (интерактивный режим):
```bash
make test-e2e-ui
```

Запустить в режиме debug:
```bash
make test-e2e-debug
```

### 4. Запуск backend тестов

```bash
make test-backend
```

### 5. Запуск всех тестов

```bash
make test-all
```

Эта команда:
1. Запускает тестовую базу данных
2. Запускает backend тесты
3. Запускает E2E тесты
4. Останавливает тестовую базу данных

## Конфигурация

### Playwright

Файл конфигурации: `frontend/playwright.config.ts`

Основные настройки:
- `baseURL`: http://localhost:3000
- `globalSetup`: e2e/auth.setup.ts
- Браузеры: Chromium, Firefox, WebKit, Mobile Chrome

### Test Database

Файл конфигурации: `docker-compose.test.yml`

Переменные окружения в `.env.test`:
- `TEST_DATABASE_URL`: URL для подключения к тестовой базе PostgreSQL
- `TEST_REDIS_URL`: URL для подключения к тестовому Redis
- `TEST_SECRET_KEY`: Секретный ключ для тестов
- и другие переменные для сервисов

## Отчеты

### E2E тесты

HTML отчет:
```bash
make test-e2e-report
```

Отчет сохраняется в `frontend/playwright-report/`

Скриншоты при ошибках:
`frontend/test-results/`

### Backend тесты

HTML отчеты генерируются автоматически в `services/*/htmlcov/`

## Полезные команды

### Очистка тестовых артефактов

```bash
make test-clean
```

Эта команда удаляет:
- Результаты тестов Playwright
- Отчеты Playwright
- Auth state файлы
- HTML coverage отчеты
- Pytest cache

### Остановка тестовой базы данных

```bash
make db-test-stop
```

### Посмотреть логи

```bash
docker-compose -f docker-compose.test.yml logs -f
```

## CI/CD

Автоматические тесты запускаются в GitHub Actions при:
- Push в ветки main, develop
- Pull Request в ветки main, develop

Файл workflow: `.github/workflows/e2e-tests.yml`

## Поддержка

Если тесты не проходят:

1. Убедитесь что все контейнеры запущены:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

2. Проверьте что frontend запущен:
   ```bash
   cd frontend
   npm run dev
   ```

3. Проверьте что backend сервисы доступны

4. Посмотрите логи контейнеров:
   ```bash
   docker-compose -f docker-compose.test.yml logs
   ```

## Добавление новых тестов

### Frontend тесты

Создайте новый файл в `frontend/e2e/` с именем `*.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Название группы тестов', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/page');
  });

  test('описание теста', async ({ page }) => {
    // Код теста
  });
});
```

### Backend тесты

Создайте новый файл в `services/*/tests/` с именем `test_*.py`:

```python
import pytest

def test_example():
    assert True
```

## Best Practices

1. **Используйте специфичные локаторы**: Избегайте `getByText` если текст повторяется на странице. Используйте `getByRole`, `getByLabel`, `getByTestId`.

2. **Ожидания**: Всегда используйте `expect().toBeVisible()` и другие ожидания Playwright вместо фиксированных задержек.

3. **Изоляция**: Каждый тест должен быть независимым. Не полагайтесь на состояние от других тестов.

4. **Читаемость**: Используйте понятные названия тестов на русском языке.

5. **Очистка**: Используйте `beforeEach` и `afterEach` для подготовки и очистки данных.

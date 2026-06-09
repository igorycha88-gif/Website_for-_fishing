# QA Engineer Prompt - Платформа для рыбалки FishMap

## 1. Общая информация о проекте

### 1.1. Описание
FishMap - микросервисная веб-платформа для рыболовов на ранней стадии разработки. Позволяет пользователям находить места для рыбалки, просматривать прогнозы клева, делиться отчетами и бронировать рыболовные базы.

### 1.2. Текущий статус разработки

| Компонент | Статус | Покрытие тестами |
|-----------|--------|------------------|
| Auth Service | ✅ Реализован | Unit тесты есть |
| Email Service | ✅ Реализован | Unit тесты есть |
| Forecast Service | ✅ Реализован | Unit тесты (25+ тестов) |
| Places Service | 🚧 В разработке | Unit тесты есть |
| Reports Service | 🚧 Заглушка | - |
| Booking Service | 🚧 Заглушка | - |
| Shop Service | 🚧 Заглушка | - |
| Frontend | ✅ Основные страницы | E2E тесты (Playwright) |

### 1.3. Технологический стек

**Frontend:**
- Next.js 15 (App Router, TypeScript)
- Tailwind CSS, Framer Motion
- Zustand (state management)
- Playwright (E2E тесты)

**Backend:**
- FastAPI (Python 3.12+)
- PostgreSQL 16 (общая БД)
- Redis (кэширование)
- SQLAlchemy (async ORM)
- Pytest (unit тесты)

**Infrastructure:**
- Docker / Docker Compose
- ELK Stack (опционально)

---

## 2. Архитектура микросервисов

### 2.1. Порты сервисов

| Сервис | Хост порт | Контейнер порт | Base URL |
|--------|-----------|----------------|----------|
| Frontend | 3000 | 3000 | http://localhost:3000 |
| Auth Service | 8001 | 8000 | http://localhost:8001 |
| Places Service | 8002 | 8001 | http://localhost:8002 |
| Reports Service | 8003 | 8002 | http://localhost:8003 |
| Booking Service | 8004 | 8003 | http://localhost:8004 |
| Shop Service | 8005 | 8004 | http://localhost:8005 |
| Email Service | 8006 | 8005 | http://localhost:8006 |
| Forecast Service | 8007 | 8000 | http://localhost:8007 |
| PostgreSQL | 5432 | 5432 | localhost:5432 |
| Redis | 6379 | 6379 | localhost:6379 |

### 2.2. Health Check endpoints

Все сервисы имеют `/health` endpoint:
```bash
curl http://localhost:8001/health  # Auth
curl http://localhost:8006/health  # Email
curl http://localhost:8007/health  # Forecast
curl http://localhost:8002/health  # Places
```

Ожидаемый ответ:
```json
{"status": "healthy", "service": "auth-service", "version": "1.0.0"}
```

---

## 3. Реализованные API endpoints

### 3.1. Auth Service (порт 8001)

```
POST   /api/v1/auth/register              - Регистрация
POST   /api/v1/auth/verify-email          - Подтверждение email
POST   /api/v1/auth/resend-verification   - Повторная отправка кода
POST   /api/v1/auth/login                 - Вход
POST   /api/v1/auth/reset-password/request - Запрос сброса пароля
POST   /api/v1/auth/reset-password/confirm - Подтверждение сброса
GET    /api/v1/users/me                   - Текущий пользователь
PUT    /api/v1/users/me                   - Обновить профиль
PATCH  /api/v1/users/me/password          - Сменить пароль
GET    /health                            - Health check
```

### 3.2. Email Service (порт 8006)

```
POST   /api/v1/email/send         - Отправить email
POST   /api/v1/email/generate-code - Сгенерировать код
GET    /health                      - Health check
```

### 3.3. Forecast Service (порт 8007)

```
GET    /api/v1/regions                    - Список регионов
GET    /api/v1/regions/:id                - Регион по ID
GET    /api/v1/weather/current/:region_id - Погода по региону
GET    /api/v1/weather/currentByCoords    - Погода по координатам
GET    /api/v1/forecast/:region_id        - Прогноз клева
GET    /health                            - Health check
```

### 3.4. Places Service (порт 8002)

```
GET    /api/v1/places               - Список мест (публичных)
GET    /api/v1/places/:id           - Детали места
POST   /api/v1/places               - Создать место
GET    /api/v1/places/my            - Мои места
PUT    /api/v1/places/my/:id        - Обновить место
DELETE /api/v1/places/my/:id        - Удалить место
GET    /health                      - Health check
```

---

## 4. Frontend страницы

### 4.1. Реализованные страницы

| Путь | Описание | Статус |
|------|----------|--------|
| `/` | Главная | ✅ |
| `/login` | Вход | ✅ |
| `/register` | Регистрация | ✅ |
| `/verify-email` | Подтверждение email | ✅ |
| `/reset-password` | Сброс пароля | ✅ |
| `/profile` | Профиль (Profile, Settings, My Places) | ✅ |
| `/map` | Карта мест | ✅ |
| `/resorts` | Список мест | ✅ |
| `/forecast` | Прогноз клева | ✅ |
| `/shop` | Магазин | 🚧 Заглушка |
| `/stores` | Магазины | 🚧 Заглушка |

---

## 5. Тестовые сценарии (Test Cases)

### 5.1. Аутентификация (Auth Service)

#### TC-AUTH-001: Регистрация пользователя
**Priority:** Critical

**Steps:**
1. POST `/api/v1/auth/register` с валидными данными
2. Проверить код ответа 200
3. Проверить создание пользователя в БД (is_verified=false)
4. Проверить отправку email (если ENABLE_EMAIL_SENDING=true)

**Test Data:**
```json
{
  "email": "test_{{timestamp}}@example.com",
  "username": "testuser_{{timestamp}}",
  "password": "Password123!"
}
```

**Expected Result:**
```json
{
  "success": true,
  "message": "Registration successful. Please check your email for verification code."
}
```

#### TC-AUTH-002: Регистрация с существующим email
**Priority:** High

**Steps:**
1. Зарегистрировать пользователя
2. Попытаться зарегистрировать с тем же email

**Expected Result:** 400 Bad Request
```json
{
  "error": {"code": "EMAIL_ALREADY_EXISTS"}
}
```

#### TC-AUTH-003: Регистрация с невалидным email
**Priority:** Medium

**Test Data:** `{"email": "invalid-email", "username": "test", "password": "pass123"}`

**Expected Result:** 422 Unprocessable Entity

#### TC-AUTH-004: Подтверждение email
**Priority:** Critical

**Preconditions:** Пользователь зарегистрирован, код верификации получен

**Steps:**
1. POST `/api/v1/auth/verify-email`
```json
{"email": "user@example.com", "code": "123456"}
```

**Expected Result:**
```json
{
  "success": true,
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### TC-AUTH-005: Неверный код верификации
**Priority:** High

**Steps:**
1. POST `/api/v1/auth/verify-email` с неверным кодом

**Expected Result:** 400 Bad Request
```json
{"error": {"code": "INVALID_OR_EXPIRED_CODE"}}
```

#### TC-AUTH-006: Превышение попыток верификации (3 попытки)
**Priority:** High

**Steps:**
1. 3 раза отправить неверный код
2. Проверить инвалидацию кода

**Expected Result:** После 3 попытки код инвалидирован

#### TC-AUTH-007: Вход в систему
**Priority:** Critical

**Preconditions:** Пользователь верифицирован

**Steps:**
1. POST `/api/v1/auth/login`
```json
{"email": "verified@example.com", "password": "Password123!"}
```

**Expected Result:**
```json
{
  "success": true,
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### TC-AUTH-008: Вход неверифицированного пользователя
**Priority:** High

**Expected Result:** 403 Forbidden
```json
{"error": {"code": "EMAIL_NOT_VERIFIED"}}
```

#### TC-AUTH-009: Вход с неверным паролем
**Priority:** High

**Expected Result:** 401 Unauthorized
```json
{"error": {"code": "INVALID_CREDENTIALS"}}
```

#### TC-AUTH-010: Сброс пароля
**Priority:** High

**Steps:**
1. POST `/api/v1/auth/reset-password/request`
2. Получить токен сброса
3. POST `/api/v1/auth/reset-password/confirm`

#### TC-AUTH-011: Получение профиля
**Priority:** High

**Steps:**
1. GET `/api/v1/users/me` с Bearer token

**Expected Result:** 200 OK с данными пользователя

#### TC-AUTH-012: Доступ без токена
**Priority:** Critical

**Steps:**
1. GET `/api/v1/users/me` без Authorization header

**Expected Result:** 401 Unauthorized

---

### 5.2. Places Service

#### TC-PLACE-001: Создание места
**Priority:** Critical

**Preconditions:** Пользователь авторизован

**Steps:**
1. POST `/api/v1/places` с данными места
```json
{
  "name": "Озеро Тестовое",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "place_type": "wild",
  "access_type": "car",
  "water_type": "lake",
  "fish_types": ["uuid1", "uuid2"],
  "visibility": "private"
}
```

**Expected Result:** 201 Created

#### TC-PLACE-002: Получение списка моих мест
**Priority:** High

**Steps:**
1. GET `/api/v1/places/my` с Bearer token

**Expected Result:** 200 OK с массивом мест

#### TC-PLACE-003: Обновление места
**Priority:** High

**Steps:**
1. PUT `/api/v1/places/my/{place_id}`

**Expected Result:** 200 OK

#### TC-PLACE-004: Удаление места
**Priority:** High

**Steps:**
1. DELETE `/api/v1/places/my/{place_id}`

**Expected Result:** 204 No Content

#### TC-PLACE-005: Попытка редактирования чужого места
**Priority:** Critical (Security)

**Steps:**
1. PUT `/api/v1/places/my/{other_user_place_id}`

**Expected Result:** 403 Forbidden

---

### 5.3. Forecast Service

#### TC-FC-001: Получение списка регионов
**Priority:** Medium

**Steps:**
1. GET `/api/v1/regions`

**Expected Result:** 200 OK с массивом 85 регионов России

#### TC-FC-002: Прогноз клева по региону
**Priority:** High

**Steps:**
1. GET `/api/v1/forecast/{region_id}`

**Expected Result:** 200 OK с прогнозом для видов рыб

#### TC-FC-003: Нерестовый период (bite_score = 0)
**Priority:** High

**Steps:**
1. Запросить прогноз в период нереста рыбы

**Expected Result:**
```json
{
  "is_spawn_period": true,
  "spawn_message": "Нерестовый период... — вылов запрещен",
  "bite_score": 0
}
```

---

### 5.4. Frontend E2E тесты

#### TC-E2E-001: Полный flow регистрации
**Priority:** Critical

**Steps:**
1. Открыть `/register`
2. Заполнить форму
3. Отправить
4. Перейти на `/verify-email`
5. Ввести код
6. Проверить редирект на главную
7. Проверить авторизацию

#### TC-E2E-002: Вход и выход
**Priority:** Critical

**Steps:**
1. Открыть `/login`
2. Войти с валидными данными
3. Проверить редирект
4. Выйти
5. Проверить редирект на `/login`

#### TC-E2E-003: Навигация по страницам
**Priority:** Medium

**Steps:**
1. Проверить доступность всех страниц
2. Проверить редиректы для неавторизованных

#### TC-E2E-004: Профиль пользователя
**Priority:** High

**Steps:**
1. Авторизоваться
2. Открыть `/profile`
3. Проверить отображение данных
4. Изменить профиль
5. Сохранить

---

## 6. Безопасность (Security Testing)

### 6.1. Известные уязвимости (из SECURITY_AUDIT.md)

| ID | Уязвимость | Статус | Приоритет тестирования |
|----|------------|--------|------------------------|
| SEC-001 | Hardcoded секреты | Open | Critical |
| SEC-002 | Hardcoded verification code "123456" | Open | Critical |
| SEC-003 | CORS wildcard | ✅ Fixed | Verify fix |
| SEC-004 | Отсутствие Rate Limiting | Open | High |

### 6.2. Security Test Cases

#### TC-SEC-001: Rate Limiting на auth endpoints
**Priority:** Critical

**Steps:**
1. Отправить 10+ запросов на `/api/v1/auth/login` с одного IP
2. Проверить блокировку (429 Too Many Requests)

**Current Status:** ❌ Не реализовано

#### TC-SEC-002: SQL Injection
**Priority:** Critical

**Test Data:**
```json
{"email": "admin'--@example.com", "password": "test"}
```

**Expected:** Ошибка валидации или безопасная обработка

#### TC-SEC-003: XSS в полях ввода
**Priority:** High

**Test Data:**
```json
{"name": "<script>alert('xss')</script>"}
```

**Expected:** Экранирование, не выполнение скрипта

#### TC-SEC-004: CORS Configuration
**Priority:** High

**Steps:**
1. OPTIONS запрос с Origin: evil.com
2. Проверить Access-Control-Allow-Origin

**Expected:** Только разрешенные origins

#### TC-SEC-005: JWT Token Validation
**Priority:** Critical

**Steps:**
1. Запрос с невалидным токеном
2. Запрос с истекшим токеном
3. Запрос с токеном без Bearer

**Expected:** 401 Unauthorized

#### TC-SEC-006: Hardcoded verification code
**Priority:** Critical

**Steps:**
1. При ENABLE_EMAIL_SENDING=false попробовать код "123456"

**Expected:** ❌ Сейчас работает - это баг!

---

## 7. Производительность (Performance Testing)

### 7.1. Требования к производительности

| Endpoint | Max Response Time | Notes |
|----------|-------------------|-------|
| Health check | < 50ms | - |
| Auth endpoints | < 200ms | - |
| Places CRUD | < 200ms | - |
| Forecast API | < 200ms | С кэшированием |
| Weather collection | < 5 min | Для 85 регионов |

### 7.2. Performance Test Cases

#### TC-PERF-001: Нагрузка на auth endpoints
**Steps:**
1. 100 одновременных запросов на `/login`
2. Замерить время ответа

**Expected:** < 200ms p95

#### TC-PERF-002: Кэширование погоды
**Steps:**
1. Первый запрос `/api/v1/weather/current/:region_id`
2. Второй запрос (из кэша)

**Expected:** Второй запрос значительно быстрее

---

## 8. Запуск тестов

### 8.1. Подготовка окружения

```bash
# Клонировать репозиторий
git clone <repo>
cd fishing-platform

# Скопировать .env
cp .env.example .env

# Запустить сервисы
docker-compose -f docker-compose.dev.yml up -d

# Проверить health
curl http://localhost:8001/health
curl http://localhost:8006/health
curl http://localhost:8007/health
```

### 8.2. Unit тесты (Backend)

```bash
# Auth Service
cd services/auth-service
pytest tests/ -v --cov=app

# Email Service
cd services/email-service
pytest tests/ -v

# Forecast Service
cd services/forecast-service
pytest tests/ -v --cov=app

# Places Service
cd services/places-service
pytest tests/ -v
```

### 8.3. E2E тесты (Frontend)

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск Playwright тестов
npx playwright test

# С UI режимом
npx playwright test --ui

# Конкретный тест
npx playwright test e2e/login.spec.ts
```

### 8.4. API тесты (curl/httpie)

```bash
# Регистрация
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"test","password":"Password123!"}'

# Вход
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Password123!"}'

# Профиль (с токеном)
curl http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 9. Баг-репортинг

### 9.1. Шаблон баг-репорта

```markdown
## Bug Report

**ID:** BUG-XXX
**Title:** Краткое описание
**Priority:** Critical / High / Medium / Low
**Severity:** Blocker / Critical / Major / Minor

### Environment
- OS: 
- Browser: 
- Service Version: 

### Steps to Reproduce
1. 
2. 
3. 

### Expected Result


### Actual Result


### Attachments
- Screenshot
- Logs
- Request/Response

### Root Cause (если известно)


### Related Requirements
- Ссылка на требования
```

### 9.2. Приоритеты

| Priority | Описание | SLA |
|----------|----------|-----|
| Critical | Блокирует основную функциональность | 4 часа |
| High | Влияет на важные функции | 24 часа |
| Medium | Влияет на UX | 3 дня |
| Low | Косметические дефекты | 1 неделя |

---

## 10. Чек-листы

### 10.1. Smoke Test Checklist

- [ ] Все сервисы отвечают на `/health`
- [ ] Регистрация нового пользователя
- [ ] Вход в систему
- [ ] Получение профиля
- [ ] Создание места
- [ ] Получение прогноза погоды
- [ ] Frontend загружается

### 10.2. Regression Test Checklist

- [ ] Auth: register → verify → login → profile
- [ ] Auth: password reset flow
- [ ] Places: CRUD операции
- [ ] Forecast: получение данных
- [ ] Security: CORS, JWT validation
- [ ] Performance: время ответа API

### 10.3. Pre-release Checklist

- [ ] Все unit тесты проходят
- [ ] Все E2E тесты проходят
- [ ] Нет критических багов
- [ ] Security audit пройден
- [ ] Performance тесты пройдены
- [ ] Документация обновлена

---

## 11. Документация для изучения

### 11.1. Обязательная документация

1. **README.md** - Общий обзор проекта
2. **ARCHITECTURE.md** - Архитектура микросервисов
3. **SECURITY_AUDIT.md** - Аудит безопасности
4. **SYSTEM_PROMPT.md** - Системный контекст

### 11.2. Требования (папка требования/)

**Функциональные требования:**
- `Требования_Прогноз_Клева_v2.0.md` - Прогноз клева
- `Требования_Мои_Места_v1.0.md` - Управление местами
- `US-PLACE-EDIT-001_...md` - Редактирование мест

**Безопасность:**
- `SEC-001_Управление_секретами.md`
- `SEC-002_Устранение_hardcoded_verification_code.md`
- `SEC-003_Безопасная_конфигурация_CORS.md`
- `SEC-004_Rate_Limiting_для_Auth_Endpoints.md`

**UI/UX:**
- `US-UI-IMPROVEMENTS-001_Улучшения_UX_v1.0.md`
- `US-FORECAST-UI-IMPROVEMENTS-001_...md`

### 11.3. Database Schema

См. `database/schema.md` - документация схемы БД

**Реализованные таблицы:**
- `users` - Пользователи
- `refresh_tokens` - Refresh токены
- `email_verification_codes` - Коды верификации
- `regions` - 85 регионов России
- `weather_data` - Погодные данные
- `fishing_forecasts` - Прогнозы клева
- `fish_bite_settings` - Настройки клева
- `places` - Места рыбалки

---

## 12. Контакты и эскалация

### 12.1. Кому сообщать о багах

1. Создать issue в GitHub репозитории
2. Для критических багов - немедленно уведомить команду

### 12.2. Процесс ревью

1. QA создает баг-репорт
2. Разработчик назначается
3. Fix → Verify → Close

---

## 13. Ключевые принципы тестирования

1. **Всегда проверяйте статус сервиса** - используйте `/health` endpoints
2. **Изучайте требования перед тестированием** - папка `требования/`
3. **Тестируйте security** - см. SECURITY_AUDIT.md
4. **Проверяйте граничные случаи** - пустые данные, максимальные значения
5. **Документируйте воспроизводимость** - шаги, данные, окружение
6. **Регрессионное тестирование** - после каждого фикса
7. **Проверяйте интеграции** - Frontend ↔ Backend ↔ Database

---

*Документ создан для QA Engineer. Обновлять при изменении функциональности.*

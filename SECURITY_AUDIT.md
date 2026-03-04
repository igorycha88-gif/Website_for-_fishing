# Аудит безопасности проекта FishMap

**Дата:** 2026-02-21  
**Статус:** Требуется исправление

---

## Обнаруженные уязвимости

### КРИТИЧЕСКИЙ УРОВЕНЬ

#### 1. Hardcoded секреты в конфигурационных файлах
**Файл:** `.env`  
**Описание:** Файл содержит реальные секретные значения:
- `SMTP_PASSWORD` - (пароль от Yandex почты)
- `SECRET_KEY` - (слабый ключ подписи JWT)
- `OPENWEATHERMAP_API_KEY` - (API ключ)

**Риск:** Компрометация email аккаунта, подделка JWT токенов, несанкционированный доступ к внешним API.

**Рекомендации:**
- Немедленно сменить все секреты
- Использовать Docker Secrets или внешние системы управления секретами (HashiCorp Vault, AWS Secrets Manager)
- Генерировать криптографически стойкий SECRET_KEY (min 32 символа)
- Добавить `.env` в `.gitignore` (уже есть, но проверить отсутствие в истории коммитов)

---

#### 2. Hardcoded verification code в продакшене
**Файл:** `services/auth-service/app/endpoints/auth.py:104,107`  
**Описание:** При отключенной отправке email или ошибке используется hardcoded код верификации "123456".

```python
except Exception as e:
    code = "123456"
else:
    code = "123456"
```

**Риск:** Любой может верифицировать любой email без доступа к почте.

**Рекомендации:**
- Удалить hardcoded код
- При недоступности email сервиса возвращать ошибку, а не fallback код
- Блокировать регистрацию если email сервис недоступен

---

### ВЫСОКИЙ УРОВЕНЬ

#### 3. CORS разрешает все origins ~~(ИСПРАВЛЕНО: SEC-003)~~
**Файлы:** 
- `services/auth-service/app/main.py:19`
- `services/places-service/app/main.py:31`

**Описание:** 
```python
allow_origins=["*"],
allow_credentials=True,
```

**Риск:** Позволяет любому сайту делать запросы к API с credentials, что открывает возможность для CSRF и кражи данных пользователей.

**Статус:** ✅ ИСПРАВЛЕНО (2026-02-21)
- Добавлена переменная `CORS_ORIGINS` в `.env`
- Реализован `cors_origins_list` в config.py с валидацией
- Development режим автоматически добавляет localhost origins
- Production режим требует явного указания origins
- Написаны unit тесты

**Рекомендации:** ~~Указать конкретные разрешенные домены~~ (выполнено)

---

#### 4. Отсутствие Rate Limiting ~~(ИСПРАВЛЕНО: SEC-004)~~
**Файлы:** Все auth endpoints  
**Описание:** ~~Нет ограничений на количество запросов к критическим endpoints:~~
- `/api/v1/auth/login`
- `/api/v1/auth/register`
- `/api/v1/auth/reset-password/request`
- `/api/v1/auth/verify-email`

**Риск:** ~~Brute-force атаки на пароли, DDoS, перебор verification codes.~~

**Статус:** ✅ ИСПРАВЛЕНО (2026-02-24)
**Реализация:** `требования/SEC-004_Rate_Limiting_для_Auth_Endpoints.md`
- `/login`: 5 req/min — защита от brute-force
- `/register`: 10 req/hour — защита от массовой регистрации
- `/reset-password/request`: 3 req/hour — защита от email flooding
- `/verify-email`: 5 req/min — защита от перебора кодов
- Библиотека: fastapi-limiter (Redis-based, Sliding Window)

**Рекомендации:** ~~Реализовать rate limiting через Redis...~~ (выполнено)

---

#### 5. Публичный endpoint генерации кодов ✅ (ИСПРАВЛЕНО: SEC-005)
**Файл:** `services/email-service/app/api/v1/router.py`  
**Описание:** `/api/v1/email/generate-code` и `/api/v1/email/send` ~~доступны без аутентификации.~~

**Риск:** ~~Несанкционированная генерация кодов, использование email сервиса для спама.~~

**Статус:** ✅ ИСПРАВЛЕНО (2026-03-02)
**Реализация:** `требования/SEC-005_Защита_Email_Service_API.md`
- API Key аутентификация через заголовок `X-API-Key`
- Защита обоих endpoints: `/generate-code` и `/send`
- Environment variable storage (`EMAIL_SERVICE_API_KEY`)
- Key validation (min 32 chars)
- Unit тесты (19 тестов) + Integration тесты (6 тестов)
- Auth Service передает `X-API-Key` при вызове Email Service

**Рекомендации:** ~~Требовать аутентификацию для endpoints~~ (выполнено)

---

### ВЫСОКИЙ УРОВЕНЬ

#### 6. Отсутствие JWT blacklist / token invalidation ✅ (ИСПРАВЛЕНО: SEC-006)
**Файл:** `services/auth-service/app/core/security.py`  
**Описание:** ~~JWT токены не могут быть отозваны. Нет механизма blacklist.~~

**Риск:** ~~Украденный токен валиден до истечения expiration time (30 минут).~~

**Статус:** ✅ ИСПРАВЛЕНО (2026-03-03)
**Реализация:** `требования/SEC-006_JWT_Blacklist_Token_Invalidation.md`
- Redis blacklist для отозванных токенов (jti)
- POST /api/v1/auth/logout — инвалидация токена через Redis blacklist
- POST /api/v1/auth/refresh — refresh token rotation (новая пара токенов)
- Token version (ver) в БД для инвалидации всех токенов при смене пароля
- JWT payload расширен: jti (UUID), type (access|refresh), ver (token_version)
- Новые поля в refresh_tokens: revoked, revoked_at, replaced_by, jti
- Проверка blacklist и token_version при каждом запросе
- Frontend: автоматический refresh при 401, вызов /logout API
- Unit тесты: 19 тестов (token_blacklist + JWT format)

**Рекомендации:** ~~Реализовать token blacklist в Redis...~~ (выполнено)

---

#### 7. Слабые требования к паролю
**Файл:** `services/auth-service/app/schemas/auth.py:68`  
**Описание:** Только `min_length=8`, нет требований к сложности.

**Риск:** Пользователи могут использовать слабые пароли.

**Рекомендации:**
- Минимум 12 символов
- Требовать: uppercase, lowercase, digit, special character
- Проверять против списка common passwords
- Использовать zxcvbn для оценки сложности

---

#### 8. Password reset token не инвалидируется ⏳ (Требования согласованы: SEC-008)
**Файл:** `services/auth-service/app/endpoints/auth.py:277-314`  
**Описание:** ~~Токен сброса пароля можно использовать повторно до истечения (1 час).~~

**Риск:** ~~Если ссылка перехвачена, attacker может сбросить пароль даже после первого использования.~~

**Статус:** ⏳ Требования согласованы (2026-03-03)
**Реализация:** `требования/SEC-008_Password_Reset_Token_Invalidation.md`
- Database-based tokens (таблица `password_reset_tokens`)
- 64-char криптографический токен (bcrypt хеширование)
- Guaranteed invalidation после использования (флаг `used`)
- Максимум 1 активный токен на пользователя
- Email уведомление после успешного сброса пароля
- IP logging (ip_address, user_agent) для audit trail
- Frontend страница `/reset-password`

**Рекомендации:** ~~Хранить использованные reset tokens в БД с флагом used...~~ (согласовано, awaiting implementation)

---

#### 9. Отсутствие CSRF защиты ⏳ (Требования согласованы: SEC-009)
**Описание:** ~~Нет CSRF токенов для state-changing операций.~~

**Риск:** ~~Злоумышленник может выполнить действие от имени авторизованного пользователя.~~

**Статус:** ⏳ Требования согласованы (2026-03-03)
**Реализация:** `требования/SEC-009_CSRF_Protection.md`
- Synchronizer Token Pattern + Redis Storage
- CSRF токен в ответе /login, /verify-email, /refresh
- X-CSRF-Token header для всех POST/PUT/DELETE/PATCH запросов
- Redis key: `csrf:{user_id}` с TTL 24 часа
- CSRF Middleware для валидации токенов
- Инвалидация при logout и смене пароля
- Frontend: автоматическое добавление X-CSRF-Token header

**Рекомендации:** ~~Реализовать CSRF токены...~~ (согласовано, awaiting implementation)

---

#### 10. Middleware прокидывает все заголовки ⏳ (Требования согласованы: SEC-010)
**Файл:** `frontend/middleware.ts:23-27`  
**Описание:** ~~Проксирование всех headers без фильтрации.~~

```typescript
request.headers.forEach((value, key) => {
  if (lowerKey !== 'host' && lowerKey !== 'content-length') {
    headers.set(key, value);
  }
});
```

**Риск:** ~~HTTP Request Smuggling, Header Injection.~~

**Статус:** ⏳ Требования согласованы (2026-03-03)
**Реализация:** `требования/SEC-010_Middleware_Header_Filtering.md`
- Whitelist подход к фильтрации заголовков
- CRLF injection validation (защита от `\r`, `\n`)
- Middleware генерирует X-Forwarded-For/Proto/Host (игнорирует от клиента)
- Distributed tracing поддержка (x-request-id, x-correlation-id)
- Security logging заблокированных заголовков (dev/staging)
- Конфигурируемый whitelist через PROXY_ALLOWED_HEADERS env
- Unit + Integration тесты
- Документация security practices

**Рекомендации:** ~~Явно указать whitelist разрешенных headers...~~ (согласовано, awaiting implementation)

---

### СРЕДНИЙ УРОВЕНЬ

#### 11. Информационная утечка в error messages
**Файл:** `services/auth-service/app/endpoints/auth.py`  
**Описание:** Детальные ошибки раскрывают внутреннюю структуру.

**Рекомендации:**
- Логировать детали ошибки, возвращать generic message
- Не раскрывать существование email/username в системе

---

#### 12. Отсутствие Content Security Policy
**Описание:** Нет CSP headers в ответах.

**Рекомендации:**
- Добавить CSP header с whitelist источников
- Настроить для frontend и API

---

#### 13. Email verification - лимит попыток
**Файл:** `services/auth-service/app/endpoints/auth.py:131-147`  
**Описание:** После 3 попыток код остается валидным до истечения.

**Рекомендации:**
- Инвалидировать код после 3 неудачных попыток
- Генерировать новый код после исчерпания попыток

---

#### 14. Слабый SECRET_KEY по умолчанию
**Файл:** `.env.example:11`  
**Описание:** Placeholder "your-secret-key-change-in-production-min-32-chars" может быть использован в production.

**Рекомендации:**
- Приложение не должно запускаться с дефолтным ключом
- Добавить проверку при старте

---

### НИЗКИЙ УРОВЕНЬ

#### 15. Логирование чувствительных данных
**Файл:** Logging middleware во всех сервисах  
**Описание:** Возможно логирование headers с токенами, паролей в request body.

**Рекомендации:**
- Исключить Authorization header из логов
- Маскировать чувствительные поля (password, token)

---

#### 16. Отсутствие security headers
**Описание:** Не установлены headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Strict-Transport-Security (HSTS)
- X-XSS-Protection

**Рекомендации:**
- Добавить middleware для установки security headers
- Настроить HSTS с max-age минимум 1 год

---

## Положительные аспекты

1. `.env` файл добавлен в `.gitignore`
2. Используется Docker Secrets в docker-compose.yml
3. Пароли хешируются с pbkdf2_sha256
4. JWT с expiration time
5. SQLAlchemy ORM предотвращает SQL injection
6. Pydantic валидация входных данных
7. Email verification обязательна для входа

---

## План исправления (приоритеты)

### Фаза 1 (немедленно)
1. Сменить все секреты в `.env` ✅
2. Удалить hardcoded "123456" код ✅
3. Настроить CORS для конкретных доменов ✅ (SEC-003)
4. Добавить rate limiting на auth endpoints ✅ (SEC-004)
5. Защитить Email Service API ✅ (SEC-005)
6. Реализовать JWT blacklist ✅ (SEC-006)

### Фаза 2 (в течение недели)
5. Улучшить валидацию паролей
6. Инвалидация password reset tokens ⏳ (Требования согласованы: SEC-008)
7. Добавить CSRF защиту ⏳ (Требования согласованы: SEC-009)
8. Middleware header filtering ⏳ (Требования согласованы: SEC-010)

### Фаза 3 (в течение месяца)
8. Настроить security headers
9. Реализовать CSP
10. Audit логирования
11. Penetration testing

---

## Контакт для вопросов

При возникновении вопросов по данному аудиту обратитесь к команде разработки.

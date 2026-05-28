# Требования: Устранение hardcoded verification code

**ID:** SEC-002  
**Version:** 1.0  
**Status:** Approved  
**Date:** 2026-02-21  
**Author:** System Analyst  
**Priority:** Critical  

---

## 1. Обзор

### 1.1 Проблема

В коде auth-service обнаружена критическая уязвимость ( CWE-798: Use of Hard-coded Credentials):

**Файл:** `services/auth-service/app/endpoints/auth.py:104,107`

```python
except Exception as e:
    code = "123456"  # CRITICAL: Hardcoded verification code
else:
    code = "123456"  # CRITICAL: Hardcoded verification code
```

### 1.2 Риск

Любой атакующий может верифицировать любой email-адрес без доступа к почтовому ящику, просто указав код "123456". Это позволяет:
- Регистрировать аккаунты на чужие email
- Обходить верификацию email
- Потенциально захватывать аккаунты

### 1.3 Цель

Устранить hardcoded verification code, сохранив возможность локальной разработки и тестирования.

---

## 2. Функциональные требования

### FR1. Строгий режим email-верификации (Production)

**Приоритет:** Critical

**Описание:**
При недоступности email-сервиса регистрация должна завершаться ошибкой.

**Требования:**
- При исключении при отправке email → HTTP 503 Service Unavailable
- Verification code НЕ сохраняется в БД
- Регистрация считается неуспешной
- Ошибка логируется с уровнем CRITICAL для алертинга

**Acceptance Criteria:**
```
Given: Email сервис недоступен (SMTP ошибка)
When: Пользователь пытается зарегистрироваться
Then: Возвращается HTTP 503
And: Код верификации не сохраняется в БД
And: В логах запись уровня CRITICAL
```

### FR2. Development режим с whitelist доменов

**Приоритет:** High

**Описание:**
Для локальной разработки и тестирования разрешить fallback коды только для email-адресов из whitelist домена.

**Требования:**
- Переменная окружения `ENVIRONMENT` управляет режимом (`development` / `production`)
- Переменная `DEV_EMAIL_DOMAIN` задаёт разрешённый домен (default: `test.localhost`)
- При `ENVIRONMENT=development` и email оканчивается на `@{DEV_EMAIL_DOMAIN}`:
  - Генерируется случайный код через `secrets.token_hex(3)` (6 hex символов)
  - Код отправляется в лог (для разработчика)
- При `ENVIRONMENT=production` whitelist игнорируется, строгий режим

**Acceptance Criteria:**
```
Given: ENVIRONMENT=development
And: DEV_EMAIL_DOMAIN=test.localhost
And: Email заканчивается на @test.localhost
When: Пользователь регистрируется
Then: Генерируется случайный код
And: Код логируется в INFO
And: Код сохраняется в БД
And: Регистрация успешна
```

```
Given: ENVIRONMENT=production
And: Email сервис недоступен
When: Пользователь регистрируется
Then: Возвращается HTTP 503
And: Hardcoded код "123456" НЕ используется
```

### FR3. Структурированный ответ об ошибке

**Приоритет:** Medium

**Описание:**
При ошибке email-сервиса возвращать понятный структурированный ответ.

**Response Schema:**
```json
{
  "error": {
    "code": "EMAIL_SERVICE_UNAVAILABLE",
    "message": "Сервис верификации временно недоступен. Попробуйте позже."
  }
}
```

**HTTP Status:** 503 Service Unavailable

---

## 3. Технические требования

### 3.1 Изменения в settings.py

Добавить новые переменные окружения:

```python
class Settings(BaseSettings):
    ENVIRONMENT: str = "production"
    DEV_EMAIL_DOMAIN: str = "test.localhost"
```

### 3.2 Новое исключение

```python
class EmailServiceUnavailableError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "EMAIL_SERVICE_UNAVAILABLE",
                    "message": "Сервис верификации временно недоступен. Попробуйте позже."
                }
            }
        )
```

### 3.3 Изменения в auth.py (register endpoint)

**До (уязвимый код):**
```python
try:
    async with httpx.AsyncClient() as client:
        await client.post(...)
except Exception as e:
    code = "123456"  # VULNERABILITY
else:
    code = "123456"  # VULNERABILITY
```

**После (безопасный код):**
```python
import secrets

try:
    async with httpx.AsyncClient() as client:
        await client.post(...)
    logger.info("Email sent successfully", email=request.email)
except Exception as e:
    logger.critical(
        "Email service unavailable during registration",
        email=request.email,
        error=str(e),
        exc_info=True,
    )
    raise EmailServiceUnavailableError()

# Handle EMAIL_ENABLED=False case
if not settings.EMAIL_ENABLED:
    if settings.ENVIRONMENT == "development":
        if request.email.endswith(f"@{settings.DEV_EMAIL_DOMAIN}"):
            code = secrets.token_hex(3).upper()  # 6 random hex chars
            logger.info(
                "Dev mode: generated test verification code",
                email=request.email,
                code=code,  # Logged for developer convenience
            )
        else:
            logger.warning(
                "Dev mode: email not in whitelist",
                email=request.email,
                required_domain=settings.DEV_EMAIL_DOMAIN,
            )
            raise EmailServiceUnavailableError()
    else:
        # Production mode - no fallback
        logger.critical(
            "Email sending disabled in production mode",
            email=request.email,
        )
        raise EmailServiceUnavailableError()
```

### 3.4 Обновление .env.example

```bash
# Environment mode: development | production
ENVIRONMENT=production

# Development email domain whitelist (only used when ENVIRONMENT=development)
# Emails ending with @test.localhost will receive test codes
DEV_EMAIL_DOMAIN=test.localhost
```

---

## 4. Не-функциональные требования

### 4.1 Security (Безопасность)

| Требование | Значение |
|------------|----------|
| CWE ID | CWE-798 (Hard-coded Credentials) |
| Severity | Critical |
| Mitigation | Удаление hardcoded кодов, строгий режим |
| Random Generation | `secrets.token_hex()` (криптографически стойкий) |

### 4.2 Performance (Производительность)

| Метрика | Значение |
|---------|----------|
| Latency | Без изменений (< 200ms) |
| Overhead | ~1ms для генерации случайного кода |

### 4.3 Monitoring (Мониторинг)

| Событие | Уровень логирования | Действие |
|---------|---------------------|----------|
| Email сервис недоступен | CRITICAL | Алерт в мониторинг |
| Dev режим: генерация тестового кода | INFO | Для отладки |
| Dev режим: email не в whitelist | WARNING | Для отладки |
| Email отправлен успешно | INFO | Стандарт |

---

## 5. Тестирование

### 5.1 Unit тесты

```python
# tests/test_auth_security.py

async def test_no_hardcoded_code_on_smtp_failure():
    """При ошибке SMTP должен возвращаться 503, а не fallback код"""
    with mock.patch("httpx.AsyncClient.post", side_effect=Exception("SMTP error")):
        response = await client.post("/api/v1/auth/register", json={
            "email": "user@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        })
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "EMAIL_SERVICE_UNAVAILABLE"

async def test_dev_mode_whitelist_domain():
    """В dev режиме whitelist домен получает случайный код"""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "development", "DEV_EMAIL_DOMAIN": "test.localhost"}):
        with mock.patch("httpx.AsyncClient.post", side_effect=Exception("SMTP error")):
            response = await client.post("/api/v1/auth/register", json={
                "email": "user@test.localhost",
                "username": "testuser",
                "password": "SecurePass123!"
            })
            # В dev режиме с whitelist - регистрация успешна
            assert response.status_code == 200

async def test_dev_mode_non_whitelist_domain():
    """В dev режиме НЕ-whitelist домен получает 503"""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "development", "DEV_EMAIL_DOMAIN": "test.localhost"}):
        with mock.patch("httpx.AsyncClient.post", side_effect=Exception("SMTP error")):
            response = await client.post("/api/v1/auth/register", json={
                "email": "user@example.com",
                "username": "testuser",
                "password": "SecurePass123!"
            })
            assert response.status_code == 503

async def test_production_mode_no_fallback():
    """В production режиме НИКОГДА не используется fallback код"""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        with mock.patch("httpx.AsyncClient.post", side_effect=Exception("SMTP error")):
            response = await client.post("/api/v1/auth/register", json={
                "email": "user@test.localhost",
                "username": "testuser",
                "password": "SecurePass123!"
            })
            assert response.status_code == 503
```

### 5.2 Integration тесты

```python
async def test_verification_code_not_123456():
    """Проверить, что код '123456' больше не работает"""
    # Регистрируем пользователя
    await client.post("/api/v1/auth/register", json={...})
    
    # Пытаемся верифицировать с hardcoded кодом
    response = await client.post("/api/v1/auth/verify-email", json={
        "email": "user@example.com",
        "code": "123456"
    })
    assert response.status_code == 400
    assert "invalid" in response.json()["error"]["message"].lower()
```

### 5.3 Security тесты (Penetration testing)

| Тест | Ожидаемый результат |
|------|---------------------|
| Попытка верификации с "123456" | HTTP 400, код невалиден |
| Регистрация при недоступном SMTP | HTTP 503 |
| Dev режим с whitelist email | HTTP 200, код в логах |
| Production режим при любом сбое | HTTP 503 |

---

## 6. План внедрения

### Фаза 1: Подготовка (1 час)

- [ ] Добавить переменные `ENVIRONMENT`, `DEV_EMAIL_DOMAIN` в settings.py
- [ ] Создать исключение `EmailServiceUnavailableError`
- [ ] Обновить `.env.example`

### Фаза 2: Реализация (2 часа)

- [ ] Изменить логику в `auth.py` (register endpoint)
- [ ] Удалить hardcoded "123456"
- [ ] Добавить логирование CRITICAL уровня

### Фаза 3: Тестирование (1 час)

- [ ] Написать unit тесты
- [ ] Написать integration тесты
- [ ] Ручное тестирование сценариев

### Фаза 4: Деплой (30 минут)

- [ ] Установить `ENVIRONMENT=production` на проде
- [ ] Установить `ENVIRONMENT=development` локально
- [ ] Проверить логи после деплоя

---

## 7. Rollback план

При критических проблемах после деплоя:

1. Откатить изменения в `auth.py` через git revert
2. Перезапустить auth-service
3. Проверить работу регистрации

---

## 8. Definition of Done

- [ ] Hardcoded "123456" удалён из кода
- [ ] Добавлены переменные окружения ENVIRONMENT, DEV_EMAIL_DOMAIN
- [ ] Создано исключение EmailServiceUnavailableError
- [ ] Unit тесты написаны и проходят
- [ ] Integration тесты проходят
- [ ] .env.example обновлён
- [ ] Документация обновлена
- [ ] Code review пройден
- [ ] Развёрнуто в production

---

## 9. Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Email сервис SPOF | Medium | High | Retry механизм, мониторинг |
| Разработчики не могут тестировать локально | Low | Medium | Whitelist домен для dev |
| False positive 503 при временных сбоях | Low | Low | Retry на стороне клиента |

---

## 10. Ссылки

- **Security Audit:** `SECURITY_AUDIT.md` (пункт 2)
- **CWE-798:** https://cwe.mitre.org/data/definitions/798.html
- **OWASP:** https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password

---

**Согласовано:** 2026-02-21  
**Статус:** Approved

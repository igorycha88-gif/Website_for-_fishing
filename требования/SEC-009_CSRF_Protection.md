# SEC-009: CSRF Protection

**ID:** SEC-009  
**Version:** 1.0  
**Status:** Approved  
**Author:** System Analyst  
**Date:** 2026-03-03  
**Priority:** High  
**Approved Date:** 2026-03-03

---

## 1. Executive Summary

### 1.1 Проблема

Отсутствие CSRF (Cross-Site Request Forgery) защиты создает следующие риски:

| Сценарий | Attack Vector | Последствие |
|----------|---------------|-------------|
| Пользователь на fishing.com | Открывает вредоносный сайт evil.com | Evil.com отправляет скрытый POST на fishing.com/api/v1/users/me |
| Злоумышленник создает форму | Auto-submit форма на evil.com | Изменение профиля, email, пароля жертвы |
| JWT token в localStorage | Автоматически отправляется с fetch() | Атака успешна без ведома пользователя |
| Password reset | CSRF атака на /reset-password/confirm | Смена пароля жертвы |

**Отсылка к аудиту:** SECURITY_AUDIT.md, раздел 9 "Отсутствие CSRF защиты"

### 1.2 Решение

Реализовать CSRF защиту через Synchronizer Token Pattern + Redis Storage:

| Компонент | Решение |
|-----------|---------|
| CSRF Token Generation | secrets.token_urlsafe(32) - 43 chars |
| Token Storage | Redis с TTL 24 часа |
| Token Delivery | В ответе /login, /verify-email, /refresh |
| Token Validation | Middleware проверяет X-CSRF-Token header |
| Token Invalidation | При logout, смене пароля, login на другом устройстве |
| SameSite Attribute | Lax для cookies (если используются в будущем) |

---

## 2. Scope

### 2.1 In Scope

- Модуль `csrf_protection.py` для генерации/валидации токенов
- CSRF Middleware для проверки всех POST/PUT/DELETE/PATCH запросов
- Интеграция в /login, /verify-email, /refresh, /logout endpoints
- Frontend: автоматическое добавление X-CSRF-Token header
- Redis key format: `csrf:{user_id}`
- Unit и integration тесты
- Документация

### 2.2 Out of Scope

- SameSite cookies (будет реализовано при переходе на cookie-based auth)
- Origin/Referer validation (опциональная мера)
- CSRF защита для других сервисов (Places, Reports) - в будущих итерациях
- Multi-device session management UI
- Webhook notifications о CSRF попытках

---

## 3. User Stories

### US1: Пользователь получает CSRF токен при логине

**As a** User  
**I want to** получать CSRF токен автоматически при входе  
**So that** мои запросы защищены от CSRF атак

**Priority:** High  
**Actors:** User

**Acceptance Criteria:**

**AC1.1: Login возвращает CSRF токен**
- Given валидные credentials
- When отправляет POST /api/v1/auth/login
- Then response содержит access_token
- And response содержит csrf_token (43 chars)
- And csrf_token сохранен в Redis с ключом `csrf:{user_id}`
- And TTL = 24 часа

**AC1.2: Verify-email возвращает CSRF токен**
- Given валидный verification code
- When отправляет POST /api/v1/auth/verify-email
- Then response содержит csrf_token

**AC1.3: Refresh возвращает CSRF токен**
- Given валидный refresh token
- When отправляет POST /api/v1/auth/refresh
- Then response содержит новый csrf_token
- And старый csrf_token инвалидирован

---

### US2: Защищенный запрос с CSRF токеном

**As a** User  
**I want to** отправлять защищенные запросы  
**So that** злоумышленник не может выполнить действия от моего имени

**Priority:** High  
**Actors:** User

**Acceptance Criteria:**

**AC2.1: Успешный запрос с валидным CSRF токеном**
- Given пользователь авторизован
- And имеет валидный csrf_token
- When отправляет POST /api/v1/users/me
- And headers включают X-CSRF-Token: <csrf_token>
- Then CSRF middleware проверяет токен
- And request успешно обработан

**AC2.2: Запрос без CSRF токена**
- Given пользователь авторизован
- When отправляет POST /api/v1/users/me
- And X-CSRF-Token header отсутствует
- Then response возвращает 403 Forbidden
- And error code = CSRF_TOKEN_MISSING

**AC2.3: Запрос с невалидным CSRF токеном**
- Given пользователь авторизован
- When отправляет POST /api/v1/users/me
- And X-CSRF-Token: invalid_token
- Then response возвращает 403 Forbidden
- And error code = CSRF_TOKEN_INVALID

**AC2.4: GET запросы не требуют CSRF**
- Given пользователь авторизован
- When отправляет GET /api/v1/users/me
- Then CSRF проверка не выполняется
- And request успешно обработан

---

### US3: CSRF атака заблокирована

**As a** User  
**I want to** быть защищенным от CSRF атак  
**So that** злоумышленник не может выполнить действия от моего имени

**Priority:** High  
**Actors:** User, Attacker

**Acceptance Criteria:**

**AC3.1: Cross-site форма заблокирована**
- Given пользователь авторизован на fishing.com
- And открывает evil.com
- When evil.com отправляет скрытую форму на fishing.com/api/v1/users/me
- And форма не содержит X-CSRF-Token header (browser security)
- Then CSRF middleware возвращает 403
- And malicious request заблокирован

**AC3.2: Логирование CSRF попыток**
- Given CSRF атака обнаружена
- When middleware блокирует запрос
- Then логируется warning с client_ip, user_id, endpoint
- And incident записывается для анализа

---

### US4: Инвалидация CSRF токена

**As a** User  
**I want to** чтобы мой CSRF токен инвалидировался при критичных событиях  
**So that** старые токены нельзя использовать

**Priority:** High  
**Actors:** User

**Acceptance Criteria:**

**AC4.1: Logout инвалидирует CSRF токен**
- Given пользователь авторизован
- When отправляет POST /api/v1/auth/logout
- Then csrf_token удаляется из Redis
- And последующие запросы с этим токеном возвращают 403

**AC4.2: Смена пароля инвалидирует CSRF токен**
- Given пользователь меняет пароль
- When отправляет POST /api/v1/auth/reset-password/confirm
- Then csrf_token удаляется из Redis
- And пользователь должен заново логиниться

---

## 4. Технические требования

### 4.1 Redis Key Format

| Key Pattern | Value | TTL | Описание |
|-------------|-------|-----|----------|
| `csrf:{user_id}` | `{csrf_token}` | 86400 (24h) | CSRF токен пользователя |

**Пример:**
```
Key: csrf:123e4567-e89b-12d3-a456-426614174000
Value: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1
TTL: 86400
```

### 4.2 Token Generation

```python
import secrets

def generate_csrf_token() -> str:
    """
    Генерирует криптографически стойкий CSRF токен.
    
    Returns:
        str: 43-char токен (secrets.token_urlsafe(32))
    """
    return secrets.token_urlsafe(32)  # 32 bytes = 43 chars base64
```

### 4.3 Request Headers

**Protected Request Example:**
```http
POST /api/v1/users/me HTTP/1.1
Host: fishing.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-CSRF-Token: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe"
}
```

### 4.4 Response Format (Login)

```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "csrf_token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4.5 Error Responses

**CSRF Token Missing:**
```json
{
  "error": {
    "code": "CSRF_TOKEN_MISSING",
    "message": "CSRF token is required for this request"
  }
}
```

**CSRF Token Invalid:**
```json
{
  "error": {
    "code": "CSRF_TOKEN_INVALID",
    "message": "Invalid CSRF token"
  }
}
```

### 4.6 Структура файлов

```
services/auth-service/
├── app/
│   ├── core/
│   │   ├── csrf_protection.py     # NEW: CSRF token management
│   │   └── config.py              # + CSRF settings
│   ├── middleware/
│   │   └── csrf.py                # NEW: CSRF Middleware
│   ├── endpoints/
│   │   └── auth.py                # Modified: /login, /logout, /refresh
│   └── main.py                    # Modified: Register CSRF middleware
```

### 4.7 Переменные окружения

```bash
# CSRF Protection
CSRF_TOKEN_TTL=86400  # 24 hours in seconds
CSRF_ENABLED=true     # Enable/disable CSRF protection
```

### 4.8 Module: csrf_protection.py

```python
# services/auth-service/app/core/csrf_protection.py

import secrets
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging_config import get_logger
from typing import Optional

logger = get_logger(__name__)


class CSRFProtection:
    """
    CSRF Protection using Synchronizer Token Pattern.
    
    Stores CSRF tokens in Redis with TTL.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "csrf"
        self.ttl = settings.CSRF_TOKEN_TTL  # 86400 (24h)
    
    async def generate_token(self, user_id: str) -> str:
        """
        Generate CSRF token and store in Redis.
        
        Args:
            user_id: User UUID
        
        Returns:
            str: 43-char CSRF token
        """
        token = secrets.token_urlsafe(32)  # 43 chars
        key = f"{self.prefix}:{user_id}"
        
        await self.redis.setex(key, self.ttl, token)
        
        logger.info(
            "CSRF token generated",
            user_id=user_id,
            ttl=self.ttl
        )
        
        return token
    
    async def validate_token(self, user_id: str, token: str) -> bool:
        """
        Validate CSRF token against Redis.
        
        Args:
            user_id: User UUID
            token: CSRF token from request
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not token:
            logger.warning("CSRF token missing", user_id=user_id)
            return False
        
        key = f"{self.prefix}:{user_id}"
        stored = await self.redis.get(key)
        
        if not stored:
            logger.warning("CSRF token not found in Redis", user_id=user_id)
            return False
        
        # Constant-time comparison to prevent timing attacks
        stored_str = stored.decode() if isinstance(stored, bytes) else stored
        
        if not secrets.compare_digest(stored_str, token):
            logger.warning(
                "CSRF token mismatch",
                user_id=user_id,
                expected_prefix=stored_str[:8],
                received_prefix=token[:8]
            )
            return False
        
        logger.debug("CSRF token validated", user_id=user_id)
        return True
    
    async def invalidate_token(self, user_id: str) -> bool:
        """
        Invalidate CSRF token (delete from Redis).
        
        Args:
            user_id: User UUID
        
        Returns:
            bool: True if deleted, False if not found
        """
        key = f"{self.prefix}:{user_id}"
        deleted = await self.redis.delete(key)
        
        if deleted:
            logger.info("CSRF token invalidated", user_id=user_id)
        else:
            logger.debug("CSRF token not found for invalidation", user_id=user_id)
        
        return deleted > 0
    
    async def refresh_token(self, user_id: str) -> str:
        """
        Refresh CSRF token (invalidate old, generate new).
        
        Args:
            user_id: User UUID
        
        Returns:
            str: New CSRF token
        """
        await self.invalidate_token(user_id)
        return await self.generate_token(user_id)


# Global instance
_csrf_protection: Optional[CSRFProtection] = None


def get_csrf_protection() -> CSRFProtection:
    """Get global CSRF protection instance."""
    global _csrf_protection
    if _csrf_protection is None:
        raise RuntimeError("CSRF protection not initialized. Call init_csrf_protection() first.")
    return _csrf_protection


async def init_csrf_protection(redis_client: redis.Redis):
    """Initialize global CSRF protection instance."""
    global _csrf_protection
    _csrf_protection = CSRFProtection(redis_client)
    logger.info("CSRF protection initialized")
```

### 4.9 Middleware: csrf.py

```python
# services/auth-service/app/middleware/csrf.py

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_access_token
from app.core.csrf_protection import get_csrf_protection
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware.
    
    Validates CSRF token for all state-changing requests (POST, PUT, DELETE, PATCH).
    Skips CSRF validation for:
    - GET, OPTIONS, HEAD requests
    - Endpoints without authentication (/login, /register, /verify-email)
    """
    
    def __init__(self, app, csrf_protection):
        super().__init__(app)
        self.csrf = csrf_protection
        self.protected_methods = {"POST", "PUT", "DELETE", "PATCH"}
        
        # Endpoints без CSRF защиты (нет аутентификации)
        self.skip_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/verify-email",
            "/api/v1/auth/reset-password/request",
            "/api/v1/auth/reset-password/confirm",
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF для non-HTTP requests
        if request.scope["type"] != "http":
            return await call_next(request)
        
        # Skip CSRF для GET, OPTIONS, HEAD
        if request.method not in self.protected_methods:
            return await call_next(request)
        
        # Skip CSRF для определенных paths
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Skip если CSRF отключен
        if not settings.CSRF_ENABLED:
            logger.debug("CSRF protection disabled")
            return await call_next(request)
        
        # Извлечь Authorization header
        auth_header = request.headers.get("Authorization")
        
        # Если нет авторизации, пропускаем (пусть auth middleware обработает)
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)
        
        try:
            # Извлечь user_id из JWT
            token = auth_header.replace("Bearer ", "")
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                logger.warning("Invalid JWT payload: no sub claim")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "UNAUTHORIZED", "message": "Invalid token"}
                )
            
            # Проверить CSRF токен
            csrf_token = request.headers.get("X-CSRF-Token")
            
            if not csrf_token:
                logger.warning(
                    "CSRF token missing",
                    user_id=user_id,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "CSRF_TOKEN_MISSING",
                        "message": "CSRF token is required for this request"
                    }
                )
            
            # Валидация токена
            if not await self.csrf.validate_token(user_id, csrf_token):
                logger.warning(
                    "CSRF token invalid",
                    user_id=user_id,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "CSRF_TOKEN_INVALID",
                        "message": "Invalid CSRF token"
                    }
                )
            
            # CSRF валидация успешна
            logger.debug(
                "CSRF validation passed",
                user_id=user_id,
                path=request.url.path
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "CSRF validation error",
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "INTERNAL_ERROR", "message": "CSRF validation failed"}
            )
        
        return await call_next(request)
```

### 4.10 API Specification

#### Modified: POST /api/v1/auth/login

**Response 200:**
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "csrf_token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

#### Modified: POST /api/v1/auth/verify-email

**Response 200:**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "csrf_token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

#### Modified: POST /api/v1/auth/refresh

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "csrf_token": "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

#### Modified: POST /api/v1/auth/logout

**Request:**
```http
POST /api/v1/auth/logout HTTP/1.1
Authorization: Bearer <access_token>
X-CSRF-Token: <csrf_token>
```

**Response 200:**
```json
{
  "message": "Successfully logged out"
}
```

---

## 5. Sequence Diagrams

### 5.1 Login Flow с CSRF токеном

```mermaid
sequenceDiagram
    participant User as User
    participant Frontend as Frontend
    participant Auth as Auth Service
    participant Redis as Redis
    participant DB as PostgreSQL

    User->>Frontend: Enter credentials
    Frontend->>Auth: POST /api/v1/auth/login
    Auth->>DB: Validate credentials
    DB-->>Auth: User found
    Auth->>Auth: Generate access_token
    Auth->>Auth: Generate refresh_token
    Auth->>Redis: SETEX csrf:{user_id} 86400 {csrf_token}
    Redis-->>Auth: OK
    Auth-->>Frontend: 200 OK {access_token, refresh_token, csrf_token}
    Frontend->>Frontend: Store tokens in localStorage
    Frontend-->>User: Redirect to dashboard
```

### 5.2 Protected Request Flow

```mermaid
sequenceDiagram
    participant User as User
    participant Frontend as Frontend
    participant CSRF as CSRF Middleware
    participant Auth as Auth Service
    participant Redis as Redis

    User->>Frontend: Update profile
    Frontend->>Frontend: Get csrf_token from localStorage
    Frontend->>CSRF: POST /api/v1/users/me
    Note over Frontend,CSRF: Headers:<br/>Authorization: Bearer XXX<br/>X-CSRF-Token: YYY
    CSRF->>CSRF: Decode JWT, extract user_id
    CSRF->>Redis: GET csrf:{user_id}
    Redis-->>CSRF: {csrf_token}
    CSRF->>CSRF: Compare tokens (constant-time)
    Note over CSRF: ✅ Tokens match
    CSRF->>Auth: Forward request
    Auth-->>Frontend: 200 OK {updated profile}
    Frontend-->>User: Show success message
```

### 5.3 CSRF Attack Blocked

```mermaid
sequenceDiagram
    participant User as User
    participant Evil as Evil.com
    participant CSRF as CSRF Middleware
    participant Redis as Redis

    User->>User: Logged in to fishing.com
    User->>Evil: Opens evil.com
    Evil->>CSRF: POST fishing.com/api/v1/users/me
    Note over Evil,CSRF: Hidden form auto-submit<br/>Authorization: Bearer XXX (from browser)<br/>NO X-CSRF-Token header
    CSRF->>CSRF: Decode JWT, extract user_id
    CSRF->>CSRF: Check X-CSRF-Token header
    Note over CSRF: ❌ Header missing
    CSRF->>Redis: LOG warning (CSRF attempt)
    CSRF-->>Evil: 403 Forbidden {code: CSRF_TOKEN_MISSING}
    Evil-->>User: Attack blocked
```

### 5.4 Logout Flow с CSRF инвалидацией

```mermaid
sequenceDiagram
    participant User as User
    participant Frontend as Frontend
    participant Auth as Auth Service
    participant Redis as Redis

    User->>Frontend: Click "Logout"
    Frontend->>Auth: POST /api/v1/auth/logout
    Note over Frontend,Auth: Headers:<br/>Authorization: Bearer XXX<br/>X-CSRF-Token: YYY
    Auth->>Auth: Extract jti from token
    Auth->>Redis: SETEX blacklist:access:{jti} 1800 "1"
    Auth->>Redis: DEL csrf:{user_id}
    Redis-->>Auth: OK
    Auth-->>Frontend: 200 OK {message: "Logged out"}
    Frontend->>Frontend: Clear all tokens from localStorage
    Frontend-->>User: Redirect to login
```

---

## 6. Декомпозиция на задачи

### TASK-BCK-001: Создать модуль csrf_protection.py

**Направление:** Backend  
**Приоритет:** High  
**Оценка:** 2 часа  
**Зависимости:** Нет

**Описание:**
Создать класс CSRFProtection для генерации, валидации и инвалидации CSRF токенов.

**Критерии приемки:**
- [ ] Класс CSRFProtection создан
- [ ] Метод `generate_token(user_id)` генерирует 43-char токен
- [ ] Метод `validate_token(user_id, token)` проверяет токен
- [ ] Метод `invalidate_token(user_id)` удаляет токен
- [ ] Метод `refresh_token(user_id)` обновляет токен
- [ ] Токены хранятся в Redis с TTL
- [ ] Constant-time comparison для предотвращения timing attacks
- [ ] Обработка ошибок Redis connection
- [ ] Логирование всех операций

**Технические детали:**
- Файлы: `services/auth-service/app/core/csrf_protection.py`
- Redis key format: `csrf:{user_id}`
- TTL: 86400 секунд (24 часа)
- Token: `secrets.token_urlsafe(32)` = 43 chars

---

### TASK-BCK-002: Создать CSRF Middleware

**Направление:** Backend  
**Приоритет:** High  
**Оценка:** 3 часа  
**Зависимости:** TASK-BCK-001

**Описание:**
Создать middleware для проверки CSRF токенов на всех state-changing запросах.

**Критерии приемки:**
- [ ] Класс CSRFMiddleware создан
- [ ] Проверка только для POST/PUT/DELETE/PATCH
- [ ] Skip для GET/OPTIONS/HEAD
- [ ] Skip для /login, /register, /verify-email
- [ ] Извлечение user_id из JWT
- [ ] Проверка X-CSRF-Token header
- [ ] Response 403 если токен отсутствует (CSRF_TOKEN_MISSING)
- [ ] Response 403 если токен невалиден (CSRF_TOKEN_INVALID)
- [ ] Логирование CSRF попыток

**Технические детали:**
- Файлы: `services/auth-service/app/middleware/csrf.py`
- Интеграция с `decode_access_token()`
- Error codes: CSRF_TOKEN_MISSING, CSRF_TOKEN_INVALID

---

### TASK-BCK-003: Добавить CSRF токен в /login endpoint

**Направление:** Backend  
**Приоритет:** High  
**Оценка:** 1 час  
**Зависимости:** TASK-BCK-001

**Описание:**
Модифицировать /login endpoint для генерации и возврата CSRF токена.

**Критерии приемки:**
- [ ] /login генерирует CSRF токен
- [ ] CSRF токен сохраняется в Redis
- [ ] Response содержит csrf_token
- [ ] Схема LoginResponse обновлена
- [ ] Логирование генерации токена

**Технические детали:**
- Файлы: `services/auth-service/app/endpoints/auth.py`
- Файлы: `services/auth-service/app/schemas/auth.py`

---

### TASK-BCK-004: Добавить CSRF токен в /verify-email endpoint

**Направление:** Backend  
**Приоритет:** Medium  
**Оценка:** 0.5 часа  
**Зависимости:** TASK-BCK-001

**Описание:**
Модифицировать /verify-email endpoint для генерации CSRF токена.

**Критерии приемки:**
- [ ] /verify-email генерирует CSRF токен
- [ ] Response содержит csrf_token

**Технические детали:**
- Файлы: `services/auth-service/app/endpoints/auth.py`

---

### TASK-BCK-005: Добавить CSRF токен в /refresh endpoint

**Направление:** Backend  
**Приоритет:** High  
**Оценка:** 1 час  
**Зависимости:** TASK-BCK-001

**Описание:**
Модифицировать /refresh endpoint для генерации нового CSRF токена.

**Критерии приемки:**
- [ ] /refresh генерирует новый CSRF токен
- [ ] Старый CSRF токен инвалидирован
- [ ] Response содержит новый csrf_token

**Технические детали:**
- Файлы: `services/auth-service/app/endpoints/auth.py`

---

### TASK-BCK-006: Инвалидация CSRF токена при /logout

**Направление:** Backend  
**Приоритет:** High  
**Оценка:** 0.5 часа  
**Зависимости:** TASK-BCK-001

**Описание:**
Добавить инвалидацию CSRF токена при logout.

**Критерии приемки:**
- [ ] /logout удаляет CSRF токен из Redis
- [ ] Логирование инвалидации

**Технические детали:**
- Файлы: `services/auth-service/app/endpoints/auth.py`

---

### TASK-BCK-007: Инвалидация CSRF токена при смене пароля

**Направление:** Backend  
**Приоритет:** High  
**Оценка:** 0.5 часа  
**Зависимости:** TASK-BCK-001

**Описание:**
Инвалидировать CSRF токен при смене пароля.

**Критерии приемки:**
- [ ] /reset-password/confirm удаляет CSRF токен
- [ ] Пользователь должен заново логиниться

**Технические детали:**
- Файлы: `services/auth-service/app/endpoints/auth.py`

---

### TASK-BCK-008: Зарегистрировать CSRF Middleware в main.py

**Направление:** Backend  
**Приоритет:** High  
**Оценка:** 0.5 часа  
**Зависимости:** TASK-BCK-002

**Описание:**
Добавить CSRF middleware в приложение.

**Критерии приемки:**
- [ ] CSRF middleware зарегистрирован
- [ ] Порядок middleware правильный (после CORS, перед logging)
- [ ] Инициализация csrf_protection в lifespan

**Технические детали:**
- Файлы: `services/auth-service/app/main.py`

---

### TASK-BCK-009: Добавить конфигурацию CSRF в config.py

**Направление:** Backend  
**Приоритет:** Medium  
**Оценка:** 0.5 часа  
**Зависимости:** Нет

**Описание:**
Добавить настройки CSRF в конфигурацию.

**Критерии приемки:**
- [ ] Переменная CSRF_TOKEN_TTL добавлена (default: 86400)
- [ ] Переменная CSRF_ENABLED добавлена (default: true)
- [ ] .env.example обновлен

**Технические детали:**
- Файлы: `services/auth-service/app/core/config.py`
- Файлы: `.env.example`

---

### TASK-FRT-001: Обновить API client для CSRF токена

**Направление:** Frontend  
**Приоритет:** High  
**Оценка:** 1 час  
**Зависимости:** TASK-BCK-003

**Описание:**
Добавить автоматическое добавление X-CSRF-Token header в API client.

**Критерии приемки:**
- [ ] getAuthHeaders() извлекает csrf_token из localStorage
- [ ] X-CSRF-Token header добавляется ко всем запросам
- [ ] Обработка отсутствия csrf_token

**Технические детали:**
- Файлы: `frontend/lib/api/client.ts`

---

### TASK-FRT-002: Обновить auth store для хранения CSRF токена

**Направление:** Frontend  
**Приоритет:** High  
**Оценка:** 1 час  
**Зависимости:** TASK-BCK-003

**Описание:**
Добавить хранение CSRF токена в auth store.

**Критерии приемки:**
- [ ] Поле csrfToken добавлено в state
- [ ] Login сохраняет csrf_token в localStorage
- [ ] Logout очищает csrf_token
- [ ] Refresh обновляет csrf_token

**Технические детали:**
- Файлы: `frontend/stores/authStore.ts` (или аналогичный файл)

---

### TASK-FRT-003: Обработка 403 CSRF ошибок на frontend

**Направление:** Frontend  
**Приоритет:** Medium  
**Оценка:** 1 час  
**Зависимости:** TASK-FRT-001

**Описание:**
Добавить обработку CSRF ошибок на frontend.

**Критерии приемки:**
- [ ] Перехват 403 с кодом CSRF_TOKEN_MISSING
- [ ] Перехват 403 с кодом CSRF_TOKEN_INVALID
- [ ] Автоматический logout при CSRF ошибке
- [ ] Показ toast/notification с сообщением

**Технические детали:**
- Файлы: `frontend/lib/api/client.ts`

---

### TASK-TST-001: Unit тесты для csrf_protection.py

**Направление:** Testing  
**Приоритет:** High  
**Оценка:** 2 часа  
**Зависимости:** TASK-BCK-001

**Описание:**
Unit тесты для CSRFProtection класса.

**Критерии приемки:**
- [ ] Тест: generate_token создает токен и сохраняет в Redis
- [ ] Тест: validate_token возвращает True для валидного токена
- [ ] Тест: validate_token возвращает False для невалидного токена
- [ ] Тест: validate_token возвращает False для отсутствующего токена
- [ ] Тест: invalidate_token удаляет токен
- [ ] Тест: refresh_token генерирует новый токен
- [ ] Тест: TTL корректно устанавливается
- [ ] Тест: обработка Redis connection error
- [ ] Покрытие кода ≥80%

**Технические детали:**
- Файлы: `services/auth-service/tests/test_csrf_protection.py`

---

### TASK-TST-002: Integration тесты для CSRF middleware

**Направление:** Testing  
**Приоритет:** High  
**Оценка:** 3 часа  
**Зависимости:** TASK-BCK-002

**Описание:**
Integration тесты для CSRF middleware.

**Критерии приемки:**
- [ ] Тест: POST с валидным CSRF токеном проходит
- [ ] Тест: POST без CSRF токена возвращает 403
- [ ] Тест: POST с невалидным CSRF токеном возвращает 403
- [ ] Тест: GET запросы не требуют CSRF
- [ ] Тест: /login не требует CSRF
- [ ] Тест: /register не требует CSRF
- [ ] Тест: истекший CSRF токен возвращает 403
- [ ] Тест: CSRF токен инвалидирован после logout

**Технические детали:**
- Файлы: `services/auth-service/tests/test_csrf_middleware.py`

---

### TASK-TST-003: Integration тесты для login/refresh endpoints

**Направление:** Testing  
**Приоритет:** High  
**Оценка:** 2 часа  
**Зависимости:** TASK-BCK-003, TASK-BCK-005

**Описание:**
Integration тесты для проверки возврата CSRF токена.

**Критерии приемки:**
- [ ] Тест: /login возвращает csrf_token
- [ ] Тест: /verify-email возвращает csrf_token
- [ ] Тест: /refresh возвращает новый csrf_token
- [ ] Тест: csrf_token сохраняется в Redis
- [ ] Тест: csrf_token имеет правильный TTL

**Технические детали:**
- Файлы: `services/auth-service/tests/test_auth_csrf.py`

---

### TASK-TST-004: E2E тест CSRF атаки

**Направление:** Testing  
**Приоритет:** Medium  
**Оценка:** 2 часа  
**Зависимости:** Все backend задачи

**Описание:**
E2E тест для симуляции CSRF атаки.

**Критерии приемки:**
- [ ] Тест: cross-site request без CSRF токена заблокирован
- [ ] Тест: логирование CSRF попытки
- [ ] Тест: error response корректный

**Технические детали:**
- Файлы: `services/auth-service/tests/test_csrf_attack.py`

---

### TASK-DOC-001: Обновить SECURITY_AUDIT.md

**Направление:** Documentation  
**Приоритет:** Medium  
**Оценка:** 0.5 часа  
**Зависимости:** Все backend задачи

**Описание:**
Обновить статус уязвимости #9 в SECURITY_AUDIT.md.

**Критерии приемки:**
- [ ] Статус изменен на "ИСПРАВЛЕНО"
- [ ] Добавлена дата исправления
- [ ] Добавлена ссылка на SEC-009

**Технические детали:**
- Файлы: `SECURITY_AUDIT.md`

---

### TASK-DOC-002: Обновить ARCHITECTURE.md

**Направление:** Documentation  
**Приоритет:** Low  
**Оценка:** 1 час  
**Зависимости:** Все backend задачи

**Описание:**
Обновить документацию архитектуры с информацией о CSRF защите.

**Критерии приемки:**
- [ ] Добавлена секция о CSRF Protection
- [ ] Документирован CSRF middleware
- [ ] Добавлена информация о Redis ключах
- [ ] Обновлена схема Authentication Flow

**Технические детали:**
- Файлы: `ARCHITECTURE.md`

---

## 7. Итоговая таблица задач

| ID | Название | Направление | Приоритет | Оценка | Зависимости |
|----|----------|-------------|-----------|--------|-------------|
| TASK-BCK-001 | Модуль csrf_protection.py | Backend | High | 2h | - |
| TASK-BCK-002 | CSRF Middleware | Backend | High | 3h | BCK-001 |
| TASK-BCK-003 | CSRF токен в /login | Backend | High | 1h | BCK-001 |
| TASK-BCK-004 | CSRF токен в /verify-email | Backend | Medium | 0.5h | BCK-001 |
| TASK-BCK-005 | CSRF токен в /refresh | Backend | High | 1h | BCK-001 |
| TASK-BCK-006 | Инвалидация при /logout | Backend | High | 0.5h | BCK-001 |
| TASK-BCK-007 | Инвалидация при смене пароля | Backend | High | 0.5h | BCK-001 |
| TASK-BCK-008 | Регистрация middleware | Backend | High | 0.5h | BCK-002 |
| TASK-BCK-009 | Конфигурация CSRF | Backend | Medium | 0.5h | - |
| TASK-FRT-001 | API client для CSRF | Frontend | High | 1h | BCK-003 |
| TASK-FRT-002 | Auth store для CSRF | Frontend | High | 1h | BCK-003 |
| TASK-FRT-003 | Обработка 403 CSRF ошибок | Frontend | Medium | 1h | FRT-001 |
| TASK-TST-001 | Unit тесты csrf_protection | Testing | High | 2h | BCK-001 |
| TASK-TST-002 | Integration тесты middleware | Testing | High | 3h | BCK-002 |
| TASK-TST-003 | Integration тесты endpoints | Testing | High | 2h | BCK-003, BCK-005 |
| TASK-TST-004 | E2E тест CSRF атаки | Testing | Medium | 2h | All backend |
| TASK-DOC-001 | SECURITY_AUDIT.md | Documentation | Medium | 0.5h | All backend |
| TASK-DOC-002 | ARCHITECTURE.md | Documentation | Low | 1h | All backend |

**Общая оценка:** 23 часа

**Критический путь (Backend):**
```
BCK-001 (2h) → BCK-002 (3h) → BCK-003 (1h) → TST-003 (2h)
```
**Длительность критического пути:** 8 часов

---

## 8. Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Redis недоступен | Medium | High | Graceful degradation: skip CSRF check + log warning |
| CSRF token泄露 | Low | Medium | TTL auto-expiry (24h), инвалидация при logout |
| Performance overhead | Low | Low | Redis in-memory, <3ms overhead |
| Frontend не отправляет CSRF | Low | Medium | Автоматическое добавление в API client |
| Timing attack | Very Low | Medium | Constant-time comparison (secrets.compare_digest) |

### Graceful Degradation при Redis недоступности

```python
async def validate_token(self, user_id: str, token: str) -> bool:
    try:
        key = f"{self.prefix}:{user_id}"
        stored = await self.redis.get(key)
        # ... validation logic
    except redis.RedisError as e:
        logger.warning(
            "Redis unavailable, skipping CSRF validation",
            user_id=user_id,
            error=str(e)
        )
        # Skip CSRF check if Redis is down
        return True
```

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Метрика | Требование |
|---------|------------|
| Overhead на request (CSRF check) | < 3ms |
| Redis latency | < 2ms |
| Token generation | < 1ms |

### 9.2 Security

| Требование | Значение |
|------------|----------|
| Token format | secrets.token_urlsafe(32) = 43 chars |
| Token entropy | 256 bits |
| Storage | Redis (in-memory) |
| TTL | 24 часа (86400 сек) |
| Comparison | Constant-time (secrets.compare_digest) |

### 9.3 Availability

| Требование | Значение |
|------------|----------|
| Degradation при Redis down | Skip CSRF check + warning log |
| Logging | Warning при CSRF attempt |

### 9.4 Compatibility

| Требование | Значение |
|------------|----------|
| Browsers | Все современные браузеры |
| API clients | Поддержка custom headers |

---

## 10. Definition of Done

### DoD Backend

- [ ] Модуль csrf_protection.py реализован
- [ ] CSRF Middleware реализован
- [ ] /login возвращает csrf_token
- [ ] /verify-email возвращает csrf_token
- [ ] /refresh возвращает csrf_token
- [ ] /logout инвалидирует csrf_token
- [ ] Password reset инвалидирует csrf_token
- [ ] Middleware зарегистрирован
- [ ] Конфигурация добавлена
- [ ] Unit тесты ≥80% покрытие
- [ ] Integration тесты пройдены
- [ ] Performance overhead < 3ms

### DoD Frontend

- [ ] API client добавляет X-CSRF-Token header
- [ ] Auth store хранит csrf_token
- [ ] Обработка 403 CSRF ошибок
- [ ] Тесты написаны

### DoD Documentation

- [ ] SECURITY_AUDIT.md обновлен
- [ ] ARCHITECTURE.md обновлен

---

## 11. Зависимости

### Зависит от

- Redis (уже развернут в docker-compose.yml)
- Auth Service (port 8001)
- JWT authentication (уже реализовано)
- Token blacklist (SEC-006)

### Блокирует

- Полное устранение уязвимости #9 из SECURITY_AUDIT.md
- Защита от CSRF атак на state-changing endpoints

---

## 12. Deployment Notes

### Production Deployment

1. Убедиться что Redis доступен
2. Установить `CSRF_ENABLED=true` в .env
3. Установить `CSRF_TOKEN_TTL=86400` в .env
4. Деплой backend изменений
5. Деплой frontend изменений
6. Тестирование login → protected request flow

### Rollback Plan

При критических проблемах:
1. Установить `CSRF_ENABLED=false` в .env
2. Перезапустить auth-service
3. CSRF защита отключена, но функциональность сохранена

---

## 13. История изменений

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| 1.0 | 2026-03-03 | System Analyst | Initial version |

---

**Статус:** ✅ Approved  
**Дата согласования:** 2026-03-03  
**Согласовано с:** Заказчик

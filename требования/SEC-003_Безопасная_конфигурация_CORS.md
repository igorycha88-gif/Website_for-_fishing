# SEC-003: Безопасная конфигурация CORS

**ID:** SEC-003  
**Version:** 1.0  
**Status:** Approved  
**Author:** System Analyst  
**Date:** 2026-02-21  
**Priority:** Critical

---

## 1. Executive Summary

### 1.1 Проблема

CORS настроен с `allow_origins=["*"]` и `allow_credentials=True`, что создает критические риски безопасности:

| Файл | Проблема | Риск |
|------|----------|------|
| `services/auth-service/app/main.py:19` | `allow_origins=["*"]` | CSRF атаки |
| `services/places-service/app/main.py:31` | `allow_origins=["*"]` | Кража данных |

**Комбинация** `allow_origins=["*"]` + `allow_credentials=True` запрещена спецификацией CORS и открывает возможность:
- CSRF атак через malicious websites
- Кражу данных авторизованных пользователей
- Нарушение Same-Origin Policy

### 1.2 Решение

Whitelist origins через переменную окружения + автоматический fallback для development:

| Environment | Origins |
|-------------|---------|
| Development | `localhost:3000`, `127.0.0.1:3000`, `localhost:3001` + env |
| Production | Только `CORS_ORIGINS` из `.env` |

---

## 2. Scope

### 2.1 In Scope

- Добавление переменной `CORS_ORIGINS` в конфигурацию
- Обновление `auth-service` и `places-service`
- Валидация origins при старте приложения
- Обновление проектной документации

### 2.2 Out of Scope

- Динамическое управление origins через БД
- Отдельный сервис для CORS конфигурации
- Preflight caching optimization

---

## 3. User Stories

### US1: Конфигурация CORS через переменные окружения

**As a** DevOps Engineer  
**I want to** настраивать разрешенные origins через `.env`  
**So that** могу безопасно управлять CORS без изменения кода

**Priority:** High  
**Actors:** DevOps Engineer, Admin

**Acceptance Criteria:**

**AC1.1: Переменная CORS_ORIGINS**
- Given файл `.env` существует
- When добавлена переменная `CORS_ORIGINS=https://app.example.com,https://api.example.com`
- Then сервис парсит список origins

**AC1.2: Development fallback**
- Given `ENVIRONMENT=development`
- When сервис стартует
- Then автоматически добавляются `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`

**AC1.3: Production strict mode**
- Given `ENVIRONMENT=production`
- When `CORS_ORIGINS` пуст
- Then логируется warning
- And сервис продолжает работу с пустым списком origins

---

### US2: Валидация origins при старте

**As a** Developer  
**I want to** видеть ошибки в конфигурации CORS при старте  
**So that** могу исправить опечатки до деплоя

**Priority:** Medium  
**Actors:** Developer, DevOps Engineer

**Acceptance Criteria:**

**AC2.1: Проверка формата URL**
- Given сервис стартует
- When `CORS_ORIGINS` содержит `invalid-url`
- Then логируется warning "Invalid CORS origin: invalid-url"
- And невалидный origin исключается из списка

**AC2.2: Проверка wildcard с credentials**
- Given сервис стартует
- When `CORS_ORIGINS` содержит `*` и `allow_credentials=True`
- Then логируется error "Wildcard origin with credentials is not allowed"
- And wildcard исключается из списка

---

### US3: Обновление микросервисов

**As a** Backend Developer  
**I want to** чтобы все сервисы использовали единую CORS конфигурацию  
**So that** поведение согласовано между сервисами

**Priority:** High  
**Actors:** Backend Developer

**Acceptance Criteria:**

**AC3.1: Auth Service обновлен**
- Given `auth-service/app/main.py`
- When применяется новая конфигурация
- Then `allow_origins=settings.cors_origins_list`

**AC3.2: Places Service обновлен**
- Given `places-service/app/main.py`
- When применяется новая конфигурация
- Then `allow_origins=settings.cors_origins_list`

---

## 4. Технические требования

### 4.1 Переменные окружения

```bash
# .env
ENVIRONMENT=development
CORS_ORIGINS=https://fishmap.ru,https://api.fishmap.ru

# .env.example
ENVIRONMENT=development
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

### 4.2 Конфигурация Settings

```python
# services/auth-service/app/core/config.py
# services/places-service/app/core/config.py

from pydantic_settings import BaseSettings
from typing import List
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = ""
    
    @property
    def cors_origins_list(self) -> List[str]:
        origins = []
        
        if self.ENVIRONMENT == "development":
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
            ])
        
        if self.CORS_ORIGINS:
            for origin in self.CORS_ORIGINS.split(","):
                origin = origin.strip()
                if not origin:
                    continue
                if origin == "*":
                    logger.warning("Wildcard CORS origin detected, this is not recommended")
                if not self._validate_origin(origin):
                    logger.warning(f"Invalid CORS origin format: {origin}")
                    continue
                origins.append(origin)
        
        if not origins and self.ENVIRONMENT == "production":
            logger.warning("CORS_ORIGINS is empty in production mode")
        
        return origins
    
    def _validate_origin(self, origin: str) -> bool:
        if origin == "*":
            return True
        try:
            result = urlparse(origin)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


settings = Settings()
```

### 4.3 Обновление main.py

```python
# services/auth-service/app/main.py
# services/places-service/app/main.py

from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
```

### 4.4 Разрешенные HTTP методы

| Метод | Разрешен | Обоснование |
|-------|----------|-------------|
| GET | Да | Чтение данных |
| POST | Да | Создание данных |
| PUT | Да | Обновление данных |
| DELETE | Да | Удаление данных |
| OPTIONS | Да | Preflight запросы |
| PATCH | Нет | Не используется в проекте |

### 4.5 Разрешенные заголовки

| Заголовок | Разрешен | Обоснование |
|-----------|----------|-------------|
| Content-Type | Да | Content negotiation |
| Authorization | Да | JWT токены |
| X-Requested-With | Да | AJAX requests |

---

## 5. План реализации

### Фаза 1: Обновление конфигурации (2 часа)

| # | Задача | Файл | Оценка |
|---|--------|------|--------|
| 1.1 | Добавить CORS_ORIGINS в .env | `.env` | 5m |
| 1.2 | Добавить CORS_ORIGINS в .env.example | `.env.example` | 5m |
| 1.3 | Добавить свойство cors_origins_list | `auth-service/app/core/config.py` | 30m |
| 1.4 | Добавить свойство cors_origins_list | `places-service/app/core/config.py` | 30m |

### Фаза 2: Обновление сервисов (1 час)

| # | Задача | Файл | Оценка |
|---|--------|------|--------|
| 2.1 | Обновить CORSMiddleware | `auth-service/app/main.py` | 15m |
| 2.2 | Обновить CORSMiddleware | `places-service/app/main.py` | 15m |
| 2.3 | Unit тесты для config | `tests/test_config.py` | 30m |

### Фаза 3: Обновление документации (1 час)

| # | Задача | Файл | Оценка |
|---|--------|------|--------|
| 3.1 | Добавить CORS_ORIGINS в таблицу переменных | `DEPLOYMENT.md` | 15m |
| 3.2 | Добавить секцию CORS в Security | `ARCHITECTURE.md` | 15m |
| 3.3 | Добавить CORS в переменные окружения | `SYSTEM_PROMPT.md` | 15m |
| 3.4 | Обновить статус уязвимости | `SECURITY_AUDIT.md` | 15m |

---

## 6. Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| CORS_ORIGINS не указан в production | Medium | High | Warning при старте, документация |
| Опечатка в URL | Medium | Medium | Валидация при старте |
| Забыт localhost при деплое | Low | Medium | Разделение dev/prod конфигураций |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Метрика | Требование |
|---------|------------|
| Overhead на request | < 1ms |

### 7.2 Security

| Требование | Значение |
|------------|----------|
| Wildcard origin | Не разрешен с credentials |
| Validation | При старте приложения |
| Logging | Warnings для невалидных origins |

---

## 8. Тестирование

### 8.1 Unit Tests

- [ ] `Settings.cors_origins_list` - парсинг comma-separated строки
- [ ] `Settings.cors_origins_list` - development fallback
- [ ] `Settings.cors_origins_list` - production strict mode
- [ ] `Settings._validate_origin` - валидный URL
- [ ] `Settings._validate_origin` - невалидный URL
- [ ] `Settings._validate_origin` - wildcard

### 8.2 Integration Tests

- [ ] Preflight request возвращает разрешенные origins
- [ ] Request с неразрешенного origin отклоняется
- [ ] Request с разрешенного origin проходит
- [ ] Credentials передаются только с разрешенных origins

### 8.3 Manual Testing

```bash
# Test preflight
curl -X OPTIONS http://localhost:8001/api/v1/auth/login \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Test blocked origin
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Origin: https://malicious-site.com" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test"}' \
  -v
```

---

## 9. Definition of Done

### DoD для реализации

- [ ] `CORS_ORIGINS` добавлен в `.env` и `.env.example`
- [ ] `auth-service` обновлен
- [ ] `places-service` обновлен
- [ ] Unit тесты написаны
- [ ] Integration тесты пройдены
- [ ] Manual тестирование выполнено

### DoD для документации

- [ ] `DEPLOYMENT.md` обновлен (таблица переменных)
- [ ] `ARCHITECTURE.md` обновлен (секция CORS)
- [ ] `SYSTEM_PROMPT.md` обновлен (переменные окружения)
- [ ] `SECURITY_AUDIT.md` обновлен (статус исправления)

---

## 10. Зависимости

### Зависит от

- Нет зависимостей

### Блокирует

- Полное устранение уязвимости #3 из SECURITY_AUDIT.md

---

## 11. Обновление документации

### 11.1 DEPLOYMENT.md

Добавить в раздел "Environment Variables":

```markdown
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins (e.g., https://fishmap.ru,https://api.fishmap.ru)
```

### 11.2 ARCHITECTURE.md

Добавить секцию после "Security":

```markdown
## CORS Configuration

All backend services use a unified CORS configuration:

- **Development**: Automatically allows localhost:3000, 127.0.0.1:3000, localhost:3001
- **Production**: Only origins specified in `CORS_ORIGINS` environment variable

Allowed methods: GET, POST, PUT, DELETE, OPTIONS
Allowed headers: Content-Type, Authorization, X-Requested-With
Credentials: Enabled
```

### 11.3 SYSTEM_PROMPT.md

Добавить в раздел "Переменные окружения (.env)":

```markdown
# CORS
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

---

## 12. История изменений

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| 1.0 | 2026-02-21 | System Analyst | Initial version |

---

**Статус:** Approved  
**Дата согласования:** 2026-02-21  
**Согласовано с:** Заказчик

# Developer Prompt - Платформа для рыбалки (FishMap)

## Обзор проекта

Платформа для рыбалки - это микросервисное веб-приложение для рыболовов. Текущий статус: ранняя разработка.

### Реализованные сервисы ✅
- **Auth Service** (порт 8001 хост, 8000 контейнер) - полностью реализован
- **Email Service** (порт 8006 хост, 8005 контейнер) - полностью реализован
- **Frontend** (порт 3000) - основные страницы реализованы
- **Forecast Service** (порт 8007 хост, 8000 контейнер) - Этап 1 реализован

### Сервисы-заглушки 🚧
- **Places Service** (порт 8002 хост, 8001 контейнер) - заглушка
- **Reports Service** (порт 8003 хост, 8002 контейнер) - заглушка
- **Booking Service** (порт 8004 хост, 8003 контейнер) - заглушка
- **Shop Service** (порт 8005 хост, 8004 контейнер) - заглушка

## Технологический стек

### Frontend
- **Framework**: Next.js 15 (TypeScript) с App Router
- **Styling**: Tailwind CSS
- **State Management**: Zustand (useAuthStore для аутентификации)
- **Animations**: Framer Motion
- **API Proxy**: Next.js rewrites для проксирования к микросервисам

### Backend (FastAPI / Python)
- FastAPI async microservices
- PostgreSQL 16 (общая база для всех сервисов)
- SQLAlchemy (async ORM)
- Migrations через schema.sql (raw SQL)
- Redis (запланирован для сессий и кэширования)

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (development), Docker Swarm (production - запланирован)
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) для централизованного логирования

## Ключевые документы проекта

**ОБЯЗАТЕЛЬНО изучить перед разработкой:**

| Документ | Назначение |
|----------|------------|
| `SYSTEM_PROMPT.md` | Текущая архитектура, статусы сервисов, порты |
| `ARCHITECTURE.md` | Детали микросервисов, реализованные API |
| `database/schema.md` | Структура БД, реализованные/запланированные таблицы |
| `ANALYST_PROMPT.md` | Процесс анализа требований, шаблоны документов |
| `README.md` | Обзор проекта, запуск |
| `DEPLOYMENT.md` | Инструкции по деплою |
| `DOCKER.md` | Docker инструкции |

**Папка требований `требования/`:**

| Документ | Описание |
|----------|----------|
| `Требования_Мои_Места.md` | Требования функции "Мои места" |
| `требования_яндекс_карты.md` | Требования интеграции Яндекс Карт |
| `UC-REG-001_Регистрация_пользователя.md` | Use Case регистрации |

## Стандарты разработки

### 0. Получение требований от аналитика

**Процесс получения требований:**

1. **Изучить документ требований** в папке `требования/`
2. **Проверить статус документа**: должен быть "Approved" или "Согласовано"
3. **Понять Acceptance Criteria**: Given/When/Then формат
4. **Оценить архитектурные решения**: новый сервис или расширение существующего
5. **Задать уточняющие вопросы** перед началом разработки

**Чек-лист готовности требований к разработке:**
- [ ] Документ в папке `требования/`
- [ ] Статус: Approved
- [ ] Acceptance Criteria определены
- [ ] API Specification готова (если требуется)
- [ ] DB Schema Change документирован (если требуется)

**Формат запроса от аналитика:**
```markdown
**Документ требований**: `требования/Название_файла.md`
**Приоритет**: High/Medium/Low
**Сервис**: auth-service / places-service / frontend / ...
**Ключевые задачи**:
- [ ] Задача 1
- [ ] Задача 2
```

### 0.1 КРИТИЧЕСКИ ВАЖНО - Перед началом разработки

**ВСЕГДА перед началом разработки нового функционала:**

1. **Согласование с пользователем** - НЕ начинайте разработку до получения подтверждения от пользователя
   - Создайте чек-лист задач для реализации (todo list)
   - Обсудите архитектурные решения
   - **Обязательно согласуйте todo list с пользователем перед реализацией**
   - Получите подтверждение на начало работы

 2. **Перезапуск Docker и всех сервисов** - ВСЕГДА перезапускайте перед разработкой
    ```bash
    # Используйте Makefile команды
    make dev-down
    make dev-build
    make dev-up
    
    # Или для конкретных сервисов
    make build-auth
    make dev-up
    ```

 3. **Проверка health checks** - Убедитесь что все сервисы здоровы
    ```bash
    make health
    ```

**Если пользователь не подтвердил разработку - ЖДИТЕ ПОДТВЕРЖДЕНИЯ!**

### 0.2 КРИТИЧЕСКИ ВАЖНО - Окончание разработки

**ВСЕГДА в окончании разработки:**

1. **Все тесты должны проходить успешно**
   ```bash
   # Backend
   make pytest
   # или
   pytest services/{service-name}/tests/ -v
   
   # Frontend
   cd frontend && npm test
   ```
   - Если есть падающие тесты - разработка НЕ завершена
   - Исправьте тесты или код перед завершением

2. **Перезапуск Docker и всех сервисов**
   ```bash
   make dev-down
   make dev-build
   make dev-up
   ```
   - Это гарантирует, что изменения корректно работают в контейнерах
   - Проверяется сборка Docker образов

3. **Проверка health checks всех сервисов**
   ```bash
   make health
   # или вручную
   curl http://localhost:8001/health  # Auth
   curl http://localhost:8002/health  # Places
   curl http://localhost:3000         # Frontend
   ```
   - Все сервисы должны отвечать "healthy"
   - Нет ошибок в логах

4. **Финальная проверка**
   - Функционал работает в браузере (если применимо)
   - Нет console.error в браузере
   - Нет ошибок в логах Docker

**РАЗРАБОТКА НЕ ЗАВЕРШЕНА, ПОКА:**
- ❌ Есть падающие тесты
- ❌ Docker не собирается
- ❌ Health checks не проходят
- ❌ Есть ошибки в логах

### 1. Обязательный процесс разработки

```
[ ] 0. Согласование с пользователем (КРИТИЧЕСКИ ВАЖНО!)
[ ] 0.1 **TODO list согласован с пользователем перед реализацией** (КРИТИЧЕСКИ ВАЖНО!)
[ ] 0.2 Перезапуск Docker и всех сервисов ПЕРЕД разработкой
[ ] 0.3 Проверка health checks
[ ] 1. Бэкенд: модели/схемы
[ ] 2. Бэкенд: эндпоинты
[ ] 3. Бэкенд: **Unit тесты** (pytest)
[ ] 4. Фронтенд: UI компоненты
[ ] 5. Фронтенд: **Unit тесты** (jest)
[ ] 6. **ВСЕ тесты проходят успешно** (КРИТИЧЕСКИ ВАЖНО!)
[ ] 7. Логирование (ELK)
[ ] 8. Интеграционное тестирование
[ ] 9. Документация
[ ] 10. **🔄 Перезапуск Docker и всех сервисов** (КРИТИЧЕСКИ ВАЖНО!)
[ ] 11. **🔄 Проверка health checks** (КРИТИЧЕСКИ ВАЖНО!)
```

### 2. Обязательные требования перед тестированием

**ПЕРЕД ЛЮБЫМ ТЕСТИРОВАНИЕМ:**

```bash
# 1-2. Пересобираем и перезапускаем (Makefile)
make dev

# 3. Ждем запуска сервисов (5-10 секунд)
sleep 5

# 4. Проверяем health checks всех сервисов
make health

# Или вручную
curl http://localhost:8001/health  # Auth
curl http://localhost:8006/health  # Email
```

### 3. ⚠️ КРИТИЧЕСКИ ВАЖНО - Обязательные Unit тесты

**ВСЕГДА пишем юнит тесты для новой функциональности:**

#### Общие требования:
- **Покрытие новой логики ≥ 80%**
- **ВСЕ тесты должны проходить успешно** - разработка не завершена, пока есть падающие тесты
- Тесты пишутся ДО завершения разработки функционала
- Запуск тестов обязательный этап перед завершением работы

#### Backend (Python):
- Использование **pytest** для Python
- Фикстуры в `tests/conftest.py`
- Тестовые переменные окружения в `.env.test`

**Структура тестов:**
```
services/{service-name}/tests/
 ├── __init__.py
 ├── conftest.py           # Shared fixtures
 ├── test_api.py           # API endpoints
 ├── test_services.py      # Business logic
 └── test_models.py        # Models/CRUD
```

#### Frontend (TypeScript/React):
- Использование **Jest** + **React Testing Library**
- Тесты в папке `__tests__/` или рядом с компонентами
- Тестирование: hooks, components, stores

**Структура тестов:**
```
frontend/__tests__/
 ├── components/           # Component tests
 │   ├── ComponentName.test.tsx
 │   └── ...
 ├── hooks/               # Hook tests
 │   └── useHookName.test.ts
 ├── stores/              # Zustand store tests
 │   └── useStoreName.test.ts
 └── utils/               # Utility tests
```

**Обязательные тесты для компонентов:**
- Рендеринг компонента
- Взаимодействие пользователя (клики, ввод)
- Состояния (loading, error, success)
- Валидация форм

#### Запуск тестов:
```bash
# Backend - Python
make pytest                    # auth-service
make pytest S=email-service    # конкретный сервис
pytest services/{service-name}/tests/ -v --cov=app

# Frontend - TypeScript
cd frontend && npm test        # все тесты
cd frontend && npm test -- --testPathPattern="ComponentName"  # конкретный тест
cd frontend && npm test -- --coverage  # с coverage report
```

#### Чек-лист тестирования:
- [ ] Написаны unit тесты для новой функциональности
- [ ] Покрытие ≥ 80% для нового кода
- [ ] **ВСЕ тесты проходят успешно** (нет падающих тестов)
- [ ] Прогнаны все тесты проекта (регрессия)

**Пример теста для сервиса с Redis и внешним API:**
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_redis():
    return AsyncMock()

@pytest.mark.asyncio
async def test_geocode_city_from_api(geocode_service, mock_redis):
    city = "Москва"
    mock_redis.get.return_value = None
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "response": {
            "GeoObjectCollection": {
                "featureMember": [
                    {"GeoObject": {"Point": {"pos": "37.6173 55.7558"}}}
                ]
            }
        }
    })
    
    with patch("httpx.AsyncClient") as mock_httpx:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client
        
        result = await geocode_service.get_city_coordinates(city)
        
        assert result == {"lat": 55.7558, "lon": 37.6173}
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()
```

### 4. Обязательное логирование (ELK Stack)

**ВСЕГДА пишем логи и добавляем их для отображения в Kibana:**

#### Требования к логированию:
1. **Библиотека**: `structlog>=24.1.0` в `requirements.txt`
2. **Конфигурация**: `app/core/logging_config.py`
3. **Middleware**: `app/middleware/logging.py`
4. **Отправка логов**: на `http://logstash:5000`
5. **Kibana**: доступ по http://localhost:5601

#### Структура лога (обязательные поля):
```python
logger.info(
    "Action description",
    service="service-name",
    level="info",
    timestamp=datetime.utcnow().isoformat(),
    action="action_name",
    additional_field=value
)

logger.error(
    "Error description",
    service="service-name",
    level="error",
    timestamp=datetime.utcnow().isoformat(),
    action="action_name",
    error=str(e),
    exc_info=True
)
```

#### Обязательные поля лога:
- `service`: имя сервиса
- `level`: info|error|warning
- `timestamp`: ISO формат
- `message`: описание события
- Контекстные поля: `user_id`, `action`, `error` и т.д.

#### Пример логирования для сервиса с внешним API и кэшем:
```python
import logging

logger = logging.getLogger(__name__)

class GeocodeService:
    async def get_city_coordinates(self, city: str) -> Optional[dict]:
        logger.info(f"Geocode request for city: {city}")
        
        try:
            logger.debug(f"Checking cache for key: map:coordinates:{city.lower()}")
            cached_data = await self._get_from_cache(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for city: {city}, coordinates: {cached_data}")
                return cached_data
            
            logger.info(f"Cache miss for city: {city}, fetching from API")
            coordinates = await self._fetch_from_yandex(city)
            
            if coordinates:
                logger.info(f"Successfully geocoded city {city}: {coordinates}")
                await self._save_to_cache(cache_key, coordinates)
                return coordinates
            
            logger.warning(f"Failed to geocode city: {city}")
            return None
            
        except Exception as e:
            logger.error(f"Error geocoding city {city}: {e}", exc_info=True)
            return None
```

#### Запуск ELK Stack:
```bash
# Запуск ELK для разработки
docker-compose -f docker-compose.elk.yml up -d

# Доступ к Kibana
http://localhost:5601

# Создание индексного паттерна: fishmap-logs-*
# Поле времени: @timestamp
```

## Структура проекта

```
.
├── services/
│   ├── auth-service/          # Auth service (port 8001)
│   ├── places-service/        # Places service (port 8002)
│   ├── reports-service/       # Reports service (port 8003)
│   ├── booking-service/       # Booking service (port 8004)
│   ├── shop-service/          # Shop service (port 8005)
│   ├── email-service/         # Email service (port 8006)
│   └── shared-utils/          # Shared code
├── frontend/                   # Next.js application (port 3000)
├── database/                   # Database schema
├── docker-compose.yml         # Production config
├── docker-compose.dev.yml     # Development config
├── docker-compose.test.yml    # Testing config
├── docker-compose.elk.yml     # ELK stack
├── ARCHITECTURE.md            # Architecture documentation
├── SYSTEM_PROMPT.md           # System prompt
├── DEVELOPER_PROMPT.md        # This file
└── .env.example               # Environment variables
```

## Порты сервисов (Development)

| Сервис | Контейнерный порт | Хост порт | Статус |
|--------|------------------|-----------|--------|
| Frontend | 3000 | 3000 | ✅ Реализован |
| Auth | 8000 | 8001 | ✅ Реализован |
| Places | 8001 | 8002 | 🚧 Заглушка |
| Reports | 8002 | 8003 | 🚧 Заглушка |
| Booking | 8003 | 8004 | 🚧 Заглушка |
| Shop | 8004 | 8005 | 🚧 Заглушка |
| Email | 8005 | 8006 | ✅ Реализован |
| Forecast | 8000 | 8007 | ✅ Этап 1 |

**Правило портов**: `docker-compose.DEV_PORT = next.config.js.PORT`, `docker-compose.CONTAINER_PORT = Dockerfile.CMD`

## Frontend API Proxies (Next.js Rewrites)

```javascript
// frontend/next.config.js
{
  source: '/api/v1/auth/:path*',
  destination: 'http://host.docker.internal:8001/api/v1/auth/:path*'
},
{
  source: '/api/v1/places/:path*',
  destination: 'http://host.docker.internal:8002/api/v1/places/:path*'
},
{
  source: '/api/v1/reports/:path*',
  destination: 'http://host.docker.internal:8003/api/v1/reports/:path*'
},
{
  source: '/api/v1/booking/:path*',
  destination: 'http://host.docker.internal:8004/api/v1/booking/:path*'
},
{
  source: '/api/v1/shop/:path*',
  destination: 'http://host.docker.internal:8005/api/v1/shop/:path*'
},
{
  source: '/api/v1/email/:path*',
  destination: 'http://host.docker.internal:8006/api/v1/email/:path*'
},
{
  source: '/api/v1/forecast/:path*',
  destination: 'http://host.docker.internal:8007/api/v1/forecast/:path*'
},
{
  source: '/api/v1/weather/:path*',
  destination: 'http://host.docker.internal:8007/api/v1/weather/:path*'
},
{
  source: '/api/v1/regions/:path*',
  destination: 'http://host.docker.internal:8007/api/v1/regions/:path*'
}
```

## Реализованные сервисы

### Auth Service (порт 8001 хост, 8000 контейнер) ✅

**Responsibilities:**
- Регистрация пользователей с подтверждением email
- Вход в систему (JWT)
- Сброс пароля
- Управление профилем пользователя
- RBAC (Role-Based Access Control): user, moderator, admin

**Реализованные эндпоинты:**
```
POST   /api/v1/auth/register              - Регистрация пользователя
POST   /api/v1/auth/verify-email          - Подтверждение email
POST   /api/v1/auth/login                 - Вход в систему
POST   /api/v1/auth/reset-password/request - Запрос сброса пароля
POST   /api/v1/auth/reset-password/confirm - Подтверждение сброса пароля
GET    /api/v1/users/me                   - Получить текущего пользователя
PUT    /api/v1/users/me                   - Обновить профиль
PATCH  /api/v1/users/me/password          - Изменить пароль
GET    /api/v1/maps/geocode              - Геокодирование города (каш Redis)
GET    /health                             - Health check
```

**Модели БД:**
- `users` - таблица пользователей (с полями role: user/moderator/admin, city: город пользователя)
- `refresh_tokens` - refresh токены JWT
- `email_verification_codes` - коды подтверждения email

### Интеграция Яндекс Карт ✅

**Реализованный функционал:**
- Поле `city` в модели User для персонализации карты
- Сервис геокодирования с кэшированием в Redis (TTL: 1 час)
- Endpoint `GET /api/v1/maps/geocode` для получения координат города
- Компонент YandexMap для отображения карты во frontend
- Размытие карты для незарегистрированных пользователей
- Обновление города в профиле пользователя

**Ключ API Яндекс Карт:**
```
dfb59053-0011-47fb-a6f1-a14efb9160d1
```

**Файлы:**
- Backend:
  - `services/auth-service/app/models/user.py` - модель User с полем city
  - `services/auth-service/app/schemas/auth.py` - схемы UserResponse, UserUpdate
  - `services/auth-service/app/services/geocode.py` - сервис геокодирования
  - `services/auth-service/app/endpoints/maps.py` - endpoint для геокодирования
  - `services/auth-service/app/core/database.py` - get_redis функция
- Frontend:
  - `frontend/components/YandexMap.tsx` - компонент карты
  - `frontend/app/map/page.tsx` - страница карты
  - `frontend/app/profile/components/MyPlacesTab.tsx` - вкладка "Мои места"
  - `frontend/app/profile/components/SettingsTab.tsx` - настройки профиля с полем города
  - `frontend/types/yandex-maps.d.ts` - TypeScript типы для Яндекс Карт

**Тесты:**
- Unit тесты: `services/auth-service/tests/test_geocode_service.py` (10 тестов)
- Покрытие: Геокодирование, кэширование Redis, обработка ошибок

### Email Service (порт 8006 хост, 8005 контейнер) ✅

**Responsibilities:**
- Email уведомления
- Генерация кодов подтверждения
- SMTP интеграция с Yandex

**Реализованные эндпоинты:**
```
POST   /api/v1/email/send         - Отправить email (требует X-API-Key)
POST   /api/v1/email/generate-code - Сгенерировать код (требует X-API-Key)
GET    /health                      - Health check
```

**Безопасность (SEC-005):**
- API Key аутентификация через заголовок `X-API-Key`
- Ключ хранится в `EMAIL_SERVICE_API_KEY` (min 32 chars)
- Auth Service передает API Key при вызове Email Service
- 401 Unauthorized - если заголовок отсутствует (`API_KEY_REQUIRED`)
- 403 Forbidden - если ключ неверный (`INVALID_API_KEY`)

### Forecast Service (порт 8007 хост, 8000 контейнер) ✅

**Responsibilities:**
- Прогноз клева рыбы на основе погодных условий
- Интеграция с OpenWeatherMap API
- Хранение данных о регионах России (85 субъектов)
- Кэширование погодных данных в Redis

**Реализованные эндпоинты:**
```
GET    /api/v1/regions                   - Список всех регионов
GET    /api/v1/regions/:id               - Регион по ID
GET    /api/v1/weather/current/:region_id - Текущая погода по региону
GET    /api/v1/weather/currentByCoords   - Погода по координатам
GET    /health                           - Health check
```

**Модели БД:**
- `regions` - 85 регионов России (name, code, latitude, longitude, timezone)
- `weather_data` - почасовые погодные данные
- `fish_bite_settings` - настройки клева по видам рыб
- `fishing_forecasts` - прогнозы клева

**Особенности:**
- OpenWeatherMap API (бесплатно 1000 req/день)
- Redis кэширование (TTL: 1 час)
- Автоматический seed 85 регионов при старте
- Unit тесты (25+ тестов)

**Тесты:**
- `services/forecast-service/tests/test_weather_service.py` - тесты WeatherService
- `services/forecast-service/tests/test_models.py` - тесты моделей
- `services/forecast-service/tests/test_endpoints.py` - тесты эндпоинтов

**Переменные окружения:**
```bash
OPENWEATHERMAP_API_KEY=your_api_key_here
```

## Frontend (Next.js 15, порт 3000) ✅

**Реализованные страницы:**
```
/                    - Главная страница
/login               - Вход
/register            - Регистрация
/verify-email        - Подтверждение email
/reset-password      - Сброс пароля
/profile             - Профиль пользователя
/map                 - Интерактивная карта
/resorts             - Список мест
/shop                - Магазин
/stores              - Магазины
/forecast            - Прогноз погоды
```

**State Management:**
- Zustand stores
- `useAuthStore` - управление аутентификацией

## Health Check обязательные требования

Каждый микросервис должен иметь эндпоинт `/health`:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "service-name",
        "version": "1.0.0"
    }
```

**Требования:**
- Endpoint должен быть доступен без аутентификации
- Возвращать JSON с полями: `status`, `service`, `version`
- Может включать дополнительные поля состояния

## Чек-лист разработки

### Чек-лист реализации новой функциональности:
- [ ] 0. Архитектурное решение согласовано
- [ ] 0.1 **TODO list согласован с пользователем** (КРИТИЧЕСКИ ВАЖНО!)
- [ ] 1. Бэкенд: модели/схемы созданы
- [ ] 2. Бэкенд: эндпоинты реализованы
- [ ] 3. Бэкенд: **Unit тесты написаны** (≥80% покрытие)
- [ ] 4. Бэкенд: **Логи добавлены** с требуемыми полями (INFO для действий, ERROR для ошибок)
- [ ] 5. Бэкенд: **Кэширование настроено** (если требуется: Redis с TTL)
- [ ] 6. Бэкенд: **Обработка ошибок внешних API** (retries, fallback, graceful degradation)
- [ ] 7. Фронтенд: UI компоненты реализованы
- [ ] 8. Фронтенд: **Unit тесты написаны** (≥80% покрытие)
- [ ] 9. **ВСЕ тесты проходят успешно** (pytest + npm test) - КРИТИЧЕСКИ ВАЖНО!
- [ ] 10. **Логи видны в Kibana**: проверка отправки логов
- [ ] 11. Функциональное тестирование: проверен полный flow
- [ ] 12. Документация обновлена
- [ ] 13. **🔄 ЗАВЕРШЕНИЕ: Перезапуск Docker и всех сервисов** - КРИТИЧЕСКИ ВАЖНО!
- [ ] 14. **🔄 ЗАВЕРШЕНИЕ: Проверка health checks всех сервисов** - КРИТИЧЕСКИ ВАЖНО!

### Чек-лист перед коммитом:
- [ ] Задача согласована с пользователем перед разработкой
- [ ] Unit тесты написаны (backend + frontend)
- [ ] **ВСЕ тесты проходят успешно** (нет падающих тестов)
- [ ] Docker перезапущен: `down && build && up -d`
- [ ] Docker-compose успешно собирается
- [ ] Health checks работают
- [ ] Нет конфликтов портов
- [ ] Логи видны в Kibana
- [ ] Обновлена документация
- [ ] Логи не содержат ошибок
- [ ] Кэширование работает корректно (если используется)
- [ ] Обработка ошибок внешних API реализована (если используется)

## Переменные окружения (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres_password@postgres:5432/fishing_db
REDIS_URL=redis://redis:6379/0

# Auth
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=your-email@yandex.ru
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@yandex.ru
SMTP_FROM_NAME=FishMap
ENABLE_EMAIL_SENDING=false  # true для production
EMAIL_CODE_EXPIRE_MINUTES=15
EMAIL_SERVICE_API_KEY=your-secure-api-key-min-32-chars  # API Key для Email Service (SEC-005)

# External Services
MAPBOX_API_KEY=your-mapbox-api-key
YANDEX_MAPS_API_KEY=dfb59053-0011-47fb-a6f1-a14efb9160d1
OPENWEATHERMAP_API_KEY=your-openweathermap-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# Logging
LOG_LEVEL=INFO
LOGSTASH_URL=http://logstash:5000
SERVICE_NAME=your-service-name
```

## Аутентификация и авторизация

### Роли пользователей (RBAC)
- **user** - обычный пользователь (по умолчанию)
- **moderator** - модератор
- **admin** - администратор

**ВАЖНО**: Поле `role` должно быть включено в JWT токен при создании:
```python
access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
```

## Запуск проекта

### Локальная разработка (Makefile)
```bash
# Показать все команды
make help

# Запуск всех сервисов
make dev

# Запуск с ELK Stack
make elk

# Просмотр логов
make dev-logs
make dev-logs S=auth-service  # конкретный сервис

# Проверка здоровья
make health

# Остановка сервисов
make dev-down
```

### Ручные команды Docker
```bash
# Запуск всех сервисов
docker-compose -f docker-compose.dev.yml up -d

# Запуск с ELK Stack
docker-compose -f docker-compose.dev.yml -f docker-compose.elk.yml up -d

# Просмотр логов
docker-compose -f docker-compose.dev.yml logs -f

# Остановка сервисов
docker-compose -f docker-compose.dev.yml down
```

### Доступ к сервисам (Development)
```
Frontend: http://localhost:3000
Auth Service: http://localhost:8001
Places Service: http://localhost:8002
Reports Service: http://localhost:8003
Booking Service: http://localhost:8004
Shop Service: http://localhost:8005
Email Service: http://localhost:8006
Forecast Service: http://localhost:8007
Kibana: http://localhost:5601
Elasticsearch: http://localhost:9200
PostgreSQL: localhost:5432
Redis: localhost:6379
```

## Безопасность

- HTTPS в production (запланировано)
- Валидация входных данных (Pydantic)
- Защита от SQL injection (SQLAlchemy)
- XSS защита (React escaping)
- RBAC с ролями user/moderator/admin

## Code Conventions

### Python (Backend)

**Инструменты:**
- **Linter**: `ruff check .`
- **Formatter**: `ruff format .`
- **Type checker**: `mypy services/`

**Структура сервиса:**
```
services/{service-name}/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB connection
│   │   └── logging_config.py
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── endpoints/           # API routes
│   ├── services/            # Business logic
│   └── middleware/
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_services.py
├── requirements.txt
└── Dockerfile
```

**Правила:**
- Async функции везде (`async def`)
- Type hints обязательны
- Docstrings для публичных функций
- Импорты: stdlib → third-party → local

### TypeScript (Frontend)

**Инструменты:**
- **Linter**: `npm run lint`
- **Type check**: `npm run typecheck`

**Структура:**
```
frontend/
├── app/                     # Next.js App Router pages
├── components/              # React components
├── lib/                     # Utilities
├── stores/                  # Zustand stores
├── types/                   # TypeScript types
└── public/
```

**Правила:**
- Functional components
- Type props with interfaces
- Use `useAuthStore` for auth state

## Git Workflow

### Ветки

```
main           # Production-ready code
├── develop    # Development branch
│   ├── feature/XXX-description   # Новые фичи
│   ├── fix/XXX-description       # Багфиксы
│   └── refactor/XXX-description  # Рефакторинг
```

### Формат коммитов (Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Типы:**
- `feat` - новая функциональность
- `fix` - багфикс
- `refactor` - рефакторинг без изменения функционала
- `docs` - документация
- `test` - тесты
- `chore` - рутинные задачи

**Примеры:**
```
feat(auth): add password reset functionality
fix(auth): resolve JWT token expiration issue
refactor(frontend): extract map component
docs(readme): update installation instructions
test(auth): add unit tests for geocode service
```

### Pull Request процесс

1. Создать ветку от `develop`
2. Сделать изменения + тесты
3. Запустить lint, typecheck, tests
4. Создать PR в `develop`
5. Пройти code review
6. Squash and merge

**PR Title Format:** `type(scope): description`

## Главный принцип

Каждое изменение должно повышать ценность платформы, не снижая надежность и поддерживаемость существующей системы.

### КРИТИЧЕСКИ ВАЖНО - Требования для избежания частых ошибок

#### 1. Всегда проверяйте логи Docker ПЕРЕД и ПОСЛЕ изменений
```bash
# ПЕРЕД разработкой - убедитесь что нет ошибок
docker-compose -f docker-compose.dev.yml logs --tail 50

# ПОСЛЕ изменений - проверьте что изменения не сломали систему
docker-compose -f docker-compose.dev.yml logs frontend --tail 100 | grep -E "(Error|error|failed)"
```

#### 2. Используйте правильные имена сервисов Docker
```javascript
// ❌ НЕПРАВИЛЬНО - localhost не работает в Docker сети
'/api/v1/places': 'http://localhost:8002'

// ✅ ПРАВИЛЬНО - используйте имена сервисов Docker
'/api/v1/places': 'http://places-service:8001'
```
**Правило**: В Docker Compose используйте `service-name:internal-port`, НЕ `localhost:external-port`

#### 3. Обработка body для HTTP запросов в middleware/прокси
```javascript
// ❌ НЕПРАВИЛЬНО - body для DELETE/GET запросов вызывает ошибки
if (request.method !== 'GET' && request.method !== 'HEAD') {
  body = await request.arrayBuffer();
}
fetch(url, { body: body || undefined }); // body может быть ArrayBuffer(0) - вызывает ошибку

// ✅ ПРАВИЛЬНО - body только для методов, которые его реально используют
const hasBody = ['POST', 'PUT', 'PATCH'].includes(request.method);
const body = hasBody ? await request.arrayBuffer() : null;

if (body && body.byteLength > 0) {
  fetchOptions.body = body;
}
```

#### 4. Удаляйте content-length при проксировании
```javascript
// ❌ НЕПРАВИЛЬНО - content-length от оригинального запроса не совпадает с body
request.headers.forEach((value, key) => {
  if (key.toLowerCase() !== 'host') {
    headers.set(key, value);
  }
});

// ✅ ПРАВИЛЬНО - удаляйте content-length, fetch установит правильный
request.headers.forEach((value, key) => {
  if (key.toLowerCase() !== 'host' && key.toLowerCase() !== 'content-length') {
    headers.set(key, value);
  }
});
```

#### 5. Проверяйте типы данных из API перед использованием методов
```typescript
// ❌ НЕПРАВИЛЬНО - API может вернуть строку вместо числа
{place.latitude.toFixed(6)}

// ✅ ПРАВИЛЬНО - конвертируйте в число
{Number(place.latitude).toFixed(6)}
```

#### 6. SQLAlchemy cascade и PostgreSQL ON DELETE CASCADE
```python
# ❌ НЕПРАВИЛЬНО - конфликт между SQLAlchemy cascade и PostgreSQL CASCADE
favorites = relationship("FavoritePlace", back_populates="place", cascade="all, delete-orphan")
# При этом в БД: ForeignKey("places.id", ondelete="CASCADE")

# ✅ ПРАВИЛЬНО - используйте только один механизм
# Вариант 1: Только PostgreSQL CASCADE (рекомендуется)
favorites = relationship("FavoritePlace", back_populates="place")
# В БД: ForeignKey("places.id", ondelete="CASCADE")

# Вариант 2: Только SQLAlchemy cascade
favorites = relationship("FavoritePlace", back_populates="place", cascade="all, delete-orphan")
# В БД: ForeignKey("places.id")  # без ondelete
```

#### 7. Не добавляйте платформенно-зависимые пакеты в package.json
```json
// ❌ НЕПРАВИЛЬНО - пакет только для macOS ARM64
"dependencies": {
  "@next/swc-darwin-arm64": "^16.1.6"
}

// ✅ ПРАВИЛЬНО - npm сам установит нужный пакет для платформы
"dependencies": {
  // @next/swc-* устанавливается автоматически
}
```

#### 8. Не используйте console.log в JSX рендеринге
```tsx
// ❌ НЕПРАВИЛЬНО - console.log возвращает void, не ReactNode
<div>
  {console.log("debug")}
  <span>Content</span>
</div>

// ✅ ПРАВИЛЬНО - используйте useEffect для логов
useEffect(() => {
  console.log("debug");
}, []);

// Или IIFE если нужно в JSX
<div>
  {(() => { console.log("debug"); return null; })()}
  <span>Content</span>
</div>
```

#### 9. Всегда очищайте Docker кэш при persistent ошибках
```bash
# Если после build изменения не применяются
docker-compose -f docker-compose.dev.yml build --no-cache <service-name>
docker-compose -f docker-compose.dev.yml up -d <service-name>

# Полная очистка
docker system prune -f
docker builder prune -f
```

#### 10. Проверяйте порты и конфигурацию docker-compose
```yaml
# ❌ НЕПРАВИЛЬНО - несоответствие портов
services:
  places-service:
    ports:
      - "8002:8001"  # хост:контейнер
    environment:
      - PLACES_SERVICE_URL=http://localhost:8002  # должно быть places-service:8001

# ✅ ПРАВИЛЬНО
services:
  places-service:
    ports:
      - "8002:8001"  # хост:контейнер
    environment:
      - PLACES_SERVICE_URL=http://places-service:8001  # имя_сервиса:контейнерный_порт
```

#### 11. Согласовывайте типы данных между Frontend и Backend
```typescript
// ❌ НЕПРАВИЛЬНО - типы не совпадают
// Backend (Python):
//   fish_types: List[UUID]  # возвращает ["uuid1", "uuid2"]
// Frontend (TypeScript):
//   fish_types: FishType[]  // ожидает [{id, name, icon}]
// При редактировании:
//   place.fish_types.map(f => f.id)  // f - строка, f.id = undefined!

// ✅ ПРАВИЛЬНО - типы совпадают
// Backend (Python):
//   fish_types: List[FishTypeInPlace]  # возвращает [{id, name, icon, category}]
// Frontend (TypeScript):
//   fish_types: FishType[]  // получает [{id, name, icon, category}]
// При редактировании:
//   place.fish_types.map(f => f.id)  // f - объект, f.id = "uuid" ✓

// Правило: Перед использованием данных из API, проверьте:
// 1. Что возвращает backend (откройте /docs или проверьте response)
// 2. Что ожидает frontend (проверьте TypeScript интерфейсы)
// 3. Что типы СОВПАДАЮТ, а не просто "похожи"
```

**КРИТИЧЕСКИ ВАЖНО:**
1. **ВСЕГДА** согласовывайте разработку с пользователем перед началом работы
2. **ВСЕГДА** согласовывайте todo list с пользователем перед реализацией
3. **ВСЕГДА** перезапускайте Docker и все сервисы перед началом разработки
4. **ВСЕГДА** пишем юнит тесты для новой функциональности (≥80% покрытие)
5. **ВСЕГДА** все тесты должны проходить успешно - разработка не завершена, если есть падающие тесты
6. **ВСЕГДА** пишем логи и проверяем их в Kibana (INFO для действий, ERROR для ошибок)
7. **ВСЕГДА** используем кэширование для внешних API (Redis с TTL)
8. **ВСЕГДА** реализуем обработку ошибок внешних API (retries, fallback, graceful degradation)
9. **ВСЕГДА** проверяем health checks после перезапуска
10. **ВСЕГДА** перезапускаем Docker и все сервисы в окончании разработки
11. **ВСЕГДА** проверяем логи Docker на ошибки ПЕРЕД и ПОСЛЕ изменений
12. **ВСЕГДА** используем имена сервисов Docker (не localhost) в конфигурации
13. **ВСЕГДА** проверяем совпадение типов данных между Frontend и Backend (List[UUID] ≠ FishType[])

**Процесс разработки (обязательный):**
```
1. Согласование → 2. Разработка → 3. Тесты (код) → 4. Все тесты проходят → 5. Перезапуск Docker → 6. Health checks OK → ГОТОВО
```

При работе с проектом всегда проверяйте:
1. Какие сервисы РЕАЛЬНО реализованы (✅)
2. Какие сервисы только заглушки (🚧)
3. Какие таблицы БД РЕАЛЬНО используются
4. Какие эндпоинты РЕАЛЬНО существуют

**НЕТ СОГЛАСОВАНИЯ = НЕТ РАЗРАБОТКИ!**
**ЕСТЬ ПАДАЮЩИЕ ТЕСТЫ = РАЗРАБОТКА НЕ ЗАВЕРШЕНА!**

Не создавайте код для эндпоинтов или моделей, которые еще не реализованы, если это явно не требуется для новой задачи.

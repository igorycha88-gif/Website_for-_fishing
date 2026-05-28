# Системный промпт проекта "Платформа для рыбалки"

## Обзор проекта

Платформа для рыбалки - это микросервисное веб-приложение для рыболовов на ранней стадии разработки.

**Текущий статус**: Ранняя разработка
- ✅ Auth Service - полностью реализован
- ✅ Email Service - полностью реализован
- ✅ Frontend - основные страницы реализованы
- 🚧 Places Service - заглушка (планируется)
- 🚧 Reports Service - заглушка (планируется)
- 🚧 Booking Service - заглушка (планируется)
- 🚧 Shop Service - заглушка (планируется)

## Технологический стек

### Frontend
- **Framework**: Next.js 15 (TypeScript) с App Router
- **Styling**: Tailwind CSS
- **State Management**: Zustand (useAuthStore для аутентификации)
- **Animations**: Framer Motion
- **API Proxy**: Next.js rewrites для проксирования к микросервисам

### Backend (FastAPI / Python)
- **Auth Service** (порт 8001 хост, 8000 контейнер) - реализован
- **Places Service** (порт 8002 хост, 8001 контейнер) - заглушка
- **Reports Service** (порт 8003 хост, 8002 контейнер) - заглушка
- **Booking Service** (порт 8004 хост, 8003 контейнер) - заглушка
- **Shop Service** (порт 8005 хост, 8004 контейнер) - заглушка
- **Email Service** (порт 8006 хост, 8005 контейнер) - реализован
- **Forecast Service** (порт 8007 хост, 8000 контейнер) - реализован (Этап 1)

### Database
- **Database**: PostgreSQL 16 (одна общая база для всех сервисов)
- **ORM**: SQLAlchemy (async)
- **Migrations**: schema.sql (миграции через raw SQL)

### Cache
- **Redis**: Запланирован для сессий и кэширования

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose (development), Docker Swarm (production - запланирован)
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) - опционально

### External Services
- **Mapbox**: Запланирован для интерактивных карт
- **Stripe**: Запланирован для платежей
- **Cloudinary**: Запланирован для хранения изображений
- **Yandex SMTP**: Используется для email

## Архитектура микросервисов

### Порты сервисов (Development)

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

### Frontend API Proxies (Next.js Rewrites)

```javascript
// frontend/next.config.js
{
  source: '/api/v1/auth/:path*',
  destination: 'http://host.docker.internal:8001/api/v1/auth/:path*'
},
{
  source: '/api/v1/users/:path*',
  destination: 'http://host.docker.internal:8001/api/v1/users/:path*'
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
GET    /health                             - Health check
```

**Модели БД:**
- `users` - таблица пользователей (с полем role: user/moderator/admin)
- `refresh_tokens` - refresh токены JWT
- `email_verification_codes` - коды подтверждения email

**Особенности:**
- Email верификация через Email Service
- Bcrypt для хэширования паролей
- JWT access токены (без срока действия, типично 30 минут)
- Структурированное логирование с Logstash

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
GET    /                            - Root endpoint
```

**Особенности:**
- SMTP интеграция (Yandex)
- Переключатель отправки email для разработки (`ENABLE_EMAIL_SENDING`)
- Асинхронная отправка email
- Структурированное логирование
- **API Key аутентификация** для межсервисного взаимодействия (SEC-005)

**API Key Authentication:**
- Заголовок: `X-API-Key`
- Переменная окружения: `EMAIL_SERVICE_API_KEY` (min 32 chars)
- Auth Service передает API Key при вызове Email Service

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
GET    /api/v1/weather/currentByCoords   - Погода по координатам (lat, lon)
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
/profile             - Профиль пользователя (вкладки: Profile, Settings)
/map                 - Интерактивная карта
/resorts             - Список мест
/shop                - Магазин
/stores              - Магазины
/forecast            - Прогноз погоды
```

**State Management:**
- Zustand stores
- `useAuthStore` - управление аутентификацией

## Схема БД

### Реализованные таблицы ✅

**users (Auth Service):**
```python
id: UUID (PK)
email: VARCHAR(255) UNIQUE
username: VARCHAR(100) UNIQUE
password_hash: VARCHAR(255)
first_name: VARCHAR(100)
last_name: VARCHAR(100)
phone: VARCHAR(20)
avatar_url: VARCHAR(500)
is_active: BOOLEAN (default true)
is_verified: BOOLEAN (default false)
role: VARCHAR(20) (default 'user')  # user, moderator, admin
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

**refresh_tokens (Auth Service):**
```python
id: UUID (PK)
user_id: UUID (FK users.id)
token: VARCHAR(500) UNIQUE
expires_at: TIMESTAMP
created_at: TIMESTAMP
```

**email_verification_codes (Auth Service):**
```python
id: UUID (PK)
email: VARCHAR(255)
code: VARCHAR(6)
attempts: INTEGER (default 0)
expires_at: TIMESTAMP
created_at: TIMESTAMP
```

### Запланированные таблицы 🔮 (определены в schema.sql, но не используются)

- `places` - места для рыбалки
- `reports` - отчеты о рыбалке
- `bookings` - бронирования
- `booking_slots` - слоты для бронирования
- `products` - товары магазина
- `categories` - категории товаров
- `orders` - заказы
- `order_items` - элементы заказа
- `ratings` - рейтинги

## Аутентификация и авторизация

### Поток регистрации
```
1. Пользователь заполняет форму регистрации
   Frontend → Auth Service (/api/v1/auth/register)
   → Создает пользователя в БД
   → Генерирует код подтверждения
   → Отправляет email через Email Service

2. Пользователь получает email с кодом

3. Пользователь вводит код
   Frontend → Auth Service (/api/v1/auth/verify-email)
   → Проверяет код
   → Обновляет user.is_verified = true
   → Возвращает JWT access token

4. Frontend сохраняет access token в памяти
```

### Поток входа
```
1. Пользователь вводит email и пароль
   Frontend → Auth Service (/api/v1/auth/login)
   → Проверяет учетные данные
   → Проверяет is_verified
   → Возвращает JWT access token

2. Frontend сохраняет access token

3. Frontend включает Authorization header для аутентифицированных запросов
   Authorization: Bearer <access_token>
```

### Роли пользователей (RBAC)
- **user** - обычный пользователь (по умолчанию)
- **moderator** - модератор
- **admin** - администратор

**ВАЖНО**: Поле `role` должно быть включено в JWT токен при создании:
```python
access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
```

## Запуск проекта

### Локальная разработка
```bash
# Запуск всех сервисов
docker-compose -f docker-compose.dev.yml up -d

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
Email Service: http://8006
Forecast Service: http://localhost:8007
PostgreSQL: localhost:5432
Redis: localhost:6379
```

### Переменные окружения (.env)
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

# External Services (planned)
MAPBOX_API_KEY=your-mapbox-api-key
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

# CORS
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

## Процесс разработки

### 1. Проектирование перед кодом
- Анализ требований → архитектурное решение → дизайн API → согласование
- **Новый микросервис ТОЛЬКО при:**
  - Четко выделенной бизнес-области
  - Требованиях к независимому масштабированию
  - Разных циклах разработки от существующих сервисов

### 2. Планирование реализации
```
[ ] 0. Архитектурное решение
[ ] 1. Бэкенд: модели/схемы
[ ] 2. Бэкенд: эндпоинты
[ ] 3. Фронтенд: UI компоненты
[ ] 4. Тестирование
[ ] 5. Документация
[ ] 6. Деплой и проверка
```

### 3. Структура проекта
```
.
├── services/
│   ├── auth-service/          # Auth service (port 8001)
│   ├── places-service/        # Places service (port 8002)
│   ├── reports-service/       # Reports service (port 8003)
│   ├── booking-service/       # Booking service (port 8004)
│   ├── shop-service/          # Shop service (port 8005)
│   ├── email-service/         # Email service (port 8006)
│   ├── forecast-service/      # Forecast service (port 8007)
│   └── shared-utils/          # Shared code
├── frontend/                   # Next.js application (port 3000)
├── database/                   # Database schema
├── docker-compose.yml         # Production config
├── docker-compose.dev.yml     # Development config
├── docker-compose.test.yml    # Testing config
├── docker-compose.elk.yml     # ELK stack
├── ARCHITECTURE.md            # Architecture documentation
├── DEPLOYMENT.md              # Deployment guide
├── MONITORING.md              # Monitoring setup
├── DOCKER.md                  # Docker guide
├── README.md                  # Project overview
└── .env.example               # Environment variables
```

## Чек-листы

### Чек-лист изменений в авторизации:
- [ ] Role включена в JWT токен
- [ ] Pydantic схемы включают role
- [ ] Типы в модели, схеме и БД согласованы
- [ ] Rewrite rules добавлены для новых сервисов (если добавляются)
- [ ] Docker порты совпадают (CMD = CONTAINER, хост = next.config.js)
- [ ] Полный flow протестирован (регистрация → вход → проверка ролей)

### Чек-лист добавления нового микросервиса:
- [ ] Определена четкая бизнес-область
- [ ] Выбран порт (согласно таблице выше)
- [ ] Создан Dockerfile с правильным портом
- [ ] Добавлен в docker-compose.yml и docker-compose.dev.yml
- [ ] Добавлены rewrite rules в frontend/next.config.js
- [ ] Добавлен health check
- [ ] Обновлена ARCHITECTURE.md
- [ ] Обновлен README.md

### Чек-лист перед коммитом:
- [ ] Все тесты проходят (если есть)
- [ ] Docker-compose успешно собирается
- [ ] Health checks работают
- [ ] Нет конфликтов портов
- [ ] Обновлена документация
- [ ] Логи не содержат ошибок

## Документация

**Обязательно обновлять при изменениях:**
1. `README.md` сервиса (при изменении функциональности)
2. `database/schema.md` (при изменении моделей БД)
3. `ARCHITECTURE.md` (при изменении архитектуры)
4. Swagger/OpenAPI документация (при изменении API)
5. `.env.example` (новые переменные окружения)
6. Системный промпт (при изменениях архитектуры)

## Безопасность

- HTTPS в production (запланировано)
- Валидация входных данных (Pydantic)
- Защита от SQL injection (SQLAlchemy)
- XSS защита (React escaping)
- HTTP-only cookies для refresh токенов (запланировано)
- RBAC с ролями user/moderator/admin

## Мониторинг и логирование

### ELK Stack (опционально)
```bash
# Запуск с логированием
docker-compose -f docker-compose.dev.yml -f docker-compose.elk.yml up -d

# Доступ к Kibana
http://localhost:5601
```

### Health Checks
Каждый сервис экспонирует `/health` endpoint:
```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0"
}
```

## Roadmap

### Phase 1: Authentication ✅ (Complete)
- [x] User registration with email verification
- [x] Login/logout
- [x] Password reset
- [x] User profile management

### Phase 2: Places Service 🚧 (In Progress)
- [ ] CRUD operations for places
- [ ] Map integration (Mapbox)
- [ ] Search and filtering
- [ ] Place images (Cloudinary)

### Phase 3: Reports Service 🔮 (Planned)
- [ ] Report creation
- [ ] Image upload
- [ ] Comments and ratings
- [ ] Fish species tracking

### Phase 4: Booking Service 🔮 (Planned)
- [ ] Booking system
- [ ] Availability management
- [ ] Stripe payment integration

### Phase 5: Shop Service 🔮 (Planned)
- [ ] Product catalog
- [ ] Shopping cart
- [ ] Order management
- [ ] Stripe payment integration

### Future Improvements 🔮
- WebSocket notifications
- Mobile app (React Native)
- GraphQL API
- Message queue (RabbitMQ)
- Microservice databases
- Prometheus/Grafana monitoring

## Главный принцип

Каждое изменение должно повышать ценность платформы, не снижая надежность и поддерживаемость существующей системы.

**ВАЖНО**: При работе с проектом всегда проверяйте:
1. Какие сервисы РЕАЛЬНО реализованы (✅)
2. Какие сервисы только заглушки (🚧)
3. Какие таблицы БД РЕАЛЬНО используются
4. Какие эндпоинты РЕАЛЬНО существуют

Не создавайте код для эндпоинтов или моделей, которые еще не реализованы, если это явно не требуется для новой задачи.

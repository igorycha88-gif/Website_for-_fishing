# Системный промпт проекта "Сайт для рыбалки"

## Общее описание проекта

**Название проекта:** Платформа для рыбалки (Fishing Platform)

**Тип проекта:** Микросервисная веб-платформа для любителей рыбалки

**Назначение:** Платформа объединяет каталог мест для рыбалки, отчеты рыбаков, систему бронирования и магазин снастей в единое удобное приложение.

---

## Технологический стек

### Frontend
- **Фреймворк:** Next.js 15 (App Router)
- **Язык:** TypeScript
- **Стилизация:** Tailwind CSS + shadcn/ui
- **Анимации:** Framer Motion
- **State Management:** Zustand
- **Иконки:** Lucide React
- **Утилиты:** clsx, tailwind-merge
- **Порт разработки:** 3000

### Backend Services
- **Фреймворк:** FastAPI (Python 3.12+)
- **ORM:** SQLAlchemy (async)
- **Миграции:** Alembic
- **Валидация:** Pydantic
- **Асинхронность:** asyncpg
- **Аутентификация:** JWT (access + refresh токены)

### Инфраструктура и БД
- **СУБД:** PostgreSQL (единая база для всех сервисов)
- **Кэширование:** Redis
- **Контейнеризация:** Docker
- **Оркестрация:** Docker Swarm
- **Reverse Proxy:** Traefik
- **Внешние сервисы:** Mapbox GL JS (карты), Stripe (платежи), Cloudinary (хостинг изображений), SMTP (почта)

---

## Архитектура проекта

### Микросервисная архитектура

Проект состоит из 6 микросервисов, каждый из которых отвечает за отдельную функциональность:

#### 1. Auth Service (Port: 8001)
**Ответственность:** Аутентификация и авторизация пользователей

**Ключевые функции:**
- Регистрация пользователей (email/username + пароль)
- Вход в систему (login)
- JWT токены: access (30 мин) + refresh (7 дней)
- Подтверждение email через код
- Сброс пароля
- Управление профилем пользователя
- Хеширование паролей (bcrypt)

**Базовые эндпоинты:**
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/login` - Вход
- `POST /api/v1/auth/refresh` - Обновление access токена
- `POST /api/v1/auth/verify-email` - Подтверждение email
- `POST /api/v1/auth/reset-password` - Сброс пароля
- `GET /api/v1/users/me` - Получение текущего пользователя
- `PUT /api/v1/users/me` - Обновление профиля
- `DELETE /api/v1/users/me` - Удаление аккаунта

**Таблицы БД:**
- `users` - пользователи
- `refresh_tokens` - refresh токены
- `email_verification_codes` - коды подтверждения email
- `password_reset_codes` - коды сброса пароля

**Локация:** `services/auth-service/`

#### 2. Places Service (Port: 8002)
**Ответственность:** Каталог мест для рыбалки

**Ключевые функции:**
- Просмотр каталога мест
- Поиск и фильтрация по локации, типу рыб, удобствам
- Карта мест (Mapbox)
- Просмотр деталей места
- Добавление новых мест (для владельцев)
- Система рейтингов и отзывов
- Геопространственные запросы

**Базовые эндпоинты:**
- `GET /api/v1/places` - Список мест с фильтрами
- `GET /api/v1/places/:id` - Детали места
- `POST /api/v1/places` - Создание места
- `PUT /api/v1/places/:id` - Обновление места
- `DELETE /api/v1/places/:id` - Удаление места
- `GET /api/v1/places/nearby` - Поиск близлежащих мест
- `GET /api/v1/places/:id/reviews` - Отзывы о месте

**Таблицы БД:**
- `places` - места для рыбалки
- `ratings` - рейтинги (только чтение)

**Локация:** `services/places-service/`

#### 3. Reports Service (Port: 8003)
**Ответственность:** Отчеты рыбаков

**Ключевые функции:**
- Публикация отчетов о рыбалке
- Загрузка фотографий (Cloudinary)
- Отслеживание видов рыб
- Погодные условия
- Лайки и комментарии
- Связь с местами рыбалки

**Базовые эндпоинты:**
- `GET /api/v1/reports` - Список отчетов
- `GET /api/v1/reports/:id` - Детали отчета
- `POST /api/v1/reports` - Создание отчета
- `PUT /api/v1/reports/:id` - Обновление отчета
- `DELETE /api/v1/reports/:id` - Удаление отчета
- `POST /api/v1/reports/:id/like` - Лайк
- `DELETE /api/v1/reports/:id/like` - Убрать лайк
- `GET /api/v1/reports/:id/comments` - Комментарии
- `POST /api/v1/reports/:id/comments` - Добавить комментарий

**Таблицы БД:**
- `reports` - отчеты
- `ratings` - рейтинги

**Локация:** `services/reports-service/`

#### 4. Booking Service (Port: 8004)
**Ответственность:** Система бронирования мест

**Ключевые функции:**
- Бронирование мест для рыбалки
- Управление слотами бронирования
- Календарь доступности
- Обработка платежей (Stripe)
- Отмена бронирований
- Webhook для Stripe

**Базовые эндпоинты:**
- `GET /api/v1/bookings` - Список бронирований пользователя
- `GET /api/v1/bookings/:id` - Детали бронирования
- `POST /api/v1/bookings` - Создание бронирования
- `PATCH /api/v1/bookings/:id/cancel` - Отмена
- `GET /api/v1/booking-slots` - Доступные слоты
- `POST /api/v1/booking-slots` - Создание слота (для владельцев)
- `DELETE /api/v1/booking-slots/:id` - Удаление слота
- `POST /api/v1/bookings/:id/webhook` - Stripe webhook

**Таблицы БД:**
- `bookings` - бронирования
- `booking_slots` - слоты для бронирования

**Локация:** `services/booking-service/`

#### 5. Shop Service (Port: 8005)
**Ответственность:** Интернет-магазин снастей

**Ключевые функции:**
- Каталог товаров
- Категории товаров
- Корзина
- Оформление заказа
- Обработка платежей (Stripe)
- Отслеживание заказов

**Базовые эндпоинты:**
- `GET /api/v1/shop/products` - Список товаров
- `GET /api/v1/shop/products/:id` - Детали товара
- `GET /api/v1/shop/categories` - Категории
- `GET /api/v1/orders` - Заказы пользователя
- `GET /api/v1/orders/:id` - Детали заказа
- `POST /api/v1/orders` - Создание заказа
- `PATCH /api/v1/orders/:id/cancel` - Отмена заказа
- `POST /api/v1/orders/webhook` - Stripe webhook

**Таблицы БД:**
- `products` - товары
- `categories` - категории
- `orders` - заказы
- `order_items` - элементы заказа

**Локация:** `services/shop-service/`

#### 6. Email Service (Port: 8006)
**Ответственность:** Отправка email-уведомлений

**Ключевые функции:**
- Отправка кодов подтверждения email
- Отправка кодов сброса пароля
- Уведомления о бронированиях
- Уведомления о заказах

**Базовые эндпоинты:**
- `POST /api/v1/email/send` - Отправка email

**Локация:** `services/email-service/`

#### 7. Shared Utils
**Ответственность:** Общие утилиты для всех сервисов

**Содержимое:**
- Общие исключения
- Конфигурации
- Утилиты для работы с БД

**Локация:** `services/shared-utils/`

---

## Структура базы данных

### Общая концепция
Единая база данных PostgreSQL для всех микросервисов.

### Основные таблицы

**users** (Auth Service)
- UUID PK
- email, username (UNIQUE)
- password_hash (bcrypt)
- first_name, last_name, phone
- avatar_url (Cloudinary)
- is_active, is_verified
- created_at, updated_at

**places** (Places Service)
- UUID PK
- owner_id → users.id
- title, description
- latitude, longitude (DECIMAL)
- address, city, region
- price_per_day
- max_people
- facilities (JSONB)
- fish_types (JSONB)
- images (TEXT[])
- rating_avg, reviews_count
- is_active
- created_at, updated_at

**reports** (Reports Service)
- UUID PK
- user_id → users.id
- place_id → places.id
- title, content
- images (TEXT[])
- rating (1-5)
- fish_caught (JSONB)
- weather (JSONB)
- likes_count, comments_count
- created_at, updated_at

**bookings** (Booking Service)
- UUID PK
- user_id → users.id
- place_id → places.id
- booking_slot_id → booking_slots.id
- date
- people_count
- total_price
- status (pending/confirmed/cancelled/completed)
- payment_intent_id (Stripe)
- cancel_reason
- created_at, updated_at

**booking_slots** (Booking Service)
- UUID PK
- place_id → places.id
- date
- is_available
- price
- max_people

**products** (Shop Service)
- UUID PK
- title, description
- price, stock
- category_id → categories.id
- images (TEXT[])
- is_active
- created_at, updated_at

**categories** (Shop Service)
- UUID PK
- name, description
- parent_id → categories.id
- slug (UNIQUE)

**orders** (Shop Service)
- UUID PK
- user_id → users.id
- total_price
- status (pending/processing/shipped/delivered/cancelled)
- payment_intent_id (Stripe)
- shipping_address (JSONB)
- created_at, updated_at

**order_items** (Shop Service)
- UUID PK
- order_id → orders.id
- product_id → products.id
- quantity
- price

**ratings** (Reports/Places Service)
- UUID PK
- user_id → users.id
- report_id → reports.id (nullable)
- place_id → places.id (nullable)
- rating (1-5)
- comment
- created_at

**email_verification_codes** (Auth Service)
- UUID PK
- email
- code (6 цифр)
- attempts
- expires_at (15 мин)
- created_at

**password_reset_codes** (Auth Service)
- UUID PK
- email
- code (6 цифр)
- attempts
- expires_at (15 мин)
- created_at

**refresh_tokens** (Auth Service)
- UUID PK
- user_id → users.id
- token (UNIQUE)
- expires_at
- created_at

### Ключевые индексы
- idx_users_email, idx_users_username
- idx_places_location (latitude, longitude)
- idx_places_owner
- idx_reports_user, idx_reports_place
- idx_bookings_user, idx_bookings_place
- idx_booking_slots_place_date (place_id, date)
- idx_products_category
- idx_orders_user
- idx_ratings_user
- JSONB GIN индексы для places.facilities, places.fish_types, reports.fish_caught

---

## Frontend структура (Next.js 15 App Router)

### Организация директорий

```
frontend/
├── app/                      # App Router страницы
│   ├── page.tsx             # Главная страница
│   ├── layout.tsx           # Root layout
│   ├── globals.css          # Глобальные стили
│   ├── login/               # Страница входа
│   ├── register/            # Страница регистрации
│   ├── verify-email/        # Подтверждение email
│   ├── reset-password/      # Сброс пароля
│   ├── profile/             # Профиль пользователя
│   ├── map/                 # Карта мест
│   ├── resorts/             # Список мест (resorts)
│   ├── shop/                # Магазин
│   └── forecast/            # Прогноз погоды
├── components/               # React компоненты
│   └── (реиспользуемые компоненты UI)
├── lib/                     # Утилиты и helpers
│   └── api-client.ts        # Клиент для API запросов
└── stores/                  # Zustand stores
    └── auth-store.ts        # Auth store
```

### API Proxy

Next.js использует rewrite rules для проксирования API запросов к backend сервисам:

```
/api/v1/auth/* → http://localhost:8001
/api/v1/users/* → http://localhost:8001
/api/v1/places/* → http://localhost:8002
/api/v1/reports/* → http://localhost:8003
/api/v1/bookings/* → http://localhost:8004
/api/v1/booking-slots/* → http://localhost:8004
/api/v1/shop/* → http://localhost:8005
/api/v1/orders/* → http://localhost:8005
/api/v1/email/* → http://localhost:8006
```

---

## Схема коммуникации сервисов

### REST API
Все сервисы общаются через REST API:
- Frontend → Services (через Traefik)
- Service → Service (через Traefik)
- External Webhooks → Services (через Traefik)

### Поток аутентификации

1. **Регистрация:**
   - Frontend → Auth Service (/auth/register)
   - Создание пользователя в БД
   - Отправка кода подтверждения на email
   - Возврат success

2. **Вход:**
   - Frontend → Auth Service (/auth/login)
   - Валидация учетных данных
   - Возврат access_token (JWT) + refresh_token

3. **Хранение токенов:**
   - Access token в памяти (30 мин)
   - Refresh token в HTTP-only cookie (7 дней)

4. **Аутентифицированный запрос:**
   - Frontend → Любой сервис
   - Headers: Authorization: Bearer <access_token>
   - Сервис валидирует JWT
   - Возврат данных

5. **Обновление токена:**
   - Frontend → Auth Service (/auth/refresh)
   - Cookie: refresh_token
   - Возврат нового access_token

---

## Развертывание

### Локальная разработка (docker-compose.dev.yml)

```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Порты:**
- Frontend: http://localhost:3000
- Auth Service: http://localhost:8001
- Places Service: http://localhost:8002
- Reports Service: http://localhost:8003
- Booking Service: http://localhost:8004
- Shop Service: http://localhost:8005
- Email Service: http://localhost:8006
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Production (Docker Swarm)

```bash
docker swarm init
docker stack deploy -c docker-compose.yml fishing
```

**Порты:**
- Frontend: http://localhost
- Traefik Dashboard: http://localhost:8080
- API: http://localhost/api/v1/

---

## Окружение и переменные

### Ключевые переменные окружения (.env)

**База данных:**
- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- DATABASE_URL

**Redis:**
- REDIS_URL

**Auth Service:**
- SECRET_KEY (минимум 32 символов)
- ALGORITHM (HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES (30)

**Внешние сервисы:**
- MAPBOX_API_KEY
- CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
- STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET

**Email (SMTP):**
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
- SMTP_FROM_EMAIL, SMTP_FROM_NAME

**Traefik:**
- TRAEFIK_DASHBOARD_CREDENTIALS

---

## Конвенции кодирования

### Python Backend
- Используйте async/await для всех операций с БД и внешних запросов
- Pydantic для валидации данных
- SQLAlchemy async session
- JWT для аутентификации
- Structured logging
- CORS настроен на все origins (в development)

### TypeScript Frontend
- App Router (Next.js 15)
- TypeScript strict mode
- Zustand для state management
- Tailwind CSS для стилей
- Framer Motion для анимаций
- Lucide React для иконок

### Общее
- UUID для всех идентификаторов
- JSONB для сложных структур (facilities, fish_types, weather)
- HTTP-only cookies для refresh токенов
- Bearer Authorization header для access токена
- CORS middleware во всех сервисах

---

## Безопасность

### Аутентификация
- JWT access tokens (30 min)
- Refresh tokens (7 days)
- HTTP-only cookies
- bcrypt password hashing

### Авторизация
- RBAC (Role-Based Access Control)
- Проверка владения ресурсами
- Admin endpoints

### Защита данных
- HTTPS в production
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- XSS protection (React)

---

## Логирование и мониторинг

### Структурированное логирование
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "auth-service",
  "message": "User logged in",
  "user_id": "abc-123",
  "ip": "192.168.1.1"
}
```

### Health Checks
Каждый сервис имеет `/health` endpoint:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

---

## Тестирование

### Backend Tests
```bash
pytest services/
```

### Frontend Tests
```bash
npm test
```

---

## Будущие улучшения

1. Event-Driven Architecture (RabbitMQ/Kafka)
2. Database per Service
3. GraphQL Gateway
4. Micro Frontends
5. CI/CD Pipeline
6. Monitoring (Prometheus, Grafana, ELK)
7. Rate Limiting (per-user и per-IP)
8. WebSocket (real-time notifications)

---

## Документация

Основные файлы документации:
- README.md - общая информация
- ARCHITECTURE.md - архитектура
- DEPLOYMENT.md - развертывание
- DOCKER.md - Docker конфигурация
- database/schema.md - схема БД

---

## Быстрая навигация

### Backend Services Structure
```
services/
├── auth-service/           # Аутентификация (Port 8001)
│   ├── app/
│   │   ├── api/v1/        # API роуты
│   │   ├── core/          # Config, security, database
│   │   ├── crud/          # CRUD операции
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── schemas/       # Pydantic схемы
│   │   ├── endpoints/     # Endpoint handlers
│   │   └── main.py        # FastAPI app
│   ├── tests/
│   └── requirements.txt
├── places-service/         # Места (Port 8002)
├── reports-service/        # Отчеты (Port 8003)
├── booking-service/       # Бронирование (Port 8004)
├── shop-service/          # Магазин (Port 8005)
├── email-service/          # Email (Port 8006)
└── shared-utils/          # Общие утилиты
```

### Frontend Structure
```
frontend/
├── app/                    # App Router
├── components/             # Компоненты
├── lib/                    # Утилиты
└── stores/                 # Zustand stores
```

---

## Ключевые паттерны

### CRUD Pattern
Каждый сервис следует стандартному CRUD паттерну:
- `models/` - SQLAlchemy модели БД
- `schemas/` - Pydantic схемы (request/response)
- `crud/` - CRUD операции с БД
- `endpoints/` или `api/v1/` - HTTP endpoints

### API Response Pattern
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Place with id 'abc' not found",
    "details": {}
  }
}
```

### Error Codes
- VALIDATION_ERROR (400)
- UNAUTHORIZED (401)
- FORBIDDEN (403)
- RESOURCE_NOT_FOUND (404)
- CONFLICT (409)
- INTERNAL_ERROR (500)

---

## Заключение

Этот системный промпт содержит полную информацию о платформе для рыбалки, включая архитектуру, технологический стек, структуру сервисов, базу данных, развертывание и конвенции кодирования. Используйте его как справочник при разработке, рефакторинге или расширении функциональности проекта.

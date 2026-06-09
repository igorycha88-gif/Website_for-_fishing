# Places Service

Сервис управления местами для рыбалки в FishMap.

## Технологический стек

- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM (async)
- **PostgreSQL** - база данных
- **Pydantic** - валидация данных
- **Yandex Geocoder API** - геокодирование

## Функциональность

### CRUD операции для мест

- Создание места для рыбалки
- Получение списка мест с фильтрацией
- Получение детальной информации о месте
- Редактирование места
- Удаление места

### Фильтрация и поиск

- Фильтрация по владельцу (owner_id)
- Фильтрация по публичности (is_public)
- Фильтрация по статусу (status)
- Поиск в прямоугольной области (bbox)
- Фильтрация по типам рыб
- Фильтрация по минимальному рейтингу
- Поиск в радиусе от точки (lat, lng, radius)
- Фильтрация по удобствам
- Пагинация и сортировка

### Модерация

- Проверка на запрещенные слова
- Авто-модерация публичных мест
- Ручная модерация администраторами

### Интеграции

- **Auth Service** - проверка токенов и ролей пользователей
- **Yandex Geocoder** - преобразование адреса в координаты и наоборот

## API Endpoints

### Places

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/places` | Создать место | Required |
| GET | `/api/v1/places` | Получить список мест | Optional |
| GET | `/api/v1/places/{id}` | Получить место по ID | Optional |
| PUT | `/api/v1/places/{id}` | Обновить место | Owner |
| DELETE | `/api/v1/places/{id}` | Удалить место | Owner |
| GET | `/api/v1/places/nearby` | Поиск мест рядом | Optional |
| POST | `/api/v1/places/{id}/moderate` | Модерация места | Admin/Moderator |
| GET | `/api/v1/places/{id}/statistics` | Статистика места | Optional |

### Справочники

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/places/fish-types` | Список видов рыб |
| GET | `/api/v1/places/facilities` | Список удобств |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Проверка работоспособности |

## Схемы данных

### Place

```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "title": "string (2-200)",
  "description": "string (10-5000)",
  "latitude": "decimal (-90 to 90)",
  "longitude": "decimal (-180 to 180)",
  "address": "string (max 500)",
  "city": "string (max 100)",
  "region": "string (max 100)",
  "price_per_day": "decimal",
  "max_people": "integer",
  "facilities": ["string"],
  "fish_types": ["string"],
  "images": ["string", "max 5"],
  "rating_avg": "decimal (0-5)",
  "reviews_count": "integer",
  "is_active": "boolean",
  "is_public": "boolean",
  "status": "active | pending_moderation | rejected",
  "visit_date": "ISO 8601",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

### Статусы места

- `active` - активное место
- `pending_moderation` - на модерации
- `rejected` - отклонено модератором

### Типы рыб (30 видов)

Карась, Лещ, Сазан, Щука, Судак, Окунь, Карп, Амур, Толстолобик, Сом, Плотва, Густера, Красноперка, Жерех, Голавль, Форель, Кумжа, Ручьевая форель, Радужная форель, Голец, Налим, Пелядь, Муксун, Сиг, Омуль, Хариус, Умбра, Бычок, Ерш, Другое.

### Удобства (15 видов)

Парковка, Туалет, Душ, WiFi, Электричество, Магазин, Прокат снастей, Аренда лодки, Баня, Мангал, Костровище, Кемпинг, Прокат удочек, Место для чистки рыбы, Холодильник.

## Переменные окружения

```bash
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/fishing_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
YANDEX_MAPS_API_KEY=dfb59053-0011-47fb-a6f1-a14efb9160d1
AUTH_SERVICE_URL=http://auth-service:8001
DEFAULT_LAT=55.7558
DEFAULT_LNG=37.6173
DEFAULT_ZOOM=10
```

## Запуск

### Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Сборка образа
docker build -t places-service .

# Запуск контейнера
docker run -p 8002:8000 --env-file .env places-service
```

### Docker Compose

```bash
docker-compose up places-service
```

## Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=app

# Конкретный тест
pytest tests/test_places.py::test_create_place
```

## Архитектура

```
services/places-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── places.py      # API endpoints
│   │       └── router.py            # Роутер
│   ├── core/
│   │   ├── config.py               # Конфигурация
│   │   ├── constants.py            # Константы (типы рыб, удобства)
│   │   ├── database.py             # Подключение к БД
│   │   └── security.py            # JWT и авторизация
│   ├── crud/
│   │   └── place.py               # CRUD операции
│   ├── models/
│   │   ├── user.py                # Модель User
│   │   ├── place.py               # Модель Place
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── place.py               # Pydantic схемы
│   │   └── __init__.py
│   ├── services/
│   │   └── yandex_geocoder.py     # Яндекс Геокодер
│   ├── main.py                    # FastAPI app
│   └── __init__.py
├── tests/
│   ├── conftest.py
│   └── test_places.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Безопасность

- **JWT токены** - для авторизации запросов
- **Проверка ролей** - admin/moderator для модерации
- **Проверка владения** - пользователи могут редактировать только свои места
- **Валидация данных** - Pydantic схемы
- **Фильтрация запрещенных слов** - для названий и описаний
- **Защита от SQL injection** - SQLAlchemy ORM

## Мониторинг

- **Health check**: `/health`
- **Структурированное логирование**
- **Swagger документация**: `/docs`

## Зависимости

- **fastapi** - веб-фреймворк
- **uvicorn** - ASGI сервер
- **sqlalchemy** - ORM
- **asyncpg** - async PostgreSQL драйвер
- **pydantic** - валидация
- **pydantic-settings** - настройки
- **python-jose** - JWT
- **passlib** - хеширование паролей
- **httpx** - async HTTP клиент
- **pytest** - тестирование
- **pytest-asyncio** - async тесты

## Авторизация

### Получение токена

```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

Response:
{
  "access_token": "jwt_token_here",
  "token_type": "bearer"
}
```

### Использование токена

```bash
curl -H "Authorization: Bearer jwt_token_here" \
  http://localhost:8002/api/v1/places
```

## Лицензия

MIT

# Auth Service

Сервис аутентификации пользователей для Fishing Platform.

## Возможности

- Регистрация пользователей с подтверждением email
- Вход в систему (JWT аутентификация)
- Повторная отправка кода верификации email
- Управление профилем пользователя
- Сброс пароля
- Подтверждение email

## API Эндпоинты

### Аутентификация

#### POST /api/v1/auth/register
Регистрация нового пользователя.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

**Response:**
```json
{
  "message": "Registration successful. Please check your email for verification code."
}
```

#### POST /api/v1/auth/verify-email
Подтверждение email с кодом из письма.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "access_token": "jwt_token_here"
}
```

#### POST /api/v1/auth/resend-verification
Повторная отправка кода подтверждения email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "New verification code sent to your email"
}
```

**Ограничения:**
- Email должен быть зарегистрирован в системе
- Email не должен быть уже подтвержден
- Код действителен 15 минут

#### POST /api/v1/auth/login
Вход в систему.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "jwt_token_here"
}
```

### Сброс пароля

#### POST /api/v1/auth/reset-password/request
Запрос на сброс пароля. Отправляет 6-значный код на email пользователя.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Password reset code sent to your email"
}
```

#### POST /api/v1/auth/reset-password/confirm
Подтверждение сброса пароля с кодом и новым паролем.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "newpassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password reset successful",
  "access_token": "jwt_token_here"
}
```

**Ограничения:**
- Код действителен 15 минут
- Максимум 3 попытки ввода кода
- После успешного сброса пароля пользователь автоматически авторизуется

### Пользователь

#### GET /api/v1/users/me
Получение данных текущего пользователя (требуется авторизация).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "avatar_url": "https://example.com/avatar.jpg",
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### PUT /api/v1/users/me
Обновление профиля пользователя (требуется авторизация).

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "city": "Moscow"
}
```

#### PATCH /api/v1/users/me/password
Изменение пароля (требуется авторизация).

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

#### DELETE /api/v1/users/me
Удаление аккаунта (требуется авторизация).

## Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены истекают через 30 минут
- Коды подтверждения действительны 15 минут
- Максимум 3 попытки ввода кода
- Все sensitive данные хранятся в переменных окружения

## Переменные окружения

```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/db_name
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EMAIL_SERVICE_URL=http://localhost:8005
```

## Запуск

### Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервиса
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Сборка образа
docker build -t auth-service .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env auth-service
```

## Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=app --cov-report=html

# Запуск только unit-тестов
pytest tests/test_password_reset_code_crud.py

# Запуск только интеграционных тестов
pytest tests/test_password_reset_api.py
```

## Структура проекта

```
auth-service/
├── app/
│   ├── api/v1/          # API роутеры
│   ├── core/            # Конфигурация и безопасность
│   ├── crud/            # CRUD операции
│   ├── models/          # SQLAlchemy модели
│   ├── schemas/         # Pydantic схемы
│   ├── endpoints/       # Эндпоинты
│   └── main.py          # Точка входа
├── tests/               # Тесты
│   ├── conftest.py      # Конфигурация тестов
│   ├── test_password_reset_code_crud.py
│   └── test_password_reset_api.py
├── Dockerfile
└── requirements.txt
```

## База данных

Сервис использует следующие таблицы:

- `users` - данные пользователей
- `refresh_tokens` - refresh токены
- `email_verification_codes` - коды подтверждения email
- `password_reset_codes` - коды сброса пароля

Подробнее о схеме базы данных см. `database/schema.md`

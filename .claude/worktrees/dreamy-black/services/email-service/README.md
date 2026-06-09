# Email Service

Сервис для отправки email-уведомлений, включая письма подтверждения регистрации и сброса пароля.

## Обзор

Email Service - это микросервис, отвечающий за отправку email-уведомлений пользователям платформы FishMap. Сервис интегрируется с SMTP сервером Яндекса и предоставляет REST API для генерации кодов подтверждения и отправки писем.

## Возможности

- **Подтверждение email при регистрации**: Отправка писем с кодом подтверждения для новых пользователей
- **Сброс пароля**: Отправка писем с кодом для сброса забытого пароля
- **Разные шаблоны писем**: Отдельные HTML и текстовые шаблоны для каждого типа уведомления
- **Генерация безопасных кодов**: Генерация 6-значных числовых кодов
- **Настройка времени действия**: Конфигурируемое время действия кодов (по умолчанию 15 минут)

## Технологический стек

- **FastAPI** - асинхронный веб-фреймворк
- **aiosmtplib** - SMTP клиент
- **Pydantic** - валидация данных
- **pytest** - тестирование

## Переменные окружения

Следующие переменные окружения должны быть настроены:

```bash
# SMTP настройки
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=FishMapOne
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=FishMapOne@yandex.ru
SMTP_FROM_NAME=FishMap

# Настройки кодов подтверждения
EMAIL_CODE_EXPIRE_MINUTES=15
EMAIL_CODE_LENGTH=6
```

### Настройка SMTP Яндекса

1. Создайте аккаунт на [Яндекс Почта](https://mail.yandex.ru/)
2. Получите пароль приложения:
   - Перейдите в настройки аккаунта
   - Выберите "Безопасность"
   - Создайте новый пароль приложения для почты
3. Настройте переменные окружения

## API Документация

### Эндпоинты

#### 1. Генерация кода подтверждения

Создает новый код подтверждения.

**Запрос:**
```http
POST /api/v1/email/generate-code
```

**Ответ:**
```json
{
  "code": "123456"
}
```

#### 2. Отправка email

Отправляет email с кодом подтверждения. Поддерживает два типа писем: подтверждение регистрации и сброс пароля.

**Запрос:**
```http
POST /api/v1/email/send
Content-Type: application/json

{
  "to_email": "user@example.com",
  "verification_code": "123456",
  "username": "testuser",
  "email_type": "verification"
}
```

**Параметры:**
- `to_email` (string, required): Email получателя
- `verification_code` (string, required): Код подтверждения (6 цифр)
- `username` (string, required): Имя пользователя
- `email_type` (string, required): Тип письма (`verification` или `password_reset`)

**Успешный ответ:**
```json
{
  "success": true,
  "message": "Verification email sent successfully"
}
```

**Ошибка:**
```json
{
  "code": "EMAIL_SEND_FAILED",
  "message": "Failed to send email",
  "details": {}
}
```

## Шаблоны писем

### Письмо подтверждения регистрации

- **Тема**: "Код подтверждения регистрации - FishMap"
- **Содержимое**: Приветствие пользователя, код подтверждения, информация о сроке действия
- **Дизайн**: Синий заголовок (#1a3a52), голубой блок кода (#00b4d8)

### Письмо сброса пароля

- **Тема**: "Код для сброса пароля - FishMap"
- **Содержимое**: Информация о запросе сброса, код подтверждения, предупреждение о безопасности
- **Дизайн**: Оранжево-красный заголовок (#ff6b6b), зеленый блок кода (#2ecc71), желтое предупреждение

## Локальная разработка

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск сервиса

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```

### Запуск тестов

```bash
pytest tests/ -v --cov=app
```

## Использование с Docker

### Сборка образа

```bash
docker build -t email-service .
```

### Запуск с docker-compose

```bash
docker-compose -f docker-compose.dev.yml up email-service
```

## Интеграция с Auth Service

Email Service интегрируется с Auth Service через HTTP API:

1. **При регистрации пользователя**:
   - Auth Service вызывает `/api/v1/email/generate-code` для получения кода
   - Auth Service вызывает `/api/v1/email/send` с `email_type: "verification"`

2. **При сбросе пароля**:
   - Auth Service вызывает `/api/v1/email/generate-code` для получения кода
   - Auth Service вызывает `/api/v1/email/send` с `email_type: "password_reset"`

Пример вызова из Auth Service:

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://email-service:8005/api/v1/email/send",
        json={
            "to_email": "user@example.com",
            "verification_code": "123456",
            "username": "testuser",
            "email_type": "verification"
        },
        timeout=30.0
    )
```

## Тестирование

### Unit-тесты

Покрытие бизнес-логики генерации кодов и создания шаблонов писем.

```bash
pytest tests/test_email_functions.py -v
```

### Интеграционные тесты

Проверка API эндпоинтов и интеграции с SMTP.

```bash
pytest tests/test_email_api.py -v
```

## Структура проекта

```
email-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── router.py       # API роуты
│   ├── core/
│   │   ├── config.py          # Конфигурация
│   │   └── email.py           # Логика отправки писем
│   ├── schemas/
│   │   └── email.py           # Pydantic схемы
│   └── main.py                 # FastAPI приложение
├── tests/
│   ├── conftest.py             # Фикстуры pytest
│   ├── test_email_functions.py # Unit-тесты
│   └── test_email_api.py       # Интеграционные тесты
├── requirements.txt
├── Dockerfile
└── README.md
```

## Безопасность

- Пароли приложений SMTP хранятся в переменных окружения
- Коды подтверждения генерируются криптографически безопасным способом
- Используется TLS для безопасной отправки писем
- Валидация email-адресов с помощью email-validator

## Мониторинг и логирование

Сервис логирует операции отправки писем:

```python
logger.info(f"Email sent to {to_email}, type: {email_type}")
```

Ошибки отправки логируются с деталями исключения.

## Troubleshooting

### Email не отправляется

1. Проверьте настройки SMTP в переменных окружения
2. Убедитесь, что пароль приложения Яндекса корректный
3. Проверьте соединение с SMTP сервером:
   ```bash
   telnet smtp.yandex.ru 465
   ```

### Код не генерируется

1. Проверьте, что сервис запущен и доступен
2. Проверьте логи на наличие ошибок
3. Убедитесь, что все переменные окружения настроены

## Лицензия

© 2024 FishMap. Все права защищены.

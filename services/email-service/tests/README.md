# Тесты Email Service

## Структура

```
services/email-service/tests/
├── __init__.py
├── conftest.py                 # Фикстуры для pytest
├── test_email_functions.py     # Unit тесты функций email
└── test_email_api.py           # API тесты эндпоинтов
```

## Запуск тестов

```bash
cd services/email-service
pip install -r requirements.txt
pytest -v
```

## Покрытие

### test_email_functions.py
- ✅ Генерация кода подтверждения (длина, уникальность, диапазон)
- ✅ Отправка email успешно
- ✅ Отправка email при ошибке SMTP
- ✅ Проверка HTML содержимого email

### test_email_api.py
- ✅ Health check
- ✅ Генерация кода (API)
- ✅ Отправка email (API) успешно
- ✅ Отправка email (API) при ошибке
- ✅ Валидация email адреса

## Интеграционные тесты с Auth Service

См. `services/auth-service/tests/test_auth_email_integration.py`
- ✅ Регистрация с успешной отправкой email
- ✅ Регистрация при недоступности Email Service
- ✅ Регистрация при ошибке отправки email
- ✅ Подтверждение email с валидным кодом
- ✅ Подтверждение email с невалидным кодом

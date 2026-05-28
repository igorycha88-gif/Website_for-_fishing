# Управление секретами (HashiCorp Vault)

## Обзор

Проект использует HashiCorp Vault для централизованного управления секретами. Это обеспечивает:
- Безопасное хранение секретов вне кода
- Автоматическую ротацию секретов
- Аудит доступа к секретам
- AppRole аутентификацию для сервисов

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                      │
│                                                              │
│  ┌─────────┐    ┌─────────────────────────────────────────┐ │
│  │  Vault  │◄───│         Microservices                    │ │
│  │ :8200   │    │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │ │
│  └─────────┘    │  │  Auth   │ │  Email  │ │ Forecast│    │ │
│       │         │  │ Service │ │ Service │ │ Service │    │ │
│       ▼         │  └─────────┘ └─────────┘ └─────────┘    │ │
│  ┌─────────┐    │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │ │
│  │  Init   │    │  │ Places  │ │ Reports │ │ Booking │    │ │
│  │  Job    │    │  │ Service │ │ Service │ │ Service │    │ │
│  └─────────┘    │  └─────────┘ └─────────┘ └─────────┘    │ │
│                 └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Запуск Vault

### Development режим

```bash
# Запуск всех сервисов с Vault
docker-compose -f docker-compose.dev.yml up -d

# Vault запустится в dev mode с root token: dev-root-token
# Инициализация произойдет автоматически через vault-init container
```

### Проверка статуса Vault

```bash
# Health check
curl http://localhost:8200/v1/sys/health

# Проверка инициализации
docker exec -it $(docker ps -q -f name=vault) vault status
```

## Структура секретов

| Путь | Описание | Ротация |
|------|----------|---------|
| `secret/data/fishmap/auth/jwt` | JWT secret key | 90 дней |
| `secret/data/fishmap/database/postgres` | PostgreSQL password | 90 дней |
| `secret/data/fishmap/email/smtp` | SMTP password | Уведомление |
| `secret/data/fishmap/payment/stripe` | Stripe keys | Уведомление |
| `secret/data/fishmap/storage/cloudinary` | Cloudinary secret | Уведомление |
| `secret/data/fishmap/external/weather` | OpenWeatherMap API key | Уведомление |
| `secret/data/fishmap/external/mapbox` | Mapbox API key | Уведомление |

## AppRole аутентификация

Каждый сервис имеет свою AppRole с ограниченными правами:

| Сервис | Policy | Доступ |
|--------|--------|--------|
| auth-service | auth-service | JWT, Database |
| email-service | email-service | SMTP, Database |
| forecast-service | forecast-service | Weather API, Database |
| places-service | places-service | Mapbox, JWT, Database |
| reports-service | reports-service | Cloudinary, Database |
| booking-service | booking-service | Stripe, JWT, Database |
| shop-service | shop-service | Stripe, JWT, Database |

### Получение Role ID и Secret ID

```bash
# После запуска vault-init, проверьте логи
docker logs $(docker ps -q -f name=vault-init)

# Вывод будет содержать Role ID и Secret ID для каждого сервиса
```

## Использование в сервисах

### Конфигурация environment переменных

```yaml
# docker-compose.yml
services:
  auth-service:
    environment:
      USE_VAULT: "true"
      VAULT_ADDR: "http://vault:8200"
      VAULT_ROLE_ID: ${AUTH_VAULT_ROLE_ID}
      VAULT_SECRET_ID: ${AUTH_VAULT_SECRET_ID}
```

### Код Python

```python
from vault_client import get_vault_client

# Получение клиента
vault = get_vault_client()

# Получение секрета
jwt_secret = vault.get_jwt_secret()
username, password = vault.get_database_credentials()
```

### Fallback механизм

Если Vault недоступен, сервисы используют переменные окружения:

```python
# В config.py
class Settings(BaseSettings):
    USE_VAULT: bool = False  # Отключить Vault
    SECRET_KEY: str = ""     # Fallback из .env
    
    def load_secrets_from_vault(self):
        if not self.USE_VAULT:
            return  # Использовать .env
        # ... загрузка из Vault
```

## Ручное управление секретами

### Запись секрета

```bash
# Войти в контейнер Vault
docker exec -it $(docker ps -q -f name=vault) sh

# Установить переменные
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='dev-root-token'

# Записать секрет
vault kv put secret/fishmap/auth/jwt secret_key="new-secret-key-here"
```

### Чтение секрета

```bash
# Читать секрет
vault kv get secret/fishmap/auth/jwt

# Читать конкретное поле
vault kv get -field=secret_key secret/fishmap/auth/jwt
```

### Создание новой AppRole

```bash
# Создать policy
vault policy write my-service vault/policies/my-service.hcl

# Создать AppRole
vault write auth/approle/role/my-service \
    token_policies=my-service \
    token_ttl=1h \
    token_max_ttl=4h

# Получить Role ID
vault read auth/approle/role/my-service/role-id

# Создать Secret ID
vault write -field=secret_id -f auth/approle/role/my-service/secret-id
```

## Policies

Policies находятся в `vault/policies/`:

```hcl
# Пример: vault/policies/auth-service.hcl
path "secret/data/fishmap/auth/*" {
  capabilities = ["read"]
}

path "secret/data/fishmap/database/postgres" {
  capabilities = ["read"]
}
```

## Инициализация

Скрипт `vault/init.sh` автоматически:
1. Ожидает запуска Vault
2. Включает KV secrets engine
3. Создает секреты из .env
4. Создает policies
5. Включает AppRole auth
6. Создает AppRoles для всех сервисов

## Ротация секретов

### Автоматическая ротация (SECRET_KEY, DATABASE_PASSWORD)

```bash
# В production настроен rotation job
# Для ручной ротации:
vault kv put secret/fishmap/auth/jwt secret_key="$(openssl rand -base64 32)"
```

### Уведомления для внешних API

Для внешних ключей (SMTP, Stripe, etc.) отправляются уведомления:
- На email администратора
- За 14 дней до истечения 90-дневного периода

## Безопасность

### Development режим
- Root token: `dev-root-token` (только для разработки!)
- Не использовать в production

### Production требования
1. Отключить dev mode
2. Использовать TLS
3. Настроить unseal keys (Shamir)
4. Включить audit logging
5. Настроить backup

### Audit логи

```bash
# Включить audit логирование
vault audit enable file file_path=/vault/audit/audit.log

# Просмотр логов
docker exec $(docker ps -q -f name=vault) cat /vault/audit/audit.log
```

## Troubleshooting

### Vault недоступен

```bash
# Проверить статус
docker-compose -f docker-compose.dev.yml logs vault

# Перезапустить
docker-compose -f docker-compose.dev.yml restart vault vault-init
```

### Ошибка аутентификации

```bash
# Проверить Role ID / Secret ID
docker exec -it $(docker ps -q -f name=vault) vault read auth/approle/role/auth-service/role-id

# Пересоздать Secret ID
docker exec -it $(docker ps -q -f name=vault) vault write -field=secret_id -f auth/approle/role/auth-service/secret-id
```

### Секрет не найден

```bash
# Проверить путь
docker exec -it $(docker ps -q -f name=vault) vault kv list secret/fishmap/

# Проверить policy
docker exec -it $(docker ps -q -f name=vault) vault policy read auth-service
```

## Rollback план

### Откат к .env

```bash
# В .env установить
USE_VAULT=false

# Перезапустить сервисы
docker-compose -f docker-compose.dev.yml up -d
```

### Экстренное восстановление

1. Остановить Vault: `docker-compose -f docker-compose.dev.yml stop vault`
2. Установить `USE_VAULT=false` для всех сервисов
3. Перезапустить: `docker-compose -f docker-compose.dev.yml up -d`

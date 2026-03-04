# Fishing Platform - Docker Deployment

Инструкции по сборке и запуску Docker образов.

## 🐳 Быстрый старт

### Makefile команды

```bash
# Показать все команды
make help

# Development
make dev           # Собрать и запустить все сервисы
make dev-build     # Собрать все сервисы
make dev-up        # Запустить все сервисы
make dev-down      # Остановить все сервисы
make dev-logs      # Логи всех сервисов
make dev-logs S=auth-service  # Логи конкретного сервиса
make dev-restart   # Перезапустить все сервисы

# Health & Status
make health        # Проверить здоровье всех сервисов
make status        # Статус контейнеров

# Testing
make pytest        # Запустить тесты auth-service
make pytest S=email-service  # Тесты конкретного сервиса

# ELK Stack
make elk           # Запустить ELK + development
make elk-up        # Запустить только ELK
make elk-down      # Остановить ELK

# Cleanup
make clean         # Удалить контейнеры и volumes
make clean-all     # Полная очистка + docker prune
make clean-images  # Удалить все образы проекта
```

### Сборка и запуск

```bash
# Собрать образ
make build

# Запустить контейнеры
make up

# Или одной командой
make build-dev
```

### Управление

```bash
# Остановить
make dev-down

# Перезапустить
make dev-restart

# Посмотреть логи
make dev-logs

# Посмотреть логи конкретного сервиса
make dev-logs S=auth-service

# Очистить всё
make clean-all
```

## 📦 Ручные команды Docker

### Сборка образа

```bash
# Frontend only
docker-compose -f docker-compose.frontend.yml build

# All services (development)
docker-compose -f docker-compose.dev.yml build
```

### Запуск контейнеров

```bash
# Local development (all services)
docker-compose -f docker-compose.dev.yml up -d

# Frontend only
docker-compose -f docker-compose.frontend.yml up -d
```

### Остановка

```bash
docker-compose -f docker-compose.dev.yml down
```

## 🔗 Доступ к сервисам

### Локальная разработка (docker-compose.dev.yml)

| Сервис        | Порт хоста | Порт контейнера |
|---------------|------------|----------------|
| Frontend      | 3000       | 3000           |
| Auth Service  | 8001       | 8000           |
| Places Service | 8002       | 8001           |
| Reports Service| 8003       | 8002           |
| Booking Service| 8004       | 8003           |
| Shop Service  | 8005       | 8004           |
| Email Service | 8006       | 8005           |
| PostgreSQL    | 5432       | 5432           |
| Redis         | -          | 6379           |

### Production (Docker Swarm)

- **Фронтенд**: http://localhost
- **Traefik Dashboard**: http://localhost:8080
- **API**: http://localhost/api/v1/ (через Traefik)

**Примечание**: В локальной разработке Next.js использует rewrites для проксирования API запросов к микросервисам через их порты хоста. В production Traefik обрабатывает маршрутизацию.

## 🛠️ Локальная разработка

Для разработки без Docker:

```bash
# Backend
cd services/auth-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📝 Конфигурация

Файлы конфигурации:

- `docker-compose.yml` - Production конфиг (Docker Swarm)
- `docker-compose.dev.yml` - Локальная разработка
- `docker-compose.frontend.yml` - Только фронтенд
- `docker-compose.elk.yml` - ELK Stack (Elasticsearch, Logstash, Kibana)
- `services/*/Dockerfile` - Dockerfile для backend сервисов (мультистейдж, non-root)
- `services/*/.dockerignore` - Исключения из образа
- `frontend/Dockerfile` - Dockerfile для Next.js
- `frontend/next.config.js` - Конфигурация Next.js с rewrites
- `frontend/.dockerignore` - Исключения из образа
- `Makefile` - Упрощённые команды

## 🚀 Оптимизация образа

### Frontend (Next.js)
Docker использует мультистейдж сборку:
1. **deps** - Установка зависимостей
2. **builder** - Сборка приложения
3. **runner** - Production runtime

Размер оптимизированного образа: ~150MB

### Backend (FastAPI)
С версии 1.0.0 backend сервисы используют мультистейдж сборку:

1. **builder** - Установка зависимостей через uv
2. **runtime** - Минимальный runtime образ

**Особенности Dockerfile для backend:**
- Non-root пользователь (`appuser:appgroup`) для безопасности
- Healthcheck на основе Python urllib (без curl)
- LABEL метаданные для идентификации
- .dockerignore для исключения лишних файлов

**Размер образа:** ~400MB (vs ~600MB до оптимизации)

### Размеры образов (Phase 2)

| Сервис | Размер | Пользователь | Healthcheck |
|--------|--------|--------------|-------------|
| auth-service | 403MB | appuser | ✅ |
| email-service | 301MB | appuser | ✅ |
| places-service | 377MB | appuser | ✅ |
| reports-service | 367MB | appuser | ✅ |
| booking-service | 379MB | appuser | ✅ |
| shop-service | 379MB | appuser | ✅ |
| frontend | 260MB | node | ✅ |

**Итого:** Все backend сервисы используют мультистейдж сборку с non-root пользователем.

### Структура Dockerfile (auth-service пример)
```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime
LABEL org.opencontainers.image.title="FishMap Auth Service"
WORKDIR /app

# Non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages ...
COPY --chown=appuser:appgroup . .

USER appuser
ENV PORT=8000
EXPOSE $PORT

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s \
    CMD python -c "import urllib.request; ..." || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 Troubleshooting

### Проблема с портами

Если порт занят, измените в `docker-compose.dev.yml`:

```yaml
ports:
  - "3001:3000"  # Используйте другой порт
```

### Проблемы с авторизацией

Если авторизация не работает в локальной разработке:

1. Проверьте, что все сервисы запущены: `docker-compose -f docker-compose.dev.yml ps`
2. Проверьте health checks: `curl http://localhost:8001/health`
3. Убедитесь, что NEXT_PUBLIC_API_URL в frontend/.env.local установлен на http://localhost:3000
4. Проверьте rewrites в frontend/next.config.js

### Очистка кэша Docker

```bash
docker system prune -a
```

### Пересборка без кэша

```bash
docker-compose -f docker-compose.dev.yml build --no-cache
```

## 📊 Мониторинг

### ELK Stack для логирования

ELK Stack (Elasticsearch, Logstash, Kibana) интегрирован для централизованного логирования:

```bash
# Запуск ELK Stack
docker-compose -f docker-compose.elk.yml up -d

# Доступ к Kibana
http://localhost:5601

# Создание index pattern: fishmap-logs-*
# Поле времени: @timestamp
```

**Важно:** Все ELK сервисы используют сеть `fishing-network` для связи с микросервисами.

| Сервис | Порт | Назначение |
|--------|------|------------|
| Elasticsearch | 9200 | Хранение логов |
| Logstash | 5000 | Прием логов от сервисов |
| Kibana | 5601 | Визуализация логов |

### Команды мониторинга

```bash
# Статус контейнеров
docker-compose -f docker-compose.dev.yml ps

# Использование ресурсов
docker stats

# Логи конкретного сервиса
docker-compose -f docker-compose.dev.yml logs -f auth-service

# Проверка healthcheck
curl http://localhost:8001/health
```

## 🌐 Production (Docker Swarm)

### Требования

- Docker Swarm инициализирован
- Домен с DNS записями
- Email для Let's Encrypt

### Шаг 1: Инициализация Swarm

```bash
# На manager node
docker swarm init

# Добавить worker nodes (если нужно)
docker swarm join-token worker
```

### Шаг 2: Управление секретами

```bash
# Генерация секретов
make secrets-generate

# Создание Docker Swarm секретов
make secrets-create

# Проверка
make secrets-list
```

**Список секретов:**
| Секрет | Описание |
|--------|----------|
| secret_key | JWT secret key |
| postgres_password | PostgreSQL password |
| smtp_password | SMTP password |
| stripe_secret_key | Stripe API key |
| stripe_webhook_secret | Stripe webhook secret |
| cloudinary_api_secret | Cloudinary secret |

### Шаг 3: Настройка переменных

Создайте `.env.production`:
```bash
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com
POSTGRES_USER=postgres
POSTGRES_DB=fishing_db
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=your-email@yandex.ru
SMTP_FROM_EMAIL=your-email@yandex.ru
YANDEX_MAPS_API_KEY=your-key
STRIPE_PUBLISHABLE_KEY=your-key
```

### Шаг 4: Деплой

```bash
# Deploy stack
make prod-deploy

# Проверка статуса
make prod-ps

# Логи
make prod-logs
```

### Шаг 5: Проверка

```bash
# HTTP -> HTTPS редирект
curl -I http://your-domain.com

# Health check
curl https://your-domain.com/api/v1/auth/health
```

### Makefile команды для Production

```bash
make prod-deploy    # Деплой в Swarm
make prod-ps        # Статус сервисов
make prod-logs      # Логи
make prod-rollback  # Откат
```

### HTTPS / Let's Encrypt

Traefik автоматически получает SSL сертификаты:
- ACME HTTP challenge через entrypoint `web`
- Сертификаты хранятся в volume `traefik_letsencrypt`
- Автоматическое обновление

### Отказоустойчивость

| Сервис | Реплики |
|--------|---------|
| traefik | 1 |
| postgres | 1 |
| redis | 1 |
| auth-service | 2 |
| email-service | 1 |
| places-service | 2 |
| reports-service | 2 |
| booking-service | 2 |
| shop-service | 2 |
| frontend | 2 |

## ⚙️ Docker Compose Best Practices (Phase 3)

### Resource Limits

Все сервисы имеют ограничения ресурсов:

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

| Сервис | CPU Limit | Memory Limit |
|--------|-----------|--------------|
| postgres | 1 | 512M |
| redis | 0.5 | 128M |
| backend services | 1 | 512M |
| frontend | 1 | 512M |

### Logging с ротацией

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service"
```

**Параметры:**
- `max-size: 10m` - максимальный размер файла лога
- `max-file: 3` - количество файлов до ротации
- `labels: service` - метка для фильтрации

### Restart Policy

```yaml
restart: unless-stopped
```

- Автоматический перезапуск при падении
- Не перезапускается после явной остановки

### Healthcheck Dependencies

Сервисы ждут готовности зависимостей:

```yaml
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

**Healthcheck для инфраструктуры:**
- PostgreSQL: `pg_isready -U postgres`
- Redis: `redis-cli ping`

### YAML Anchors

Для устранения дублирования используются YAML anchors:

```yaml
x-logging: &logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

services:
  auth-service:
    logging: *logging
```

# Fishing Platform - Docker Deployment

Инструкции по сборке и запуску Docker образов.

## 🐳 Быстрый старт

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
make down

# Перезапустить
make restart

# Посмотреть логи
make logs

# Очистить всё
make clean
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
- `frontend/Dockerfile` - Dockerfile для Next.js
- `frontend/next.config.js` - Конфигурация Next.js с rewrites
- `frontend/.dockerignore` - Исключения из образа
- `Makefile` - Упрощённые команды

## 🚀 Оптимизация образа

Docker использует мультистейдж сборку:

1. **deps** - Установка зависимостей
2. **builder** - Сборка приложения
3. **runner** - Production runtime

Размер оптимизированного образа: ~150MB

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

```bash
# Статус контейнеров
docker-compose -f docker-compose.dev.yml ps

# Использование ресурсов
docker stats

# Логи конкретного сервиса
docker-compose -f docker-compose.dev.yml logs -f frontend
```

## 🌐 Prod окружение

Для продакшена добавьте:

1. Настройте Traefik для HTTPS
2. Добавьте переменные окружения в `.env`
3. Настройте логирование (ELK, Loki и т.д.)
4. Добавьте healthchecks
5. Настройте репликацию сервисов

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
docker-compose -f docker-compose.frontend.yml build
```

### Запуск контейнеров

```bash
# В фоне
docker-compose -f docker-compose.frontend.yml up -d

# С логами
docker-compose -f docker-compose.frontend.yml up
```

### Остановка

```bash
docker-compose -f docker-compose.frontend.yml down
```

 ## 🔗 Доступ к сервисам

 После запуска:

### Development (docker-compose.dev.yml)
 - **Фронтенд**: http://localhost:3000
 - **Auth Service**: http://localhost:8001
 - **Places Service**: http://localhost:8002
 - **Reports Service**: http://localhost:8003
 - **Booking Service**: http://localhost:8004
 - **Shop Service**: http://localhost:8005
 - **Email Service**: http://localhost:8006
 - **PostgreSQL**: localhost:5432
 - **Redis**: localhost:6379

### Production (docker-compose.yml with Docker Swarm)
 - **Фронтенд**: http://localhost
 - **Traefik Dashboard**: http://localhost:8080
 - **API**: http://localhost/api/v1/

### API Proxy
В режиме разработки Next.js автоматически проксирует API запросы к соответствующим backend сервисам через Next.js rewrites:
- Все запросы к `/api/v1/*` автоматически перенаправляются на соответствующие сервисы
- Фронтенд использует относительные пути для API запросов
- Конфигурация проксирования находится в `frontend/next.config.js`

## 🛠️ Локальная разработка

Для разработки без Docker:

```bash
cd frontend
npm install
npm run dev
```

## 📝 Конфигурация

Файлы конфигурации:

- `docker-compose.frontend.yml` - Docker Compose конфиг
- `frontend/Dockerfile` - Dockerfile для Next.js
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

Если порт 3000 занят, измените в `docker-compose.frontend.yml`:

```yaml
ports:
  - "3001:3000"  # Используйте другой порт
```

### Очистка кэша Docker

```bash
docker system prune -a
```

### Пересборка без кэша

```bash
docker-compose -f docker-compose.frontend.yml build --no-cache
```

## 📊 Мониторинг

```bash
# Статус контейнеров
docker-compose -f docker-compose.frontend.yml ps

# Использование ресурсов
docker stats
```

## 🌐 Prod окружение

Для продакшена добавьте:

1. Настройте Traefik для HTTPS
2. Добавьте переменные окружения в `.env`
3. Настройте логирование (ELK, Loki и т.д.)
4. Добавьте healthchecks

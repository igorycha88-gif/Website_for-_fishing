# Скилл AI-DevOps: Продакшн-деплой FishMap на VPS

## 1. Роль

Ты — Production DevOps-инженер платформы FishMap. Отвечаешь за деплой, доступность, мониторинг и откаты всех микросервисов на VPS-сервере. Включаешься в конвейер `PIPELINE_PROD.js` после успешного тестирования (GO от Тестировщика) или напрямую от Аналитика для инфраструктурных задач.

**Ключевые принципы:**

1. **ПОЛНАЯ пересборка ВСЕХ сервисов** — частичные пересборки запрещены
2. **Автоматизация** — параметры определяются автоматически, без вопросов пользователю
3. **Безопасность** — бэкап БД перед каждым деплоем, healthcheck всех сервисов
4. **Версионирование** — каждый деплой = новая версия (semver), git tag обязателен
5. **Откат** — при ошибке не перезапускать автоматически, вывести диагностику

---

## 2. Ключевые отличия от Dev-деплоя

| Параметр | Dev (`docker-compose.dev.yml`) | Prod (`docker-compose.vps.yml` / `docker-compose.vps-host.yml`) |
|----------|------|------|
| **Compose-файл** | `docker-compose.dev.yml` | `docker-compose.vps-host.yml` (host network) |
| **Env-файл** | `.env` | `.env.vps` |
| **Сеть** | `fishing-network` (bridge) | `host` (все на `127.0.0.1`) |
| **Порт Frontend** | 3000 | 3080 |
| **Порт Auth** | 8001 | 8001 |
| **Порт Places** | 8002 | 8002 |
| **Порт Reports** | 8003 | 8003 |
| **Порт Booking** | 8004 | 8004 |
| **Порт Shop** | 8005 | 8005 |
| **Порт Email** | 8006 | 8006 |
| **Порт Forecast** | 8007 | 8007 |
| **Reverse Proxy** | Нет | nginx (SmartTraffic) |
| **SSL/HTTPS** | Нет | Через nginx (Let's Encrypt) |
| **Логирование** | stdout | json-file (max 10m × 3 files) |
| **Рестарт** | no | `unless-stopped` |
| **ENVIRONMENT** | `development` | `production` |
| **Memory limits** | Нет | Да (80–256 MB на сервис) |
| **Бэкап БД** | Нет | Обязателен перед деплоем |
| **Версионирование** | Нет | VERSION файл + git tag |
| **Миграции** | Через docker-entrypoint-initdb | Через docker-entrypoint-initdb + ручные при необходимости |
| **Setup-скрипт** | Нет | `deploy/vps/setup-vps.sh` |

---

## 3. Архитектура VPS (ASCII-схема)

```
                        ┌─────────────────── Интернет ───────────────────┐
                        │                                                  │
                        ▼                                                  │
              ┌──────────────────┐                                         │
              │   SmartTraffic   │                                         │
              │   nginx (80/443) │                                         │
              │   SSL termination│                                         │
              └────────┬─────────┘                                         │
                       │ proxy_pass http://host.docker.internal:3080       │
                       │                                                   │
                       ▼                                                   │
    ┌──────────────────────────────────────────────────────────────────────┤
    │                        VPS (host network)                           │
    │                                                                     │
    │  ┌─────────────┐                                                    │
    │  │  Frontend   │  Next.js 15 · port 3080                           │
    │  │  (Node.js)  │  /api/health                                       │
    │  └──────┬──────┘                                                    │
    │         │ HTTP (127.0.0.1)                                           │
    │         │                                                            │
    │    ┌────┴────────────────────────────────────────┐                  │
    │    │                                             │                  │
    │    ▼                ▼          ▼          ▼       ▼                  │
    │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐       │
    │  │ Auth │  │Places│  │Email │  │Fore- │  │Reprt │  │Shop  │       │
    │  │ 8001 │  │ 8002 │  │ 8006 │  │cast  │  │ 8003 │  │ 8005 │       │
    │  │      │  │      │  │      │  │ 8007 │  │      │  │      │       │
    │  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘       │
    │     │         │         │         │         │         │            │
    │     │    ┌────┴─────────┴─────────┴─────────┘         │            │
    │     │    │                                              │            │
    │     ▼    ▼                                              ▼            │
    │  ┌──────────────┐                              ┌──────────┐        │
    │  │  PostgreSQL  │                              │  Redis   │        │
    │  │  16-alpine   │                              │ 7-alpine │        │
    │  │  127.0.0.1   │                              │127.0.0.1 │        │
    │  │  :5432       │                              │ :6379    │        │
    │  └──────────────┘                              └──────────┘        │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  Logging (опционально)                                              │
    │  docker-compose.elk.yml → Elasticsearch + Logstash + Kibana        │
    │  Kibana: http://localhost:5601                                      │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Переменные окружения (.env.vps)

Файл: `.env.vps` (шаблон: `.env.vps.example`). **Никогда не коммитить!**

### Обязательные переменные

```bash
# === Database ===
POSTGRES_DB=fishing_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<STRONG_PASSWORD_MIN_20_CHARS>

# === Auth Service ===
SECRET_KEY=<RANDOM_STRING_MIN_32_CHARS>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# === SMTP (Email Service) ===
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USER=<your_email@yandex.ru>
SMTP_PASSWORD=<smtp_app_password>
SMTP_FROM_EMAIL=<your_email@yandex.ru>
SMTP_FROM_NAME=FishMap

# === Email Service ===
ENABLE_EMAIL_SENDING=true
EMAIL_CODE_EXPIRE_MINUTES=15
EMAIL_SERVICE_API_KEY=<RANDOM_API_KEY_MIN_32_CHARS>

# === Forecast Service ===
OPENWEATHERMAP_API_KEY=<your_openweathermap_api_key>

# === Frontend ===
NEXT_PUBLIC_API_URL=http://<FISHMAP_DOMAIN_OR_IP>
YANDEX_MAPS_API_KEY=<your_yandex_maps_api_key>
STRIPE_PUBLISHABLE_KEY=

# === Logging ===
LOG_LEVEL=INFO

# === Domain (nginx config) ===
FISHMAP_DOMAIN=yourdomain.ru
```

### Проверка env перед деплоем

```bash
# Проверить что .env.vps существует и заполнен
[ -f .env.vps ] && echo "OK" || echo "MISSING: .env.vps"

# Проверить обязательные переменные (не содержат CHANGE_ME)
grep -c "CHANGE_ME" .env.vps && echo "ERROR: unfilled variables" || echo "OK"
```

---

## 5. Docker-образы

### Стратегия сборки

Все образы собираются **на VPS** из исходного кода (нет внешнего registry).

```bash
# Полная пересборка всех образов
docker compose -f docker-compose.vps-host.yml build --no-cache

# Пересборка конкретного сервиса (ТОЛЬКО для отладки, не для деплоя)
docker compose -f docker-compose.vps-host.yml build --no-cache auth-service
```

### Backend (FastAPI, Python 3.12)

Каждый сервис: `services/<service-name>/Dockerfile`

```
Stage 1 (builder):    pip install requirements.txt
Stage 2 (runtime):    копирование пакетов + код, non-root user
Healthcheck:          python -c "...urlopen('http://localhost:PORT/health')"
Command:              uvicorn app.main:app --host 127.0.0.1 --port XXXX
```

### Frontend (Next.js 15)

`frontend/Dockerfile`

```
Stage 1 (deps):       npm install
Stage 2 (builder):    npm run build (с NEXT_PUBLIC_* build args)
Stage 3 (runner):     standalone output, non-root user
Healthcheck:          HTTP GET / (или /api/health)
Command:              node server.js
```

### Build args (frontend)

```bash
NEXT_PUBLIC_YANDEX_MAPS_API_KEY=${YANDEX_MAPS_API_KEY}
NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY}
```

---

## 6. Версионирование

Подробно: `VERSIONING.md`

### Semver-правила

| Тип | Когда | Пример | Версия |
|------|-------|--------|--------|
| **patch** | Баг-фиксы, мелкие правки | `fix: валидация координат` | 0.4.1 → 0.4.2 |
| **minor** | Новый функционал | `feat: модуль бронирования` | 0.4.1 → 0.5.0 |
| **major** | Breaking changes | `feat!: новая авторизация` | 0.4.1 → 1.0.0 |

### Команды версионирования

```bash
# Текущая версия
cat VERSION

# Определить тип изменений
git log v$(cat VERSION)..HEAD --oneline

# Обновить версию (пример: patch)
echo "0.4.2" > VERSION

# Обновить CHANGELOG
# (см. VERSIONING.md → CHANGELOG.md формат)

# Закоммитить и тегировать
git add VERSION CHANGELOG.md
git commit -m "chore: release v$(cat VERSION)"
git tag -a "v$(cat VERSION)" -m "Release v$(cat VERSION): $(date +%Y-%m-%d)"
git push --follow-tags
```

### Версия в healthcheck

Каждый backend-сервис возвращает версию в `/health`:

```json
{
  "status": "ok",
  "service": "auth-service",
  "version": "0.4.2"
}
```

```bash
# Проверить версию сервиса на проде
curl -s http://127.0.0.1:8001/health | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])"
```

---

## 7. Полное тестирование на проде

### 7.1. Автоматизированные API-тесты

Выполняются DevOps после деплоя. Скрипт проверяет все healthcheck-эндпоинты и ключевые API.

```bash
#!/bin/bash
# post-deploy-api-test.sh — запускать на VPS после деплоя

set -euo pipefail

PASS=0
FAIL=0

check() {
    local name="$1" url="$2" expected="${3:-200}"
    local status
    status=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null) || status="000"
    if [ "$status" = "$expected" ]; then
        echo "  ✅ $name ($url) → $status"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $name ($url) → $status (expected $expected)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== FishMap Post-Deploy API Tests ==="
echo ""

echo "--- Infrastructure ---"
check "PostgreSQL" "http://127.0.0.1:8001/health"
check "Redis"      "http://127.0.0.1:8001/health"

echo ""
echo "--- Backend Services ---"
check "Auth"      "http://127.0.0.1:8001/health"
check "Email"     "http://127.0.0.1:8006/health"
check "Forecast"  "http://127.0.0.1:8007/health"

echo ""
echo "--- Frontend ---"
check "Frontend"     "http://127.0.0.1:3080"
check "Frontend API" "http://127.0.0.1:3080/api/health"

echo ""
echo "--- Auth API (functional) ---"
check "Auth: register OPTIONS" "http://127.0.0.1:8001/api/v1/auth/register" "405"
check "Auth: login OPTIONS"    "http://127.0.0.1:8001/api/v1/auth/login"    "405"

echo ""
echo "--- External (nginx) ---"
DOMAIN=$(grep FISHMAP_DOMAIN .env.vps 2>/dev/null | cut -d= -f2 || echo "")
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "yourdomain.ru" ]; then
    check "nginx → Frontend" "http://$DOMAIN"
else
    echo "  ⏭️  nginx test skipped (no domain configured)"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
```

### 7.2. Ручной E2E-чеклист для пользователя

После автоматизированных тестов — попросить пользователя проверить:

```
### Ручной E2E-чеклист (пользователь)

1. [ ] Главная страница открывается: http://<DOMAIN>
2. [ ] Регистрация нового пользователя работает
3. [ ] Логин с существующим пользователем работает
4. [ ] Страница карты загружается (Яндекс.Карты)
5. [ ] Прогноз погоды отображается на странице прогноза
6. [ ] Email-подтверждение приходит (если ENABLE_EMAIL_SENDING=true)
7. [ ] Навигация между страницами работает (все ссылки кликабельны)
8. [ ] Мобильная версия корректна (responsive)
9. [ ] Выход из аккаунта работает
10. [ ] Нет ошибок в DevTools Console (F12)
```

---

## 8. Команды продакшн-деплоя

### Compose-файл для продакшна

```bash
COMPOSE_FILE="docker-compose.vps-host.yml"
ENV_FILE=".env.vps"
```

### 8.1. Preflight (предполётная проверка)

```bash
# Проверить что мы на VPS
[ -f .env.vps ] || { echo "ERROR: .env.vps not found"; exit 1; }

# Проверить заполненность переменных
grep -c "CHANGE_ME" .env.vps && { echo "ERROR: unfilled variables in .env.vps"; exit 1; } || true

# Проверить Docker
docker info >/dev/null 2>&1 || { echo "ERROR: Docker not running"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: Docker Compose not available"; exit 1; }

# Проверить свободное место на диске (минимум 2 GB)
AVAIL=$(df -h / | tail -1 | awk '{print $4}' | sed 's/G//')
[ "$(echo "$AVAIL > 2" | bc 2>/dev/null || echo 0)" -eq 1 ] || echo "WARN: low disk space (${AVAIL}G available)"

# Проверить git status (нет ли незакоммиченных изменений)
git status --porcelain | head -5
```

### 8.2. Backup (бэкап БД)

```bash
# Создать директорию для бэкапов
mkdir -p /opt/fishmap/backups

# Бэкап PostgreSQL
docker exec $(docker ps -q -f name=postgres) \
    pg_dump -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-fishing_db}" \
    | gzip > "/opt/fishmap/backups/fishing_db_$(date +%Y%m%d_%H%M%S).sql.gz"

# Проверить бэкап
ls -lh /opt/fishmap/backups/ | tail -3

# Бэкап Redis (опционально)
docker exec $(docker ps -q -f name=redis) redis-cli BGSAVE
```

### 8.3. Build (полная пересборка)

```bash
# Загрузить свежий код
git pull origin main

# Полная пересборка ВСЕХ образов (без кеша)
docker compose -f docker-compose.vps-host.yml --env-file .env.vps build --no-cache

# Ожидаемое время: 3-7 минут на VPS
```

### 8.4. Deploy (запуск контейнеров)

```bash
# Остановить текущие контейнеры
docker compose -f docker-compose.vps-host.yml --env-file .env.vps down

# Запустить все сервисы с пересозданием
docker compose -f docker-compose.vps-host.yml --env-file .env.vps up -d --force-recreate
```

### 8.5. Verify (проверка healthcheck)

```bash
# Ожидание healthcheck (максимум 180 сек для продакшна)
echo "Waiting for all services to become healthy..."
ELAPSED=0
while [ $ELAPSED -lt 180 ]; do
    UNHEALTHY=$(docker compose -f docker-compose.vps-host.yml ps --format json 2>/dev/null \
        | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    h = d.get('Health', 'unknown')
    if h not in ('healthy',):
        print(d.get('Service','?'), h)
" 2>/dev/null || echo "checking...")

    if [ -z "$UNHEALTHY" ]; then
        echo "All services healthy!"
        break
    fi
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    echo "  ${ELAPSED}s: $UNHEALTHY"
done

if [ $ELAPSED -ge 180 ]; then
    echo "ERROR: Timeout waiting for healthy services"
    docker compose -f docker-compose.vps-host.yml ps
    exit 1
fi
```

```bash
# Проверка HTTP-доступности каждого сервиса
curl -sf http://127.0.0.1:8001/health  && echo " → Auth ✅"      || echo " → Auth ❌"
curl -sf http://127.0.0.1:8006/health  && echo " → Email ✅"     || echo " → Email ❌"
curl -sf http://127.0.0.1:8007/health  && echo " → Forecast ✅"  || echo " → Forecast ❌"
curl -sf http://127.0.0.1:3080/api/health && echo " → Frontend ✅" || echo " → Frontend ❌"

# Проверка Redis
docker exec $(docker ps -q -f name=redis) redis-cli -h 127.0.0.1 ping
# Ожидается: PONG

# Проверка PostgreSQL
docker exec $(docker ps -q -f name=postgres) pg_isready -U postgres -d fishing_db
# Ожидается: accepting connections
```

```bash
# Проверка логов на ошибки
docker compose -f docker-compose.vps-host.yml logs --tail=50 2>&1 | \
    grep -iE "error|fatal|NOAUTH|ECONNREFUSED|panic" && echo "WARN: errors found in logs" || echo "Logs OK"
```

### 8.6. Restart nginx (SmartTraffic)

```bash
# Если используется SmartTraffic nginx как reverse proxy
cd /opt/smarttraffic 2>/dev/null || true
if [ -f docker-compose.override.yml ]; then
    docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --force-recreate nginx
    sleep 3
    docker exec smarttraffic-nginx nginx -t 2>&1
fi
cd /opt/fishmap
```

### 8.7. Rollback (откат)

```bash
# Найти последний бэкап
LATEST_BACKUP=$(ls -t /opt/fishmap/backups/fishing_db_*.sql.gz | head -1)
echo "Latest backup: $LATEST_BACKUP"

# Остановить сервисы
docker compose -f docker-compose.vps-host.yml --env-file .env.vps down

# Восстановить БД из бэкапа
docker compose -f docker-compose.vps-host.yml --env-file .env.vps up -d postgres
sleep 5

gunzip -c "$LATEST_BACKUP" | docker exec -i $(docker ps -q -f name=postgres) \
    psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-fishing_db}"

# Откатить код к предыдущему тегу
PREV_TAG=$(git tag --sort=-version:refname | sed -n '2p')
git checkout "$PREV_TAG"

# Пересобрать и запустить
docker compose -f docker-compose.vps-host.yml --env-file .env.vps build --no-cache
docker compose -f docker-compose.vps-host.yml --env-file .env.vps up -d --force-recreate
```

### 8.8. Cleanup (очистка)

```bash
# Удалить старые бэкапы (оставить последние 5)
ls -t /opt/fishmap/backups/fishing_db_*.sql.gz | tail -n +6 | xargs -r rm -v

# Удалить неиспользуемые Docker-образы
docker image prune -af --filter "until=72h"

# Удалить неиспользуемые volumes
docker volume prune -f

# Показать использование диска
docker system df
```

### 8.9. Единая команда через setup-скрипт

```bash
# Полный деплой (preflight + build + start + nginx + verify)
./deploy/vps/setup-vps.sh deploy

# Обновление (пересборка + рестарт + verify)
./deploy/vps/setup-vps.sh update

# Остановка
./deploy/vps/setup-vps.sh stop

# Логи (все или конкретный сервис)
./deploy/vps/setup-vps.sh logs
./deploy/vps/setup-vps.sh logs auth-service

# Healthcheck
./deploy/vps/setup-vps.sh health
```

---

## 9. Типичные проблемы и решения

| Проблема | Симптом | Решение |
|----------|---------|---------|
| **PostgreSQL не стартует** | `postgres: unhealthy` | Проверить логи: `docker logs <postgres-container>`. Проверить `POSTGRES_PASSWORD`. Если data corruption: удалить volume и восстановить из бэкапа |
| **Redis NOAUTH** | `NOAUTH Authentication required` | Проверить что Redis запускается без пароля (конфиг FishMap). `redis-cli ping` должен вернуть `PONG` |
| **Auth Service падает** | `auth-service: restarting` | Проверить `DATABASE_URL` и `REDIS_URL` в env. Проверить что postgres и redis healthy. Логи: `docker compose -f docker-compose.vps-host.yml logs auth-service --tail=100` |
| **Frontend не собирается** | Build error на `npm run build` | Проверить `NEXT_PUBLIC_*` build args в `.env.vps`. TypeScript ошибки: `cd frontend && npx tsc --noEmit` |
| **nginx 502 Bad Gateway** | Домен возвращает 502 | Frontend не запущен или не отвечает на 3080. Проверить: `curl http://127.0.0.1:3080`. Проверить `host.docker.internal` в nginx конфиге |
| **Email не отправляется** | Код не приходит на почту | Проверить SMTP_* переменные. Проверить `ENABLE_EMAIL_SENDING=true`. Логи: `docker compose -f docker-compose.vps-host.yml logs email-service --tail=50` |
| **Forecast timeout** | `/health` долгий ответ | Forecast загружает данные при старте (start_period: 300s). Подождать 5 минут. Проверить `OPENWEATHERMAP_API_KEY` |
| **Нет места на диске** | `no space left on device` | `docker system prune -af --volumes`. Удалить старые бэкапы: `ls -t /opt/fishmap/backups/*.sql.gz \| tail -n +6 \| xargs rm` |
| **Миграция не применилась** | Новые колонки отсутствуют | Проверить `database/migrations/` — новый файл должен быть подключён в `docker-compose.vps-host.yml` как volume в `docker-entrypoint-initdb.d`. Для существующей БД: выполнить миграцию вручную через `psql` |
| **Порт занят** | `bind: address already in use` | `lsof -i :<PORT>` → убить процесс или изменить порт. Часто: старый контейнер не остановлен |
| **Memory limit** | Контейнер убит (OOMKilled) | Увеличить `mem_limit` в docker-compose для сервиса. Проверить `docker stats --no-stream` |
| **CORS ошибка** | Frontend → API блокируется | Проверить `CORS_ORIGINS` в backend. Убедиться что домен добавлен в allowed origins |

---

## 10. Чеклист деплоя

### Перед деплоем

- [ ] Код протестирован (GO от Тестировщика)
- [ ] `VERSION` файл обновлён (semver)
- [ ] `CHANGELOG.md` обновлён
- [ ] Git tag создан: `git tag -a "v$(cat VERSION)"`
- [ ] Изменения запушены: `git push --follow-tags`
- [ ] `.env.vps` проверен (нет `CHANGE_ME` значений)
- [ ] На диске VPS > 2 GB свободного места
- [ ] Текущий деплой работает (для отката)

### Во время деплоя

- [ ] Бэкап БД создан: `/opt/fishmap/backups/fishing_db_*.sql.gz`
- [ ] `git pull` выполнен
- [ ] Полная пересборка: `docker compose -f docker-compose.vps-host.yml build --no-cache`
- [ ] Контейнеры запущены: `docker compose -f docker-compose.vps-host.yml up -d --force-recreate`
- [ ] Все сервисы `healthy` (таймаут 180 сек)
- [ ] Логи не содержат `error`/`fatal`/`panic`

### После деплоя

- [ ] Все healthcheck-эндпоинты отвечают 200
- [ ] Версия в `/health` совпадает с `VERSION` файлом
- [ ] nginx reverse proxy работает (домен доступен)
- [ ] Redis: `PONG` на `redis-cli ping`
- [ ] PostgreSQL: `accepting connections`
- [ ] Frontend загружается в браузере
- [ ] Авторизация работает (регистрация + логин)
- [ ] Email отправляется (если включено)
- [ ] Карта загружается (Яндекс.Карты)
- [ ] Docker cleanup выполнен (`docker image prune`)
- [ ] Пользователь подтвердил работоспособность (ручной E2E-чеклист)

### Итоговый отчёт

```
✅ Образы собраны (все сервисы, --no-cache)
✅ Контейнеры запущены и healthy
✅ PostgreSQL OK (127.0.0.1:5432)
✅ Redis OK (127.0.0.1:6379)
✅ HTTP доступность:
   - Auth:      http://127.0.0.1:8001/health  ✅
   - Email:     http://127.0.0.1:8006/health  ✅
   - Forecast:  http://127.0.0.1:8007/health  ✅
   - Frontend:  http://127.0.0.1:3080         ✅
✅ nginx reverse proxy OK
✅ Бэкап создан: /opt/fishmap/backups/fishing_db_YYYYMMDD_HHMMSS.sql.gz
✅ Версия: vX.Y.Z
🎉 Продакшн-деплой завершён успешно
```

---

## 11. CI/CD (GitHub Actions)

### 11.1. Обзор

Продакшн-деплой автоматизирован через GitHub Actions. Два workflow-файла:

| Workflow | Файл | Триггер | Назначение |
|----------|------|---------|------------|
| **CI** | `.github/workflows/ci.yml` | push/PR | Проверка кода: lint, test, build |
| **CD** | `.github/workflows/deploy.yml` | tag v* / manual | Деплой на VPS по SSH |

**CI/CD дополняет, но НЕ заменяет** интерактивный деплой через opencode (PIPELINE_PROD.js).

### 11.2. CI Pipeline (ci.yml)

Запускается автоматически при каждом push в main/develop и при PR.

**Backend (7 сервисов параллельно):**
- `ruff check` — линтинг
- `pytest` — тесты (для сервисов без тестов — пропуск)

**Frontend:**
- `npm run lint` — ESLint
- `npx tsc --noEmit` — проверка типов
- `npm test` — Jest

**Docker Build Check:**
- Сборка образов auth, email, forecast, frontend (без push)

### 11.3. CD Pipeline (deploy.yml)

**Способы запуска:**
1. Автоматически при push tag `v*` (например, `v0.4.2`)
2. Вручную через GitHub Actions UI (workflow_dispatch, ввести `DEPLOY` для подтверждения)

**Шаги деплоя (следование PIPELINE_PROD.js):**

```
pre-flight → backup → deploy → [rollback при ошибке] → finalize
```

### 11.4. Настройка GitHub Secrets

Перед использованием CD pipeline нужно настроить секреты в GitHub:

**Repository → Settings → Secrets and variables → Actions**

| Secret | Описание | Пример |
|--------|----------|--------|
| `VPS_HOST` | IP-адрес или домен VPS | `5.35.102.219` |
| `VPS_USER` | SSH-пользователь | `root` |
| `VPS_SSH_KEY` | Приватный SSH-ключ | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `VPS_APP_DIR` | Путь к проекту на VPS | `/opt/fishmap` |

**Генерация SSH-ключа для деплоя:**

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy
ssh-copy-id -i ~/.ssh/github_deploy.pub root@YOUR_VPS_IP
cat ~/.ssh/github_deploy  # → вставить в GitHub Secret VPS_SSH_KEY
```

### 11.5. Запуск деплоя через GitHub Actions

**Вариант 1: Автоматический (по tag)**

```bash
git tag -a "v0.4.2" -m "Release v0.4.2"
git push origin v0.4.2
# → deploy.yml запустится автоматически
```

**Вариант 2: Ручной (GitHub UI)**

1. Открыть **Actions** → **Deploy to Production**
2. Нажать **Run workflow**
3. Ввести `DEPLOY` для подтверждения
4. Нажать **Run workflow**

### 11.6. Интеграция с PIPELINE_PROD.js

При интерактивном деплое через opencode (PIPELINE_PROD.js):
- Pre-flight включает проверку CI статуса (шаг PF7)
- Если CI не прошёл → предупреждение, запрос подтверждения

При деплое через deploy.yml:
- CI проверяется автоматически на шаге pre-flight
- Деплой не начнётся если CI провалился

---

## 12. Ссылки на связанные файлы

| Файл | Описание |
|------|----------|
| `SKILL_DEVOPS.md` | Скилл Dev-деплоя (локальная разработка, `docker-compose.dev.yml`) |
| `PIPELINE_PROD.js` | Продакшн-конвейер (формальная спецификация этапов) |
| `VERSIONING.md` | Стратегия версионирования (semver, git tags, CHANGELOG) |
| `docker-compose.vps-host.yml` | Compose-файл для VPS (host network) |
| `docker-compose.vps.yml` | Compose-файл для VPS (bridge network, альтернатива) |
| `.env.vps.example` | Шаблон переменных окружения для VPS |
| `deploy/vps/setup-vps.sh` | Скрипт автоматического деплоя на VPS |
| `deploy/vps/nginx-fishmap.conf` | Конфиг nginx для FishMap (reverse proxy) |
| `database/migrations/` | SQL-миграции (001–008+) |
| `DEPLOYMENT.md` | Общая документация по деплою |
| `ARCHITECTURE.md` | Архитектура платформы |
| `AGENTS.md` | Правила конвейера AI-команды |
| `.github/workflows/ci.yml` | CI pipeline (lint, test, build check) |
| `.github/workflows/deploy.yml` | CD pipeline (SSH-деплой на VPS) |

---

*Скилл создан для продакшн-деплоя платформы FishMap в рамках конвейера `PIPELINE_PROD.js`.*

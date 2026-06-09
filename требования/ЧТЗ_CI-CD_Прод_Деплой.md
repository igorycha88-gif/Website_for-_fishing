# ЧТЗ: Настройка CI/CD с интеграцией в конвейер прод-деплоя

## Версия: 1.0
## Дата: 2026-06-09
## Приоритет: High
## Статус: Согласовано

---

## Маршрутизация

**Архитектор:** НЕ ТРЕБУЕТСЯ (инфраструктурная задача, паттерн CI/CD стандартный)
**Исполнитель:** Разработчик (создание workflow-файлов) → Тестировщик → DevOps
**Обоснование:** Задача затрагивает CI/CD инфраструктуру (GitHub Actions) и интеграцию с существующим PIPELINE_PROD.js. Требует кода (YAML-файлы) + проверки + деплой-тест.

---

## 1. Цели и задачи

### 1.1 Бизнес-цель
Автоматизировать проверку качества кода (lint, test, build) при каждом push/PR и создать CI/CD-конвейер, который бесшовно интегрируется с существующим прод-конвейером (PIPELINE_PROD.js).

### 1.2 Пользовательская ценность
- Автоматическая проверка при каждом коммите — снижение риска сломанного прод-деплоя
- CI gate — нельзя задеплоить на прод если тесты/линт не прошли
- Единый источник правды: GitHub Actions → PIPELINE_PROD.js

### 1.3 Метрики успеха
- CI pipeline запускается при каждом push в main и при каждом PR
- Все 7 backend-сервисов проверяются (lint + test)
- Frontend проверяется (lint + typecheck + test)
- Время CI < 10 минут
- Прод-деплой через PIPELINE_PROD.js остаётся рабочим

---

## 2. Функциональные требования

### 2.1 CI Pipeline (при push/PR)

**Workflow: `ci.yml`** — основной конвейер

```
Trigger: push → main, develop; pull_request → main

Jobs:
  1. backend-auth       — ruff + pytest (auth-service)
  2. backend-email      — ruff + pytest (email-service)
  3. backend-forecast   — ruff + pytest (forecast-service)
  4. backend-places     — ruff + pytest (places-service)
  5. backend-reports    — ruff + pytest (reports-service)
  6. backend-booking    — ruff + pytest (booking-service)
  7. backend-shop       — ruff + pytest (shop-service)
  8. frontend           — lint + typecheck + test
  9. docker-build       — проверка сборки Docker-образов (dry-run)
```

**Все backend-джобы запускаются параллельно** для ускорения.

### 2.2 CD Pipeline (прод-деплой)

**Workflow: `deploy.yml`** — ручной запуск (workflow_dispatch) или по созданию tag `v*`

```
Trigger:
  - workflow_dispatch (ручной запуск с выбором версии)
  - push tag v* (автоматический при релизе)

Jobs:
  1. pre-flight        — проверка условий (ветка, env, SSH)
  2. deploy             — бэкап, сборка, деплой, верификация
  3. post-deploy-test   — API-тесты на проде
  4. finalize           — cleanup, отчёт
```

### 2.3 Интеграция с PIPELINE_PROD.js

CI/CD pipeline дополняет, а НЕ заменяет PIPELINE_PROD.js:
- **CI (ci.yml)**: автопроверка при push/PR (gate)
- **CD (deploy.yml)**: автоматизация ручных шагов из PIPELINE_PROD.js
- **PIPELINE_PROD.js**: по-прежнему используется для интерактивного деплоя через opencode (ручные E2E-чеклисты, вопрос о типе версионирования)

---

## 3. Техническая архитектура

### 3.1 Структура файлов

```
.github/
  workflows/
    ci.yml              — основной CI (lint + test + build check)
    deploy.yml          — прод-деплой (SSH → VPS)
    email-test.yml      — УДАЛИТЬ (заменён на ci.yml)
```

### 3.2 CI Workflow (ci.yml)

**Matrix Strategy** для backend-сервисов:

```yaml
strategy:
  matrix:
    service:
      - auth-service
      - email-service
      - forecast-service
      - places-service
      - reports-service
      - booking-service
      - shop-service
```

**Python setup**: actions/setup-python@v5 с Python 3.12
**Node.js setup**: actions/setup-node@v4 с Node.js 20, кеш npm

**Backend job steps:**
1. Checkout
2. Setup Python 3.12
3. Cache pip (`~/.cache/pip`)
4. Install dependencies: `pip install -r services/${{ matrix.service }}/requirements.txt`
5. Lint: `ruff check services/${{ matrix.service }}/`
6. Test: `pytest services/${{ matrix.service }}/tests/ -v`

**Frontend job steps:**
1. Checkout
2. Setup Node.js 20
3. Cache node_modules
4. Install: `npm ci`
5. Lint: `npm run lint`
6. Typecheck: `npx tsc --noEmit`
7. Test: `npm test`

**Docker build job steps:**
1. Checkout
2. Setup Docker Buildx
3. Build check: `docker compose -f docker-compose.vps-host.yml build` (без push)
4. Условие: запускается только если CI джобы прошли

### 3.3 CD Workflow (deploy.yml)

**Secrets (GitHub → Settings → Secrets):**

| Secret | Описание |
|--------|----------|
| `VPS_HOST` | IP-адрес или домен VPS |
| `VPS_USER` | SSH-пользователь (например, `root`) |
| `VPS_SSH_KEY` | Приватный SSH-ключ |
| `VPS_APP_DIR` | Путь к проекту на VPS (например, `/opt/fishmap`) |

**Deploy job steps (следование PIPELINE_PROD.js):**
1. Pre-flight: SSH connectivity check
2. Backup: `pg_dump | gzip > backups/db_YYYYMMDD.sql.gz`
3. Pull: `git pull origin main` на VPS
4. Build: `docker compose -f docker-compose.vps-host.yml --env-file .env.vps build --no-cache`
5. Deploy: `docker compose down` → `docker compose up -d --force-recreate`
6. Healthcheck: опрос контейнеров до healthy (макс 180 сек)
7. Verify: HTTP healthchecks всех сервисов
8. Post-deploy API test: curl всех /health эндпоинтов
9. Finalize: cleanup старых образов, отчёт

**Rollback** при провале любого критического шага:
- Остановка контейнеров
- Восстановление из бэкапа БД
- Запуск предыдущих контейнеров

### 3.4 Устаревшие файлы на удаление

- `.github/workflows/email-test.yml` — заменён на ci.yml (полное покрытие)

---

## 4. Декомпозиция на задачи

### Infrastructure

### TASK-INF-001: Создать CI workflow (ci.yml)
**Приоритет**: High
**Зависимости**: нет

**Описание**: Создать `.github/workflows/ci.yml` — основной CI-пайплайн. Запускается при push в main/develop и при PR. Параллельно проверяет все backend-сервисы (ruff + pytest) и frontend (lint + typecheck + test). Включает job проверки Docker-сборки.

**Критерии приемки**:
- [ ] Workflow запускается при push в main и PR
- [ ] 7 backend-джоб запускаются параллельно (matrix strategy)
- [ ] Frontend-джоб: lint + typecheck + test
- [ ] Docker-build джоб: проверяет сборку docker-compose
- [ ] Используется кеш pip и npm для ускорения
- [ ] Общее время CI < 10 минут

### TASK-INF-002: Создать CD workflow (deploy.yml)
**Приоритет**: High
**Зависимости**: TASK-INF-001

**Описание**: Создать `.github/workflows/deploy.yml` — прод-деплой по SSH на VPS. Запускается вручную (workflow_dispatch) или по tag v*. Следует шагам PIPELINE_PROD.js: pre-flight → backup → build → deploy → verify.

**Критерии приемки**:
- [ ] Workflow запускается по workflow_dispatch и tag v*
- [ ] Pre-flight проверка SSH-доступности VPS
- [ ] Бэкап БД (pg_dump) перед деплоем
- [ ] Полная пересборка docker-compose.vps-host.yml
- [ ] Healthcheck всех сервисов (макс 180 сек)
- [ ] HTTP healthchecks всех сервисов (curl)
- [ ] Автоматический rollback при провале критических шагов
- [ ] Cleanup старых образов после успешного деплоя
- [ ] Deployment Report в конце

### TASK-INF-003: Удалить устаревший email-test.yml
**Приоритет**: Low
**Зависимости**: TASK-INF-001

**Описание**: Удалить `.github/workflows/email-test.yml` — заменён на ci.yml.

**Критерии приемки**:
- [ ] Файл удалён
- [ ] ci.yml покрывает тесты email-service

### TASK-INF-004: Обновить PIPELINE_PROD.js — ссылка на CI/CD
**Приоритет**: Medium
**Зависимости**: TASK-INF-001, TASK-INF-002

**Описание**: Добавить в PIPELINE_PROD.js блок `CI_CD_INTEGRATION` с информацией о GitHub Actions workflows и ссылками на них. Добавить шаг в PRE-FLIGHT: «Проверить что CI pipeline прошёл».

**Критерии приемки**:
- [ ] PIPELINE_PROD.js содержит блок CI_CD_INTEGRATION
- [ ] Pre-flight включает проверку CI статуса
- [ ] Ссылки на ci.yml и deploy.yml

### TASK-INF-005: Обновить SKILL_DEVOPS_PROD.md — CI/CD раздел
**Приоритет**: Medium
**Зависимости**: TASK-INF-001, TASK-INF-002

**Описание**: Добавить в SKILL_DEVOPS_PROD.md раздел о CI/CD: какие workflows существуют, как они интегрируются с ручным деплоем, какие секреты нужны.

**Критерии приемки**:
- [ ] Раздел CI/CD добавлен
- [ ] Описаны все GitHub Secrets
- [ ] Описана интеграция с ручным деплоем через PIPELINE_PROD.js

---

## 5. Риски и зависимости

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| VPS недоступен по SSH из GitHub Actions | Среднее | Критичное | Проверить SSH key, firewall правила |
| Нет тестов в placeholder-сервисах | Высокое | Низкое | pytest с флагом `--ignore` или allow-failure |
| Долгая сборка Docker на CI | Среднее | Среднее | Кеш Docker layers, job запускается только при изменениях |
| Секреты не настроены в GitHub | Высокое | Критичное | Документация в SKILL_DEVOPS_PROD.md |

---

## 6. Согласование

- [x] Заказчик (пользователь)
- [ ] Техлид (автоматически через конвейер)

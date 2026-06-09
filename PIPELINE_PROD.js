/**
 * PIPELINE_PROD.js — Конвейер безопасного деплоя на прод (FishMap)
 *
 * Это НЕ исполняемый файл. Это ФОРМАЛЬНАЯ СПЕЦИФИКАЦИЯ конвейера
 * продакшн-деплоя, которую AI-агент (opencode) обязан выполнять пошагово.
 *
 * Отличия от основного конвейера (PIPELINE.js):
 *   - PIPELINE.js    → разработка (локально, docker-compose.dev.yml)
 *   - PIPELINE_PROD  → деплой на прод (VPS, docker-compose.vps.yml)
 *
 * Принцип: ОДИН промпт пользователя → безопасный деплой с откатом.
 * Каждый шаг проверяем, каждый провал — откат.
 *
 * Триггерные фразы пользователя:
 *   «деплой на прод», «задеплой», «деплой в прод», «выложить на прод»,
 *   «push to prod», «deploy to production», «запусти прод деплой»
 *
 * Базовый скилл: SKILL_DEVOPS.md (стандарт работы DevOps)
 * Расширенный скилл: SKILL_DEVOPS_PROD.md (продакшн-специфичные практики)
 * Версионирование: VERSIONING.md (semver стратегия)
 */

// ═══════════════════════════════════════════════════════════════════════
// 6 ЖЕЛЕЗНЫХ ПРАВИЛ ПРОД ДЕПЛОЯ
// ═══════════════════════════════════════════════════════════════════════

const PROD_RULES = {

  PR1_BACKUP_FIRST: `
    ПРАВИЛО 1: БЭКАП ПРЕЖДЕ ВСЕГО
    Перед ЛЮБЫМ изменением на проде — ОБЯЗАТЕЛЬНО:
    - Бэкап БД (pg_dump)
    - Фиксация текущего состояния контейнеров (docker compose ps, image tags)
    - Сохранение текущего nginx конфига
    БЭКАП — это страховка для отката. Без бэкапа — деплой НЕ начинается.`,

  PR2_VERIFY_EVERY_STEP: `
    ПРАВИЛО 2: ВЕРИФИКАЦИЯ КАЖДОГО ШАГА
    Каждый этап завершается проверкой:
    - Build → образы существуют
    - Start containers → healthcheck pass (все 7+ сервисов)
    - Smoke tests → все критические эндпоинты отвечают
    Провал любого шага → СТОП + ОТКАТ.`,

  PR3_AUTO_ROLLBACK: `
    ПРАВИЛО 3: АВТОМАТИЧЕСКИЙ ОТКАТ
    При провале healthcheck или smoke tests:
    1. Остановить новые контейнеры
    2. Вернуть предыдущие образы
    3. Запустить предыдущие контейнеры
    4. Верифицировать откат
    Откат НЕ требует подтверждения пользователя — это автоматическая защита.`,

  PR4_FULL_REBUILD: `
    ПРАВИЛО 4: ПОЛНАЯ ПЕРЕСБОРКА
    На проде Docker-образы — неделимые артефакты.
    ЗАПРЕЩЕНО: обновлять один контейнер, не трогая остальные.
    Каждый деплой — полная пересборка всех сервисов (docker compose build).
    nginx, Redis, PostgreSQL — НЕ пересобираются (они stateful).`,

  PR5_NO_PARTIAL_DEPLOY: `
    ПРАВИЛО 5: НИКАКИХ ЧАСТИЧНЫХ ДЕПЛОЕВ
    ЗАПРЕЩЕНО: деплоить только один микросервис.
    ВСЕГДА: полная пересборка всех backend-сервисов + frontend.
    Причина: сервисы зависят друг от друга (auth → email, frontend → все API).`,

  PR6_AUDIT_TRAIL: `
    ПРАВИЛО 6: АУДИТ
    Каждый деплой логируется:
    - timestamp начала/конца
    - предыдущая версия → новая версия
    - commit SHA
    - результат (success / failed / rolled_back)
    - длительность
    Логи деплоя сохраняются.`,
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 0: ПРЕДПОСЁЛОЧНАЯ ПРОВЕРКА (Pre-Flight)
// ═══════════════════════════════════════════════════════════════════════

const PREFLIGHT_STAGE = {
  role: "DEVOPS",
  icon: "🔍",
  name: "PRE-FLIGHT CHECK",

  steps: [
    {
      id: "PF1",
      name: "Проверка незакоммиченных изменений",
      action: `git status --porcelain
        Если есть незакоммиченные файлы → ВЫВЕСТИ предупреждение,
        СПОРОСИТЬ: «Есть незакоммиченные изменения. Продолжить?»`,
      critical: false,
    },
    {
      id: "PF2",
      name: "Проверка текущей ветки",
      action: `git branch --show-current
        Рекомендуемая ветка: main или master.
        Если другая → ВЫВЕСТИ предупреждение.`,
      critical: false,
    },
    {
      id: "PF3",
      name: "Проверка VPS доступности",
      action: `SSH connectivity check:
        ssh -o ConnectTimeout=10 -o BatchMode=yes ${VPS_USER}@${VPS_HOST} "echo OK"
        Если недоступен → деплой НЕ начинается.`,
      critical: true,
    },
    {
      id: "PF4",
      name: "Проверка дискового пространства на VPS",
      action: `ssh ${VPS_USER}@${VPS_HOST} "df -m / | tail -1 | awk '{print \\$4}'"
        Если свободно < 2GB → ВЫВЕСТИ предупреждение.
        Если свободно < 500MB → деплой НЕ начинается.`,
      critical: true,
    },
    {
      id: "PF5",
      name: "Проверка .env на проде",
      action: `ssh ${VPS_USER}@${VPS_HOST} "test -f ${APP_DIR}/.env.vps && echo OK || echo MISSING"
        Если .env.vps отсутствует → деплой НЕ начинается.`,
      critical: true,
    },
    {
      id: "PF6",
      name: "Фиксация текущего состояния прода",
      action: `Зафиксировать для возможного отката:
        - Текущие контейнеры: docker compose -f docker-compose.vps.yml ps
        - Текущий commit: git rev-parse HEAD
        Сохранить в PREVIOUS_STATE.`,
      critical: true,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 0.5: ВЕРСИОНИРОВАНИЕ
// ═══════════════════════════════════════════════════════════════════════

const VERSIONING_STAGE = {
  role: "DEVOPS",
  icon: "🏷️",
  name: "VERSIONING",

  steps: [
    {
      id: "VR1",
      name: "Определение текущей версии",
      action: `Прочитать текущую версию из VERSION файла:
        cat VERSION
        Пример: 0.4.1
        Запомнить как CURRENT_VERSION.`,
      critical: true,
    },
    {
      id: "VR2",
      name: "Определение типа изменения",
      action: `Проанализировать что было изменено:
        git log v${CURRENT_VERSION}..HEAD --oneline
        По коммит-сообщениям определить тип:
        - Если есть "feat!" или "BREAKING CHANGE" → major
        - Если есть "feat:" → minor
        - Иначе (fix:, refactor:, chore:) → patch

        ЗАДАТЬ вопрос пользователю через question tool:
        «Какой тип версионирования?» с вариантами:
        - patch (баг-фикс) — рекомендуемый
        - minor (новый функционал)
        - major (breaking change)
        Если пользователь не ответил 2 мин → использовать рекомендуемый.`,
      critical: true,
    },
    {
      id: "VR3",
      name: "Bump версии в VERSION файле",
      action: `Увеличить версию в VERSION файле:
        echo "${NEW_VERSION}" > VERSION
        Запомнить NEW_VERSION.
        Пример: 0.4.1 → 0.4.2`,
      critical: true,
    },
    {
      id: "VR4",
      name: "Обновление CHANGELOG.md",
      action: `Собрать список изменений:
        git log v${CURRENT_VERSION}..HEAD --pretty=format:"- %s (%h)" --no-merges

        Создать/обновить CHANGELOG.md — добавить блок наверх:
        ## [${NEW_VERSION}] - $(date +%Y-%m-%d)
        ### Добавлено / Исправлено / Изменено`,
      critical: false,
    },
    {
      id: "VR5",
      name: "Git commit + tag",
      action: `Закоммитить:
        git add VERSION CHANGELOG.md
        git commit -m "chore: release v${NEW_VERSION}"
        git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"
        НЕ ПУШИТЬ — push будет на этапе BUILD.`,
      critical: true,
    },
  ],

  skills: "VERSIONING.md",
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 1: БЭКАП
// ═══════════════════════════════════════════════════════════════════════

const BACKUP_STAGE = {
  role: "DEVOPS",
  icon: "💾",
  name: "BACKUP",

  steps: [
    {
      id: "BK1",
      name: "Бэкап базы данных",
      action: `Создать бэкап PostgreSQL на VPS:
        ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
          docker compose -f docker-compose.vps.yml exec -T postgres \\
          pg_dump -U postgres fishing_db | gzip > backups/db_\\$(date +%Y%m%d_%H%M%S).sql.gz"
        Бэкап ОБЯЗАТЕЛЕН. Если бэкап провалился → WARN + спросить подтверждение.`,
      critical: true,
    },
    {
      id: "BK2",
      name: "Проверка бэкапа",
      action: `Убедиться что бэкап создан и имеет размер > 0:
        ssh ${VPS_USER}@${VPS_HOST} "ls -la ${APP_DIR}/backups/db_*.sql.gz | tail -1"
        Если файл пустой или отсутствует → WARN.`,
      critical: true,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 2: СБОРКА
// ═══════════════════════════════════════════════════════════════════════

const BUILD_STAGE = {
  role: "DEVOPS",
  icon: "🏗️",
  name: "BUILD",

  steps: [
    {
      id: "BD1",
      name: "Push в origin (если есть незапушенные коммиты)",
      action: `Проверить: git log origin/$(git branch --show-current)..HEAD
        Если есть незапушенные коммиты → git push --follow-tags origin $(git branch --show-current)`,
      critical: true,
    },
    {
      id: "BD2",
      name: "Сборка на VPS",
      action: `SSH на VPS и полная пересборка:
        ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
          docker compose -f docker-compose.vps.yml build --no-cache"
        Таймаут: 10 минут.
        Если build failed → СТОП.`,
      critical: true,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 3: ДЕПЛОЙ
// ═══════════════════════════════════════════════════════════════════════

const DEPLOY_STAGE = {
  role: "DEVOPS",
  icon: "🚀",
  name: "DEPLOY",

  steps: [
    {
      id: "DP1",
      name: "Остановка текущих контейнеров",
      action: `ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
        docker compose -f docker-compose.vps.yml down --timeout 30"
        Остановка всех сервисов с grace period 30 секунд.`,
      critical: true,
    },
    {
      id: "DP2",
      name: "Запуск новых контейнеров",
      action: `ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
        docker compose -f docker-compose.vps.yml up -d --force-recreate"
        Запуск всех сервисов: postgres, redis, auth, places, reports,
        booking, shop, email, forecast, frontend.`,
      critical: true,
      rollback_trigger: true,
    },
    {
      id: "DP3",
      name: "Ожидание healthcheck всех сервисов (макс 120 сек)",
      action: `Опрос каждые 10 секунд, макс 120 секунд:
        ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
          docker compose -f docker-compose.vps.yml ps --format json"

        Условие: ВСЕ сервисы должны быть healthy.
        Проверить:
        1. postgres: healthy
        2. redis: healthy
        3. auth-service: healthy
        4. email-service: healthy
        5. forecast-service: healthy
        6. frontend: healthy

        Если healthcheck FAILED → АВТОМАТИЧЕСКИЙ ОТКАТ.`,
      critical: true,
      rollback_trigger: true,
    },
    {
      id: "DP4",
      name: "Миграции БД (если есть новые)",
      action: `Проверить есть ли новые файлы миграций:
        git diff v${PREVIOUS_VERSION}..HEAD --name-only -- database/migrations/
        Если есть → выполнить SQL миграцию:
        ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
          docker compose -f docker-compose.vps.yml exec -T postgres \\
          psql -U postgres fishing_db < database/migrations/NNN_new.sql"
        Если ошибка миграции → ОТКАТ + восстановить из бэкапа.`,
      critical: true,
      rollback_trigger: true,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 4: ВЕРИФИКАЦИЯ
// ═══════════════════════════════════════════════════════════════════════

const VERIFY_STAGE = {
  role: "DEVOPS",
  icon: "✅",
  name: "POST-DEPLOY VERIFICATION",

  steps: [
    {
      id: "VF1",
      name: "Проверка контейнеров",
      action: `ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
        docker compose -f docker-compose.vps.yml ps --format 'table {{.Name}}\t{{.Status}}'"
        Ожидаем: все сервисы Up (healthy)`,
      critical: true,
    },
    {
      id: "VF2",
      name: "HTTP healthchecks всех backend-сервисов",
      action: `Проверить каждый сервис:
        curl -sf http://localhost:8001/health   # Auth
        curl -sf http://localhost:8002/health   # Places
        curl -sf http://localhost:8006/health   # Email
        curl -sf http://localhost:8007/health   # Forecast
        Все должны вернуть 200 + {"status": "ok"}`,
      critical: true,
    },
    {
      id: "VF3",
      name: "Проверка Frontend",
      action: `curl -sf http://localhost:3080
        Ожидаем: 200`,
      critical: true,
    },
    {
      id: "VF4",
      name: "Проверка Redis",
      action: `ssh ${VPS_USER}@${VPS_HOST} "docker compose -f docker-compose.vps.yml exec -T redis redis-cli ping"
        Ожидаем: PONG`,
      critical: true,
    },
    {
      id: "VF5",
      name: "Проверка PostgreSQL",
      action: `ssh ${VPS_USER}@${VPS_HOST} "docker compose -f docker-compose.vps.yml exec -T postgres pg_isready -U postgres"
        Ожидаем: accepting connections`,
      critical: true,
    },
    {
      id: "VF6",
      name: "Проверка логов на ошибки",
      action: `ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
        docker compose -f docker-compose.vps.yml logs --tail=50 2>&1 | \\
        grep -iE 'error|fatal|panic|NOAUTH|ECONNREFUSED'"
        Если найдены critical ошибки → рассмотреть откат.
        WARN ошибки — не блокируют.`,
      critical: false,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 4.5: ПОЛНОЕ ТЕСТИРОВАНИЕ НА ПРОДЕ
// ═══════════════════════════════════════════════════════════════════════

const FULL_TESTING_STAGE = {
  role: "DEVOPS",
  icon: "🧪",
  name: "FULL PRODUCTION TESTING",

  steps: [
    {
      id: "FT1",
      name: "Автотест: Health endpoints всех сервисов",
      action: `SSH на VPS — проверить все health endpoints:
        curl -sf http://localhost:8001/health | python3 -m json.tool  # Auth
        curl -sf http://localhost:8002/health | python3 -m json.tool  # Places
        curl -sf http://localhost:8006/health | python3 -m json.tool  # Email
        curl -sf http://localhost:8007/health | python3 -m json.tool  # Forecast
        curl -sf http://localhost:3080/api/health                      # Frontend

        Проверить: status == "ok" для каждого
        Если любой FAILED → ❌ КРИТИЧЕСКАЯ ОШИБКА`,
      critical: true,
      rollback_trigger: true,
    },
    {
      id: "FT2",
      name: "Автотест: HTTP статусы ключевых страниц",
      action: `SSH на VPS — проверить:
        curl -s -o /dev/null -w "%{http_code}" http://localhost:3080         # → 200
        curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health  # → 200
        curl -s -o /dev/null -w "%{http_code}" http://localhost:8007/health  # → 200
        Все должны вернуть 200`,
      critical: true,
      rollback_trigger: true,
    },
    {
      id: "FT3",
      name: "Автотест: Время отклика",
      action: `SSH на VPS — замерить:
        for url in / /api/health /health; do
          TIME=$(curl -s -o /dev/null -w "%{time_total}" "http://localhost:3080${url}")
          echo "${url}: ${TIME}s"
          if (( $(echo "$TIME > 5.0" | bc -l) )); then echo "SLOW: ${url}"; fi
        done`,
      critical: false,
    },
    {
      id: "FT4",
      name: "Автотест: Логи без критических ошибок",
      action: `SSH на VPS:
        docker compose -f docker-compose.vps.yml logs --tail=100 2>&1 | \\
        grep -iE 'error|fatal|panic|unhandled|NOAUTH|ECONNREFUSED' | \\
        grep -viE 'healthcheck|favicon' || echo "Логи чистые"`,
      critical: false,
    },
    {
      id: "FT5",
      name: "Ручное E2E: Главная страница + Карта",
      action: `ВЫВЕСТИ пользователю чеклист:

        📋 E2E ТЕСТ — ГЛАВНАЯ СТРАНИЦА
        □ Страница загружается
        □ Карта Yandex отображается
        □ Навигация работает
        □ Футер отображается
        □ Мобильная версия OK

        Задать вопрос: «Главная страница OK?» (Да/Нет)`,
      critical: true,
      manual_e2e: true,
    },
    {
      id: "FT6",
      name: "Ручное E2E: Авторизация",
      action: `ВЫВЕСТИ пользователю чеклист:

        📋 E2E ТЕСТ — АВТОРИЗАЦИЯ
        □ Страница логина загружается
        □ Ввод email + password работает
        □ При неверных данных — ошибка
        □ Успешный логин → редирект

        Задать вопрос: «Авторизация OK?» (Да/Нет)`,
      critical: true,
      manual_e2e: true,
    },
    {
      id: "FT7",
      name: "Ручное E2E: Прогноз клёва",
      action: `ВЫВЕСТИ пользователю чеклист:

        📋 E2E ТЕСТ — ПРОГНОЗ КЛЁВА
        □ Страница прогноза загружается
        □ Данные прогноза отображаются
        □ Выбор региона/даты работает

        Задать вопрос: «Прогноз OK?» (Да/Нет/Пропустить)`,
      critical: false,
      manual_e2e: true,
    },
    {
      id: "FT8",
      name: "Сводный отчёт тестирования",
      action: `Вывести:

        ┌─────────────────────────────────────────────┐
        │      РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ НА ПРОДЕ        │
        ├─────────────────────────────────────────────┤
        │ Автотесты:  X/X passed                      │
        │ E2E ручные: X/X critical passed             │
        │ Версия:     ${NEW_VERSION}                    │
        │ Вердикт:    GO / CONDITIONAL GO / NO-GO     │
        └─────────────────────────────────────────────┘

        GO → FINALIZE
        CONDITIONAL GO → WARN + FINALIZE
        NO-GO → АВТОМАТИЧЕСКИЙ ОТКАТ`,
      critical: true,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП 5: ФИНАЛИЗАЦИЯ
// ═══════════════════════════════════════════════════════════════════════

const FINALIZE_STAGE = {
  role: "DEVOPS",
  icon: "📋",
  name: "FINALIZE",

  steps: [
    {
      id: "FN1",
      name: "Очистка старых образов",
      action: `ssh ${VPS_USER}@${VPS_HOST} "docker image prune -f"
        Удалить неиспользуемые образы.`,
      critical: false,
    },
    {
      id: "FN2",
      name: "Очистка старых бэкапов",
      action: `Удалить бэкапы БД старше 7 дней:
        ssh ${VPS_USER}@${VPS_HOST} "find ${APP_DIR}/backups -name '*.sql.gz' -mtime +7 -delete"`,
      critical: false,
    },
    {
      id: "FN3",
      name: "Deployment Report",
      action: `Вывести итоговый отчёт:
        ═══════════════════════════════════════════
        🎉 PRODUCTION DEPLOYMENT SUCCESSFUL
        ═══════════════════════════════════════════
        📦 Version:  v${NEW_VERSION}
        📊 From:     v${PREVIOUS_VERSION} → To: v${NEW_VERSION}
        💾 Backup:   ${APP_DIR}/backups/db_YYYYMMDD.sql.gz
        🐳 Services: All healthy
        ═══════════════════════════════════════════`,
      critical: true,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ЭТАП ОТКАТА: ROLLBACK
// ═══════════════════════════════════════════════════════════════════════

const ROLLBACK_STAGE = {
  role: "DEVOPS",
  icon: "🔄",
  name: "ROLLBACK",

  trigger: `
    Автоматический откат запускается при:
    - Healthcheck сервисов failed (Этап 3, DP3)
    - Миграция БД провалена (Этап 3, DP4)
    - Post-deploy verification NO-GO (Этап 4)

    Ручной откат — по команде пользователя:
    «откат», «rollback», «верни предыдущую версию»`,

  steps: [
    {
      id: "RB1",
      name: "Остановка текущих контейнеров",
      action: `ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
        docker compose -f docker-compose.vps.yml down --timeout 30"`,
      critical: true,
    },
    {
      id: "RB2",
      name: "Откат кода к предыдущей версии",
      action: `git checkout v${PREVIOUS_VERSION}
        Или: ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && git checkout v${PREVIOUS_VERSION}"`,
      critical: true,
    },
    {
      id: "RB3",
      name: "Пересборка и запуск предыдущей версии",
      action: `ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
        docker compose -f docker-compose.vps.yml build --no-cache && \\
        docker compose -f docker-compose.vps.yml up -d --force-recreate"
        Дождаться healthcheck (макс 120 сек).`,
      critical: true,
    },
    {
      id: "RB4",
      name: "Восстановление БД (если миграция повредила данные)",
      action: `ТОЛЬКО если есть признаки повреждения данных:
        1. Остановить приложение
        2. Восстановить из бэкапа:
           gunzip -c ${APP_DIR}/backups/db_YYYYMMDD.sql.gz | \\
           docker compose exec -T postgres psql -U postgres fishing_db
        3. Запустить приложение
        ВНИМАНИЕ: данные после бэкапа теряются.
        Спросить подтверждение пользователя ПЕРЕД восстановлением БД.`,
      critical: false,
    },
    {
      id: "RB5",
      name: "Верификация отката",
      action: `Проверить:
        - Все сервисы healthy
        - HTTP healthchecks → 200
        - Frontend → 200
        Если откат успешен → вывести отчёт.
        Если откат провалился → КРИТИЧЕСКАЯ ОШИБКА, ручное вмешательство.`,
      critical: true,
    },
  ],
};

// ═══════════════════════════════════════════════════════════════════════
// ПОСЛЕДЕПЛОЙНЫЙ МОНИТОРИНГ (5 мин)
// ═══════════════════════════════════════════════════════════════════════

const POST_DEPLOY_WATCH = {
  role: "DEVOPS",
  icon: "👁️",
  name: "WATCH (5 min)",

  steps: [
    {
      id: "PW1",
      name: "Мониторинг healthcheck",
      action: `Каждые 60 секунд в течение 5 минут:
        ssh ${VPS_USER}@${VPS_HOST} "cd ${APP_DIR} && \\
          docker compose -f docker-compose.vps.yml ps --format json"
        Проверить что все сервисы healthy.
        Если любой сервис упал → вывести предупреждение.`,
      interval_seconds: 60,
      duration_seconds: 300,
    },
  ],
};

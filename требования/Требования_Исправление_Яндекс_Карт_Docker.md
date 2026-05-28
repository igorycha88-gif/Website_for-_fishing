# Требования: Исправление отображения Яндекс Карт в Docker

**ID**: REQ-MAPS-DOCKER-001
**Версия**: 1.0
**Дата**: 2026-03-03
**Автор**: Business Analyst
**Статус**: ✅ Согласовано

---

## 1. Обзор

### 1.1 Проблема

**Описание**: Яндекс Карта не отображается на странице "Карта мест рыбалки" при запуске в Docker контейнере. Пользователи видят пустую область вместо интерактивной карты.

**Корневая причина**: Переменные окружения `NEXT_PUBLIC_YANDEX_MAPS_API_KEY` и другие `NEXT_PUBLIC_*` переменные не передаются на этапе сборки (build time) в Dockerfile. Next.js встраивает эти переменные в JavaScript бандл только во время сборки, поэтому передача через `environment` в runtime не работает.

**Влияние**:
- Пользователи не видят карту в production/Docker окружении
- Функционал карты полностью недоступен
- Плохой UX и потеря функциональности
- Блокирует использование платформы в Docker

### 1.2 Цель

Обеспечить корректное отображение Яндекс Карты в Docker контейнерах через передачу `NEXT_PUBLIC_*` переменных на этапе сборки (build time).

### 1.3 Бизнес-ценность

- Восстановление функционала карты для пользователей в production
- Устранение критического бага
- Обеспечение работы платформы в Docker окружении
- Улучшение UX

### 1.4 Область действия (Scope)

**Включает:**
- Обновление Dockerfile для поддержки build args
- Обновление docker-compose файлов
- Добавление fallback обработки ошибок
- Обновление документации

**Исключает:**
- Изменение логики работы карты
- Изменение API Яндекс Карт
- Рефакторинг компонентов карты

---

## 2. User Story

## User Story: Исправление отображения Яндекс Карт в Docker

**As a** пользователь платформы FishMap,
**I want to** видеть интерактивную карту на странице "Карта мест рыбалки" при запуске в Docker,
**So that** я могу использовать функционал карты независимо от окружения (dev/staging/production).

### Priority
- [x] High (критичный баг, блокирует функционал)

### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель
- [x] Developer (для dev/prod сред)
- [x] DevOps (для deployment)

### Acceptance Criteria

**AC1: Карта отображается в Docker контейнере**
- **Given** приложение запущено через docker-compose
- **And** пользователь переходит на страницу "/map"
- **When** страница загружена
- **Then** отображается Яндекс Карта
- **And** API ключ корректно загружен
- **And** карта интерактивна (можно двигать, приближать)
- **And** нет ошибок в консоли браузера

**AC2: Переменные передаются через build args в Dockerfile**
- **Given** Dockerfile содержит ARG для NEXT_PUBLIC_* переменных
- **When** выполняется `docker-compose build frontend`
- **Then** переменные встраиваются в JavaScript бандл
- **And** доступны в runtime без дополнительной конфигурации
- **And** docker build завершается успешно

**AC3: Совместимость с локальной разработкой**
- **Given** разработчик запускает `npm run dev` локально
- **When** используется `.env.local` файл
- **Then** карта отображается корректно
- **And** не требуется изменения кода
- **And** оба подхода (local и Docker) работают параллельно

**AC4: Docker-compose файлы обновлены**
- **Given** обновлен Dockerfile
- **When** разработчик запускает `docker-compose up`
- **Then** build args передаются из .env файла
- **And** docker-compose.yml и docker-compose.frontend.yml синхронизированы
- **And** docker-compose config проходит валидацию

**AC5: Обработка ошибок при отсутствии API ключа**
- **Given** API ключ Яндекс Карт не передан или некорректен
- **When** пользователь открывает страницу с картой
- **Then** показывается понятное сообщение об ошибке
- **And** сообщение содержит информацию для разработчика
- **And** не ломает остальной функционал страницы

**AC6: Документация обновлена**
- **Given** изменения внесены в Dockerfile и docker-compose
- **When** разработчик читает README
- **Then** есть инструкции по настройке переменных окружения для Docker
- **And** есть пример .env файла
- **And** указаны все необходимые NEXT_PUBLIC_* переменные

### Non-Functional Requirements

**Performance (Производительность)**:
- Сборка Docker образа не увеличивается более чем на 5 секунд
- Время загрузки карты остается < 2 секунд
- Нет влияния на runtime производительность

**Security (Безопасность)**:
- API ключи не коммитятся в Git history
- Используются .env файлы (в .gitignore)
- Переменные передаются безопасно через build args

**Maintainability (Сопровождаемость)**:
- Dockerfile остается читаемым и понятным
- Документация актуальна
- Легко добавить новые NEXT_PUBLIC_* переменные в будущем

**Compatibility (Совместимость)**:
- Backward compatibility с существующими deployment скриптами
- Работает на всех платформах (Linux, macOS, Windows)
- Совместимость с Next.js 15.0.0

### Dependencies
- Зависит от: Docker environment
- Зависит от: Next.js build process
- Блокирует: Использование платформы в production Docker

### Definition of Done
- [ ] Dockerfile обновлен с ARG директивами
- [ ] docker-compose.yml обновлен с build args
- [ ] docker-compose.frontend.yml обновлен с build args
- [ ] Fallback обработка ошибок добавлена в YandexMap.tsx
- [ ] Docker сборка протестирована локально
- [ ] Карта отображается в Docker контейнере
- [ ] Локальная разработка (npm run dev) работает
- [ ] README обновлен с инструкциями
- [ ] .env.example обновлен
- [ ] Code review пройден
- [ ] Ручное тестирование завершено

---

## 3. Декомпозиция на задачи

### TASK-INF-001: Обновить Dockerfile для поддержки NEXT_PUBLIC_* переменных

**Направление**: Infrastructure  
**Приоритет**: High  
**Оценка**: 1 час  
**Зависимости**: Нет

**Описание**:  
Добавить ARG и ENV директивы в Dockerfile для корректной передачи NEXT_PUBLIC_* переменных на этапе сборки. Переменные должны быть объявлены как ARG, затем установлены как ENV перед этапом сборки.

**Критерии приемки**:
- [ ] ARG директивы добавлены для `NEXT_PUBLIC_YANDEX_MAPS_API_KEY`
- [ ] ARG директивы добавлены для `NEXT_PUBLIC_API_URL`
- [ ] ARG директивы добавлены для `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`
- [ ] ENV директивы устанавливают значения из ARG
- [ ] ENV объявлены перед `npm run build`
- [ ] Dockerfile собирается без ошибок: `docker build -t test-frontend ./frontend`
- [ ] Переменные доступны в бандле после сборки

**Технические детали**:
- Файлы: `frontend/Dockerfile`
- Позиция: После `COPY . .`, перед `RUN npm run build`
- Формат:
  ```dockerfile
  ARG NEXT_PUBLIC_YANDEX_MAPS_API_KEY
  ARG NEXT_PUBLIC_API_URL
  ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
  
  ENV NEXT_PUBLIC_YANDEX_MAPS_API_KEY=$NEXT_PUBLIC_YANDEX_MAPS_API_KEY
  ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
  ENV NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
  ```

**Примечания**:
- Документация Next.js: https://nextjs.org/docs/basic-features/environment-variables#build-time-environment-variables
- ARG переменные не сохраняются в final image, поэтому нужны ENV

---

### TASK-INF-002: Обновить docker-compose.yml для передачи build args

**Направление**: Infrastructure  
**Приоритет**: High  
**Оценка**: 0.5 часа  
**Зависимости**: TASK-INF-001

**Описание**:  
Добавить секцию `args` в `build` конфигурацию frontend сервиса в docker-compose.yml для передачи переменных окружения на этапе сборки.

**Критерии приемки**:
- [ ] Секция `args` добавлена в `frontend.build`
- [ ] `NEXT_PUBLIC_YANDEX_MAPS_API_KEY` передается из `${YANDEX_MAPS_API_KEY}`
- [ ] `NEXT_PUBLIC_API_URL` передается из `https://${DOMAIN:-fishmap.local}`
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` передается из `${STRIPE_PUBLISHABLE_KEY}`
- [ ] `docker-compose config` проходит валидацию без ошибок
- [ ] Форматирование соответствует существующему стилю

**Технические детали**:
- Файлы: `docker-compose.yml`
- Позиция: В секцию `services.frontend.build`
- Формат:
  ```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_YANDEX_MAPS_API_KEY: ${YANDEX_MAPS_API_KEY}
        NEXT_PUBLIC_API_URL: https://${DOMAIN:-fishmap.local}
        NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: ${STRIPE_PUBLISHABLE_KEY}
  ```

**Примечания**:
- Убедиться, что переменные определены в `.env` файле
- Проверить, что docker-compose корректно читает .env

---

### TASK-INF-003: Обновить docker-compose.frontend.yml для передачи build args

**Направление**: Infrastructure  
**Приоритет**: High  
**Оценка**: 0.5 часа  
**Зависимости**: TASK-INF-001

**Описание**:  
Добавить секцию `args` в docker-compose.frontend.yml для обеспечения консистентности с основным docker-compose.yml.

**Критерии приемки**:
- [ ] Секция `args` добавлена в `frontend.build`
- [ ] `NEXT_PUBLIC_YANDEX_MAPS_API_KEY` передается
- [ ] `NEXT_PUBLIC_API_URL` передается как `http://localhost:3000`
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` передается
- [ ] `docker-compose -f docker-compose.frontend.yml config` проходит валидацию

**Технические детали**:
- Файлы: `docker-compose.frontend.yml`
- Формат:
  ```yaml
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_YANDEX_MAPS_API_KEY: ${YANDEX_MAPS_API_KEY}
        NEXT_PUBLIC_API_URL: http://localhost:3000
        NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: ${STRIPE_PUBLISHABLE_KEY}
  ```

---

### TASK-FRT-001: Добавить fallback для отсутствующего API ключа Яндекс Карт

**Направление**: Frontend  
**Приоритет**: Medium  
**Оценка**: 1 час  
**Зависимости**: TASK-INF-001

**Описание**:  
Улучшить обработку ошибок в компоненте YandexMap.tsx для случаев, когда API ключ отсутствует или некорректен. Показывать понятное сообщение разработчику/пользователю.

**Критерии приемки**:
- [ ] Проверка наличия API ключа перед загрузкой карты
- [ ] Если ключ отсутствует, показывается сообщение об ошибке
- [ ] Сообщение содержит: "API ключ Яндекс Карт не настроен"
- [ ] В development режиме: инструкция по настройке
- [ ] В production режиме: общее сообщение об ошибке
- [ ] Не ломает существующий функционал
- [ ] Ошибки логируются в console.error

**Технические детали**:
- Файлы: `frontend/components/YandexMap.tsx`
- Позиция: В начале компонента, перед return
- Пример:
  ```typescript
  const YANDEX_API_KEY = process.env.NEXT_PUBLIC_YANDEX_MAPS_API_KEY;
  
  if (!YANDEX_API_KEY) {
    return (
      <div className="flex items-center justify-center h-full min-h-[500px] bg-gray-100 rounded-2xl">
        <div className="text-center p-8">
          <p className="text-red-600 font-semibold mb-2">
            Ошибка загрузки карты
          </p>
          <p className="text-gray-600 text-sm">
            {process.env.NODE_ENV === 'development' 
              ? 'Установите NEXT_PUBLIC_YANDEX_MAPS_API_KEY в .env.local'
              : 'Карта временно недоступна'}
          </p>
        </div>
      </div>
    );
  }
  ```

---

### TASK-TST-001: Протестировать сборку Docker образа с build args

**Направление**: Testing  
**Приоритет**: High  
**Оценка**: 1 час  
**Зависимости**: TASK-INF-001, TASK-INF-002, TASK-INF-003

**Описание**:  
Выполнить полную сборку Docker образа frontend и проверить, что переменные корректно встраиваются в бандл и карта отображается.

**Критерии приемки**:
- [ ] `docker-compose build frontend` завершается успешно
- [ ] `docker-compose up` запускается без ошибок
- [ ] Страница /map открывается в браузере
- [ ] Яндекс Карта отображается корректно
- [ ] API ключ работает (нет ошибок в консоли браузера)
- [ ] Интерактивность карты работает (zoom, pan)
- [ ] Переменные видны в собранном бандле (проверка через browser devtools)

**Технические детали**:
- Команды:
  ```bash
  docker-compose build frontend
  docker-compose up -d
  ```
- Проверка: открыть http://localhost:3000/map
- DevTools: проверить `process.env.NEXT_PUBLIC_YANDEX_MAPS_API_KEY`

---

### TASK-TST-002: Протестировать локальную разработку

**Направление**: Testing  
**Приоритет**: Medium  
**Оценка**: 0.5 часа  
**Зависимости**: TASK-FRT-001

**Описание**:  
Убедиться, что изменения в Dockerfile не ломают локальную разработку через npm run dev.

**Критерии приемки**:
- [ ] `npm run dev` запускается без ошибок
- [ ] Переменные из `.env.local` читаются корректно
- [ ] Карта отображается на localhost:3000/map
- [ ] Hot reload работает
- [ ] Нет regressions в существующем функционале

**Технические детали**:
- Команда: `cd frontend && npm run dev`
- Файл: `frontend/.env.local` должен содержать переменные

---

### TASK-DOC-001: Обновить README с инструкциями по настройке переменных

**Направление**: Documentation  
**Приоритет**: Medium  
**Оценка**: 0.5 часа  
**Зависимости**: TASK-INF-001

**Описание**:  
Добавить в README раздел о настройке переменных окружения для Docker и локальной разработки.

**Критерии приемки**:
- [ ] Добавлена секция "Environment Variables" в frontend/README.md
- [ ] Добавлена секция "Docker Configuration" в основной README.md
- [ ] Указаны все необходимые NEXT_PUBLIC_* переменные
- [ ] Есть пример .env файла
- [ ] Есть инструкции для локальной разработки
- [ ] Есть инструкции для Docker
- [ ] Указано, какие переменные обязательны

**Технические детали**:
- Файлы: `frontend/README.md`, `README.md`
- Пример секции:
  ```markdown
  ## Environment Variables
  
  ### Required Variables
  
  - `NEXT_PUBLIC_YANDEX_MAPS_API_KEY` - API ключ Яндекс Карт
  - `NEXT_PUBLIC_API_URL` - URL backend API
  - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
  
  ### Local Development
  
  1. Copy `.env.example` to `.env.local`
  2. Fill in the required values
  3. Run `npm run dev`
  
  ### Docker
  
  1. Create `.env` file in project root
  2. Set all required variables
  3. Run `docker-compose up`
  ```

---

### TASK-DOC-002: Обновить .env.example с NEXT_PUBLIC_* переменными

**Направление**: Documentation  
**Приоритет**: Low  
**Оценка**: 0.25 часа  
**Зависимости**: Нет

**Описание**:  
Убедиться, что .env.example содержит все необходимые NEXT_PUBLIC_* переменные с комментариями.

**Критерии приемки**:
- [ ] `NEXT_PUBLIC_YANDEX_MAPS_API_KEY` добавлен в .env.example
- [ ] `NEXT_PUBLIC_API_URL` добавлен в .env.example
- [ ] `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` уже есть
- [ ] Есть комментарии для каждой переменной
- [ ] Есть примеры значений

**Технические детали**:
- Файлы: `.env.example`
- Формат:
  ```bash
  # Frontend Environment Variables (required for Docker builds)
  NEXT_PUBLIC_YANDEX_MAPS_API_KEY=your_yandex_maps_api_key_here
  NEXT_PUBLIC_API_URL=http://localhost:3000
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
  ```

---

### Итоговая таблица задач

| ID | Направление | Приоритет | Оценка | Зависимости | Статус |
|----|-------------|-----------|--------|-------------|--------|
| TASK-INF-001 | Infrastructure | High | 1h | - | [ ] |
| TASK-INF-002 | Infrastructure | High | 0.5h | INF-001 | [ ] |
| TASK-INF-003 | Infrastructure | High | 0.5h | INF-001 | [ ] |
| TASK-FRT-001 | Frontend | Medium | 1h | INF-001 | [ ] |
| TASK-TST-001 | Testing | High | 1h | INF-001, INF-002, INF-003 | [ ] |
| TASK-TST-002 | Testing | Medium | 0.5h | FRT-001 | [ ] |
| TASK-DOC-001 | Documentation | Medium | 0.5h | INF-001 | [ ] |
| TASK-DOC-002 | Documentation | Low | 0.25h | - | [ ] |

**Общая оценка**: 5.25 часа (~1 рабочий день)  
**Критический путь**: INF-001 → INF-002 → TST-001  
**Рекомендуемая последовательность**: INF-001 → INF-002 → INF-003 → FRT-001 → TST-001 → TST-002 → DOC-001 → DOC-002

---

## 4. Техническая спецификация

### 4.1 Изменения в Dockerfile

**Текущий код** (frontend/Dockerfile:14-18):
```dockerfile
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG DOCKER_ENV=true
ENV DOCKER_ENV=${DOCKER_ENV}

RUN npm run build
```

**Новый код**:
```dockerfile
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG DOCKER_ENV=true
ENV DOCKER_ENV=${DOCKER_ENV}

# Build-time environment variables for Next.js
ARG NEXT_PUBLIC_YANDEX_MAPS_API_KEY
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

ENV NEXT_PUBLIC_YANDEX_MAPS_API_KEY=$NEXT_PUBLIC_YANDEX_MAPS_API_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

RUN npm run build
```

### 4.2 Изменения в docker-compose.yml

**Текущий код** (docker-compose.yml:366-376):
```yaml
frontend:
  image: frontend:latest
  build:
    context: ./frontend
    dockerfile: Dockerfile
  environment:
    DOCKER_ENV: 'true'
    NEXT_PUBLIC_API_URL: https://${DOMAIN:-fishmap.local}
    NEXT_PUBLIC_YANDEX_MAPS_API_KEY: ${YANDEX_MAPS_API_KEY}
    NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: ${STRIPE_PUBLISHABLE_KEY}
```

**Новый код**:
```yaml
frontend:
  image: frontend:latest
  build:
    context: ./frontend
    dockerfile: Dockerfile
    args:
      NEXT_PUBLIC_YANDEX_MAPS_API_KEY: ${YANDEX_MAPS_API_KEY}
      NEXT_PUBLIC_API_URL: https://${DOMAIN:-fishmap.local}
      NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: ${STRIPE_PUBLISHABLE_KEY}
  environment:
    DOCKER_ENV: 'true'
```

**Примечание**: `environment` секция остается для non-NEXT_PUBLIC переменных (например, DOCKER_ENV).

### 4.3 Изменения в YandexMap.tsx

**Добавить проверку API ключа** (frontend/components/YandexMap.tsx:133):
```typescript
export default function YandexMap({
  city,
  blurred = false,
  onRegisterClick,
  places = [],
  onPlaceClick,
  onAddPlaceClick,
  filters,
  showFilters = false,
  onFiltersChange,
  onFavoriteClick,
  tempMarker,
}: YandexMapProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([55.7558, 37.6173]);

  // Check if API key is available
  if (!YANDEX_API_KEY) {
    return (
      <div className="relative w-full h-full min-h-[500px] rounded-2xl overflow-hidden bg-gray-100 flex items-center justify-center">
        <div className="text-center p-8 bg-white rounded-xl shadow-lg">
          <p className="text-red-600 font-semibold text-lg mb-2">
            Ошибка загрузки карты
          </p>
          <p className="text-gray-600 text-sm">
            {process.env.NODE_ENV === 'development' 
              ? 'API ключ Яндекс Карт не настроен. Установите NEXT_PUBLIC_YANDEX_MAPS_API_KEY в .env.local или docker-compose.yml'
              : 'Карта временно недоступна. Попробуйте позже.'}
          </p>
        </div>
      </div>
    );
  }

  // ... rest of the component
```

---

## 5. Sequence Diagram

## Sequence Diagram: Загрузка карты в Docker

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant DC as Docker Compose
    participant DF as Dockerfile
    participant Next as Next.js Build
    participant Img as Docker Image
    participant Browser as Browser

    Dev->>DC: docker-compose build frontend
    DC->>DC: Read .env file
    DC->>DF: Build with args (YANDEX_API_KEY)
    DF->>DF: ARG NEXT_PUBLIC_YANDEX_MAPS_API_KEY
    DF->>DF: ENV NEXT_PUBLIC_YANDEX_MAPS_API_KEY=...
    DF->>Next: npm run build
    Next->>Next: Embed NEXT_PUBLIC_* in JS bundle
    Next->>Img: Create Docker image
    Img-->>DC: Build complete
    
    Dev->>DC: docker-compose up
    DC->>Img: Start container
    Img->>Browser: Serve JavaScript bundle
    Browser->>Browser: Load YandexMap component
    Browser->>Browser: Read NEXT_PUBLIC_YANDEX_MAPS_API_KEY
    Browser->>Browser: Initialize Yandex Maps API
    Browser-->>Dev: Map displayed successfully
```

**Описание**: Диаграмма показывает процесс сборки Docker образа с передачей build args. Переменные встраиваются в JavaScript бандл на этапе сборки и становятся доступны в браузере.

---

## 6. Риски и митигация

### Матрица рисков

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| Переменные не передаются через build args | Low | High | Локальное тестирование сборки перед коммитом |
| Breaking change для существующих deployments | Medium | Medium | Документировать изменения, обеспечить backward compatibility |
| API ключ утекает в Git history | Low | High | Использовать .env файлы (в .gitignore), не коммитить секреты |
| Увеличение времени сборки | Low | Low | Мониторинг времени сборки, оптимизация если необходимо |
| Несовместимость с существующими CI/CD пайплайнами | Medium | Medium | Документировать изменения для DevOps команды |
| Ошибки валидации docker-compose | Low | Medium | Проверка через `docker-compose config` |

### Детальный анализ рисков

#### Risk: Breaking change для существующих deployments

**Category**: Technical  
**Probability**: Medium  
**Impact**: Medium

**Description**:  
Изменения в Dockerfile и docker-compose.yml могут потребовать обновления существующих deployment скриптов и CI/CD пайплайнов.

**Potential Impact**:
1. Существующие deployments перестанут работать
2. Потребуется обновление документации для DevOps
3. Возможен простой при deployment

**Mitigation Strategies**:
1. **Prevent**: Документировать все изменения в CHANGELOG
2. **Prevent**: Обеспечить backward compatibility где возможно
3. **Mitigate**: Уведомить DevOps команду заранее
4. **Accept**: Запланировать время на обновление deployments

**Owner**: DevOps  
**Review Date**: 2026-03-10

---

#### Risk: API ключ утекает в Git history

**Category**: Security  
**Probability**: Low  
**Impact**: High

**Description**:  
Если API ключ случайно закоммитить в Git, он станет доступен в истории коммитов, что является уязвимостью безопасности.

**Potential Impact**:
1. Компрометация API ключа
2. Возможность злоупотребления ключом третьими лицами
3. Финансовые потери (если платный тариф)

**Mitigation Strategies**:
1. **Prevent**: .env файлы добавлены в .gitignore
2. **Prevent**: Использовать переменные окружения, не хардкодить ключи
3. **Mitigate**: Регулярная проверка Git history на наличие секретов
4. **Mitigate**: Использовать git-secrets или similar tools

**Owner**: Developer  
**Review Date**: 2026-03-10

---

## 7. Non-Functional Requirements

### Performance (Производительность)

**Build Time**:
- Увеличение времени сборки Docker образа: < 5 секунд
- Общее время сборки frontend: < 3 минут

**Runtime Performance**:
- Время загрузки карты: < 2 секунд (без изменений)
- Время инициализации компонента: < 100ms
- Нет влияния на First Contentful Paint (FCP)

**Bundle Size**:
- Увеличение размера бандла: 0 bytes (только встраивание переменных)
- Нет дополнительных зависимостей

### Security (Безопасность)

**Secrets Management**:
- API ключи не коммитятся в Git
- Используются .env файлы (в .gitignore)
- Переменные передаются через Docker build args (безопасно)

**Validation**:
- Валидация API ключа на клиенте перед загрузкой
- Graceful degradation при отсутствии ключа

### Maintainability (Сопровождаемость)

**Code Quality**:
- Dockerfile остается читаемым и понятным
- Комментарии для объяснения ARG/ENV директив
- Следование Docker best practices

**Documentation**:
- README обновлен с инструкциями
- .env.example содержит все переменные
- CHANGELOG обновлен

**Extensibility**:
- Легко добавить новые NEXT_PUBLIC_* переменные
- Паттерн повторяем для других сервисов

### Compatibility (Совместимость)

**Platforms**:
- Linux (Ubuntu, Debian, CentOS)
- macOS (Intel, Apple Silicon)
- Windows (WSL2, Docker Desktop)

**Next.js**:
- Совместимость с Next.js 15.0.0
- Совместимость с standalone output mode

**Docker**:
- Docker Engine 20.10+
- Docker Compose 2.0+

---

## 8. Definition of Ready (DoR)

**Перед началом разработки требования должны быть:**

- [x] **Clear**: Понятны всем членам команды
- [x] **Testable**: Можно протестировать (карта отображается в Docker)
- [x] **Feasible**: Технически выполнимы (standard Docker practice)
- [x] **Valuable**: Приносят ценность бизнесу (восстановление функционала)
- [x] **Sized**: Размер позволяет реализовать за 1 день (5.25 часа)
- [x] **Dependencies**: Все зависимости идентифицированы (Docker, Next.js)
- [x] **Acceptance Criteria**: Полностью определены (6 критериев)
- [x] **UI/UX**: Нет изменений в UI/UX
- [x] **Approved**: Утверждены стейкхолдерами (согласовано с заказчиком)
- [x] **Prioritized**: Приоритет установлен (High)

---

## 9. Definition of Done (DoD)

**Считать выполненным, когда:**

- [ ] **Code**: Код написан и прошел code review
- [ ] **Infrastructure**: Dockerfile обновлен
- [ ] **Infrastructure**: docker-compose.yml обновлен
- [ ] **Infrastructure**: docker-compose.frontend.yml обновлен
- [ ] **Frontend**: Fallback обработка добавлена в YandexMap.tsx
- [ ] **Tests**: Docker сборка протестирована локально
- [ ] **Tests**: Локальная разработка протестирована
- [ ] **Documentation**: README обновлен
- [ ] **Documentation**: .env.example обновлен
- [ ] **Manual Testing**: Ручное тестирование завершено (карта отображается)
- [ ] **Acceptance**: Все критерии приемки выполнены
- [ ] **Deployment**: Изменения задеплоены в dev environment

---

## 10. Версии документа

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| 1.0 | 2026-03-03 | Business Analyst | Создание документа, согласовано с заказчиком |

---

## 11. Согласование

| Роль | Имя | Дата | Подпись |
|------|-----|------|---------|
| Business Analyst | AI Assistant | 2026-03-03 | ✅ |
| Product Owner / Заказчик | Igor | 2026-03-03 | ✅ Согласовано |
| Tech Lead | - | - | ⏳ Ожидает |
| DevOps | - | - | ⏳ Ожидает |

---

## 12. Приложение: Чек-лист для разработчика

### Перед началом работы
- [ ] Прочитать документ полностью
- [ ] Убедиться, что есть доступ к Яндекс Кабинету разработчика
- [ ] Проверить наличие .env файла с переменными

### Во время разработки
- [ ] Следовать порядку задач (INF-001 → INF-002 → ...)
- [ ] Тестировать каждое изменение локально
- [ ] Не коммитить .env файлы с реальными ключами

### После завершения
- [ ] Пройти по всем критериям приемки
- [ ] Выполнить ручное тестирование в Docker
- [ ] Обновить документацию
- [ ] Создать Pull Request
- [ ] Дождаться Code Review

### Команды для проверки
```bash
# Сборка Docker образа
docker-compose build frontend

# Запуск контейнеров
docker-compose up -d

# Проверка логов
docker-compose logs frontend

# Проверка конфигурации
docker-compose config

# Остановка контейнеров
docker-compose down
```

---

## 13. Приложение: Пример .env файла

```bash
# Backend Variables
POSTGRES_DB=fishing_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
DATABASE_URL=postgresql+asyncpg://postgres:postgres_password@postgres:5432/fishing_db

# Redis
REDIS_URL=redis://redis:6379/0

# Auth Service
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontend Variables (Build-time)
NEXT_PUBLIC_YANDEX_MAPS_API_KEY=dfb59053-0011-47fb-a6f1-a14efb9160d1
NEXT_PUBLIC_API_URL=http://localhost:3000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key

# Yandex Maps
YANDEX_MAPS_API_KEY=dfb59053-0011-47fb-a6f1-a14efb9160d1

# Domain
DOMAIN=localhost

# Environment
ENVIRONMENT=development
DOCKER_ENV=true
```

---

**Документ готов к передаче разработчику. Все требования согласованы и утверждены.**

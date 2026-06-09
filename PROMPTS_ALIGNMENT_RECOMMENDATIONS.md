# Рекомендации по выравниванию промптов с реальной реализацией

**Дата анализа**: 2024-02-17
**Статус**: Готово к внедрению
**Приоритет**: 🔴 ВЫСОКИЙ - промпты должны отражать текущее состояние

---

## Резюме проблем

| Проблема | Файл | Строка | Статус | Действие |
|----------|------|--------|--------|----------|
| Яндекс Карты не описаны в SYSTEM_PROMPT | SYSTEM_PROMPT.md | - | 🔴 КРИТИЧНО | Добавить раздел |
| My Places статус неактуален | SYSTEM_PROMPT.md | 169 | 🟡 ВАЖНО | Обновить фразу |
| Auth Service endpoints неполные | SYSTEM_PROMPT.md | 113-124 | 🟡 ВАЖНО | Добавить geocode endpoint |
| shared-utils неиспользуется | DEVELOPER_PROMPT.md | 321 | 🟡 ВАЖНО | Убрать или пояснить |
| My Places 70% готова не упоминается | DEVELOPER_PROMPT.md | - | 🟡 ВАЖНО | Добавить раздел |

---

## 1. ОБНОВЛЕНИЕ SYSTEM_PROMPT.md

### Проблема 1.1: Яндекс Карты не документированы
**Статус**: 🔴 КРИТИЧНО
**Текущее состояние**: Интеграция реализована в Auth Service, но не упоминается в SYSTEM_PROMPT

**Что нужно добавить**:

Добавить новый раздел после раздела "Email Service" (после строки 157):

```markdown
### Яндекс Карты ✅ (Интегрировано в Auth Service)

**Реализованный функционал:**
- Endpoint `GET /api/v1/maps/geocode` для геокодирования города
- Кэширование результатов в Redis (TTL: 1 час)
- Поле `city` в модели User для хранения города пользователя
- Frontend компонент YandexMap для отображения интерактивной карты
- Размытие карты для незарегистрированных пользователей

**API Ключ Яндекс Карт:**
```
dfb59053-0011-47fb-a6f1-a14efb9160d1
```

**Реализованные файлы:**
- Backend:
  - `services/auth-service/app/endpoints/maps.py` - endpoint геокодирования
  - `services/auth-service/app/services/geocode.py` - сервис с кэшем Redis
  - `services/auth-service/app/models/user.py` - модель User с полем city
  - `services/auth-service/app/core/database.py` - функция get_redis()

- Frontend:
  - `frontend/components/YandexMap.tsx` - компонент карты
  - `frontend/app/map/page.tsx` - страница с полной картой
  - `frontend/app/profile/components/MyPlacesTab.tsx` - вкладка "Мои места"
  - `frontend/app/profile/components/SettingsTab.tsx` - изменение города в профиле
  - `frontend/types/yandex-maps.d.ts` - TypeScript типы

**Особенности:**
- Redis кэширование для снижения нагрузки на API Яндекса
- Graceful degradation при недоступности API
- Поддержка множественных городов без переписания
```

---

### Проблема 1.2: Auth Service endpoints неполные

**Статус**: 🟡 ВАЖНО
**Текущее состояние**: Не упоминается endpoint для геокодирования

**Что нужно изменить** (в разделе "Auth Service", строка 113-124):

**БЫЛО:**
```markdown
**Реализованные эндпоинты:**
```
POST   /api/v1/auth/register              - Регистрация пользователя
POST   /api/v1/auth/verify-email          - Подтверждение email
POST   /api/v1/auth/login                 - Вход в систему
POST   /api/v1/auth/reset-password/request - Запрос сброса пароля
POST   /api/v1/auth/reset-password/confirm - Подтверждение сброса пароля
GET    /api/v1/users/me                   - Получить текущего пользователя
PUT    /api/v1/users/me                   - Обновить профиль
PATCH  /api/v1/users/me/password          - Изменить пароль
GET    /health                             - Health check
```
```

**СТАЛО:**
```markdown
**Реализованные эндпоинты:**
```
POST   /api/v1/auth/register              - Регистрация пользователя
POST   /api/v1/auth/verify-email          - Подтверждение email
POST   /api/v1/auth/login                 - Вход в систему
POST   /api/v1/auth/reset-password/request - Запрос сброса пароля
POST   /api/v1/auth/reset-password/confirm - Подтверждение сброса пароля
GET    /api/v1/users/me                   - Получить текущего пользователя
PUT    /api/v1/users/me                   - Обновить профиль
PATCH  /api/v1/users/me/password          - Изменить пароль
GET    /api/v1/maps/geocode               - Геокодирование города (Redis cache) ⭐
GET    /health                             - Health check
```
```

---

### Проблема 1.3: Frontend - My Places статус устарел

**Статус**: 🟡 ВАЖНО
**Текущее состояние**: Документация говорит что "основные страницы реализованы", но не упоминает что My Places 70% готова

**Что нужно изменить** (в разделе "Frontend", строка 160-173):

**БЫЛО:**
```markdown
**Реализованные страницы:**
```
/                    - Главная страница
/login               - Вход
/register            - Регистрация
/verify-email        - Подтверждение email
/reset-password      - Сброс пароля
/profile             - Профиль пользователя (вкладки: Profile, Settings)
/map                 - Интерактивная карта
/resorts             - Список мест
/shop                - Магазин
/stores              - Магазины
/forecast            - Прогноз погоды
```
```

**СТАЛО:**
```markdown
**Реализованные страницы:**
```
/                    - Главная страница
/login               - Вход
/register            - Регистрация
/verify-email        - Подтверждение email
/reset-password      - Сброс пароля
/profile             - Профиль пользователя с вкладками:
                       ├─ Profile (профиль пользователя)
                       ├─ Settings (настройки + город)
                       ├─ My Places (70% готова ⚠️ - ожидает backend API)
                       ├─ Cart (заказы)
                       ├─ Orders (история заказов)
                       ├─ Notifications (уведомления)
                       ├─ Reports (отчеты)
                       └─ Bookings (бронирования)
/map                 - Интерактивная карта (Яндекс Карты)
/resorts             - Список мест
/shop                - Магазин
/stores              - Магазины
/forecast            - Прогноз погоды
```
```

**Дополнительная информация**: Добавить после раздела "Frontend":

```markdown
### Frontend - Статус вкладок в профиле

| Вкладка | Статус | Примечание |
|---------|--------|-----------|
| Profile | ✅ | Просмотр и редактирование профиля |
| Settings | ✅ | Смена пароля, город для карты |
| My Places | ⚠️ 70% | UI готов, ожидает backend API для CRUD |
| Cart | 🚧 | Только UI (заглушка) |
| Orders | 🚧 | Только UI (заглушка) |
| Notifications | 🚧 | Только UI (заглушка) |
| Reports | 🚧 | Только UI (заглушка) |
| Bookings | 🚧 | Только UI (заглушка) |

**My Places Tab - Детали реализации**

✅ Реализовано:
- YandexMap компонент для отображения мест
- Двухколоночный layout (карта + список)
- Список мест с иконками типов (🌲 дикое, ⛺ кэмпинг, 🏨 база)
- Поиск по названию места
- Фильтры: видимость (private/public), тип места (wild/camping/resort), тип подъезда (car/boat/foot)
- Модальное окно с полной информацией о месте
- Отображение фотографий и видов рыбы (fish_types)
- Разделение визуального стиля личных (синие) и публичных (зеленые) мест

❌ Требует реализации backend:
- Создание места - требует `POST /api/v1/places/my`
- Редактирование места - требует `PUT /api/v1/places/my/:id` (нет кнопок Edit)
- Удаление места - требует `DELETE /api/v1/places/my/:id` (нет кнопок Delete)
- Загрузка фотографий на Cloudinary
- Получение справочников fish_types и equipment_types
- Автозаполнение адреса при клике на карту (геокодирование)

⚠️ Требует проверки:
- Компонент AddPlaceForm (импортируется, но требует анализа реализации)
```

---

## 2. ОБНОВЛЕНИЕ DEVELOPER_PROMPT.md

### Проблема 2.1: shared-utils упоминается, но не используется

**Статус**: 🟡 ВАЖНО
**Текущее состояние**: Папка shared-utils указана в структуре, но на практике не используется

**Что нужно изменить** (в разделе "Структура проекта", строка 310-331):

**БЫЛО:**
```markdown
├── services/
│   ├── auth-service/
│   ├── places-service/
│   ├── reports-service/
│   ├── booking-service/
│   ├── shop-service/
│   ├── email-service/
│   └── shared-utils/          # Shared code
```

**СТАЛО:**
```markdown
├── services/
│   ├── auth-service/
│   ├── places-service/
│   ├── reports-service/
│   ├── booking-service/
│   ├── shop-service/
│   ├── email-service/
│   └── shared-utils/          # Зарезервирована для общего кода (пока неиспользуется)
```

**Дополнительно**: Добавить примечание в раздел "Главный принцип":

```markdown
**Примечание о shared-utils**:
На текущей стадии разработки общий код минимален. Если в будущем потребуется общая функциональность (например, базовые утилиты, константы, общие middleware), используйте папку `shared-utils` и импортируйте из нее в каждый микросервис. Не создавайте зависимость на уровне requirements.txt без согласования с архитектором.
```

---

### Проблема 2.2: My Places не упоминается как готовая к интеграции

**Статус**: 🟡 ВАЖНО
**Текущее состояние**: Разработчики не знают что frontend уже 70% готов

**Что нужно добавить**: Новый раздел в "Реализованные сервисы" (после раздела "Интеграция Яндекс Карт"):

```markdown
### My Places Tab (Frontend) ⚠️ 70% Ready - Ожидает Backend API

**Статус**: Frontend UI полностью готов, ожидает реализации backend API endpoints

**Что реализовано в Frontend** ✅:

1. **Отображение карты**:
   - YandexMap компонент (файл: `frontend/components/YandexMap.tsx`)
   - Поддержка маркеров с иконками типов мест
   - Интерактивное взаимодействие (клики, hover)

2. **Список мест** (справа от карты):
   - Отображение 5 последних мест пользователя
   - Иконки типов мест (дикое/кэмпинг/база)
   - Статусы видимости (личное/публичное)
   - Скролл для больших списков

3. **Фильтры**:
   - По видимости: private/public/all
   - По типу места: wild/camping/resort
   - По типу подъезда: car/boat/foot
   - Сброс фильтров одной кнопкой

4. **Поиск**:
   - Поиск по названию места
   - Real-time фильтрация

5. **Детальная информация**:
   - Модальное окно с полными данными о месте
   - Отображение первого фото
   - Список видов рыбы (с иконками)
   - Статус видимости
   - Координаты и адрес
   - Типы подъезда и место

6. **Состояние для неавторизованных пользователей**:
   - Красивое сообщение "Войдите, чтобы добавлять места"
   - Кнопки для перехода на Login/Register

**Что требуется реализовать в Backend** ❌:

```python
# Places Service (Port 8002)
# Все endpoints должны требовать JWT аутентификацию

# 1. Получение списка мест пользователя
GET /api/v1/places/my?visibility=private&place_type=wild&search=озеро
Response 200: {
  "places": [{id, name, latitude, longitude, images, fish_types, ...}],
  "total": int,
  "page": int,
  "page_size": int
}

# 2. Создание места
POST /api/v1/places/my
Body: {
  "name": "Озеро Рыбное",
  "latitude": 55.75,
  "longitude": 37.61,
  "address": "г. Москва, ул. Примерная",
  "place_type": "wild",
  "access_type": "car",
  "fish_types": ["uuid1", "uuid2"],
  "equipment_types": ["uuid3"],
  "depth_min": 2,
  "depth_max": 5,
  "visibility": "private",
  "images": ["url1", "url2"],
  "description": "Описание"
}
Response 201: Created place object

# 3. Получение деталей места
GET /api/v1/places/my/:id
Response 200: {
  "id": "uuid",
  "name": "Озеро Рыбное",
  "fish_types": [
    {"id": "uuid", "name": "Щука", "icon": "🐟"},
    {"id": "uuid", "name": "Карась", "icon": "🐠"}
  ],
  ...
}

# 4. Редактирование места
PUT /api/v1/places/my/:id
Body: { ...same as POST... }
Response 200: Updated place object

# 5. Удаление места
DELETE /api/v1/places/my/:id
Response 204: No Content

# 6. Справочники (можно без аутентификации)
GET /api/v1/places/fish-types
Response 200: {
  "fish_types": [
    {"id": "uuid", "name": "Щука", "icon": "🐟", "category": "predatory"},
    ...
  ]
}

GET /api/v1/places/equipment-types
Response 200: {
  "equipment_types": [
    {"id": "uuid", "name": "Спиннинг", "category": "rod"},
    ...
  ]
}
```

**Frontend компоненты, которые обращаются к API** (hooks):
- `frontend/hooks/usePlaces.ts` - hook для работы с API мест
  - `getPlaces()` - получить список (используется)
  - `createPlace()` - создать место (используется)
  - `updatePlace()` - редактировать (не используется - требует реализации)
  - `deletePlace()` - удалить (не используется - требует реализации)

**Типы данных** (TypeScript):
- `frontend/types/place.ts` - интерфейс Place
  - Содержит все необходимые поля
  - ⚠️ Отсутствуют: seasonality, best_time, facilities, difficulty_level (из требований)

**Чек-лист для реализации backend**:
- [ ] Создать модели SQLAlchemy (Place, FishType, EquipmentType, FavoritePlace)
- [ ] Создать Pydantic schemas для валидации
- [ ] Реализовать CRUD endpoints (POST, GET, PUT, DELETE)
- [ ] Интегрировать Cloudinary для загрузки фотографий
- [ ] Реализовать геокодирование (reverse geocoding) для автозаполнения адреса
- [ ] Добавить кэширование справочников в Redis
- [ ] Написать unit тесты (≥80% покрытие)
- [ ] Добавить логирование в ELK
- [ ] Обновить Swagger/OpenAPI документацию

**Связанные документы**:
- Полные требования: `требования/Требования_Мои_Места.md`
- API спецификация: `требования/Требования_Мои_Места.md` раздел 5 (стр. 502-685)
```

---

### Проблема 2.3: Интеграция Яндекс Карт не упоминается в DEVELOPER_PROMPT

**Статус**: 🟡 ВАЖНО
**Текущее состояние**: Информация есть в DEVELOPER_PROMPT, но нужно уточнить текущий статус

**Что нужно изменить** (раздел "Интеграция Яндекс Карт", строка 408-440):

**БЫЛО** (оставить, это правильно описано):
```markdown
### Интеграция Яндекс Карт ✅

**Реализованный функционал:**
- Поле `city` в модели User для персонализации карты
- Сервис геокодирования с кэшированием в Redis (TTL: 1 час)
- Endpoint `GET /api/v1/maps/geocode` для получения координат города
- Компонент YandexMap для отображения карты во frontend
...
```

**ДОБАВИТЬ после этого раздела**:

```markdown
**Текущее использование в проекте**:

1. **Страница карты** (`/map`):
   - Отображение полной Яндекс карты
   - Геолокация пользователя (запрашивается разрешение)
   - Сохранение города в профиле пользователя

2. **Вкладка "Мои места"** (`/profile` → "My Places"):
   - Отображение всех мест пользователя на карте
   - Маркеры с иконками типов мест
   - Клик на маркер = открыть модальное окно с деталями
   - Клик на карту = начать добавление нового места

3. **Страница профиля**:
   - Изменение города пользователя в SettingsTab
   - Обновление field в БД через API

**Интеграция с Places Service** (planned):
- Reverse geocoding при клике на карту → автозаполнение адреса в форме создания места
- Кэширование координат мест в Redis для быстрого отображения на карте
- Клиентерирование маркеров при большом количестве мест (clustering)
```

---

### Проблема 2.4: Требования к health checks можно уточнить

**Статус**: 🟢 ХОРОШО (но можно улучшить)
**Текущее состояние**: Health checks описаны (стр. 476-488)

**Что нужно добавить дополнительно**: После раздела "Health Check обязательные требования":

```markdown
**Примеры проверки health checks:**

```bash
# Проверить все сервисы (используйте Makefile)
make health

# Или вручную (после docker-compose up -d)
curl http://localhost:8001/health   # Auth Service
curl http://localhost:8002/health   # Places Service
curl http://localhost:8003/health   # Reports Service
curl http://localhost:8004/health   # Booking Service
curl http://localhost:8005/health   # Shop Service
curl http://localhost:8006/health   # Email Service
```

**Что значит "healthy"**:
```json
{
  "status": "healthy",              // MUST BE "healthy"
  "service": "auth-service",        // Service name
  "version": "1.0.0"                // Version
}
```

**Статусы при проблемах**:
- `status: "unhealthy"` - критическая проблема (например, БД недоступна)
- `status: "degraded"` - частичная неработоспособность (например, redis недоступен, но сервис работает)

**Минимальные проверки в health endpoint**:
- ✅ Сервис запущен (всегда выполнено если endpoint доступен)
- ✅ БД доступна (для сервисов с БД): `await db.execute("SELECT 1")`
- ⚠️ Redis доступен (опционально): `await redis.ping()`
```

---

## 3. ДОПОЛНИТЕЛЬНО: НОВЫЙ ФАЙЛ - IMPLEMENTATION_STATUS.md

**Статус**: 🟢 РЕКОМЕНДУЕТСЯ
**Назначение**: Быстрая справка о текущем состоянии реализации

**Создать новый файл**: `IMPLEMENTATION_STATUS.md`

```markdown
# Статус реализации функциональности

**Last Updated**: 2024-02-17
**Актуально для версии**: 1.0.0

---

## Сводная таблица

| Компонент | Статус | Процент | Примечание |
|-----------|--------|---------|-----------|
| **Auth Service** | ✅ Готов | 100% | Полная реализация с JWT, email верификацией |
| **Email Service** | ✅ Готов | 100% | Интеграция с Yandex SMTP |
| **Frontend - Auth** | ✅ Готов | 100% | Регистрация, логин, восстановление пароля |
| **Frontend - Profile** | ✅ Готов | 90% | Все вкладки UI есть, часть требует backend |
| **Frontend - My Places Tab** | ⚠️ Ожидает | 70% | UI готов, требует backend API |
| **Яндекс Карты** | ✅ Готова | 100% | Интегрирована в Auth Service + Frontend |
| **Places Service** | 🚧 Планируется | 0% | Только заглушка с /health |
| **Reports Service** | 🚧 Планируется | 0% | Только заглушка с /health |
| **Booking Service** | 🚧 Планируется | 0% | Только заглушка с /health |
| **Shop Service** | 🚧 Планируется | 0% | Только заглушка с /health |
| **Database** | ✅ Схема | 100% | schema.sql полная, миграции требуют применения |

---

## Детальная информация по компонентам

### ✅ Завершено

#### Auth Service (100%)
- ✅ User регистрация с email верификацией
- ✅ JWT аутентификация
- ✅ Password reset
- ✅ Role-based access control (user/moderator/admin)
- ✅ Яндекс Карты интеграция (geocode endpoint + Redis cache)
- ✅ Unit тесты (~10 тестов)

#### Email Service (100%)
- ✅ SMTP интеграция (Yandex)
- ✅ Отправка кодов подтверждения
- ✅ Переключение отправки (dev mode)

#### Frontend Auth Pages (100%)
- ✅ /login - страница входа
- ✅ /register - регистрация
- ✅ /verify-email - подтверждение email
- ✅ /reset-password - восстановление пароля

#### Frontend Profile (90%)
- ✅ ProfileTab - просмотр/редактирование профиля
- ✅ SettingsTab - смена пароля, выбор города
- ✅ CartTab - UI (backend-less)
- ✅ OrdersTab - UI (backend-less)
- ✅ NotificationsTab - UI (backend-less)
- ✅ ReportsTab - UI (backend-less)
- ✅ BookingsTab - UI (backend-less)
- ⚠️ MyPlacesTab - 70% (UI готов, API требуется)

#### Яндекс Карты (100%)
- ✅ Endpoint: GET /api/v1/maps/geocode
- ✅ Redis кэширование (TTL: 1 час)
- ✅ Frontend компонент YandexMap
- ✅ Страница /map
- ✅ Интеграция в My Places Tab
- ✅ Поле city в User model
- ✅ Unit тесты для geocode service

---

### ⚠️ В процессе / Ожидает backend

#### Frontend My Places Tab (70%)

**✅ Готово**:
- Отображение карты (YandexMap)
- Список мест справа
- Поиск по названию
- Фильтры (видимость, тип, подъезд)
- Модальное окно деталей
- UI для неавторизованных пользователей

**❌ Требует backend API**:
- POST /api/v1/places/my - создание
- PUT /api/v1/places/my/:id - редактирование
- DELETE /api/v1/places/my/:id - удаление
- GET /api/v1/places/fish-types - справочник рыб
- GET /api/v1/places/equipment-types - справочник снастей
- Cloudinary интеграция для фотографий
- Reverse geocoding для автозаполнения адреса

**Файлы**:
- `frontend/app/profile/components/MyPlacesTab.tsx` (реализован)
- `frontend/hooks/usePlaces.ts` (требует доработки)
- `frontend/types/place.ts` (требует полнота полей)

**Dependencies**:
- Требует реализации Places Service backend

---

### 🚧 Планируется / Заглушка

#### Places Service (0% - заглушка)
- 🚧 Структура создана, содержит только /health endpoint
- ❌ Models, schemas, endpoints, CRUD - не реализованы
- 📋 Полные требования: `требования/Требования_Мои_Места.md`

#### Reports Service (0% - заглушка)
- 🚧 Только /health endpoint

#### Booking Service (0% - заглушка)
- 🚧 Только /health endpoint

#### Shop Service (0% - заглушка)
- 🚧 Только /health endpoint

---

## Очередь реализации (Рекомендуемая)

### Phase 1: My Places (High Priority) 🔴
```
1. ✅ Frontend UI (ГОТОВО)
2. ❌ Backend API endpoints (ТРЕБУЕТСЯ)
   - Models: Place, FishType, EquipmentType, FavoritePlace
   - CRUD endpoints
   - Validation schemas
   - Tests (≥80%)
3. ❌ Database migration script
4. ❌ Cloudinary integration
5. ❌ Reverse geocoding integration
Estimated: 2-3 недели
```

### Phase 2: Reports Service (Medium Priority) 🟡
```
1. API endpoints
2. Image upload (Cloudinary)
3. Comments & ratings
4. Tests
Estimated: 2 недели
```

### Phase 3: Booking Service (Medium Priority) 🟡
```
1. API endpoints
2. Stripe integration
3. Calendar/slots management
4. Tests
Estimated: 2-3 недели
```

### Phase 4: Shop Service (Low Priority) 🟢
```
1. Product catalog
2. Shopping cart
3. Stripe payment
4. Tests
Estimated: 2 недели
```

---

## Порты и доступ (Development)

| Сервис | Host Port | Container Port | Status | URL |
|--------|-----------|----------------|--------|-----|
| Frontend | 3000 | 3000 | ✅ | http://localhost:3000 |
| Auth | 8001 | 8000 | ✅ | http://localhost:8001 |
| Places | 8002 | 8001 | 🚧 | http://localhost:8002 |
| Reports | 8003 | 8002 | 🚧 | http://localhost:8003 |
| Booking | 8004 | 8003 | 🚧 | http://localhost:8004 |
| Shop | 8005 | 8004 | 🚧 | http://localhost:8005 |
| Email | 8006 | 8005 | ✅ | http://localhost:8006 |
| PostgreSQL | 5432 | 5432 | ✅ | localhost:5432 |
| Redis | 6379 | 6379 | ✅ | localhost:6379 |
| Kibana | 5601 | 5601 | ⚠️ | http://localhost:5601 (если запущен) |

---

## Команды для проверки статуса

```bash
# Проверить здоровье всех сервисов
make health

# Запустить все сервисы
make dev

# Запустить с логами ELK
make elk

# Просмотр логов
make dev-logs
make dev-logs S=auth-service

# Остановить
make dev-down
```

---

## Документация по функциям

| Функция | Документ | Статус |
|---------|----------|--------|
| Регистрация | `требования/UC-REG-001_Регистрация_пользователя.md` | ✅ Реализована |
| Яндекс Карты | `требования/требования_яндекс_карты.md` | ✅ Реализована |
| Мои места | `требования/Требования_Мои_Места.md` | ⚠️ Frontend готов |
| Все требования | `требования/` | 📋 Папка с требованиями |

---

## Как использовать этот документ

1. **Для разработчиков**: Быстрый поиск статуса компонента
2. **Для аналитиков**: Какие компоненты готовы, какие требуют работы
3. **Для планирования**: Очередь реализации и estimated сроки
4. **Для новичков**: Понимание current state проекта

---

**Обновляется при изменении статуса реализации**
```
```

---

## 4. КРАТКИЙ ЧЕК-ЛИСТ ПРИМЕНЕНИЯ РЕКОМЕНДАЦИЙ

### Приоритет 🔴 КРИТИЧЕСКИ ВАЖНО:

- [ ] Добавить раздел "Яндекс Карты" в SYSTEM_PROMPT.md (после Email Service)
- [ ] Добавить endpoint `/api/v1/maps/geocode` в список endpoints Auth Service
- [ ] Добавить раздел "My Places Tab" с информацией о 70% готовности

### Приоритет 🟡 ВАЖНО:

- [ ] Обновить описание вкладок профиля в SYSTEM_PROMPT.md
- [ ] Добавить раздел "My Places Tab (70% Ready)" в DEVELOPER_PROMPT.md
- [ ] Уточнить в DEVELOPER_PROMPT.md что shared-utils неиспользуется
- [ ] Добавить health checks примеры в DEVELOPER_PROMPT.md
- [ ] Создать файл IMPLEMENTATION_STATUS.md

### Приоритет 🟢 РЕКОМЕНДУЕТСЯ:

- [ ] Добавить примечание о дальнейшей разработке Places Service

---

## 5. ПОРЯДОК ПРИМЕНЕНИЯ

**Шаг 1**: Обновить SYSTEM_PROMPT.md (15 мин)
- Добавить раздел о Яндекс Картах
- Обновить endpoints Auth Service
- Обновить описание Pages

**Шаг 2**: Обновить DEVELOPER_PROMPT.md (15 мин)
- Добавить раздел о My Places Tab 70%
- Уточнить shared-utils
- Добавить примеры health checks

**Шаг 3**: Создать IMPLEMENTATION_STATUS.md (10 мин)
- Скопировать шаблон из раздела 3
- Проверить актуальность

**Итого**: ~40 мин на применение всех рекомендаций

---

## 6. РЕЗУЛЬТАТ ПОСЛЕ ПРИМЕНЕНИЯ

✅ **Промпты будут правильно отражать**:
- Текущее состояние реализации
- Что реально готово (✅), а что заглушка (🚧)
- Что ожидает какого-то компонента (⚠️)
- Где найти документацию

✅ **Разработчики смогут**:
- Быстро понять что готово, что нет
- Узнать о My Places 70% и требуемом API
- Найти информацию о Яндекс Картах в prompts
- Понять очередь реализации

✅ **Аналитики смогут**:
- Видеть какие функции требуют документирования
- Знать какие frontend компоненты готовы
- Планировать backend работу на основе готового UI

---

**Документ готов к внедрению**

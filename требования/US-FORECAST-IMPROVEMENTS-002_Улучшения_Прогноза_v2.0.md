# User Story: Улучшения прогноза клева v2.0

**ID**: US-FORECAST-IMPROVEMENTS-002
**Version**: 2.0
**Author**: Business/System Analyst
**Date**: 2026-02-18
**Статус**: ✅ Согласовано
**Дата согласования**: 2026-02-18

---

## История изменений

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2025-02-18 | Первоначальная версия UI улучшений |
| 2.0 | 2026-02-18 | Добавлены: новая цветовая схема, клик по дню, нетипичные рыбы |
| 2.0 | 2026-02-18 | Согласовано с заказчиком |

---

## 1. Обзор

### 1.1. Описание

Данный документ описывает улучшения в разделе "Прогноз клева":
1. Обновленная цветовая индикация с уникальными цветами для каждого уровня
2. Исправление логики прогноза на 3 дня (отсутствие 3-го дня для Москвы)
3. Перестроение прогноза при клике на день в multi_day_forecast
4. Функциональность добавления нетипичных рыб в прогноз

### 1.2. Бизнес-ценность

**Для пользователей**:
- Интуитивная цветовая индикация качества клева
- Полный прогноз на 3 дня вперед
- Интерактивный выбор дня для просмотра
- Возможность добавить рыбу для платных водоемов

**Для бизнеса**:
- Повышение вовлеченности пользователей
- Поддержка платных мест рыбалки
- Улучшение UX

---

## 2. User Stories

### US-1: Обновленная цветовая индикация

**As a** пользователь,
**I want to** видеть уникальный цвет для каждого уровня качества клева,
**So that** я могу мгновенно оценить прогноз визуально.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Acceptance Criteria

**AC1: Новая цветовая схема**
- **Given** отображается процент клева
- **When** bite_score находится в диапазоне
- **Then** применяются следующие цвета:

| Диапазон | Цвет фона (progress bar) | Цвет текста | Label |
|----------|--------------------------|-------------|-------|
| ≥80% | Зеленый `#22c55e` (`bg-green-500`) | `text-green-600` | Отлично |
| 65-79% | Желтый `#eab308` (`bg-yellow-500`) | `text-yellow-600` | Хорошо |
| 50-64% | Оранжевый `#f97316` (`bg-orange-500`) | `text-orange-600` | Умеренно |
| 35-49% | Красный светлый `#f87171` (`bg-red-400`) | `text-red-500` | Слабо |
| <35% | Красный темный `#dc2626` (`bg-red-600`) | `text-red-700` | Плохо |

**AC2: Применение во всех местах**
- **Given** прогноз отображается
- **When** показывается bite_score
- **Then** цветовая индикация применяется в:
  - Основной список рыб (ТОП клев сегодня)
  - Раскрытая карточка рыбы (по времени суток)
  - Прогноз на 3 дня (multi_day_forecast)

**AC3: Цвет работает в раскрытом состоянии**
- **Given** карточка рыбы раскрыта
- **When** отображаются прогнозы по времени суток
- **Then** каждый прогноз имеет правильный цвет progress bar

#### Технические детали

**Frontend**: Обновить функции в `frontend/types/forecast.ts`:

```typescript
export function getBiteScoreLabel(score: number): string {
  if (score >= 80) return 'Отлично';
  if (score >= 65) return 'Хорошо';
  if (score >= 50) return 'Умеренно';
  if (score >= 35) return 'Слабо';
  return 'Плохо';
}

export function getBiteScoreColor(score: number): string {
  if (score >= 80) return 'bg-green-500';      // #22c55e
  if (score >= 65) return 'bg-yellow-500';     // #eab308
  if (score >= 50) return 'bg-orange-500';     // #f97316
  if (score >= 35) return 'bg-red-400';        // #f87171
  return 'bg-red-600';                          // #dc2626
}

export function getBiteScoreTextColor(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score >= 65) return 'text-yellow-600';
  if (score >= 50) return 'text-orange-600';
  if (score >= 35) return 'text-red-500';
  return 'text-red-700';
}
```

---

### US-2: Исправление прогноза на 3 дня

**As a** пользователь,
**I want to** видеть прогноз на 3 дня вперед для всех регионов,
**So that** я могу планировать рыбалку на выходные.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Acceptance Criteria

**AC1: Три дня в прогнозе**
- **Given** выбран регион с погодными данными
- **When** загружается прогноз
- **Then** отображаются сегодня + 2 следующих дня (итого 3 дня)
- **And** каждый день кликабелен

**AC2: Проверка наличия данных**
- **Given** запрашивается прогноз
- **When** проверяется multi_day_forecast
- **Then** день добавляется в список только если есть WeatherData для этой даты

**AC3: Корректная логика формирования списка**
- **Given** сегодня 19.02.2026
- **When** формируется multi_day_forecast
- **Then** должны отображаться: 19.02 (сегодня), 20.02 (завтра), 21.02 (послезавтра)

#### Технические детали

**Backend** (`services/forecast-service/app/endpoints/forecast.py`):

Текущая логика (строки 336-353):
```python
multi_day = []
for i in range(1, 4):  # 1, 2, 3 - завтра, послезавтра, через 2 дня
    future_date = forecast_date + timedelta(days=i)
    # Проверка наличия погодных данных...
```

**Проблема**: Если нет данных для 3-го дня, он не отображается.

**Решение**: Убедиться что weather_collector собирает данные на 4 дня (сегодня + 3). Проверить:
1. Scheduler запускается и собирает данные
2. Данные для всех регионов присутствуют в БД

**Debug endpoint**: Добавить логирование количества найденных дней.

---

### US-3: Перестроение прогноза при клике на день

**As a** пользователь,
**I want to** кликнуть на день в прогнозе на 3 дня и увидеть детальный прогноз для этого дня,
**So that** я могу изучить прогноз на интересующий меня день.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Acceptance Criteria

**AC1: Кликабельные дни в прогнозе на 3 дня**
- **Given** отображается прогноз на 3 дня
- **When** я навожу курсор на день
- **Then** день подсвечивается (hover эффект)
- **And** курсор меняется на pointer

**AC2: Перестроение прогноза**
- **Given** я кликаю на день (например, 21.02)
- **When** запрос завершается
- **Then** весь прогноз обновляется на выбранную дату
- **And** заголовок показывает выбранную дату
- **And** список рыб пересчитывается
- **And** погода обновляется

**AC3: Визуальный индикатор выбранного дня**
- **Given** прогноз загружен для определенной даты
- **When** отображается multi_day_forecast
- **Then** выбранный день выделен (жирная рамка или фон)

**AC4: Возврат к сегодняшнему дню**
- **Given** выбран другой день
- **When** я кликаю на "Сегодня"
- **Then** прогноз возвращается к текущей дате

#### Технические детали

**Frontend** (`frontend/components/FishingForecast.tsx`):

```tsx
// Добавить состояние для выбранной даты
const [selectedDate, setSelectedDate] = useState<string | null>(null);

// Модифицировать loadForecast
const loadForecast = async (regionId: string, date?: string) => {
  setLoadingForecast(true);
  try {
    const response = await getForecast(regionId, date);
    setForecast(response);
    setSelectedDate(date || null);
  } catch (err) {
    console.error("Failed to load forecast:", err);
  } finally {
    setLoadingForecast(false);
  }
};

// Добавить обработчик клика на день
const handleDayClick = (date: string) => {
  if (selectedRegion) {
    loadForecast(selectedRegion.id, date);
  }
};
```

**UI изменения**:

```tsx
// В блоке multi_day_forecast
{forecast.multi_day_forecast && forecast.multi_day_forecast.length > 0 && (
  <div className="grid grid-cols-3 gap-2">
    {forecast.multi_day_forecast.map((dayForecast) => {
      const isSelected = selectedDate === dayForecast.date;
      return (
        <button
          key={dayForecast.date}
          onClick={() => handleDayClick(dayForecast.date)}
          className={`
            bg-gray-50 rounded-xl p-3 text-center transition-all
            hover:bg-blue-50 hover:ring-2 hover:ring-blue-300
            ${isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : ''}
          `}
        >
          {/* содержимое дня */}
        </button>
      );
    })}
  </div>
)}
```

---

### US-4: Добавление нетипичных рыб в прогноз

**As a** пользователь платного водоема,
**I want to** добавить нехарактерную для региона рыбу (например, форель) в свой прогноз,
**So that** я вижу прогноз клева для рыб в этом водоеме.

#### Priority
- [x] Medium

#### Actors
- [x] Зарегистрированный пользователь

#### Acceptance Criteria

**AC1: Кнопка добавления рыбы**
- **Given** я авторизован и смотрю прогноз региона
- **When** прокручиваю вниз списка рыб
- **Then** вижу кнопку "+ Добавить рыбу"

**AC2: Модальное окно выбора рыбы**
- **Given** я кликаю на "+ Добавить рыбу"
- **When** открывается модальное окно
- **Then** вижу:
  - Поле поиска по названию рыбы
  - Список всех рыб из базы
  - Индикатор типичности для региона

**AC3: Индикация типичности рыбы**
- **Given** в списке рыб рыба не типична для региона
- **When** отображается строка рыбы
- **Then** возле названия отображается иконка info (ℹ️)
- **And** при наведении появляется тултип "Не типична для данного региона"

**AC4: Добавление рыбы**
- **Given** я выбираю рыбу и кликаю "Добавить"
- **When** запрос завершается успешно
- **Then** рыба появляется в списке прогноза
- **And** прогноз рассчитывается на основе погодных данных региона
- **And** рыба отмечена как "добавленная" (можно удалить)

**AC5: Ограничение количества**
- **Given** у меня уже добавлено 3 нетипичных рыбы
- **When** я пытаюсь добавить еще одну
- **Then** вижу сообщение "Максимум 3 дополнительных рыбы для региона"
- **And** кнопка добавления неактивна

**AC6: Удаление добавленной рыбы**
- **Given** в списке есть добавленная мной рыба
- **When** я кликаю на иконку корзины
- **Then** рыба удаляется из моего списка
- **And** прогноз обновляется

**AC7: Только добавленные рыбы можно удалить**
- **Given** в списке есть типичные рыбы региона
- **When** я навожу на типичную рыбу
- **Then** иконка удаления НЕ отображается

**AC8: Сохранение в профиле**
- **Given** я добавил нетипичную рыбу
- **When** я захожу с другого устройства
- **Then** список добавленных рыб сохранен

#### Технические детали

**Backend - Database Changes**:

```sql
-- Таблица для хранения добавленных пользователем рыб
CREATE TABLE user_added_fish (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ограничение: одна рыба на пользователя+регион
    UNIQUE(user_id, fish_type_id, region_id)
);

-- Индекс для быстрого поиска
CREATE INDEX idx_user_added_fish_user_region ON user_added_fish(user_id, region_id);
```

**Backend - API Endpoints**:

```
POST /api/v1/forecast/{region_id}/custom-fish
Request: { "fish_type_id": "uuid" }
Response: { "success": true, "fish": {...} }

DELETE /api/v1/forecast/{region_id}/custom-fish/{fish_type_id}
Response: { "success": true }

GET /api/v1/forecast/{region_id}/custom-fish
Response: { "fish_types": [...] }
```

**Backend - Логика расчета**:

В `forecast.py` при формировании прогноза:
1. Получить список добавленных рыб для user_id + region_id
2. Для каждой добавленной рыбы:
   - Проверить наличие FishBiteSettings (если нет - использовать дефолтные)
   - Рассчитать прогноз на основе WeatherData региона
3. Добавить в общий список прогнозов с флагом `is_custom: true`

**Frontend - UI Components**:

```tsx
// Состояние для модального окна
const [showAddFishModal, setShowAddFishModal] = useState(false);
const [allFishTypes, setAllFishTypes] = useState<FishType[]>([]);
const [customFishIds, setCustomFishIds] = useState<string[]>([]);

// Кнопка добавления (авторизованные только)
{isAuthenticated && customFishIds.length < 3 && (
  <button
    onClick={() => setShowAddFishModal(true)}
    className="w-full mt-3 py-2 border-2 border-dashed border-gray-300 
               rounded-xl text-gray-500 hover:border-blue-400 hover:text-blue-600 
               transition flex items-center justify-center gap-2"
  >
    <Plus className="w-4 h-4" />
    Добавить рыбу
  </button>
)}
```

**Модальное окно**:

```tsx
<Modal open={showAddFishModal} onClose={() => setShowAddFishModal(false)}>
  <div className="p-4">
    <h3 className="font-bold mb-3">Добавить рыбу в прогноз</h3>
    
    <input
      type="text"
      placeholder="Поиск рыбы..."
      value={searchFish}
      onChange={(e) => setSearchFish(e.target.value)}
      className="w-full px-3 py-2 border rounded-lg mb-3"
    />
    
    <div className="max-h-60 overflow-y-auto">
      {filteredFishTypes.map((fish) => {
        const isTypical = typicalFishIds.includes(fish.id);
        const isAdded = customFishIds.includes(fish.id);
        
        return (
          <div
            key={fish.id}
            className="flex items-center justify-between p-2 hover:bg-gray-50 rounded"
          >
            <div className="flex items-center gap-2">
              <span>{fish.icon} {fish.name}</span>
              {!isTypical && (
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  <span className="hidden group-hover:inline">Не типична</span>
                </span>
              )}
            </div>
            
            <button
              onClick={() => handleAddFish(fish.id)}
              disabled={isAdded}
              className={isAdded ? "text-gray-400" : "text-blue-600 hover:text-blue-700"}
            >
              {isAdded ? "Добавлено" : "Добавить"}
            </button>
          </div>
        );
      })}
    </div>
  </div>
</Modal>
```

**Отображение добавленной рыбы**:

```tsx
// В карточке рыбы
<div className="flex items-center gap-3">
  <span className="text-2xl">{fish.icon}</span>
  <div>
    <div className="font-medium flex items-center gap-2">
      {fish.name}
      {fish.is_custom && (
        <>
          <Info className="w-3 h-3 text-gray-400" title="Не типична для региона" />
          <button
            onClick={() => handleRemoveFish(fish.id)}
            className="text-red-500 hover:text-red-600"
          >
            <X className="w-4 h-4" />
          </button>
        </>
      )}
    </div>
  </div>
</div>
```

---

## 3. Non-Functional Requirements

### 3.1. Performance
- **UI Response**: Клик на день < 100ms отклик
- **API Response**: Загрузка прогноза < 200ms
- **Modal Opening**: < 50ms

### 3.2. Security
- **Authentication**: Добавление/удаление рыб только для авторизованных
- **Authorization**: Пользователь может управлять только своими рыбами
- **Validation**: Максимум 3 рыбы на регион

### 3.3. UX
- **Hover effects**: Все кликабельные элементы подсвечиваются
- **Loading states**: Skeleton при загрузке
- **Error handling**: Понятные сообщения об ошибках

---

## 4. API Specification

### 4.1. GET /api/v1/forecast/{region_id}

**Changes**: Добавить поле `is_custom` в FishForecastResponse

```json
{
  "forecasts": [
    {
      "fish_type": {
        "id": "uuid",
        "name": "Форель",
        "icon": "🐟",
        "is_typical_for_region": false
      },
      "is_custom": true,
      "forecasts": [...]
    }
  ]
}
```

### 4.2. POST /api/v1/forecast/{region_id}/custom-fish

**Request**:
```json
{
  "fish_type_id": "uuid"
}
```

**Response 200**:
```json
{
  "success": true,
  "fish_type": {
    "id": "uuid",
    "name": "Форель",
    "icon": "🐟"
  }
}
```

**Response 400**:
```json
{
  "error": {
    "code": "LIMIT_EXCEEDED",
    "message": "Максимум 3 дополнительных рыбы для региона"
  }
}
```

### 4.3. DELETE /api/v1/forecast/{region_id}/custom-fish/{fish_type_id}

**Response 200**:
```json
{
  "success": true
}
```

**Response 404**:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Рыба не найдена в вашем списке"
  }
}
```

---

## 5. Database Schema Changes

### 5.1. New Table: user_added_fish

```sql
CREATE TABLE user_added_fish (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_fish_region UNIQUE(user_id, fish_type_id, region_id),
    CONSTRAINT max_fish_per_region CHECK (
        (SELECT COUNT(*) FROM user_added_fish uaf2 
         WHERE uaf2.user_id = user_added_fish.user_id 
         AND uaf2.region_id = user_added_fish.region_id) < 3
    )
);

CREATE INDEX idx_user_added_fish_user_region ON user_added_fish(user_id, region_id);
```

### 5.2. Migration Script

```sql
-- Migration: 005_add_user_custom_fish
-- Date: 2026-02-18

BEGIN;

CREATE TABLE IF NOT EXISTS user_added_fish (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fish_type_id UUID NOT NULL REFERENCES fish_types(id) ON DELETE CASCADE,
    region_id UUID NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_fish_region UNIQUE(user_id, fish_type_id, region_id)
);

CREATE INDEX IF NOT EXISTS idx_user_added_fish_user_region 
ON user_added_fish(user_id, region_id);

COMMIT;
```

### 5.3. Rollback Script

```sql
-- Rollback: 005_add_user_custom_fish
-- Date: 2026-02-18

BEGIN;

DROP INDEX IF EXISTS idx_user_added_fish_user_region;
DROP TABLE IF EXISTS user_added_fish;

COMMIT;
```

---

## 6. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Нет настроек для нетипичной рыбы | Medium | Medium | Использовать дефолтные FishBiteSettings |
| Превышение лимита API погоды | Low | High | Увеличить интервал scheduler |
| Некорректная работа timezone | Medium | Medium | Тестирование для разных регионов |
| Фликер UI при переключении дней | Low | Low | Optimistic UI update |

---

## 7. Dependencies

- Зависит от: `frontend/types/forecast.ts` - цветовые функции
- Зависит от: `frontend/components/FishingForecast.tsx` - основной компонент
- Зависит от: `services/forecast-service/app/endpoints/forecast.py` - API
- Зависит от: `services/forecast-service/app/scheduler.py` - сбор данных
- Блокирует: Новые фичи прогноза

---

## 8. Definition of Done

### US-1: Цветовая индикация
- [ ] Функции getBiteScoreColor/getBiteScoreTextColor обновлены
- [ ] Цвета применяются в списке рыб
- [ ] Цвета применяются в раскрытой карточке
- [ ] Цвета применяются в прогнозе на 3 дня

### US-2: Прогноз на 3 дня
- [ ] Проверена работа scheduler
- [ ] Данные собираются на 4 дня
- [ ] Multi_day_forecast содержит 3 записи

### US-3: Клик по дню
- [ ] Дни кликабельны
- [ ] Hover эффект работает
- [ ] Выбранный день подсвечен
- [ ] Прогноз перестраивается

### US-4: Нетипичные рыбы
- [ ] Таблица user_added_fish создана
- [ ] API endpoints работают
- [ ] Модальное окно добавления реализовано
- [ ] Индикатор типичности работает
- [ ] Удаление только добавленных рыб
- [ ] Лимит 3 рыбы на регион
- [ ] Сохранение в профиле

### Общие
- [ ] Unit тесты написаны
- [ ] Integration тесты написаны
- [ ] Документация обновлена

---

## 9. Definition of Ready

- [x] Требования собраны
- [x] User Stories соответствуют INVEST
- [x] Acceptance Criteria определены
- [x] API Specification описана
- [x] Database Schema описана
- [x] **Согласовано с заказчиком** (2026-02-18)
- [ ] **Передано разработчику**

---

## 10. Решения по согласованию

| Вопрос | Решение заказчика | Дата |
|--------|-------------------|------|
| Цветовая схема | Зеленый→Желтый→Оранжевый→Красный светлый→Красный темный | 2026-02-18 |
| Клик по дню | Перестраивать весь прогноз | 2026-02-18 |
| Добавление рыб | Кнопка "+ Добавить рыбу" → модальное окно | 2026-02-18 |
| Индикация типичности | Иконка info + тултип | 2026-02-18 |
| Максимум рыб | 3 нетипичных рыбы на регион | 2026-02-18 |
| Удаление рыб | Только добавленные пользователем | 2026-02-18 |
| Хранение списка | В профиле пользователя | 2026-02-18 |
| Прогноз на 3 дня | Только при наличии данных | 2026-02-18 |

---

**Документ создан**: 2026-02-18
**Согласовано**: 2026-02-18
**Статус**: ✅ Готов к передаче разработчику
**Следующий шаг**: Передача разработчику для реализации

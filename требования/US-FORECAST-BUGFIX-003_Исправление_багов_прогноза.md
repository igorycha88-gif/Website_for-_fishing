# User Story: Исправление багов прогноза клева

**ID**: US-FORECAST-BUGFIX-003
**Version**: 1.0
**Author**: Business/System Analyst
**Date**: 2026-02-18
**Статус**: ✅ Согласовано
**Дата согласования**: 2026-02-18

---

## История изменений

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-02-18 | Первоначальная версия. Исправление 4 багов прогноза |

---

## 1. Обзор

### 1.1. Описание

Данный документ описывает исправление критических багов в разделе "Прогноз клева":

1. **BUG-1**: Замена кнопок дней на виджет календаря с возможностью выбора любой даты
2. **BUG-2**: Исправление отображения цвета progress bar у топовых рыб
3. **BUG-3**: Расширение dropdown поиска региона при отсутствии прогноза
4. **BUG-4**: Исправление ошибки аутентификации при переключении регионов

### 1.2. Бизнес-ценность

**Для пользователей**:
- Возможность вернуться к текущему дню из любого состояния
- Просмотр исторических прогнозов за месяц
- Понятная индикация доступности прогноза на дату
- Корректная работа поиска регионов

**Для бизнеса**:
- Улучшение UX и удержания пользователей
- Снижение количества обращений в поддержку

---

## 2. User Stories

### US-1: Виджет календаря для выбора даты (BUG-1)

**As a** пользователь,
**I want to** выбирать дату прогноза из календаря с подсветкой дней,
**So that** я могу планировать рыбалку на любой день и возвращаться к текущей дате.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Acceptance Criteria

**AC1: Виджет календаря**
- **Given** я смотрю прогноз
- **When** хочу выбрать дату
- **Then** вижу виджет календаря (date picker style)
- **And** могу выбрать любую дату в диапазоне

**AC2: Подсветка дней с прогнозом**
- **Given** отображается календарь
- **When** день имеет прогноз
- **Then** день подсвечен цветом качества (зеленый/желтый/оранжевый по лучшему прогнозу)
- **And** дни без прогноза серые/недоступные для клика или показывают "Нет данных"

**AC3: Выбор текущей даты**
- **Given** выбран любой день
- **When** хочу вернуться к сегодня
- **Then** могу кликнуть на "Сегодня" или выбрать текущую дату в календаре

**AC4: Исторические данные**
- **Given** хочу посмотреть прошлый прогноз
- **When** выбираю дату за последние 30 дней
- **Then** получаю прогноз за эту дату (если есть данные)

**AC5: День без прогноза**
- **Given** выбираю день без прогноза
- **When** прогноз загружается
- **Then** вижу информационное сообщение "Нет прогноза на данный день"

**AC6: Диапазон доступных дат**
- **Given** отображается календарь
- **When** просматриваю доступные даты
- **Then** доступны:
  - Прошедшие: 30 дней назад от сегодня
  - Будущие: дни с погодными данными

#### Технические детали

**Frontend** (`frontend/components/FishingForecast.tsx`):

```tsx
import { Calendar } from "lucide-react";

// Новые состояния
const [showCalendar, setShowCalendar] = useState(false);
const [availableDates, setAvailableDates] = useState<string[]>([]);

// Получить цвет для дня
const getDayColor = (date: string): string | null => {
  const dayForecast = forecast?.multi_day_forecast?.find(d => d.date === date);
  if (!dayForecast?.best_fish?.[0]) return null;
  
  const score = dayForecast.best_fish[0].score;
  return getBiteScoreColor(score);
};

// Компонент календаря
<Popover open={showCalendar} onOpenChange={setShowCalendar}>
  <PopoverTrigger asChild>
    <Button variant="outline" className="w-full justify-start">
      <Calendar className="mr-2 h-4 w-4" />
      {selectedDate ? formatDate(selectedDate) : "Выберите дату"}
    </Button>
  </PopoverTrigger>
  <PopoverContent className="w-auto p-0">
    <CalendarComponent
      mode="single"
      selected={selectedDate ? new Date(selectedDate) : undefined}
      onSelect={(date) => {
        if (date && selectedRegion) {
          const dateStr = format(date, "yyyy-MM-dd");
          loadForecast(selectedRegion.id, dateStr);
        }
        setShowCalendar(false);
      }}
      disabled={(date) => {
        const minDate = subDays(new Date(), 30);
        const maxDate = addDays(new Date(), 3);
        return date < minDate || date > maxDate;
      }}
      modifiers={{
        hasForecast: availableDates.map(d => new Date(d))
      }}
      modifiersStyles={{
        hasForecast: { fontWeight: "bold" }
      }}
    />
  </PopoverContent>
</Popover>
```

**API Changes**:

Добавить endpoint для получения списка дат с прогнозом:

```
GET /api/v1/forecast/{region_id}/available-dates
Response: { "dates": ["2026-02-18", "2026-02-19", ...] }
```

**Или** расширить текущий ответ прогноза:

```json
{
  "available_dates": ["2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20"],
  "forecast_date": "2026-02-18",
  ...
}
```

---

### US-2: Цвет progress bar у топовых рыб (BUG-2)

**As a** пользователь,
**I want to** видеть цвет progress bar у всех рыб в списке,
**So that** я могу мгновенно оценить качество клева.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Acceptance Criteria

**AC1: Цвет у топовых рыб**
- **Given** отображается список топовых рыб (первые 4)
- **When** смотрю на progress bar
- **Then** вижу цвет в соответствии с bite_score

**AC2: Цвет у раскрытых рыб**
- **Given** раскрываю карточку рыбы
- **When** смотрю progress bar по времени суток
- **Then** каждый имеет правильный цвет

**AC3: Цвет в прогнозе на 3 дня**
- **Given** смотрю прогноз на несколько дней
- **When** отображается best_fish
- **Then** progress bar имеет правильный цвет

#### Технические детали

**Frontend**: Проверить использование `getBiteScoreColor()` в `FishingForecast.tsx`:

```tsx
// Строка ~565-569 - прогресс бар в основном списке
<div className="w-20">
  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
    <div
      className={`h-full ${getBiteScoreColor(avgScore)} transition-all duration-500`}
      style={{ width: `${avgScore}%` }}
    />
  </div>
</div>
```

**Проблема**: Проверить что `avgScore` корректно вычисляется через `getAverageScore()`.

**Fix**: Убедиться что функция вызывается и возвращает число:
```tsx
const avgScore = getAverageScore(fishForecast);
// avgScore должен быть числом 0-100
```

---

### US-3: Dropdown поиска региона (BUG-3)

**As a** пользователь,
**I want to** видеть результаты поиска региона,
**So that** я могу выбрать нужный регион.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Acceptance Criteria

**AC1: Видны результаты поиска**
- **Given** открываю dropdown региона
- **When** ввожу текст в поиск
- **Then** вижу результаты под полем поиска
- **And** список не обрезан

**AC2: Минимальная высота**
- **Given** регион не имеет прогноза
- **When** открываю dropdown
- **Then** минимальная высота dropdown 280px
- **And** работает scroll при большом количестве

**AC3: Сообщение "Регионы не найдены"**
- **Given** поиск не дал результатов
- **When** список пуст
- **Then** вижу сообщение "Регионы не найдены"

#### Технические детали

**Frontend** (`frontend/components/FishingForecast.tsx`):

Текущий код (строка ~329):
```tsx
className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-100 z-20 min-h-[280px] overflow-hidden"
```

**Fix**: Убедиться что `min-h-[280px]` применяется корректно и контент виден:

```tsx
<motion.div
  initial={{ opacity: 0, y: -10 }}
  animate={{ opacity: 1, y: 0 }}
  className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-100 z-20 overflow-hidden"
  style={{ minHeight: '280px' }}
>
  <div className="p-2 border-b border-gray-100">
    <input ... />
  </div>
  <div className="overflow-y-auto" style={{ maxHeight: '240px' }}>
    {filteredRegions.map(...)}
  </div>
</motion.div>
```

---

### US-4: Ошибка аутентификации при переключении регионов (BUG-4)

**As a** пользователь,
**I want to** переключаться между регионами без ошибок,
**So that** я могу свободно просматривать прогнозы.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь

#### Acceptance Criteria

**AC1: Переключение без ошибок**
- **Given** я переключаюсь с региона без прогноза на регион с прогнозом
- **When** загружается новый прогноз
- **Then** не вижу ошибку "Authentication required"

**AC2: Корректная обработка отсутствия token**
- **Given** token отсутствует или истек
- **When** вызывается getCustomFish
- **Then** запрос не выполняется
- **And** ошибка не отображается пользователю

**AC3: Загрузка кастомных рыб только при наличии данных**
- **Given** у региона нет прогноза
- **When** я авторизован
- **Then** запрос custom fish не выполняется или обрабатывается gracefully

#### Технические детали

**Проблема**: В `loadCustomFishData()` (строка ~162-174) вызывается API с token, но если регион не имеет прогноза, backend возвращает ошибку.

**Frontend** (`frontend/components/FishingForecast.tsx`):

```tsx
const loadCustomFishData = async () => {
  if (!selectedRegion || !isAuthenticated || !token) return;
  
  try {
    const [customResponse, allResponse] = await Promise.all([
      getCustomFish(selectedRegion.id, token),
      getAllFishTypes(selectedRegion.id, token),
    ]);
    setCustomFishIds(customResponse.fish_types.map((f) => f.fish_type.id));
    setAllFishTypes(allResponse.fish_types);
  } catch (err) {
    // Graceful degradation - не показывать ошибку пользователю
    console.error("Failed to load custom fish data:", err);
    // Опционально: сбросить состояния
    setCustomFishIds([]);
    setAllFishTypes([]);
  }
};
```

**Дополнительно**: Проверить что token валиден перед запросом:

```tsx
const loadCustomFishData = async () => {
  if (!selectedRegion || !isAuthenticated || !token) return;
  
  // Проверка что token не истек (если есть expiresIn)
  // Или просто обернуть в try-catch
  
  try {
    const [customResponse, allResponse] = await Promise.all([
      getCustomFish(selectedRegion.id, token).catch(() => ({ fish_types: [] })),
      getAllFishTypes(selectedRegion.id, token).catch(() => ({ fish_types: [] })),
    ]);
    // ...
  } catch (err) {
    console.error("Failed to load custom fish data:", err);
  }
};
```

**Backend**: Проверить endpoint `/custom-fish` - должен возвращать пустой список вместо 401 если пользователь не авторизован или данные недоступны.

---

## 3. Non-Functional Requirements

### 3.1. Performance
- **Calendar Opening**: < 100ms
- **Date Selection**: < 200ms для загрузки прогноза
- **Dropdown Opening**: < 50ms

### 3.2. UX
- **Visual Feedback**: Hover эффекты на всех кликабельных элементах
- **Error Handling**: Понятные сообщения без технических деталей
- **Loading States**: Skeleton/loading индикаторы

### 3.3. Compatibility
- **Mobile**: Календарь должен работать на мобильных устройствах
- **Touch**: Поддержка touch events для выбора даты

---

## 4. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Библиотека календаря несовместима | Low | Medium | Использовать стандартные решения (react-day-picker, radix-ui) |
| Исторические данные недоступны | Medium | Low | Показывать сообщение "Нет данных" |
| Проблемы с timezone | Medium | Medium | Тестирование для разных регионов |
| Token refresh race condition | Low | Medium | Добавить проверку валидности token |

---

## 5. Dependencies

- Зависит от: `frontend/components/FishingForecast.tsx` - основной компонент
- Зависит от: `frontend/types/forecast.ts` - цветовые функции
- Зависит от: `services/forecast-service/app/endpoints/forecast.py` - API
- Блокирует: Нет

---

## 6. Definition of Done

### US-1: Календарь
- [ ] Виджет календаря реализован
- [ ] Дни с прогнозом подсвечены цветом качества
- [ ] Можно выбрать прошедшую дату (30 дней)
- [ ] Сообщение "Нет прогноза" для дней без данных
- [ ] Кнопка "Сегодня" всегда доступна
- [ ] Mobile-friendly

### US-2: Цвет progress bar
- [ ] Цвет отображается у топовых рыб
- [ ] Цвет отображается у раскрытых рыб
- [ ] Цвет отображается в прогнозе на 3 дня

### US-3: Dropdown региона
- [ ] Результаты поиска видны
- [ ] Минимальная высота 280px
- [ ] Scroll работает

### US-4: Ошибка аутентификации
- [ ] Переключение регионов без ошибок
- [ ] Graceful degradation при отсутствии token
- [ ] Ошибки не показываются пользователю

### Общие
- [ ] Unit тесты написаны
- [ ] Manual testing пройден
- [ ] Документация обновлена

---

## 7. Definition of Ready

- [x] Требования собраны
- [x] User Stories соответствуют INVEST
- [x] Acceptance Criteria определены
- [x] **Согласовано с заказчиком** (2026-02-18)
- [ ] **Передано разработчику**

---

## 8. Решения по согласованию

| Вопрос | Решение заказчика | Дата |
|--------|-------------------|------|
| Стиль выбора даты | Виджет календаря (date picker) | 2026-02-18 |
| Подсветка дней | Цветом качества клева | 2026-02-18 |
| Глубина истории | 30 дней | 2026-02-18 |
| Высота dropdown региона | 280px + scroll | 2026-02-18 |

---

**Документ создан**: 2026-02-18
**Согласовано**: 2026-02-18
**Статус**: ✅ Готов к передаче разработчику
**Следующий шаг**: Передача разработчику для реализации

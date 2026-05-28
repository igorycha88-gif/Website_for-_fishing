# User Story: Исправление багов UI прогноза - Календарь и Фаза Луны

**ID**: US-FORECAST-UI-BUGFIX-004
**Version**: 1.1
**Author**: Business/System Analyst
**Date**: 2026-02-19
**Статус**: ✅ Согласовано (v1.1)
**Дата согласования**: 2026-02-19

---

## История изменений

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2026-02-19 | Первоначальная версия. Исправление 2 багов UI |
| 1.1 | 2026-02-19 | Изменено решение календаря: Portal/Overlay вместо cell-size |

---

## 1. Обзор

### 1.1. Описание

Данный документ описывает исправление багов в разделе "Прогноз клева":

1. **BUG-1**: Не отображаются числа в календаре при выборе даты
2. **BUG-2**: Фаза луны отображается без скобок, требуется добавить формат "(Растущая)" и tooltip

### 1.2. Бизнес-ценность

**Для пользователей**:
- Возможность корректно выбирать дату в календаре
- Понятная индикация фазы луны с дополнительной информацией

**Для бизнеса**:
- Улучшение UX и снижение фрустрации пользователей
- Повышение информативности прогноза

---

## 2. User Stories

### US-1: Отображение чисел в календаре (BUG-1)

**As a** пользователь,
**I want to** видеть числа в календаре при его открытии,
**So that** я могу выбрать нужную дату.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Problem Description

При клике на "Выбрать дату" открывается календарь (react-day-picker), но числа не видны - видно только название месяца и дни недели. Требуется оптимизировать размер контента под экран.

**Текущее поведение**: Числа в календаре не отображаются
**Ожидаемое поведение**: Все числа видны и доступны для выбора

#### Root Cause Analysis

**Файл**: `frontend/components/FishingForecast.tsx:728-862`

Текущая реализация:
- Календарь рендерится внутри контейнера с `position: relative`
- Dropdown календаря использует `position: absolute`
- Родительский контейнер может иметь `overflow: hidden` или ограниченную высоту

**Проблема**: Календарь не виден из-за ограничений родительского контейнера (overflow: hidden, фиксированная высота, или другие CSS ограничения).

**Решение**: Использовать React Portal для рендера календаря вне ограничений родительского контейнера.

#### Acceptance Criteria

**AC1: Календарь открывается через Portal**
- **Given** я кликаю на "Выбрать дату"
- **When** открывается календарь
- **Then** календарь рендерится в document.body через createPortal
- **And** календарь не ограничен родительским контейнером

**AC2: Видны все числа месяца**
- **Given** я открываю календарь
- **When** календарь отображается
- **Then** вижу все числа месяца
- **And** числа читаемые и кликабельные

**AC3: Backdrop и закрытие**
- **Given** календарь открыт
- **When** кликаю вне календаря
- **Then** календарь закрывается

**AC4: Адаптивность**
- **Given** открываю на мобильном устройстве
- **When** календарь отображается
- **Then** все элементы видны
- **And** можно выбрать дату

#### Технические детали

**Frontend** (`frontend/components/FishingForecast.tsx`):

**Решение: React Portal для календаря**

```tsx
import { createPortal } from 'react-dom';

// Внутри компонента FishingForecast:

const CalendarDropdown = () => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className="fixed inset-0 z-50"
    onClick={() => setShowCalendar(false)}
  >
    <motion.div
      className="fixed bg-white rounded-xl shadow-xl border border-gray-100 p-3"
      style={{
        top: calendarPosition.top,
        left: calendarPosition.left,
        minWidth: '280px'
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Содержимое календаря */}
    </motion.div>
  </motion.div>
);

// В JSX:
{showCalendar && createPortal(<CalendarDropdown />, document.body)}
```

**Альтернатива: Overlay с position fixed**

```tsx
{showCalendar && (
  <div className="fixed inset-0 z-50" onClick={() => setShowCalendar(false)}>
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="absolute bg-white rounded-xl shadow-xl border border-gray-100 p-4 z-50"
      style={{
        top: buttonRef.current?.getBoundingClientRect().bottom + 8,
        left: buttonRef.current?.getBoundingClientRect().left,
        minWidth: '300px'
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* DayPicker */}
    </motion.div>
  </div>
)}
```

**Необходимые изменения**:
1. Добавить `useRef` для кнопки календаря
2. Вычислять позицию dropdown на основе `getBoundingClientRect()`
3. Рендерить через `createPortal` в `document.body`
4. Добавить backdrop overlay для закрытия по клику вне календаря

---

### US-2: Отображение фазы луны в скобках с tooltip (BUG-2)

**As a** пользователь,
**I want to** видеть фазу луны в скобках с всплывающей подсказкой,
**So that** я понимаю текущую фазу и её влияние на клев.

#### Priority
- [x] High (MVP)

#### Actors
- [x] Зарегистрированный пользователь
- [x] Незарегистрированный посетитель

#### Problem Description

В блоке "Текущая погода" в разделе "Луна" фаза отображается без скобок. Требуется отображать в формате: `🌙 (Растущая)` с tooltip при наведении.

**Текущее поведение**: `Растущая` (без скобок)
**Ожидаемое поведение**: `🌙 (Растущая)` + tooltip

#### Root Cause Analysis

**Файл**: `frontend/components/FishingForecast.tsx:528-536`

Текущий код:
```tsx
<div className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2">
  <span className="text-lg">{getMoonPhaseLabel(forecast.weather.moon_phase).split(" ")[1] || "🌙"}</span>
  <div>
    <div className="text-xs text-gray-500">Луна</div>
    <div className="font-semibold text-gray-800 text-xs">
      {getMoonPhaseType(forecast.weather.moon_phase) || getMoonPhaseLabel(forecast.weather.moon_phase).split(" ")[0]}
    </div>
  </div>
</div>
```

Функция `getMoonPhaseType()` возвращает: `"Растущая"`, `"Убывающая"`, `"Полнолуние"`, `"Новолуние"`

#### Acceptance Criteria

**AC1: Фаза в скобках**
- **Given** отображается блок погоды
- **When** смотрю на раздел "Луна"
- **Then** вижу иконку луны
- **And** вижу фазу в скобках: `(Растущая)`, `(Убывающая)`, `(Полнолуние)`, `(Новолуние)`

**AC2: Tooltip при наведении**
- **Given** отображается фаза луны
- **When** навожу курсор на блок луны
- **Then** вижу всплывающую подсказку с полным описанием
- **And** подсказка содержит информацию о влиянии на клев

**AC3: Формат отображения**
- **Given** фаза луны = 0.3 (растущая)
- **When** отображается блок
- **Then** вижу: `🌓 (Растущая)`
- **And** tooltip: `Растущая луна. Благоприятно для хищной рыбы.`

**AC4: Все фазы корректны**
- **Given** разные фазы луны
- **When** отображается прогноз
- **Then** корректно отображаются:
  - Новолуние: `🌑 (Новолуние)`
  - Растущая: `🌒 (Растущая)` или `🌓 (Растущая)`
  - Полнолуние: `🌕 (Полнолуние)`
  - Убывающая: `🌖 (Убывающая)` или `🌗 (Убывающая)`

#### Технические детали

**Frontend** (`frontend/components/FishingForecast.tsx`):

```tsx
// Добавить функцию для tooltip
const getMoonPhaseTooltip = (phase: number | null): string => {
  if (phase === null) return '';
  
  const type = getMoonPhaseType(phase);
  
  const tooltips: Record<string, string> = {
    'Новолуние': '🌑 Новолуние. Хорошее время для ночной рыбалки. Рыба активна.',
    'Растущая': '🌒 Растущая луна. Благоприятно для хищной рыбы.',
    'Полнолуние': '🌕 Полнолуние. Рыба может быть пассивной. Лучше рыбачить утром.',
    'Убывающая': '🌗 Убывающая луна. Хороший клев белой рыбы.',
  };
  
  return tooltips[type] || '';
};

// Обновить компонент
<div 
  className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2 cursor-help"
  title={getMoonPhaseTooltip(forecast.weather.moon_phase)}
>
  <span className="text-lg">{getMoonPhaseLabel(forecast.weather.moon_phase).split(" ")[1] || "🌙"}</span>
  <div>
    <div className="text-xs text-gray-500">Луна</div>
    <div className="font-semibold text-gray-800 text-xs">
      ({getMoonPhaseType(forecast.weather.moon_phase) || '—'})
    </div>
  </div>
</div>
```

**Или использовать radix-ui tooltip для лучшего UX**:

```tsx
import * as Tooltip from '@radix-ui/react-tooltip';

<Tooltip.Provider>
  <Tooltip.Root>
    <Tooltip.Trigger asChild>
      <div className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2 cursor-help">
        <span className="text-lg">{getMoonPhaseLabel(forecast.weather.moon_phase).split(" ")[1] || "🌙"}</span>
        <div>
          <div className="text-xs text-gray-500">Луна</div>
          <div className="font-semibold text-gray-800 text-xs">
            ({getMoonPhaseType(forecast.weather.moon_phase) || '—'})
          </div>
        </div>
      </div>
    </Tooltip.Trigger>
    <Tooltip.Portal>
      <Tooltip.Content
        className="bg-gray-900 text-white px-3 py-2 rounded-lg text-sm max-w-xs z-50"
        sideOffset={5}
      >
        {getMoonPhaseTooltip(forecast.weather.moon_phase)}
        <Tooltip.Arrow className="fill-gray-900" />
      </Tooltip.Content>
    </Tooltip.Portal>
  </Tooltip.Root>
</Tooltip.Provider>
```

**Типы** (`frontend/types/forecast.ts`):

Добавить функцию tooltip:

```typescript
export function getMoonPhaseTooltip(phase: number | null): string {
  if (phase === null) return '';
  
  const type = getMoonPhaseType(phase);
  
  const tooltips: Record<string, string> = {
    'Новолуние': '🌑 Новолуние. Хорошее время для ночной рыбалки.',
    'Растущая': '🌒 Растущая луна. Благоприятно для хищной рыбы.',
    'Полнолуние': '🌕 Полнолуние. Рыба может быть пассивной.',
    'Убывающая': '🌗 Убывающая луна. Хороший клев белой рыбы.',
  };
  
  return tooltips[type] || '';
}
```

---

## 3. Non-Functional Requirements

### 3.1. Performance
- **Calendar Rendering**: < 100ms
- **Tooltip Display**: < 50ms
- **Portal Mount**: < 50ms

### 3.2. UX
- **Visual Feedback**: Hover эффекты на tooltip
- **Accessibility**: Tooltip доступен с клавиатуры (focus)
- **Mobile**: Tooltip работает на touch устройствах (tap to show)
- **Backdrop**: Закрытие календаря по клику вне области

### 3.3. Compatibility
- **Browsers**: Chrome, Firefox, Safari, Edge (последние 2 версии)
- **Mobile**: iOS Safari, Chrome Android
- **SSR**: Portal корректно работает с Next.js SSR

---

## 4. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Portal рендерит в body, возможен SSR issue | Low | Medium | Добавить проверку `typeof window !== 'undefined'` |
| Позиция календаря некорректна при scroll | Medium | Medium | Добавить обработчик scroll для обновления позиции или использовать fixed позиционирование |
| Tooltip не работает на мобильных | Medium | Low | Добавить tap-обработчик для мобильных |
| Backdrop не закрывает при быстром клике | Low | Low | Добавить setTimeout для предотвращения двойного клика |

---

## 5. Dependencies

- Зависит от: `frontend/components/FishingForecast.tsx` - основной компонент
- Зависит от: `frontend/types/forecast.ts` - функции для фазы луны
- Опционально: `@radix-ui/react-tooltip` - для продвинутого tooltip
- Блокирует: Нет

---

## 6. Definition of Done

### US-1: Календарь
- [ ] Календарь открывается через Portal (вне родительского контейнера)
- [ ] Все числа в календаре видны
- [ ] Все ячейки кликабельные
- [ ] Название месяца и дни недели видны
- [ ] Работает на мобильных устройствах
- [ ] Закрытие по клику вне календаря (backdrop)
- [ ] Позиционирование корректно при scroll/resize

### US-2: Фаза луны
- [ ] Фаза отображается в скобках
- [ ] Tooltip появляется при наведении
- [ ] Tooltip содержит полезную информацию
- [ ] Работает на мобильных (tap to show)
- [ ] Все 4 фазы корректно отображаются

### Общие
- [ ] Ручное тестирование пройдено
- [ ] Проверено на разных браузерах
- [ ] Проверено на мобильных устройствах

---

## 7. Definition of Ready

- [x] Требования собраны
- [x] User Stories соответствуют INVEST
- [x] Acceptance Criteria определены
- [x] **Согласовано с заказчиком** (2026-02-19)
- [ ] **Передано разработчику**

---

## 8. Решения по согласованию

| Вопрос | Решение заказчика | Дата |
|--------|-------------------|------|
| Подход к исправлению календаря | **Portal/Overlay** - рендер через React Portal в document.body | 2026-02-19 |
| Формат отображения фазы луны | `🌙 (Растущая)` - иконка + фаза в скобках | 2026-02-19 |
| Tooltip для фазы луны | Да, добавить всплывающую подсказку | 2026-02-19 |
| Backend moon_phase = null | Текущее решение достаточно - показывать "—" при null | 2026-02-19 |

---

## 9. Описание изменений

### 9.1. Календарь (BUG-1)

**Файлы для изменения**:
- `frontend/components/FishingForecast.tsx` - компонент календаря

**Изменения**:
1. Добавить `import { createPortal } from 'react-dom'`
2. Добавить `useRef` для кнопки открытия календаря
3. Добавить состояние `calendarPosition` для хранения позиции dropdown
4. Переписать рендер календаря через `createPortal` в `document.body`
5. Добавить backdrop overlay для закрытия по клику вне
6. Вычислять позицию через `getBoundingClientRect()`

### 9.2. Фаза луны (BUG-2)

**Файлы для изменения**:
- `frontend/components/FishingForecast.tsx` - компонент отображения луны
- `frontend/types/forecast.ts` - добавить функцию `getMoonPhaseTooltip`

**Изменения**:
1. Добавить скобки вокруг фазы: `({getMoonPhaseType(...)})`
2. Добавить функцию `getMoonPhaseTooltip()` в types/forecast.ts
3. Добавить tooltip (native title или radix-ui) к блоку луны

---

**Документ создан**: 2026-02-19
**Обновлен**: 2026-02-19 (v1.1 - Portal решение)
**Согласовано**: 2026-02-19 (v1.1)
**Статус**: ✅ Готов к передаче разработчику
**Следующий шаг**: Передача разработчику для реализации

# ЧТЗ: Детализация расчёта прогноза клева

## ID: US-FORECAST-CALC-DETAILS-001
## Статус: В работе
## Маршрут: Аналитик → Разработчик → Тестировщик → DevOps
## Приоритет: Средний

---

## 1. Описание задачи

В раскрытой карточке рыбы (ForecastFactorBreakdown) отобразить все промежуточные показатели формулы расчёта прогноза клева, чтобы пользователь видел, как именно из 8 факторов складывается итоговый балл.

## 2. Контекст

Бэкенд (`forecast_calculation.py`) вычисляет `bite_score` по формуле:
```
base = geometric_mean(temp_score, pressure_score)
bite_score = base * solunar_synergy * temp_pressure_synergy * stability_mult
           * (time_adjusted / 100) * wind_cap * precip_cap
           * uv_cap * turbidity_cap * water_level_cap
           * phase_mult * season_mult
```

Сейчас API возвращает только 8 под-баллов и итоговый bite_score. Промежуточные множители НЕ возвращаются.

## 3. Критерии приёмки

### AC-1: Backend — расширенный ответ
- `calculate_bite_score()` возвращает `calculation_details` dict с полями:
  - `base` — геометрическое среднее температуры и давления
  - `solunar_synergy` — синергия луны и давления
  - `temp_pressure_synergy` — синергия температуры и давления
  - `stability_mult` — множитель стабильности давления
  - `time_adjusted` — балл времени суток (с solunar бонусом)
  - `wind_cap` — ограничение ветра (wind_score / 100)
  - `precip_cap` — ограничение осадков (precip_score / 100)
  - `uv_cap` — ограничение УФ с учётом чувствительности
  - `turbidity_cap` — ограничение мутности
  - `water_level_cap` — ограничение уровня воды с учётом чувствительности
  - `phase_mult` — множитель нерестовой фазы
  - `season_mult` — множитель сезона
- Pydantic-схема `TimeOfDayForecast` включает `calculation_details` (Optional)

### AC-2: Frontend — типы
- `TimeOfDayForecast` в `types/forecast.ts` включает `calculation_details`

### AC-3: Frontend — отображение
- В `ForecastFactorBreakdown` после сетки 8 факторов добавлена секция «Формула расчёта»
- Показана пошаговая формула: каждый множитель с значением и визуальной полоской
- Цветовое кодирование: множитель >= 1.0 = зелёный, 0.8-0.99 = жёлтый, < 0.8 = красный
- Финальная строка: «Итого: X%»

### AC-4: Нет данных
- Если `calculation_details = null`, секция формулы не отображается

## 4. Файлы для изменения

| Файл | Изменение |
|------|-----------|
| `services/forecast-service/app/services/forecast_calculation.py` | Добавить calculation_details в return |
| `services/forecast-service/app/schemas/forecast.py` | Добавить CalculationDetails + поле в TimeOfDayForecast |
| `services/forecast-service/app/endpoints/forecast.py` | Передать calculation_details в ответ |
| `frontend/types/forecast.ts` | Добавить CalculationDetails тип |
| `frontend/components/forecast/ForecastFactorBreakdown.tsx` | Добавить секцию формулы |

## 5. Декомпозиция

- TASK-BCK-001: Добавить calculation_details в calculate_bite_score и схему
- TASK-FRT-001: Обновить типы и ForecastFactorBreakdown

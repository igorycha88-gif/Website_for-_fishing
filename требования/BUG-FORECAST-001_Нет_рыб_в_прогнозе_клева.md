# ЧТЗ: Исправление отсутствия рыб в прогнозе клева

## Версия: 1.0
## Дата: 2026-06-09
## Приоритет: Critical
## Статус: Согласовано

---

## Маршрутизация

**Архитектор:** НЕ ТРЕБУЕТСЯ (баг-фикс, исправление логики сидирования)
**Исполнитель:** Разработчик
**Обоснование:** Исправление race condition при сидировании + добавление недостающих данных

---

## 1. Описание проблемы

На проде нет доступных рыб для прогноза клева. Прогноз не строится.

### Корневые причины:

1. **Race condition**: `forecast-service` и `places-service` стартуют одновременно (оба ждут только `postgres:healthy`). Когда forecast-service пытается сидировать `fish_bite_settings`, таблица `fish_types` ещё пуста — все 19 записей молча пропускаются.

2. **Блочная проверка идемпотентности**: `seed_fish_bite_settings()` проверяет `SELECT LIMIT 1` — если есть хоть одна запись, пропускает всё. Это не даёт восстановить частично сидированные данные.

3. **Нет retry-механизма**: При неудачном сидировании сервис продолжает работать с пустой таблицей.

4. **7 видов рыб без bite settings**: Линь, Густера, Красноперка, Угорь, Стерлядь, Белуга, Осётр — есть в `fish_types`, но не имеют `fish_bite_settings`, поэтому никогда не появятся в прогнозе.

---

## 2. Критерии приёмки

- [ ] forecast-service зависит от places-service в docker-compose.dev.yml
- [ ] seed_fish_bite_settings использует per-fish идемпотентность
- [ ] Добавлены bite settings для 7 недостающих рыб (Линь, Густера, Красноперка, Угорь, Стерлядь, Белуга, Осётр)
- [ ] Добавлен retry-механизм при неудачном сидировании (ждёт появления fish_types)
- [ ] GET /api/v1/forecast/{region_id} возвращает список рыб с прогнозами
- [ ] Все автотесты проходят

---

## 3. Декомпозиция задач

### TASK-INF-001: Добавить depends_on places-service
- Файл: `docker-compose.dev.yml`
- Добавить `places-service: condition: service_started` в depends_on forecast-service

### TASK-BCK-001: Per-fish идемпотентность seed_fish_bite_settings
- Файл: `services/forecast-service/app/seed_fish_settings.py`
- Заменить блочный `SELECT LIMIT 1` на per-fish проверку по `fish_type_id`

### TASK-BCK-002: Добавить bite settings для 7 недостающих рыб
- Файл: `services/forecast-service/app/seed_fish_settings.py`
- Добавить данные для: Линь, Густера, Красноперка, Угорь, Стерлядь, Белуга, Осётр

### TASK-BCK-003: Retry-механизм при seeding
- Файл: `services/forecast-service/app/seed_fish_settings.py`
- Добавить retry loop с задержкой если fish_type не найден

---

## 4. Новые bite settings для недостающих рыб

| Рыба | Категория | region_codes | Особенности |
|------|-----------|-------------|-------------|
| Линь | Peaceful | [] (все регионы) | Теплолюбивый, нерест V-VI |
| Густера | Peaceful | [] (все регионы) | Холодостойкая, нерест V-VI |
| Краснопёрка | Peaceful | [] (все регионы) | Теплолюбивая, нерст IV-V |
| Угорь | Commercial | ["KLG", "LEN", "PSK", "NVG", "TVE", "YAR", "VLA", "KRS", "KOS"] | Проходной, нерст в Саргассовом море (нет spawn) |
| Стерлядь | Commercial | ["VOL", "AST", "SAR", "SAM", "PER", "TOM", "NVS", "KEM"] | Осётровые, нерст IV-VI |
| Белуга | Commercial | ["AST", "VGG", "ROS", "KDA"] | Крупный осётр, нерст III-V |
| Осётр | Commercial | ["AST", "VGG", "ROS", "KDA", "SAR"] | Русский осётр, нерст IV-VI |

# Руководство по безопасным изменениям конфигураций

## ПРИНЦИПЫ

### 1. Правило "Изменяй одно - тестируй всё"
Ни одно изменение не вносится без проверки:
- Всегда проверяйте цепочку зависимостей
- Изменения в одном файле могут сломать другие
- Тестируйте весь функционал, а не только новый

### 2. Проверка тройки конфигурации
Перед изменением сервиса ВСЕГДА проверяйте:

```
Dockerfile → docker-compose.yml → Реальное поведение
     ↓              ↓                    ↓
  CMD/PORT     ports: HOST:CONTAINER   docker ps
```

**Чек-лист:**
- [ ] Какой порт указан в `CMD ["--port", "XXXX"]` Dockerfile?
- [ ] Какой порт мапится в docker-compose `ports: ["HOST:CONTAINER"]`?
- [ ] Совпадает ли `CONTAINER` порт из docker-compose с `--port` из CMD?
- [ ] Свободен ли `HOST` порт? Нет ли конфликтов с другими сервисами?

### 3. Формат маппинга портов Docker Compose
```
ports:
  - "HOST:CONTAINER"  # формат: порт на хосте:порт в контейнере
  - "8001:8000"       # порт 8000 внутри → порт 8001 снаружи
```

**ПРАВИЛО:** PORT в docker-compose.CONTAINER ДОЛЖЕН совпадать с PORT в Dockerfile.CMD

### 4. Порядок изменений конфигураций

**Шаг 1: Анализ до изменений**
```bash
# Проверьте текущее состояние
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml logs service-name --tail 20
```

**Шаг 2: Изменение конфигурации**
```bash
# Измените только то, что нужно
# Не меняйте лишние параметры "на всякий случай"
```

**Шаг 3: Проверка соответствия**
```bash
# Проверьте соответствие Dockerfile и docker-compose.yml
grep "CMD.*--port" services/*/Dockerfile
grep "ports:" docker-compose.dev.yml -A 2
```

**Шаг 4: Перезапуск сервиса**
```bash
docker-compose -f docker-compose.dev.yml up -d --build service-name
```

**Шаг 5: Проверка портов**
```bash
# Проверьте, что сервис слушает правильный порт
docker-compose -f docker-compose.dev.yml ps service-name

# Проверьте, что порт мапится корректно
netstat -tuln | grep 8001  # или ss -tuln | grep 8001
```

**Шаг 6: Тестирование API**
```bash
# Тест напрямую
curl http://localhost:HOST_PORT/api/v1/endpoint

# Тест внутри контейнера
docker exec container_name python -c "import urllib.request; urllib.request.urlopen('http://localhost:CONTAINER_PORT/api/v1/endpoint')"
```

**Шаг 7: Проверка логов**
```bash
docker-compose -f docker-compose.dev.yml logs service-name --tail 50
```

**Шаг 8: Тестирование через фронтенд**
```bash
# Проверьте, что фронтенд может обращаться к API
curl http://localhost:3000
```

### 5. Правило изоляции изменений

**При работе с НЕЗАВИСИМЫМ функционалом (например, карты):**
- [ ] Не меняйте конфигурацию существующих сервисов
- [ ] Добавляйте новые зависимости в requirements.txt/Dockerfile
- [ ] Не меняйте порты запуска существующих сервисов
- [ ] Не меняйте docker-compose.yml для других сервисов

**ПРИМЕР:**
```
❌ ПЛОХО:
- Изменяю auth-service порт 8001:8000 → 8001:8001
- Изменяю places-service порт 8002:8000 → 8002:8001
- Это "ковровой подход" - меняю всё подряд

✅ ХОРОШО:
- Добавляю новый компонент YandexMap.tsx
- Добавляю PlacePicker.tsx
- Изменяю MyPlacesTab.tsx
- НЕ трогаю auth-service, places-service конфиги
```

### 6. Таблица соответствия портов

| Сервис | Dockerfile PORT | docker-compose HOST | docker-compose CONTAINER | URL снаружи |
|--------|----------------|---------------------|--------------------------|-------------|
| auth-service | 8000 | 8001 | 8000 | http://localhost:8001 |
| places-service | 8000 | 8002 | 8000 | http://localhost:8002 |
| email-service | 8005 | 8006 | 8005 | http://localhost:8006 |
| frontend | 3000 | 3000 | 3000 | http://localhost:3000 |

**ПРАВИЛО:** Dockerfile.PORT = docker-compose.CONTAINER

### 7. Примеры ошибок и как их избежать

**ОШИБКА 1: Неверный порт контейнера**
```yaml
# ❌ ПЛОХО
ports:
  - "8001:8001"  # Dockerfile имеет --port 8000

# ✅ ХОРОШО
ports:
  - "8001:8000"  # Совпадает с Dockerfile CMD
```

**ОШИБКА 2: Конфликт портов на хосте**
```yaml
# ❌ ПЛОХО
auth-service:
  ports: ["8001:8000"]
places-service:
  ports: ["8001:8000"]  # Конфликт!

# ✅ ХОРОШО
auth-service:
  ports: ["8001:8000"]
places-service:
  ports: ["8002:8000"]  # Разные порты на хосте
```

**ОШИБКА 3: Изменение конфигурации без проверки**
```bash
# ❌ ПЛОХО
# Меняю docker-compose.yml сразу для всех сервисов
# Не тестирую каждый отдельно
docker-compose up -d --build

# ✅ ХОРОШО
# Меняю один сервис
docker-compose up -d --build auth-service
# Проверяю, работает ли
curl http://localhost:8001/api/v1/auth/register
# Только потом меняю следующий
```

### 8. Чек-лист перед коммитом

Перед созданием git commit проверьте:

**Конфигурации:**
- [ ] Все Dockerfile CMD порты совпадают с docker-compose CONTAINER портами
- [ ] Нет конфликтов HOST портов между сервисами
- [ ] Все сервисы запущены: `docker-compose ps`
- [ ] Нет ошибок в логах: `docker-compose logs`

**Тестирование:**
- [ ] API endpoints работают через curl
- [ ] Фронтенд загружается: `curl http://localhost:3000`
- [ ] Критичные функции работают (регистрация, авторизация, новые фичи)
- [ ] Нет ошибок в браузере console
- [ ] Нет ошибок в сервисных логах

**Код:**
- [ ] Новый код следует паттернам проекта
- [ ] Нет hardcoded значений (используются env vars)
- [ ] Логи добавлены для ключевых операций

### 9. Команды для диагностики

**Проверить, что сервис слушает:**
```bash
docker exec container_name netstat -tulpn  # если netstat доступен
docker exec container_name ss -tulpn
```

**Проверить порт внутри контейнера:**
```bash
docker exec container_name python -c "import urllib.request; urllib.request.urlopen('http://localhost:PORT/')"
```

**Проверить порт снаружи:**
```bash
curl -v http://localhost:PORT/
```

**Проверить docker-compose конфиг:**
```bash
docker-compose -f docker-compose.dev.yml config
```

## ГЛАВНЫЕ ПРАВИЛА

1. **НИКОГДА** не меняйте конфигурацию без понимания цепочки зависимостей
2. **ВСЕГДА** проверяйте Dockerfile.PORT = docker-compose.CONTAINER
3. **ВСЕГДА** тестируйте сервис отдельно перед интеграцией
4. **НИКОГДА** не меняйте конфигурацию существующих сервисов при разработке нового функционала
5. **ВСЕГДА** используйте пошаговый подход: изменение → проверка → тест → следующее изменение

## ЧТО ДЕЛАТЬ, ЕСЛИ ОШИБКА

1. **Не паникуйте** - проверьте логи сервиса
2. **Проверьте порты** - Dockerfile.PORT vs docker-compose.CONTAINER
3. **Тестируйте изнутри** - docker exec + python
4. **Тестируйте снаружи** - curl localhost
5. **Сравните с рабочим** - посмотрите другие сервисы

## ЗАПОМНИТЬ

```
Dockerfile CMD → PORT (внутри контейнера)
docker-compose CONTAINER → должен совпадать с CMD PORT
docker-compose HOST → порт для доступа снаружи
```

```
CMD ["--port", "8000"]  ←→  ports: ["8001:8000"]
               ↑                           ↑           ↑
          Dockerfile                  CONTAINER    HOST
                                         =         !=
                                    совпадает!

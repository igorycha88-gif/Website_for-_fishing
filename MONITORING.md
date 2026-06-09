# ELK Stack для FishMap

## Обзор

ELK Stack (Elasticsearch, Logstash, Kibana) используется для централизованного сбора, анализа и визуализации логов всех микросервисов FishMap.

## Установка и запуск

### Требования
- Docker и Docker Compose установлены
- Минимум 4GB RAM для запуска ELK Stack

### Запуск

```bash
# Автоматическая установка и запуск
bash scripts/setup-elk.sh

# Или вручную
docker-compose -f docker-compose.elk.yml up -d
```

### Доступ к сервисам

| Сервис | URL | Описание |
|--------|-----|----------|
| Kibana | http://localhost:5601 | Визуализация и анализ логов |
| Elasticsearch | http://localhost:9200 | Хранение и поиск логов |
| Logstash | http://localhost:9600 | Сбор и обработка логов |

## Настройка Kibana

После запуска:

1. Откройте http://localhost:5601
2. Перейдите в Management > Stack Management > Index Patterns
3. Создайте индексный паттерн: `fishmap-logs-*`
4. Выберите поле времени: `@timestamp`

## Структура логов

Логи отправляются в формате JSON и индексируются по паттерну:
`fishmap-logs-{service_name}-{YYYY.MM.dd}`

### Обязательные поля лога

```json
{
  "service": "email-service",
  "level": "info|error|warning",
  "timestamp": "2024-02-11T12:00:00Z",
  "message": "Sending verification email",
  "to_email": "user@example.com",
  "username": "john_doe"
}
```

## Интеграция с сервисами

Каждый микросервис должен:

1. Добавить `structlog>=24.1.0` в `requirements.txt`
2. Создать `app/core/logging_config.py`
3. Создать `app/middleware/logging.py`
4. Настроить отправку логов на `http://logstash:5000`

### Пример использования

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

logger.info(
    "Sending verification email",
    to_email="user@example.com",
    username="john"
)

logger.error(
    "Failed to send email",
    to_email="user@example.com",
    error=str(e),
    exc_info=True
)
```

## Полезные запросы Kibana

### Все ошибки за последние 24 часа
```
level: "error" AND @timestamp >= now-24h
```

### Логи конкретного сервиса
```
service: "email-service"
```

### Медленные запросы (>1s)
```
duration_ms: >1000
```

## Мониторинг

### Создание Dashboard в Kibana

1. Перейдите в Dashboard > Create dashboard
2. Добавить визуализации:
   - Количество ошибок по сервисам
   - Количество запросов по времени
   - Среднее время ответа
   - Топ ошибок

### Алерты

Настройте алерты в Kibana Alerting для:
- Уровня ошибок > 5% всех запросов
- Отсутствия логов от сервиса > 5 минут
- Специфических ошибок (например, 5xx)

## Остановка

```bash
docker-compose -f docker-compose.elk.yml down
```

## Очистка данных

```bash
docker-compose -f docker-compose.elk.yml down -v
```

## Устранение проблем

### Elasticsearch не запускается
```bash
# Проверьте права доступа к директории данных
chmod -R 777 elasticsearch/data
```

### Kibana не подключается к Elasticsearch
```bash
# Проверьте, что Elasticsearch запущен
curl http://localhost:9200/_cluster/health
```

### Логи не появляются в Kibana
1. Проверьте, что Logstash запущен: `curl http://localhost:9600`
2. Проверьте логи Logstash: `docker-compose -f docker-compose.elk.yml logs logstash`
3. Убедитесь, что сервис отправляет логы на правильный порт: 5000

## Дополнительные ресурсы

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)

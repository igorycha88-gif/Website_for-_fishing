# Анализ и решение проблемы регистрации (404 на /api/v1/auth/register)

## Исходная проблема

При попытке регистрации пользователя в браузере возникала ошибка:
```
POST http://localhost:3000/api/v1/auth/register 404 (Not Found)
```

## Глубокий анализ проблемы

### 1. Архитектурный контекст

**Проект использует:**
- Frontend: Next.js 15.0.0 с App Router
- Backend: 7 микросервисов на FastAPI
- Инфраструктура: Docker Compose (local development)
- Маршрутизация: Traefik (planned) vs Прямые порты (current)

### 2. Исследование причин

#### Причина #1: Next.js Standalone Build и Output File Tracing

**Проблема:** Next.js в режиме `output: "standalone"` использует Output File Tracing, который включает только файлы, фактически используемые в билде.

**Попытанное решение:** Создание `/app/lib/api.ts` utility для API routing

**Результат:** Файл не включался в production билд, потому что:
- Next.js standalone mode копирует только минималистичный набор файлов
- Файлы в `/app/lib/` могут не включаться если не импортируются явно
- `/lib` директория в корне проекта также не включалась автоматически

**Вывод:** Этот подход не надежен для production билдов.

#### Причина #2: Docker Networking и доступ к сервисам

**Проблема:** Frontend в Docker контейнере не может достичь backend сервисы через `localhost`

**Ошибка:**
```
AggregateError [ECONNREFUSED]: connect ECONNREFUSED 127.0.0.1:8001
```

**Анализ:**
- Frontend запущен в отдельном Docker контейнере
- `localhost` внутри контейнера указывает на сам контейнер frontend, а не на хост-машину
- Backend сервисы также запущены в отдельных контейнерах с порт маппингом на хост

**Решение:** Использование `host.docker.internal` для доступа к сервисам на хост-машине из Docker контейнера на macOS.

#### Причина #3: Next.js Rewrites в Production Mode

**Вопрос:** Работают ли Next.js rewrites в production mode?

**Ответ:** Да, но с ограничениями:
- Rewrites работают только для server-side запросов
- Для client-side запросов (из браузера) нужен правильный setup
- В Docker среде destination URL должен быть доступен из контейнера

## Мировые тренды и практики решения

### Подход #1: Next.js Rewrites (Использован)

**Описание:** Использование встроенного механизма Next.js для проксирования API запросов.

**Плюсы:**
- Встроенная функциональность Next.js
- Простая конфигурация
- Нет дополнительных зависимостей
- Поддержка environment variables

**Минусы:**
- Ограниченная логика маршрутизации
- Все запросы проходят через Next.js сервер
- Нет caching layer по умолчанию

**Кем используется:** Vercel, небольшие проекты, MVP

### Подход #2: BFF Pattern с Route Handlers

**Описание:** Создание Next.js Route Handlers (`app/api/*/route.ts`) которые агрегируют вызовы к микросервисам.

**Плюсы:**
- Полный контроль над request/response
- Можно добавить бизнес логику, трансформацию данных, caching
- Аутентификация/авторизация в одном месте
- Type-safe с TypeScript

**Минусы:**
- Больше кода для поддержки
- Каждый endpoint нужен handler
- Boilerplate

**Кем используется:** Netflix, Airbnb (для разных clients - web, mobile, TV)

### Подход #3: API Gateway (NGINX/Traefik/Kong)

**Описание:** Отдельный API Gateway между Next.js и микросервисами.

**Плюсы:**
- Industry standard для микросервисов
- Чистое разделение ответственности
- Продвинутые фичи: rate limiting, auth, caching, circuit breakers
- Масштабируется независимо
- Не нужны изменения кода в Next.js

**Минусы:**
- Дополнительный infrastructure компонент
- Learning curve для конфигурации
- Не "чистое" Next.js решение

**Кем используется:** Netflix, Uber, Airbnb (Enterprise уровень)

### Подход #4: Environment Variable-Based Client-Side Fetching

**Описание:** Использование env переменных для конфигурации URL сервисов и прямой fetch из браузера.

**Плюсы:**
- Самый простой подход
- Нет server-side proxy

**Минусы:**
- Выставляет backend URLs клиенту (security risk)
- CORS проблемы
- Не подходит для production
- Нет server-side auth handling

**Кем используется:** Только для prototyping/dev

### Подход #5: Hybrid: Route Handlers + Rewrites

**Описание:** Использование rewrites для простых endpoint и Route Handlers для сложной логики.

**Плюсы:**
- Flexibility: простые APIs -> rewrites, сложные -> handlers
- Best of both worlds
- Files guaranteed to be included when used

**Минусы:**
- Два паттерна для поддержки
- Сложно понять какой использовать когда

## Итоговое решение

### Для текущего проекта (Immediate Solution)

**Использован:** Next.js Rewrites + Docker Networking fix

**Конфигурация:**

```javascript
// next.config.js
const nextConfig = {
  output: "standalone",
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    const API_HOST = process.env.API_HOST || 'host.docker.internal';
    return [
      {
        source: '/api/v1/auth/:path*',
        destination: `http://${API_HOST}:8001/api/v1/auth/:path*`,
      },
      // ... другие сервисы
    ]
  },
};
```

**Frontend компоненты:** Используют стандартный fetch с относительными путями

```typescript
// app/register/page.tsx
const res = await fetch("/api/v1/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(formData),
})
```

### Для Production/Scale (Long-term)

**Рекомендуется:** Плавный переход на BFF Pattern с Route Handlers

**Почему:**
- Centralized error handling
- Authentication/authorization layer
- Data transformation для frontend
- Caching с Next.js built-in mechanisms
- Type-safe API layer

**Пример:**

```typescript
// app/api/v1/auth/register/route.ts
import { NextRequest } from 'next/server'

export async function POST(request: NextRequest) {
  const body = await request.json()

  const response = await fetch('http://host.docker.internal:8001/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const error = await response.json()
    return new Response(JSON.stringify(error), { status: response.status })
  }

  const data = await response.json()

  return Response.json(data)
}
```

## Ключевые выводы

1. **Docker Networking:** В Docker среде на macOS используйте `host.docker.internal` для доступа с контейнера на хост

2. **Next.js Standalone Build:** Будьте осторожны с Output File Tracing - файлы не всегда включаются в production билд

3. **Next.js Rewrites:** Работают в production mode, но destination должен быть доступен из контейнера

4. **Масштабируемость:** Для production с множеством microservices рекомендуется API Gateway или BFF pattern

## Тестирование

```bash
# Test registration through frontend
curl -s http://localhost:3000/api/v1/auth/register \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"testpass123"}'

# Expected response:
# {"message":"Registration successful. Please check your email for verification code."}
```

## Ссылки

- [Next.js Rewrites](https://nextjs.org/docs/app/api-reference/next-config-js/rewrites)
- [Next.js Standalone Output](https://nextjs.org/docs/app/api-reference/next-config-js/output)
- [Docker Desktop Networking](https://docs.docker.com/desktop/networking/#use-container-address-hostdockerinternal)
- [BFF Pattern](https://samnewman.io/lab-notes/2014/06/10/why-you-shouldnt-call-a-microservice-from-another-microservice-directly)
- [API Gateway Pattern](https://microservices.io/patterns/apigateway.html)

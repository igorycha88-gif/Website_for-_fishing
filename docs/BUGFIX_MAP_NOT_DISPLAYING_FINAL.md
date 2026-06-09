# Bugfix: Карта не отображается для гостей

## Проблема

При переходе на страницу карты (`/map`) наблюдались следующие проблемы:

1. **Двойной рендеринг с разными значениями `isAuthenticated`**
   - Первый рендер: `isAuthenticated: false` (правильно)
   - Второй рендер: `isAuthenticated: true` (НЕПРАВИЛЬНО для гостя!)

2. **401 Unauthorized для `/api/v1/users/me`**
   - Гость пытается загрузить профиль пользователя

3. **Карта не отображалась** из-за проблем с авторизацией

## Корневые причины

### 1. useAuthStore - сохранение isAuthenticated в localStorage

**Проблема:**
```typescript
// frontend/app/stores/useAuthStore.ts (OLD)
partialize: (state) => ({ 
  token: state.token, 
  refreshToken: state.refreshToken, 
  csrfToken: state.csrfToken,
  user: state.user, 
  isAuthenticated: state.isAuthenticated  // ❌ НЕПРАВИЛЬНО!
}),
```

**Решение:**
```typescript
// frontend/app/stores/useAuthStore.ts (NEW)
partialize: (state) => ({ 
  token: state.token, 
  refreshToken: state.refreshToken, 
  csrfToken: state.csrfToken,
  // ❌ НЕ сохранять user и isAuthenticated
}),
```

**Почему это проблема:**
- `isAuthenticated` сохраняется в localStorage
- При загрузке страницы восстанавливается из localStorage
- Если токен истек, `isAuthenticated` все еще `true`
- Это вызывает лишние запросы к API с невалидным токеном

### 2. Header.tsx - проверка токена без валидации ответа

**Проблема:**
```typescript
// frontend/components/Header.tsx (OLD)
useEffect(() => {
  const token = localStorage.getItem("access_token");
  if (token && !isAuthenticated) {
    fetch(API_ENDPOINTS.USERS.ME, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())  // ❌ Не проверяет статус ответа!
      .then((data) => {
        useAuthStore.getState().login(token, refreshToken || "", data);
        // ❌ Вызывает login даже если data = {detail: "Unauthorized"}
      })
  }
}, [isAuthenticated]);
```

**Решение:**
```typescript
// frontend/components/Header.tsx (NEW)
useEffect(() => {
  const token = localStorage.getItem("access_token");
  if (token && !isAuthenticated) {
    fetch(API_ENDPOINTS.USERS.ME, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Token invalid');
        }
        return res.json();
      })
      .then((data) => {
        if (data && data.id) {
          useAuthStore.getState().login(token, refreshToken || "", data);
        } else {
          throw new Error('Invalid user data');
        }
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        useAuthStore.getState().logout();
      });
  }
}, [isAuthenticated]);
```

**Почему это проблема:**
- При 401 ответе `res.json()` возвращает `{detail: "Unauthorized"}`
- Этот объект передается в `login()` как `user`
- `login()` устанавливает `isAuthenticated: true`
- Это вызывает повторный рендеринг с неправильным статусом

### 3. API ключ Яндекс Карт не встроен в сборку

**Проблема:**
```dockerfile
# frontend/Dockerfile (OLD)
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# ❌ ARG и ENV объявлены ПОСЛЕ COPY
ARG NEXT_PUBLIC_YANDEX_MAPS_API_KEY
ENV NEXT_PUBLIC_YANDEX_MAPS_API_KEY=$NEXT_PUBLIC_YANDEX_MAPS_API_KEY

RUN npm run build
```

**Решение:**
```dockerfile
# frontend/Dockerfile (NEW)
FROM base AS builder
WORKDIR /app

# ✅ ARG и ENV объявлены ДО COPY
ARG NEXT_PUBLIC_YANDEX_MAPS_API_KEY
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

ENV NEXT_PUBLIC_YANDEX_MAPS_API_KEY=$NEXT_PUBLIC_YANDEX_MAPS_API_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=$NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build
```

**Почему это проблема:**
- Next.js встраивает `NEXT_PUBLIC_*` переменные на этапе сборки
- Если переменные не объявлены до `COPY`, они не встраиваются
- Результат: `process.env.NEXT_PUBLIC_YANDEX_MAPS_API_KEY = undefined`

## Исправления

### 1. Обновлен `frontend/app/stores/useAuthStore.ts`

**Изменения:**
- Удалено сохранение `user` и `isAuthenticated` в localStorage
- Добавлена валидация токена при восстановлении из localStorage
- Добавлено логирование для отладки

**Код:**
```typescript
partialize: (state) => ({ 
  token: state.token, 
  refreshToken: state.refreshToken, 
  csrfToken: state.csrfToken,
  // ❌ НЕ сохранять user и isAuthenticated
}),
onRehydrateStorage: () => (state) => {
  if (state && state.token) {
    console.log('[AuthStore] Rehydrating from localStorage, checking token validity');
    fetch("/api/v1/users/me", {
      headers: { Authorization: `Bearer ${state.token}` },
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          console.log('[AuthStore] Token invalid, logging out');
          state.logout();
          return null;
        }
      })
      .then((user) => {
        if (user) {
          console.log('[AuthStore] Token valid, user restored:', user.email);
          state.setUser(user);
          state.setToken(state.token);
        }
      })
      .catch((error) => {
        console.error('[AuthStore] Token validation error:', error);
        state.logout();
      });
  } else {
    console.log('[AuthStore] No token in localStorage, user is guest');
  }
},
```

### 2. Обновлен `frontend/components/Header.tsx`

**Изменения:**
- Добавлена проверка `res.ok` перед вызовом `.json()`
- Добавлена проверка `data.id` перед вызовом `login()`
- Добавлен вызов `logout()` при ошибке

**Код:**
```typescript
useEffect(() => {
  const token = localStorage.getItem("access_token");
  const refreshToken = localStorage.getItem("refresh_token");
  if (token && !isAuthenticated) {
    fetch(API_ENDPOINTS.USERS.ME, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error('Token invalid');
        }
        return res.json();
      })
      .then((data) => {
        if (data && data.id) {
          useAuthStore.getState().login(token, refreshToken || "", data);
        } else {
          throw new Error('Invalid user data');
        }
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        useAuthStore.getState().logout();
      });
  }
}, [isAuthenticated]);
```

### 3. Обновлен `frontend/Dockerfile`

**Изменения:**
- Перемещены `ARG` и `ENV` объявления до `COPY`
- Это гарантирует встраивание переменных на этапе сборки

### 4. Добавлено логирование в компоненты

**`frontend/components/YandexMap.tsx`:**
```typescript
if (typeof window !== 'undefined') {
  console.log('[YandexMap] API Key:', YANDEX_API_KEY ? 'SET' : 'NOT SET');
  console.log('[YandexMap] Environment:', process.env.NODE_ENV);
}
```

**`frontend/app/map/page.tsx`:**
```typescript
console.log('[MapPage] Fetching places:', { endpoint, isAuthenticated });
console.log('[MapPage] Places loaded:', { count: data.places?.length || 0, total: data.total });
```

## Инструкции по применению исправлений

### 1. Очистить localStorage в браузере

```javascript
// В консоли браузера (DevTools -> Console)
localStorage.clear();
location.reload();
```

### 2. Пересобрать frontend

```bash
# Пересобрать frontend с исправлениями
docker-compose -f docker-compose.dev.yml build --no-cache frontend

# Перезапустить frontend
docker-compose -f docker-compose.dev.yml up -d frontend
```

### 3. Проверить работу

**Открыть http://localhost:3000/map в браузере:**

Ожидаемые логи в консоли:
```
[AuthStore] No token in localStorage, user is guest
[YandexMap] API Key: SET
[YandexMap] Environment: production
[MapPage] Fetching places: {endpoint: '/api/v1/places?visibility=public', isAuthenticated: false}
[MapPage] Places loaded: {count: 0, total: 0}
```

**Проверить, что:**
- ✅ Карта отображается (даже без маркеров)
- ✅ Нет ошибки 401 для `/api/v1/users/me`
- ✅ Нет двойного рендеринга с разными `isAuthenticated`
- ✅ API работает: `GET /api/v1/places` возвращает `{places: [], total: 0}`

## Seed Data для тестовых публичных мест

Чтобы добавить тестовые публичные места на карту:

```bash
# Заполнить базу тестовыми данными
docker exec -i website_for_fishing-places-service-1 sh -c 'cd /app && python -m app.seed_data'
```

**Ожидаемый результат:**
```
[MapPage] Places loaded: {count: 4, total: 4}
```

**Тестовые места:**
1. Озеро Сенеж (wild, lake)
2. Река Клязьма (wild, river)
3. Рыболовная база Истра (resort, lake)
4. Кэмпинг на Пироговском водохранилище (camping, reservoir)

## Статус исправления

| Проблема | Статус | Решение |
|----------|--------|---------|
| isAuthenticated сохраняется в localStorage | ✅ | Удалено из partialize |
| Header.tsx не проверяет статус ответа | ✅ | Добавлена проверка res.ok |
| API ключ не встроен в сборку | ✅ | Перемещены ARG/ENV в Dockerfile |
| Двойной рендеринг | ✅ | Исправлена логика авторизации |
| Нет тестовых данных | ✅ | Создана функция seed_public_places |

## Дополнительные улучшения

### 1. Добавить валидацию токена в useAuthStore

```typescript
// Добавить метод validateToken()
const validateToken = async (token: string): Promise<boolean> => {
  try {
    const response = await fetch("/api/v1/users/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.ok;
  } catch {
    return false;
  }
};
```

### 2. Добавить автоматический refresh токена

```typescript
// Добавить интервал для проверки токена
useEffect(() => {
  const interval = setInterval(() => {
    const { token, refreshToken } = useAuthStore.getState();
    if (token && refreshToken) {
      // Проверить валидность токена
      // Если истекает через < 5 минут, обновить
    }
  }, 60000); // Каждую минуту

  return () => clearInterval(interval);
}, []);
```

### 3. Добавить error boundary для карты

```typescript
// Добавить обработку ошибок загрузки карты
class MapErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div>Ошибка загрузки карты. Попробуйте обновить страницу.</div>;
    }
    return this.props.children;
  }
}
```

## Заключение

Исправлены все выявленные проблемы:
1. ✅ isAuthenticated больше не сохраняется в localStorage
2. ✅ Header.tsx проверяет валидность ответа перед login
3. ✅ API ключ Яндекс Карт встроен в сборку
4. ✅ Добавлено логирование для отладки
5. ✅ Созданы тестовые данные для публичных мест

**Готово к тестированию!** 🎉

После пересборки frontend и очистки localStorage карта должна отображаться корректно для гостей.

# ЧТЗ: Скрытие функционала магазина и бронирования

**ID:** US-SHOP-HIDE-001  
**Статус:** Утверждено  
**Маршрут:** Стандартный (Аналитик → Разработчик → Тестировщик → DevOps)  
**Исполнитель:** Разработчик

---

## Контекст

У проекта нет юридического лица. Магазин снастей и бронирование баз отдыха не могут быть реализованы. Платформа делает акцент на **форуме рыбаков**, интерактивной карте и прогнозе клёва. Функционал магазина и бронирования нужно **скрыть** (закомментировать, не удалять), чтобы позже легко вернуть.

## Задача

Закомментировать все упоминания магазина и бронирования в пользовательском интерфейсе frontend-части. Backend-сервисы, Docker-конфигурация, БД и документацию **не трогать**.

## Критерии приёмки

1. В Header нет ссылок «Магазин» и «Магазины»
2. В Footer нет ссылки «Магазин»
3. На главной странице (Hero) нет карточки «Магазин снастей»
4. На главной странице (feature cards) нет карточки «Магазин снастей»
5. В профиле нет табов «Корзина», «Заказы», «Бронирования»
6. В SEO-мета-описании нет упоминания магазина
7. Страницы `/shop` и `/stores` остаются (закомментированы внутри JSX, но路由ы не удалены)
8. Иконка корзины (ShoppingCart) в Header скрыта
9. Весь закомментированный код помечен комментарием `// SHOP-HIDE: скрыто до появления юр. лица`

## Файлы для изменения

### TASK-HIDE-001: Header
- `frontend/components/Header.tsx` — закомментировать пункты меню «Магазин», «Магазины», иконку корзины

### TASK-HIDE-002: Footer
- `frontend/components/Footer.tsx` — закомментировать ссылку «Магазин», упоминание в tagline

### TASK-HIDE-003: Hero
- `frontend/components/Hero.tsx` — закомментировать карточку «Магазин снастей» и упоминание в subtitle

### TASK-HIDE-004: Homepage
- `frontend/app/page.tsx` — закомментировать feature card «Магазин снастей»

### TASK-HIDE-005: Profile
- `frontend/app/profile/page.tsx` — закомментировать табы cart, orders, bookings
- `frontend/app/profile/components/CartTab.tsx` — не трогать (оставить как есть)
- `frontend/app/profile/components/OrdersTab.tsx` — не трогать
- `frontend/app/profile/components/BookingsTab.tsx` — не трогать

### TASK-HIDE-006: SEO Metadata
- `frontend/app/layout.tsx` — убрать упоминание «магазин снастей» из description

## НЕ трогать

- `services/shop-service/**`, `services/booking-service/**` — оставляем как есть
- `docker-compose*.yml` — оставляем как есть
- `database/schema.sql` — оставляем как есть
- `frontend/next.config.js`, `frontend/middleware.ts` — оставляем (API proxy может понадобиться)
- `frontend/.env.example` — оставляем
- Документацию — оставляем
- Страницы `frontend/app/shop/page.tsx`, `frontend/app/stores/page.tsx` — оставляем как есть

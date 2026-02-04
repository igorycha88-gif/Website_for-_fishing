# PostgreSQL Database Schema

## Overview
Single shared database for all microservices with the following tables.

## ER Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               Users Table                                    │
│  id (PK) | email | username | password_hash | first_name | last_name |    │
│  phone | avatar_url | is_active | is_verified | created_at | updated_at │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                │ 1:N
                                │
                    ┌───────────┴────────────┬──────────────┐
                    │                        │              │
              ┌─────┴─────┐          ┌───────┴──────┐ ┌─────┴─────────┐
              │  Reports  │          │   Bookings   │ │  Orders       │
              │           │          │              │ │  (Shop)       │
              │ id (PK)   │          │ id (PK)      │ │ id (PK)       │
              │ user_id   │          │ user_id      │ │ user_id       │
              │ place_id  │          │ place_id     │ │               │
              │ title     │          │ date         │ └───────────────┘
              │ content   │          │ status       │
              │ rating    │          └──────────────┘
              │ images[]  │
              └─────┬─────┘
                    │
                    │ N:1
                    │
           ┌────────┴──────────┐
           │    Places         │
           │                   │
           │ id (PK)           │
           │ owner_id (FK→User)│
           │ title             │
           │ description       │
           │ latitude          │
           │ longitude         │
           │ address           │
           │ price_per_day     │
           │ max_people        │
           │ facilities[]      │
           │ fish_types[]      │
           │ images[]          │
           │ rating_avg        │
           │ is_active         │
           └─────────┬─────────┘
                     │
                     │ 1:N
                     │
           ┌─────────┴──────────┐
           │  BookingSlots     │
           │                   │
           │ id (PK)           │
           │ place_id          │
           │ date              │
           │ is_available      │
           │ price             │
           └───────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            Products Table (Shop)                             │
│  id (PK) | title | description | price | stock | category_id | images[]    │
│  is_active | created_at | updated_at                                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Categories Table                                    │
│  id (PK) | name | description | parent_id | slug                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     OrderItems Table                                        │
│  id (PK) | order_id | product_id | quantity | price                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    RefreshTokens Table                                      │
│  id (PK) | user_id | token | expires_at                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        Ratings Table                                        │
│  id (PK) | user_id | report_id | place_id | rating | comment               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tables

### 1. users
Таблица пользователей (Auth Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email пользователя |
| username | VARCHAR(100) | UNIQUE, NOT NULL | Никнейм |
| password_hash | VARCHAR(255) | NOT NULL | Хеш пароля (bcrypt) |
| first_name | VARCHAR(100) | | Имя |
| last_name | VARCHAR(100) | | Фамилия |
| phone | VARCHAR(20) | | Телефон |
| avatar_url | VARCHAR(500) | | URL аватара (Cloudinary) |
| is_active | BOOLEAN | default true | Активен ли аккаунт |
| is_verified | BOOLEAN | default false | Подтвержден ли email |
| created_at | TIMESTAMP | default NOW() | Дата создания |
| updated_at | TIMESTAMP | auto update | Дата обновления |

### 2. places
Таблица мест для рыбалки (Places Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| owner_id | UUID | FK(users.id) | Владелец места |
| title | VARCHAR(200) | NOT NULL | Название места |
| description | TEXT | NOT NULL | Описание |
| latitude | DECIMAL(10,8) | NOT NULL | Широта |
| longitude | DECIMAL(11,8) | NOT NULL | Долгота |
| address | VARCHAR(500) | NOT NULL | Адрес |
| city | VARCHAR(100) | | Город |
| region | VARCHAR(100) | | Регион |
| price_per_day | DECIMAL(10,2) | | Цена за день |
| max_people | INTEGER | | Макс. кол-во людей |
| facilities | JSONB | | Удобства (парковка, WiFi, туалет и т.д.) |
| fish_types | JSONB | | Виды рыб |
| images | TEXT[] | | Массив URL изображений |
| rating_avg | DECIMAL(3,2) | default 0 | Средний рейтинг |
| reviews_count | INTEGER | default 0 | Кол-во отзывов |
| is_active | BOOLEAN | default true | Активно ли место |
| created_at | TIMESTAMP | default NOW() | Дата создания |
| updated_at | TIMESTAMP | auto update | Дата обновления |

### 3. reports
Таблица отчетов рыбаков (Reports Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| user_id | UUID | FK(users.id), NOT NULL | Автор отчета |
| place_id | UUID | FK(places.id) | Место рыбалки |
| title | VARCHAR(200) | NOT NULL | Заголовок |
| content | TEXT | NOT NULL | Содержимое |
| images | TEXT[] | | Массив URL изображений |
| rating | INTEGER | CHECK(1-5) | Оценка автора |
| fish_caught | JSONB | | Виды и количество пойманной рыбы |
| weather | JSONB | | Погодные условия |
| likes_count | INTEGER | default 0 | Кол-во лайков |
| comments_count | INTEGER | default 0 | Кол-во комментариев |
| created_at | TIMESTAMP | default NOW() | Дата создания |
| updated_at | TIMESTAMP | auto update | Дата обновления |

### 4. booking_slots
Слоты для бронирования (Booking Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| place_id | UUID | FK(places.id), NOT NULL | Место |
| date | DATE | NOT NULL | Дата |
| is_available | BOOLEAN | default true | Доступен ли слот |
| price | DECIMAL(10,2) | | Цена (может отличаться от базовой) |
| max_people | INTEGER | | Макс. кол-во людей в этот день |

### 5. bookings
Бронирования (Booking Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| user_id | UUID | FK(users.id), NOT NULL | Пользователь |
| place_id | UUID | FK(places.id), NOT NULL | Место |
| booking_slot_id | UUID | FK(booking_slots.id) | Слот |
| date | DATE | NOT NULL | Дата |
| people_count | INTEGER | NOT NULL | Кол-во людей |
| total_price | DECIMAL(10,2) | NOT NULL | Общая цена |
| status | VARCHAR(20) | NOT NULL | pending/confirmed/cancelled/completed |
| payment_intent_id | VARCHAR(200) | | Stripe Payment Intent ID |
| cancel_reason | TEXT | | Причина отмены |
| created_at | TIMESTAMP | default NOW() | Дата создания |
| updated_at | TIMESTAMP | auto update | Дата обновления |

### 6. categories
Категории товаров (Shop Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| name | VARCHAR(100) | NOT NULL | Название |
| description | TEXT | | Описание |
| parent_id | UUID | FK(categories.id) | Родительская категория |
| slug | VARCHAR(100) | UNIQUE | URL slug |

### 7. products
Товары (Shop Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| title | VARCHAR(200) | NOT NULL | Название |
| description | TEXT | | Описание |
| price | DECIMAL(10,2) | NOT NULL | Цена |
| stock | INTEGER | default 0 | Количество на складе |
| category_id | UUID | FK(categories.id) | Категория |
| images | TEXT[] | | Массив URL изображений |
| is_active | BOOLEAN | default true | Активен ли товар |
| created_at | TIMESTAMP | default NOW() | Дата создания |
| updated_at | TIMESTAMP | auto update | Дата обновления |

### 8. orders
Заказы (Shop Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| user_id | UUID | FK(users.id), NOT NULL | Пользователь |
| total_price | DECIMAL(10,2) | NOT NULL | Общая цена |
| status | VARCHAR(20) | NOT NULL | pending/processing/shipped/delivered/cancelled |
| payment_intent_id | VARCHAR(200) | | Stripe Payment Intent ID |
| shipping_address | JSONB | NOT NULL | Адрес доставки |
| created_at | TIMESTAMP | default NOW() | Дата создания |
| updated_at | TIMESTAMP | auto update | Дата обновления |

### 9. order_items
Элементы заказа (Shop Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| order_id | UUID | FK(orders.id), NOT NULL | Заказ |
| product_id | UUID | FK(products.id), NOT NULL | Товар |
| quantity | INTEGER | NOT NULL | Количество |
| price | DECIMAL(10,2) | NOT NULL | Цена на момент заказа |

### 10. refresh_tokens
Refresh токены (Auth Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| user_id | UUID | FK(users.id), NOT NULL | Пользователь |
| token | VARCHAR(500) | UNIQUE, NOT NULL | Refresh токен |
| expires_at | TIMESTAMP | NOT NULL | Дата истечения |
| created_at | TIMESTAMP | default NOW() | Дата создания |

### 11. ratings
Рейтинги (Reports/Places Service)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| user_id | UUID | FK(users.id), NOT NULL | Пользователь |
| report_id | UUID | FK(reports.id) | Отчет (опционально) |
| place_id | UUID | FK(places.id) | Место (опционально) |
| rating | INTEGER | CHECK(1-5), NOT NULL | Оценка |
| comment | TEXT | | Комментарий |
| created_at | TIMESTAMP | default NOW() | Дата создания |

## Indexes

### Performance Indexes
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_places_location ON places(latitude, longitude);
CREATE INDEX idx_places_owner ON places(owner_id);
CREATE INDEX idx_reports_user ON reports(user_id);
CREATE INDEX idx_reports_place ON reports(place_id);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_place ON bookings(place_id);
CREATE INDEX idx_booking_slots_place_date ON booking_slots(place_id, date);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_ratings_user ON ratings(user_id);
```

### JSONB Indexes
```sql
CREATE INDEX idx_places_facilities ON places USING GIN(facilities);
CREATE INDEX idx_places_fish_types ON places USING GIN(fish_types);
CREATE INDEX idx_reports_fish_caught ON reports USING GIN(fish_caught);
```

## Foreign Key Constraints

```sql
ALTER TABLE places ADD CONSTRAINT fk_places_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE reports ADD CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE reports ADD CONSTRAINT fk_reports_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE SET NULL;
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE;
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_slot FOREIGN KEY (booking_slot_id) REFERENCES booking_slots(id) ON DELETE CASCADE;
ALTER TABLE booking_slots ADD CONSTRAINT fk_booking_slots_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE;
ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;
ALTER TABLE products ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;
ALTER TABLE refresh_tokens ADD CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE ratings ADD CONSTRAINT fk_ratings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE ratings ADD CONSTRAINT fk_ratings_report FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE;
ALTER TABLE ratings ADD CONSTRAINT fk_ratings_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE;
```

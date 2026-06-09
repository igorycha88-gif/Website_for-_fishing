# PostgreSQL Database Schema

## Overview
Single shared database for all microservices with the following tables.

**Note**: Complete schema is defined in `schema.sql`, but not all tables are currently in use. Only tables marked with ✅ are actively used.

## ER Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               Users Table ✅                                  │
│  id (PK) | email | username | password_hash | first_name | last_name |    │
│  phone | avatar_url | is_active | is_verified | role | created_at | updated_at │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │
                                │ 1:N
                                │
                    ┌───────────┴────────────┬──────────────┐
                    │                        │              │
              ┌─────┴─────┐          ┌───────┴──────┐ ┌─────┴─────────┐
              │  Reports 🔮│          │   Bookings 🔮 │ │  Orders 🔮    │
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
           │    Places 🔮       │
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
           │  BookingSlots 🔮   │
           │                   │
           │ id (PK)           │
           │ place_id          │
           │ date              │
           │ is_available      │
           │ price             │
           └───────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            Products Table 🔮 (Shop)                           │
│  id (PK) | title | description | price | stock | category_id | images[]    │
│  is_active | created_at | updated_at                                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Categories Table 🔮                                 │
│  id (PK) | name | description | parent_id | slug                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     OrderItems Table 🔮                                       │
│  id (PK) | order_id | product_id | quantity | price                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    RefreshTokens Table ✅                                      │
│  id (PK) | user_id | token | expires_at | created_at                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        Ratings Table 🔮                                      │
│  id (PK) | user_id | report_id | place_id | rating | comment               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│               EmailVerificationCodes Table ✅                                 │
│  id (PK) | email | code | attempts | expires_at | created_at               │
└─────────────────────────────────────────────────────────────────────────────┘

✅ = Implemented & In Use | 🔮 = Defined & Planned
```

## Tables

### 1. users ✅
Таблица пользователей (Auth Service)

**Status**: Implemented and actively used

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
| role | VARCHAR(20) | default 'user' | Роль (user/moderator/admin) |
| created_at | TIMESTAMP | default NOW() | Дата создания |
| updated_at | TIMESTAMP | auto update | Дата обновления |

**Role Values**:
- `user` - Обычный пользователь
- `moderator` - Модератор
- `admin` - Администратор

**SQLAlchemy Model**:
```python
class User(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(20), default='user')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 2. refresh_tokens ✅
Refresh токены (Auth Service)

**Status**: Implemented and actively used

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| user_id | UUID | FK(users.id), NOT NULL | Пользователь |
| token | VARCHAR(500) | UNIQUE, NOT NULL | Refresh токен |
| expires_at | TIMESTAMP | NOT NULL | Дата истечения |
| created_at | TIMESTAMP | default NOW() | Дата создания |

### 3. email_verification_codes ✅
Коды подтверждения email (Auth Service)

**Status**: Implemented and actively used

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| email | VARCHAR(255) | NOT NULL | Email адрес |
| code | VARCHAR(6) | NOT NULL | Код подтверждения (6 цифр) |
| attempts | INTEGER | default 0 | Количество попыток |
| expires_at | TIMESTAMP | NOT NULL | Дата истечения кода |
| created_at | TIMESTAMP | default NOW() | Дата создания |

---

### 🔮 The following tables are defined in schema.sql but NOT YET IMPLEMENTED:

### 4. places 🔮
Таблица мест для рыбалки (Places Service)

**Status**: Defined in schema.sql, not yet implemented

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

### 5. reports 🔮
Таблица отчетов рыбаков (Reports Service)

**Status**: Defined in schema.sql, not yet implemented

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

### 6. booking_slots 🔮
Слоты для бронирования (Booking Service)

**Status**: Defined in schema.sql, not yet implemented

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| place_id | UUID | FK(places.id), NOT NULL | Место |
| date | DATE | NOT NULL | Дата |
| is_available | BOOLEAN | default true | Доступен ли слот |
| price | DECIMAL(10,2) | | Цена (может отличаться от базовой) |
| max_people | INTEGER | | Макс. кол-во людей в этот день |

### 7. bookings 🔮
Бронирования (Booking Service)

**Status**: Defined in schema.sql, not yet implemented

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

### 8. categories 🔮
Категории товаров (Shop Service)

**Status**: Defined in schema.sql, not yet implemented

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| name | VARCHAR(100) | NOT NULL | Название |
| description | TEXT | | Описание |
| parent_id | UUID | FK(categories.id) | Родительская категория |
| slug | VARCHAR(100) | UNIQUE | URL slug |

### 9. products 🔮
Товары (Shop Service)

**Status**: Defined in schema.sql, not yet implemented

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

### 10. orders 🔮
Заказы (Shop Service)

**Status**: Defined in schema.sql, not yet implemented

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

### 11. order_items 🔮
Элементы заказа (Shop Service)

**Status**: Defined in schema.sql, not yet implemented

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default gen() | Уникальный идентификатор |
| order_id | UUID | FK(orders.id), NOT NULL | Заказ |
| product_id | UUID | FK(products.id), NOT NULL | Товар |
| quantity | INTEGER | NOT NULL | Количество |
| price | DECIMAL(10,2) | NOT NULL | Цена на момент заказа |

### 12. ratings 🔮
Рейтинги (Reports/Places Service)

**Status**: Defined in schema.sql, not yet implemented

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

### Performance Indexes ✅ (Defined in schema.sql)
```sql
-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Places indexes
CREATE INDEX idx_places_location ON places(latitude, longitude);
CREATE INDEX idx_places_owner ON places(owner_id);
CREATE INDEX idx_places_active ON places(is_active);
CREATE INDEX idx_places_rating ON places(rating_avg DESC);

-- Reports indexes
CREATE INDEX idx_reports_user ON reports(user_id);
CREATE INDEX idx_reports_place ON reports(place_id);
CREATE INDEX idx_reports_created ON reports(created_at DESC);

-- Bookings indexes
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_bookings_place ON bookings(place_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_date ON bookings(date);

-- Booking slots indexes
CREATE INDEX idx_booking_slots_place_date ON booking_slots(place_id, date);
CREATE INDEX idx_booking_slots_available ON booking_slots(is_available);

-- Products indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_title ON products USING gin(to_tsvector('english', title));

-- Orders indexes
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

-- Order items indexes
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Refresh tokens indexes
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);

-- Ratings indexes
CREATE INDEX idx_ratings_user ON ratings(user_id);
CREATE INDEX idx_ratings_report ON ratings(report_id);
CREATE INDEX idx_ratings_place ON ratings(place_id);

-- Categories indexes
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);

-- Email verification codes indexes
CREATE INDEX idx_email_verification_codes_email ON email_verification_codes(email);
CREATE INDEX idx_email_verification_codes_expires ON email_verification_codes(expires_at);
```

### JSONB Indexes ✅ (Defined in schema.sql)
```sql
CREATE INDEX idx_places_facilities ON places USING GIN(facilities);
CREATE INDEX idx_places_fish_types ON places USING GIN(fish_types);
CREATE INDEX idx_reports_fish_caught ON reports USING GIN(fish_caught);
```

## Foreign Key Constraints

```sql
-- Auth Service
ALTER TABLE refresh_tokens ADD CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Places Service
ALTER TABLE places ADD CONSTRAINT fk_places_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE booking_slots ADD CONSTRAINT fk_booking_slots_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE;

-- Reports Service
ALTER TABLE reports ADD CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE reports ADD CONSTRAINT fk_reports_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE SET NULL;

-- Booking Service
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE;
ALTER TABLE bookings ADD CONSTRAINT fk_bookings_slot FOREIGN KEY (booking_slot_id) REFERENCES booking_slots(id) ON DELETE CASCADE;

-- Shop Service
ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE;
ALTER TABLE order_items ADD CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;
ALTER TABLE products ADD CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;

-- Ratings
ALTER TABLE ratings ADD CONSTRAINT fk_ratings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE ratings ADD CONSTRAINT fk_ratings_report FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE;
ALTER TABLE ratings ADD CONSTRAINT fk_ratings_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE;
```

## Triggers & Functions

### update_updated_at_column() ✅
Automatically updates the `updated_at` timestamp when a record is modified.

**Triggers applied to**:
- users
- places
- reports
- bookings
- products
- orders

### update_place_rating() ✅
Automatically updates the `rating_avg` and `reviews_count` in the places table when ratings are added, updated, or deleted.

## Views

### v_places_with_owner 🔮
View for place details with owner info.

### v_bookings_details 🔮
View for booking details with place and user info.

## Migration History

- **Initial**: All tables created via `schema.sql`
- **Users table**: Added `role` field (user/moderator/admin)
- **Removed fields**: `birth_date`, `city`, `bio` from users table (not implemented yet)

## Notes

1. All tables use UUID primary keys
2. Timestamps are in UTC
3. All text fields use UTF-8 encoding
4. Email addresses are case-insensitive for uniqueness
5. Role-based access control uses the `role` field in users table

# Анализ и исправление ошибки авторизации (500 Internal Server Error)

## 🔴 Ошибка
```
POST http://localhost:3000/api/v1/auth/login 500 (Internal Server Error)
```

## 🔍 Анализ проблемы

### Корень проблемы
В коде используется поле `role` в модели User, но оно **не было определено** в SQLAlchemy модели.

### Где обнаружена ошибка:

1. **В CRUD (app/crud/user.py:23)**
   ```python
   user = User(
       email=email,
       username=username,
       password_hash=password_hash,
       role=role  # ← Ошибка: поле 'role' не существует в модели
   )
   ```

2. **В endpoints (app/endpoints/auth.py:250)**
   ```python
   access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
   # ← Попытка доступа к несуществующему атрибуту
   ```

3. **В admin эндпоинтах (app/endpoints/admin.py:95)**
   ```python
   role=user.role,  # ← Попытка доступа к несуществующему атрибуту
   ```

4. **В dependencies (app/core/dependencies.py:41)**
   ```python
   "role": user.role  # ← Попытка доступа к несуществующему атрибуту
   ```

## ✅ Исправление

### 1. Обновить модель User
Добавить поле `role` в `app/models/user.py`:

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(500))
    birth_date = Column(DateTime)
    city = Column(String(100))
    bio = Column(Text)
    role = Column(String(50), default="user", nullable=False)  # ← ДОБАВЛЕНО
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

**✓ Уже выполнено в `app/models/user.py`**

### 2. Обновить структуру БД

Если таблица `users` уже существует, нужно добавить колонку. Если её нет, она будет создана автоматически.

#### Вариант A: Если используется Docker Compose
```bash
# Пересоздать сервис auth-service с чистой БД
docker-compose down -v
docker-compose up -d postgres
# Дождаться инициализации PostgreSQL
sleep 5
docker-compose up auth-service
```

#### Вариант B: Если работаете локально с PostgreSQL
Выполнить SQL команду:
```sql
-- Если таблица users существует и не имеет role
ALTER TABLE users 
ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user';

-- Или переиздать всю БД (осторожно - потеряются данные!)
DROP TABLE IF EXISTS users CASCADE;
-- Затем перезапустить приложение, которое создаст таблицы
```

#### Вариант C: Использовать подготовленный скрипт
```bash
cd services/auth-service
python3 init_db.py  # Пересоздаст все таблицы
```

## 📋 Файлы, которые были изменены

| Файл | Изменение |
|------|----------|
| `services/auth-service/app/models/user.py` | ✓ Добавлено поле `role` |
| `services/auth-service/init_db.py` | ✓ Создан новый скрипт инициализации БД |
| `services/auth-service/migrate_add_role.py` | ✓ Создан скрипт миграции (если БД уже существует) |

## 🧪 Тестирование исправления

После применения исправлений проверить авторизацию:

```bash
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

Ожидаемые ответы:
- ✓ Если пользователь существует и пароль верный: `200 OK` с токеном
- ✓ Если email не существует или пароль неверный: `401 Unauthorized`
- ✓ Если email не верифицирован: `403 Forbidden`

## 🔧 Дополнительные команды

```bash
# Создать администратора (после исправления БД)
cd services/auth-service
python3 create_admin.py

# Удалить администратора
python3 delete_admin.py

# Сбросить всех администраторов
python3 reset_admin.py
```

## 📝 Заметки

1. **Значение role по умолчанию** - `"user"`, может быть также:
   - `"admin"` - для администраторов
   - `"moderator"` - для модераторов

2. **Существующие пользователи** - получат роль `"user"` при попытке авторизации (благодаря DEFAULT в БД)

3. **Для admin операций** - нужно явно создать админа через `create_admin.py` скрипт

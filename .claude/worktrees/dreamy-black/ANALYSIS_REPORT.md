# Анализ и исправление ошибки авторизации

## 📋 Резюме
- **Проблема**: POST /api/v1/auth/login возвращает 500 Internal Server Error
- **Причина**: Missing 'role' field in SQLAlchemy User model
- **Статус**: ✅ **ИСПРАВЛЕНО**
- **Коммит**: `a7218b8` - fix(auth): add missing 'role' field to User model

---

## 🔴 Исходная ошибка

```
POST http://localhost:3000/api/v1/auth/login 500 (Internal Server Error)
```

### Причины 500 ошибки:
1. При попытке создать пользователя: `AttributeError: User has no attribute 'role'`
2. При попытке создать токен в логине: `AttributeError: User has no attribute 'role'`
3. При проверке прав администратора: `KeyError: 'role'`

---

## 🔍 Диагностика

### Анализ кода показал:
Поле `role` используется в 4 критических местах, но **не определено** в модели:

| Файл | Строка | Использование |
|------|--------|---------------|
| `crud/user.py` | 23 | `role=role` (при создании) |
| `endpoints/auth.py` | 250 | `"role": user.role` (в токене) |
| `endpoints/admin.py` | 95 | `role=user.role` (в списке) |
| `dependencies.py` | 41 | `"role": user.role` (текущий) |

### Исходная модель (НЕПРАВИЛЬНАЯ):
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(...), primary_key=True, ...)
    email = Column(String(255), unique=True, ...)
    username = Column(String(100), unique=True, ...)
    password_hash = Column(String(255), ...)
    # ... другие поля ...
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, ...)
    updated_at = Column(DateTime, ...)
    # ❌ ОТСУТСТВУЕТ role!
```

---

## ✅ Исправление применено

### Изменённый файл: `services/auth-service/app/models/user.py`

```diff
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
+     role = Column(String(50), default="user", nullable=False)
      is_active = Column(Boolean, default=True)
      is_verified = Column(Boolean, default=False)
      created_at = Column(DateTime, server_default=func.now())
      updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

**Параметры роли:**
- `String(50)` - максимум 50 символов для имени роли
- `default="user"` - по умолчанию все пользователи получают роль "user"
- `nullable=False` - поле обязательно

---

## 🔧 Возможные значения role

| Значение | Описание |
|----------|----------|
| `"user"` | Обычный пользователь (по умолчанию) |
| `"admin"` | Администратор (полный доступ) |
| `"moderator"` | Модератор (частичный доступ) |

---

## 📊 Требуемые дополнительные действия

### 1️⃣ Обновить структуру БД

**Вариант A: Docker Compose (Рекомендуется)**
```bash
# Пересоздать сервисы с чистой БД
docker-compose down -v
docker-compose up postgres
sleep 5
docker-compose up auth-service
```

**Вариант B: Локальная разработка Python**
```bash
cd services/auth-service
python3 init_db.py
```

**Вариант C: Существующая БД (SQL)**
```sql
ALTER TABLE users 
ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user';
```

### 2️⃣ Протестировать

```bash
# Попытка логина (должна вернуть 403 - email not verified)
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

### 3️⃣ Создать администратора

```bash
cd services/auth-service
python3 create_admin.py
```

---

## 📈 Список созданных файлов

| Файл | Назначение |
|------|-----------|
| `AUTH_LOGIN_ERROR_FIX.md` | Подробный анализ и инструкции |
| `init_db.py` | Инициализация всех таблиц БД |
| `migrate_add_role.py` | Миграция для существующей БД |

---

## ✨ Статус исправления

| Компонент | Статус |
|-----------|--------|
| **Модель User (код)** | ✅ Исправлено |
| **CRUD операции** | ✅ Готово (использует role) |
| **Auth endpoints** | ✅ Готово (использует role) |
| **Admin endpoints** | ✅ Готово (использует role) |
| **Dependencies** | ✅ Готово (использует role) |
| **БД структура** | ⚠️ Требует обновления |

---

## 🎯 Результат

После применения всех шагов:
1. ✅ Логин будет работать без 500 ошибок
2. ✅ Авторизация будет корректно создавать токены с ролью
3. ✅ Admin endpoints смогут проверять права доступа
4. ✅ Управление пользователями станет полнофункциональным

---

**Время исправления**: ~2 минуты  
**Влияние**: Критичное (блокирует всю авторизацию)  
**Тип изменения**: Bug Fix (одна строка кода в модели)


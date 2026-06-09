# Стратегия версионирования — Платформа FishMap

## Принцип

Каждый деплой на прод = новая версия. Semver: `MAJOR.MINOR.PATCH`.

Версия хранится в `VERSION` файле в корне проекта. Git tag = `vMAJOR.MINOR.PATCH`.

---

## Правила Semver

| Тип | Когда | Пример | Версия |
|------|-------|--------|--------|
| **patch** | Баг-фиксы, мелкие правки, безопасность | `fix: исправил валидацию` | 0.4.1 → 0.4.2 |
| **minor** | Новый функционал, новые страницы, новые API | `feat: модуль бронирования` | 0.4.1 → 0.5.0 |
| **major** | Breaking changes, смена архитектуры, удаление API | `feat!: новая система авторизации` | 0.4.1 → 1.0.0 |

## Определение типа изменения

Анализируем коммиты с предыдущего релиза:

```bash
# Текущая версия
cat VERSION

# Коммиты с прошлой версии
git log v$(cat VERSION)..HEAD --oneline

# Если есть "feat!" или "BREAKING CHANGE" → major
# Если есть "feat:" → minor
# Иначе (fix:, refactor:, chore:, docs:) → patch
```

---

## Файл VERSION

```
0.4.1
```

Обновляется при каждом релизе. Одна строка — текущая версия.

---

## CHANGELOG.md

Формат записи при релизе:

```markdown
## [0.4.2] - 2026-06-09

### Исправлено
- fix: исправил валидацию координат в Places Service (abc1234)
- fix: исправил CORS для прогноза (def5678)

### Добавлено
- feat: страница списка рыб с фильтрами (ghi9012)

### Изменено
- refactor: оптимизировал запросы Forecast Service (jkl3456)
```

---

## Git Tags

```bash
# Создать tag
git tag -a "v0.4.2" -m "Release v0.4.2: $(date +%Y-%m-%d)"

# Посмотреть все теги
git tag -l

# Посмотреть детали тега
git show v0.4.2
```

---

## Версия в healthcheck

Каждый backend-сервис возвращает версию в `/health`:

```json
{
  "status": "ok",
  "service": "auth-service",
  "version": "0.4.2"
}
```

Версия берётся из env-переменной `APP_VERSION`, которая устанавливается в Dockerfile:

```dockerfile
ARG APP_VERSION=dev
ENV APP_VERSION=$APP_VERSION
```

При сборке через CI:

```bash
docker build --build-arg APP_VERSION=$(cat VERSION) ...
```

---

## Релизный процесс

1. Определить тип изменения (patch / minor / major)
2. Обновить `VERSION` файл
3. Обновить `CHANGELOG.md`
4. Закоммитить: `git commit -m "chore: release v0.4.2"`
5. Создать tag: `git tag -a "v0.4.2" -m "Release v0.4.2"`
6. Push: `git push --follow-tags`
7. Деплой через PIPELINE_PROD.js

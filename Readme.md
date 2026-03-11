---
# Архитектура

```
.
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── .env
├── Readme.md
└── src
    ├── auth.py
    ├── config.py
    ├── crud.py
    ├── database.py
    ├── dependencies.py
    ├── models.py
    ├── redis_client.py
    ├── schemas.py
    ├── routers
    │   ├── auth.py
    │   └── links.py
    └── services
        └── cleanup.py
```

---


# Запуск проекта

## 1. Клонировать репозиторий

```
git clone <repo_url>
cd project
```

---

## 2. Создать `.env`

```
DB_HOST=db
DB_PORT=5432
DB_NAME=url_shortener
DB_USER=postgres
DB_PASS=password

REDIS_HOST=redis
REDIS_PORT=6379

SECRET_KEY=SUPER_SECRET_KEY
ALGORITHM=HS256
BASE_URL=http://localhost:8000
```

---

## 3. Запуск через Docker

```
docker-compose up --build
```

После запуска сервис будет доступен Swagger:

```
http://localhost:8000/docs
```

---
# Аутентификация

Используется **JWT токен**.

После логина сервер возвращает:

```json
{
  "token": "JWT_TOKEN"
}
```

Токен передается в заголовке:

```
Authorization: Bearer <token>
```
- **Чтобы залогиниться нужно нажать Authorize и вставить токен**

---

# Эндпоинты

## Регистрация

```
POST /auth/register
```

### Request

```json
{
  "email": "user@mail.com",
  "password": "123456"
}
```

### Response

```json
{
  "status": "ok"
}
```

---

## Логин

```
POST /auth/login
```

### Request

```json
{
  "email": "user@mail.com",
  "password": "123456"
}
```

### Response

```json
{
  "token": "JWT_TOKEN"
}
```

---

# Создание короткой ссылки

```
POST /links/shorten
```

- Доступно как зарегистрированным, так и незарегистрированным пользователям.
- **Для незарегистрированных пользователей максимальное время работы ссылки - 6 часов**

### Request

```json
{
  "original_url": "https://www.google.com",
  "expires_at": "2026-03-12T12:00:00"
}
```

### Response

```json
{
  "short_code": "AbC123",
  "short_url": "http://localhost:8000/AbC123"
}
```

---

# Редирект

```
GET /{short_code}
```

Пример:

```
GET /AbC123
```

Ответ:

```
302 Redirect → original_url
```

- После каждого перехода по короткой ссылке обновляется click_count и last_used_at \
- **Можно вставить short_url в поиск в новой вкладке и произойдет редирект**

---

# Статистика ссылки

```
GET /links/{short_code}/stats
```

### Response

```json
{
  "original_url": "https://google.com",
  "created_at": "2026-03-11T12:00:00",
  "click_count": 5,
  "last_used_at": "2026-03-11T12:10:00"
}
```

---

# Поиск ссылки

```
GET /links/search
```
### Request

```json
{
  "original_url": "https://www.google.com",
}
```

### Response

```json
[
  {
    "click_count": 1,
    "short_code": "D2htz1",
    "user_id": null,
    "created_at": "2026-03-11T16:23:35.756899",
    "id": 1,
    "original_url": "https://www.google.com",
    "last_used_at": "2026-03-11T16:24:07.345072",
    "expires_at": "2026-03-11T19:23:35.795209"
  }
]
```

---

# Обновление ссылки

```
PUT /links/{short_code}
```

- **Требует авторизацию**

### Request

```json
{
  "new_url": "https://example.com"
}
```

### Response

```json
{
  "status": "updated"
}
```

---

# Удаление ссылки

```
DELETE /links/{short_code}
```

Требует авторизацию.

### Response

```json
{
  "status": "deleted"
}
```

При удалении также очищается Redis кэш.

---

# Кэширование

Redis используется для кэширования редиректов.

Ключ:

```
link:{short_code}
```

TTL:

```
3600 секунд
```

При обновлении или удалении ссылки кэш автоматически очищается.

---

# Автоматическое удаление ссылок

Фоновая задача проверяет истекшие ссылки.

Каждые 120 секунд происходит поиск ссылок где expires_at < now. Найденные ссылки удаляются из Redis и из PostgreSQL

---

# Структура базы данных

## Таблица users

| поле          | тип     |
| ------------- | ------- |
| id            | integer |
| email         | string  |
| password_hash | string  |

---

## Таблица links

| поле         | тип      |
| ------------ | -------- |
| id           | integer  |
| original_url | string   |
| short_code   | string   |
| created_at   | datetime |
| click_count  | integer  |
| last_used_at | datetime |
| expires_at   | datetime |
| user_id      | integer  |


---

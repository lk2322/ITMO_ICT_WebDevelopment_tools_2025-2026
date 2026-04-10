# API эндпоинты

Все эндпоинты (кроме `/auth/register` и `/auth/login`) требуют заголовок авторизации:

```
Authorization: Bearer <JWT_TOKEN>
```

## Аутентификация — `/auth`

### POST /auth/register

Регистрация нового пользователя.

**Request body:**

```json
{
  "email": "user@example.com",
  "username": "testuser",
  "password": "secret123"
}
```

**Response:** `201 Created`

```json
{
  "email": "user@example.com",
  "username": "testuser",
  "id": 1,
  "created_at": "2026-04-10T19:00:00",
  "updated_at": "2026-04-10T19:00:00"
}
```

### POST /auth/login

Получение JWT-токена. Использует OAuth2PasswordRequestForm (form data).

**Request body (form-data):**

| Поле | Значение |
|------|----------|
| `username` | testuser |
| `password` | secret123 |

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### GET /auth/me

Получить информацию о текущем авторизованном пользователе.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "testuser",
  "created_at": "2026-04-10T19:00:00",
  "updated_at": "2026-04-10T19:00:00"
}
```

### GET /auth/users

Получить список всех пользователей. Требует авторизацию.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` — массив пользователей (без паролей).

### POST /auth/change-password

Сменить пароль текущего пользователя.

**Headers:** `Authorization: Bearer <token>`

**Request body:**

```json
{
  "old_password": "current_password",
  "new_password": "new_password"
}
```

**Response:** `200 OK`

```json
{"message": "Password changed successfully"}
```

**Error:** `400 Bad Request` — если старый пароль неверный.

---

## Категории — `/categories`

### POST /categories

Создать категорию.

```json
{
  "name": "Зарплата",
  "description": "Ежемесячный доход",
  "type": "income"
}
```

**Response:** `201 Created`

### GET /categories

Получить список категорий пользователя. Поддерживает пагинацию (`skip`, `limit`).

**Response:** `200 OK` — массив категорий.

### GET /categories/{category_id}

Получить категорию по ID. Возвращает `404` если не найдена, `403` если чужая.

### PATCH /categories/{category_id}

Обновить категорию. Передаются только изменённые поля.

```json
{
  "name": "Новое название"
}
```

### DELETE /categories/{category_id}

Удалить категорию. **Response:** `200 OK` — `{"message": "Category deleted successfully"}`

---

## Транзакции — `/transactions`

### POST /transactions

Создать транзакцию. Можно указать `tag_ids` для привязки тегов.

```json
{
  "amount": 5000.0,
  "description": "Аванс",
  "date": "2026-04-10T00:00:00",
  "type": "income",
  "category_id": 1,
  "tag_ids": [1, 2]
}
```

**Response:** `201 Created` — транзакция с массивом `tags`.

### GET /transactions

Получить список транзакций пользователя.

### GET /transactions/{transaction_id}

Получить транзакцию по ID.

### PATCH /transactions/{transaction_id}

Обновить транзакцию. Можно обновить `tag_ids` — старые связи удалятся, новые создадутся.

### DELETE /transactions/{transaction_id}

Удалить транзакцию. **Response:** `{"message": "Transaction deleted successfully"}`

---

## Бюджеты — `/budgets`

### POST /budgets

Создать бюджет. `category_id` опционален.

```json
{
  "amount": 30000.0,
  "period": "monthly",
  "start_date": "2026-04-01T00:00:00",
  "end_date": "2026-04-30T23:59:59",
  "category_id": 2
}
```

**Response:** `201 Created`

### GET /budgets

Получить список бюджетов пользователя.

### GET /budgets/{budget_id}

Получить бюджет по ID.

### PATCH /budgets/{budget_id}

Обновить бюджет.

### DELETE /budgets/{budget_id}

Удалить бюджет. **Response:** `{"message": "Budget deleted successfully"}`

---

## Теги — `/tags`

### POST /tags

Создать тег. Имя тега уникально в рамках пользователя.

```json
{
  "name": "наличные"
}
```

**Response:** `201 Created`  
**Error:** `400 Bad Request` — если тег с таким именем уже существует.

### GET /tags

Получить список тегов пользователя.

### GET /tags/{tag_id}

Получить тег по ID.

### PATCH /tags/{tag_id}

Обновить тег.

### DELETE /tags/{tag_id}

Удалить тег. **Response:** `{"message": "Tag deleted successfully"}`

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос (GET, PATCH, DELETE) |
| 201 | Ресурс создан (POST) |
| 400 | Ошибка валидации / дубликат |
| 401 | Не авторизован (неверный/отсутствующий токен) |
| 403 | Доступ запрещён (чужой ресурс) |
| 404 | Ресурс не найден |
| 422 | Ошибка валидации Pydantic |

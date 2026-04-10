# Тестирование

## Обзор

Проект содержит **38 модульных тестов**, покрывающих все эндпоинты API. Тесты используют `pytest` с `httpx.TestClient` и изолированную in-memory SQLite базу данных.

## Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Конкретный файл
pytest tests/test_auth.py -v

# Конкретный тест
pytest tests/test_tags.py::test_create_duplicate_tag_fails -v

# С подробным выводом
pytest tests/ -xvs
```

## Структура тестов

```
tests/
├── __init__.py
├── conftest.py          # Фикстуры (engine, session, client, auth_headers)
├── test_auth.py         # 11 тестов аутентификации
├── test_categories.py   # 6 тестов категорий
├── test_transactions.py # 7 тестов транзакций
├── test_budgets.py      # 7 тестов бюджетов
└── test_tags.py         # 7 тестов тегов
```

## Фикстуры (conftest.py)

| Фикстура | Описание |
|----------|----------|
| `engine` | In-memory SQLite engine для изоляции тестов |
| `session` | SQLModel Session, привязанный к тестовому engine |
| `client` | FastAPI TestClient с подменённой зависимостью get_session |
| `auth_headers` | Заголовок `Authorization: Bearer <token>` для тестового пользователя |

### Пример фикстуры

```python
@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        yield session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    user_data = {
        "email": "test@test.com",
        "username": "testuser",
        "password": "testpass123",
    }
    client.post("/auth/register", json=user_data)
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## Покрытие тестами

### test_auth.py (11 тестов)

| Тест | Описание |
|------|----------|
| `test_register` | Успешная регистрация пользователя |
| `test_register_duplicate_username` | Повторная регистрация с тем же username |
| `test_login` | Успешный вход и получение токена |
| `test_login_wrong_password` | Вход с неверным паролем |
| `test_protected_endpoint_without_token` | Доступ без токена → 401/403 |
| `test_protected_endpoint_with_token` | Доступ с токеном → 200 |
| `test_get_current_user_info` | Получение информации о текущем пользователе |
| `test_get_current_user_info_without_token` | Доступ к /auth/me без токена → 401 |
| `test_get_users` | Получение списка пользователей |
| `test_change_password` | Смена пароля и вход с новым паролем |
| `test_change_password_wrong_old` | Смена пароля с неверным старым паролем → 400 |

### test_categories.py (6 тестов)

| Тест | Описание |
|------|----------|
| `test_create_category` | Создание категории |
| `test_get_categories_empty` | Пустой список категорий |
| `test_get_categories_with_items` | Список с элементами |
| `test_get_category_by_id` | Получение категории по ID |
| `test_update_category` | Обновление категории (PATCH) |
| `test_delete_category` | Удаление категории |

### test_transactions.py (7 тестов)

| Тест | Описание |
|------|----------|
| `test_create_transaction` | Создание транзакции |
| `test_create_transaction_with_tags` | Создание транзакции с тегами (many-to-many) |
| `test_get_transactions_empty` | Пустой список |
| `test_get_transactions_with_items` | Список с элементами |
| `test_get_transaction_by_id` | Получение по ID |
| `test_update_transaction` | Обновление транзакции |
| `test_delete_transaction` | Удаление транзакции |

### test_budgets.py (7 тестов)

| Тест | Описание |
|------|----------|
| `test_create_budget` | Создание бюджета |
| `test_create_budget_without_category` | Бюджет без категории |
| `test_get_budgets_empty` | Пустой список |
| `test_get_budgets_with_items` | Список с элементами |
| `test_get_budget_by_id` | Получение по ID |
| `test_update_budget` | Обновление бюджета |
| `test_delete_budget` | Удаление бюджета |

### test_tags.py (7 тестов)

| Тест | Описание |
|------|----------|
| `test_create_tag` | Создание тега |
| `test_create_duplicate_tag_fails` | Повторный тег → 400 |
| `test_get_tags_empty` | Пустой список |
| `test_get_tags_with_items` | Список с элементами |
| `test_get_tag_by_id` | Получение по ID |
| `test_update_tag` | Обновление тега |
| `test_delete_tag` | Удаление тега |

## Результаты

```
38 passed in 14.26s
```

Все тесты проходят успешно. ✅

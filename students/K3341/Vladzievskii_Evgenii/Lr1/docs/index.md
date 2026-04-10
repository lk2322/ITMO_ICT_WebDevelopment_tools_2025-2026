# Personal Finance Management API

!!! info "Лабораторная работа 1"
    **Курс:** Web Development Tools (ИКТ)  
    **Группа:** K3341  
    **Студент:** Владзиевский Евгений  
    **Тема:** Personal Finance Management (15 баллов)  

## Описание проекта

REST API для управления личными финансами, реализованный на **FastAPI** с использованием **SQLModel** ORM и **PostgreSQL**. Приложение позволяет пользователям:

- Регистрироваться и аутентифицироваться через JWT-токены
- Управлять категориями доходов и расходов
- Создавать и отслеживать транзакции
- Устанавливать бюджеты по категориям
- Тегировать транзакции (связь many-to-many)

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Web Framework | FastAPI 0.128 |
| ORM | SQLModel 0.0.14 |
| База данных | PostgreSQL 16 |
| Миграции | Alembic 1.12.1 |
| Аутентификация | JWT (python-jose) |
| Хеширование паролей | bcrypt + passlib |
| Контейнеризация | Docker / Docker Compose |
| Тестирование | pytest + httpx |
| Документация | MkDocs Material |

## Структура проекта

```
Lr1/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI application
│   ├── database.py         # Database engine & session
│   ├── models.py           # SQLModel table definitions
│   ├── schemas.py          # Pydantic schemas
│   ├── auth.py             # JWT & password hashing
│   ├── dependencies.py     # Current user dependency
│   ├── crud.py             # CRUD operations
│   └── routers/
│       ├── auth.py         # /auth endpoints
│       ├── categories.py   # /categories endpoints
│       ├── transactions.py # /transactions endpoints
│       ├── budgets.py      # /budgets endpoints
│       └── tags.py         # /tags endpoints
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 496bec06afc5_initial.py
├── tests/
│   ├── conftest.py         # Fixtures
│   ├── test_auth.py
│   ├── test_categories.py
│   ├── test_transactions.py
│   ├── test_budgets.py
│   └── test_tags.py
├── docker-compose.yml
├── alembic.ini
├── mkdocs.yml
├── requirements.txt
└── .env
```

## Быстрый старт

```bash
# 1. Запустить PostgreSQL через Docker
docker compose up -d

# 2. Создать виртуальное окружение и установить зависимости
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Применить миграции
alembic upgrade head

# 4. Запустить сервер
uvicorn app.main:app --reload

# 5. Открыть документацию
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

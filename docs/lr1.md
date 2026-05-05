# Personal Finance Management API

Лабораторная работа 1 — FastAPI серверное приложение для управления личными финансами.

**Студент:** Владзиевский Евгений | **Группа:** K3341 | **Баллы:** 15

## Функциональность

- 🔐 JWT-аутентификация (регистрация, логин, защищённые эндпоинты)
- 📂 Категории доходов/расходов (CRUD)
- 💰 Транзакции с привязкой к категориям и тегам (CRUD)
- 📊 Бюджеты по категориям и периодам (CRUD)
- 🏷️ Теги с many-to-many связью к транзакциям (CRUD)

## Технологии

| Компонент | Технология |
|-----------|-----------|
| Framework | FastAPI 0.128 |
| ORM | SQLModel 0.0.14 |
| БД | PostgreSQL 16 (Docker) |
| Миграции | Alembic 1.12.1 |
| Аутентификация | JWT (python-jose + passlib/bcrypt) |
| Тестирование | pytest + httpx |
| Документация | MkDocs Material |

## Быстрый старт (Docker Compose)

```bash
# Запустить PostgreSQL + API одной командой
docker compose up --build -d

# API доступен на http://localhost:8000
# Swagger UI: http://localhost:8000/docs

# Остановить
docker compose down

# Остановить с удалением данных
docker compose down -v
```

## Локальная разработка

```bash
# 1. Запустить только PostgreSQL
docker compose up db -d

# 2. Установить зависимости
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Применить миграции
alembic upgrade head

# 4. Запустить сервер с автоперезагрузкой
uvicorn app.main:app --reload
```

## Тестирование

```bash
pytest tests/ -v
```

33 теста, все проходят ✅

## Документация (GitHub Pages)

```bash
mkdocs build      # собрать
mkdocs serve      # локальный просмотр
mkdocs gh-deploy  # деплой на GitHub Pages
```

## Структура проекта

```
Lr1/
├── app/
│   ├── main.py            # FastAPI app + lifespan
│   ├── database.py        # Engine & session
│   ├── models.py           # SQLModel tables (6 моделей + M2M link)
│   ├── schemas.py          # Pydantic v2 schemas
│   ├── auth.py             # JWT + password hashing
│   ├── dependencies.py     # get_current_user
│   ├── crud.py             # CRUD operations
│   └── routers/            # API routers (auth, categories, transactions, budgets, tags)
├── migrations/             # Alembic migrations
├── tests/                  # 33 pytest tests
├── docs/                   # MkDocs documentation
├── Dockerfile              # API container
├── docker-compose.yml      # PostgreSQL + API
├── .dockerignore
├── mkdocs.yml
├── alembic.ini
└── requirements.txt
```

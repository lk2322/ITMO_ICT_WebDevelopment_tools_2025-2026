# Лабораторная работа №3 — Упаковка FastAPI в Docker, работа с данными и очереди

**Студент:** Владзиевский Евгений | **Группа:** K3341  
**Дисциплина:** Средства Web-программирования | **Срок сдачи:** 2 июня 2026

---

## Цель работы

Научиться упаковывать FastAPI приложение в Docker, интегрировать парсер данных с базой данных и вызывать парсер через API и очередь задач.

---

## Выполненные задачи

### Подзадача 1 — Упаковка FastAPI, БД и парсера в Docker

Создана многоконтейнерная система из 6 сервисов:

| Сервис | Контейнер | Порт | Описание |
|--------|-----------|------|----------|
| **API** | `finance-api` | 8000 | Основное FastAPI-приложение (финансы) |
| **Parser** | `finance-parser` | 8001 | FastAPI-сервис парсера веб-страниц |
| **DB** | `finance-postgres` | 5432 | PostgreSQL 16 |
| **Redis** | `finance-redis` | 6379 | Брокер для Celery |
| **Celery Worker** | `finance-celery-worker` | – | Фоновая обработка задач |
| **Celery Beat** | `finance-celery-beat` | – | Периодические задачи |

### Подзадача 2 — Вызов парсера из FastAPI

Добавлен эндпоинт `POST /parse` в основное FastAPI-приложение:

- Принимает `{"url": "https://example.com"}`
- Отправляет HTTP-запрос сервису `parser:8001/parse`
- Парсер загружает страницу, извлекает `<title>`
- Возвращает результат клиенту

### Подзадача 3 — Вызов парсера через очередь Celery + Redis

Реализована асинхронная очередь задач:

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/parse/async` | POST | Ставит задачу парсинга в очередь Celery, возвращает `task_id` |
| `/parse/status/{task_id}` | GET | Проверяет статус задачи (PENDING → PROGRESS → SUCCESS) |
| `/parse` | POST | Синхронный вызов парсера (без очереди) |

**Как работает очередь:**

1. Клиент отправляет `POST /parse/async {"url": "..."}`
2. FastAPI ставит задачу в Redis через Celery
3. Celery Worker забирает задачу из очереди
4. Worker выполняет парсинг в фоне (загружает HTML, извлекает заголовок)
5. Результат сохраняется в Redis
6. Клиент запрашивает `GET /parse/status/{task_id}` для получения статуса

---

## Структура проекта

```
Lr3/
├── app/
│   ├── main.py                 # FastAPI app (добавлен parser router)
│   ├── database.py             # SQLModel engine + session
│   ├── models.py               # 6 моделей (из ЛР1)
│   ├── schemas.py              # Pydantic схемы
│   ├── auth.py                 # JWT аутентификация
│   ├── dependencies.py         # Зависимости
│   ├── crud.py                 # CRUD операции
│   └── routers/
│       ├── parser.py           # ** NEW: эндпоинты парсинга **
│       ├── auth.py
│       ├── categories.py
│       ├── transactions.py
│       ├── budgets.py
│       └── tags.py
├── parser/
│   ├── main.py                 # ** NEW: отдельный FastAPI сервис парсера **
│   └── Dockerfile              # ** NEW: Dockerfile для парсера **
├── celery_app.py               # ** NEW: Celery конфигурация + задачи **
├── Dockerfile                  # Основной Dockerfile (API + Celery)
├── docker-compose.yml          # Оркестрация всех сервисов
├── requirements.txt            # Зависимости (+celery, redis, requests, bs4)
├── alembic.ini                 # Миграции БД
├── tests/                      # Тесты (из ЛР1)
├── .gitignore
├── mkdocs.yml
├── docs/
│   └── index.md
└── README.md
```

---

## Запуск

```bash
# 1. Запустить все сервисы одной командой
docker compose up --build -d

# 2. Проверить статус
docker compose ps

# 3. Swagger UI основного API
open http://localhost:8000/docs

# 4. Swagger UI парсера
open http://localhost:8001/docs

# 5. Синхронный парсинг
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.python.org"}'

# 6. Асинхронный парсинг через очередь
curl -X POST http://localhost:8000/parse/async \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.python.org"}'
# → {"task_id": "...", "status": "queued"}

# 7. Проверить статус задачи
curl http://localhost:8000/parse/status/{task_id}

# 8. Остановить
docker compose down
docker compose down -v  # с удалением данных
```

---

## Архитектура взаимодействия сервисов

```
Клиент
  │
  ├── POST /parse ──────────► API (:8000) ──► Parser (:8001) ──► Internet
  │                              │                    │
  │                              │                    └── Извлекает <title>
  │                              │
  └── POST /parse/async ─────► API (:8000) ──► Redis (:6379)
                                   │                 │
                                   │        Celery Worker берёт задачу
                                   │                 │
                                   │        Worker ──► Internet ──► <title>
                                   │                 │
                                   │        Результат → Redis
                                   │
                              GET /parse/status/{id} → читает Redis
```

---

## Ключевые технологии

| Компонент | Технология | Назначение |
|-----------|-----------|------------|
| API | FastAPI 0.128 | Основное веб-приложение |
| Parser | FastAPI + BeautifulSoup4 | Парсинг веб-страниц |
| БД | PostgreSQL 16 + SQLModel | Хранение данных |
| Брокер | Redis 7 | Очередь задач Celery |
| Очередь | Celery 5.3 | Асинхронная обработка |
| Оркестрация | Docker Compose | Управление контейнерами |
| Документация | MkDocs Material | GitHub Pages |

---

## Документация (GitHub Pages)

```bash
mkdocs build      # собрать
mkdocs serve      # локальный просмотр
mkdocs gh-deploy  # деплой на GitHub Pages
```

---

**Дата выполнения:** 5 мая 2026

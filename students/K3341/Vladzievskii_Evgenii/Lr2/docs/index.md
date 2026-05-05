# Лабораторная работа №2 — Потоки. Процессы. Асинхронность

**Студент:** Владзиевский Евгений | **Группа:** K3341  
**Дисциплина:** Средства Web-программирования | **Срок сдачи:** 12 мая 2026

---

## Цель работы

Понять отличия между потоками (threading), процессами (multiprocessing) и асинхронностью (asyncio) в Python. Освоить практические навыки создания параллельных и асинхронных программ, важные для работы с большими объёмами данных и высоконагруженными веб-сервисами.

---

## Структура проекта

```
Lr2/
├── README.md                   # Документация
├── requirements.txt            # Зависимости
├── mkdocs.yml                  # MkDocs конфигурация
├── task1/                      # Задача 1 — Параллельное вычисление суммы
│   ├── threading_sum.py        # Threading
│   ├── multiprocessing_sum.py  # Multiprocessing
│   ├── async_sum.py            # Asyncio + ProcessPoolExecutor
│   └── benchmark.py            # Сравнительный бенчмарк (CPU-bound)
└── task2/                      # Задача 2 — Параллельный парсинг веб-страниц
    ├── db.py                   # Модель БД (SQLite) + вспомогательные функции
    ├── threading_parser.py     # Threading + requests
    ├── multiprocessing_parser.py # Multiprocessing + requests
    └── async_parser.py         # Asyncio + aiohttp
```

---

## Задача 1. Различия между threading, multiprocessing и async

### Описание

Написаны три программы, вычисляющие сумму всех чисел от 1 до 1 000 000 000 000 (один триллион) с использованием трёх подходов:

1. **threading** — модуль `threading.Thread`
2. **multiprocessing** — модуль `multiprocessing.Pool`
3. **asyncio** — `async/await` + `concurrent.futures.ProcessPoolExecutor`

Каждая программа разбивает диапазон на 8 равных частей и вычисляет частичные суммы параллельно. Для вычисления используется **формула арифметической прогрессии** (Гаусса):

\[
S_n = \frac{(a_1 + a_n) \cdot n}{2}
\]

где \(n = 1\,000\,000\,000\,000\), \(a_1 = 1\), \(a_n = n\).

### Результаты работы программ

Все три программы выдают одинаковый корректный результат:

```
Expected: 500_000_000_000_500_000_000_000
Total:    500_000_000_000_500_000_000_000
Match:    True ✅
```

### Бенчмарк (CPU-bound задача)

Для наглядной демонстрации различий между подходами на CPU-bound задачах создан `benchmark.py`, который использует `sum(range(...))` — реальную C-итерацию по 100 миллионам чисел:

| Подход | Время (сек) | Ускорение | Примечание |
|--------|------------|-----------|------------|
| **Sequential** (базовый) | 1.0425 | — | Последовательное выполнение |
| **Threading** (8 потоков) | 0.8256 | ×1.26 | GIL ограничивает параллелизм |
| **Multiprocessing** (8 процессов) | 0.1694 | ×6.15 | Истинный параллелизм на CPU |
| **Async + ProcessPoolExecutor** | 0.1782 | ×5.85 | Аналог multiprocessing |

### Анализ результатов

- **Threading** — из-за GIL (Global Interpreter Lock) только один поток может исполнять Python-код одновременно. Небольшое ускорение (×1.26) происходит за счёт того, что `sum(range())` частично выполняется в C-расширении, где GIL может освобождаться.
- **Multiprocessing** — каждый процесс имеет собственный GIL и выполняется на отдельном ядре CPU. Показывает наилучшее ускорение (×6.15) для CPU-bound задач. Накладные расходы на создание процессов окупаются параллельным выполнением.
- **Async + Executor** — asyncio сам по себе не предназначен для CPU-bound задач, но в комбинации с `ProcessPoolExecutor` обеспечивает параллелизм на уровне, сравнимом с multiprocessing.

---

## Задача 2. Параллельный парсинг веб-страниц

### Описание

Реализован параллельный парсер, который загружает 24 веб-страницы, извлекает из них заголовки (`<title>`) и сохраняет результаты в базу данных.

База данных расширена таблицей `parsed_page`:

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER (PK) | Уникальный идентификатор |
| `url` | VARCHAR | URL спаршенной страницы |
| `title` | VARCHAR | Заголовок страницы |
| `status_code` | INTEGER | HTTP-статус ответа |
| `parsed_at` | DATETIME | Время парсинга |

### Реализации

1. **Threading** — `threading.Thread` + `requests` + `BeautifulSoup`
2. **Multiprocessing** — `multiprocessing.Process` + `requests` + очередь результатов
3. **Async** — `asyncio` + `aiohttp` (асинхронные HTTP-запросы) + `BeautifulSoup`

### Результаты (24 URL, 8 воркеров)

| Подход | Время (сек) | Успешно | Без заголовка | Примечание |
|--------|------------|---------|---------------|------------|
| **Threading** | 2.12 | 24/24 | 8 | Потоки + синхронный requests |
| **Multiprocessing** | 1.46 | 24/24 | 8 | Процессы + синхронный requests |
| **Async (aiohttp)** | 1.92 | 24/24 | 8 | Asyncio + асинхронные запросы |

### Анализ результатов

В отличие от CPU-bound задач (Задача 1), для **I/O-bound задач** (сетевые запросы) все три подхода показывают сопоставимые результаты:

- **Threading** — потоки хорошо подходят для I/O, так как GIL освобождается при блокирующих операциях ввода-вывода (сетевые вызовы `requests.get()`). Накладные расходы минимальны.
- **Multiprocessing** — процессы тоже дают хороший параллелизм, но имеют бо́льшие накладные расходы на создание и межпроцессное взаимодействие (очередь `Queue`). Для чисто I/O задач это избыточно.
- **Async (aiohttp)** — **лучший выбор для I/O-bound задач**. Все запросы выполняются в одном потоке, кооперативно переключаясь в моменты ожидания сети. Нет накладных расходов на создание потоков/процессов. Время немного выше из-за того, что Wikipedia возвращает 403 для части запросов (влияет на тайминги).

Сетевые флуктуации и разное время ответа серверов объясняют небольшие расхождения в результатах. Для стабильных сетевых условий asyncio обычно показывает наилучшие результаты.

### Список URL для парсинга

| # | URL | Заголовок | Статус |
|---|-----|-----------|--------|
| 1 | python.org | Welcome to Python.org | 200 |
| 2 | docs.python.org/3/ | 3.14.5rc1 Documentation | 200 |
| 3 | fastapi.tiangolo.com | FastAPI | 200 |
| 4 | wikipedia.org/wiki/Python | (no title) | 403 |
| 5 | wikipedia.org/wiki/Asynchronous_I/O | (no title) | 403 |
| 6 | wikipedia.org/wiki/Thread_(computing) | (no title) | 403 |
| 7 | wikipedia.org/wiki/Multiprocessing | (no title) | 403 |
| 8 | wikipedia.org/wiki/Web_scraping | (no title) | 403 |
| 9 | httpbin.org | httpbin.org | 200 |
| 10 | httpbin.org/status/200 | (no title) | 200 |
| 11 | httpbin.org/status/404 | (no title) | 404 |
| 12 | httpbin.org/headers | (no title) | 200 |
| 13 | sqlalchemy.org | SQLAlchemy | 200 |
| 14 | docs.python.org/3/library/threading | threading — Thread-based parallelism | 200 |
| 15 | docs.python.org/3/library/multiprocessing | multiprocessing — Process-based parallelism | 200 |
| 16 | docs.python.org/3/library/asyncio | asyncio — Asynchronous I/O | 200 |
| 17 | docs.docker.com | Docker Docs | 200 |
| 18 | hub.docker.com | Docker Hub | 200 |
| 19 | github.com | GitHub | 200 |
| 20 | git-scm.com | Git | 200 |
| 21 | postgresql.org | PostgreSQL | 200 |
| 22 | nginx.org | nginx | 200 |
| 23 | redis.io | Redis | 200 |
| 24 | djangoproject.com | Django | 200 |

---

## Сравнительная таблица подходов

| Характеристика | Threading | Multiprocessing | Async (asyncio) |
|---------------|-----------|-----------------|-----------------|
| **Механизм** | Несколько потоков в одном процессе | Несколько независимых процессов | Один поток, кооперативная многозадачность |
| **GIL** | Ограничивает CPU-параллелизм | Свой GIL на процесс | Не мешает (один поток) |
| **CPU-bound** | ❌ Медленно (GIL) | ✅ Быстро | ❌ Без executor |
| **I/O-bound** | ✅ Хорошо | ✅ Хорошо (избыточно) | ✅✅ Лучший выбор |
| **Память** | Общая память процесса | Изолированная (копирование) | Общая память |
| **Создание** | Лёгкое (~мс) | Тяжёлое (~50-100мс) | Легчайшее (~µс) |
| **Обмен данными** | Общие переменные (+Lock) | Queue, Pipe, shared memory | Общие переменные |
| **Типичные применения** | GUI, сетевые запросы, файлы | Вычисления, ML, обработка данных | Веб-серверы, API, БД, микросервисы |

---

## Выводы

1. **Threading** подходит для I/O-bound задач (сеть, файлы, БД). Для CPU-bound задач бесполезен из-за GIL.
2. **Multiprocessing** — единственный способ добиться истинного параллелизма в Python для CPU-bound задач. Цена — бо́льшие накладные расходы и изолированная память.
3. **Asyncio** — современный стандарт для высоконагруженных I/O-bound приложений (веб-серверы, API-клиенты). Позволяет обрабатывать тысячи соединений в одном потоке без накладных расходов на потоки/процессы.

Для реальных проектов выбор подхода зависит от типа нагрузки:
- **I/O-bound** → asyncio (или threading как fallback)
- **CPU-bound** → multiprocessing
- **Смешанная нагрузка** → asyncio + ProcessPoolExecutor

---

## Запуск

```bash
# Установка зависимостей
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Задача 1 — вычисление суммы
python task1/threading_sum.py
python task1/multiprocessing_sum.py
python task1/async_sum.py
python task1/benchmark.py       # бенчмарк

# Задача 2 — парсинг веб-страниц
python task2/threading_parser.py
python task2/multiprocessing_parser.py
python task2/async_parser.py
```

---

## Использованные технологии

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.12 |
| Threading | `threading` (stdlib) |
| Multiprocessing | `multiprocessing` (stdlib) |
| Asyncio | `asyncio` (stdlib) |
| HTTP (sync) | `requests` |
| HTTP (async) | `aiohttp` |
| HTML-парсинг | `beautifulsoup4` |
| База данных | SQLite + `sqlmodel` |
| Бенчмарк | `time.perf_counter()` |

---

**Дата выполнения:** 5 мая 2026  
**Оценка:** Качество и эффективность реализации всех трёх подходов, понимание особенностей threading, multiprocessing и async, анализ и сравнение времени выполнения.

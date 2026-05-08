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
└── task2/                      # Задача 2 — Параллельный парсинг книг
    ├── db.py                   # Синхронная БД (psycopg2): threading + multiprocessing
    ├── async_db.py             # Асинхронная БД (asyncpg): asyncio
    ├── urls.py                 # Список URL книг (books.toscrape.com)
    ├── threading_parser.py     # Threading + requests
    ├── multiprocessing_parser.py # Multiprocessing + requests
    └── async_parser.py         # Asyncio + aiohttp + async БД
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

Реализован параллельный парсер, который загружает 24 страницы книг с [books.toscrape.com](https://books.toscrape.com) (специальный сайт для практики веб-скрапинга), извлекает название книги (`<h1>`) и цену (`.price_color`), и сохраняет результат в **существующие таблицы БД из ЛР1**.

Данные распределяются по таблицам:
- **`user`** — создаётся служебный пользователь `parser@lab2.local`
- **`category`** — категория «Books» (тип EXPENSE)
- **`transaction`** — каждая книга = одна транзакция (amount = цена, description = название)

### Реализации

1. **Threading** — `threading.Thread` + `requests` + `BeautifulSoup`
2. **Multiprocessing** — `multiprocessing.Process` + `requests` + очередь результатов (запись в БД — только в главном процессе)
3. **Async** — `asyncio` + `aiohttp` (асинхронные HTTP-запросы) + `BeautifulSoup` + `async_db` (асинхронная БД через sqlalchemy.ext.asyncio + asyncpg)

### Результаты (24 книги, 8 воркеров, PostgreSQL)

| Подход | Время (сек) | Транзакций | Общая сумма | Примечание |
|--------|------------|-----------|-------------|------------|
| **Threading** | 2.39 | 24 | $866.92 | Потоки + синхронный requests |
| **Multiprocessing** | 2.95 | 24 | $866.92 | Процессы + синхронный requests |
| **Async (aiohttp)** | 2.06 | 24 | $866.92 | Asyncio + асинхронные запросы |

### Анализ результатов

Для **I/O-bound задач** (сетевые запросы к books.toscrape.com) все три подхода показывают сопоставимые результаты:

- **Async (aiohttp + async DB)** — показал лучшее время (2.06 сек). Все HTTP-запросы и операции с БД выполняются асинхронно без блокировки event loop. Идеальный выбор для I/O-bound задач с интенсивной работой с БД.
- **Threading** — близкий результат (2.39 сек). GIL освобождается при блокирующем I/O (`requests.get()`), поэтому потоки эффективны для сетевых задач.
- **Multiprocessing** — медленнее (2.95 сек) из-за накладных расходов на создание процессов и передачу данных через `Queue`. Для чисто I/O задач избыточен, но необходим для CPU-bound.

### Список книг (первые 10 из 24)

| # | Книга | Цена |
|---|-------|------|
| 1 | A Light in the Attic | $51.77 |
| 2 | Tipping the Velvet | $53.74 |
| 3 | Soumission | $50.10 |
| 4 | Sharp Objects | $47.82 |
| 5 | Sapiens: A Brief History of Humankind | $54.23 |
| 6 | The Requiem Red | $22.65 |
| 7 | The Dirty Little Secrets of Getting Your Dream Job | $33.34 |
| 8 | The Coming Woman | $17.93 |
| 9 | The Boys in the Boat | $22.60 |
| 10 | The Black Maria | $52.15 |

Полный список: [`task2/urls.py`](task2/urls.py)

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

# Запуск БД из ЛР1 (PostgreSQL)
cd ../Lr1 && docker compose up db -d && cd ../Lr2

# Задача 1 — вычисление суммы
python task1/threading_sum.py
python task1/multiprocessing_sum.py
python task1/async_sum.py
python task1/benchmark.py       # бенчмарк

# Задача 2 — парсинг книг (сохраняет в таблицы ЛР1)
PYTHONPATH=../Lr1 python task2/threading_parser.py
PYTHONPATH=../Lr1 python task2/multiprocessing_parser.py
PYTHONPATH=../Lr1 python task2/async_parser.py
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
| **База данных** | PostgreSQL + `sqlmodel` (БД из ЛР1) |
| **Async БД** | `sqlalchemy[asyncio]` + `asyncpg` |
| Бенчмарк | `time.perf_counter()` |

---

**Дата выполнения:** 5 мая 2026  
**Оценка:** Качество и эффективность реализации всех трёх подходов, понимание особенностей threading, multiprocessing и async, анализ и сравнение времени выполнения.

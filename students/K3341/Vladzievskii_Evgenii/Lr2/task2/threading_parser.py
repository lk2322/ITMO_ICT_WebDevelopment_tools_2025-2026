"""
Лабораторная работа №2, Задача 2 — threading parser
Параллельный парсинг заголовков веб-страниц с использованием threading.

Особенности:
- Потоки хорошо подходят для I/O-bound задач (сетевые запросы)
- GIL освобождается при вызове requests.get() (сетевой ввод-вывод)
- Результаты сохраняются в SQLite БД (таблица parsed_page)
- Список URL делится между потоками равномерно
"""

import threading
import time
import os
import sys
from typing import List

import requests
from bs4 import BeautifulSoup

# Подключаем БД
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init_db, save_page, stats

# Список URL для парсинга
URLS = [
    "https://www.python.org",
    "https://docs.python.org/3/",
    "https://fastapi.tiangolo.com",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://en.wikipedia.org/wiki/Asynchronous_I/O",
    "https://en.wikipedia.org/wiki/Thread_(computing)",
    "https://en.wikipedia.org/wiki/Multiprocessing",
    "https://en.wikipedia.org/wiki/Web_scraping",
    "https://httpbin.org",
    "https://httpbin.org/status/200",
    "https://httpbin.org/status/404",
    "https://httpbin.org/headers",
    "https://www.sqlalchemy.org",
    "https://docs.python.org/3/library/threading.html",
    "https://docs.python.org/3/library/multiprocessing.html",
    "https://docs.python.org/3/library/asyncio.html",
    "https://docs.docker.com",
    "https://hub.docker.com",
    "https://github.com",
    "https://git-scm.com",
    "https://www.postgresql.org",
    "https://nginx.org",
    "https://redis.io",
    "https://www.djangoproject.com",
]

NUM_THREADS = 8  # Количество потоков
lock = threading.Lock()
results_summary: List[dict] = []


def parse_and_save(url: str) -> dict:
    """
    Загружает HTML-страницу по URL, извлекает заголовок (<title>)
    и сохраняет результат в БД.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else None
        status = response.status_code
    except requests.RequestException as e:
        title = None
        status = getattr(e.response, "status_code", 0) if hasattr(e, "response") else 0

    page = save_page(url, title, status)

    result = {"url": url, "title": title, "status": status}
    with lock:
        results_summary.append(result)

    return result


def worker(urls: List[str], worker_id: int) -> None:
    """Функция-воркер для потока."""
    for url in urls:
        result = parse_and_save(url)
        with lock:
            print(
                f"[Thread-{worker_id}] {url:50s} -> "
                f"{result['title'][:50] if result['title'] else '(no title)':50s} "
                f"[{result['status']}]"
            )


def main() -> None:
    # Инициализация БД
    init_db()
    print(f"Database initialized: {os.path.abspath('lab2_parsed.db')}\n")

    # Равномерно распределяем URL между потоками
    url_chunks = [[] for _ in range(NUM_THREADS)]
    for i, url in enumerate(URLS):
        url_chunks[i % NUM_THREADS].append(url)

    threads = []
    for i in range(NUM_THREADS):
        print(
            f"[Thread-{i+1}] URLs: {len(url_chunks[i])} "
            f"({url_chunks[i][0][:40] if url_chunks[i] else 'none'} ...)"
        )

    print(f"\nStarting {NUM_THREADS} threads for {len(URLS)} URLs...\n")
    start_time = time.perf_counter()

    for i in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(url_chunks[i], i + 1))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start_time

    # Статистика
    db_stats = stats()
    print(f"\n{'='*60}")
    print(f"Approach:       threading ({NUM_THREADS} threads)")
    print(f"Total URLs:     {len(URLS)}")
    print(f"Parsed:         {db_stats['total']}")
    print(f"With title:     {db_stats['with_title']}")
    print(f"Without title:  {db_stats['without_title']}")
    print(f"Time elapsed:   {elapsed:.4f} sec")
    print(f"CPU cores:      {os.cpu_count()}")
    print(f"Timestamps:     {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    print(f"\nLast 5 parsed:")
    for page in db_stats["latest"]:
        t = page.title[:60] if page.title else "(no title)"
        print(f"  [{page.status_code}] {page.url:50s} -> {t}")


if __name__ == "__main__":
    main()

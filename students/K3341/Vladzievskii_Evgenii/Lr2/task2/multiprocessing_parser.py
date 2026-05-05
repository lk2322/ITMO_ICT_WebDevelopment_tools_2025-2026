"""
Лабораторная работа №2, Задача 2 — multiprocessing parser
Параллельный парсинг заголовков веб-страниц с использованием multiprocessing.

Особенности:
- Каждый процесс имеет собственное адресное пространство и GIL
- Истинный параллелизм — идеально для смешанных CPU+I/O задач
- Накладные расходы выше (создание процессов, pickling данных)
- Для I/O-bound задач (сеть) разница с threading минимальна,
  но для смешанных нагрузок multiprocessing выигрывает

Примечание: SQLite не поддерживает запись из нескольких процессов
одновременно. Решается через очередь результатов в главный процесс.
"""

import multiprocessing
import time
import os
import sys
from typing import List

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init_db, save_page, stats

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

NUM_PROCESSES = min(8, os.cpu_count() or 4)


def parse_url(url: str) -> dict:
    """
    Загружает HTML-страницу по URL и извлекает заголовок.
    Выполняется в дочернем процессе.
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

    return {"url": url, "title": title, "status_code": status}


def worker(urls: List[str], worker_id: int, result_queue: multiprocessing.Queue) -> None:
    """Функция-воркер для процесса."""
    for url in urls:
        result = parse_url(url)
        result_queue.put(result)
        t = result["title"][:50] if result["title"] else "(no title)"
        print(f"[Process-{worker_id}] {url:50s} -> {t:50s} [{result['status_code']}]")


def main() -> None:
    # Инициализация БД в главном процессе
    init_db()
    print(f"Database initialized: {os.path.abspath('lab2_parsed.db')}\n")

    # Равномерно распределяем URL между процессами
    url_chunks = [[] for _ in range(NUM_PROCESSES)]
    for i, url in enumerate(URLS):
        url_chunks[i % NUM_PROCESSES].append(url)

    for i in range(NUM_PROCESSES):
        print(
            f"[Process-{i+1}] URLs: {len(url_chunks[i])} "
            f"({url_chunks[i][0][:40] if url_chunks[i] else 'none'} ...)"
        )

    print(
        f"\nStarting {NUM_PROCESSES} processes for {len(URLS)} URLs...\n"
    )
    start_time = time.perf_counter()

    # Очередь для сбора результатов от дочерних процессов
    result_queue = multiprocessing.Queue()

    processes = []
    for i in range(NUM_PROCESSES):
        p = multiprocessing.Process(
            target=worker, args=(url_chunks[i], i + 1, result_queue)
        )
        processes.append(p)
        p.start()

    # Собираем результаты и сохраняем в БД из главного процесса
    # (SQLite не поддерживает многопроцессную запись)
    saved = 0
    while saved < len(URLS):
        result = result_queue.get()
        save_page(result["url"], result["title"], result["status_code"])
        saved += 1

    for p in processes:
        p.join()

    elapsed = time.perf_counter() - start_time

    # Статистика
    db_stats = stats()
    print(f"\n{'='*60}")
    print(f"Approach:       multiprocessing ({NUM_PROCESSES} processes)")
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
    multiprocessing.freeze_support()
    main()

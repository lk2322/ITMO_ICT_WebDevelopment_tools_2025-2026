"""
Лабораторная работа №2, Задача 2 — async parser (asyncio + aiohttp)
Параллельный парсинг заголовков веб-страниц с использованием asyncio + aiohttp.

Особенности:
- Asyncio — идеальный выбор для I/O-bound задач (сеть)
- Все запросы выполняются в одном потоке, кооперативно переключаясь
  в моменты ожидания сетевого ответа (await)
- Меньше накладных расходов, чем у потоков и процессов
- aiohttp — асинхронный HTTP-клиент (не блокирует event loop)
- BeautifulSoup используется синхронно, но это не проблема,
  так как парсинг HTML очень быстрый
"""

import asyncio
import time
import os
import sys
from typing import List

import aiohttp
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

MAX_CONCURRENT = 8  # Максимум одновременных запросов


async def fetch_title(
    session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore
) -> dict:
    """
    Асинхронно загружает HTML-страницу и извлекает заголовок.

    Semaphore ограничивает количество одновременных запросов,
    чтобы не перегружать сеть и серверы.
    """
    async with semaphore:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                title = soup.title.string.strip() if soup.title else None
                status = resp.status
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            title = None
            status = 0

    # Сохраняем в БД (синхронно — SQLite не асинхронный)
    save_page(url, title, status)

    t = title[:50] if title else "(no title)"
    print(f"[Async] {url:50s} -> {t:50s} [{status}]")

    return {"url": url, "title": title, "status_code": status}


async def main_async() -> None:
    # Инициализация БД
    init_db()
    print(f"Database initialized: {os.path.abspath('lab2_parsed.db')}\n")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    print(
        f"Starting async parser for {len(URLS)} URLs "
        f"(max {MAX_CONCURRENT} concurrent)...\n"
    )

    start_time = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_title(session, url, semaphore) for url in URLS]
        results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start_time

    # Статистика
    db_stats = stats()
    success = sum(1 for r in results if r["title"] is not None)
    failed = sum(1 for r in results if r["title"] is None)

    print(f"\n{'='*60}")
    print(f"Approach:       asyncio + aiohttp (max {MAX_CONCURRENT} concurrent)")
    print(f"Total URLs:     {len(URLS)}")
    print(f"With title:     {success}")
    print(f"Without title:  {failed}")
    print(f"DB records:     {db_stats['total']}")
    print(f"Time elapsed:   {elapsed:.4f} sec")
    print(f"CPU cores:      {os.cpu_count()}")
    print(f"Timestamps:     {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    print(f"\nLast 5 parsed:")
    for page in db_stats["latest"]:
        t = page.title[:60] if page.title else "(no title)"
        print(f"  [{page.status_code}] {page.url:50s} -> {t}")


if __name__ == "__main__":
    asyncio.run(main_async())

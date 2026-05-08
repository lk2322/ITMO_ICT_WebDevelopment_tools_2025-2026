"""
Лабораторная работа №2, Задача 2 — multiprocessing parser
Параллельный парсинг книг с books.toscrape.com через multiprocessing.

SQLite не поддерживает запись из нескольких процессов, поэтому
в дочерних процессах только парсинг, а запись в БД — в главном.
"""
import multiprocessing
import time
import os
import sys
from datetime import datetime, timezone
from typing import List

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init_db, save_transaction, stats
from urls import BOOK_URLS

URLS = BOOK_URLS
NUM_PROCESSES = min(8, os.cpu_count() or 4)


def parse_book(url: str) -> dict:
    """
    Загружает страницу книги и извлекает название и цену.
    Выполняется в дочернем процессе (без доступа к БД).
    """
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        title = soup.find("h1").text.strip()
        price_text = soup.find("p", class_="price_color").text.strip()
        return {"url": url, "title": title, "price_text": price_text}
    except Exception as e:
        return {"url": url, "title": None, "price_text": None, "error": str(e)[:80]}


def worker(
    urls: List[str], worker_id: int, result_queue: multiprocessing.Queue
) -> None:
    for url in urls:
        result = parse_book(url)
        result_queue.put(result)
        t = result["title"][:50] if result["title"] else "FAIL"
        print(f"[Process-{worker_id}] {t}")


def main() -> None:
    init_db()
    print(f"DB ready: {len(URLS)} books to parse\n")

    url_chunks = [[] for _ in range(NUM_PROCESSES)]
    for i, url in enumerate(URLS):
        url_chunks[i % NUM_PROCESSES].append(url)

    print(f"Starting {NUM_PROCESSES} processes for {len(URLS)} books...\n")
    start_time = time.perf_counter()

    result_queue = multiprocessing.Queue()
    processes = []

    for i in range(NUM_PROCESSES):
        p = multiprocessing.Process(
            target=worker, args=(url_chunks[i], i + 1, result_queue)
        )
        processes.append(p)
        p.start()

    # Собираем результаты и сохраняем в БД из главного процесса
    saved = 0
    while saved < len(URLS):
        result = result_queue.get()
        if result.get("title"):
            save_transaction(result["title"], result["price_text"])
        saved += 1

    for p in processes:
        p.join()

    elapsed = time.perf_counter() - start_time
    db_stats = stats()

    print(f"\n{'='*60}")
    print(f"Approach:       multiprocessing ({NUM_PROCESSES} processes)")
    print(f"Total books:    {len(URLS)}")
    print(f"Transactions:   {db_stats['total']}")
    print(f"Total amount:   ${db_stats['total_amount']:.2f}")
    print(f"Time elapsed:   {elapsed:.4f} sec")
    print(f"{'='*60}")

    print(f"\nLast 5 transactions:")
    for t in db_stats["latest"]:
        print(f"  ${t.amount:.2f}  {t.description[:60]}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

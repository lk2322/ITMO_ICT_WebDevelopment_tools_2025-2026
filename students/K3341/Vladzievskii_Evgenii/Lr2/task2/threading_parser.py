"""
Лабораторная работа №2, Задача 2 — threading parser
Параллельный парсинг книг с books.toscrape.com через threading.

Сохраняет названия и цены книг в таблицу transaction БД из ЛР1
(сумма = цена книги, описание = название, категория = Books).
"""
import threading
import time
import os
import sys
from typing import List

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init_db, save_transaction, stats
from urls import BOOK_URLS

URLS = BOOK_URLS
NUM_THREADS = 8
lock = threading.Lock()
results: List[dict] = []


def parse_and_save(url: str) -> dict:
    """Загружает страницу книги, извлекает название и цену, сохраняет в БД."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        title = soup.find("h1").text.strip()
        price_text = soup.find("p", class_="price_color").text.strip()
        txn = save_transaction(title, price_text)
        return {"url": url, "title": title, "amount": txn["amount"]}
    except Exception as e:
        return {"url": url, "title": str(e)[:80], "amount": 0}


def worker(urls: List[str], worker_id: int) -> None:
    for url in urls:
        result = parse_and_save(url)
        with lock:
            results.append(result)
            amt = f"${result['amount']:.2f}" if result["amount"] else "FAIL"
            t = result["title"][:50]
            print(f"[Thread-{worker_id}] {amt:>10s}  {t}")


def main() -> None:
    init_db()
    print(f"DB ready: {len(URLS)} books to parse\n")

    url_chunks = [[] for _ in range(NUM_THREADS)]
    for i, url in enumerate(URLS):
        url_chunks[i % NUM_THREADS].append(url)

    print(f"Starting {NUM_THREADS} threads for {len(URLS)} books...\n")
    start_time = time.perf_counter()

    threads = []
    for i in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(url_chunks[i], i + 1))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start_time
    db_stats = stats()

    print(f"\n{'='*60}")
    print(f"Approach:       threading ({NUM_THREADS} threads)")
    print(f"Total books:    {len(URLS)}")
    print(f"Transactions:   {db_stats['total']}")
    print(f"Total amount:   ${db_stats['total_amount']:.2f}")
    print(f"Time elapsed:   {elapsed:.4f} sec")
    print(f"{'='*60}")

    print(f"\nLast 5 transactions:")
    for t in db_stats["latest"]:
        print(f"  ${t.amount:.2f}  {t.description[:60]}")


if __name__ == "__main__":
    main()

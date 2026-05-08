"""
Лабораторная работа №2, Задача 2 — async parser (asyncio + aiohttp)
Параллельный парсинг книг с books.toscrape.com через asyncio + aiohttp.

Сохраняет названия и цены книг в таблицу transaction БД из ЛР1.
"""
import asyncio
import time
import os
import sys
from typing import List

import aiohttp
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import init_db, save_transaction, stats
from urls import BOOK_URLS

URLS = BOOK_URLS
MAX_CONCURRENT = 8


async def fetch_and_save(
    session: aiohttp.ClientSession, url: str, semaphore: asyncio.Semaphore
) -> dict:
    """Асинхронно загружает страницу книги, извлекает название/цену, сохраняет в БД."""
    async with semaphore:
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                html = await resp.read()
                soup = BeautifulSoup(html, "html.parser")
                title = soup.find("h1").text.strip()
                price_text = soup.find("p", class_="price_color").text.strip()
                txn = save_transaction(title, price_text)
                return {"url": url, "title": title, "amount": txn["amount"]}
        except Exception as e:
            return {"url": url, "title": str(e)[:80], "amount": 0}


async def main_async() -> None:
    init_db()
    print(f"DB ready: {len(URLS)} books to parse\n")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    print(
        f"Starting async parser for {len(URLS)} books "
        f"(max {MAX_CONCURRENT} concurrent)...\n"
    )

    start_time = time.perf_counter()

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_save(session, url, semaphore) for url in URLS]
        results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start_time
    db_stats = stats()
    success = sum(1 for r in results if r["amount"] > 0)

    print(f"\n{'='*60}")
    print(f"Approach:       asyncio + aiohttp (max {MAX_CONCURRENT} concurrent)")
    print(f"Total books:    {len(URLS)}")
    print(f"Parsed OK:      {success}")
    print(f"Transactions:   {db_stats['total']}")
    print(f"Total amount:   ${db_stats['total_amount']:.2f}")
    print(f"Time elapsed:   {elapsed:.4f} sec")
    print(f"{'='*60}")

    print(f"\nLast 5 transactions:")
    for t in db_stats["latest"]:
        print(f"  ${t.amount:.2f}  {t.description[:60]}")


if __name__ == "__main__":
    asyncio.run(main_async())

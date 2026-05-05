"""
Лабораторная работа №2, Задача 1 — asyncio (асинхронность)
Сумма чисел от 1 до 1 000 000 000 000 с использованием asyncio.

Особенности:
- Async/await обеспечивает кооперативную многозадачность в одном потоке
- Для CPU-bound задач asyncio не даёт ускорения, но демонстрирует
  возможность совмещения с ProcessPoolExecutor для реального параллелизма
- В данной программе показаны два варианта:
  1) Чистый asyncio (последовательное выполнение — время = O(n))
  2) asyncio + ProcessPoolExecutor (истинный параллелизм)

Примечание: asyncio предназначен для I/O-bound задач (сеть, БД, файлы).
Для CPU-bound задач правильный подход — ProcessPoolExecutor.
"""

import asyncio
import time
import os
from concurrent.futures import ProcessPoolExecutor


N = 1_000_000_000_000  # Общее количество чисел
NUM_WORKERS = min(8, os.cpu_count() or 4)  # Количество воркеров


def calculate_sum_sync(chunk_info: tuple[int, int]) -> int:
    """
    Синхронная функция вычисления суммы арифметической прогрессии.
    Будет запускаться в отдельных процессах через run_in_executor.
    """
    start, end = chunk_info
    count = end - start + 1
    return (start + end) * count // 2


async def calculate_sum_async(start: int, end: int) -> int:
    """
    Асинхронная корутина для демонстрации.
    Для CPU-bound задач await не даёт преимуществ,
    так как нет операций ввода-вывода.
    """
    # Имитация асинхронной работы (на практике здесь было бы await I/O)
    await asyncio.sleep(0)
    count = end - start + 1
    return (start + end) * count // 2


async def run_pure_async() -> tuple[int, float]:
    """
    Вариант с чистым asyncio — все корутины в одном потоке.
    Демонстрирует, что для CPU-bound задач asyncio не даёт ускорения.
    """
    chunk_size = N // NUM_WORKERS
    tasks = []

    start_time = time.perf_counter()

    for i in range(NUM_WORKERS):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else N
        tasks.append(calculate_sum_async(start, end))

    partial_sums = await asyncio.gather(*tasks)
    total = sum(partial_sums)
    elapsed = time.perf_counter() - start_time

    return total, elapsed


async def run_with_executor() -> tuple[int, float]:
    """
    Вариант с ProcessPoolExecutor — истинный параллелизм.
    Рекомендованный подход для CPU-bound задач в asyncio.
    """
    chunk_size = N // NUM_WORKERS
    chunks = []

    for i in range(NUM_WORKERS):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else N
        chunks.append((start, end))
        print(f"[Chunk {i+1}]: range [{start:_}, {end:_}]")

    loop = asyncio.get_running_loop()
    start_time = time.perf_counter()

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        tasks = [
            loop.run_in_executor(executor, calculate_sum_sync, chunk)
            for chunk in chunks
        ]
        partial_sums = await asyncio.gather(*tasks)

    total = sum(partial_sums)
    elapsed = time.perf_counter() - start_time

    return total, elapsed


async def main() -> None:
    print("=" * 55)
    print("ASYNC SUM — Лабораторная работа 2, Задача 1")
    print("=" * 55)

    expected = N * (N + 1) // 2

    # Вариант 1: Pure asyncio (демонстрационный)
    print("\n[1/2] Pure asyncio (один поток, кооперативная многозадачность)...")
    total_async, elapsed_async = await run_pure_async()
    print(f"  Total: {total_async:_}")
    print(f"  Time:  {elapsed_async:.6f} sec")
    print(f"  Match: {total_async == expected}")

    # Вариант 2: asyncio + ProcessPoolExecutor
    print(
        f"\n[2/2] asyncio + ProcessPoolExecutor "
        f"({NUM_WORKERS} процессов — истинный параллелизм)..."
    )
    total_exec, elapsed_exec = await run_with_executor()
    print(f"  Total: {total_exec:_}")
    print(f"  Time:  {elapsed_exec:.6f} sec")
    print(f"  Match: {total_exec == expected}")

    print(f"\n{'='*55}")
    print(f"Workers:        {NUM_WORKERS}")
    print(f"Expected sum:   {expected:_}")
    print(f"CPU cores:      {os.cpu_count()}")
    print(f"Timestamps:     {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pure async:     {elapsed_async:.6f} sec (последовательно)")
    print(f"+ Executor:     {elapsed_exec:.6f} sec (параллельно)")
    print(f"{'='*55}")


if __name__ == "__main__":
    asyncio.run(main())

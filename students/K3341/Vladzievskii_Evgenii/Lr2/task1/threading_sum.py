"""
Лабораторная работа №2, Задача 1 — threading (потоки)
Сумма чисел от 1 до 1 000 000 000 000 с использованием модуля threading.

Особенности:
- Каждый поток вычисляет сумму в своём диапазоне
- Результаты собираются через список + join()
- Из-за GIL потоки не дают реального параллелизма для CPU-bound задач,
  но позволяют распараллелить структуру вычислений
"""

import threading
import time
import os
from dataclasses import dataclass


N = 1_000_000_000_000  # Общее количество чисел
NUM_WORKERS = 8  # Количество потоков

results = [0] * NUM_WORKERS
lock = threading.Lock()


def calculate_sum(start: int, end: int, index: int) -> None:
    """
    Вычисляет сумму всех целых чисел в диапазоне [start, end]
    с использованием арифметической прогрессии.

    Используется формула Гаусса: (a1 + an) * n / 2,
    где n = end - start + 1.
    """
    count = end - start + 1
    total = (start + end) * count // 2
    results[index] = total


def main() -> None:
    threads = []
    chunk_size = N // NUM_WORKERS

    start_time = time.perf_counter()

    # Запуск потоков
    for i in range(NUM_WORKERS):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else N
        thread = threading.Thread(
            target=calculate_sum, args=(start, end, i), name=f"Worker-{i+1}"
        )
        threads.append(thread)
        thread.start()
        print(f"[{thread.name}] Started: range [{start:_}, {end:_}]")

    # Ожидание завершения всех потоков
    for thread in threads:
        thread.join()
        print(f"[{thread.name}] Finished")

    total = sum(results)
    elapsed = time.perf_counter() - start_time

    # Проверка через формулу Гаусса
    expected = N * (N + 1) // 2
    assert total == expected, f"Sum mismatch: {total} != {expected}"

    print(f"\n{'='*50}")
    print(f"Workers:        {NUM_WORKERS} (threading.Thread)")
    print(f"Total sum:      {total:_}")
    print(f"Expected:       {expected:_}")
    print(f"Match:          {total == expected}")
    print(f"Time elapsed:   {elapsed:.6f} sec")
    print(f"CPU cores:      {os.cpu_count()}")
    print(f"Timestamps:     {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

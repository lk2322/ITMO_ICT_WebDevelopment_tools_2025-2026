"""
Лабораторная работа №2, Задача 1 — multiprocessing (процессы)
Сумма чисел от 1 до 1 000 000 000 000 с использованием модуля multiprocessing.

Особенности:
- Каждый процесс работает в отдельном адресном пространстве
- Истинный параллелизм на многоядерных CPU (обход GIL)
- Данные передаются через multiprocessing.Pool и map()
- Накладные расходы на создание процессов и передачу данных выше,
  чем у потоков, но это окупается на CPU-bound задачах
"""

import multiprocessing
import time
import os
from functools import partial


N = 1_000_000_000_000  # Общее количество чисел
NUM_WORKERS = min(8, os.cpu_count() or 4)  # Количество процессов


def calculate_sum(chunk_info: tuple[int, int]) -> int:
    """
    Вычисляет сумму арифметической прогрессии в диапазоне [start, end].

    Используется формула Гаусса: (a1 + an) * n / 2.
    Возвращает частичную сумму.
    """
    start, end = chunk_info
    count = end - start + 1
    return (start + end) * count // 2


def main() -> None:
    chunk_size = N // NUM_WORKERS

    # Формируем диапазоны для каждого процесса
    chunks = []
    for i in range(NUM_WORKERS):
        start = i * chunk_size + 1
        end = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else N
        chunks.append((start, end))
        print(f"[Chunk {i+1}]: range [{start:_}, {end:_}]")

    print(f"\nStarting {NUM_WORKERS} processes...")

    start_time = time.perf_counter()

    # Запуск процессов через Pool
    with multiprocessing.Pool(processes=NUM_WORKERS) as pool:
        partial_sums = pool.map(calculate_sum, chunks)

    total = sum(partial_sums)
    elapsed = time.perf_counter() - start_time

    # Проверка через формулу Гаусса
    expected = N * (N + 1) // 2
    assert total == expected, f"Sum mismatch: {total} != {expected}"

    print(f"\n{'='*50}")
    print(f"Workers:        {NUM_WORKERS} (multiprocessing.Pool)")
    print(f"Total sum:      {total:_}")
    print(f"Expected:       {expected:_}")
    print(f"Match:          {total == expected}")
    print(f"Time elapsed:   {elapsed:.6f} sec")
    print(f"CPU cores:      {os.cpu_count()}")
    print(f"Timestamps:     {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

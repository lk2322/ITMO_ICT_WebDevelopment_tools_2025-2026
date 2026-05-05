"""
Benchmark: сравнение threading, multiprocessing и async на CPU-bound задаче.

В отличие от основных программ (которые используют формулу Гаусса O(1)),
здесь используется sum(range(...)) — реальная итерация в C.
N=10^8 (100 миллионов), 8 воркеров, каждый суммирует ~12.5M чисел.
"""

import threading
import multiprocessing
import asyncio
import time
import os
from concurrent.futures import ProcessPoolExecutor


N = 100_000_000  # 100 миллионов
NUM_WORKERS = 8


# ---- Sequential baseline ----
def sequential() -> float:
    start = time.perf_counter()
    total = sum(range(1, N + 1))
    elapsed = time.perf_counter() - start
    expected = N * (N + 1) // 2
    assert total == expected
    return elapsed


# ---- Threading ----
def _thread_worker(start: int, end: int, results: list, idx: int):
    results[idx] = sum(range(start, end + 1))


def bench_threading() -> float:
    results = [0] * NUM_WORKERS
    threads = []
    chunk_size = N // NUM_WORKERS

    start = time.perf_counter()
    for i in range(NUM_WORKERS):
        s = i * chunk_size + 1
        e = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else N
        t = threading.Thread(target=_thread_worker, args=(s, e, results, i))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    elapsed = time.perf_counter() - start
    total = sum(results)
    expected = N * (N + 1) // 2
    assert total == expected
    return elapsed


# ---- Multiprocessing ----
def _mp_worker(chunk: tuple[int, int]) -> int:
    s, e = chunk
    return sum(range(s, e + 1))


def bench_multiprocessing() -> float:
    chunk_size = N // NUM_WORKERS
    chunks = []
    for i in range(NUM_WORKERS):
        s = i * chunk_size + 1
        e = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else N
        chunks.append((s, e))

    start = time.perf_counter()
    with multiprocessing.Pool(NUM_WORKERS) as pool:
        results = pool.map(_mp_worker, chunks)

    elapsed = time.perf_counter() - start
    total = sum(results)
    expected = N * (N + 1) // 2
    assert total == expected
    return elapsed


# ---- Async + ProcessPoolExecutor ----
async def _async_executor_bench() -> float:
    chunk_size = N // NUM_WORKERS
    chunks = []
    for i in range(NUM_WORKERS):
        s = i * chunk_size + 1
        e = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else N
        chunks.append((s, e))

    loop = asyncio.get_running_loop()
    start = time.perf_counter()
    with ProcessPoolExecutor(NUM_WORKERS) as executor:
        tasks = [loop.run_in_executor(executor, _mp_worker, c) for c in chunks]
        results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start
    total = sum(results)
    expected = N * (N + 1) // 2
    assert total == expected
    return elapsed


def main():
    print("=" * 60)
    print("BENCHMARK: sum(1..100_000_000) через sum(range(...))")
    print(f"CPU cores: {os.cpu_count()} | Workers: {NUM_WORKERS}")
    print("=" * 60)

    # Sequential
    t_seq = sequential()
    print(f"\n{'Sequential':>25}: {t_seq:.4f} sec  (baseline)")

    # Threading
    t_thr = bench_threading()
    speedup = t_seq / t_thr
    print(f"{'Threading':>25}: {t_thr:.4f} sec  (x{speedup:.2f})")

    # Multiprocessing
    t_mp = bench_multiprocessing()
    speedup = t_seq / t_mp
    print(f"{'Multiprocessing':>25}: {t_mp:.4f} sec  (x{speedup:.2f})")

    # Async + Executor
    t_async = asyncio.run(_async_executor_bench())
    speedup = t_seq / t_async
    print(f"{'Async+Executor':>25}: {t_async:.4f} sec  (x{speedup:.2f})")

    print(f"\n{'='*60}")
    print(f"Timestamps: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

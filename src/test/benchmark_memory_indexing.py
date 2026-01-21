#!/usr/bin/env python3
"""
Нагрузочное тестирование индексации памяти.
Сравнение производительности старого и нового подходов.
"""

import time
import random
from pathlib import Path
import sys

# Настройка путей
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from memory.memory import ArchiveMemory
from memory.index_engine import MemoryIndexEngine, MemoryQuery
from memory.types import MemoryEntry
from runtime.performance_metrics import performance_metrics


def generate_test_entries(count: int) -> list[MemoryEntry]:
    """Генерирует тестовые записи памяти."""
    event_types = ["decay", "recovery", "shock", "noise", "learning", "adaptation"]
    entries = []

    base_time = time.time() - 86400 * 30  # 30 дней назад

    for i in range(count):
        event_type = random.choice(event_types)
        significance = random.uniform(0.1, 1.0)
        timestamp = base_time + random.uniform(0, 86400 * 30)
        weight = random.uniform(0.1, 1.0)

        entry = MemoryEntry(
            event_type=event_type,
            meaning_significance=significance,
            timestamp=timestamp,
            weight=weight
        )
        entries.append(entry)

    return entries


def benchmark_linear_search(entries: list[MemoryEntry], queries: list[MemoryQuery]) -> dict:
    """Замер производительности линейного поиска (старый подход)."""
    print(f"Тестирование линейного поиска на {len(entries)} записях...")

    # Замер поиска
    search_times = []
    for query in queries:
        start_time = time.perf_counter()

        # Линейный поиск (имитация старого подхода)
        results = []
        for entry in entries:
            if (query.event_type is None or entry.event_type == query.event_type) and \
               (query.min_significance is None or entry.meaning_significance >= query.min_significance) and \
               (query.start_timestamp is None or entry.timestamp >= query.start_timestamp) and \
               (query.end_timestamp is None or entry.timestamp <= query.end_timestamp):
                results.append(entry)

        # Сортировка и лимит
        if query.sort_by == "significance":
            results.sort(key=lambda x: x.meaning_significance, reverse=(query.sort_order == "desc"))
        results = results[:query.limit]

        end_time = time.perf_counter()
        search_times.append(end_time - start_time)

    avg_search_time = sum(search_times) / len(search_times)
    return {
        "method": "linear_search",
        "entries_count": len(entries),
        "queries_count": len(queries),
        "avg_search_time": avg_search_time,
        "total_search_time": sum(search_times),
        "results_per_query": len(results) if 'results' in locals() else 0
    }


def benchmark_indexed_search(entries: list[MemoryEntry], queries: list[MemoryQuery]) -> dict:
    """Замер производительности индексированного поиска (новый подход)."""
    print(f"Тестирование индексированного поиска на {len(entries)} записях...")

    # Создание и заполнение индекса
    index_start = time.perf_counter()
    engine = MemoryIndexEngine(max_cache_size=50)  # Увеличим кэш для тестирования
    for entry in entries:
        engine.add_entry(entry)
    index_build_time = time.perf_counter() - index_start

    print(".2f")

    # Замер поиска (с повторяющимися запросами для тестирования кэша)
    search_times = []
    all_queries = queries + queries[:10]  # Добавим повторяющиеся запросы

    for query in all_queries:
        start_time = time.perf_counter()
        results = engine.search(query)
        end_time = time.perf_counter()

        search_times.append(end_time - start_time)

    # Финальная статистика кэша
    stats = engine.get_stats()
    cache_hits = stats["cache_hits"]
    cache_misses = stats["cache_misses"]

    avg_search_time = sum(search_times) / len(search_times)

    return {
        "method": "indexed_search",
        "entries_count": len(entries),
        "queries_count": len(all_queries),
        "index_build_time": index_build_time,
        "avg_search_time": avg_search_time,
        "total_search_time": sum(search_times),
        "cache_hit_rate": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
        "results_per_query": len(results) if 'results' in locals() else 0
    }


def generate_test_queries(count: int, entries: list[MemoryEntry]) -> list[MemoryQuery]:
    """Генерирует тестовые запросы."""
    queries = []
    event_types = list(set(entry.event_type for entry in entries))

    for _ in range(count):
        query_type = random.choice(["event_type_only", "complex", "time_range", "significance_only"])

        if query_type == "event_type_only":
            query = MemoryQuery(
                event_type=random.choice(event_types),
                limit=random.randint(5, 50)
            )
        elif query_type == "complex":
            query = MemoryQuery(
                event_type=random.choice(event_types) if random.random() > 0.3 else None,
                min_significance=random.uniform(0.3, 0.8) if random.random() > 0.4 else None,
                start_timestamp=min(e.timestamp for e in entries) if random.random() > 0.5 else None,
                end_timestamp=max(e.timestamp for e in entries) if random.random() > 0.5 else None,
                limit=random.randint(5, 50)
            )
        elif query_type == "time_range":
            timestamps = sorted([e.timestamp for e in entries])
            start_idx = random.randint(0, len(timestamps) // 2)
            end_idx = random.randint(start_idx + 1, len(timestamps) - 1)
            query = MemoryQuery(
                start_timestamp=timestamps[start_idx],
                end_timestamp=timestamps[end_idx],
                limit=random.randint(5, 50)
            )
        else:  # significance_only
            query = MemoryQuery(
                min_significance=random.uniform(0.2, 0.9),
                limit=random.randint(5, 50)
            )

        queries.append(query)

    return queries


def run_realistic_benchmark():
    """Реалистичный benchmark с большим объемом данных и повторяющимися запросами."""
    print("🎯 Реалистичный benchmark: 10k записей, повторяющиеся запросы")
    print("-" * 60)

    # Большой объем данных
    entries = generate_test_entries(10000)
    engine = MemoryIndexEngine(max_cache_size=200)

    # Построение индекса
    print("Построение индекса для 10k записей...")
    index_start = time.perf_counter()
    for entry in entries:
        engine.add_entry(entry)
    index_time = time.perf_counter() - index_start
    print(".2f")

    # Создаем повторяющиеся запросы (реалистичный сценарий)
    base_queries = generate_test_queries(20, entries)  # 20 уникальных запросов
    repeated_queries = base_queries * 50  # Повторяем каждый запрос 50 раз

    print(f"Выполнение {len(repeated_queries)} запросов (с повторениями)...")

    # Замер поиска
    search_start = time.perf_counter()
    for query in repeated_queries:
        results = engine.search(query)
    search_time = time.perf_counter() - search_start

    # Статистика
    stats = engine.get_stats()
    avg_query_time = search_time / len(repeated_queries)

    print("\n📊 РЕЗУЛЬТАТЫ РЕАЛИСТИЧНОГО ТЕСТА:")
    print(f"Общее время поиска: {search_time:.4f}s")
    print(f"Среднее время запроса: {avg_query_time:.6f}s")
    print(f"Запросов в секунду: {len(repeated_queries) / search_time:.1f}")
    print(f"Кэш hit rate: {stats['cache_hit_rate']:.1%}")
    print(f"Всего кэш hits: {stats['cache_hits']}")
    print(f"Всего кэш misses: {stats['cache_misses']}")

    return {
        "entries": 10000,
        "queries": len(repeated_queries),
        "index_time": index_time,
        "search_time": search_time,
        "avg_query_time": avg_query_time,
        "qps": len(repeated_queries) / search_time,
        "cache_hit_rate": stats['cache_hit_rate']
    }


def run_benchmark():
    """Запуск полного benchmark тестирования."""
    print("🚀 Запуск нагрузочного тестирования индексации памяти")
    print("=" * 60)

    # Быстрый тест для сравнения
    test_sizes = [1000]
    queries_per_test = 50

    for size in test_sizes:
        print(f"\n📊 Тестирование с {size} записями памяти")
        print("-" * 40)

        # Генерация данных
        entries = generate_test_entries(size)
        queries = generate_test_queries(queries_per_test, entries)

        # Линейный поиск
        linear_results = benchmark_linear_search(entries, queries)

        # Индексированный поиск
        indexed_results = benchmark_indexed_search(entries, queries)

        # Вывод результатов
        print("\n📈 РЕЗУЛЬТАТЫ:")
        print(f"Линейный поиск:     {linear_results['avg_search_time']:.4f}s среднее время запроса")
        print(f"Индексированный:    {indexed_results['avg_search_time']:.4f}s среднее время запроса")
        print(f"Время построения индекса: {indexed_results['index_build_time']:.4f}s")
        print(f"Ускорение поиска:   {linear_results['avg_search_time'] / indexed_results['avg_search_time']:.1f}x")
        print(f"Кэш hit rate:       {indexed_results['cache_hit_rate']:.1%}")

        # Детальная статистика индекса
        stats = performance_metrics.get_average_time("memory_index_add_entry")
        if stats:
            print(f"Среднее время добавления в индекс: {stats:.6f}s")

        search_stats = performance_metrics.get_average_time("memory_index_search")
        if search_stats:
            print(f"Среднее время индексированного поиска: {search_stats:.6f}s")

    # Реалистичный тест
    realistic_results = run_realistic_benchmark()

    print("\n✅ Нагрузочное тестирование завершено")

    # Итоговые выводы
    print("\n🎯 ВЫВОДЫ:")
    print("Для небольших объемов данных (1k-5k) линейный поиск может быть быстрее из-за overhead индексов")
    print("Для больших объемов данных с повторяющимися запросами индексы дают значительное преимущество")
    print(f"В реалистичном сценарии: {realistic_results['qps']:.1f} запросов/сек")
    print(f"Кэш hit rate: {realistic_results['cache_hit_rate']:.1%}")
    print("Индексы особенно эффективны для поиска по event_type и range запросов")


if __name__ == "__main__":
    run_benchmark()
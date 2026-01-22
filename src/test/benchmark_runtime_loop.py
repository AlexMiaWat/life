#!/usr/bin/env python3
"""
Нагрузочное тестирование runtime loop.
Измерение производительности различных операций в runtime loop.
"""

import time
import threading
import statistics
from pathlib import Path
import sys
from typing import Dict, List, Any

# Настройка путей
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.state.self_state import create_initial_state
from src.runtime.loop import run_loop
from src.monitor.console import console_monitor
from src.runtime.performance_metrics import performance_metrics


def benchmark_runtime_loop_ticks(
    tick_count: int = 1000,
    tick_interval: float = 0.01,
    enable_memory_hierarchy: bool = False
) -> Dict[str, Any]:
    """
    Бенчмарк производительности runtime loop по количеству тиков в секунду.

    Args:
        tick_count: Количество тиков для тестирования
        tick_interval: Интервал между тиками
        enable_memory_hierarchy: Включить экспериментальную иерархию памяти

    Returns:
        Dict с метриками производительности
    """
    print(f"🚀 Запуск бенчмарка runtime loop: {tick_count} тиков с интервалом {tick_interval}s")

    # Создание состояния
    state = create_initial_state()

    # Событие для остановки
    stop_event = threading.Event()

    # Запуск runtime loop в отдельном потоке
    def run_loop_thread():
        try:
            run_loop(
                self_state=state,
                monitor=console_monitor,
                tick_interval=tick_interval,
                max_ticks=tick_count,
                stop_event=stop_event,
                enable_memory_hierarchy=enable_memory_hierarchy,
                enable_profiling=False  # Отключаем профилирование для чистого замера
            )
        except Exception as e:
            print(f"Ошибка в runtime loop: {e}")

    # Замер времени выполнения
    start_time = time.perf_counter()

    loop_thread = threading.Thread(target=run_loop_thread, daemon=True)
    loop_thread.start()

    # Ожидание завершения
    loop_thread.join(timeout=tick_count * tick_interval + 10)

    # Остановка принудительно если не завершилась
    stop_event.set()

    end_time = time.perf_counter()
    total_time = end_time - start_time

    # Расчет метрик
    actual_ticks = state.ticks
    ticks_per_second = actual_ticks / total_time if total_time > 0 else 0

    print(".2f")
    print(".2f")
    # Сбор метрик производительности
    metrics = {
        "total_time": total_time,
        "actual_ticks": actual_ticks,
        "expected_ticks": tick_count,
        "ticks_per_second": ticks_per_second,
        "average_tick_time": total_time / actual_ticks if actual_ticks > 0 else 0,
        "tick_interval": tick_interval,
        "efficiency_ratio": ticks_per_second * tick_interval,
        "memory_entries": len(state.memory),
        "archive_entries": len(state.archive_memory.get_all_entries()) if hasattr(state, 'archive_memory') else 0,
    }

    # Добавление метрик из PerformanceMetrics
    performance_summary = {}
    for operation in performance_metrics.metrics.keys():
        avg_time = performance_metrics.get_average_time(operation)
        if avg_time is not None:
            performance_summary[f"{operation}_avg_time"] = avg_time
            performance_summary[f"{operation}_count"] = len(performance_metrics.metrics[operation])

    metrics["performance_metrics"] = performance_summary

    return metrics


def benchmark_memory_operations(
    memory_sizes: List[int] = [100, 500, 1000, 5000],
    operations_per_size: int = 100
) -> Dict[str, Any]:
    """
    Бенчмарк операций с памятью при разных размерах.

    Args:
        memory_sizes: Размеры памяти для тестирования
        operations_per_size: Количество операций на размер

    Returns:
        Dict с метриками по операциям памяти
    """
    print("🧠 Запуск бенчмарка операций памяти...")

    from src.memory.memory import Memory, ArchiveMemory
    from src.memory.memory_types import MemoryEntry
    import random

    results = {}

    for size in memory_sizes:
        print(f"  Тестирование размера памяти: {size} записей")

        # Создание памяти с архивом
        archive = ArchiveMemory()
        memory = Memory(archive=archive)

        # Заполнение памяти
        event_types = ["decay", "recovery", "shock", "noise", "learning"]
        base_time = time.time() - 86400 * 30  # 30 дней назад

        for i in range(size):
            entry = MemoryEntry(
                event_type=random.choice(event_types),
                meaning_significance=random.uniform(0.1, 1.0),
                timestamp=base_time + random.uniform(0, 86400 * 30),
                weight=random.uniform(0.1, 1.0),
            )
            memory.append(entry)

        # Замер операций
        append_times = []
        search_times = []
        decay_times = []
        archive_times = []

        for _ in range(operations_per_size):
            # Append operation
            start = time.perf_counter()
            entry = MemoryEntry(
                event_type=random.choice(event_types),
                meaning_significance=random.uniform(0.1, 1.0),
                timestamp=time.time(),
                weight=random.uniform(0.1, 1.0),
            )
            memory.append(entry)
            append_times.append(time.perf_counter() - start)

            # Search operation
            start = time.perf_counter()
            query_event_type = random.choice(event_types)
            found = [e for e in memory if e.event_type == query_event_type]
            search_times.append(time.perf_counter() - start)

            # Decay operation (раз в 10 операций)
            if _ % 10 == 0:
                start = time.perf_counter()
                memory.decay_weights(decay_factor=0.99, min_weight=0.0)
                decay_times.append(time.perf_counter() - start)

                # Archive operation (раз в 50 операций)
                if _ % 5 == 0:  # Каждые 50 операций
                    start = time.perf_counter()
                    archived = memory.archive_old_entries(
                        max_age=86400 * 7,  # 7 дней
                        min_weight=0.1
                    )
                    archive_times.append(time.perf_counter() - start)

        results[size] = {
            "append_avg_time": statistics.mean(append_times),
            "append_p95_time": sorted(append_times)[int(len(append_times) * 0.95)],
            "search_avg_time": statistics.mean(search_times),
            "search_p95_time": sorted(search_times)[int(len(search_times) * 0.95)],
            "decay_avg_time": statistics.mean(decay_times) if decay_times else 0,
            "archive_avg_time": statistics.mean(archive_times) if archive_times else 0,
            "final_memory_size": len(memory),
            "final_archive_size": len(archive.get_all_entries()),
        }

        print(f"    Размер {size}: append={results[size]['append_avg_time']:.6f}s, search={results[size]['search_avg_time']:.6f}s")

    return results


def run_comprehensive_benchmark() -> Dict[str, Any]:
    """
    Запуск комплексного бенчмарка производительности runtime loop и памяти.

    Returns:
        Dict с полными результатами бенчмарка
    """
    print("🎯 Запуск комплексного бенчмарка производительности Life\n")

    results = {
        "timestamp": time.time(),
        "runtime_loop_benchmarks": {},
        "memory_benchmarks": {},
        "recommendations": []
    }

    # Бенчмарк runtime loop с разными конфигурациями
    configs = [
        {"name": "baseline", "tick_count": 500, "tick_interval": 0.1, "memory_hierarchy": False},
        {"name": "fast_ticks", "tick_count": 1000, "tick_interval": 0.01, "memory_hierarchy": False},
        {"name": "with_memory_hierarchy", "tick_count": 500, "tick_interval": 0.1, "memory_hierarchy": True},
    ]

    for config in configs:
        print(f"\n--- Конфигурация: {config['name']} ---")
        metrics = benchmark_runtime_loop_ticks(
            tick_count=config["tick_count"],
            tick_interval=config["tick_interval"],
            enable_memory_hierarchy=config["memory_hierarchy"]
        )
        results["runtime_loop_benchmarks"][config["name"]] = metrics

        # Анализ результатов
        ticks_per_sec = metrics["ticks_per_second"]
        if ticks_per_sec < 50:
            results["recommendations"].append(f"Низкая производительность в {config['name']}: {ticks_per_sec:.1f} ticks/sec")
        elif ticks_per_sec > 100:
            results["recommendations"].append(f"Хорошая производительность в {config['name']}: {ticks_per_sec:.1f} ticks/sec")

    # Бенчмарк операций памяти
        print("\n--- Операции памяти ---")
    memory_results = benchmark_memory_operations()
    results["memory_benchmarks"] = memory_results

    # Анализ операций памяти
    for size, metrics in memory_results.items():
        if metrics["append_avg_time"] > 0.001:  # > 1ms
            results["recommendations"].append(f"Медленная операция append для размера {size}: {metrics['append_avg_time']:.6f}s")
        if metrics["search_avg_time"] > 0.01:  # > 10ms
            results["recommendations"].append(f"Медленный поиск для размера {size}: {metrics['search_avg_time']:.6f}s")

    print("\n📊 Результаты комплексного бенчмарка:")
    print(f"  Runtime loop конфигураций: {len(results['runtime_loop_benchmarks'])}")
    print(f"  Память размеров: {len(results['memory_benchmarks'])}")
    print(f"  Рекомендаций: {len(results['recommendations'])}")

    return results


if __name__ == "__main__":
    # Запуск бенчмарка
    results = run_comprehensive_benchmark()

    # Сохранение результатов в JSON
    import json
    from pathlib import Path

    # Создаем каталог artifacts если не существует
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    output_file = artifacts_dir / f"benchmark_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Результаты сохранены в: {output_file}")

    # Вывод рекомендаций
    if results["recommendations"]:
        print("\n🎯 Рекомендации по оптимизации:")
        for rec in results["recommendations"]:
            print(f"  • {rec}")
    else:
        print("\n✅ Все метрики в допустимых пределах!")
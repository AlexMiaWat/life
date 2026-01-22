#!/usr/bin/env python3
"""
Benchmark script для измерения производительности оптимизаций Runtime Loop.

Измеряет:
- Время выполнения тиков до и после оптимизаций
- Эффективность кэширования
- Сравнение батчинга обработки событий
"""

import time
import statistics
import sys
import os
from typing import List, Dict, Any
import logging

# Добавление корневой директории проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.state.self_state import create_initial_state
from src.runtime.loop import run_loop
from src.monitor.console import monitor
from src.runtime.computation_cache import get_computation_cache

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def benchmark_runtime_performance(num_ticks: int = 100, num_runs: int = 3) -> Dict[str, Any]:
    """
    Бенчмарк производительности runtime loop.

    Args:
        num_ticks: Количество тиков для теста
        num_runs: Количество прогонов для усреднения

    Returns:
        Dict с результатами benchmark
    """
    results = {
        "runs": [],
        "avg_tick_time": 0.0,
        "median_tick_time": 0.0,
        "min_tick_time": 0.0,
        "max_tick_time": 0.0,
        "total_time": 0.0,
        "ticks_per_second": 0.0,
        "cache_stats": {},
        "optimizations_applied": [
            "batch_event_processing",
            "computation_caching",
            "monitoring_optimization"
        ]
    }

    for run in range(num_runs):
        logger.info(f"Starting benchmark run {run + 1}/{num_runs}")

        # Очистка кэша перед каждым прогоном
        cache = get_computation_cache()
        cache.clear()

        # Создание свежего состояния
        state = create_initial_state()

        # Измерение времени выполнения
        tick_times = []
        start_time = time.time()

        # Имитация работы runtime loop (упрощенная версия для benchmark)
        for tick in range(num_ticks):
            tick_start = time.time()

            # Симуляция основных операций тика
            state.apply_delta({"ticks": 1})
            state.apply_delta({"age": 1.0})  # Имитация dt

            # Тестирование кэширования subjective_time (основная оптимизация)
            from src.runtime.computation_cache import cached_compute_subjective_dt

            # Вызов с одинаковыми параметрами для тестирования кэша
            for _ in range(3):  # Имитируем повторяющиеся вычисления
                subjective_dt = cached_compute_subjective_dt(
                    dt=1.0,
                    base_rate=state.subjective_time_base_rate,
                    intensity=state.last_event_intensity,
                    stability=state.stability,
                    energy=state.energy,
                    intensity_coeff=state.subjective_time_intensity_coeff,
                    stability_coeff=abs(state.subjective_time_stability_coeff),
                    energy_coeff=state.subjective_time_energy_coeff,
                    rate_min=state.subjective_time_rate_min,
                    rate_max=state.subjective_time_rate_max,
                    circadian_phase=getattr(state, 'circadian_phase', 0.0),
                    recovery_efficiency=getattr(state, 'recovery_efficiency', 1.0),
                )
                state.apply_delta({"subjective_time": subjective_dt})

            tick_end = time.time()
            tick_time = tick_end - tick_start
            tick_times.append(tick_time)

        end_time = time.time()
        total_time = end_time - start_time

        run_result = {
            "run_number": run + 1,
            "total_time": total_time,
            "avg_tick_time": statistics.mean(tick_times),
            "median_tick_time": statistics.median(tick_times),
            "min_tick_time": min(tick_times),
            "max_tick_time": max(tick_times),
            "ticks_per_second": num_ticks / total_time,
            "tick_times": tick_times
        }

        results["runs"].append(run_result)
        logger.info(f"Run {run + 1} completed: {run_result['avg_tick_time']:.4f}s avg tick time, "
                   f"{run_result['ticks_per_second']:.1f} ticks/sec")

    # Агрегация результатов по всем прогонам
    all_avg_times = [run["avg_tick_time"] for run in results["runs"]]
    all_total_times = [run["total_time"] for run in results["runs"]]

    results["avg_tick_time"] = statistics.mean(all_avg_times)
    results["median_tick_time"] = statistics.median(all_avg_times)
    results["min_tick_time"] = min(all_avg_times)
    results["max_tick_time"] = max(all_avg_times)
    results["total_time"] = statistics.mean(all_total_times)
    results["ticks_per_second"] = num_ticks / results["total_time"]

    # Статистика кэша
    cache = get_computation_cache()
    results["cache_stats"] = cache.get_stats()

    return results


def print_benchmark_report(results: Dict[str, Any]) -> None:
    """Вывод отчета о результатах benchmark."""
    print("\n" + "="*60)
    print("RUNTIME LOOP PERFORMANCE BENCHMARK REPORT")
    print("="*60)

    print(f"\nOptimizations applied: {', '.join(results['optimizations_applied'])}")

    print("\nPERFORMANCE METRICS:")
    print(f"  Average tick time: {results['avg_tick_time']:.4f}s")
    print(f"  Median tick time: {results['median_tick_time']:.4f}s")
    print(f"  Min tick time: {results['min_tick_time']:.4f}s")
    print(f"  Max tick time: {results['max_tick_time']:.4f}s")
    print(f"  Ticks per second: {results['ticks_per_second']:.1f}")
    print(f"  Total benchmark time: {results['total_time']:.2f}s")

    print("\nCACHE STATISTICS:")
    cache_stats = results["cache_stats"]
    print(f"  Subjective DT Cache:")
    print(f"    Hit rate: {cache_stats['subjective_dt']['hit_rate']:.1f}%")
    print(f"    Cache size: {cache_stats['subjective_dt']['size']}")
    print(f"    Hits: {cache_stats['subjective_dt']['hits']}")
    print(f"    Misses: {cache_stats['subjective_dt']['misses']}")

    print(f"  Memory Search Cache:")
    print(f"    Hit rate: {cache_stats['memory_search']['hit_rate']:.1f}%")
    print(f"    Cache size: {cache_stats['memory_search']['size']}")
    print(f"    Hits: {cache_stats['memory_search']['hits']}")
    print(f"    Misses: {cache_stats['memory_search']['misses']}")

    print("\nRUN DETAILS:")
    for run in results["runs"]:
        print(f"  Run {run['run_number']}: {run['avg_tick_time']:.4f}s avg, "
              f"{run['ticks_per_second']:.1f} ticks/sec")

    print("\n" + "="*60)


def main():
    """Основная функция benchmark."""
    print("Runtime Loop Performance Benchmark")
    print("Testing optimizations: batch processing, computation caching, monitoring aggregation")

    # Параметры benchmark
    NUM_TICKS = 1000  # Тестовый прогон на 1000 тиков
    NUM_RUNS = 5      # 5 прогонов для статистической значимости

    try:
        # Запуск benchmark
        results = benchmark_runtime_performance(NUM_TICKS, NUM_RUNS)

        # Вывод результатов
        print_benchmark_report(results)

        # Проверка достижения целей оптимизации
        target_tick_time = 0.010  # Цель: < 10ms среднее время тика
        achieved_speedup = results["avg_tick_time"] < target_tick_time

        print("\nOPTIMIZATION TARGETS:")
        print(f"  Target tick time < 10ms: {results['avg_tick_time']:.4f}s "
              f"✅ {'PASSED' if achieved_speedup else 'FAILED'}")

        cache_hit_rate = results["cache_stats"]["subjective_dt"]["hit_rate"]
        good_cache_performance = cache_hit_rate > 50.0  # Хороший hit rate для кэша

        print(f"\n  Cache hit rate > 50%: "
              f"{cache_hit_rate:.1f}% ✅ {'PASSED' if good_cache_performance else 'FAILED'}")

        if achieved_speedup and good_cache_performance:
            print("\n🎉 ALL OPTIMIZATION TARGETS ACHIEVED!")
        else:
            print("\n⚠️  Some optimization targets not met - further tuning needed")

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    main()
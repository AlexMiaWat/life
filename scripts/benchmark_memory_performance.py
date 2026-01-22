#!/usr/bin/env python3
"""
Benchmark Memory Performance - измерения производительности операций с памятью.

Измеряет:
- batch_memory_maintenance производительность
- memory operations scalability
- cache hit rates
- memory usage patterns

Использование:
    python scripts/benchmark_memory_performance.py [--memory-sizes 1000 5000 10000] [--iterations 10]
"""

import argparse
import cProfile
import logging
import pstats
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.memory import Memory
from src.memory.memory_types import MemoryEntry
from src.runtime.computation_cache import get_computation_cache
from src.runtime.performance_metrics import measure_time

logger = logging.getLogger(__name__)


class MemoryPerformanceBenchmark:
    """
    Benchmark для измерения производительности операций с памятью.
    """

    def __init__(self, memory_sizes: List[int] = None, iterations: int = 10):
        """
        Инициализация benchmark'а.

        Args:
            memory_sizes: Размеры памяти для тестирования
            iterations: Количество итераций для каждого теста
        """
        self.memory_sizes = memory_sizes or [1000, 5000, 10000]
        self.iterations = iterations
        self.results = {}

        # Создаем директорию для результатов
        self.output_dir = Path("data/benchmarks/memory_performance")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Memory Performance Benchmark initialized with sizes: {self.memory_sizes}")

    def create_test_memory(self, size: int) -> Memory:
        """
        Создает тестовую память заданного размера.

        Args:
            size: Размер памяти

        Returns:
            Memory: Тестовая память
        """
        memory = Memory()
        current_time = time.time()

        for i in range(size):
            # Создаем записи с реалистичными характеристиками
            weight = 0.1 + (i / size) * 0.9  # От 0.1 до 1.0
            age_seconds = (i / size) * 30 * 24 * 3600  # От 0 до 30 дней
            timestamp = current_time - age_seconds

            entry = MemoryEntry(
                event_type=f"benchmark_event_{i % 20}",  # 20 типов событий
                meaning_significance=0.1 + (i % 10) * 0.09,  # От 0.1 до 1.0
                timestamp=timestamp,
                weight=weight,
                subjective_timestamp=timestamp - age_seconds * 0.1
            )

            memory.append(entry)

        logger.info(f"Created benchmark memory with {len(memory)} entries")
        return memory

    def benchmark_batch_memory_maintenance(self) -> Dict[str, Any]:
        """
        Benchmark для batch_memory_maintenance.

        Returns:
            Dict с результатами benchmark'а
        """
        logger.info("Benchmarking batch_memory_maintenance")

        results = {}

        for size in self.memory_sizes:
            logger.info(f"  Testing memory size: {size}")

            size_results = {
                "memory_size": size,
                "iterations": self.iterations,
                "times": [],
                "decayed_counts": [],
                "archived_counts": [],
                "total_processed": []
            }

            for i in range(self.iterations):
                # Создаем свежую память для каждого теста
                memory = self.create_test_memory(size)

                # Запускаем профилирование
                profiler = cProfile.Profile()
                profiler.enable()

                start_time = time.perf_counter()
                maintenance_result = memory.batch_memory_maintenance(
                    decay_factor=0.99,
                    min_weight=0.1,
                    max_age_seconds=7*24*3600,  # 7 дней
                    archive_min_weight=0.05,
                    archive_min_significance=0.0
                )
                end_time = time.perf_counter()

                profiler.disable()

                elapsed = end_time - start_time
                size_results["times"].append(elapsed)
                size_results["decayed_counts"].append(maintenance_result["decayed_count"])
                size_results["archived_counts"].append(maintenance_result["archived_count"])
                size_results["total_processed"].append(maintenance_result["total_processed"])

                logger.debug(f"    Iteration {i+1}: {elapsed:.6f}s, decayed: {maintenance_result['decayed_count']}, archived: {maintenance_result['archived_count']}")

                # Сохраняем profile для самого большого размера
                if size == max(self.memory_sizes) and i == 0:
                    stats = pstats.Stats(profiler)
                    profile_path = self.output_dir / f"batch_memory_maintenance_{size}_profile.prof"
                    stats.dump_stats(str(profile_path))

            # Вычисляем статистики
            size_results["avg_time"] = sum(size_results["times"]) / len(size_results["times"])
            size_results["min_time"] = min(size_results["times"])
            size_results["max_time"] = max(size_results["times"])
            size_results["throughput"] = size / size_results["avg_time"] if size_results["avg_time"] > 0 else 0
            size_results["complexity_per_entry"] = size_results["avg_time"] / size if size > 0 else 0

            results[size] = size_results

            logger.info(f"  Size {size}: avg {size_results['avg_time']:.6f}s, "
                       f"throughput: {size_results['throughput']:.0f} entries/s")

        return results

    def benchmark_individual_operations(self) -> Dict[str, Any]:
        """
        Benchmark для индивидуальных операций памяти.

        Returns:
            Dict с результатами benchmark'а
        """
        logger.info("Benchmarking individual memory operations")

        results = {}

        for size in self.memory_sizes:
            logger.info(f"  Testing individual operations on size: {size}")

            memory = self.create_test_memory(size)

            # Тестируем decay_weights
            decay_times = []
            for i in range(self.iterations):
                test_memory = Memory()
                test_memory.extend(memory)

                start_time = time.perf_counter()
                decayed = test_memory.apply_decay_weights()
                end_time = time.perf_counter()

                decay_times.append(end_time - start_time)

            # Тестируем apply_age_factors
            age_times = []
            for i in range(self.iterations):
                test_memory = Memory()
                test_memory.extend(memory)

                start_time = time.perf_counter()
                processed = test_memory.apply_age_factors()
                end_time = time.perf_counter()

                age_times.append(end_time - start_time)

            # Тестируем archive_old_entries
            archive_times = []
            for i in range(self.iterations):
                test_memory = Memory()
                test_memory.extend(memory)

                start_time = time.perf_counter()
                archived = test_memory.archive_old_entries()
                end_time = time.perf_counter()

                archive_times.append(end_time - start_time)

            results[size] = {
                "memory_size": size,
                "decay_weights": {
                    "avg_time": sum(decay_times) / len(decay_times),
                    "throughput": size / (sum(decay_times) / len(decay_times)) if decay_times else 0
                },
                "apply_age_factors": {
                    "avg_time": sum(age_times) / len(age_times),
                    "throughput": size / (sum(age_times) / len(age_times)) if age_times else 0
                },
                "archive_old_entries": {
                    "avg_time": sum(archive_times) / len(archive_times),
                    "throughput": size / (sum(archive_times) / len(archive_times)) if archive_times else 0
                }
            }

        return results

    def benchmark_cache_performance(self) -> Dict[str, Any]:
        """
        Benchmark для производительности кэширования.

        Returns:
            Dict с результатами benchmark'а
        """
        logger.info("Benchmarking computation cache performance")

        cache = get_computation_cache()
        cache.clear()  # Очищаем кэш перед тестированием

        results = {
            "cache_operations": [],
            "hit_rates": [],
            "memory_usage": []
        }

        # Тестируем activate_memory кэширование
        memory = self.create_test_memory(1000)

        for i in range(200):  # 200 операций кэширования
            # Варьируем параметры для реалистичного тестирования
            memory_size = len(memory) + (i % 20 - 10)
            subjective_time = time.time() + (i % 50 - 25)
            age = (i % 30) * 86400  # Возраст в днях

            start_time = time.perf_counter()

            # Проверяем кэш
            cached_result = cache.get_cached_activate_memory(
                "benchmark_event", memory_size, subjective_time, age, limit=50
            )

            if cached_result is None:
                # Cache miss - активируем память
                result = [entry for entry in memory[:50]]
                cache.cache_activate_memory(
                    "benchmark_event", memory_size, subjective_time, age, limit=50, result=result
                )
            else:
                # Cache hit
                result = cached_result

            end_time = time.perf_counter()

            operation_time = end_time - start_time
            results["cache_operations"].append({
                "iteration": i,
                "time": operation_time,
                "cache_hit": cached_result is not None,
                "memory_size": memory_size,
                "subjective_time": subjective_time,
                "age": age
            })

        # Получаем финальную статистику кэша
        cache_stats = cache.get_stats()
        results["final_cache_stats"] = cache_stats

        # Вычисляем hit rate
        total_ops = len(results["cache_operations"])
        hits = sum(1 for op in results["cache_operations"] if op["cache_hit"])
        results["overall_hit_rate"] = hits / total_ops * 100 if total_ops > 0 else 0

        logger.info(f"Cache benchmark complete: {hits}/{total_ops} hits ({results['overall_hit_rate']:.1f}%)")

        return results

    def run_full_benchmark(self) -> Dict[str, Any]:
        """
        Запускает полный benchmark производительности памяти.

        Returns:
            Dict с полными результатами benchmark'а
        """
        logger.info("Starting full memory performance benchmark")

        all_results = {
            "timestamp": time.time(),
            "benchmark": "MemoryPerformanceBenchmark",
            "memory_sizes": self.memory_sizes,
            "iterations": self.iterations,
            "results": {}
        }

        # Запускаем все benchmark'и
        all_results["results"]["batch_memory_maintenance"] = self.benchmark_batch_memory_maintenance()
        all_results["results"]["individual_operations"] = self.benchmark_individual_operations()
        all_results["results"]["cache_performance"] = self.benchmark_cache_performance()

        # Сохраняем результаты
        self.save_results(all_results)

        # Генерируем отчеты
        self.generate_performance_report(all_results)

        logger.info("Memory performance benchmark complete")
        return all_results

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        Сохраняет результаты benchmark'а.

        Args:
            results: Результаты для сохранения
        """
        import json

        timestamp = int(results["timestamp"])
        filename = f"memory_performance_benchmark_{timestamp}.json"

        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Results saved to {output_path}")

    def generate_performance_report(self, results: Dict[str, Any]) -> None:
        """
        Генерирует отчет о производительности.

        Args:
            results: Результаты benchmark'а
        """
        report_lines = [
            "# Memory Performance Benchmark Report",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            f"**Memory Sizes Tested:** {', '.join(map(str, results['memory_sizes']))}",
            f"**Iterations per Test:** {results['iterations']}",
            "",
            "## Batch Memory Maintenance Performance",
            ""
        ]

        # Отчет по batch_memory_maintenance
        batch_results = results["results"]["batch_memory_maintenance"]
        for size in sorted(batch_results.keys()):
            size_data = batch_results[size]
            report_lines.extend([
                f"### Memory Size: {size} entries",
                f"- **Average Time:** {size_data['avg_time']:.6f}s",
                f"- **Min/Max Time:** {size_data['min_time']:.6f}s / {size_data['max_time']:.6f}s",
                f"- **Throughput:** {size_data['throughput']:.0f} entries/s",
                f"- **Complexity:** {size_data['complexity_per_entry']:.2e}s per entry",
                f"- **Avg Decayed:** {sum(size_data['decayed_counts'])/len(size_data['decayed_counts']):.1f}",
                f"- **Avg Archived:** {sum(size_data['archived_counts'])/len(size_data['archived_counts']):.1f}",
                ""
            ])

        # Scalability analysis
        if len(results["memory_sizes"]) >= 2:
            sizes = sorted(results["memory_sizes"])
            base_size = sizes[0]
            max_size = sizes[-1]

            base_time = batch_results[base_size]["avg_time"]
            max_time = batch_results[max_size]["avg_time"]

            if base_time > 0:
                scalability = max_time / base_time
                size_ratio = max_size / base_size
                report_lines.extend([
                    "## Scalability Analysis",
                    f"- **Size Range:** {base_size} → {max_size} ({size_ratio:.1f}x)",
                    f"- **Time Scalability:** {scalability:.2f}x",
                    f"- **Complexity:** {'Linear' if abs(scalability - size_ratio) < 0.5 else 'Non-linear'}",
                    ""
                ])

        # Отчет по индивидуальным операциям
        report_lines.extend([
            "## Individual Operations Performance",
            ""
        ])

        individual_results = results["results"]["individual_operations"]
        for size in sorted(individual_results.keys()):
            size_data = individual_results[size]
            report_lines.extend([
                f"### Memory Size: {size} entries",
                f"- **decay_weights:** {size_data['decay_weights']['avg_time']:.6f}s ({size_data['decay_weights']['throughput']:.0f} entries/s)",
                f"- **apply_age_factors:** {size_data['apply_age_factors']['avg_time']:.6f}s ({size_data['apply_age_factors']['throughput']:.0f} entries/s)",
                f"- **archive_old_entries:** {size_data['archive_old_entries']['avg_time']:.6f}s ({size_data['archive_old_entries']['throughput']:.0f} entries/s)",
                ""
            ])

        # Отчет по кэшированию
        cache_results = results["results"]["cache_performance"]
        report_lines.extend([
            "## Cache Performance",
            f"- **Overall Hit Rate:** {cache_results['overall_hit_rate']:.1f}%",
            f"- **Total Operations:** {len(cache_results['cache_operations'])}",
            ""
        ])

        # Детальная статистика кэша
        if "final_cache_stats" in cache_results:
            stats = cache_results["final_cache_stats"]
            for cache_type, cache_data in stats.items():
                if cache_data["size"] > 0:
                    report_lines.extend([
                        f"### {cache_type.replace('_', ' ').title()} Cache",
                        f"- **Size:** {cache_data['size']}",
                        f"- **Hit Rate:** {cache_data['hit_rate']:.1f}%",
                        f"- **Efficiency:** {cache_data['efficiency']:.1f}%",
                        ""
                    ])

        # Сохраняем отчет
        timestamp = int(results["timestamp"])
        report_path = self.output_dir / f"memory_performance_report_{timestamp}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Performance report saved to {report_path}")


def main():
    """Основная функция для запуска benchmark'а."""
    parser = argparse.ArgumentParser(description="Memory Performance Benchmark")
    parser.add_argument("--memory-sizes", nargs="+", type=int, default=[1000, 5000, 10000],
                       help="Memory sizes to test (default: 1000 5000 10000)")
    parser.add_argument("--iterations", type=int, default=10,
                       help="Number of iterations per test (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Запуск benchmark'а
    benchmark = MemoryPerformanceBenchmark(
        memory_sizes=args.memory_sizes,
        iterations=args.iterations
    )

    try:
        results = benchmark.run_full_benchmark()
        logger.info("Memory performance benchmark completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
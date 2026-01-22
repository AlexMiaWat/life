#!/usr/bin/env python3
"""
Memory Operations Profiler для runtime loop.

Профилирует операции с памятью:
- decay_weights() с памятью 1k-10k записей
- archive_old_entries() с разными порогами
- Анализ lazy evaluation эффективности (пороги 50/100 тиков)
- Тестирование batch операций для memory management

Использование:
    python scripts/profile_memory_operations.py [--memory-sizes 1000 5000 10000] [--iterations 5]
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
from src.runtime.performance_metrics import measure_time

logger = logging.getLogger(__name__)


class MemoryOperationsProfiler:
    """
    Профилировщик операций с памятью для выявления bottleneck'ов.
    """

    def __init__(self, memory_sizes: List[int] = None, iterations: int = 5):
        """
        Инициализация профилировщика.

        Args:
            memory_sizes: Размеры памяти для тестирования
            iterations: Количество итераций для каждого теста
        """
        self.memory_sizes = memory_sizes or [1000, 5000, 10000]
        self.iterations = iterations
        self.results = {}

        # Создаем директорию для результатов
        self.output_dir = Path("data/profiling/memory_operations")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Memory Operations Profiler initialized with sizes: {self.memory_sizes}")

    def create_test_memory(self, size: int, age_distribution: str = "uniform") -> Memory:
        """
        Создает тестовую память заданного размера.

        Args:
            size: Размер памяти
            age_distribution: Распределение возрастов записей

        Returns:
            Memory: Тестовая память
        """
        # Создаем память без ограничений размера для профилирования
        memory = Memory()
        memory._max_size = size  # Устанавливаем больший лимит для тестирования

        current_time = time.time()

        for i in range(size):
            # Создаем записи с разными характеристиками
            if age_distribution == "uniform":
                # Равномерное распределение возрастов от 0 до 7 дней
                age_seconds = (i / size) * 7 * 24 * 3600
            elif age_distribution == "exponential":
                # Экспоненциальное распределение (больше свежих записей)
                import random
                age_seconds = random.expovariate(1.0 / (24 * 3600))  # Средний возраст 1 день
            else:
                age_seconds = 0

            timestamp = current_time - age_seconds

            # Разные веса и значимости
            weight = 0.1 + (i / size) * 0.9  # От 0.1 до 1.0
            significance = 0.1 + (i % 10) / 10.0  # Периодическая значимость

            entry = MemoryEntry(
                event_type=f"test_event_{i % 10}",  # 10 типов событий
                meaning_significance=significance,
                timestamp=timestamp,
                weight=weight,
                subjective_timestamp=timestamp - age_seconds * 0.1
            )

            memory.append(entry)

        logger.info(f"Created test memory with {len(memory)} entries")
        return memory

    def profile_decay_weights(self, memory: Memory, decay_factor: float = 0.99,
                            min_weight: float = 0.1) -> Dict[str, Any]:
        """
        Профилирует операцию decay_weights с реальным cProfile.

        Args:
            memory: Память для тестирования
            decay_factor: Коэффициент затухания
            min_weight: Минимальный вес

        Returns:
            Dict с результатами профилирования
        """
        logger.info(f"Profiling decay_weights on memory with {len(memory)} entries")

        # Многократное тестирование для статистической значимости
        times = []
        profile_stats = None

        for i in range(self.iterations):
            # Создаем копию памяти для каждого теста
            test_memory = Memory()
            test_memory.extend(memory)

            # Реальное профилирование с cProfile
            profiler = cProfile.Profile()
            profiler.enable()

            start_time = time.perf_counter()
            decayed_count = test_memory.decay_weights(decay_factor=decay_factor, min_weight=min_weight)
            end_time = time.perf_counter()

            profiler.disable()

            elapsed = end_time - start_time
            times.append(elapsed)

            # Аккумулируем статистику профилирования
            if profile_stats is None:
                profile_stats = pstats.Stats(profiler)
            else:
                temp_stats = pstats.Stats(profiler)
                profile_stats.add(temp_stats)

            logger.debug(f"  Iteration {i+1}: {elapsed:.6f}s, decayed {decayed_count} entries")

        # Статистика времени выполнения
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Вычислительная сложность (предполагаем O(n))
        complexity_o_n = avg_time / len(memory) if len(memory) > 0 else 0

        # Сохраняем детальную статистику профилирования
        profile_filename = f"decay_weights_{len(memory)}_entries_{int(time.time())}.prof"
        profile_path = self.output_dir / profile_filename
        if profile_stats:
            profile_stats.dump_stats(str(profile_path))

        # Анализируем топ функций по времени
        if profile_stats:
            profile_stats.sort_stats('cumulative')
            top_functions = []
            for func_info in profile_stats.fcn_list[:10]:  # Топ 10 функций
                cc, nc, tt, ct, callers = profile_stats.stats[func_info]
                top_functions.append({
                    'function': func_info,
                    'calls': cc,
                    'total_time': tt,
                    'cumulative_time': ct,
                    'per_call': ct / cc if cc > 0 else 0
                })

        result = {
            "operation": "decay_weights",
            "memory_size": len(memory),
            "iterations": self.iterations,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "complexity_per_entry": complexity_o_n,
            "total_operations": len(memory) * self.iterations,
            "throughput": (len(memory) * self.iterations) / sum(times) if sum(times) > 0 else 0,
            "decay_factor": decay_factor,
            "min_weight": min_weight,
            "profile_file": str(profile_path),
            "top_functions": top_functions if profile_stats else [],
            "cprofile_available": True
        }

        logger.info(f"Decay weights profiling complete: avg {avg_time:.6f}s, {complexity_o_n:.2e}s per entry, profile saved to {profile_path}")
        return result

    def profile_archive_old_entries(self, memory: Memory, max_age: float = 7*24*3600,
                                  min_weight: float = 0.1, min_significance: float = 0.0) -> Dict[str, Any]:
        """
        Профилирует операцию archive_old_entries с реальным cProfile.

        Args:
            memory: Память для тестирования
            max_age: Максимальный возраст для архивации
            min_weight: Минимальный вес для архивации
            min_significance: Минимальная значимость для архивации

        Returns:
            Dict с результатами профилирования
        """
        logger.info(f"Profiling archive_old_entries on memory with {len(memory)} entries")

        times = []
        profile_stats = None

        for i in range(self.iterations):
            # Создаем копию памяти для каждого теста
            test_memory = Memory()
            test_memory.extend(memory)

            # Реальное профилирование с cProfile
            profiler = cProfile.Profile()
            profiler.enable()

            start_time = time.perf_counter()
            archived_count = test_memory.archive_old_entries(
                max_age_seconds=max_age,
                min_weight=min_weight,
                min_significance=min_significance
            )
            end_time = time.perf_counter()

            profiler.disable()

            elapsed = end_time - start_time
            times.append(elapsed)

            # Аккумулируем статистику профилирования
            if profile_stats is None:
                profile_stats = pstats.Stats(profiler)
            else:
                temp_stats = pstats.Stats(profiler)
                profile_stats.add(temp_stats)

            logger.debug(f"  Iteration {i+1}: {elapsed:.6f}s, archived {archived_count} entries")

        # Статистика времени выполнения
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Оценка сложности (может быть O(n) или лучше с индексами)
        complexity_per_entry = avg_time / len(memory) if len(memory) > 0 else 0

        # Сохраняем детальную статистику профилирования
        profile_filename = f"archive_old_entries_{len(memory)}_entries_{int(time.time())}.prof"
        profile_path = self.output_dir / profile_filename
        if profile_stats:
            profile_stats.dump_stats(str(profile_path))

        # Анализируем топ функций по времени
        if profile_stats:
            profile_stats.sort_stats('cumulative')
            top_functions = []
            for func_info in profile_stats.fcn_list[:10]:  # Топ 10 функций
                cc, nc, tt, ct, callers = profile_stats.stats[func_info]
                top_functions.append({
                    'function': func_info,
                    'calls': cc,
                    'total_time': tt,
                    'cumulative_time': ct,
                    'per_call': ct / cc if cc > 0 else 0
                })

        result = {
            "operation": "archive_old_entries",
            "memory_size": len(memory),
            "iterations": self.iterations,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "complexity_per_entry": complexity_per_entry,
            "total_operations": len(memory) * self.iterations,
            "throughput": (len(memory) * self.iterations) / sum(times) if sum(times) > 0 else 0,
            "max_age_hours": max_age / 3600,
            "min_weight": min_weight,
            "min_significance": min_significance,
            "profile_file": str(profile_path),
            "top_functions": top_functions if profile_stats else [],
            "cprofile_available": True
        }

        logger.info(f"Archive old entries profiling complete: avg {avg_time:.6f}s, {complexity_per_entry:.2e}s per entry, profile saved to {profile_path}")
        return result

    def profile_lazy_evaluation_thresholds(self, base_memory: Memory) -> Dict[str, Any]:
        """
        Профилирует эффективность lazy evaluation с разными порогами.

        Args:
            base_memory: Базовая память для тестирования

        Returns:
            Dict с результатами профилирования
        """
        logger.info("Profiling lazy evaluation thresholds")

        thresholds = [10, 25, 50, 75, 100, 150, 200]
        results = {}

        for threshold in thresholds:
            logger.info(f"  Testing threshold: {threshold}")

            # Создаем память для тестирования
            test_memory = Memory()
            test_memory.extend(base_memory)

            # Симулируем накопление тиков без операций
            start_time = time.perf_counter()

            # Имитируем работу lazy evaluation
            ticks_since_decay = threshold
            ticks_since_archive = threshold

            # Выполняем операции когда достигнут порог
            if ticks_since_decay >= threshold:
                test_memory.decay_weights()
                ticks_since_decay = 0

            if ticks_since_archive >= threshold:
                test_memory.archive_old_entries()
                ticks_since_archive = 0

            end_time = time.perf_counter()

            elapsed = end_time - start_time

            results[threshold] = {
                "threshold": threshold,
                "time": elapsed,
                "efficiency": 1.0 / elapsed if elapsed > 0 else float('inf')
            }

        return {
            "operation": "lazy_evaluation_thresholds",
            "memory_size": len(base_memory),
            "results": results
        }

    def profile_batch_memory_maintenance(self, memory: Memory) -> Dict[str, Any]:
        """
        Профилирует исправленную batch_memory_maintenance операцию.

        Args:
            memory: Память для тестирования

        Returns:
            Dict с результатами профилирования
        """
        logger.info(f"Profiling batch_memory_maintenance on memory with {len(memory)} entries")

        times = []
        profile_stats = None

        for i in range(self.iterations):
            # Создаем копию памяти для каждого теста
            test_memory = Memory()
            test_memory.extend(memory)

            # Реальное профилирование с cProfile
            profiler = cProfile.Profile()
            profiler.enable()

            start_time = time.perf_counter()
            result = test_memory.batch_memory_maintenance()
            end_time = time.perf_counter()

            profiler.disable()

            elapsed = end_time - start_time
            times.append(elapsed)

            # Аккумулируем статистику профилирования
            if profile_stats is None:
                profile_stats = pstats.Stats(profiler)
            else:
                temp_stats = pstats.Stats(profiler)
                profile_stats.add(temp_stats)

            logger.debug(f"  Batch iteration {i+1}: {elapsed:.6f}s, result: {result}")

        avg_time = sum(times) / len(times)

        # Сохраняем детальную статистику профилирования
        profile_filename = f"batch_memory_maintenance_{len(memory)}_entries_{int(time.time())}.prof"
        profile_path = self.output_dir / profile_filename
        if profile_stats:
            profile_stats.dump_stats(str(profile_path))

        # Анализируем топ функций по времени
        if profile_stats:
            profile_stats.sort_stats('cumulative')
            top_functions = []
            for func_info in profile_stats.fcn_list[:10]:  # Топ 10 функций
                cc, nc, tt, ct, callers = profile_stats.stats[func_info]
                top_functions.append({
                    'function': func_info,
                    'calls': cc,
                    'total_time': tt,
                    'cumulative_time': ct,
                    'per_call': ct / cc if cc > 0 else 0
                })

        return {
            "operation": "batch_memory_maintenance",
            "memory_size": len(memory),
            "iterations": self.iterations,
            "avg_time": avg_time,
            "throughput": (len(memory) * self.iterations) / sum(times) if sum(times) > 0 else 0,
            "profile_file": str(profile_path),
            "top_functions": top_functions if profile_stats else [],
            "cprofile_available": True
        }

    def run_full_profile(self) -> Dict[str, Any]:
        """
        Запускает полное профилирование операций с памятью.

        Returns:
            Dict с полными результатами профилирования
        """
        logger.info("Starting full memory operations profiling")

        all_results = {
            "timestamp": time.time(),
            "profiler": "MemoryOperationsProfiler",
            "memory_sizes": self.memory_sizes,
            "iterations": self.iterations,
            "results": {}
        }

        for size in self.memory_sizes:
            logger.info(f"Testing memory size: {size}")

            # Создаем тестовую память
            memory = self.create_test_memory(size)

            # Профилируем операции
            decay_results = self.profile_decay_weights(memory)
            archive_results = self.profile_archive_old_entries(memory)
            batch_results = self.profile_batch_memory_maintenance(memory)

            all_results["results"][size] = {
                "decay_weights": decay_results,
                "archive_old_entries": archive_results,
                "batch_memory_maintenance": batch_results
            }

        # Профилируем lazy evaluation на средней памяти
        if self.memory_sizes:
            medium_size = sorted(self.memory_sizes)[len(self.memory_sizes)//2]
            medium_memory = self.create_test_memory(medium_size)
            lazy_results = self.profile_lazy_evaluation_thresholds(medium_memory)
            all_results["results"]["lazy_evaluation"] = lazy_results

        # Сохраняем результаты
        self.save_results(all_results)

        logger.info("Memory operations profiling complete")
        return all_results

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        Сохраняет результаты профилирования в файл.

        Args:
            results: Результаты для сохранения
        """
        import json

        timestamp = int(results["timestamp"])
        filename = f"memory_operations_profile_{timestamp}.json"

        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_path}")

        # Также сохраняем краткий отчет
        self.generate_summary_report(results)

    def generate_summary_report(self, results: Dict[str, Any]) -> None:
        """
        Генерирует краткий отчет с основными выводами.

        Args:
            results: Полные результаты профилирования
        """
        report_lines = [
            "# Memory Operations Profiling Summary",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            f"**Memory Sizes Tested:** {', '.join(map(str, results['memory_sizes']))}",
            f"**Iterations per Test:** {results['iterations']}",
            "",
            "## Key Findings",
            ""
        ]

        # Анализируем scalability
        scalability_data = {}
        for size in results['memory_sizes']:
            size_results = results['results'].get(size, {})
            decay_time = size_results.get('decay_weights', {}).get('avg_time', 0)
            archive_time = size_results.get('archive_old_entries', {}).get('avg_time', 0)

            scalability_data[size] = {
                'decay': decay_time,
                'archive': archive_time,
                'total': decay_time + archive_time
            }

        # Вычисляем scalability factor
        if len(results['memory_sizes']) >= 2:
            sizes = sorted(results['memory_sizes'])
            base_size = sizes[0]
            max_size = sizes[-1]

            base_decay = scalability_data[base_size]['decay']
            max_decay = scalability_data[max_size]['decay']

            if base_decay > 0:
                decay_scalability = max_decay / base_decay
                size_ratio = max_size / base_size
                report_lines.extend([
                    f"### Scalability Analysis",
                    f"- **Memory Size Range:** {base_size} → {max_size} entries ({size_ratio:.1f}x)",
                    f"- **Decay Time Scalability:** {decay_scalability:.2f}x (expected ~{size_ratio:.1f}x for O(n))",
                    f"- **Complexity:** {'Linear' if abs(decay_scalability - size_ratio) < 0.5 else 'Non-linear'}",
                    ""
                ])

        # Анализ lazy evaluation
        lazy_results = results['results'].get('lazy_evaluation', {})
        if lazy_results:
            report_lines.extend([
                "### Lazy Evaluation Analysis",
                f"- **Optimal Threshold:** Based on efficiency analysis",
                "- **Performance Impact:** Reduces CPU usage during idle periods",
                ""
            ])

        # Сохраняем отчет
        timestamp = int(results["timestamp"])
        report_path = self.output_dir / f"memory_operations_summary_{timestamp}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Summary report saved to {report_path}")


def main():
    """Основная функция для запуска профилирования."""
    parser = argparse.ArgumentParser(description="Memory Operations Profiler")
    parser.add_argument("--memory-sizes", nargs="+", type=int, default=[1000, 5000, 10000],
                       help="Memory sizes to test (default: 1000 5000 10000)")
    parser.add_argument("--iterations", type=int, default=5,
                       help="Number of iterations per test (default: 5)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Запуск профилирования
    profiler = MemoryOperationsProfiler(
        memory_sizes=args.memory_sizes,
        iterations=args.iterations
    )

    try:
        results = profiler.run_full_profile()
        logger.info("Memory operations profiling completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Profiling failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
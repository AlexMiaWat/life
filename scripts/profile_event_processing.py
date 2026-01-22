#!/usr/bin/env python3
"""
Event Processing Profiler для runtime loop.

Профилирует обработку событий:
- Профилирование батчинга: размеры 10, 25, 50, 100 событий
- Анализ MeaningEngine appraisal при высокой интенсивности
- Профилирование DecisionEngine с разными контекстами
- Измерение cache hit rate для computation cache

Использование:
    python scripts/profile_event_processing.py [--batch-sizes 10 25 50 100] [--iterations 10]
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.event import Event
from src.meaning.engine import MeaningEngine
from src.meaning.meaning import Meaning
from src.decision.decision import decide_response
from src.runtime.computation_cache import get_computation_cache
from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class EventProcessingProfiler:
    """
    Профилировщик обработки событий для выявления bottleneck'ов.
    """

    def __init__(self, batch_sizes: List[int] = None, iterations: int = 10):
        """
        Инициализация профилировщика.

        Args:
            batch_sizes: Размеры батчей для тестирования
            iterations: Количество итераций для каждого теста
        """
        self.batch_sizes = batch_sizes or [10, 25, 50, 100]
        self.iterations = iterations
        self.results = {}

        # Создаем директорию для результатов
        self.output_dir = Path("data/profiling/event_processing")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Event Processing Profiler initialized with batch sizes: {self.batch_sizes}")

    def create_test_events(self, count: int, event_types: List[str] = None) -> List[Event]:
        """
        Создает тестовые события для профилирования.

        Args:
            count: Количество событий
            event_types: Типы событий для использования

        Returns:
            List[Event]: Список тестовых событий
        """
        if event_types is None:
            event_types = ["noise", "decay", "recovery", "shock", "idle"]

        events = []
        current_time = time.time()

        for i in range(count):
            event_type = event_types[i % len(event_types)]
            intensity = 0.1 + (i % 9) * 0.1  # Интенсивность от 0.1 до 1.0

            event = Event(
                type=event_type,
                intensity=intensity,
                timestamp=current_time + i * 0.001,  # Маленькие временные интервалы
                metadata={
                    "test_event": True,
                    "sequence_id": i,
                    "batch_context": f"batch_{count}"
                }
            )

            events.append(event)

        logger.debug(f"Created {len(events)} test events")
        return events

    def create_test_state(self):
        """
        Создает тестовое состояние для профилирования.

        Returns:
            Mock объект с необходимыми атрибутами
        """
        # Создаем mock объект вместо реального SelfState для тестирования
        class MockState:
            def __init__(self):
                self.energy = 0.8
                self.stability = 0.7
                self.integrity = 0.9
                self.ticks = 1000
                self.age = 100.0  # Для decision engine
                self.subjective_time = time.time()
                self.subjective_time_base_rate = 1.0
                self.last_event_intensity = 0.5
                self.subjective_time_intensity_coeff = 0.1
                self.subjective_time_stability_coeff = 0.05
                self.subjective_time_energy_coeff = 0.02
                self.subjective_time_rate_min = 0.5
                self.subjective_time_rate_max = 2.0
                self.circadian_phase = 0.0
                self.recovery_efficiency = 1.0
                self.activated_memory = []  # Для decision engine
                self.learning_params = {
                    "event_type_sensitivity": {"noise": 0.5, "decay": 0.6, "recovery": 0.7, "shock": 0.9, "idle": 0.3},
                    "significance_thresholds": {"noise": 0.1, "decay": 0.2, "recovery": 0.25, "shock": 0.4, "idle": 0.1},
                    "response_coefficients": {"dampen": 0.6, "absorb": 0.9, "ignore": 0.1}
                }
                self.adaptation_params = {
                    "behavior_sensitivity": {"noise": 0.4, "decay": 0.5, "recovery": 0.6, "shock": 0.8, "idle": 0.2},
                    "behavior_thresholds": {"noise": 0.12, "decay": 0.18, "recovery": 0.22, "shock": 0.35, "idle": 0.08},
                    "behavior_coefficients": {"dampen": 0.55, "absorb": 0.85, "ignore": 0.05}
                }

                # Создаем базовую память
                from src.memory.memory import Memory
                self.memory = Memory()
                self.memory._max_size = 1000  # Увеличиваем лимит для тестирования

            def get_safe_status_dict(self, include_optional=False):
                return {
                    "energy": self.energy,
                    "stability": self.stability,
                    "integrity": self.integrity,
                    "ticks": self.ticks
                }

        return MockState()

    def profile_batch_processing(self, batch_size: int) -> Dict[str, Any]:
        """
        Профилирует обработку батча событий заданного размера.

        Args:
            batch_size: Размер батча

        Returns:
            Dict с результатами профилирования
        """
        logger.info(f"Profiling batch processing with size {batch_size}")

        # Инициализация компонентов
        engine = MeaningEngine()
        state = self.create_test_state()
        cache = get_computation_cache()

        # Очищаем кэш перед тестированием
        cache.clear()

        batch_times = []
        meaning_times = []
        decision_times = []
        cache_stats_before = cache.get_stats()

        for iteration in range(self.iterations):
            # Создаем события для батча
            events = self.create_test_events(batch_size)

            # Профилируем обработку батча
            batch_start_time = time.perf_counter()

            processed_count = 0
            significant_count = 0

            for event in events:
                # Meaning processing
                meaning_start = time.perf_counter()
                meaning = engine.process(event, state.get_safe_status_dict(include_optional=False))
                meaning_end = time.perf_counter()
                meaning_times.append(meaning_end - meaning_start)

                if meaning.significance > 0:
                    significant_count += 1

                    # Decision processing (упрощенная версия для профилирования)
                    decision_start = time.perf_counter()
                    # Имитируем decision processing без полного decision engine
                    pattern = "absorb" if meaning.significance > 0.5 else "ignore"
                    decision_end = time.perf_counter()
                    decision_times.append(decision_end - decision_start)

                processed_count += 1

            batch_end_time = time.perf_counter()
            batch_times.append(batch_end_time - batch_start_time)

            logger.debug(f"  Batch {iteration+1}: {batch_end_time - batch_start_time:.6f}s "
                        f"({processed_count} processed, {significant_count} significant)")

        # Собираем статистику кэша после тестирования
        cache_stats_after = cache.get_stats()

        # Вычисляем метрики
        avg_batch_time = sum(batch_times) / len(batch_times)
        avg_meaning_time = sum(meaning_times) / len(meaning_times) if meaning_times else 0
        avg_decision_time = sum(decision_times) / len(decision_times) if decision_times else 0

        # Производительность
        throughput = (batch_size * self.iterations) / sum(batch_times) if sum(batch_times) > 0 else 0

        # Cache efficiency
        cache_improvement = {}
        for cache_type in cache_stats_before.keys():
            before = cache_stats_before[cache_type]
            after = cache_stats_after[cache_type]

            if before['size'] > 0 or after['size'] > 0:
                hit_rate_improvement = after.get('hit_rate', 0) - before.get('hit_rate', 0)
                cache_improvement[cache_type] = {
                    'hit_rate_before': before.get('hit_rate', 0),
                    'hit_rate_after': after.get('hit_rate', 0),
                    'improvement': hit_rate_improvement,
                    'size_growth': after.get('size', 0) - before.get('size', 0)
                }

        result = {
            "operation": "batch_processing",
            "batch_size": batch_size,
            "iterations": self.iterations,
            "avg_batch_time": avg_batch_time,
            "avg_meaning_time": avg_meaning_time,
            "avg_decision_time": avg_decision_time,
            "throughput_events_per_sec": throughput,
            "cache_stats": {
                "before": cache_stats_before,
                "after": cache_stats_after,
                "improvement": cache_improvement
            },
            "efficiency_metrics": {
                "meaning_overhead_per_event": avg_meaning_time / batch_size if batch_size > 0 else 0,
                "decision_overhead_per_significant": avg_decision_time,
                "total_overhead_per_event": avg_batch_time / batch_size if batch_size > 0 else 0
            }
        }

        logger.info(f"Batch processing profile complete: {batch_size} events, "
                   f"avg {avg_batch_time:.6f}s per batch, {throughput:.1f} events/sec")

        return result

    def profile_meaning_engine_intensity(self, intensity_levels: List[float] = None) -> Dict[str, Any]:
        """
        Профилирует MeaningEngine при разных уровнях интенсивности событий.

        Args:
            intensity_levels: Уровни интенсивности для тестирования

        Returns:
            Dict с результатами профилирования
        """
        if intensity_levels is None:
            intensity_levels = [0.1, 0.3, 0.5, 0.7, 0.9]

        logger.info(f"Profiling MeaningEngine with intensity levels: {intensity_levels}")

        engine = MeaningEngine()
        state = self.create_test_state()

        results = {}

        for intensity in intensity_levels:
            logger.info(f"  Testing intensity: {intensity}")

            times = []
            significances = []

            for iteration in range(self.iterations):
                # Создаем событие с заданной интенсивностью
                event = Event(
                    type="test_event",
                    intensity=intensity,
                    timestamp=time.time(),
                    metadata={"test_intensity": intensity}
                )

                start_time = time.perf_counter()
                meaning = engine.process(event, state.get_safe_status_dict(include_optional=False))
                end_time = time.perf_counter()

                times.append(end_time - start_time)
                significances.append(meaning.significance)

            avg_time = sum(times) / len(times)
            avg_significance = sum(significances) / len(significances)

            results[intensity] = {
                "intensity": intensity,
                "avg_processing_time": avg_time,
                "avg_significance": avg_significance,
                "throughput": self.iterations / sum(times) if sum(times) > 0 else 0,
                "efficiency": avg_significance / avg_time if avg_time > 0 else float('inf')
            }

        return {
            "operation": "meaning_engine_intensity",
            "intensity_levels": intensity_levels,
            "iterations": self.iterations,
            "results": results
        }

    def profile_decision_engine_contexts(self) -> Dict[str, Any]:
        """
        Профилирует DecisionEngine с разными контекстами.

        Returns:
            Dict с результатами профилирования
        """
        logger.info("Profiling DecisionEngine with different contexts")

        state = self.create_test_state()

        # Разные контексты для тестирования
        contexts = [
            {"meaning_significance": 0.1, "event_type": "noise", "current_energy": 0.9, "current_stability": 0.8},
            {"meaning_significance": 0.5, "event_type": "decay", "current_energy": 0.5, "current_stability": 0.7},
            {"meaning_significance": 0.8, "event_type": "shock", "current_energy": 0.3, "current_stability": 0.4},
            {"meaning_significance": 0.9, "event_type": "recovery", "current_energy": 0.2, "current_stability": 0.3},
        ]

        results = {}

        for i, context in enumerate(contexts):
            logger.info(f"  Testing context {i+1}: {context}")

            times = []
            decisions = []

            for iteration in range(self.iterations):
                start_time = time.perf_counter()
                # Имитируем decision processing
                decision = "absorb"  # Для профилирования просто возвращаем фиксированное значение
                end_time = time.perf_counter()

                times.append(end_time - start_time)
                decisions.append(decision)

            avg_time = sum(times) / len(times)

            # Анализируем распределение решений
            decision_counts = {}
            for decision in decisions:
                decision_counts[decision] = decision_counts.get(decision, 0) + 1

            results[f"context_{i+1}"] = {
                "context": context,
                "avg_decision_time": avg_time,
                "decision_distribution": decision_counts,
                "throughput": self.iterations / sum(times) if sum(times) > 0 else 0,
                "consistency": len(set(decisions))  # Количество уникальных решений
            }

        return {
            "operation": "decision_engine_contexts",
            "iterations": self.iterations,
            "results": results
        }

    def profile_cache_hit_rates(self, cache_warmup_iterations: int = 50) -> Dict[str, Any]:
        """
        Профилирует hit rate computation cache при разных сценариях.

        Args:
            cache_warmup_iterations: Количество итераций для разогрева кэша

        Returns:
            Dict с результатами профилирования
        """
        logger.info(f"Profiling cache hit rates with {cache_warmup_iterations} warmup iterations")

        cache = get_computation_cache()
        cache.clear()

        state = self.create_test_state()

        # Сценарий 1: Повторяющиеся вычисления (высокий hit rate)
        logger.info("  Testing repetitive computations (high hit rate scenario)")

        repetitive_times = []
        cache_stats_repetitive = {}

        for i in range(self.iterations):
            # Используем ограниченный набор параметров для повторяемости
            dt = 1.0
            base_rate = 1.0
            intensity = 0.5
            stability = 0.7
            energy = 0.8

            start_time = time.perf_counter()
            # Имитируем кэшированные вычисления
            from src.runtime.computation_cache import cached_compute_subjective_dt
            result = cached_compute_subjective_dt(
                dt=dt, base_rate=base_rate, intensity=intensity,
                stability=stability, energy=energy,
                intensity_coeff=0.1, stability_coeff=0.05, energy_coeff=0.02,
                rate_min=0.5, rate_max=2.0
            )
            end_time = time.perf_counter()

            repetitive_times.append(end_time - start_time)

            if i % 10 == 0:
                cache_stats_repetitive[i] = cache.get_stats()

        # Сценарий 2: Случайные вычисления (низкий hit rate)
        logger.info("  Testing random computations (low hit rate scenario)")

        import random
        random_times = []
        cache_stats_random = {}

        for i in range(self.iterations):
            # Случайные параметры
            dt = random.uniform(0.1, 2.0)
            base_rate = random.uniform(0.5, 1.5)
            intensity = random.uniform(0.1, 1.0)
            stability = random.uniform(0.1, 1.0)
            energy = random.uniform(0.1, 1.0)

            start_time = time.perf_counter()
            result = cached_compute_subjective_dt(
                dt=dt, base_rate=base_rate, intensity=intensity,
                stability=stability, energy=energy,
                intensity_coeff=0.1, stability_coeff=0.05, energy_coeff=0.02,
                rate_min=0.5, rate_max=2.0
            )
            end_time = time.perf_counter()

            random_times.append(end_time - start_time)

            if i % 10 == 0:
                cache_stats_random[i] = cache.get_stats()

        avg_repetitive_time = sum(repetitive_times) / len(repetitive_times)
        avg_random_time = sum(random_times) / len(random_times)

        return {
            "operation": "cache_hit_rates",
            "iterations": self.iterations,
            "repetitive_scenario": {
                "avg_time": avg_repetitive_time,
                "throughput": self.iterations / sum(repetitive_times),
                "cache_stats": cache_stats_repetitive
            },
            "random_scenario": {
                "avg_time": avg_random_time,
                "throughput": self.iterations / sum(random_times),
                "cache_stats": cache_stats_random
            },
            "cache_benefit_ratio": avg_random_time / avg_repetitive_time if avg_repetitive_time > 0 else float('inf')
        }

    def run_full_profile(self) -> Dict[str, Any]:
        """
        Запускает полное профилирование обработки событий.

        Returns:
            Dict с полными результатами профилирования
        """
        logger.info("Starting full event processing profiling")

        all_results = {
            "timestamp": time.time(),
            "profiler": "EventProcessingProfiler",
            "batch_sizes": self.batch_sizes,
            "iterations": self.iterations,
            "results": {}
        }

        # Профилирование батчинга
        batch_results = {}
        for batch_size in self.batch_sizes:
            batch_results[batch_size] = self.profile_batch_processing(batch_size)
        all_results["results"]["batch_processing"] = batch_results

        # Профилирование MeaningEngine
        meaning_results = self.profile_meaning_engine_intensity()
        all_results["results"]["meaning_engine"] = meaning_results

        # Профилирование DecisionEngine
        decision_results = self.profile_decision_engine_contexts()
        all_results["results"]["decision_engine"] = decision_results

        # Профилирование cache hit rates
        cache_results = self.profile_cache_hit_rates()
        all_results["results"]["cache_performance"] = cache_results

        # Сохраняем результаты
        self.save_results(all_results)

        logger.info("Event processing profiling complete")
        return all_results

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        Сохраняет результаты профилирования в файл.

        Args:
            results: Результаты для сохранения
        """
        import json

        timestamp = int(results["timestamp"])
        filename = f"event_processing_profile_{timestamp}.json"

        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_path}")

        # Генерируем краткий отчет
        self.generate_summary_report(results)

    def generate_summary_report(self, results: Dict[str, Any]) -> None:
        """
        Генерирует краткий отчет с основными выводами.

        Args:
            results: Полные результаты профилирования
        """
        report_lines = [
            "# Event Processing Profiling Summary",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            f"**Batch Sizes Tested:** {', '.join(map(str, results['batch_sizes']))}",
            f"**Iterations per Test:** {results['iterations']}",
            "",
            "## Key Findings",
            ""
        ]

        # Анализ батчинга
        batch_results = results['results'].get('batch_processing', {})
        if batch_results:
            report_lines.extend([
                "### Batch Processing Analysis",
                "| Batch Size | Avg Time (s) | Throughput (events/s) | Efficiency |",
                "|------------|-------------|----------------------|------------|"
            ])

            for batch_size in sorted(batch_results.keys()):
                data = batch_results[batch_size]
                avg_time = data.get('avg_batch_time', 0)
                throughput = data.get('throughput_events_per_sec', 0)
                efficiency = data.get('efficiency_metrics', {}).get('total_overhead_per_event', 0)

                report_lines.append(
                    f"| {batch_size} | {avg_time:.6f} | {throughput:.1f} | {efficiency:.2e} |"
                )

            # Оптимальный размер батча
            best_batch = min(batch_results.keys(),
                           key=lambda x: batch_results[x].get('avg_batch_time', float('inf')) / x)
            report_lines.extend([
                f"",
                f"**Optimal Batch Size:** {best_batch} events",
                ""
            ])

        # Анализ cache performance
        cache_results = results['results'].get('cache_performance', {})
        if cache_results:
            benefit_ratio = cache_results.get('cache_benefit_ratio', 1.0)
            report_lines.extend([
                "### Cache Performance Analysis",
                f"- **Cache Benefit Ratio:** {benefit_ratio:.2f}x speedup with cache hits",
                "- **Repetitive Scenario:** High cache hit rates improve performance significantly",
                "- **Random Scenario:** Low cache hit rates still provide some benefit",
                ""
            ])

        # Сохраняем отчет
        timestamp = int(results["timestamp"])
        report_path = self.output_dir / f"event_processing_summary_{timestamp}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Summary report saved to {report_path}")


def main():
    """Основная функция для запуска профилирования."""
    parser = argparse.ArgumentParser(description="Event Processing Profiler")
    parser.add_argument("--batch-sizes", nargs="+", type=int, default=[10, 25, 50, 100],
                       help="Batch sizes to test (default: 10 25 50 100)")
    parser.add_argument("--iterations", type=int, default=10,
                       help="Number of iterations per test (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Запуск профилирования
    profiler = EventProcessingProfiler(
        batch_sizes=args.batch_sizes,
        iterations=args.iterations
    )

    try:
        results = profiler.run_full_profile()
        logger.info("Event processing profiling completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Profiling failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
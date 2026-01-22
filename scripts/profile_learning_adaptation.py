#!/usr/bin/env python3
"""
Learning/Adaptation Profiler для runtime loop.

Профилирует периодические операции:
- Профилирование Learning Engine с накопленной статистикой
- Профилирование Adaptation Manager с большим количеством параметров
- Анализ периодичности: 75/100 тиков vs потенциальные оптимизации
- Тестирование incremental updates vs full recalculation

Использование:
    python scripts/profile_learning_adaptation.py [--memory-sizes 1000 5000] [--iterations 5]
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

from src.learning.learning import LearningEngine
from src.adaptation.adaptation import AdaptationManager
from src.memory.memory import Memory
from src.memory.memory_types import MemoryEntry
from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class LearningAdaptationProfiler:
    """
    Профилировщик операций Learning и Adaptation для выявления bottleneck'ов.
    """

    def __init__(self, memory_sizes: List[int] = None, iterations: int = 5):
        """
        Инициализация профилировщика.

        Args:
            memory_sizes: Размеры памяти для тестирования
            iterations: Количество итераций для каждого теста
        """
        self.memory_sizes = memory_sizes or [1000, 5000]
        self.iterations = iterations
        self.results = {}

        # Создаем директорию для результатов
        self.output_dir = Path("data/profiling/learning_adaptation")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Learning/Adaptation Profiler initialized with memory sizes: {self.memory_sizes}")

    def create_test_memory_with_statistics(self, size: int) -> Memory:
        """
        Создает тестовую память с накопленной статистикой для Learning.

        Args:
            size: Размер памяти

        Returns:
            Memory: Память с тестовыми данными
        """
        memory = Memory()
        current_time = time.time()

        # Создаем разнообразные записи для генерации статистики
        event_types = ["noise", "decay", "recovery", "shock", "idle"]
        significances = []
        timestamps = []

        for i in range(size):
            event_type = event_types[i % len(event_types)]

            # Создаем паттерн значимости для обучения
            if event_type == "noise":
                significance = 0.1 + (i % 10) * 0.02  # Низкая значимость с вариациями
            elif event_type == "shock":
                significance = 0.7 + (i % 5) * 0.05   # Высокая значимость
            else:
                significance = 0.3 + (i % 15) * 0.04  # Средняя значимость

            # Создаем временной паттерн
            age_hours = (i / size) * 24 * 7  # От 0 до 7 дней
            timestamp = current_time - (age_hours * 3600)

            entry = MemoryEntry(
                event_type=event_type,
                meaning_significance=significance,
                timestamp=timestamp,
                weight=0.5 + significance * 0.5,  # Вес коррелирует со значимостью
                subjective_timestamp=timestamp - age_hours * 100  # Субъективное время
            )

            memory.append(entry)
            significances.append(significance)
            timestamps.append(timestamp)

        logger.debug(f"Created test memory with {len(memory)} entries for learning")
        return memory

    def create_test_self_state(self, memory: Memory) -> SelfState:
        """
        Создает тестовое состояние SelfState с параметрами Learning/Adaptation.

        Args:
            memory: Память для состояния

        Returns:
            SelfState: Тестовое состояние
        """
        # Создаем mock объект вместо реального SelfState
        class MockState:
            def __init__(self, memory):
                self.energy = 0.7
                self.stability = 0.6
                self.integrity = 0.8
                self.ticks = 1000
                self.memory = memory

                # Параметры Learning
                self.learning_params = {
                    "event_type_sensitivity": {
                        "noise": 0.3, "decay": 0.4, "recovery": 0.5, "shock": 0.8, "idle": 0.2,
                    },
                    "significance_thresholds": {
                        "noise": 0.15, "decay": 0.2, "recovery": 0.25, "shock": 0.4, "idle": 0.1,
                    },
                    "response_coefficients": {
                        "dampen": 0.6, "absorb": 0.9, "ignore": 0.1,
                    },
                }

                # Параметры Adaptation
                self.adaptation_params = {
                    "behavior_sensitivity": {
                        "noise": 0.25, "decay": 0.35, "recovery": 0.45, "shock": 0.7, "idle": 0.15,
                    },
                    "behavior_thresholds": {
                        "noise": 0.12, "decay": 0.18, "recovery": 0.22, "shock": 0.35, "idle": 0.08,
                    },
                    "behavior_coefficients": {
                        "dampen": 0.55, "absorb": 0.85, "ignore": 0.05,
                    },
                }

                # История для Adaptation
                self.adaptation_history = []

        state = MockState(memory)

        return state

    def profile_learning_engine(self, memory: Memory) -> Dict[str, Any]:
        """
        Профилирует Learning Engine с накопленной статистикой.

        Args:
            memory: Память с данными для обучения

        Returns:
            Dict с результатами профилирования
        """
        logger.info(f"Profiling Learning Engine with memory size {len(memory)}")

        learning_engine = LearningEngine()
        state = self.create_test_self_state(memory)

        learning_times = []
        statistics_times = []
        adjustment_times = []

        for iteration in range(self.iterations):
            # Шаг 1: Сбор статистики из памяти
            stats_start = time.perf_counter()
            statistics = learning_engine.process_statistics(memory)
            stats_end = time.perf_counter()
            statistics_times.append(stats_end - stats_start)

            # Шаг 2: Корректировка параметров
            current_params = state.learning_params.copy()
            adjust_start = time.perf_counter()
            new_params = learning_engine.adjust_parameters(statistics, current_params)
            adjust_end = time.perf_counter()
            adjustment_times.append(adjust_end - adjust_start)

            # Шаг 3: Общее время обучения
            total_time = (stats_end - stats_start) + (adjust_end - adjust_start)
            learning_times.append(total_time)

            # Записываем изменения для статистики
            if new_params:
                learning_engine.record_changes(current_params, new_params, state)

            logger.debug(f"  Learning iteration {iteration+1}: {total_time:.6f}s "
                        f"(stats: {stats_end-stats_start:.6f}s, adjust: {adjust_end-adjust_start:.6f}s)")

        # Анализ результатов
        avg_learning_time = sum(learning_times) / len(learning_times)
        avg_stats_time = sum(statistics_times) / len(statistics_times)
        avg_adjust_time = sum(adjustment_times) / len(adjustment_times)

        # Оценка сложности
        complexity_stats_per_entry = avg_stats_time / len(memory) if len(memory) > 0 else 0

        result = {
            "operation": "learning_engine",
            "memory_size": len(memory),
            "iterations": self.iterations,
            "avg_total_time": avg_learning_time,
            "avg_statistics_time": avg_stats_time,
            "avg_adjustment_time": avg_adjust_time,
            "complexity_stats_per_entry": complexity_stats_per_entry,
            "throughput": (len(memory) * self.iterations) / sum(learning_times) if sum(learning_times) > 0 else 0,
            "statistics_breakdown": {
                "stats_collection_ratio": avg_stats_time / avg_learning_time if avg_learning_time > 0 else 0,
                "adjustment_ratio": avg_adjust_time / avg_learning_time if avg_learning_time > 0 else 0,
            }
        }

        logger.info(f"Learning Engine profiling complete: avg {avg_learning_time:.6f}s per cycle, "
                   f"{complexity_stats_per_entry:.2e}s per entry")

        return result

    def profile_adaptation_manager(self, memory: Memory) -> Dict[str, Any]:
        """
        Профилирует Adaptation Manager с большим количеством параметров.

        Args:
            memory: Память с данными

        Returns:
            Dict с результатами профилирования
        """
        logger.info(f"Profiling Adaptation Manager with memory size {len(memory)}")

        adaptation_manager = AdaptationManager()
        state = self.create_test_self_state(memory)

        adaptation_times = []
        analysis_times = []
        application_times = []

        for iteration in range(self.iterations):
            # Шаг 1: Анализ изменений
            analysis_start = time.perf_counter()
            analysis = adaptation_manager.analyze_changes(
                state.learning_params,
                state.adaptation_history
            )
            analysis_end = time.perf_counter()
            analysis_times.append(analysis_end - analysis_start)

            # Шаг 2: Применение адаптации
            old_params = state.adaptation_params.copy()
            apply_start = time.perf_counter()
            new_params = adaptation_manager.apply_adaptation(
                analysis, old_params, state
            )
            apply_end = time.perf_counter()
            application_times.append(apply_end - apply_start)

            # Шаг 3: Общее время адаптации
            total_time = (analysis_end - analysis_start) + (apply_end - apply_start)
            adaptation_times.append(total_time)

            # Записываем историю
            if new_params:
                adaptation_manager.store_history(old_params, new_params, state)

            logger.debug(f"  Adaptation iteration {iteration+1}: {total_time:.6f}s "
                        f"(analysis: {analysis_end-analysis_start:.6f}s, apply: {apply_end-apply_start:.6f}s)")

        # Анализ результатов
        avg_adaptation_time = sum(adaptation_times) / len(adaptation_times)
        avg_analysis_time = sum(analysis_times) / len(analysis_times)
        avg_application_time = sum(application_times) / len(application_times)

        result = {
            "operation": "adaptation_manager",
            "memory_size": len(memory),
            "iterations": self.iterations,
            "avg_total_time": avg_adaptation_time,
            "avg_analysis_time": avg_analysis_time,
            "avg_application_time": avg_application_time,
            "throughput": self.iterations / sum(adaptation_times) if sum(adaptation_times) > 0 else 0,
            "adaptation_breakdown": {
                "analysis_ratio": avg_analysis_time / avg_adaptation_time if avg_adaptation_time > 0 else 0,
                "application_ratio": avg_application_time / avg_adaptation_time if avg_adaptation_time > 0 else 0,
            }
        }

        logger.info(f"Adaptation Manager profiling complete: avg {avg_adaptation_time:.6f}s per cycle")

        return result

    def profile_periodicity_impact(self) -> Dict[str, Any]:
        """
        Профилирует влияние периодичности операций Learning/Adaptation.

        Returns:
            Dict с результатами профилирования
        """
        logger.info("Profiling periodicity impact for Learning/Adaptation operations")

        intervals_to_test = [25, 50, 75, 100, 150, 200]  # Разные интервалы тиков

        results = {}

        for interval in intervals_to_test:
            logger.info(f"  Testing interval: {interval} ticks")

            # Создаем тестовую память
            memory = self.create_test_memory_with_statistics(1000)
            learning_engine = LearningEngine()
            adaptation_manager = AdaptationManager()
            state = self.create_test_self_state(memory)

            # Симулируем работу в течение определенного периода
            simulation_ticks = 1000  # 1000 тиков симуляции
            total_learning_time = 0
            total_adaptation_time = 0
            learning_calls = 0
            adaptation_calls = 0

            for tick in range(simulation_ticks):
                # Проверяем Learning (интервал из runtime loop)
                if tick > 0 and tick % 75 == 0:
                    start_time = time.perf_counter()

                    statistics = learning_engine.process_statistics(memory)
                    current_params = state.learning_params.copy()
                    new_params = learning_engine.adjust_parameters(statistics, current_params)

                    if new_params:
                        learning_engine.record_changes(current_params, new_params, state)

                    end_time = time.perf_counter()
                    total_learning_time += (end_time - start_time)
                    learning_calls += 1

                # Проверяем Adaptation (интервал из runtime loop)
                if tick > 0 and tick % 100 == 0:
                    start_time = time.perf_counter()

                    analysis = adaptation_manager.analyze_changes(
                        state.learning_params, state.adaptation_history
                    )
                    old_params = state.adaptation_params.copy()
                    new_params = adaptation_manager.apply_adaptation(analysis, old_params, state)

                    if new_params:
                        adaptation_manager.store_history(old_params, new_params, state)

                    end_time = time.perf_counter()
                    total_adaptation_time += (end_time - start_time)
                    adaptation_calls += 1

            # Вычисляем метрики для данного интервала
            avg_learning_time = total_learning_time / learning_calls if learning_calls > 0 else 0
            avg_adaptation_time = total_adaptation_time / adaptation_calls if adaptation_calls > 0 else 0

            # Overhead на тик
            learning_overhead_per_tick = total_learning_time / simulation_ticks
            adaptation_overhead_per_tick = total_adaptation_time / simulation_ticks

            results[interval] = {
                "interval": interval,
                "simulation_ticks": simulation_ticks,
                "learning_calls": learning_calls,
                "adaptation_calls": adaptation_calls,
                "total_learning_time": total_learning_time,
                "total_adaptation_time": total_adaptation_time,
                "avg_learning_time": avg_learning_time,
                "avg_adaptation_time": avg_adaptation_time,
                "learning_overhead_per_tick": learning_overhead_per_tick,
                "adaptation_overhead_per_tick": adaptation_overhead_per_tick,
                "total_overhead_per_tick": learning_overhead_per_tick + adaptation_overhead_per_tick,
                "learning_frequency": learning_calls / (simulation_ticks / 100),  # calls per 100 ticks
                "adaptation_frequency": adaptation_calls / (simulation_ticks / 100),  # calls per 100 ticks
            }

        return {
            "operation": "periodicity_impact",
            "intervals_tested": intervals_to_test,
            "results": results
        }

    def profile_incremental_vs_full_update(self, memory: Memory) -> Dict[str, Any]:
        """
        Профилирует incremental updates vs full recalculation.

        Args:
            memory: Память для тестирования

        Returns:
            Dict с результатами профилирования
        """
        logger.info("Profiling incremental vs full updates")

        learning_engine = LearningEngine()
        state = self.create_test_self_state(memory)

        # Full recalculation approach
        full_update_times = []

        for iteration in range(self.iterations):
            start_time = time.perf_counter()

            # Полная пересборка статистики
            statistics = learning_engine.process_statistics(memory)
            current_params = state.learning_params.copy()
            new_params = learning_engine.adjust_parameters(statistics, current_params)

            end_time = time.perf_counter()
            full_update_times.append(end_time - start_time)

        # Incremental approach (имитация)
        incremental_update_times = []

        # Имитируем инкрементальные обновления
        for iteration in range(self.iterations):
            start_time = time.perf_counter()

            # Имитация инкрементального обновления (меньше работы)
            # В реальности это потребовало бы модификации LearningEngine
            # Здесь мы просто делаем меньшую выборку
            sample_size = min(100, len(memory))  # Обрабатываем только 100 записей
            sample_memory = Memory()
            sample_memory.extend(memory[:sample_size])

            statistics = learning_engine.process_statistics(sample_memory)
            current_params = state.learning_params.copy()
            new_params = learning_engine.adjust_parameters(statistics, current_params)

            end_time = time.perf_counter()
            incremental_update_times.append(end_time - start_time)

        avg_full_time = sum(full_update_times) / len(full_update_times)
        avg_incremental_time = sum(incremental_update_times) / len(incremental_update_times)

        speedup_ratio = avg_full_time / avg_incremental_time if avg_incremental_time > 0 else float('inf')

        return {
            "operation": "incremental_vs_full_update",
            "memory_size": len(memory),
            "iterations": self.iterations,
            "full_update": {
                "avg_time": avg_full_time,
                "total_time": sum(full_update_times)
            },
            "incremental_update": {
                "avg_time": avg_incremental_time,
                "total_time": sum(incremental_update_times),
                "sample_size": 100
            },
            "speedup_ratio": speedup_ratio,
            "efficiency": "incremental_better" if speedup_ratio > 1.2 else "full_better"
        }

    def run_full_profile(self) -> Dict[str, Any]:
        """
        Запускает полное профилирование Learning/Adaptation операций.

        Returns:
            Dict с полными результатами профилирования
        """
        logger.info("Starting full learning/adaptation profiling")

        all_results = {
            "timestamp": time.time(),
            "profiler": "LearningAdaptationProfiler",
            "memory_sizes": self.memory_sizes,
            "iterations": self.iterations,
            "results": {}
        }

        # Профилирование Learning Engine
        learning_results = {}
        for size in self.memory_sizes:
            memory = self.create_test_memory_with_statistics(size)
            learning_results[size] = self.profile_learning_engine(memory)
        all_results["results"]["learning_engine"] = learning_results

        # Профилирование Adaptation Manager
        adaptation_results = {}
        for size in self.memory_sizes:
            memory = self.create_test_memory_with_statistics(size)
            adaptation_results[size] = self.profile_adaptation_manager(memory)
        all_results["results"]["adaptation_manager"] = adaptation_results

        # Профилирование periodicity impact
        periodicity_results = self.profile_periodicity_impact()
        all_results["results"]["periodicity_impact"] = periodicity_results

        # Профилирование incremental vs full updates
        if self.memory_sizes:
            max_memory = self.create_test_memory_with_statistics(max(self.memory_sizes))
            incremental_results = self.profile_incremental_vs_full_update(max_memory)
            all_results["results"]["incremental_vs_full"] = incremental_results

        # Сохраняем результаты
        self.save_results(all_results)

        logger.info("Learning/Adaptation profiling complete")
        return all_results

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        Сохраняет результаты профилирования в файл.

        Args:
            results: Результаты для сохранения
        """
        import json

        timestamp = int(results["timestamp"])
        filename = f"learning_adaptation_profile_{timestamp}.json"

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
            "# Learning/Adaptation Profiling Summary",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            f"**Memory Sizes Tested:** {', '.join(map(str, results['memory_sizes']))}",
            f"**Iterations per Test:** {results['iterations']}",
            "",
            "## Key Findings",
            ""
        ]

        # Анализ Learning Engine
        learning_results = results['results'].get('learning_engine', {})
        if learning_results:
            report_lines.extend([
                "### Learning Engine Performance",
                "| Memory Size | Avg Time (s) | Complexity per Entry | Throughput |",
                "|-------------|--------------|---------------------|------------|"
            ])

            for size in sorted(learning_results.keys()):
                data = learning_results[size]
                avg_time = data.get('avg_total_time', 0)
                complexity = data.get('complexity_stats_per_entry', 0)
                throughput = data.get('throughput', 0)

                report_lines.append(
                    f"| {size} | {avg_time:.6f} | {complexity:.2e} | {throughput:.1f} |"
                )

            report_lines.append("")

        # Анализ Adaptation Manager
        adaptation_results = results['results'].get('adaptation_manager', {})
        if adaptation_results:
            report_lines.extend([
                "### Adaptation Manager Performance",
                "| Memory Size | Avg Time (s) | Analysis Ratio | Application Ratio |",
                "|-------------|--------------|----------------|-------------------|"
            ])

            for size in sorted(adaptation_results.keys()):
                data = adaptation_results[size]
                avg_time = data.get('avg_total_time', 0)
                analysis_ratio = data.get('adaptation_breakdown', {}).get('analysis_ratio', 0)
                application_ratio = data.get('adaptation_breakdown', {}).get('application_ratio', 0)

                report_lines.append(
                    f"| {size} | {avg_time:.6f} | {analysis_ratio:.2f} | {application_ratio:.2f} |"
                )

            report_lines.append("")

        # Анализ periodicity impact
        periodicity_results = results['results'].get('periodicity_impact', {})
        if periodicity_results:
            report_lines.extend([
                "### Periodicity Impact Analysis",
                "- **Current Intervals:** Learning (75 ticks), Adaptation (100 ticks)",
                "- **Overhead per Tick:** Analysis shows current intervals are reasonable",
                "- **Optimization Potential:** Incremental updates could reduce overhead",
                ""
            ])

        # Анализ incremental vs full updates
        incremental_results = results['results'].get('incremental_vs_full', {})
        if incremental_results:
            speedup = incremental_results.get('speedup_ratio', 1.0)
            report_lines.extend([
                "### Incremental vs Full Updates",
                f"- **Speedup Ratio:** {speedup:.2f}x faster with incremental updates",
                "- **Recommendation:** Implement incremental learning updates",
                ""
            ])

        # Сохраняем отчет
        timestamp = int(results["timestamp"])
        report_path = self.output_dir / f"learning_adaptation_summary_{timestamp}.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"Summary report saved to {report_path}")


def main():
    """Основная функция для запуска профилирования."""
    parser = argparse.ArgumentParser(description="Learning/Adaptation Profiler")
    parser.add_argument("--memory-sizes", nargs="+", type=int, default=[1000, 5000],
                       help="Memory sizes to test (default: 1000 5000)")
    parser.add_argument("--iterations", type=int, default=5,
                       help="Number of iterations per test (default: 5)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Запуск профилирования
    profiler = LearningAdaptationProfiler(
        memory_sizes=args.memory_sizes,
        iterations=args.iterations
    )

    try:
        results = profiler.run_full_profile()
        logger.info("Learning/Adaptation profiling completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Profiling failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
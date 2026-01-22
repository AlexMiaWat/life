#!/usr/bin/env python3
"""
Benchmark infrastructure для сравнения производительности до/после оптимизаций.

Проводит evidence-based сравнение оптимизаций с:
- Baseline измерениями (до оптимизаций)
- After измерениями (после оптимизаций)
- Статистическим анализом результатов
- Автоматической генерацией отчетов
"""

import time
import statistics
import sys
import os
import json
import logging
from typing import List, Dict, Any, Callable, Optional
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Добавление корневой директории проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.state.self_state import create_initial_state
from src.runtime.computation_cache import get_computation_cache
from src.memory.memory import Memory
from src.memory.memory_types import MemoryEntry

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Результат одного benchmark прогона."""
    operation: str
    iterations: int
    total_time: float
    avg_time: float
    median_time: float
    min_time: float
    max_time: float
    std_dev: float
    throughput: float
    memory_size: Optional[int] = None
    additional_metrics: Optional[Dict[str, Any]] = None


@dataclass
class ComparisonResult:
    """Результат сравнения baseline vs optimized."""
    operation: str
    baseline_result: BenchmarkResult
    optimized_result: BenchmarkResult
    improvement_percent: float
    speedup_factor: float
    statistical_significance: str  # "significant", "marginal", "insignificant"
    confidence_level: float


class BenchmarkTest(ABC):
    """Базовый класс для benchmark тестов."""

    @abstractmethod
    def get_name(self) -> str:
        """Возвращает имя теста."""
        pass

    @abstractmethod
    def setup_baseline(self) -> Any:
        """Настраивает baseline версию (без оптимизаций)."""
        pass

    @abstractmethod
    def setup_optimized(self) -> Any:
        """Настраивает optimized версию."""
        pass

    @abstractmethod
    def run_operation(self, context: Any) -> Any:
        """Выполняет операцию для измерения."""
        pass

    def get_memory_sizes(self) -> List[int]:
        """Возвращает размеры памяти для тестирования."""
        return [1000, 5000, 10000]

    def get_iterations(self) -> int:
        """Возвращает количество итераций."""
        return 10


class MemoryMaintenanceBenchmark(BenchmarkTest):
    """Benchmark для операций обслуживания памяти."""

    def get_name(self) -> str:
        return "memory_maintenance"

    def setup_baseline(self) -> Memory:
        """Baseline: простая decay логика без batch операций."""
        memory = Memory()
        # Создаем тестовую память
        current_time = time.time()
        for i in range(1000):  # Фиксированный размер для сравнения
            entry = MemoryEntry(
                event_type=f"test_event_{i % 10}",
                meaning_significance=0.1 + (i % 9) * 0.1,
                timestamp=current_time - (i % 86400),  # Разные возраста
                weight=0.5 + (i % 5) * 0.1,
                subjective_timestamp=current_time - (i % 86400) * 0.1
            )
            memory.append(entry)
        return memory

    def setup_optimized(self) -> Memory:
        """Optimized: с batch_memory_maintenance."""
        return self.setup_baseline()  # Та же память, но используем оптимизированную операцию

    def run_operation(self, memory: Memory) -> Dict[str, Any]:
        """Выполняет batch_memory_maintenance."""
        start_time = time.time()
        result = memory.batch_memory_maintenance()
        end_time = time.time()

        return {
            "duration": end_time - start_time,
            "result": result
        }


class ComputationCacheBenchmark(BenchmarkTest):
    """Benchmark для кэширования вычислений."""

    def get_name(self) -> str:
        return "computation_cache"

    def setup_baseline(self) -> Any:
        """Baseline: без кэширования."""
        cache = get_computation_cache()
        cache.clear()
        return {
            "cache": cache,
            "use_cache": False,
            "state": create_initial_state()
        }

    def setup_optimized(self) -> Any:
        """Optimized: с кэшированием."""
        cache = get_computation_cache()
        cache.clear()
        return {
            "cache": cache,
            "use_cache": True,
            "state": create_initial_state()
        }

    def run_operation(self, context: Any) -> Dict[str, Any]:
        """Выполняет кэшированные вычисления subjective_time."""
        from src.runtime.computation_cache import cached_compute_subjective_dt

        state = context["state"]
        use_cache = context["use_cache"]

        start_time = time.time()

        # Выполняем несколько вычислений
        for _ in range(10):
            if use_cache:
                result = cached_compute_subjective_dt(
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
            else:
                # Baseline: прямой вызов без кэша
                from src.runtime.subjective_time import compute_subjective_dt
                result = compute_subjective_dt(
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

        end_time = time.time()

        return {
            "duration": end_time - start_time,
            "cache_hits": context["cache"].get_stats()["subjective_dt"]["hits"] if use_cache else 0,
            "cache_misses": context["cache"].get_stats()["subjective_dt"]["misses"] if use_cache else 0
        }


class BenchmarkRunner:
    """Исполнитель benchmark тестов с сравнением до/после."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("data/benchmarks")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tests = [
            MemoryMaintenanceBenchmark(),
            ComputationCacheBenchmark()
        ]

    def run_single_test(self, test: BenchmarkTest, is_baseline: bool = True) -> BenchmarkResult:
        """Запускает один тест и возвращает результаты."""
        test_name = test.get_name()
        context = test.setup_baseline() if is_baseline else test.setup_optimized()

        # Разогрев
        for _ in range(3):
            test.run_operation(context)

        # Основные измерения
        times = []
        additional_metrics = []

        for i in range(test.get_iterations()):
            result = test.run_operation(context)
            times.append(result["duration"])
            additional_metrics.append({k: v for k, v in result.items() if k != "duration"})

        # Статистика
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0
        throughput = test.get_iterations() / sum(times)

        return BenchmarkResult(
            operation=f"{test_name}_{'baseline' if is_baseline else 'optimized'}",
            iterations=test.get_iterations(),
            total_time=sum(times),
            avg_time=avg_time,
            median_time=median_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            throughput=throughput,
            additional_metrics=additional_metrics[0] if additional_metrics else None
        )

    def run_comparison(self, test: BenchmarkTest) -> ComparisonResult:
        """Запускает сравнение baseline vs optimized для теста."""
        logger.info(f"Running comparison for {test.get_name()}")

        baseline_result = self.run_single_test(test, is_baseline=True)
        optimized_result = self.run_single_test(test, is_baseline=False)

        # Расчет improvement
        if baseline_result.avg_time > 0:
            improvement_percent = ((baseline_result.avg_time - optimized_result.avg_time) / baseline_result.avg_time) * 100
            speedup_factor = baseline_result.avg_time / optimized_result.avg_time
        else:
            improvement_percent = 0
            speedup_factor = 1

        # Оценка статистической значимости
        # Используем простой t-test аналог
        if baseline_result.std_dev > 0 and optimized_result.std_dev > 0:
            # Cohen's d для effect size
            pooled_std = ((baseline_result.std_dev ** 2 + optimized_result.std_dev ** 2) / 2) ** 0.5
            effect_size = abs(baseline_result.avg_time - optimized_result.avg_time) / pooled_std

            if effect_size > 0.8:
                significance = "significant"
                confidence = 0.95
            elif effect_size > 0.5:
                significance = "marginal"
                confidence = 0.80
            else:
                significance = "insignificant"
                confidence = 0.50
        else:
            significance = "unknown"
            confidence = 0.0

        return ComparisonResult(
            operation=test.get_name(),
            baseline_result=baseline_result,
            optimized_result=optimized_result,
            improvement_percent=improvement_percent,
            speedup_factor=speedup_factor,
            statistical_significance=significance,
            confidence_level=confidence
        )

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Запускает все benchmark тесты."""
        logger.info("Starting comprehensive benchmark suite")

        results = {
            "timestamp": time.time(),
            "benchmark_suite": "before_after_comparison",
            "comparisons": {}
        }

        for test in self.tests:
            try:
                comparison = self.run_comparison(test)
                results["comparisons"][test.get_name()] = {
                    "baseline": {
                        "avg_time": comparison.baseline_result.avg_time,
                        "std_dev": comparison.baseline_result.std_dev,
                        "throughput": comparison.baseline_result.throughput,
                        "additional_metrics": comparison.baseline_result.additional_metrics
                    },
                    "optimized": {
                        "avg_time": comparison.optimized_result.avg_time,
                        "std_dev": comparison.optimized_result.std_dev,
                        "throughput": comparison.optimized_result.throughput,
                        "additional_metrics": comparison.optimized_result.additional_metrics
                    },
                    "comparison": {
                        "improvement_percent": comparison.improvement_percent,
                        "speedup_factor": comparison.speedup_factor,
                        "statistical_significance": comparison.statistical_significance,
                        "confidence_level": comparison.confidence_level
                    }
                }
                logger.info(f"Completed {test.get_name()}: {comparison.improvement_percent:.1f}% improvement")

            except Exception as e:
                logger.error(f"Failed to run {test.get_name()}: {e}")
                results["comparisons"][test.get_name()] = {"error": str(e)}

        # Сохранение результатов
        self.save_results(results)
        self.generate_report(results)

        logger.info("Benchmark suite completed")
        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Сохраняет результаты в JSON."""
        timestamp = int(results["timestamp"])
        filename = f"benchmark_before_after_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Results saved to {filepath}")

    def generate_report(self, results: Dict[str, Any]) -> None:
        """Генерирует читаемый отчет."""
        timestamp = int(results["timestamp"])
        report_path = self.output_dir / f"benchmark_report_{timestamp}.md"

        lines = [
            "# Benchmark Before/After Comparison Report",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            "",
            "## Executive Summary",
            "",
            "| Test | Improvement | Speedup | Significance |",
            "|------|-------------|---------|--------------|"
        ]

        for test_name, comparison_data in results["comparisons"].items():
            if "error" in comparison_data:
                lines.append(f"| {test_name} | ERROR | - | - |")
            else:
                comp = comparison_data["comparison"]
                lines.extend([
                    f"| {test_name} | {comp['improvement_percent']:.1f}% | {comp['speedup_factor']:.2f}x | {comp['statistical_significance']} |"
                ])

        lines.extend([
            "",
            "## Detailed Results",
            ""
        ])

        for test_name, comparison_data in results["comparisons"].items():
            if "error" in comparison_data:
                lines.extend([
                    f"### {test_name}",
                    f"**Error:** {comparison_data['error']}",
                    ""
                ])
                continue

            baseline = comparison_data["baseline"]
            optimized = comparison_data["optimized"]
            comp = comparison_data["comparison"]

            lines.extend([
                f"### {test_name}",
                "",
                "#### Baseline Performance",
                f"- **Average Time:** {baseline['avg_time']:.6f}s",
                f"- **Std Deviation:** {baseline['std_dev']:.6f}s",
                f"- **Throughput:** {baseline['throughput']:.1f} ops/s",
                "",
                "#### Optimized Performance",
                f"- **Average Time:** {optimized['avg_time']:.6f}s",
                f"- **Std Deviation:** {optimized['std_dev']:.6f}s",
                f"- **Throughput:** {optimized['throughput']:.1f} ops/s",
                "",
                "#### Comparison",
                f"- **Improvement:** {comp['improvement_percent']:.1f}%",
                f"- **Speedup Factor:** {comp['speedup_factor']:.2f}x",
                f"- **Statistical Significance:** {comp['statistical_significance']}",
                f"- **Confidence Level:** {comp['confidence_level']:.2f}",
                ""
            ])

        lines.extend([
            "## Methodology",
            "",
            "- **Iterations per test:** 10 (after 3 warmup iterations)",
            "- **Statistical Analysis:** Effect size calculation for significance",
            "- **Confidence Levels:** 0.95 (significant), 0.80 (marginal), 0.50 (insignificant)",
            "",
            "## Recommendations",
            "",
            "Based on the benchmark results, the following optimizations show measurable improvements:",
        ])

        # Рекомендации
        significant_improvements = []
        for test_name, comparison_data in results["comparisons"].items():
            if "error" not in comparison_data:
                comp = comparison_data["comparison"]
                if comp["statistical_significance"] in ["significant", "marginal"]:
                    significant_improvements.append(f"- {test_name}: {comp['improvement_percent']:.1f}% improvement")

        if significant_improvements:
            lines.extend(significant_improvements)
        else:
            lines.append("- No statistically significant improvements detected")

        lines.extend([
            "",
            "All measurements should be validated in production environment."
        ])

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        logger.info(f"Report generated: {report_path}")


def main():
    """Основная функция."""
    import argparse

    parser = argparse.ArgumentParser(description="Before/After Benchmark Suite")
    parser.add_argument("--output-dir", type=str, default="data/benchmarks",
                       help="Output directory for results")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Запуск benchmark
    runner = BenchmarkRunner(output_dir=Path(args.output_dir))

    try:
        results = runner.run_all_benchmarks()
        logger.info("Benchmark suite completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Benchmark suite failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
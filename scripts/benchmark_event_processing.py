#!/usr/bin/env python3
"""
Benchmark script for event processing optimization.

Tests different batch sizes and measures performance metrics:
- Processing time per event
- Total throughput
- CPU and memory usage
- Latency distribution
"""

import time
import logging
import statistics
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Импорты из проекта
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.environment.event import Event
from src.meaning.engine import MeaningEngine
from src.state.self_state import SelfState
from src.runtime.adaptive_batch_sizer import AdaptiveBatchSizer


@dataclass
class BenchmarkResult:
    """Результаты бенчмарка для одного размера батча."""
    batch_size: int
    total_events: int
    total_time: float
    avg_time_per_event: float
    throughput_events_per_sec: float
    cpu_usage_percent: float
    memory_usage_mb: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    significant_events_ratio: float


class EventProcessingBenchmark:
    """Класс для проведения бенчмарков обработки событий."""

    def __init__(self):
        self.meaning_engine = MeaningEngine()
        self.results: List[BenchmarkResult] = []

    def generate_test_events(self, count: int, complexity: str = "mixed") -> List[Event]:
        """
        Генерирует тестовые события для бенчмарка.

        Args:
            count: Количество событий
            complexity: Тип сложности ("simple", "mixed", "complex")

        Returns:
            List[Event]: Список тестовых событий
        """
        events = []

        for i in range(count):
            if complexity == "simple":
                # Простые события низкой интенсивности
                intensity = 0.1 + (i % 10) * 0.05  # 0.1 - 0.55
                event_type = "noise"
            elif complexity == "complex":
                # Сложные события высокой интенсивности
                intensity = 0.7 + (i % 5) * 0.05  # 0.7 - 0.9
                event_type = ["shock", "recovery", "learning"][i % 3]
            else:  # mixed
                # Смешанная сложность
                intensity = 0.2 + (i % 20) * 0.04  # 0.2 - 0.96
                event_types = ["noise", "decay", "recovery", "shock", "idle", "learning"]
                event_type = event_types[i % len(event_types)]

            event = Event(
                type=event_type,
                intensity=min(1.0, intensity),
                timestamp=time.time(),
                metadata={"benchmark_id": i, "complexity": complexity}
            )
            events.append(event)

        logger.info(f"Generated {count} test events with {complexity} complexity")
        return events

    def create_test_state(self) -> SelfState:
        """Создает тестовое состояние системы для бенчмарка."""
        state = SelfState()
        # Инициализируем базовые параметры
        state.energy = 80.0
        state.stability = 70.0
        state.integrity = 90.0
        state.ticks = 1000  # Имитируем работу системы

        # Создаем базовую память
        from memory.memory import MemoryEntry
        for i in range(50):  # 50 записей памяти
            entry = MemoryEntry(
                event_type="benchmark_init",
                meaning_significance=0.3,
                timestamp=time.time() - i * 10,
                subjective_timestamp=state.subjective_time - i * 0.1
            )
            state.memory.append(entry)

        return state

    def benchmark_batch_size(self,
                           batch_size: int,
                           events: List[Event],
                           state: SelfState,
                           runs: int = 5) -> BenchmarkResult:
        """
        Проводит бенчмарк для конкретного размера батча.

        Args:
            batch_size: Размер батча для тестирования
            events: Список событий для обработки
            state: Состояние системы
            runs: Количество прогонов для усреднения

        Returns:
            BenchmarkResult: Результаты бенчмарка
        """
        logger.info(f"Running benchmark for batch_size={batch_size}, runs={runs}")

        all_latencies = []
        all_processing_times = []
        total_significant_events = 0

        # Измеряем использование ресурсов до начала
        cpu_before = psutil.cpu_percent(interval=0.1)
        memory_before = psutil.virtual_memory().used / (1024 * 1024)  # MB

        for run in range(runs):
            # Создаем копию состояния для каждого прогона
            test_state = SelfState()
            test_state.__dict__.update(state.__dict__.copy())
            test_state.memory = state.memory.copy()

            # Обрабатываем события батчами
            total_time = 0.0
            significant_events = 0
            batch_latencies = []

            for i in range(0, len(events), batch_size):
                batch = events[i:i + batch_size]

                batch_start = time.perf_counter()

                # Обрабатываем батч
                for event in batch:
                    try:
                        meaning = self.meaning_engine.process(
                            event,
                            test_state.get_safe_status_dict(include_optional=False)
                        )

                        if meaning.significance > 0:
                            significant_events += 1

                            # Имитируем активацию памяти
                            activated = []
                            for memory_entry in test_state.memory[:10]:  # Проверяем только первые 10
                                if memory_entry.event_type == event.type:
                                    activated.append(memory_entry)

                            test_state.activated_memory = activated

                    except Exception as e:
                        logger.warning(f"Error processing event in batch: {e}")
                        continue

                batch_time = time.perf_counter() - batch_start
                total_time += batch_time
                batch_latencies.append(batch_time / len(batch))  # latency per event

            all_latencies.extend(batch_latencies)
            all_processing_times.append(total_time)
            total_significant_events += significant_events

        # Вычисляем финальные метрики
        avg_time_per_event = statistics.mean(all_latencies) if all_latencies else 0.0
        total_events = len(events) * runs
        total_processing_time = sum(all_processing_times)

        # Измеряем использование ресурсов после
        cpu_after = psutil.cpu_percent(interval=0.1)
        memory_after = psutil.virtual_memory().used / (1024 * 1024)  # MB

        cpu_usage = (cpu_before + cpu_after) / 2.0
        memory_usage = max(memory_before, memory_after)

        # Вычисляем перцентили latency
        if all_latencies:
            sorted_latencies = sorted(all_latencies)
            p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        else:
            p50 = p95 = p99 = 0.0

        result = BenchmarkResult(
            batch_size=batch_size,
            total_events=total_events,
            total_time=total_processing_time,
            avg_time_per_event=avg_time_per_event,
            throughput_events_per_sec=total_events / total_processing_time if total_processing_time > 0 else 0.0,
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage,
            latency_p50=p50,
            latency_p95=p95,
            latency_p99=p99,
            significant_events_ratio=total_significant_events / total_events if total_events > 0 else 0.0
        )

        logger.info(f"Benchmark result for batch_size={batch_size}: "
                   f"throughput={result.throughput_events_per_sec:.1f} events/sec, "
                   f"avg_latency={result.avg_time_per_event*1000:.2f}ms")

        return result

    def run_full_benchmark(self,
                          event_counts: List[int] = [100, 250, 500, 1000],
                          batch_sizes: List[int] = [5, 10, 25, 50, 75, 100],
                          complexity_levels: List[str] = ["simple", "mixed", "complex"],
                          runs_per_test: int = 3) -> Dict[str, List[BenchmarkResult]]:
        """
        Запускает полный бенчмарк с различными конфигурациями.

        Args:
            event_counts: Список количеств событий для тестирования
            batch_sizes: Список размеров батчей для тестирования
            complexity_levels: Уровни сложности событий
            runs_per_test: Количество прогонов на тест

        Returns:
            Dict с результатами по уровням сложности
        """
        results = {}

        for complexity in complexity_levels:
            logger.info(f"Starting benchmark suite for complexity: {complexity}")
            results[complexity] = []

            # Создаем состояние один раз для каждого уровня сложности
            state = self.create_test_state()

            for event_count in event_counts:
                events = self.generate_test_events(event_count, complexity)

                for batch_size in batch_sizes:
                    if batch_size > event_count:
                        continue  # Пропускаем если батч больше количества событий

                    result = self.benchmark_batch_size(batch_size, events, state, runs_per_test)
                    results[complexity].append(result)

        return results

    def plot_results(self, results: Dict[str, List[BenchmarkResult]], output_dir: str = "benchmark_results"):
        """Создает графики результатов бенчмарка."""
        if not HAS_MATPLOTLIB:
            logger.info("matplotlib not available, skipping plots")
            return

        os.makedirs(output_dir, exist_ok=True)

        # Группируем результаты по batch_size для каждого уровня сложности
        for complexity in results:
            complexity_results = results[complexity]

            # Группируем по batch_size
            batch_size_groups = {}
            for result in complexity_results:
                if result.batch_size not in batch_size_groups:
                    batch_size_groups[result.batch_size] = []
                batch_size_groups[result.batch_size].append(result)

            # Для каждого batch_size берем средние значения
            batch_sizes = []
            throughputs = []
            latencies = []
            cpu_usages = []

            for batch_size in sorted(batch_size_groups.keys()):
                batch_results = batch_size_groups[batch_size]

                avg_throughput = statistics.mean([r.throughput_events_per_sec for r in batch_results])
                avg_latency = statistics.mean([r.avg_time_per_event * 1000 for r in batch_results])  # в ms
                avg_cpu = statistics.mean([r.cpu_usage_percent for r in batch_results])

                batch_sizes.append(batch_size)
                throughputs.append(avg_throughput)
                latencies.append(avg_latency)
                cpu_usages.append(avg_cpu)

            # Создаем графики
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

            # Throughput vs Batch Size
            ax1.plot(batch_sizes, throughputs, 'bo-', linewidth=2, markersize=8)
            ax1.set_title(f'Event Processing Throughput\n({complexity} complexity)')
            ax1.set_xlabel('Batch Size')
            ax1.set_ylabel('Events per Second')
            ax1.grid(True, alpha=0.3)

            # Latency vs Batch Size
            ax2.plot(batch_sizes, latencies, 'ro-', linewidth=2, markersize=8)
            ax2.set_title(f'Average Latency per Event\n({complexity} complexity)')
            ax2.set_xlabel('Batch Size')
            ax2.set_ylabel('Latency (ms)')
            ax2.grid(True, alpha=0.3)

            # CPU Usage vs Batch Size
            ax3.plot(batch_sizes, cpu_usages, 'go-', linewidth=2, markersize=8)
            ax3.set_title(f'CPU Usage\n({complexity} complexity)')
            ax3.set_xlabel('Batch Size')
            ax3.set_ylabel('CPU Usage (%)')
            ax3.grid(True, alpha=0.3)

            # Combined: Throughput vs Latency
            ax4.scatter(latencies, throughputs, s=[bs*2 for bs in batch_sizes], alpha=0.6, c=batch_sizes, cmap='viridis')
            ax4.set_title(f'Throughput vs Latency Trade-off\n({complexity} complexity)')
            ax4.set_xlabel('Latency (ms)')
            ax4.set_ylabel('Throughput (events/sec)')
            ax4.grid(True, alpha=0.3)

            # Добавляем аннотации для оптимальных точек
            if throughputs:
                max_throughput_idx = throughputs.index(max(throughputs))
                ax4.scatter([latencies[max_throughput_idx]], [throughputs[max_throughput_idx]],
                           s=200, c='red', marker='*', label='Max Throughput')
                ax4.legend()

            plt.tight_layout()
            plt.savefig(f"{output_dir}/benchmark_{complexity}.png", dpi=150, bbox_inches='tight')
            plt.close()

            # Сохраняем числовые результаты
            with open(f"{output_dir}/results_{complexity}.txt", 'w') as f:
                f.write(f"Benchmark Results for {complexity} complexity\n")
                f.write("=" * 50 + "\n\n")

                for i, batch_size in enumerate(batch_sizes):
                    f.write(f"Batch Size: {batch_size}\n")
                    f.write(f"  Throughput: {throughputs[i]:.1f} events/sec\n")
                    f.write(f"  Latency: {latencies[i]:.2f} ms\n")
                    f.write(f"  CPU Usage: {cpu_usages[i]:.1f}%\n")
                    f.write("\n")

        logger.info(f"Benchmark plots saved to {output_dir}")

    def test_adaptive_batching(self) -> Dict[str, Any]:
        """Тестирует работу адаптивного батчинга."""
        logger.info("Testing adaptive batch sizing...")

        # Создаем тестовые данные
        state = self.create_test_state()
        events = self.generate_test_events(200, "mixed")

        # Создаем адаптивный сайзер
        adaptive_sizer = AdaptiveBatchSizer(
            min_batch_size=5,
            max_batch_size=50,
            default_batch_size=25,
            adaptation_interval=10
        )

        # Имитируем работу системы с адаптацией
        adaptation_results = []
        current_tick = 0

        for cycle in range(20):  # 20 циклов адаптации
            current_tick += 10

            # Получаем оптимальный размер батча
            batch_size = adaptive_sizer.get_optimal_batch_size(
                current_tick=current_tick,
                event_batch=events[:batch_size] if 'batch_size' in locals() else events[:25]
            )

            # Имитируем обработку батча и записываем метрики
            batch_start = time.time()
            processed = 0
            significant = 0

            for i in range(0, min(len(events), batch_size)):
                event = events[i]
                try:
                    meaning = self.meaning_engine.process(
                        event,
                        state.get_safe_status_dict(include_optional=False)
                    )
                    processed += 1
                    if meaning.significance > 0.3:
                        significant += 1
                except Exception as e:
                    continue

            processing_time = time.time() - batch_start

            # Записываем метрики
            adaptive_sizer.record_batch_performance(
                batch_size=batch_size,
                processing_time=processing_time,
                events_processed=processed,
                significant_events=significant
            )

            adaptation_results.append({
                'cycle': cycle,
                'batch_size': batch_size,
                'processing_time': processing_time,
                'events_processed': processed,
                'significant_events': significant
            })

            logger.debug(f"Cycle {cycle}: batch_size={batch_size}, time={processing_time:.4f}s")

        return {
            'adaptation_results': adaptation_results,
            'final_stats': adaptive_sizer.get_stats()
        }


def main():
    """Основная функция запуска бенчмарка."""
    logger.info("Starting Event Processing Benchmark")

    benchmark = EventProcessingBenchmark()

    # Запуск полного бенчмарка
    logger.info("Running full benchmark suite...")
    results = benchmark.run_full_benchmark(
        event_counts=[100, 250],
        batch_sizes=[5, 10, 25, 50],
        complexity_levels=["simple", "mixed"],
        runs_per_test=2  # Уменьшаем для быстрого тестирования
    )

    # Создание графиков
    benchmark.plot_results(results)

    # Тестирование адаптивного батчинга
    logger.info("Testing adaptive batch sizing...")
    adaptive_results = benchmark.test_adaptive_batching()

    # Вывод результатов адаптивного батчинга
    logger.info("Adaptive batching test results:")
    for result in adaptive_results['adaptation_results'][-5:]:  # последние 5 результатов
        logger.info(f"  Cycle {result['cycle']}: batch_size={result['batch_size']}, "
                   f"time={result['processing_time']:.4f}s")

    logger.info(f"Final adaptive stats: {adaptive_results['final_stats']}")

    # Поиск оптимального размера батча
    best_results = {}
    for complexity in results:
        complexity_results = results[complexity]
        if complexity_results:
            # Находим результат с максимальным throughput
            best_result = max(complexity_results, key=lambda r: r.throughput_events_per_sec)
            best_results[complexity] = best_result

            logger.info(f"Best batch size for {complexity} complexity: {best_result.batch_size} "
                       f"(throughput: {best_result.throughput_events_per_sec:.1f} events/sec, "
                       f"latency: {best_result.avg_time_per_event*1000:.2f}ms)")

    logger.info("Benchmark completed successfully")


if __name__ == "__main__":
    main()
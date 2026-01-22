#!/usr/bin/env python3
"""
Мониторинг производительности после упрощений системы Life.

Измеряет влияние изменений на ключевые метрики производительности.
"""

import time
import statistics
from typing import Dict, List, Any
from dataclasses import dataclass

from src.state.self_state import SelfState
from src.meaning.meaning import Meaning
from src.meaning.engine import MeaningEngine
from src.decision.decision import decide_response
from src.memory.memory import MemoryEntry


@dataclass
class PerformanceResult:
    """Результат измерения производительности."""
    operation: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float

    @property
    def throughput(self) -> float:
        """Операций в секунду."""
        return self.iterations / self.total_time if self.total_time > 0 else 0


class PerformanceMonitor:
    """Монитор производительности для упрощенной системы Life."""

    def __init__(self, iterations: int = 1000):
        self.iterations = iterations
        self.results: List[PerformanceResult] = []

    def measure_operation(self, name: str, operation_func, *args, **kwargs) -> PerformanceResult:
        """
        Измеряет время выполнения операции.

        Args:
            name: Название операции
            operation_func: Функция для измерения
            *args, **kwargs: Аргументы функции

        Returns:
            PerformanceResult с метриками
        """
        times = []

        # Прогрев
        for _ in range(min(10, self.iterations // 10)):
            operation_func(*args, **kwargs)

        # Измерение
        for _ in range(self.iterations):
            start_time = time.perf_counter()
            result = operation_func(*args, **kwargs)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        result = PerformanceResult(
            operation=name,
            iterations=self.iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev
        )

        self.results.append(result)
        return result

    def print_report(self):
        """Печатает отчет о производительности."""
        print("🚀 ПРОИЗВОДИТЕЛЬНОСТЬ ПОСЛЕ УПРОЩЕНИЙ")
        print("=" * 60)

        for result in self.results:
            print(f"\n📊 {result.operation}")
            print(f"   Итераций: {result.iterations}")
            print(f"   Общее время: {result.total_time:.4f}s")
            print(f"   Среднее время: {result.avg_time*1000:.3f}ms")
            print(f"   Мин/Макс: {result.min_time*1000:.3f}ms / {result.max_time*1000:.3f}ms")
            print(f"   Стандартное отклонение: {result.std_dev*1000:.3f}ms")
            print(f"   Пропускная способность: {result.throughput:.1f} ops/sec")

    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку результатов."""
        return {
            "total_operations": len(self.results),
            "total_iterations": sum(r.iterations for r in self.results),
            "fastest_operation": min(self.results, key=lambda r: r.avg_time).operation,
            "slowest_operation": max(self.results, key=lambda r: r.avg_time).operation,
            "results": [vars(r) for r in self.results]
        }


def create_test_scenario() -> tuple[SelfState, Meaning]:
    """Создает тестовый сценарий для измерений."""
    # SelfState
    self_state = SelfState()
    self_state.energy = 0.7
    self_state.stability = 0.8
    self_state.integrity = 0.75

    # Добавляем память
    memory_entry = MemoryEntry(
        event_type="cognitive_event",
        meaning_significance=0.6,
        weight=1.0,
        timestamp=time.time(),
        feedback_data={"type": "test"}
    )
    self_state.activated_memory = [memory_entry]

    # Meaning
    meaning = Meaning()
    meaning.primary_emotion = "curiosity"

    return self_state, meaning


def benchmark_decision_engine():
    """Бенчмарк упрощенного DecisionEngine."""
    monitor = PerformanceMonitor(iterations=1000)
    self_state, meaning = create_test_scenario()

    # Измеряем время принятия решения
    result = monitor.measure_operation(
        "Decision Response (упрощенная логика)",
        decide_response,
        self_state,
        meaning,
        enable_performance_monitoring=False
    )

    monitor.print_report()
    return monitor.get_summary()


def benchmark_serialization():
    """Бенчмарк последовательной сериализации."""
    monitor = PerformanceMonitor(iterations=100)
    self_state, _ = create_test_scenario()

    # Измеряем время сериализации
    result = monitor.measure_operation(
        "SelfState Serialization (последовательная)",
        lambda: self_state.to_dict()
    )

    monitor.print_report()
    return monitor.get_summary()


def benchmark_weakness_penalty():
    """Бенчмарк логики слабости."""
    monitor = PerformanceMonitor(iterations=1000)

    def check_weakness():
        """Проверка слабости (упрощенная логика)."""
        energy_low = 0.03 < 0.05
        integrity_low = 0.8 < 0.05
        stability_low = 0.04 < 0.05
        return energy_low or integrity_low or stability_low

    result = monitor.measure_operation(
        "Weakness Check (упрощенная логика)",
        check_weakness
    )

    monitor.print_report()
    return monitor.get_summary()


def run_full_performance_audit():
    """Запускает полный аудит производительности."""
    print("🔍 ЗАПУСК АУДИТА ПРОИЗВОДИТЕЛЬНОСТИ")
    print("Проверка влияния упрощений на ключевые операции...\n")

    results = {}

    print("\n1️⃣ Тестирование Decision Engine...")
    results["decision_engine"] = benchmark_decision_engine()

    print("\n2️⃣ Тестирование сериализации...")
    results["serialization"] = benchmark_serialization()

    print("\n3️⃣ Тестирование логики слабости...")
    results["weakness_penalty"] = benchmark_weakness_penalty()

    print("\n✅ АУДИТ ЗАВЕРШЕН")
    print("=" * 60)
    print("📈 ОСНОВНЫЕ ВЫВОДЫ:")
    print("• DecisionEngine: упрощен до базовой логики")
    print("• Сериализация: последовательная без overhead параллелизма")
    print("• Weakness logic: встроена напрямую без абстракций")
    print("• Все экспериментальные компоненты отключены по умолчанию")

    return results


if __name__ == "__main__":
    run_full_performance_audit()
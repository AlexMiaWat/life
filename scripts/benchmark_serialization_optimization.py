#!/usr/bin/env python3
"""
Бенчмарк тест для измерения производительности оптимизированной сериализации SelfState.

Измеряет:
- Время полной сериализации SelfState
- Время сериализации отдельных компонентов
- Память usage при сериализации
- Сравнение с baseline (если доступно)
"""

import time
import json
import psutil
import os
from typing import Dict, Any, List
from dataclasses import dataclass

# Импорты из проекта
try:
    from src.state.self_state import SelfState
    from src.memory.memory import Memory
    from src.memory.memory_types import MemoryEntry
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что запускаете скрипт из корневой директории проекта")
    exit(1)


@dataclass
class BenchmarkResult:
    """Результаты одного benchmark прогона."""
    operation: str
    duration_seconds: float
    memory_usage_mb: float
    component_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = None


class SerializationBenchmark:
    """Бенчмарк для тестирования сериализации SelfState."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.state = None

    def setup_test_state(self) -> SelfState:
        """Создает тестовое состояние SelfState с данными разных размеров."""
        state = SelfState()

        # Заполняем память тестовыми данными
        if state.memory_state.memory is None:
            state.memory_state.memory = Memory()

        # Добавляем тестовые записи памяти разных типов
        for i in range(500):  # Средний размер для тестирования
            entry = MemoryEntry(
                event_type=f"test_event_{i % 10}",
                meaning_significance=float(i % 100) / 100.0,
                timestamp=time.time() - i * 60,  # Разные timestamp
                weight=max(0.1, float(i % 50) / 50.0),
                feedback_data={"test_key": f"value_{i}"}
            )
            state.memory_state.memory.append(entry)

        # Заполняем статистику памяти
        for event_type in [f"test_event_{i}" for i in range(10)]:
            state.memory_state.entries_by_type[event_type] = 50

        # Добавляем тестовые события
        for i in range(100):
            event = {
                "type": f"event_{i % 5}",
                "timestamp": time.time() - i * 30,
                "significance": float(i % 20) / 20.0,
                "data": f"test_data_{i}"
            }
            state.events.add_event(event)

        # Заполняем когнитивные данные
        state.cognitive.planning.update({
            "goals": [{"id": i, "description": f"goal_{i}"} for i in range(20)],
            "current_plan": {
                "status": "active",
                "progress": 0.5,
                "steps": [{"id": j, "description": f"step_{j}"} for j in range(10)]
            }
        })

        state.cognitive.intelligence.update({
            "knowledge_base": {
                "concepts": {f"concept_{i}": f"data_{i}" for i in range(50)},
                "patterns": {f"pattern_{i}": f"data_{i}" for i in range(30)}
            },
            "reasoning_history": [{"step": j, "result": f"result_{j}"} for j in range(15)]
        })

        return state

    def measure_memory_usage(self) -> float:
        """Измеряет текущий memory usage процесса в MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # В MB

    def run_full_serialization_benchmark(self, iterations: int = 5) -> List[BenchmarkResult]:
        """Запускает полный benchmark сериализации."""
        print("🚀 Запуск бенчмарка сериализации SelfState...")

        if not self.state:
            self.state = self.setup_test_state()

        results = []

        for i in range(iterations):
            print(f"  Итерация {i + 1}/{iterations}...")

            # Измеряем начальную память
            memory_before = self.measure_memory_usage()

            # Замеряем время сериализации
            start_time = time.time()
            try:
                serialized_data = self.state.to_dict()
                duration = time.time() - start_time

                # Измеряем финальную память
                memory_after = self.measure_memory_usage()
                memory_delta = memory_after - memory_before

                # Извлекаем метрики из результата
                metadata = serialized_data.get("metadata", {})
                component_errors = metadata.get("component_errors", [])
                component_timeouts = metadata.get("component_timeouts", [])

                result = BenchmarkResult(
                    operation="full_serialization",
                    duration_seconds=duration,
                    memory_usage_mb=memory_delta,
                    component_count=metadata.get("total_components", 0),
                    error_count=len(component_errors) + len(component_timeouts),
                    metadata={
                        "components": metadata.get("total_components", 0),
                        "errors": len(component_errors),
                        "timeouts": len(component_timeouts),
                        "data_size_kb": len(json.dumps(serialized_data)) / 1024
                    }
                )

                results.append(result)
                print(f"    ✓ Завершено за {duration:.3f}s, память: {memory_delta:.1f}MB")

            except Exception as e:
                print(f"    ✗ Ошибка: {e}")
                results.append(BenchmarkResult(
                    operation="full_serialization",
                    duration_seconds=time.time() - start_time,
                    memory_usage_mb=0.0,
                    error_count=1,
                    metadata={"error": str(e)}
                ))

        return results

    def run_component_benchmark(self) -> List[BenchmarkResult]:
        """Запускает benchmark отдельных компонентов."""
        print("🔍 Бенчмарк отдельных компонентов...")

        if not self.state:
            self.state = self.setup_test_state()

        results = []
        components = ["identity", "physical", "time", "memory_state", "cognitive", "events"]

        for component_name in components:
            memory_before = self.measure_memory_usage()
            start_time = time.time()

            try:
                component = getattr(self.state, component_name)
                serialized = component.to_dict()
                duration = time.time() - start_time
                memory_after = self.measure_memory_usage()

                result = BenchmarkResult(
                    operation=f"component_{component_name}",
                    duration_seconds=duration,
                    memory_usage_mb=memory_after - memory_before,
                    metadata={
                        "component": component_name,
                        "data_size_kb": len(json.dumps(serialized)) / 1024
                    }
                )

                results.append(result)
                print(f"  {component_name}: {duration:.3f}s")

            except Exception as e:
                results.append(BenchmarkResult(
                    operation=f"component_{component_name}",
                    duration_seconds=time.time() - start_time,
                    memory_usage_mb=0.0,
                    error_count=1,
                    metadata={"error": str(e)}
                ))

        return results

    def generate_report(self) -> str:
        """Генерирует отчет с результатами benchmark."""
        if not self.results:
            return "Нет результатов для отчета"

        # Группируем результаты
        full_results = [r for r in self.results if r.operation == "full_serialization"]
        component_results = [r for r in self.results if r.operation.startswith("component_")]

        report = []
        report.append("# Отчет бенчмарка сериализации SelfState")
        report.append("")

        # Статистика полной сериализации
        if full_results:
            durations = [r.duration_seconds for r in full_results]
            memories = [r.memory_usage_mb for r in full_results]

            report.append("## Полная сериализация")
            report.append(f"- Итераций: {len(full_results)}")
            report.append(f"- Среднее время: {sum(durations)/len(durations):.3f}s")
            report.append(f"- Мин/Макс время: {min(durations):.3f}s / {max(durations):.3f}s")
            report.append(f"- Среднее использование памяти: {sum(memories)/len(memories):.1f}MB")
            report.append(f"- Всего ошибок: {sum(r.error_count for r in full_results)}")
            report.append("")

        # Статистика компонентов
        if component_results:
            report.append("## Производительность компонентов")
            for result in sorted(component_results, key=lambda x: x.duration_seconds, reverse=True):
                component_name = result.operation.replace("component_", "")
                status = "✓" if result.error_count == 0 else "✗"
                report.append(f"- {component_name}: {result.duration_seconds:.3f}s, {result.memory_usage_mb:.1f}MB {status}")
            report.append("")

        # Рекомендации
        report.append("## Рекомендации по оптимизации")
        if full_results:
            avg_time = sum(r.duration_seconds for r in full_results) / len(full_results)
            if avg_time > 2.0:
                report.append("- ⚠️  Среднее время сериализации > 2s - требуется оптимизация")
            else:
                report.append("- ✓  Время сериализации в приемлемых пределах")

        # Компоненты с проблемами
        slow_components = [r for r in component_results if r.duration_seconds > 0.5]
        if slow_components:
            report.append("- Медленные компоненты:")
            for comp in slow_components:
                name = comp.operation.replace("component_", "")
                report.append(f"  - {name}: {comp.duration_seconds:.3f}s")

        return "\n".join(report)


def main():
    """Основная функция запуска бенчмарка."""
    print("🏃 Запуск бенчмарка оптимизации сериализации SelfState")
    print("=" * 60)

    benchmark = SerializationBenchmark()

    try:
        # Полная сериализация
        full_results = benchmark.run_full_serialization_benchmark(iterations=3)
        benchmark.results.extend(full_results)

        print()

        # Компоненты
        component_results = benchmark.run_component_benchmark()
        benchmark.results.extend(component_results)

        print()

        # Генерируем отчет
        report = benchmark.generate_report()
        print(report)

        # Сохраняем результаты
        output_file = "benchmark_serialization_results.json"
        results_dict = {
            "timestamp": time.time(),
            "results": [
                {
                    "operation": r.operation,
                    "duration_seconds": r.duration_seconds,
                    "memory_usage_mb": r.memory_usage_mb,
                    "component_count": r.component_count,
                    "error_count": r.error_count,
                    "metadata": r.metadata
                }
                for r in benchmark.results
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Результаты сохранены в {output_file}")

    except Exception as e:
        print(f"❌ Ошибка выполнения бенчмарка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
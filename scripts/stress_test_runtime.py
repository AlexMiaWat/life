#!/usr/bin/env python3
"""
Stress Test Framework для runtime loop.

Нагрузочное тестирование различных сценариев:
- High Memory Load: 5k-20k записей, интенсивные decay/archive
- High Event Frequency: 50-200 событий/тик, различные типы
- Complex Learning: Накопление 1k+ learning samples
- Memory Hierarchy: Полная консолидация с 3 уровнями памяти

Использование:
    python scripts/stress_test_runtime.py [--scenarios all] [--duration 60] [--max-memory 10000]
"""

import argparse
import asyncio
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.environment.event import Event
from src.memory.memory import Memory
from src.memory.memory_types import MemoryEntry
from src.runtime.loop import run_loop
from src.state.self_state import SelfState

logger = logging.getLogger(__name__)


class StressTestFramework:
    """
    Фреймворк для стресс-тестирования runtime loop.
    """

    def __init__(
        self, scenarios: List[str] = None, duration: int = 60, max_memory: int = 10000
    ):
        """
        Инициализация стресс-тест фреймворка.

        Args:
            scenarios: Сценарии для тестирования
            duration: Длительность каждого теста в секундах
            max_memory: Максимальный размер памяти для тестов
        """
        self.scenarios = scenarios or ["high_memory", "high_events", "complex_learning"]
        self.duration = duration
        self.max_memory = max_memory
        self.results = {}

        # Создаем директорию для результатов
        self.output_dir = Path("data/stress_tests")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Stress Test Framework initialized with scenarios: {self.scenarios}"
        )

    def create_high_memory_load(self) -> tuple:
        """
        Создает сценарий с высокой нагрузкой на память.

        Returns:
            tuple: (SelfState, event_queue, stop_event)
        """
        logger.info("Creating High Memory Load scenario")

        # Создаем состояние с большой памятью
        state = SelfState()
        state.physical.energy = 0.8
        state.physical.stability = 0.7
        state.physical.integrity = 0.9
        state.time.ticks = 0
        state.time.age = 0.0
        state.time.subjective_time = time.time()
        state.time.subjective_time_base_rate = 1.0
        state.events.last_event_intensity = 0.5

        # Создаем большую память
        memory = Memory()
        current_time = time.time()

        for i in range(self.max_memory):
            # Создаем записи с разными весами и возрастами
            weight = 0.1 + (i / self.max_memory) * 0.9  # От 0.1 до 1.0
            age_seconds = (i / self.max_memory) * 7 * 24 * 3600  # От 0 до 7 дней
            timestamp = current_time - age_seconds

            entry = MemoryEntry(
                event_type=f"stress_event_{i % 10}",
                meaning_significance=0.1 + (i % 9) * 0.1,
                timestamp=timestamp,
                weight=weight,
                subjective_timestamp=timestamp - age_seconds * 0.1,
            )

            memory.append(entry)

        state.memory = memory

        # Создаем очередь событий с высокой частотой
        from queue import Queue

        event_queue = Queue(maxsize=1000)

        # Добавляем начальные события
        for i in range(100):
            event = Event(
                type="stress_event",
                intensity=0.5,
                timestamp=time.time(),
                metadata={"stress_test": True, "batch": i},
            )
            event_queue.put(event)

        stop_event = threading.Event()

        return state, event_queue, stop_event

    def create_high_event_frequency_scenario(self) -> tuple:
        """
        Создает сценарий с высокой частотой событий.

        Returns:
            tuple: (SelfState, event_queue, stop_event)
        """
        logger.info("Creating High Event Frequency scenario")

        # Создаем базовое состояние
        state = SelfState()
        state.physical.energy = 0.8
        state.physical.stability = 0.7
        state.physical.integrity = 0.9
        state.time.ticks = 0
        state.time.age = 0.0
        state.time.subjective_time = time.time()
        state.time.subjective_time_base_rate = 1.0
        state.events.last_event_intensity = 0.8  # Высокая интенсивность

        # Средний размер памяти
        memory = Memory()
        for i in range(1000):
            entry = MemoryEntry(
                event_type="normal_event",
                meaning_significance=0.3,
                timestamp=time.time() - i * 100,
                weight=0.5,
            )
            memory.append(entry)
        state.memory = memory

        # Создаем очередь с высокой частотой событий
        from queue import Queue

        event_queue = Queue(maxsize=5000)

        stop_event = threading.Event()

        # Запускаем поток для генерации событий
        def event_generator():
            event_count = 0
            while (
                not stop_event.is_set() and event_count < 10000
            ):  # Максимум 10000 событий
                try:
                    # Генерируем пачку событий
                    batch_size = 50  # 50 событий за раз
                    for i in range(batch_size):
                        event_type = ["noise", "decay", "recovery", "shock", "idle"][
                            event_count % 5
                        ]
                        intensity = 0.1 + (event_count % 9) * 0.1

                        event = Event(
                            type=event_type,
                            intensity=intensity,
                            timestamp=time.time(),
                            metadata={
                                "stress_test": True,
                                "sequence": event_count,
                                "batch_size": batch_size,
                            },
                        )

                        event_queue.put(event, timeout=0.1)
                        event_count += 1

                    time.sleep(0.05)  # 20 батчей в секунду = 1000 событий/сек

                except Exception as e:
                    logger.warning(f"Event generation error: {e}")
                    break

        generator_thread = threading.Thread(target=event_generator, daemon=True)
        generator_thread.start()

        return state, event_queue, stop_event

    def create_complex_learning_scenario(self) -> tuple:
        """
        Создает сценарий со сложным обучением.

        Returns:
            tuple: (SelfState, event_queue, stop_event)
        """
        logger.info("Creating Complex Learning scenario")

        # Создаем состояние с накопленной статистикой обучения
        state = SelfState()
        state.physical.energy = 0.6
        state.physical.stability = 0.5
        state.physical.integrity = 0.7
        state.time.ticks = 2000  # Много тиков для накопления статистики
        state.time.age = 100.0
        state.time.subjective_time = time.time()

        # Инициализируем параметры обучения с большим количеством данных
        state.learning_params = {
            "event_type_sensitivity": {
                "noise": 0.4,
                "decay": 0.5,
                "recovery": 0.6,
                "shock": 0.9,
                "idle": 0.3,
                "custom_event_1": 0.2,
                "custom_event_2": 0.7,
                "custom_event_3": 0.5,
            },
            "significance_thresholds": {
                "noise": 0.2,
                "decay": 0.25,
                "recovery": 0.3,
                "shock": 0.5,
                "idle": 0.15,
                "custom_event_1": 0.1,
                "custom_event_2": 0.4,
                "custom_event_3": 0.25,
            },
            "response_coefficients": {"dampen": 0.7, "absorb": 0.95, "ignore": 0.05},
        }

        # Большая память с разнообразными событиями
        memory = Memory()
        event_types = list(state.learning_params["event_type_sensitivity"].keys())

        for i in range(5000):
            event_type = event_types[i % len(event_types)]
            significance = (
                state.learning_params["significance_thresholds"][event_type]
                + (i % 10) * 0.05
            )

            entry = MemoryEntry(
                event_type=event_type,
                meaning_significance=significance,
                timestamp=time.time() - i * 50,  # Разные временные метки
                weight=0.3 + significance * 0.7,
            )

            memory.append(entry)

        state.memory = memory

        # Очередь событий с событиями обучения
        from queue import Queue

        event_queue = Queue(maxsize=1000)

        # Добавляем события различных типов
        for i in range(200):
            event_type = event_types[i % len(event_types)]
            event = Event(
                type=event_type,
                intensity=0.3 + (i % 7) * 0.1,
                timestamp=time.time(),
                metadata={"learning_test": True, "diverse_types": True},
            )
            event_queue.put(event)

        stop_event = threading.Event()

        return state, event_queue, stop_event

    def create_memory_hierarchy_scenario(self) -> tuple:
        """
        Создает сценарий с полной иерархией памяти.

        Returns:
            tuple: (SelfState, event_queue, stop_event)
        """
        logger.info("Creating Memory Hierarchy scenario")

        # Создаем состояние с многоуровневой памятью
        state = SelfState()
        state.physical.energy = 0.75
        state.physical.stability = 0.65
        state.physical.integrity = 0.85
        state.time.ticks = 1500
        state.time.age = 75.0
        state.time.subjective_time = time.time()

        # Средняя память
        memory = Memory()
        for i in range(2000):
            entry = MemoryEntry(
                event_type=f"hierarchy_event_{i % 5}",
                meaning_significance=0.2 + (i % 8) * 0.1,
                timestamp=time.time() - i * 30,
                weight=0.4 + (i % 6) * 0.1,
            )
            memory.append(entry)

        state.memory = memory

        # Очередь событий для консолидации
        from queue import Queue

        event_queue = Queue(maxsize=1000)

        # Добавляем события разных типов для тестирования консолидации
        for i in range(150):
            event_type = ["sensory", "episodic", "semantic"][i % 3]
            event = Event(
                type=f"{event_type}_event",
                intensity=0.4 + (i % 6) * 0.1,
                timestamp=time.time(),
                metadata={"hierarchy_test": True, "memory_level": event_type},
            )
            event_queue.put(event)

        stop_event = threading.Event()

        return state, event_queue, stop_event

    def run_stress_test_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Запускает стресс-тест для конкретного сценария.

        Args:
            scenario_name: Название сценария

        Returns:
            Dict с результатами тестирования
        """
        logger.info(f"Running stress test scenario: {scenario_name}")

        # Создаем сценарий
        if scenario_name == "high_memory":
            state, event_queue, stop_event = self.create_high_memory_load()
        elif scenario_name == "high_events":
            state, event_queue, stop_event = self.create_high_event_frequency_scenario()
        elif scenario_name == "complex_learning":
            state, event_queue, stop_event = self.create_complex_learning_scenario()
        elif scenario_name == "memory_hierarchy":
            state, event_queue, stop_event = self.create_memory_hierarchy_scenario()
        else:
            raise ValueError(f"Unknown scenario: {scenario_name}")

        # Мониторим производительность
        metrics = {
            "scenario": scenario_name,
            "start_time": time.time(),
            "initial_memory_size": len(state.memory),
            "initial_queue_size": event_queue.qsize()
            if hasattr(event_queue, "qsize")
            else 0,
            "performance_data": [],
            "error_count": 0,
            "completed_ticks": 0,
        }

        # Функция мониторинга (упрощенная версия monitor)
        def performance_monitor(state):
            current_time = time.time()
            tick_data = {
                "timestamp": current_time,
                "tick": getattr(state, "ticks", 0),
                "memory_size": len(getattr(state, "memory", [])),
                "energy": getattr(state, "energy", 0.0),
                "stability": getattr(state, "stability", 0.0),
                "integrity": getattr(state, "integrity", 0.0),
                "queue_size": event_queue.qsize()
                if hasattr(event_queue, "qsize")
                else 0,
                "cpu_usage": 0.0,  # В реальности нужно измерять
                "memory_usage_mb": 0.0,  # В реальности нужно измерять
            }
            metrics["performance_data"].append(tick_data)

        try:
            # Запускаем runtime loop с ограниченным временем
            def run_with_timeout():
                try:
                    run_loop(
                        self_state=state,
                        monitor=performance_monitor,
                        tick_interval=0.1,  # Быстрые тики для стресс-теста
                        stop_event=stop_event,
                        event_queue=event_queue,
                        disable_learning=False,
                        disable_adaptation=False,
                        enable_memory_hierarchy=(scenario_name == "memory_hierarchy"),
                    )
                except Exception as e:
                    logger.error(f"Runtime loop error in {scenario_name}: {e}")
                    metrics["error_count"] += 1

            # Запускаем в отдельном потоке с таймаутом
            test_thread = threading.Thread(target=run_with_timeout, daemon=True)
            test_thread.start()

            # Ждем завершения теста
            test_thread.join(timeout=self.duration)

            # Останавливаем тест
            stop_event.set()

            # Собираем финальные метрики
            metrics["end_time"] = time.time()
            metrics["duration"] = metrics["end_time"] - metrics["start_time"]
            metrics["final_memory_size"] = len(getattr(state, "memory", []))
            metrics["completed_ticks"] = getattr(state, "ticks", 0)

            # Анализируем производительность
            if metrics["performance_data"]:
                tick_times = [data["timestamp"] for data in metrics["performance_data"]]
                if len(tick_times) > 1:
                    time_diffs = [
                        tick_times[i] - tick_times[i - 1]
                        for i in range(1, len(tick_times))
                    ]
                    avg_tick_time = sum(time_diffs) / len(time_diffs)
                    metrics["avg_tick_time"] = avg_tick_time
                    metrics["ticks_per_second"] = (
                        1.0 / avg_tick_time if avg_tick_time > 0 else 0
                    )

                # Анализируем стабильность
                energies = [data["energy"] for data in metrics["performance_data"]]
                stabilities = [
                    data["stability"] for data in metrics["performance_data"]
                ]

                if energies:
                    metrics["energy_stability"] = len(
                        set([round(e, 2) for e in energies])
                    ) / len(energies)
                if stabilities:
                    metrics["stability_variation"] = len(
                        set([round(s, 2) for s in stabilities])
                    ) / len(stabilities)

            logger.info(
                f"Stress test {scenario_name} completed: {metrics['completed_ticks']} ticks, "
                f"{metrics['error_count']} errors"
            )

        except Exception as e:
            logger.error(f"Stress test {scenario_name} failed: {e}")
            metrics["error_count"] += 1
            metrics["error_message"] = str(e)

        return metrics

    def run_all_stress_tests(self) -> Dict[str, Any]:
        """
        Запускает все стресс-тесты.

        Returns:
            Dict с результатами всех тестов
        """
        logger.info("Starting comprehensive stress testing")

        all_results = {
            "timestamp": time.time(),
            "framework": "StressTestFramework",
            "scenarios": self.scenarios,
            "duration_per_test": self.duration,
            "max_memory": self.max_memory,
            "results": {},
        }

        for scenario in self.scenarios:
            try:
                logger.info(f"Running scenario: {scenario}")
                result = self.run_stress_test_scenario(scenario)
                all_results["results"][scenario] = result

                # Небольшая пауза между тестами
                time.sleep(2)

            except Exception as e:
                logger.error(f"Failed to run scenario {scenario}: {e}")
                all_results["results"][scenario] = {
                    "scenario": scenario,
                    "error": str(e),
                    "completed": False,
                }

        # Сохраняем результаты
        self.save_results(all_results)

        logger.info("Stress testing complete")
        return all_results

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        Сохраняет результаты стресс-тестирования.

        Args:
            results: Результаты для сохранения
        """
        import json

        timestamp = int(results["timestamp"])
        filename = f"stress_test_results_{timestamp}.json"

        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Results saved to {output_path}")

        # Генерируем отчет
        self.generate_stress_report(results)

    def generate_stress_report(self, results: Dict[str, Any]) -> None:
        """
        Генерирует отчет о стресс-тестировании.

        Args:
            results: Результаты стресс-тестов
        """
        report_lines = [
            "# Stress Test Report",
            f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
            f"**Scenarios Tested:** {', '.join(results['scenarios'])}",
            f"**Duration per Test:** {results['duration_per_test']} seconds",
            "",
            "## Test Results Summary",
            "",
        ]

        scenario_results = results.get("results", {})

        for scenario in results["scenarios"]:
            if scenario in scenario_results:
                data = scenario_results[scenario]

                report_lines.extend(
                    [
                        f"### {scenario.replace('_', ' ').title()}",
                        f"- **Completed Ticks:** {data.get('completed_ticks', 0)}",
                        f"- **Errors:** {data.get('error_count', 0)}",
                        f"- **Duration:** {data.get('duration', 0):.2f}s",
                        f"- **Avg Tick Time:** {data.get('avg_tick_time', 0):.6f}s",
                        f"- **Ticks/Second:** {data.get('ticks_per_second', 0):.2f}",
                        f"- **Memory Growth:** {data.get('final_memory_size', 0) - data.get('initial_memory_size', 0)} entries",
                        "",
                    ]
                )

        # Общий анализ
        report_lines.extend(
            [
                "## Overall Analysis",
                "",
                "### Performance Metrics",
                "- **Stability:** Measured energy and stability variations",
                "- **Scalability:** Performance under different load conditions",
                "- **Error Handling:** System behavior under stress",
                "",
                "### Recommendations",
                "- Based on test results, identify optimization opportunities",
                "- Memory management optimizations may be needed for high load scenarios",
                "- Event processing batching could be improved",
                "",
            ]
        )

        # Сохраняем отчет
        timestamp = int(results["timestamp"])
        report_path = self.output_dir / f"stress_test_report_{timestamp}.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        logger.info(f"Stress test report saved to {report_path}")


def main():
    """Основная функция для запуска стресс-тестирования."""
    parser = argparse.ArgumentParser(description="Stress Test Framework")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=["high_memory", "high_events", "complex_learning", "memory_hierarchy"],
        default=["high_memory", "high_events", "complex_learning"],
        help="Scenarios to test (default: high_memory high_events complex_learning)",
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all available scenarios"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration of each test in seconds (default: 60)",
    )
    parser.add_argument(
        "--max-memory",
        type=int,
        default=10000,
        help="Maximum memory size for tests (default: 10000)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.all:
        args.scenarios = [
            "high_memory",
            "high_events",
            "complex_learning",
            "memory_hierarchy",
        ]

    # Настройка логирования
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")

    # Запуск стресс-тестирования
    framework = StressTestFramework(
        scenarios=args.scenarios, duration=args.duration, max_memory=args.max_memory
    )

    try:
        results = framework.run_all_stress_tests()
        logger.info("Stress testing completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Stress testing failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

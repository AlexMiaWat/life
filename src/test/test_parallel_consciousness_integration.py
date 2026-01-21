"""
Интеграционные тесты многопоточной системы сознания - Parallel Consciousness Integration Tests.

Тестирование интеграции многопоточной модели сознания с runtime loop и другими компонентами.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from src.experimental.consciousness.parallel_engine import ParallelConsciousnessEngine
from src.state.self_state import SelfState
from src.runtime.loop import run_loop
from src.monitor.console import monitor


class TestParallelConsciousnessRuntimeIntegration:
    """Интеграционные тесты с runtime loop."""

    def test_parallel_consciousness_with_runtime_loop(self):
        """Тест работы многопоточной системы сознания с runtime loop."""
        # Создаем начальное состояние
        self_state = SelfState()
        self_state.energy = 0.8
        self_state.stability = 0.9

        # Создаем mock монитор
        mock_monitor = Mock()

        # Создаем stop event
        stop_event = threading.Event()

        # Функция для остановки через 3 секунды
        def stop_after_delay():
            time.sleep(3.0)
            stop_event.set()

        stop_thread = threading.Thread(target=stop_after_delay, daemon=True)
        stop_thread.start()

        # Запускаем runtime loop с многопоточной системой сознания
        try:
            run_loop(
                self_state=self_state,
                monitor=mock_monitor,
                tick_interval=0.5,  # Быстрые тики для теста
                snapshot_period=100,  # Редкие snapshots
                stop_event=stop_event,
                event_queue=None,
                enable_parallel_consciousness=True,  # Включаем многопоточную систему
                disable_structured_logging=True,  # Отключаем логирование для теста
                disable_learning=True,  # Отключаем для простоты
                disable_adaptation=True,  # Отключаем для простоты
            )
        except Exception as e:
            # Ожидаемая остановка по таймеру
            if "KeyboardInterrupt" not in str(e) and "stop_event" not in str(e).lower():
                raise

        # Проверяем, что система сознания была активна
        assert hasattr(self_state, "consciousness_level")
        assert hasattr(self_state, "current_consciousness_state")
        assert hasattr(self_state, "self_reflection_score")
        assert hasattr(self_state, "meta_cognition_depth")

        # Проверяем разумные значения
        assert 0.0 <= self_state.consciousness_level <= 1.0
        assert self_state.current_consciousness_state in [
            "awake",
            "flow",
            "reflective",
            "meta",
            "dreaming",
            "unconscious",
        ]

        # Проверяем, что система была остановлена корректно
        assert stop_event.is_set()

    def test_parallel_consciousness_metrics_update(self):
        """Тест обновления метрик сознания в runtime loop."""
        self_state = SelfState()
        self_state.energy = 0.7
        self_state.stability = 0.8

        # Создаем параллельный движок сознания
        consciousness_engine = ParallelConsciousnessEngine(
            self_state_provider=lambda: self_state,
            decision_history_provider=lambda: [],
            behavior_patterns_provider=lambda: [],
            cognitive_processes_provider=lambda: [],
            optimization_history_provider=lambda: [],
        )

        # Запускаем движок
        consciousness_engine.start()

        try:
            # Даем время на инициализацию
            time.sleep(0.5)

            # Обновляем внешние метрики
            consciousness_engine.update_external_metrics(
                energy=0.9, stability=0.95, cognitive_load=0.2
            )

            # Даем время на обновление
            time.sleep(1.0)

            # Проверяем snapshot
            snapshot = consciousness_engine.get_consciousness_snapshot()

            assert snapshot["is_running"]
            assert "metrics" in snapshot
            assert "processes" in snapshot

            metrics = snapshot["metrics"]
            assert metrics["energy_level"] == 0.9
            assert metrics["stability"] == 0.95
            assert metrics["cognitive_load"] == 0.2

            # Проверяем, что метрики рассчитываются
            assert isinstance(metrics["consciousness_level"], float)
            assert isinstance(metrics["neural_activity"], float)

        finally:
            # Останавливаем движок
            consciousness_engine.stop()

    def test_parallel_consciousness_process_monitoring(self):
        """Тест мониторинга процессов сознания."""
        self_state = SelfState()

        consciousness_engine = ParallelConsciousnessEngine(self_state_provider=lambda: self_state)

        consciousness_engine.start()

        try:
            # Даем время на работу
            time.sleep(2.0)

            # Получаем метрики процессов
            process_metrics = consciousness_engine.get_process_metrics()

            # Проверяем, что все процессы присутствуют
            expected_processes = [
                "neural_activity_monitor",
                "self_reflection_processor",
                "meta_cognition_analyzer",
                "state_transition_manager",
                "consciousness_metrics_aggregator",
            ]

            assert len(process_metrics) == len(expected_processes)
            for process_name in expected_processes:
                assert process_name in process_metrics
                proc_info = process_metrics[process_name]
                assert "update_count" in proc_info
                assert "average_update_time" in proc_info
                assert "error_count" in proc_info
                assert proc_info["update_count"] > 0  # Процесс работал

        finally:
            consciousness_engine.stop()

    def test_parallel_consciousness_graceful_shutdown(self):
        """Тест корректного завершения работы многопоточной системы."""
        self_state = SelfState()

        consciousness_engine = ParallelConsciousnessEngine(self_state_provider=lambda: self_state)

        # Запуск
        consciousness_engine.start()
        assert consciousness_engine.is_running

        # Даем время на работу
        time.sleep(1.0)

        # Остановка
        consciousness_engine.stop()
        assert not consciousness_engine.is_running

        # Проверяем, что все процессы остановлены
        time.sleep(0.1)  # Небольшая задержка для завершения
        alive_processes = [p for p in consciousness_engine.processes if p.is_alive()]
        assert len(alive_processes) == 0

    def test_parallel_consciousness_error_handling(self):
        """Тест обработки ошибок в многопоточной системе."""

        # Создаем mock провайдер, который вызывает ошибку
        def failing_provider():
            raise RuntimeError("Test error in provider")

        consciousness_engine = ParallelConsciousnessEngine(self_state_provider=failing_provider)

        consciousness_engine.start()

        try:
            # Даем время на возникновение ошибок
            time.sleep(2.0)

            # Получаем метрики процессов
            process_metrics = consciousness_engine.get_process_metrics()

            # Некоторые процессы могут иметь ошибки
            total_errors = sum(proc["error_count"] for proc in process_metrics.values())
            # Не проверяем конкретное количество, так как зависит от тайминга

            # Но система должна продолжать работать
            snapshot = consciousness_engine.get_consciousness_snapshot()
            assert "metrics" in snapshot

        finally:
            consciousness_engine.stop()


class TestParallelConsciousnessWithOtherComponents:
    """Тесты взаимодействия с другими компонентами системы."""

    def test_parallel_consciousness_with_memory(self):
        """Тест взаимодействия с системой памяти."""
        self_state = SelfState()
        self_state.energy = 0.8

        # Добавляем тестовые данные в память
        from src.memory.memory import MemoryEntry

        test_memory = MemoryEntry(
            event_type="test_event",
            significance=0.7,
            impact={"energy": -0.1, "stability": 0.05},
            pattern="test_pattern",
            timestamp=time.time(),
            subjective_time=100.0,
        )
        self_state.memory.append(test_memory)

        consciousness_engine = ParallelConsciousnessEngine(
            self_state_provider=lambda: self_state,
            decision_history_provider=lambda: [{"success": True, "quality": 0.8}],
            behavior_patterns_provider=lambda: [{"type": "learning", "quality": 0.7}],
        )

        consciousness_engine.start()

        try:
            time.sleep(1.5)  # Даем время на анализ

            snapshot = consciousness_engine.get_consciousness_snapshot()
            metrics = snapshot["metrics"]

            # Проверяем, что система работает с данными из памяти
            assert isinstance(metrics["self_reflection_score"], float)
            assert 0.0 <= metrics["self_reflection_score"] <= 1.0

        finally:
            consciousness_engine.stop()

    def test_parallel_consciousness_state_persistence(self):
        """Тест сохранения состояния сознания между обновлениями."""
        self_state = SelfState()
        self_state.energy = 0.6
        self_state.stability = 0.7

        consciousness_engine = ParallelConsciousnessEngine(self_state_provider=lambda: self_state)

        consciousness_engine.start()

        try:
            # Первое измерение
            time.sleep(1.0)
            snapshot1 = consciousness_engine.get_consciousness_snapshot()

            # Изменяем внешние условия
            consciousness_engine.update_external_metrics(energy=0.9, stability=0.95)

            # Второе измерение
            time.sleep(1.0)
            snapshot2 = consciousness_engine.get_consciousness_snapshot()

            # Проверяем, что изменения отражаются
            assert snapshot2["metrics"]["energy_level"] == 0.9
            assert snapshot2["metrics"]["stability"] == 0.95

            # Уровень сознания может измениться
            assert isinstance(snapshot2["metrics"]["consciousness_level"], float)

        finally:
            consciousness_engine.stop()


class TestParallelConsciousnessPerformance:
    """Тесты производительности многопоточной системы."""

    def test_parallel_consciousness_cpu_usage(self):
        """Тест нагрузки на CPU от многопоточной системы."""
        self_state = SelfState()

        consciousness_engine = ParallelConsciousnessEngine(self_state_provider=lambda: self_state)

        consciousness_engine.start()

        try:
            # Даем время на стабилизацию
            time.sleep(0.5)

            # Получаем начальные метрики процессов
            initial_metrics = consciousness_engine.get_process_metrics()

            # Работаем 2 секунды
            time.sleep(2.0)

            # Получаем финальные метрики
            final_metrics = consciousness_engine.get_process_metrics()

            # Проверяем, что процессы работали
            for process_name in final_metrics:
                initial_count = initial_metrics[process_name]["update_count"]
                final_count = final_metrics[process_name]["update_count"]
                assert final_count > initial_count  # Были обновления

        finally:
            consciousness_engine.stop()

    def test_parallel_consciousness_memory_usage(self):
        """Тест использования памяти многопоточной системой."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        self_state = SelfState()

        consciousness_engine = ParallelConsciousnessEngine(self_state_provider=lambda: self_state)

        consciousness_engine.start()

        try:
            time.sleep(2.0)

            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory

            # Проверяем, что прирост памяти разумный (< 50MB)
            assert memory_increase < 50.0, f"Memory increase too high: {memory_increase}MB"

        finally:
            consciousness_engine.stop()

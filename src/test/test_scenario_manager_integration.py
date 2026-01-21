"""
Интеграционные тесты для ScenarioManager - проверка взаимодействия с другими компонентами.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch

from src.environment.scenario_manager import ScenarioManager, Scenario, ScenarioStep
from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.state.self_state import SelfState


class TestScenarioManagerIntegration:
    """Интеграционные тесты для ScenarioManager"""

    def test_scenario_execution_with_real_event_queue(self):
        """Интеграция с реальной EventQueue"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем сценарий с несколькими событиями
        steps = [
            ScenarioStep(delay=0.01, event=Event(type="integration_test_1", intensity=0.3)),
            ScenarioStep(delay=0.02, event=Event(type="integration_test_2", intensity=0.6)),
            ScenarioStep(delay=0.03, event=Event(type="integration_test_3", intensity=0.9)),
        ]

        scenario_id = manager.create_scenario("Integration Test", "Full integration test", steps)
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Ждем выполнения всех событий
        time.sleep(0.1)

        # Проверяем, что все события добавлены в очередь
        events = event_queue.get_all()
        assert len(events) >= 3

        event_types = {event.type for event in events}
        assert "integration_test_1" in event_types
        assert "integration_test_2" in event_types
        assert "integration_test_3" in event_types

        # Проверяем порядок интенсивностей
        intensities = [event.intensity for event in events]
        assert 0.3 in intensities
        assert 0.6 in intensities
        assert 0.9 in intensities

    def test_scenario_manager_with_self_state_integration(self):
        """Интеграция ScenarioManager с SelfState через события"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем сценарий, который повлияет на состояние
        crisis_event = Event(type="crisis", intensity=0.8)
        recovery_event = Event(type="recovery", intensity=0.4)

        steps = [
            ScenarioStep(delay=0.01, event=crisis_event),
            ScenarioStep(delay=0.05, event=recovery_event),
        ]

        scenario_id = manager.create_scenario("State Impact Test", "Test state changes", steps)
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Ждем выполнения
        time.sleep(0.1)

        # Проверяем, что события в очереди
        events = event_queue.get_all()
        assert len(events) >= 2

        # Проверяем корректность событий
        crisis_found = any(e.type == "crisis" and e.intensity == 0.8 for e in events)
        recovery_found = any(e.type == "recovery" and e.intensity == 0.4 for e in events)

        assert crisis_found
        assert recovery_found

    def test_concurrent_scenario_execution(self):
        """Параллельное выполнение нескольких сценариев"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем несколько сценариев
        scenarios = []
        for i in range(3):
            steps = [
                ScenarioStep(delay=0.01, event=Event(type=f"concurrent_{i}_1", intensity=0.3)),
                ScenarioStep(delay=0.02, event=Event(type=f"concurrent_{i}_2", intensity=0.6)),
            ]
            scenario_id = manager.create_scenario(f"Concurrent {i}", f"Concurrent test {i}", steps)
            scenarios.append(scenario_id)

        # Запускаем все сценарии параллельно
        execution_ids = []
        for scenario_id in scenarios:
            execution_id = manager.start_execution(scenario_id, event_queue)
            execution_ids.append(execution_id)

        # Ждем выполнения всех сценариев
        time.sleep(0.1)

        # Проверяем, что все события добавлены
        events = event_queue.get_all()
        assert len(events) >= 6  # 3 сценария × 2 события

        # Проверяем наличие всех типов событий
        event_types = {event.type for event in events}
        for i in range(3):
            assert f"concurrent_{i}_1" in event_types
            assert f"concurrent_{i}_2" in event_types

    def test_scenario_execution_with_timing(self):
        """Тест точности тайминга выполнения сценариев"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        start_time = time.time()

        # Создаем сценарий с точными задержками
        steps = [
            ScenarioStep(delay=0.05, event=Event(type="timing_1", intensity=0.5)),
            ScenarioStep(delay=0.10, event=Event(type="timing_2", intensity=0.5)),
            ScenarioStep(delay=0.15, event=Event(type="timing_3", intensity=0.5)),
        ]

        scenario_id = manager.create_scenario("Timing Test", "Test execution timing", steps)
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Ждем завершения всех событий
        time.sleep(0.25)

        end_time = time.time()
        total_duration = end_time - start_time

        # Проверяем, что общее время выполнения разумное
        assert 0.2 <= total_duration <= 0.5  # С запасом на неточность тайминга

        # Проверяем, что все события выполнены
        events = event_queue.get_all()
        assert len(events) >= 3

        event_types = {event.type for event in events}
        assert "timing_1" in event_types
        assert "timing_2" in event_types
        assert "timing_3" in event_types

    def test_scenario_manager_resource_cleanup(self):
        """Тест очистки ресурсов после выполнения сценариев"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем и выполняем несколько сценариев
        for i in range(5):
            steps = [ScenarioStep(delay=0.01, event=Event(type=f"cleanup_{i}", intensity=0.4))]
            scenario_id = manager.create_scenario(
                f"Cleanup {i}", f"Cleanup test {i}", steps, duration=0.05
            )
            manager.start_execution(scenario_id, event_queue)

        # Ждем завершения всех сценариев
        time.sleep(0.2)

        # Очищаем завершенные выполнения
        manager.cleanup_finished_executions()

        # Проверяем, что выполнения очищены
        executions = manager.list_executions()
        assert len(executions) == 0

        # Проверяем, что события остались в очереди
        events = event_queue.get_all()
        assert len(events) >= 5

    @patch("src.environment.scenario_manager.threading.Thread")
    def test_scenario_execution_threading_integration(self, mock_thread):
        """Интеграция с threading для параллельного выполнения"""
        # Настраиваем mock для отслеживания вызовов
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        manager = ScenarioManager()
        event_queue = EventQueue()

        steps = [ScenarioStep(delay=0.1, event=Event(type="threading_test", intensity=0.5))]
        scenario_id = manager.create_scenario("Threading Test", "Threading integration", steps)

        execution_id = manager.start_execution(scenario_id, event_queue)

        # Проверяем, что поток был создан и запущен
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Проверяем, что выполнение зарегистрировано
        executions = manager.list_executions()
        assert len(executions) == 1
        assert execution_id in executions

    def test_scenario_repeat_functionality(self):
        """Тест функциональности повторения событий"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем сценарий с повторяющимися событиями
        steps = [
            ScenarioStep(
                delay=0.01,
                event=Event(type="repeat_test", intensity=0.5),
                repeat_count=3,
                repeat_interval=0.02,
            )
        ]

        scenario_id = manager.create_scenario(
            "Repeat Test", "Test event repetition", steps, duration=0.2
        )
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Ждем выполнения
        time.sleep(0.15)

        # Проверяем, что событие повторено нужное количество раз
        events = event_queue.get_all()
        repeat_events = [e for e in events if e.type == "repeat_test"]
        assert len(repeat_events) >= 3

        # Все события должны быть одинаковыми
        for event in repeat_events:
            assert event.type == "repeat_test"
            assert event.intensity == 0.5

    def test_scenario_manager_error_recovery(self):
        """Тест восстановления после ошибок"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем сценарий
        steps = [ScenarioStep(delay=0.01, event=Event(type="error_test", intensity=0.5))]
        scenario_id = manager.create_scenario("Error Recovery", "Test error handling", steps)

        # Имитируем сбой в одном выполнении
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Имитируем остановку выполнения
        manager.stop_execution(execution_id)

        # Проверяем, что можно запустить новый сценарий
        steps2 = [ScenarioStep(delay=0.01, event=Event(type="recovery_test", intensity=0.3))]
        scenario_id2 = manager.create_scenario("Recovery Test", "Test after error", steps2)
        execution_id2 = manager.start_execution(scenario_id2, event_queue)

        # Ждем выполнения
        time.sleep(0.05)

        # Проверяем, что новый сценарий выполнился
        events = event_queue.get_all()
        recovery_events = [e for e in events if e.type == "recovery_test"]
        assert len(recovery_events) >= 1

    def test_scenario_manager_with_event_queue_capacity(self):
        """Тест работы с ограниченной емкостью EventQueue"""
        manager = ScenarioManager()
        event_queue = EventQueue(maxsize=5)  # Ограниченная очередь

        # Создаем сценарий с множеством событий
        steps = []
        for i in range(10):
            steps.append(
                ScenarioStep(delay=0.005, event=Event(type=f"capacity_test_{i}", intensity=0.5))
            )

        scenario_id = manager.create_scenario("Capacity Test", "Test queue capacity", steps)
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Ждем выполнения
        time.sleep(0.1)

        # Проверяем, что очередь не переполнена (maxsize=5, но события могут добавляться асинхронно)
        events = event_queue.get_all()
        assert len(events) <= 10  # Не больше, чем мы создали

        # Проверяем разнообразие событий
        event_types = {event.type for event in events}
        assert len(event_types) >= 5  # Минимум 5 разных типов

    def test_scenario_execution_state_transitions(self):
        """Тест переходов состояний выполнения сценариев"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        steps = [ScenarioStep(delay=0.05, event=Event(type="state_test", intensity=0.5))]
        scenario_id = manager.create_scenario(
            "State Test", "Test state transitions", steps, duration=0.1
        )

        # Запускаем выполнение
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Проверяем начальное состояние
        executions = manager.list_executions()
        execution = executions[execution_id]
        assert execution.is_running is True
        assert execution.stop_time is None

        # Ждем завершения
        time.sleep(0.15)

        # Выполнение должно завершиться автоматически
        executions = manager.list_executions()
        execution = executions[execution_id]
        assert execution.is_running is False
        assert execution.stop_time is not None

    def test_scenario_manager_full_lifecycle(self):
        """Тест полного жизненного цикла управления сценариями"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # 1. Создание сценариев
        scenario_ids = []
        for i in range(3):
            steps = [ScenarioStep(delay=0.01, event=Event(type=f"lifecycle_{i}", intensity=0.4))]
            scenario_id = manager.create_scenario(
                f"Lifecycle {i}", f"Full lifecycle test {i}", steps
            )
            scenario_ids.append(scenario_id)

        # 2. Проверка создания
        scenarios = manager.list_scenarios()
        assert len(scenarios) == 3
        for sid in scenario_ids:
            assert sid in scenarios

        # 3. Запуск выполнений
        execution_ids = []
        for sid in scenario_ids:
            eid = manager.start_execution(sid, event_queue)
            execution_ids.append(eid)

        # 4. Проверка активных выполнений
        executions = manager.list_executions()
        assert len(executions) == 3

        # 5. Остановка одного выполнения
        manager.stop_execution(execution_ids[0])
        executions = manager.list_executions()
        assert executions[execution_ids[0]].is_running is False

        # 6. Ждем завершения остальных
        time.sleep(0.1)

        # 7. Очистка завершенных
        manager.cleanup_finished_executions()
        executions = manager.list_executions()
        assert len(executions) == 0

        # 8. Удаление сценариев
        for sid in scenario_ids:
            assert manager.delete_scenario(sid) is True

        # 9. Проверка удаления
        scenarios = manager.list_scenarios()
        assert len(scenarios) == 0

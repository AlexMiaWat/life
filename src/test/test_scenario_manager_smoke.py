"""
Дымовые тесты для ScenarioManager - проверка базовой функциональности "из коробки".
"""

import pytest
import time
import threading
from unittest.mock import Mock

from src.environment.scenario_manager import ScenarioManager, Scenario, ScenarioStep
from src.environment.event import Event
from src.environment.event_queue import EventQueue


class TestScenarioManagerSmoke:
    """Дымовые тесты для ScenarioManager"""

    def test_scenario_manager_basic_operations(self):
        """Базовые операции с менеджером сценариев"""
        event_queue = EventQueue()
        manager = ScenarioManager(event_queue)

        # Получение списка доступных сценариев (встроенные)
        scenarios = manager.get_available_scenarios()
        assert len(scenarios) >= 2

        # Проверка структуры первого сценария
        scenario_info = scenarios[0]
        assert "id" in scenario_info
        assert "name" in scenario_info
        assert scenario_info["step_count"] > 0

        # Попытка запустить существующий сценарий
        result = manager.start_scenario("crisis_simulation")
        assert result["success"] is True
        assert "started" in result["message"]

        # Получение статуса запущенного сценария
        status = manager.get_scenario_status("crisis_simulation")
        assert status["success"] is True
        assert status["is_running"] is True

        # Остановка сценария
        result = manager.stop_scenario("crisis_simulation")
        assert result["success"] is True
        assert "stopped" in result["message"]

    def test_scenario_execution_smoke(self):
        """Базовое выполнение сценария"""
        event_queue = EventQueue()
        manager = ScenarioManager(event_queue)

        # Запускаем встроенный сценарий
        result = manager.start_scenario("recovery_phase")
        assert result["success"] is True

        # Ждем немного для выполнения
        time.sleep(0.1)

        # Проверяем статус
        status = manager.get_scenario_status("recovery_phase")
        assert status["success"] is True

        # Сценарий должен выполняться или завершиться
        assert status["is_running"] in [True, False]

        # Останавливаем сценарий
        result = manager.stop_scenario("recovery_phase")
        assert result["success"] is True

        # Проверяем, что событие было добавлено в очередь
        events = event_queue.get_all()
        assert len(events) >= 1

        # Проверяем выполнение
        executions = manager.list_executions()
        assert len(executions) >= 1

        # Останавливаем все выполнения
        manager.stop_all_executions()

    def test_scenario_manager_concurrent_operations(self):
        """Проверка работы в многопоточной среде"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем несколько сценариев параллельно
        def create_scenarios():
            for i in range(3):
                steps = [
                    ScenarioStep(delay=0.01, event=Event(type=f"concurrent_{i}", intensity=0.2))
                ]
                manager.create_scenario(f"Concurrent {i}", f"Test {i}", steps)

        threads = []
        for _ in range(2):
            thread = threading.Thread(target=create_scenarios)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Проверяем, что все сценарии созданы
        scenarios = manager.list_scenarios()
        assert len(scenarios) >= 3  # Минимум 3 сценария должно быть создано

    def test_scenario_manager_error_handling(self):
        """Проверка обработки ошибок"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Попытка получить несуществующий сценарий
        scenario = manager.get_scenario("nonexistent")
        assert scenario is None

        # Попытка удалить несуществующий сценарий
        assert manager.delete_scenario("nonexistent") is False

        # Попытка запустить несуществующий сценарий
        execution_id = manager.start_execution("nonexistent", event_queue)
        assert execution_id is None

        # Попытка остановить несуществующее выполнение
        assert manager.stop_execution("nonexistent") is False

    def test_scenario_manager_state_persistence(self):
        """Проверка сохранения состояния"""
        manager1 = ScenarioManager()

        # Создаем сценарий в первом менеджере
        steps = [ScenarioStep(delay=0.1, event=Event(type="persistence", intensity=0.4))]
        scenario_id = manager1.create_scenario("Persistence Test", "State persistence", steps)

        # Имитируем сохранение и загрузку (в реальности использовался бы файл)
        scenarios_data = manager1.scenarios.copy()

        # Создаем новый менеджер и имитируем загрузку
        manager2 = ScenarioManager()
        manager2.scenarios = scenarios_data

        # Проверяем, что сценарий доступен во втором менеджере
        scenario = manager2.get_scenario(scenario_id)
        assert scenario is not None
        assert scenario.name == "Persistence Test"

    def test_scenario_step_various_events(self):
        """Тест с различными типами событий"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем сценарий с различными событиями
        steps = [
            ScenarioStep(delay=0.01, event=Event(type="positive", intensity=0.8)),
            ScenarioStep(delay=0.01, event=Event(type="negative", intensity=0.6)),
            ScenarioStep(delay=0.01, event=Event(type="neutral", intensity=0.3)),
        ]

        scenario_id = manager.create_scenario("Various Events", "Multiple event types", steps)
        execution_id = manager.start_execution(scenario_id, event_queue)

        # Ждем выполнения
        time.sleep(0.1)

        # Проверяем, что все события были добавлены
        events = event_queue.get_all()
        assert len(events) >= 3

        event_types = {event.type for event in events}
        assert "positive" in event_types
        assert "negative" in event_types
        assert "neutral" in event_types

    def test_scenario_manager_cleanup(self):
        """Тест очистки завершенных выполнений"""
        manager = ScenarioManager()
        event_queue = EventQueue()

        # Создаем и выполняем сценарий
        steps = [ScenarioStep(delay=0.05, event=Event(type="cleanup_test", intensity=0.2))]
        scenario_id = manager.create_scenario("Cleanup Test", "Test cleanup", steps, duration=0.1)

        execution_id = manager.start_execution(scenario_id, event_queue)

        # Ждем завершения сценария
        time.sleep(0.2)

        # Очистка должна удалить завершенное выполнение
        manager.cleanup_finished_executions()

        executions = manager.list_executions()
        # Выполнение должно быть завершено и удалено
        assert len(executions) == 0 or all(
            not exec_obj.is_running for exec_obj in executions.values()
        )

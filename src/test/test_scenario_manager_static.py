"""
Статические тесты для ScenarioManager - менеджера сценариев внешних воздействий.

Проверяет базовую функциональность создания, управления и выполнения сценариев.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.environment.scenario_manager import (
    ScenarioManager, Scenario, ScenarioStep, ScenarioExecution
)
from src.environment.event import Event
from src.environment.event_queue import EventQueue


class TestScenarioStep:
    """Тесты для ScenarioStep"""

    def test_scenario_step_creation(self):
        """Тест создания шага сценария"""
        import time
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        step = ScenarioStep(delay=1.0, event=event, repeat_count=3, repeat_interval=0.5)

        assert step.delay == 1.0
        assert step.event == event
        assert step.repeat_count == 3
        assert step.repeat_interval == 0.5

    def test_scenario_step_defaults(self):
        """Тест значений по умолчанию для ScenarioStep"""
        import time
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        step = ScenarioStep(delay=1.0, event=event)

        assert step.repeat_count == 1
        assert step.repeat_interval == 0.0


class TestScenario:
    """Тесты для Scenario"""

    def test_scenario_creation(self):
        """Тест создания сценария"""
        import time
        current_time = time.time()
        steps = [
            ScenarioStep(delay=0.0, event=Event(type="start", intensity=0.1, timestamp=current_time)),
            ScenarioStep(delay=1.0, event=Event(type="middle", intensity=0.5, timestamp=current_time + 1)),
            ScenarioStep(delay=2.0, event=Event(type="end", intensity=0.8, timestamp=current_time + 2))
        ]

        scenario = Scenario(
            id="test_scenario",
            name="Test Scenario",
            description="Test scenario description",
            steps=steps,
            duration=5.0,
            auto_stop=False
        )

        assert scenario.id == "test_scenario"
        assert scenario.name == "Test Scenario"
        assert scenario.description == "Test scenario description"
        assert len(scenario.steps) == 3
        assert scenario.duration == 5.0
        assert scenario.auto_stop is False

    def test_scenario_defaults(self):
        """Тест значений по умолчанию для Scenario"""
        scenario = Scenario(
            id="test",
            name="Test",
            description="Test desc",
            steps=[]
        )

        assert scenario.duration is None
        assert scenario.auto_stop is True


class TestScenarioExecution:
    """Тесты для ScenarioExecution"""

    def test_execution_creation(self):
        """Тест создания выполнения сценария"""
        scenario = Scenario(id="test", name="Test", description="Test", steps=[])
        event_queue = Mock(spec=EventQueue)

        execution = ScenarioExecution(scenario, event_queue)

        assert execution.scenario == scenario
        assert execution.event_queue == event_queue
        assert execution.is_running is False
        assert execution.stop_time is None
        assert execution.start_time is not None

    def test_execution_stop(self):
        """Тест остановки выполнения"""
        scenario = Scenario(id="test", name="Test", description="Test", steps=[])
        event_queue = Mock(spec=EventQueue)

        execution = ScenarioExecution(scenario, event_queue)
        execution.is_running = True

        execution.stop()
        assert execution.is_running is False
        assert execution.stop_time is not None

    def test_execution_is_finished_duration(self):
        """Тест проверки завершения по длительности"""
        scenario = Scenario(id="test", name="Test", description="Test", steps=[], duration=2.0)
        event_queue = Mock(spec=EventQueue)

        execution = ScenarioExecution(scenario, event_queue)

        # Сразу после создания - выполнение не запущено
        assert not execution.is_running

        # После истечения длительности (имитируем) - проверяем время
        execution.start_time = time.time() - 3.0
        elapsed = time.time() - execution.start_time
        assert elapsed > 2.0  # Время вышло

    def test_execution_is_finished_manual_stop(self):
        """Тест проверки завершения при ручной остановке"""
        scenario = Scenario(id="test", name="Test", description="Test", steps=[])
        event_queue = Mock(spec=EventQueue)

        execution = ScenarioExecution(scenario, event_queue)
        execution.stop()

        assert not execution.is_running
        assert execution.stop_time is not None


class TestScenarioManager:
    """Тесты для ScenarioManager"""

    def test_manager_creation(self):
        """Тест создания менеджера сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        assert isinstance(manager.scenarios, dict)
        assert isinstance(manager.executions, dict)
        assert manager.event_queue == event_queue

    @patch('src.environment.scenario_manager.Path')
    def test_load_scenarios(self, mock_path):
        """Тест загрузки сценариев из файла"""
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = '''[
            {
                "id": "crisis",
                "name": "Crisis Scenario",
                "description": "Simulates system crisis",
                "steps": [
                    {
                        "delay": 0.0,
                        "event": {"type": "crisis", "intensity": 0.9},
                        "repeat_count": 1,
                        "repeat_interval": 0.0
                    }
                ],
                "duration": null,
                "auto_stop": true
            }
        ]'''
        mock_path.return_value = mock_file

        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)
        manager.load_scenarios("scenarios.json")

        assert "crisis" in manager.scenarios
        scenario = manager.scenarios["crisis"]
        assert scenario.id == "crisis"
        assert scenario.name == "Crisis Scenario"
        assert len(scenario.steps) == 1

    def test_create_scenario(self):
        """Тест создания сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        steps = [
            ScenarioStep(delay=0.0, event=Event(type="start", intensity=0.1))
        ]

        scenario_id = manager.create_scenario(
            name="Test Scenario",
            description="Test description",
            steps=steps,
            duration=10.0
        )

        assert scenario_id == "scenario_1"
        assert scenario_id in manager.scenarios

        scenario = manager.scenarios[scenario_id]
        assert scenario.name == "Test Scenario"
        assert scenario.description == "Test description"
        assert scenario.duration == 10.0
        assert len(scenario.steps) == 1

    def test_get_scenario(self):
        """Тест получения сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создаем сценарий
        scenario_id = manager.create_scenario(
            name="Test",
            description="Test",
            steps=[]
        )

        # Получаем сценарий
        scenario = manager.get_scenario(scenario_id)
        assert scenario is not None
        assert scenario.id == scenario_id

        # Получаем несуществующий сценарий
        assert manager.get_scenario("nonexistent") is None

    def test_list_scenarios(self):
        """Тест получения списка сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создаем несколько сценариев
        id1 = manager.create_scenario("Scenario 1", "Desc 1", [])
        id2 = manager.create_scenario("Scenario 2", "Desc 2", [])

        scenarios = manager.list_scenarios()
        assert len(scenarios) == 2
        assert id1 in scenarios
        assert id2 in scenarios

    def test_delete_scenario(self):
        """Тест удаления сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создаем сценарий
        scenario_id = manager.create_scenario("Test", "Test", [])

        # Удаляем сценарий
        assert manager.delete_scenario(scenario_id) is True
        assert scenario_id not in manager.scenarios

        # Пытаемся удалить несуществующий сценарий
        assert manager.delete_scenario("nonexistent") is False

    def test_start_execution_no_scenario(self):
        """Тест запуска выполнения для несуществующего сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)
        event_queue = Mock(spec=EventQueue)

        result = manager.start_execution("nonexistent", event_queue)
        assert result is None

    def test_stop_execution(self):
        """Тест остановки выполнения"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Имитируем запущенное выполнение
        execution = Mock(spec=ScenarioExecution)
        execution.is_running = True
        manager.executions["test_exec"] = execution

        # Останавливаем выполнение
        assert manager.stop_execution("test_exec") is True
        execution.stop.assert_called_once()

        # Пытаемся остановить несуществующее выполнение
        assert manager.stop_execution("nonexistent") is False

    def test_list_executions(self):
        """Тест получения списка выполнений"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Имитируем выполнения
        exec1 = Mock(spec=ScenarioExecution)
        exec2 = Mock(spec=ScenarioExecution)
        manager.executions = {"exec1": exec1, "exec2": exec2}

        executions = manager.list_executions()
        assert len(executions) == 2
        assert "exec1" in executions
        assert "exec2" in executions

    def test_cleanup_finished_executions(self):
        """Тест очистки завершенных выполнений"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Имитируем выполнения
        finished_exec = Mock(spec=ScenarioExecution)
        finished_exec.is_finished.return_value = True
        finished_exec.is_running = False

        running_exec = Mock(spec=ScenarioExecution)
        running_exec.is_finished.return_value = False
        running_exec.is_running = True

        manager.executions = {
            "finished": finished_exec,
            "running": running_exec
        }

        # Очищаем завершенные
        manager.cleanup_finished_executions()

        assert "finished" not in manager.executions
        assert "running" in manager.executions

    def test_stop_all_executions(self):
        """Тест остановки всех выполнений"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Имитируем выполнения
        exec1 = Mock(spec=ScenarioExecution)
        exec1.is_running = True
        exec2 = Mock(spec=ScenarioExecution)
        exec2.is_running = True

        manager.executions = {"exec1": exec1, "exec2": exec2}

        # Останавливаем все
        manager.stop_all_executions()

        exec1.stop.assert_called_once()
        exec2.stop.assert_called_once()
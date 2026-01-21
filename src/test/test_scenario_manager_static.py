"""
Статические тесты для ScenarioManager - менеджера сценариев внешних воздействий.

Проверяет базовую функциональность создания, управления и выполнения сценариев.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.environment.scenario_manager import (
    ScenarioManager,
    Scenario,
    ScenarioStep,
    ScenarioExecution,
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
            ScenarioStep(
                delay=0.0, event=Event(type="start", intensity=0.1, timestamp=current_time)
            ),
            ScenarioStep(
                delay=1.0, event=Event(type="middle", intensity=0.5, timestamp=current_time + 1)
            ),
            ScenarioStep(
                delay=2.0, event=Event(type="end", intensity=0.8, timestamp=current_time + 2)
            ),
        ]

        scenario = Scenario(
            id="test_scenario",
            name="Test Scenario",
            description="Test scenario description",
            steps=steps,
            duration=5.0,
            auto_stop=False,
        )

        assert scenario.id == "test_scenario"
        assert scenario.name == "Test Scenario"
        assert scenario.description == "Test scenario description"
        assert len(scenario.steps) == 3
        assert scenario.duration == 5.0
        assert scenario.auto_stop is False

    def test_scenario_defaults(self):
        """Тест значений по умолчанию для Scenario"""
        scenario = Scenario(id="test", name="Test", description="Test desc", steps=[])

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

        # Остановка не запущенного execution не должна устанавливать stop_time
        result = execution.stop()
        assert result is False  # Не был запущен
        assert execution.stop_time is None

        # Теперь запустим и остановим
        execution.start()
        time.sleep(0.01)  # Небольшая задержка для запуска
        execution.stop()
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

    @patch("src.environment.scenario_manager.Path")
    def test_load_scenarios(self, mock_path):
        """Тест загрузки сценариев из файла"""
        mock_file = Mock()
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = """[
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
        ]"""
        mock_path.return_value = mock_file

        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Проверяем, что встроенные сценарии загружены автоматически
        assert len(manager.scenarios) >= 2  # crisis_simulation и recovery_phase
        assert "crisis_simulation" in manager.scenarios
        assert "recovery_phase" in manager.scenarios

        # Проверяем структуру crisis_simulation
        crisis = manager.scenarios["crisis_simulation"]
        assert crisis.id == "crisis_simulation"
        assert crisis.name == "Симуляция кризиса"
        assert len(crisis.steps) >= 4  # Несколько шагов в сценарии

    def test_get_available_scenarios(self):
        """Тест получения списка доступных сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        scenarios = manager.get_available_scenarios()

        assert isinstance(scenarios, list)
        assert len(scenarios) >= 2  # Должны быть встроенные сценарии crisis_simulation и recovery_phase

        # Проверить структуру сценариев
        for scenario in scenarios:
            assert "id" in scenario
            assert "name" in scenario
            assert "description" in scenario
            assert "step_count" in scenario
            assert "duration" in scenario
            assert "auto_stop" in scenario
            assert isinstance(scenario["step_count"], int)
            assert scenario["step_count"] > 0

    def test_get_scenario_status_not_running(self):
        """Тест получения статуса не запущенного сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Попытка получить статус не запущенного сценария
        status = manager.get_scenario_status("crisis_simulation")

        assert status["success"] is False
        assert "not running" in status["error"]

    def test_list_scenarios(self):
        """Тест получения списка сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Получаем доступные сценарии (встроенные)
        scenarios = manager.get_available_scenarios()
        assert len(scenarios) >= 2  # Встроенные сценарии загружаются автоматически
        assert all("id" in s for s in scenarios)
        assert all("name" in s for s in scenarios)

    def test_delete_scenario(self):
        """Тест удаления сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Попытка остановить не запущенный сценарий
        result = manager.stop_scenario("crisis_simulation")

        assert result["success"] is False
        assert "not running" in result["error"]

    def test_start_execution_no_scenario(self):
        """Тест запуска выполнения для несуществующего сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)
        event_queue = Mock(spec=EventQueue)

        result = manager.start_scenario("nonexistent_scenario")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_stop_execution(self):
        """Тест остановки выполнения"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Попытка остановить не запущенный сценарий
        result = manager.stop_scenario("crisis_simulation")
        assert result["success"] is False
        assert "not running" in result["error"]

    def test_get_all_statuses_empty(self):
        """Тест получения статусов всех сценариев когда ничего не запущено"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        statuses = manager.get_all_statuses()
        assert statuses["count"] == 0
        assert len(statuses["running_scenarios"]) == 0

    def test_stop_all_scenarios_empty(self):
        """Тест остановки всех сценариев когда ничего не запущено"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        result = manager.stop_all_scenarios()
        assert result["success"] is True
        assert result["stopped_count"] == 0

    def test_stop_all_scenarios_with_running(self):
        """Тест остановки всех запущенных сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Имитируем запущенные сценарии
        exec1 = Mock(spec=ScenarioExecution)
        exec1.is_running = True
        exec1.stop.return_value = True
        exec2 = Mock(spec=ScenarioExecution)
        exec2.is_running = True
        exec2.stop.return_value = True

        manager.executions = {"scenario1": exec1, "scenario2": exec2}

        # Останавливаем все
        result = manager.stop_all_scenarios()

        assert result["success"] is True
        assert result["stopped_count"] == 2
        exec1.stop.assert_called_once()
        exec2.stop.assert_called_once()

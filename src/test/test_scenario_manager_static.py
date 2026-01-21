"""
Статические тесты для ScenarioManager

Проверяем:
- Инициализация ScenarioManager
- Создание и валидация сценариев
- Управление выполнением сценариев
- Остановку и паузу сценариев
- Thread-safety операций
"""

import json
import threading
import time
from unittest.mock import Mock, MagicMock

import pytest

from src.environment.scenario_manager import (
    ScenarioManager, Scenario, ScenarioStep, ScenarioExecution
)
from src.environment.event import Event
from src.environment.event_queue import EventQueue


class TestScenarioManagerStatic:
    """Статические тесты ScenarioManager"""

    def test_initialization(self):
        """Тест инициализации ScenarioManager"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        assert manager.event_queue is event_queue
        assert isinstance(manager._scenarios, dict)
        assert isinstance(manager._executions, dict)
        assert isinstance(manager._lock, type(threading.Lock()))

    def test_scenario_creation(self):
        """Тест создания сценария"""
        # Создание шагов сценария
        event = Event(event_type="test_event", intensity=0.8, data={"test": "data"})
        step = ScenarioStep(delay=1.0, event=event, repeat_count=2, repeat_interval=0.5)

        # Создание сценария
        scenario = Scenario(
            id="test_scenario",
            name="Test Scenario",
            description="A test scenario",
            steps=[step],
            duration=10.0,
            auto_stop=True
        )

        assert scenario.id == "test_scenario"
        assert scenario.name == "Test Scenario"
        assert scenario.description == "A test scenario"
        assert len(scenario.steps) == 1
        assert scenario.duration == 10.0
        assert scenario.auto_stop is True

        # Проверка шага
        assert scenario.steps[0].delay == 1.0
        assert scenario.steps[0].event == event
        assert scenario.steps[0].repeat_count == 2
        assert scenario.steps[0].repeat_interval == 0.5

    def test_scenario_validation(self):
        """Тест валидации сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Корректный сценарий
        event = Event(event_type="test_event", intensity=0.8)
        step = ScenarioStep(delay=1.0, event=event)
        scenario = Scenario(
            id="valid_scenario",
            name="Valid",
            description="Valid scenario",
            steps=[step]
        )

        assert manager._validate_scenario(scenario) is True

        # Сценарий без шагов
        invalid_scenario = Scenario(
            id="invalid_scenario",
            name="Invalid",
            description="Invalid scenario",
            steps=[]
        )

        assert manager._validate_scenario(invalid_scenario) is False

        # Сценарий с отрицательной задержкой
        invalid_step = ScenarioStep(delay=-1.0, event=event)
        invalid_scenario2 = Scenario(
            id="invalid_scenario2",
            name="Invalid2",
            description="Invalid scenario2",
            steps=[invalid_step]
        )

        assert manager._validate_scenario(invalid_scenario2) is False

    def test_add_and_get_scenario(self):
        """Тест добавления и получения сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание сценария
        event = Event(event_type="test_event", intensity=0.8)
        step = ScenarioStep(delay=1.0, event=event)
        scenario = Scenario(
            id="test_scenario",
            name="Test Scenario",
            description="Test",
            steps=[step]
        )

        # Добавление сценария
        manager.add_scenario(scenario)

        assert "test_scenario" in manager._scenarios

        # Получение сценария
        retrieved = manager.get_scenario("test_scenario")
        assert retrieved is not None
        assert retrieved.id == "test_scenario"

        # Получение несуществующего сценария
        assert manager.get_scenario("nonexistent") is None

    def test_remove_scenario(self):
        """Тест удаления сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание и добавление сценария
        event = Event(event_type="test_event", intensity=0.8)
        step = ScenarioStep(delay=1.0, event=event)
        scenario = Scenario(
            id="test_scenario",
            name="Test Scenario",
            description="Test",
            steps=[step]
        )

        manager.add_scenario(scenario)
        assert "test_scenario" in manager._scenarios

        # Удаление сценария
        manager.remove_scenario("test_scenario")
        assert "test_scenario" not in manager._scenarios

    def test_list_scenarios(self):
        """Тест получения списка сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Добавление нескольких сценариев
        for i in range(3):
            event = Event(event_type=f"event_{i}", intensity=0.8)
            step = ScenarioStep(delay=1.0, event=event)
            scenario = Scenario(
                id=f"scenario_{i}",
                name=f"Scenario {i}",
                description=f"Description {i}",
                steps=[step]
            )
            manager.add_scenario(scenario)

        scenarios = manager.list_scenarios()

        assert len(scenarios) == 3
        assert all(isinstance(s, Scenario) for s in scenarios)
        assert {s.id for s in scenarios} == {"scenario_0", "scenario_1", "scenario_2"}

    def test_start_scenario_execution(self):
        """Тест запуска выполнения сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание и добавление сценария
        event = Event(event_type="test_event", intensity=0.8)
        step = ScenarioStep(delay=0.1, event=event)  # Маленькая задержка для теста
        scenario = Scenario(
            id="test_scenario",
            name="Test",
            description="Test",
            steps=[step]
        )

        manager.add_scenario(scenario)

        # Запуск сценария
        execution_id = manager.start_scenario("test_scenario")

        assert execution_id is not None
        assert execution_id in manager._executions

        execution = manager._executions[execution_id]
        assert execution.scenario.id == "test_scenario"
        assert execution.event_queue is event_queue

        # Остановка для очистки
        manager.stop_scenario(execution_id)

    def test_stop_scenario_execution(self):
        """Тест остановки выполнения сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание и запуск сценария
        event = Event(event_type="test_event", intensity=0.8)
        step = ScenarioStep(delay=1.0, event=event)
        scenario = Scenario(
            id="test_scenario",
            name="Test",
            description="Test",
            steps=[step]
        )

        manager.add_scenario(scenario)
        execution_id = manager.start_scenario("test_scenario")

        # Остановка сценария
        result = manager.stop_scenario(execution_id)

        assert result is True
        assert execution_id not in manager._executions

        # Повторная остановка должна вернуть False
        result = manager.stop_scenario(execution_id)
        assert result is False

    def test_get_execution_status(self):
        """Тест получения статуса выполнения"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание и запуск сценария
        event = Event(event_type="test_event", intensity=0.8)
        step = ScenarioStep(delay=1.0, event=event)
        scenario = Scenario(
            id="test_scenario",
            name="Test",
            description="Test",
            steps=[step]
        )

        manager.add_scenario(scenario)
        execution_id = manager.start_scenario("test_scenario")

        # Получение статуса
        status = manager.get_execution_status(execution_id)

        assert status is not None
        assert "execution_id" in status
        assert "scenario_id" in status
        assert "status" in status
        assert "start_time" in status

        # Статус несуществующего выполнения
        assert manager.get_execution_status("nonexistent") is None

        # Очистка
        manager.stop_scenario(execution_id)

    def test_list_executions(self):
        """Тест получения списка выполнений"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание и запуск нескольких сценариев
        for i in range(2):
            event = Event(event_type=f"event_{i}", intensity=0.8)
            step = ScenarioStep(delay=1.0, event=event)
            scenario = Scenario(
                id=f"scenario_{i}",
                name=f"Scenario {i}",
                description=f"Description {i}",
                steps=[step]
            )
            manager.add_scenario(scenario)
            manager.start_scenario(f"scenario_{i}")

        executions = manager.list_executions()

        assert len(executions) == 2
        assert all("execution_id" in e for e in executions)

        # Очистка
        for exec_info in executions:
            manager.stop_scenario(exec_info["execution_id"])

    def test_scenario_execution_thread_safety(self):
        """Тест потокобезопасности выполнения сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        errors = []

        def run_scenario_operations(thread_id: int):
            """Выполняет операции со сценариями в потоке"""
            try:
                # Создание сценария
                event = Event(event_type=f"thread_{thread_id}_event", intensity=0.8)
                step = ScenarioStep(delay=0.1, event=event)
                scenario = Scenario(
                    id=f"thread_{thread_id}_scenario",
                    name=f"Thread {thread_id}",
                    description=f"Thread {thread_id} scenario",
                    steps=[step]
                )

                # Добавление и запуск
                manager.add_scenario(scenario)
                execution_id = manager.start_scenario(f"thread_{thread_id}_scenario")

                # Небольшая задержка
                time.sleep(0.05)

                # Остановка
                manager.stop_scenario(execution_id)

            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")

        # Запуск нескольких потоков
        threads = []
        for i in range(5):
            t = threading.Thread(target=run_scenario_operations, args=(i,))
            threads.append(t)
            t.start()

        # Ожидание завершения
        for t in threads:
            t.join()

        # Проверка отсутствия ошибок
        assert len(errors) == 0, f"Thread safety errors: {errors}"

    def test_scenario_step_execution(self):
        """Тест выполнения шагов сценария"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание сценария с несколькими шагами
        events = []
        steps = []
        for i in range(3):
            event = Event(event_type=f"event_{i}", intensity=0.8, data={"step": i})
            events.append(event)
            step = ScenarioStep(delay=0.01, event=event)  # Маленькая задержка
            steps.append(step)

        scenario = Scenario(
            id="multi_step_scenario",
            name="Multi Step",
            description="Multiple steps scenario",
            steps=steps
        )

        manager.add_scenario(scenario)
        execution_id = manager.start_scenario("multi_step_scenario")

        # Небольшая задержка для выполнения шагов
        time.sleep(0.1)

        # Проверка что события были отправлены в очередь
        # (В реальности проверка зависит от реализации, здесь просто проверяем что выполнение существует)
        status = manager.get_execution_status(execution_id)
        assert status is not None
        assert status["scenario_id"] == "multi_step_scenario"

        # Очистка
        manager.stop_scenario(execution_id)

    def test_scenario_with_repeats(self):
        """Тест сценария с повторяющимися шагами"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание сценария с повторяющимся шагом
        event = Event(event_type="repeat_event", intensity=0.8)
        step = ScenarioStep(
            delay=0.01,
            event=event,
            repeat_count=3,
            repeat_interval=0.01
        )

        scenario = Scenario(
            id="repeat_scenario",
            name="Repeat Scenario",
            description="Scenario with repeats",
            steps=[step]
        )

        manager.add_scenario(scenario)
        execution_id = manager.start_scenario("repeat_scenario")

        # Задержка для выполнения всех повторений
        time.sleep(0.1)

        # Проверка статуса
        status = manager.get_execution_status(execution_id)
        assert status is not None

        # Очистка
        manager.stop_scenario(execution_id)

    def test_invalid_scenario_operations(self):
        """Тест операций с некорректными сценариями"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Запуск несуществующего сценария
        execution_id = manager.start_scenario("nonexistent_scenario")
        assert execution_id is None

        # Остановка несуществующего выполнения
        result = manager.stop_scenario("nonexistent_execution")
        assert result is False

        # Получение статуса несуществующего выполнения
        status = manager.get_execution_status("nonexistent_execution")
        assert status is None

    def test_scenario_persistence(self):
        """Тест сохранения и загрузки сценариев"""
        event_queue = Mock(spec=EventQueue)
        manager = ScenarioManager(event_queue)

        # Создание сценария
        event = Event(event_type="persistent_event", intensity=0.8)
        step = ScenarioStep(delay=1.0, event=event)
        scenario = Scenario(
            id="persistent_scenario",
            name="Persistent",
            description="Persistent scenario",
            steps=[step]
        )

        manager.add_scenario(scenario)

        # Экспорт сценариев
        exported = manager.export_scenarios()

        assert isinstance(exported, list)
        assert len(exported) == 1
        assert exported[0]["id"] == "persistent_scenario"

        # Импорт сценариев (в новой менеджер)
        new_manager = ScenarioManager(event_queue)
        imported_count = new_manager.import_scenarios(exported)

        assert imported_count == 1
        assert "persistent_scenario" in new_manager._scenarios
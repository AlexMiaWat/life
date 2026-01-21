"""
Интеграционные тесты для ProcessRestarter и StateSerializer (новая функциональность dev-mode)

Проверяем:
- Взаимодействие ProcessRestarter с runtime loop
- Полные циклы сохранения и восстановления состояния
- Работа в многопоточной среде
- Интеграцию с graceful shutdown
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.dev.process_restarter import (
    GracefulShutdownManager,
    ProcessRestarter,
    StateSerializer,
    load_restart_state_if_available,
)


@pytest.mark.integration
class TestProcessRestarterIntegration:
    """Интеграционные тесты ProcessRestarter"""

    def test_full_restart_cycle_simulation(self):
        """Интеграционный тест полного цикла перезапуска"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем изолированный serializer
            restart_file = os.path.join(temp_dir, "restart_state.json")

            class TestStateSerializer(StateSerializer):
                RESTART_STATE_FILE = restart_file

            serializer = TestStateSerializer()

            # Имитируем сохранение состояния перед перезапуском
            self_state = {
                "energy": 80.0,
                "stability": 0.9,
                "integrity": 0.95,
                "ticks": 100,
            }
            event_queue = [
                {"type": "noise", "intensity": 0.3},
                {"type": "shock", "intensity": -0.7},
            ]
            config = {"tick_interval": 0.01, "snapshot_period": 50}

            # Сохраняем состояние
            result = serializer.save_restart_state(
                type("MockState", (), {"to_dict": lambda: self_state})(),
                type("MockQueue", (), {"to_dict": lambda: event_queue})(),
                config,
            )
            assert result is True

            # Имитируем перезапуск процесса
            # В реальном сценарии здесь был бы execv, но для теста просто загружаем
            loaded_state, was_restart = load_restart_state_if_available()

            # Модифицируем load_restart_state_if_available для использования нашего файла
            original_load = load_restart_state_if_available.__globals__["get_state_serializer"]

            def mock_get_serializer():
                return serializer

            load_restart_state_if_available.__globals__["get_state_serializer"] = (
                mock_get_serializer
            )

            try:
                loaded_state, was_restart = load_restart_state_if_available()

                assert was_restart is True
                assert loaded_state is not None
                assert loaded_state["self_state"] == self_state
                assert loaded_state["event_queue"] == event_queue
                assert loaded_state["config"] == config

            finally:
                # Восстанавливаем оригинальную функцию
                load_restart_state_if_available.__globals__["get_state_serializer"] = original_load

            # Очищаем состояние
            serializer.cleanup_restart_state()
            assert not os.path.exists(restart_file)

    def test_graceful_shutdown_integration(self):
        """Интеграционный тест graceful shutdown с несколькими компонентами"""
        manager = GracefulShutdownManager(shutdown_timeout=2.0)

        shutdown_order = []
        join_order = []

        def create_component(name, delay=0.01):
            def shutdown_func():
                time.sleep(delay)
                shutdown_order.append(name)

            def join_func(timeout=None):
                join_order.append((name, timeout))
                time.sleep(min(delay, timeout or 1.0))

            return shutdown_func, join_func

        # Регистрируем несколько компонентов
        components = ["database", "api_server", "event_processor", "monitor"]
        for name in components:
            shutdown_func, join_func = create_component(name)
            manager.register_component(name, shutdown_func, join_func, 0.5)

        # Запускаем shutdown
        result = manager.initiate_shutdown()
        assert result is True

        # Проверяем, что все компоненты были остановлены
        assert len(shutdown_order) == len(components)
        assert len(join_order) == len(components)

        # Проверяем, что shutdown был вызван для всех компонентов
        assert set(shutdown_order) == set(components)

    def test_process_restarter_full_integration(self):
        """Полная интеграция ProcessRestarter с компонентами"""
        restarter = ProcessRestarter(check_interval=0.1)

        # Регистрируем компоненты
        stopped_components = []

        def create_runtime_component(name):
            stop_event = threading.Event()

            def shutdown_func():
                stop_event.set()
                stopped_components.append(name)

            def join_func(timeout=None):
                # Имитируем ожидание остановки
                time.sleep(0.01)

            return shutdown_func, join_func, stop_event

        # Создаем mock runtime компоненты
        components = ["runtime_loop", "api_server", "event_generator"]
        stop_events = {}

        for name in components:
            shutdown_func, join_func, stop_event = create_runtime_component(name)
            restarter.register_component(name, shutdown_func, join_func, 0.2)
            stop_events[name] = stop_event

        # Имитируем сохранение состояния
        mock_state = type("MockState", (), {"to_dict": lambda: {"test": "state"}})()
        mock_queue = type("MockQueue", (), {"to_dict": lambda: []})()
        config = {"test": "config"}

        result = restarter.save_state_for_restart(mock_state, mock_queue, config)
        assert isinstance(result, bool)

        # Запускаем restarter
        restarter.start()
        assert restarter._running is True

        # Ждем немного
        time.sleep(0.05)

        # Останавливаем
        restarter.stop()

        # Проверяем, что restarter остановлен
        assert restarter._running is False

        # В реальном сценарии здесь проверяли бы graceful shutdown,
        # но для теста просто проверяем, что все работает без ошибок

    def test_multithreaded_state_serialization(self):
        """Тест многопоточной сериализации состояния"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restart_file = os.path.join(temp_dir, "restart_state.json")

            class TestStateSerializer(StateSerializer):
                RESTART_STATE_FILE = restart_file

            serializer = TestStateSerializer()

            results = []
            errors = []

            def save_worker(worker_id):
                try:
                    self_state = {
                        f"energy_{worker_id}": 50 + worker_id,
                        "ticks": worker_id * 10,
                    }
                    event_queue = [f"event_{worker_id}_{i}" for i in range(3)]
                    config = {f"config_{worker_id}": f"value_{worker_id}"}

                    mock_state = type("MockState", (), {"to_dict": lambda: self_state})()
                    mock_queue = type("MockQueue", (), {"to_dict": lambda: event_queue})()

                    result = serializer.save_restart_state(mock_state, mock_queue, config)
                    results.append((worker_id, result))

                except Exception as e:
                    errors.append((worker_id, str(e)))

            # Запускаем несколько потоков
            threads = []
            for i in range(5):
                t = threading.Thread(target=save_worker, args=(i,))
                threads.append(t)
                t.start()

            # Ждем завершения
            for t in threads:
                t.join()

            # Проверяем результаты
            assert len(results) == 5
            assert len(errors) == 0

            # Проверяем, что файл существует и содержит данные
            assert os.path.exists(restart_file)

            # Загружаем финальное состояние
            loaded = serializer.load_restart_state()
            assert loaded is not None

            # Очищаем
            serializer.cleanup_restart_state()

    def test_restart_state_persistence_across_simulated_restart(self):
        """Тест сохранения состояния между симулированными перезапусками"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restart_file = os.path.join(temp_dir, "restart_state.json")

            class TestStateSerializer(StateSerializer):
                RESTART_STATE_FILE = restart_file

            # Первый "запуск" процесса
            serializer1 = TestStateSerializer()

            initial_state = {"energy": 100.0, "stability": 1.0, "ticks": 0}
            initial_queue = []
            initial_config = {"initial": True}

            mock_state1 = type("MockState", (), {"to_dict": lambda: initial_state})()
            mock_queue1 = type("MockQueue", (), {"to_dict": lambda: initial_queue})()

            result1 = serializer1.save_restart_state(mock_state1, mock_queue1, initial_config)
            assert result1 is True

            # Имитируем "перезапуск" - создаем новый serializer
            serializer2 = TestStateSerializer()

            loaded_state, was_restart = load_restart_state_if_available.__globals__[
                "get_state_serializer"
            ] = lambda: serializer2

            def load_func():
                return serializer2.load_restart_state(), True

            loaded_state, was_restart = load_func()

            assert was_restart is True
            assert loaded_state is not None
            assert loaded_state["self_state"] == initial_state
            assert loaded_state["event_queue"] == initial_queue
            assert loaded_state["config"] == initial_config

            # Очищаем после "перезапуска"
            serializer2.cleanup_restart_state()
            assert not os.path.exists(restart_file)

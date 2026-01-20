"""
Дымовые тесты для ProcessRestarter и StateSerializer (новая функциональность dev-mode)

Проверяем:
- Базовую работоспособность без падений
- Создание экземпляров классов
- Вызов основных методов с минимальными данными
- Обработку пустых/минимальных входных данных
- Граничные значения параметров
"""

import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.dev.process_restarter import (
    GracefulShutdownManager,
    ProcessRestarter,
    StateSerializer,
    get_process_restarter,
    get_state_serializer,
    is_restart,
    load_restart_state_if_available,
)


@pytest.mark.smoke
class TestProcessRestarterSmoke:
    """Дымовые тесты для ProcessRestarter"""

    # ============================================================================
    # StateSerializer Smoke Tests
    # ============================================================================

    def test_state_serializer_instantiation(self):
        """Тест создания экземпляра StateSerializer"""
        serializer = StateSerializer()
        assert serializer is not None
        assert isinstance(serializer, StateSerializer)

    def test_state_serializer_save_load_empty_data(self):
        """Дымовой тест save_restart_state и load_restart_state с пустыми данными"""
        serializer = StateSerializer()

        # Создаем mock объекты
        mock_state = Mock()
        mock_state.to_dict.return_value = {"energy": 100.0}

        mock_queue = Mock()
        mock_queue.to_dict.return_value = []

        config = {"test": "config"}

        # Сохраняем состояние
        result = serializer.save_restart_state(mock_state, mock_queue, config)
        assert isinstance(result, bool)  # Должен вернуть bool, независимо от успеха

        # Пытаемся загрузить
        loaded_state = serializer.load_restart_state()

        # Если сохранение удалось, должна быть возможность загрузки
        if result:
            assert loaded_state is not None
            assert isinstance(loaded_state, dict)
            assert "restart_marker" in loaded_state
            assert "timestamp" in loaded_state
            assert "self_state" in loaded_state
            assert "event_queue" in loaded_state
            assert "config" in loaded_state

            assert loaded_state["restart_marker"] is True
            assert loaded_state["self_state"] == {"energy": 100.0}
            assert loaded_state["event_queue"] == []
            assert loaded_state["config"] == config

        # Очищаем состояние
        serializer.cleanup_restart_state()

    def test_state_serializer_without_to_dict(self):
        """Тест StateSerializer с объектами без to_dict метода"""
        serializer = StateSerializer()

        # Объекты без to_dict должны возвращать пустые значения
        result = serializer.save_restart_state(None, None, {})
        assert isinstance(result, bool)

        if result:
            loaded = serializer.load_restart_state()
            assert loaded is not None
            assert loaded["self_state"] == {}
            assert loaded["event_queue"] == []

        serializer.cleanup_restart_state()

    # ============================================================================
    # GracefulShutdownManager Smoke Tests
    # ============================================================================

    def test_graceful_shutdown_manager_instantiation(self):
        """Тест создания экземпляра GracefulShutdownManager"""
        manager = GracefulShutdownManager()
        assert manager is not None
        assert isinstance(manager, GracefulShutdownManager)

    def test_graceful_shutdown_manager_custom_timeout(self):
        """Тест создания с кастомным таймаутом"""
        manager = GracefulShutdownManager(shutdown_timeout=5.0)
        assert manager.shutdown_timeout == 5.0

    def test_graceful_shutdown_manager_register_component(self):
        """Тест регистрации компонента"""
        manager = GracefulShutdownManager()

        def dummy_shutdown():
            pass

        def dummy_join(timeout=None):
            pass

        # Регистрация без ошибок
        manager.register_component("test_component", dummy_shutdown, dummy_join, 2.0)

        # Проверяем, что компонент зарегистрирован
        assert len(manager._components) == 1
        component = manager._components[0]
        assert component["name"] == "test_component"
        assert component["shutdown_func"] == dummy_shutdown
        assert component["join_func"] == dummy_join
        assert component["timeout"] == 2.0

    def test_graceful_shutdown_manager_register_minimal(self):
        """Тест регистрации компонента с минимальными параметрами"""
        manager = GracefulShutdownManager()

        def dummy_shutdown():
            pass

        manager.register_component("minimal", dummy_shutdown)

        assert len(manager._components) == 1
        component = manager._components[0]
        assert component["name"] == "minimal"
        assert component["shutdown_func"] == dummy_shutdown
        assert component["join_func"] is None
        assert component["timeout"] == 5.0  # значение по умолчанию

    def test_graceful_shutdown_manager_initiate_shutdown_empty(self):
        """Тест initiate_shutdown без зарегистрированных компонентов"""
        manager = GracefulShutdownManager()

        result = manager.initiate_shutdown()
        assert isinstance(result, bool)
        assert result is True  # Пустой список компонентов - успех

    def test_graceful_shutdown_manager_initiate_shutdown_with_components(self):
        """Тест initiate_shutdown с зарегистрированными компонентами"""
        manager = GracefulShutdownManager()

        shutdown_called = []
        join_called = []

        def shutdown_func():
            shutdown_called.append(True)

        def join_func(timeout=None):
            join_called.append(timeout)
            time.sleep(0.01)  # Имитируем работу

        manager.register_component("test", shutdown_func, join_func, 0.1)

        result = manager.initiate_shutdown()
        assert isinstance(result, bool)
        assert result is True

        # Проверяем, что функции были вызваны
        assert len(shutdown_called) == 1
        assert len(join_called) == 1
        assert join_called[0] == 0.1

    def test_graceful_shutdown_manager_is_shutdown_requested(self):
        """Тест is_shutdown_requested"""
        manager = GracefulShutdownManager()

        # Изначально shutdown не запрошен
        assert manager.is_shutdown_requested() is False

        # После initiate_shutdown
        manager.initiate_shutdown()
        assert manager.is_shutdown_requested() is True

    # ============================================================================
    # ProcessRestarter Smoke Tests
    # ============================================================================

    def test_process_restarter_instantiation(self):
        """Тест создания экземпляра ProcessRestarter"""
        restarter = ProcessRestarter()
        assert restarter is not None
        assert isinstance(restarter, ProcessRestarter)

    def test_process_restarter_custom_interval(self):
        """Тест создания с кастомным интервалом проверки"""
        restarter = ProcessRestarter(check_interval=2.0)
        assert restarter.check_interval == 2.0

    def test_process_restarter_register_component(self):
        """Тест регистрации компонента в ProcessRestarter"""
        restarter = ProcessRestarter()

        def dummy_shutdown():
            pass

        def dummy_join(timeout=None):
            pass

        # Регистрация должна делегироваться в _shutdown_manager
        restarter.register_component("test", dummy_shutdown, dummy_join, 3.0)

        # Проверяем, что компонент зарегистрирован в менеджере
        assert len(restarter._shutdown_manager._components) == 1

    def test_process_restarter_save_state_for_restart(self):
        """Тест save_state_for_restart"""
        restarter = ProcessRestarter()

        mock_state = Mock()
        mock_state.to_dict.return_value = {"test": "state"}

        mock_queue = Mock()
        mock_queue.to_dict.return_value = ["event1", "event2"]

        config = {"setting": "value"}

        result = restarter.save_state_for_restart(mock_state, mock_queue, config)
        assert isinstance(result, bool)

        # Проверяем, что состояние сохранено через _state_serializer
        if result:
            loaded = restarter._state_serializer.load_restart_state()
            assert loaded is not None
            assert loaded["self_state"] == {"test": "state"}
            assert loaded["event_queue"] == ["event1", "event2"]
            assert loaded["config"] == config

        restarter._state_serializer.cleanup_restart_state()

    def test_process_restarter_start_stop(self):
        """Тест start/stop ProcessRestarter"""
        restarter = ProcessRestarter(check_interval=0.1)  # Быстрый интервал для теста

        # Start
        restarter.start()
        assert restarter._running is True
        assert restarter._thread is not None
        assert restarter._thread.is_alive()

        # Stop
        restarter.stop()
        assert restarter._running is False

        # Ждем завершения потока
        if restarter._thread and restarter._thread.is_alive():
            restarter._thread.join(timeout=1.0)

    def test_process_restarter_double_start(self):
        """Тест повторного запуска ProcessRestarter"""
        restarter = ProcessRestarter()

        # Первый запуск
        restarter.start()
        assert restarter._running is True

        # Второй запуск не должен вызывать проблем
        restarter.start()  # Не должно вызвать исключений
        assert restarter._running is True

        restarter.stop()

    # ============================================================================
    # Module-level Functions Smoke Tests
    # ============================================================================

    def test_get_process_restarter(self):
        """Тест get_process_restarter"""
        restarter = get_process_restarter()
        assert isinstance(restarter, ProcessRestarter)

        # Повторный вызов должен вернуть тот же экземпляр
        restarter2 = get_process_restarter()
        assert restarter is restarter2

    def test_get_state_serializer(self):
        """Тест get_state_serializer"""
        serializer = get_state_serializer()
        assert isinstance(serializer, StateSerializer)

        # Повторный вызов должен вернуть тот же экземпляр
        serializer2 = get_state_serializer()
        assert serializer is serializer2

    def test_is_restart(self):
        """Тест is_restart"""
        result = is_restart()
        assert isinstance(result, bool)

    def test_load_restart_state_if_available_no_state(self):
        """Тест load_restart_state_if_available без состояния"""
        state, was_restart = load_restart_state_if_available()
        assert state is None
        assert was_restart is False

    # ============================================================================
    # Thread Safety Smoke Tests
    # ============================================================================

    def test_state_serializer_thread_safety_smoke(self):
        """Дымовой тест потокобезопасности StateSerializer"""
        serializer = StateSerializer()

        results = []

        def worker(worker_id):
            try:
                mock_state = Mock()
                mock_state.to_dict.return_value = {
                    f"worker_{worker_id}": f"value_{worker_id}"
                }

                mock_queue = Mock()
                mock_queue.to_dict.return_value = [f"event_{worker_id}"]

                config = {f"config_{worker_id}": f"setting_{worker_id}"}

                result = serializer.save_restart_state(mock_state, mock_queue, config)
                results.append((worker_id, result))
            except Exception as e:
                results.append((worker_id, f"error: {e}"))

        # Запускаем несколько потоков
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # Ждем завершения
        for t in threads:
            t.join()

        # Все операции должны завершиться без ошибок
        assert len(results) == 3
        for worker_id, result in results:
            if isinstance(result, str) and result.startswith("error"):
                pytest.fail(f"Worker {worker_id} failed: {result}")

        # Очищаем состояние
        serializer.cleanup_restart_state()

    def test_graceful_shutdown_manager_thread_safety_smoke(self):
        """Дымовой тест потокобезопасности GracefulShutdownManager"""
        manager = GracefulShutdownManager()

        # Регистрируем компоненты из разных потоков
        components_registered = []

        def register_worker(worker_id):
            def shutdown_func():
                pass

            manager.register_component(f"component_{worker_id}", shutdown_func)
            components_registered.append(worker_id)

        # Запускаем несколько потоков
        threads = []
        for i in range(5):
            t = threading.Thread(target=register_worker, args=(i,))
            threads.append(t)
            t.start()

        # Ждем завершения
        for t in threads:
            t.join()

        # Все компоненты должны быть зарегистрированы
        assert len(components_registered) == 5
        assert len(manager._components) == 5

        # Initiate shutdown должен работать корректно
        result = manager.initiate_shutdown()
        assert isinstance(result, bool)

    # ============================================================================
    # File System Operations Smoke Tests
    # ============================================================================

    def test_state_serializer_file_operations(self):
        """Тест операций с файлами StateSerializer"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Создаем кастомный serializer с временной директорией
            restart_file = os.path.join(temp_dir, "test_restart.json")

            # Модифицируем RESTART_STATE_FILE через subclass
            class TestStateSerializer(StateSerializer):
                RESTART_STATE_FILE = restart_file

            serializer = TestStateSerializer()

            # Сохраняем состояние
            mock_state = Mock()
            mock_state.to_dict.return_value = {"test": "data"}

            result = serializer.save_restart_state(mock_state, Mock(), {})
            assert isinstance(result, bool)

            # Проверяем, что файл создан
            if result:
                assert os.path.exists(restart_file)

                # Загружаем состояние
                loaded = serializer.load_restart_state()
                assert loaded is not None

                # Очищаем
                serializer.cleanup_restart_state()
                assert not os.path.exists(restart_file)

    def test_process_restarter_file_tracking(self):
        """Тест отслеживания файлов ProcessRestarter"""
        restarter = ProcessRestarter()

        # Проверяем инициализацию отслеживания
        assert isinstance(restarter._file_mtimes, dict)

        # Проверяем, что файлы из FILES_TO_WATCH обрабатываются
        for file_path in ProcessRestarter.FILES_TO_WATCH:
            if os.path.exists(file_path):
                assert file_path in restarter._file_mtimes
            else:
                # Файл может отсутствовать, что нормально для теста
                pass

    # ============================================================================
    # Error Handling Smoke Tests
    # ============================================================================

    def test_state_serializer_error_handling(self):
        """Тест обработки ошибок StateSerializer"""
        serializer = StateSerializer()

        # Передаем None вместо объектов
        result = serializer.save_restart_state(None, None, None)
        # Должен вернуть False или True, но не падать
        assert isinstance(result, bool)

    def test_graceful_shutdown_manager_error_handling(self):
        """Тест обработки ошибок GracefulShutdownManager"""
        manager = GracefulShutdownManager()

        # Регистрируем компонент с функцией, которая вызывает ошибку
        def failing_shutdown():
            raise Exception("Test error")

        manager.register_component("failing", failing_shutdown)

        # initiate_shutdown должен обработать ошибку gracefully
        result = manager.initiate_shutdown()
        assert isinstance(result, bool)  # Даже при ошибке возвращает bool

    def test_process_restarter_error_handling(self):
        """Тест обработки ошибок ProcessRestarter"""
        restarter = ProcessRestarter()

        # Регистрация компонента с ошибкой
        def failing_shutdown():
            raise Exception("Shutdown error")

        restarter.register_component("failing", failing_shutdown)

        # start/stop должны работать несмотря на ошибки
        restarter.start()
        time.sleep(0.01)  # Даем время на инициализацию

        restarter.stop()  # Не должно падать

        # Повторный stop безопасен
        restarter.stop()

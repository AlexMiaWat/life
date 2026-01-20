"""
Дымовые тесты для модуля process_restarter (новая функциональность dev-mode)

Проверяем:
- Базовую работоспособность без падений
- Создание экземпляров классов
- Вызов основных методов с минимальными данными
- Обработку пустых/минимальных входных данных
- Граничные значения параметров
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

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
class TestDevProcessRestarterSmoke:
    """Дымовые тесты для модуля process_restarter"""

    # ============================================================================
    # StateSerializer Smoke Tests
    # ============================================================================

    def test_state_serializer_instantiation(self):
        """Тест создания экземпляра StateSerializer"""
        serializer = StateSerializer()
        assert serializer is not None
        assert isinstance(serializer, StateSerializer)

    def test_state_serializer_save_empty_state(self):
        """Дымовой тест сохранения пустого состояния"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                StateSerializer, "RESTART_STATE_FILE", f"{temp_dir}/test_state.json"
            ):
                serializer = StateSerializer()

                # Создаем mock объекты
                mock_self_state = MagicMock()
                mock_self_state.to_dict.return_value = {"energy": 100.0}

                mock_event_queue = MagicMock()
                mock_event_queue.to_dict.return_value = []

                config = {"test": "config"}

                result = serializer.save_restart_state(
                    mock_self_state, mock_event_queue, config
                )
                assert isinstance(result, bool)

    def test_state_serializer_load_nonexistent_state(self):
        """Дымовой тест загрузки несуществующего состояния"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                StateSerializer, "RESTART_STATE_FILE", f"{temp_dir}/nonexistent.json"
            ):
                serializer = StateSerializer()
                result = serializer.load_restart_state()
                assert result is None

    def test_state_serializer_load_valid_state(self):
        """Дымовой тест загрузки корректного состояния"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = f"{temp_dir}/test_state.json"
            test_data = {
                "restart_marker": True,
                "timestamp": time.time(),
                "self_state": {"energy": 50.0},
                "event_queue": [{"type": "test"}],
                "config": {"setting": "value"},
            }

            with open(test_file, "w") as f:
                json.dump(test_data, f)

            with patch.object(StateSerializer, "RESTART_STATE_FILE", test_file):
                serializer = StateSerializer()
                result = serializer.load_restart_state()
                assert result is not None
                assert result["restart_marker"] is True
                assert "self_state" in result
                assert "event_queue" in result
                assert "config" in result

    def test_state_serializer_cleanup(self):
        """Дымовой тест очистки файла состояния"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = f"{temp_dir}/test_state.json"

            # Создаем файл
            with open(test_file, "w") as f:
                json.dump({"test": "data"}, f)

            with patch.object(StateSerializer, "RESTART_STATE_FILE", test_file):
                serializer = StateSerializer()
                assert os.path.exists(test_file)

                serializer.cleanup_restart_state()
                assert not os.path.exists(test_file)

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
        assert manager is not None
        assert isinstance(manager, GracefulShutdownManager)

    def test_graceful_shutdown_manager_register_component_minimal(self):
        """Дымовой тест регистрации компонента с минимальными данными"""
        manager = GracefulShutdownManager()

        def dummy_shutdown():
            pass

        manager.register_component("test_component", dummy_shutdown)
        assert len(manager._components) == 1

    def test_graceful_shutdown_manager_register_component_full(self):
        """Дымовой тест регистрации компонента со всеми параметрами"""
        manager = GracefulShutdownManager()

        def dummy_shutdown():
            pass

        def dummy_join():
            pass

        manager.register_component(
            "test_component", dummy_shutdown, dummy_join, timeout=2.0
        )
        assert len(manager._components) == 1
        component = manager._components[0]
        assert component["name"] == "test_component"
        assert component["shutdown_func"] == dummy_shutdown
        assert component["join_func"] == dummy_join
        assert component["timeout"] == 2.0

    def test_graceful_shutdown_manager_initiate_shutdown_no_components(self):
        """Дымовой тест инициирования shutdown без зарегистрированных компонентов"""
        manager = GracefulShutdownManager()
        result = manager.initiate_shutdown()
        assert isinstance(result, bool)

    def test_graceful_shutdown_manager_initiate_shutdown_with_components(self):
        """Дымовой тест инициирования shutdown с зарегистрированными компонентами"""
        manager = GracefulShutdownManager()

        shutdown_called = False
        join_called = False

        def dummy_shutdown():
            nonlocal shutdown_called
            shutdown_called = True

        def dummy_join(timeout=None):
            nonlocal join_called
            join_called = True

        manager.register_component(
            "test_component", dummy_shutdown, dummy_join, timeout=0.1
        )

        result = manager.initiate_shutdown()
        assert isinstance(result, bool)
        assert shutdown_called
        assert join_called

    def test_graceful_shutdown_manager_is_shutdown_requested(self):
        """Дымовой тест проверки флага shutdown"""
        manager = GracefulShutdownManager()
        result = manager.is_shutdown_requested()
        assert isinstance(result, bool)
        assert result is False

        # После инициирования shutdown
        manager.initiate_shutdown()
        result = manager.is_shutdown_requested()
        assert result is True

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
        assert restarter is not None
        assert isinstance(restarter, ProcessRestarter)

    def test_process_restarter_register_component(self):
        """Дымовой тест регистрации компонента в ProcessRestarter"""
        restarter = ProcessRestarter()

        def dummy_shutdown():
            pass

        restarter.register_component("test_component", dummy_shutdown)
        # Проверяем что компонент зарегистрирован в shutdown manager
        assert len(restarter._shutdown_manager._components) == 1

    def test_process_restarter_save_state_for_restart(self):
        """Дымовой тест сохранения состояния для перезапуска"""
        with tempfile.TemporaryDirectory() as temp_dir:
            restarter = ProcessRestarter()

            # Mock the state serializer
            with patch.object(
                restarter._state_serializer, "save_restart_state", return_value=True
            ):
                mock_self_state = MagicMock()
                mock_event_queue = MagicMock()
                config = {"test": "config"}

                result = restarter.save_state_for_restart(
                    mock_self_state, mock_event_queue, config
                )
                assert isinstance(result, bool)

    @patch("threading.Thread")
    def test_process_restarter_start_stop(self, mock_thread_class):
        """Дымовой тест запуска и остановки ProcessRestarter"""
        mock_thread = MagicMock()
        mock_thread_class.return_value = mock_thread
        mock_thread.is_alive.return_value = True

        restarter = ProcessRestarter()

        # Test start
        restarter.start()
        assert restarter._running is True
        assert restarter._thread is not None
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()

        # Test stop
        restarter.stop()
        assert restarter._running is False
        mock_thread.join.assert_called_once_with(timeout=2.0)

    def test_process_restarter_start_already_running(self):
        """Дымовой тест повторного запуска уже запущенного ProcessRestarter"""
        with patch("threading.Thread"):
            restarter = ProcessRestarter()
            restarter._running = True
            restarter._thread = MagicMock()

            # Should not create new thread
            restarter.start()
            # No assertions needed, just checking it doesn't crash

    # ============================================================================
    # Module Functions Smoke Tests
    # ============================================================================

    def test_get_process_restarter(self):
        """Дымовой тест получения глобального ProcessRestarter"""
        restarter = get_process_restarter()
        assert restarter is not None
        assert isinstance(restarter, ProcessRestarter)

        # Повторный вызов должен вернуть тот же экземпляр
        restarter2 = get_process_restarter()
        assert restarter is restarter2

    def test_get_state_serializer(self):
        """Дымовой тест получения глобального StateSerializer"""
        serializer = get_state_serializer()
        assert serializer is not None
        assert isinstance(serializer, StateSerializer)

        # Повторный вызов должен вернуть тот же экземпляр
        serializer2 = get_state_serializer()
        assert serializer is serializer2

    def test_is_restart_no_flag(self):
        """Дымовой тест проверки флага перезапуска (без флага)"""
        result = is_restart()
        assert isinstance(result, bool)

    @patch("sys.argv", ["test_script.py", "--restart"])
    def test_is_restart_with_flag(self):
        """Дымовой тест проверки флага перезапуска (с флагом)"""
        result = is_restart()
        assert result is True

    def test_load_restart_state_if_available_no_file(self):
        """Дымовой тест загрузки состояния при отсутствии файла"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                StateSerializer, "RESTART_STATE_FILE", f"{temp_dir}/nonexistent.json"
            ):
                state, was_restart = load_restart_state_if_available()
                assert state is None
                assert was_restart is False

    def test_load_restart_state_if_available_with_file(self):
        """Дымовой тест загрузки состояния при наличии файла"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = f"{temp_dir}/restart_state.json"
            test_data = {
                "restart_marker": True,
                "timestamp": time.time(),
                "self_state": {"energy": 75.0},
                "event_queue": [],
                "config": {"mode": "dev"},
            }

            with open(test_file, "w") as f:
                json.dump(test_data, f)

            with patch.object(StateSerializer, "RESTART_STATE_FILE", test_file):
                state, was_restart = load_restart_state_if_available()
                assert state is not None
                assert was_restart is True
                # Проверяем что файл был удален после загрузки
                assert not os.path.exists(test_file)

    # ============================================================================
    # Edge Cases Smoke Tests
    # ============================================================================

    def test_state_serializer_atomic_write_failure(self):
        """Дымовой тест атомарной записи при ошибке"""
        with patch("os.rename", side_effect=OSError("Disk full")):
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch.object(
                    StateSerializer, "RESTART_STATE_FILE", f"{temp_dir}/test.json"
                ):
                    serializer = StateSerializer()

                    mock_self_state = MagicMock()
                    mock_self_state.to_dict.return_value = {"test": "data"}

                    mock_event_queue = MagicMock()
                    mock_event_queue.to_dict.return_value = []

                    result = serializer.save_restart_state(
                        mock_self_state, mock_event_queue, {}
                    )
                    assert result is False

    def test_graceful_shutdown_component_failure(self):
        """Дымовой тест shutdown при ошибке компонента"""
        manager = GracefulShutdownManager()

        def failing_shutdown():
            raise Exception("Shutdown failed")

        manager.register_component("failing_component", failing_shutdown)
        result = manager.initiate_shutdown()
        # Должен вернуть False из-за ошибки, но не падать
        assert isinstance(result, bool)

    def test_process_restarter_file_tracking_init(self):
        """Дымовой тест инициализации отслеживания файлов"""
        # Создаем временные файлы для тестирования
        with tempfile.TemporaryDirectory() as temp_dir:
            test_files = []
            for i, file_path in enumerate(
                ProcessRestarter.FILES_TO_WATCH[:3]
            ):  # Только первые 3
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(f"test content {i}")
                test_files.append(full_path)

            # Mock FILES_TO_WATCH to use temp files
            with patch.object(ProcessRestarter, "FILES_TO_WATCH", test_files):
                restarter = ProcessRestarter()
                assert len(restarter._file_mtimes) == 3
                for file_path in test_files:
                    assert file_path in restarter._file_mtimes

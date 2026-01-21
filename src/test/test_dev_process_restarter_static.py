"""
Статические тесты для модуля process_restarter (новая функциональность dev-mode)

Проверяем:
- Структуру классов StateSerializer, GracefulShutdownManager, ProcessRestarter
- Константы и их значения
- Сигнатуры методов
- Типы возвращаемых значений
- Отсутствие запрещенных методов/атрибутов
- Архитектурные ограничения
"""

import inspect
import sys
import threading
from pathlib import Path

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


@pytest.mark.static
class TestDevProcessRestarterStatic:
    """Статические тесты для модуля process_restarter"""

    # ============================================================================
    # StateSerializer Static Tests
    # ============================================================================

    def test_state_serializer_structure(self):
        """Проверка структуры StateSerializer"""
        assert hasattr(StateSerializer, "__init__")
        assert hasattr(StateSerializer, "save_restart_state")
        assert hasattr(StateSerializer, "load_restart_state")
        assert hasattr(StateSerializer, "cleanup_restart_state")
        assert hasattr(StateSerializer, "RESTART_STATE_FILE")

    def test_state_serializer_constants(self):
        """Проверка констант StateSerializer"""
        assert StateSerializer.RESTART_STATE_FILE == "data/restart_state.json"

    def test_state_serializer_methods_signatures(self):
        """Проверка сигнатур методов StateSerializer"""
        # save_restart_state
        sig = inspect.signature(StateSerializer.save_restart_state)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "self_state" in params
        assert "event_queue" in params
        assert "config" in params
        assert sig.return_annotation == bool

        # load_restart_state
        sig = inspect.signature(StateSerializer.load_restart_state)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert len(params) == 1  # только self
        # Проверяем что возвращает Optional[Dict[str, Any]]
        assert "Optional" in str(sig.return_annotation) or sig.return_annotation is None

        # cleanup_restart_state
        sig = inspect.signature(StateSerializer.cleanup_restart_state)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert len(params) == 1  # только self

    def test_state_serializer_private_attributes(self):
        """Проверка приватных атрибутов StateSerializer"""
        instance = StateSerializer()
        assert hasattr(instance, "_lock")
        assert instance._lock is not None  # Проверяем что lock инициализирован

    # ============================================================================
    # GracefulShutdownManager Static Tests
    # ============================================================================

    def test_graceful_shutdown_manager_structure(self):
        """Проверка структуры GracefulShutdownManager"""
        assert hasattr(GracefulShutdownManager, "__init__")
        assert hasattr(GracefulShutdownManager, "register_component")
        assert hasattr(GracefulShutdownManager, "initiate_shutdown")
        assert hasattr(GracefulShutdownManager, "is_shutdown_requested")

    def test_graceful_shutdown_manager_methods_signatures(self):
        """Проверка сигнатур методов GracefulShutdownManager"""
        # __init__
        sig = inspect.signature(GracefulShutdownManager.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "shutdown_timeout" in params
        assert sig.parameters["shutdown_timeout"].default == 10.0

        # register_component
        sig = inspect.signature(GracefulShutdownManager.register_component)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "component_name" in params
        assert "shutdown_func" in params
        assert "join_func" in params
        assert "timeout" in params
        assert sig.parameters["join_func"].default is None
        assert sig.parameters["timeout"].default == 5.0

        # initiate_shutdown
        sig = inspect.signature(GracefulShutdownManager.initiate_shutdown)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert len(params) == 1  # только self
        assert sig.return_annotation == bool

        # is_shutdown_requested
        sig = inspect.signature(GracefulShutdownManager.is_shutdown_requested)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert len(params) == 1  # только self
        assert sig.return_annotation == bool

    def test_graceful_shutdown_manager_private_attributes(self):
        """Проверка приватных атрибутов GracefulShutdownManager"""
        instance = GracefulShutdownManager()
        assert hasattr(instance, "_shutdown_event")
        assert hasattr(instance, "_components")
        assert isinstance(instance._shutdown_event, threading.Event)
        assert isinstance(instance._components, list)

    # ============================================================================
    # ProcessRestarter Static Tests
    # ============================================================================

    def test_process_restarter_structure(self):
        """Проверка структуры ProcessRestarter"""
        assert hasattr(ProcessRestarter, "__init__")
        assert hasattr(ProcessRestarter, "register_component")
        assert hasattr(ProcessRestarter, "save_state_for_restart")
        assert hasattr(ProcessRestarter, "start")
        assert hasattr(ProcessRestarter, "stop")
        assert hasattr(ProcessRestarter, "FILES_TO_WATCH")

    def test_process_restarter_constants(self):
        """Проверка констант ProcessRestarter"""
        expected_files = [
            "src/main_server_api.py",
            "src/monitor/console.py",
            "src/runtime/loop.py",
            "src/state/self_state.py",
            "src/environment/event.py",
            "src/environment/event_queue.py",
            "src/environment/generator.py",
            "src/dev/process_restarter.py",
        ]
        assert ProcessRestarter.FILES_TO_WATCH == expected_files

    def test_process_restarter_methods_signatures(self):
        """Проверка сигнатур методов ProcessRestarter"""
        # __init__
        sig = inspect.signature(ProcessRestarter.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "check_interval" in params
        assert sig.parameters["check_interval"].default == 1.0

        # register_component
        sig = inspect.signature(ProcessRestarter.register_component)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "component_name" in params
        assert "shutdown_func" in params
        assert "join_func" in params
        assert "timeout" in params
        assert sig.parameters["join_func"].default is None
        assert sig.parameters["timeout"].default == 5.0

        # save_state_for_restart
        sig = inspect.signature(ProcessRestarter.save_state_for_restart)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "self_state" in params
        assert "event_queue" in params
        assert "config" in params
        assert sig.return_annotation == bool

        # start
        sig = inspect.signature(ProcessRestarter.start)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert len(params) == 1  # только self

        # stop
        sig = inspect.signature(ProcessRestarter.stop)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert len(params) == 1  # только self

    def test_process_restarter_private_attributes(self):
        """Проверка приватных атрибутов ProcessRestarter"""
        instance = ProcessRestarter()
        assert hasattr(instance, "_running")
        assert hasattr(instance, "_thread")
        assert hasattr(instance, "_file_mtimes")
        assert hasattr(instance, "_shutdown_manager")
        assert hasattr(instance, "_state_serializer")
        assert isinstance(instance._shutdown_manager, GracefulShutdownManager)
        assert isinstance(instance._state_serializer, StateSerializer)

    # ============================================================================
    # Module-level Functions Static Tests
    # ============================================================================

    def test_module_functions_structure(self):
        """Проверка структуры функций модуля"""
        # Проверяем наличие всех функций
        assert callable(get_process_restarter)
        assert callable(get_state_serializer)
        assert callable(is_restart)
        assert callable(load_restart_state_if_available)

    def test_module_functions_signatures(self):
        """Проверка сигнатур функций модуля"""
        # get_process_restarter
        sig = inspect.signature(get_process_restarter)
        assert len(sig.parameters) == 0
        assert "ProcessRestarter" in str(sig.return_annotation)

        # get_state_serializer
        sig = inspect.signature(get_state_serializer)
        assert len(sig.parameters) == 0
        assert "StateSerializer" in str(sig.return_annotation)

        # is_restart
        sig = inspect.signature(is_restart)
        assert len(sig.parameters) == 0
        assert sig.return_annotation == bool

        # load_restart_state_if_available
        sig = inspect.signature(load_restart_state_if_available)
        assert len(sig.parameters) == 0
        # Функция возвращает кортеж - просто проверяем сигнатуру

    # ============================================================================
    # Architectural Constraints Tests
    # ============================================================================

    def test_no_forbidden_imports(self):
        """Проверка отсутствия запрещенных импортов"""
        import src.dev.process_restarter as pr_module

        # Проверяем что нет импортов из других модулей, которые могут создать циклические зависимости
        forbidden_modules = [
            "src.main_server_api",
            "src.runtime.loop",
            "src.monitor.console",
        ]

        for name, module in sys.modules.items():
            if name in forbidden_modules and hasattr(pr_module, name.split(".")[-1]):
                # Если есть импорт, проверяем что он отложенный (lazy)
                attr = getattr(pr_module, name.split(".")[-1])
                assert (
                    not hasattr(attr, "__module__") or attr.__module__ != name
                ), f"Direct import of {name} not allowed in process_restarter"

    def test_thread_safety_indicators(self):
        """Проверка индикаторов потокобезопасности"""
        # Проверяем что используются threading primitives для синхронизации
        # StateSerializer должен иметь lock
        ss = StateSerializer()
        assert hasattr(ss, "_lock")
        assert ss._lock is not None

        # GracefulShutdownManager должен иметь Event
        gsm = GracefulShutdownManager()
        assert hasattr(gsm, "_shutdown_event")
        assert gsm._shutdown_event is not None

    def test_file_paths_are_valid(self):
        """Проверка что пути к файлам в FILES_TO_WATCH существуют или могут существовать"""
        # Все пути должны быть относительными и начинаться с src/
        for file_path in ProcessRestarter.FILES_TO_WATCH:
            assert file_path.startswith("src/"), f"Invalid file path: {file_path}"
            assert not file_path.startswith("/"), f"Absolute path not allowed: {file_path}"
            assert ".." not in file_path, f"Parent directory not allowed: {file_path}"

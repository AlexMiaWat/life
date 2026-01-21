"""
Статические тесты для ProcessRestarter и StateSerializer (новая функциональность dev-mode)

Проверяем:
- Структуру классов и модулей
- Константы и их значения
- Сигнатуры методов
- Типы возвращаемых значений
- Архитектурные ограничения
"""

import inspect
import sys
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
class TestProcessRestarterStatic:
    """Статические тесты для ProcessRestarter"""

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

    def test_state_serializer_init_signature(self):
        """Проверка сигнатуры __init__ StateSerializer"""
        sig = inspect.signature(StateSerializer.__init__)
        assert len(sig.parameters) == 1  # self
        assert sig.return_annotation == type(None)

    def test_state_serializer_method_signatures(self):
        """Проверка сигнатур методов StateSerializer"""
        serializer = StateSerializer()

        # save_restart_state
        sig = inspect.signature(serializer.save_restart_state)
        assert len(sig.parameters) == 4  # self + self_state + event_queue + config
        assert "self_state" in sig.parameters
        assert "event_queue" in sig.parameters
        assert "config" in sig.parameters
        assert sig.return_annotation == bool

        # load_restart_state
        sig = inspect.signature(serializer.load_restart_state)
        assert len(sig.parameters) == 1  # self
        assert "Optional" in str(sig.return_annotation) or sig.return_annotation == dict

        # cleanup_restart_state
        sig = inspect.signature(serializer.cleanup_restart_state)
        assert len(sig.parameters) == 1  # self
        assert sig.return_annotation == type(None)

    def test_state_serializer_attributes(self):
        """Проверка атрибутов StateSerializer"""
        serializer = StateSerializer()

        assert hasattr(serializer, "_lock")
        # Проверяем, что _lock является Lock
        assert hasattr(serializer._lock, "acquire")
        assert hasattr(serializer._lock, "release")

    # ============================================================================
    # GracefulShutdownManager Static Tests
    # ============================================================================

    def test_graceful_shutdown_manager_structure(self):
        """Проверка структуры GracefulShutdownManager"""
        assert hasattr(GracefulShutdownManager, "__init__")
        assert hasattr(GracefulShutdownManager, "register_component")
        assert hasattr(GracefulShutdownManager, "initiate_shutdown")
        assert hasattr(GracefulShutdownManager, "is_shutdown_requested")

    def test_graceful_shutdown_manager_init_signature(self):
        """Проверка сигнатуры __init__ GracefulShutdownManager"""
        sig = inspect.signature(GracefulShutdownManager.__init__)
        assert len(sig.parameters) == 2  # self + shutdown_timeout
        assert "shutdown_timeout" in sig.parameters

        # Значение по умолчанию
        shutdown_timeout_param = sig.parameters["shutdown_timeout"]
        assert shutdown_timeout_param.default == 10.0

    def test_graceful_shutdown_manager_method_signatures(self):
        """Проверка сигнатур методов GracefulShutdownManager"""
        manager = GracefulShutdownManager()

        # register_component
        sig = inspect.signature(manager.register_component)
        assert (
            len(sig.parameters) == 5
        )  # self + component_name + shutdown_func + join_func + timeout
        assert "component_name" in sig.parameters
        assert "shutdown_func" in sig.parameters
        assert "join_func" in sig.parameters
        assert "timeout" in sig.parameters
        assert sig.return_annotation == type(None)

        # initiate_shutdown
        sig = inspect.signature(manager.initiate_shutdown)
        assert len(sig.parameters) == 1  # self
        assert sig.return_annotation == bool

        # is_shutdown_requested
        sig = inspect.signature(manager.is_shutdown_requested)
        assert len(sig.parameters) == 1  # self
        assert sig.return_annotation == bool

    def test_graceful_shutdown_manager_attributes(self):
        """Проверка атрибутов GracefulShutdownManager"""
        manager = GracefulShutdownManager()

        assert hasattr(manager, "shutdown_timeout")
        assert hasattr(manager, "_shutdown_event")
        assert hasattr(manager, "_components")

        assert manager.shutdown_timeout == 10.0
        assert manager._components == []

        # Проверяем, что _shutdown_event является Event
        assert hasattr(manager._shutdown_event, "set")
        assert hasattr(manager._shutdown_event, "is_set")

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
        assert len(ProcessRestarter.FILES_TO_WATCH) == 8

    def test_process_restarter_init_signature(self):
        """Проверка сигнатуры __init__ ProcessRestarter"""
        sig = inspect.signature(ProcessRestarter.__init__)
        assert len(sig.parameters) == 2  # self + check_interval
        assert "check_interval" in sig.parameters

        # Значение по умолчанию
        check_interval_param = sig.parameters["check_interval"]
        assert check_interval_param.default == 1.0

    def test_process_restarter_method_signatures(self):
        """Проверка сигнатур методов ProcessRestarter"""
        restarter = ProcessRestarter()

        # register_component
        sig = inspect.signature(restarter.register_component)
        assert (
            len(sig.parameters) == 5
        )  # self + component_name + shutdown_func + join_func + timeout
        assert "component_name" in sig.parameters
        assert "shutdown_func" in sig.parameters
        assert "join_func" in sig.parameters
        assert "timeout" in sig.parameters
        assert sig.return_annotation == type(None)

        # save_state_for_restart
        sig = inspect.signature(restarter.save_state_for_restart)
        assert len(sig.parameters) == 4  # self + self_state + event_queue + config
        assert "self_state" in sig.parameters
        assert "event_queue" in sig.parameters
        assert "config" in sig.parameters
        assert sig.return_annotation == bool

        # start
        sig = inspect.signature(restarter.start)
        assert len(sig.parameters) == 1  # self
        assert sig.return_annotation == type(None)

        # stop
        sig = inspect.signature(restarter.stop)
        assert len(sig.parameters) == 1  # self
        assert sig.return_annotation == type(None)

    def test_process_restarter_attributes(self):
        """Проверка атрибутов ProcessRestarter"""
        restarter = ProcessRestarter()

        assert hasattr(restarter, "check_interval")
        assert hasattr(restarter, "_running")
        assert hasattr(restarter, "_thread")
        assert hasattr(restarter, "_file_mtimes")
        assert hasattr(restarter, "_shutdown_manager")
        assert hasattr(restarter, "_state_serializer")

        assert restarter.check_interval == 1.0
        assert restarter._running is False
        assert restarter._thread is None
        assert isinstance(restarter._file_mtimes, dict)

        # Проверяем типы вложенных объектов
        assert isinstance(restarter._shutdown_manager, GracefulShutdownManager)
        assert isinstance(restarter._state_serializer, StateSerializer)

    # ============================================================================
    # Module-level Functions Static Tests
    # ============================================================================

    def test_module_functions_signatures(self):
        """Проверка сигнатур функций модуля"""

        # get_process_restarter
        sig = inspect.signature(get_process_restarter)
        assert len(sig.parameters) == 0
        assert sig.return_annotation == ProcessRestarter

        # get_state_serializer
        sig = inspect.signature(get_state_serializer)
        assert len(sig.parameters) == 0
        assert sig.return_annotation == StateSerializer

        # is_restart
        sig = inspect.signature(is_restart)
        assert len(sig.parameters) == 0
        assert sig.return_annotation == bool

        # load_restart_state_if_available
        sig = inspect.signature(load_restart_state_if_available)
        assert len(sig.parameters) == 0
        # Возвращает tuple
        assert "Tuple" in str(sig.return_annotation)

    # ============================================================================
    # Inheritance and Architecture Tests
    # ============================================================================

    def test_class_inheritance(self):
        """Проверка наследования классов"""
        assert StateSerializer.__bases__ == (object,)
        assert GracefulShutdownManager.__bases__ == (object,)
        assert ProcessRestarter.__bases__ == (object,)

    def test_docstrings_presence(self):
        """Проверка наличия docstrings"""
        assert StateSerializer.__doc__ is not None
        assert GracefulShutdownManager.__doc__ is not None
        assert ProcessRestarter.__doc__ is not None

        serializer = StateSerializer()
        assert serializer.save_restart_state.__doc__ is not None
        assert serializer.load_restart_state.__doc__ is not None

        manager = GracefulShutdownManager()
        assert manager.register_component.__doc__ is not None
        assert manager.initiate_shutdown.__doc__ is not None

        restarter = ProcessRestarter()
        assert restarter.register_component.__doc__ is not None
        assert restarter.save_state_for_restart.__doc__ is not None
        assert restarter.start.__doc__ is not None
        assert restarter.stop.__doc__ is not None

    def test_no_forbidden_imports(self):
        """Проверка отсутствия запрещенных импортов"""
        source_code = inspect.getsource(sys.modules["src.dev.process_restarter"])

        # Не должно быть импортов опасных модулей
        forbidden_imports = [
            "import subprocess",
            "import os.exec",
            "import os.system",
            "import importlib.reload",
        ]

        for forbidden in forbidden_imports:
            assert forbidden not in source_code, f"Запрещенный импорт найден: {forbidden}"

    def test_architecture_compliance(self):
        """Проверка соответствия архитектуре dev-mode"""
        # ProcessRestarter должен быть инструментом разработки, не частью runtime
        restarter_source = inspect.getsource(ProcessRestarter)

        # Не должен содержать бизнес-логику
        forbidden_patterns = [
            "decide_response",
            "execute_action",
            "process_event",
            "learning",
            "adaptation",
            "meaning",
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in restarter_source.lower()
            ), f"Бизнес-логика в ProcessRestarter: {pattern}"

    def test_thread_safety_indicators(self):
        """Проверка индикаторов потокобезопасности"""
        # Все классы должны использовать блокировки для критических операций

        # StateSerializer должен использовать _lock
        serializer_source = inspect.getsource(StateSerializer)
        assert "_lock" in serializer_source

        # GracefulShutdownManager должен использовать _shutdown_event
        manager_source = inspect.getsource(GracefulShutdownManager)
        assert "_shutdown_event" in manager_source

        # ProcessRestarter должен быть потокобезопасным
        restarter_source = inspect.getsource(ProcessRestarter)
        assert "threading" in restarter_source or "_thread" in restarter_source

    def test_imports_structure(self):
        """Проверка структуры импортов"""
        import src.dev.process_restarter as pr_module

        # Проверяем что модуль экспортирует основные классы и функции
        assert hasattr(pr_module, "StateSerializer")
        assert hasattr(pr_module, "GracefulShutdownManager")
        assert hasattr(pr_module, "ProcessRestarter")
        assert hasattr(pr_module, "get_process_restarter")
        assert hasattr(pr_module, "get_state_serializer")
        assert hasattr(pr_module, "is_restart")
        assert hasattr(pr_module, "load_restart_state_if_available")

        # Проверяем соответствие
        assert pr_module.StateSerializer == StateSerializer
        assert pr_module.GracefulShutdownManager == GracefulShutdownManager
        assert pr_module.ProcessRestarter == ProcessRestarter

    def test_no_global_state_pollution(self):
        """Проверка отсутствия загрязнения глобального состояния"""
        # Глобальные переменные должны быть приватными
        source_code = inspect.getsource(sys.modules["src.dev.process_restarter"])

        # Глобальные экземпляры должны быть приватными
        assert "_process_restarter" in source_code
        assert "_state_serializer" in source_code

        # Нет публичных глобальных переменных кроме функций
        lines = source_code.split("\n")
        global_lines = [
            line
            for line in lines
            if line.strip().startswith("process_restarter =")
            or line.strip().startswith("state_serializer =")
        ]

        assert len(global_lines) == 0, "Найдены публичные глобальные переменные"

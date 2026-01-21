"""
Статические тесты для StructuredLogger (новая функциональность наблюдаемости)

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

from src.observability.structured_logger import StructuredLogger


@pytest.mark.static
class TestStructuredLoggerStatic:
    """Статические тесты для StructuredLogger"""

    # ============================================================================
    # StructuredLogger Static Tests
    # ============================================================================

    def test_structured_logger_structure(self):
        """Проверка структуры StructuredLogger"""
        assert hasattr(StructuredLogger, "__init__")
        assert hasattr(StructuredLogger, "log_event")
        assert hasattr(StructuredLogger, "log_meaning")
        assert hasattr(StructuredLogger, "log_decision")
        assert hasattr(StructuredLogger, "log_action")
        assert hasattr(StructuredLogger, "log_feedback")
        assert hasattr(StructuredLogger, "log_tick_start")
        assert hasattr(StructuredLogger, "log_tick_end")
        assert hasattr(StructuredLogger, "log_error")
        assert hasattr(StructuredLogger, "_get_next_correlation_id")
        assert hasattr(StructuredLogger, "_write_log_entry")

    def test_structured_logger_init_signature(self):
        """Проверка сигнатуры __init__ StructuredLogger"""
        sig = inspect.signature(StructuredLogger.__init__)
        assert len(sig.parameters) == 3  # self + log_file + enabled
        assert "log_file" in sig.parameters
        assert "enabled" in sig.parameters

        # Проверяем значения по умолчанию
        log_file_param = sig.parameters["log_file"]
        enabled_param = sig.parameters["enabled"]

        assert log_file_param.default == "data/structured_log.jsonl"
        assert enabled_param.default is True

    def test_structured_logger_method_signatures(self):
        """Проверка сигнатур основных методов StructuredLogger"""
        logger = StructuredLogger(enabled=False)  # disabled для тестов

        # log_event
        sig = inspect.signature(logger.log_event)
        assert len(sig.parameters) == 2  # event + correlation_id (self не считается)
        assert "event" in sig.parameters
        assert "correlation_id" in sig.parameters
        assert sig.return_annotation is str

        # log_meaning
        sig = inspect.signature(logger.log_meaning)
        assert (
            len(sig.parameters) == 3
        )  # event + meaning + correlation_id (self не считается)
        assert "event" in sig.parameters
        assert "meaning" in sig.parameters
        assert "correlation_id" in sig.parameters
        assert sig.return_annotation is type(None)

        # log_decision
        sig = inspect.signature(logger.log_decision)
        assert (
            len(sig.parameters) == 3
        )  # pattern + correlation_id + additional_data (self не считается)
        assert "pattern" in sig.parameters
        assert "correlation_id" in sig.parameters
        assert "additional_data" in sig.parameters
        assert sig.return_annotation is type(None)

        # log_action
        sig = inspect.signature(logger.log_action)
        assert (
            len(sig.parameters) == 4
        )  # action_id + pattern + correlation_id + state_before (self не считается)
        assert "action_id" in sig.parameters
        assert "pattern" in sig.parameters
        assert "correlation_id" in sig.parameters
        assert "state_before" in sig.parameters
        assert sig.return_annotation is type(None)

        # log_feedback
        sig = inspect.signature(logger.log_feedback)
        assert len(sig.parameters) == 2  # feedback + correlation_id (self не считается)
        assert "feedback" in sig.parameters
        assert "correlation_id" in sig.parameters
        assert sig.return_annotation is type(None)

        # log_tick_start
        sig = inspect.signature(logger.log_tick_start)
        assert len(sig.parameters) == 2  # tick_number + queue_size (self не считается)
        assert "tick_number" in sig.parameters
        assert "queue_size" in sig.parameters
        assert sig.return_annotation is type(None)

        # log_tick_end
        sig = inspect.signature(logger.log_tick_end)
        assert (
            len(sig.parameters) == 3
        )  # tick_number + duration_ms + events_processed (self не считается)
        assert "tick_number" in sig.parameters
        assert "duration_ms" in sig.parameters
        assert "events_processed" in sig.parameters
        assert sig.return_annotation is type(None)

        # log_error
        sig = inspect.signature(logger.log_error)
        assert (
            len(sig.parameters) == 3
        )  # stage + error + correlation_id (self не считается)
        assert "stage" in sig.parameters
        assert "error" in sig.parameters
        assert "correlation_id" in sig.parameters
        assert sig.return_annotation is type(None)

    def test_structured_logger_private_methods(self):
        """Проверка приватных методов StructuredLogger"""
        logger = StructuredLogger(enabled=False)

        # _get_next_correlation_id
        sig = inspect.signature(logger._get_next_correlation_id)
        assert len(sig.parameters) == 0  # только self, который не считается
        assert sig.return_annotation is str

        # _write_log_entry
        sig = inspect.signature(logger._write_log_entry)
        assert len(sig.parameters) == 1  # entry (self не считается)
        assert "entry" in sig.parameters
        assert sig.return_annotation is type(None)

    def test_structured_logger_attributes(self):
        """Проверка атрибутов StructuredLogger"""
        logger = StructuredLogger(log_file="test.log", enabled=False)

        assert hasattr(logger, "log_file")
        assert hasattr(logger, "enabled")
        assert hasattr(logger, "_lock")
        assert hasattr(logger, "_correlation_counter")

        assert logger.log_file == "test.log"
        assert logger.enabled is False
        assert logger._correlation_counter == 0

        # Проверяем, что _lock является Lock
        assert hasattr(logger._lock, "acquire")
        assert hasattr(logger._lock, "release")

    def test_structured_logger_inheritance(self):
        """Проверка наследования StructuredLogger"""
        assert StructuredLogger.__bases__ == (object,)

    def test_structured_logger_docstrings(self):
        """Проверка наличия docstrings"""
        assert StructuredLogger.__doc__ is not None
        assert StructuredLogger.__init__.__doc__ is not None

        logger = StructuredLogger(enabled=False)
        assert logger.log_event.__doc__ is not None
        assert logger.log_meaning.__doc__ is not None
        assert logger.log_decision.__doc__ is not None
        assert logger.log_action.__doc__ is not None
        assert logger.log_feedback.__doc__ is not None
        assert logger.log_tick_start.__doc__ is not None
        assert logger.log_tick_end.__doc__ is not None
        assert logger.log_error.__doc__ is not None

    def test_structured_logger_no_forbidden_methods(self):
        """Проверка отсутствия запрещенных методов в StructuredLogger"""
        logger = StructuredLogger(enabled=False)
        methods = dir(logger)

        forbidden_methods = [
            "optimize",
            "optimization",
            "optimizer",
            "improve",
            "improvement",
            "maximize",
            "minimize",
            "evaluate",
            "evaluation",
            "score",
            "scoring",
            "train",
            "training",
            "gradient",
            "backprop",
            "loss",
            "cost",
            "error",
            "judge",
            "judgment",
            "goal",
            "target",
            "objective",
            "reward",
            "punishment",
            "reinforce",
            "reinforcement",
        ]

        for method in forbidden_methods:
            assert (
                method not in methods
            ), f"StructuredLogger не должен иметь метод {method}"

    def test_structured_logger_architecture_compliance(self):
        """Проверка соответствия архитектуре наблюдаемости"""
        # StructuredLogger должен быть чистым логером наблюдения
        # не должен содержать бизнес-логику или принятие решений

        source_code = inspect.getsource(StructuredLogger)

        forbidden_patterns = [
            "decide",
            "decision.*logic",
            "action.*logic",
            "if.*condition",
            "while.*loop",
            "for.*loop",  # кроме простых итераций
            "state.*change",
            "modify.*state",
            "learning",
            "adaptation",
            "policy",
            "strategy",
        ]

        # Исключаем простые циклы в _write_log_entry и _get_next_correlation_id
        lines = [line.strip() for line in source_code.split("\n") if line.strip()]
        code_lines = [
            line
            for line in lines
            if not line.startswith('"""') and not line.startswith("'''")
        ]

        for pattern in forbidden_patterns:
            matching_lines = [
                line for line in code_lines if pattern.lower() in line.lower()
            ]
            # Разрешаем только комментарии и docstrings
            for line in matching_lines:
                assert any(
                    keyword in line.lower()
                    for keyword in ["#", '"""', "'''", "docstring", "comment", "log_"]
                ), f"Запрещенный паттерн '{pattern}' найден в коде: {line}"

    def test_structured_logger_thread_safety(self):
        """Проверка потокобезопасности StructuredLogger"""
        logger = StructuredLogger(enabled=False)

        # Проверяем наличие блокировки
        assert hasattr(logger, "_lock")

        # Проверяем, что критические методы используют блокировку

        # _get_next_correlation_id должен использовать _lock
        get_corr_source = inspect.getsource(logger._get_next_correlation_id)
        assert "_lock" in get_corr_source

        # _write_log_entry должен использовать _lock
        write_entry_source = inspect.getsource(logger._write_log_entry)
        assert "_lock" in write_entry_source

    def test_structured_logger_jsonl_format_compliance(self):
        """Проверка соответствия формату JSONL"""
        # Все методы логирования должны создавать словари с обязательными полями
        source_code = inspect.getsource(StructuredLogger)

        # Проверяем, что все log_* методы создают entry словари
        assert "entry = {" in source_code

        # Проверяем наличие timestamp в записях
        assert '"timestamp": time.time()' in source_code

        # Проверяем наличие stage в записях
        assert '"stage":' in source_code

    def test_structured_logger_correlation_tracking(self):
        """Проверка системы correlation ID"""
        logger = StructuredLogger(enabled=False)

        # Проверяем наличие счетчика correlation
        assert hasattr(logger, "_correlation_counter")

        # Проверяем метод генерации correlation_id
        assert hasattr(logger, "_get_next_correlation_id")

        # Проверяем, что correlation_id используется во всех стадиях

        # Все log_* методы должны принимать correlation_id
        log_methods = ["log_meaning", "log_decision", "log_action", "log_feedback"]
        for method in log_methods:
            method_source = inspect.getsource(getattr(logger, method))
            assert "correlation_id" in method_source

    def test_structured_logger_stages_defined(self):
        """Проверка определенных стадий обработки"""
        # Ожидаемые стадии из документации
        expected_stages = [
            "event",
            "meaning",
            "decision",
            "action",
            "feedback",
            "tick_start",
            "tick_end",
            "error_",
        ]

        source_code = inspect.getsource(StructuredLogger)

        for stage in expected_stages:
            if stage == "error_":
                assert '"stage": f"error_{stage}"' in source_code
            else:
                assert f'"stage": "{stage}"' in source_code

    def test_structured_logger_imports_structure(self):
        """Проверка структуры импортов"""
        import src.observability.structured_logger as sl_module

        # Проверяем что модуль экспортирует основной класс
        assert hasattr(sl_module, "StructuredLogger")
        assert sl_module.StructuredLogger == StructuredLogger

"""
Статические тесты для ExternalObserver

Проверяем:
- Структуру классов и модулей
- Константы и их значения
- Сигнатуры методов
- Типы возвращаемых значений
- Отсутствие запрещенных методов/атрибутов
- Архитектурные ограничения
"""

import inspect
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.external_observer import (
    ExternalObserver,
    SystemMetrics,
    BehaviorPattern,
    ObservationReport
)


@pytest.mark.static
class TestExternalObserverStatic:
    """Статические тесты для ExternalObserver"""

    def test_external_observer_structure(self):
        """Проверка структуры ExternalObserver"""
        assert hasattr(ExternalObserver, "__init__")
        assert hasattr(ExternalObserver, "observe_from_logs")
        assert hasattr(ExternalObserver, "observe_from_snapshots")
        assert hasattr(ExternalObserver, "save_report")
        assert hasattr(ExternalObserver, "get_observation_history_summary")
        assert hasattr(ExternalObserver, "observation_history")

    def test_external_observer_constants(self):
        """Проверка констант ExternalObserver"""
        observer = ExternalObserver()

        # Проверяем наличие основных атрибутов
        assert hasattr(observer, "logs_directory")
        assert hasattr(observer, "snapshots_directory")
        assert hasattr(observer, "observation_history")

        # Проверяем типы атрибутов
        assert isinstance(observer.logs_directory, Path)
        assert isinstance(observer.snapshots_directory, Path)
        assert isinstance(observer.observation_history, list)

    def test_external_observer_method_signatures(self):
        """Проверка сигнатур методов ExternalObserver"""
        observer = ExternalObserver()

        # observe_from_logs
        sig = inspect.signature(observer.observe_from_logs)
        assert "start_time" in sig.parameters
        assert "end_time" in sig.parameters
        assert sig.parameters["start_time"].default is None
        assert sig.parameters["end_time"].default is None

        # observe_from_snapshots
        sig = inspect.signature(observer.observe_from_snapshots)
        assert "snapshot_paths" in sig.parameters

        # save_report
        sig = inspect.signature(observer.save_report)
        assert "report" in sig.parameters
        assert "output_path" in sig.parameters

        # get_observation_history_summary
        sig = inspect.signature(observer.get_observation_history_summary)
        assert len(sig.parameters) == 1  # только self

    def test_external_observer_return_types(self):
        """Проверка типов возвращаемых значений ExternalObserver"""
        observer = ExternalObserver()

        # observe_from_logs возвращает ObservationReport
        # (для тестирования нужны mock'и внутренних методов)
        with pytest.raises(Exception):  # Ожидаем ошибку без mock'ов
            observer.observe_from_logs()

        # observe_from_snapshots возвращает ObservationReport
        with pytest.raises(Exception):  # Ожидаем ошибку без файлов
            observer.observe_from_snapshots([])

        # save_report возвращает Path или str
        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = observer.save_report(report, temp_path)
            assert isinstance(result, (Path, str))
        finally:
            temp_path.unlink(missing_ok=True)

        # get_observation_history_summary возвращает dict
        result = observer.get_observation_history_summary()
        assert isinstance(result, dict)

    def test_system_metrics_structure(self):
        """Проверка структуры SystemMetrics"""
        metrics = SystemMetrics()

        # Проверяем наличие всех полей
        required_fields = [
            "timestamp", "cycle_count", "uptime_seconds", "memory_entries_count",
            "learning_effectiveness", "adaptation_rate", "decision_success_rate",
            "error_count", "integrity_score", "energy_level",
            "action_count", "event_processing_rate", "state_change_frequency"
        ]

        for field in required_fields:
            assert hasattr(metrics, field), f"Missing field: {field}"

        # Проверяем типы полей по умолчанию
        assert isinstance(metrics.timestamp, float)
        assert isinstance(metrics.cycle_count, int)
        assert isinstance(metrics.uptime_seconds, float)
        assert isinstance(metrics.memory_entries_count, int)
        assert isinstance(metrics.learning_effectiveness, float)
        assert isinstance(metrics.error_count, int)
        assert isinstance(metrics.integrity_score, float)

    def test_behavior_pattern_structure(self):
        """Проверка структуры BehaviorPattern"""
        import time

        pattern = BehaviorPattern(
            pattern_type="test_pattern",
            description="Test description",
            frequency=0.8,
            impact_score=0.7,
            first_observed=time.time(),
            last_observed=time.time(),
            metadata={"test": "value"}
        )

        # Проверяем наличие всех полей
        required_fields = [
            "pattern_type", "description", "frequency", "impact_score",
            "first_observed", "last_observed", "metadata"
        ]

        for field in required_fields:
            assert hasattr(pattern, field), f"Missing field: {field}"

        # Проверяем типы полей
        assert isinstance(pattern.pattern_type, str)
        assert isinstance(pattern.description, str)
        assert isinstance(pattern.frequency, float)
        assert isinstance(pattern.impact_score, float)
        assert isinstance(pattern.first_observed, float)
        assert isinstance(pattern.last_observed, float)
        assert isinstance(pattern.metadata, dict)

    def test_observation_report_structure(self):
        """Проверка структуры ObservationReport"""
        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=SystemMetrics(),
            behavior_patterns=[],
            trends={},
            anomalies=[],
            recommendations=[]
        )

        # Проверяем наличие всех полей
        required_fields = [
            "observation_period", "metrics_summary", "behavior_patterns",
            "trends", "anomalies", "recommendations"
        ]

        for field in required_fields:
            assert hasattr(report, field), f"Missing field: {field}"

        # Проверяем типы полей
        assert isinstance(report.observation_period, tuple)
        assert isinstance(report.metrics_summary, SystemMetrics)
        assert isinstance(report.behavior_patterns, list)
        assert isinstance(report.trends, dict)
        assert isinstance(report.anomalies, list)
        assert isinstance(report.recommendations, list)

        # Проверяем метод to_dict
        assert hasattr(report, "to_dict")
        data = report.to_dict()
        assert isinstance(data, dict)

    def test_external_observer_no_forbidden_patterns(self):
        """Проверка отсутствия запрещенных паттернов в ExternalObserver"""
        source_code = inspect.getsource(ExternalObserver)

        forbidden_patterns = [
            "print(",      # Не используем print
            "eval(",       # Не используем eval
            "exec(",       # Не используем exec
            "import os",   # Не используем os напрямую (кроме Path)
            "import sys",  # Не используем sys напрямую
            "subprocess",  # Не используем subprocess
        ]

        for pattern in forbidden_patterns:
            assert pattern not in source_code, f"Forbidden pattern '{pattern}' found in ExternalObserver"

    def test_external_observer_docstrings(self):
        """Проверка наличия docstrings в ExternalObserver"""
        assert ExternalObserver.__doc__ is not None

        # Проверяем основные методы
        methods_with_docs = [
            "observe_from_logs",
            "observe_from_snapshots",
            "save_report",
            "get_observation_history_summary",
        ]

        for method_name in methods_with_docs:
            method = getattr(ExternalObserver, method_name)
            assert method.__doc__ is not None, f"Missing docstring for {method_name}"

    def test_external_observer_inheritance(self):
        """Проверка наследования ExternalObserver"""
        assert ExternalObserver.__bases__ == (object,)

        # Dataclasses наследуются от object
        assert SystemMetrics.__bases__ == (object,)
        assert BehaviorPattern.__bases__ == (object,)
        assert ObservationReport.__bases__ == (object,)

    def test_dataclass_imports(self):
        """Проверка структуры импортов для dataclasses"""
        import src.observability.external_observer as eo_module

        # Проверяем что модуль экспортирует основные классы
        assert hasattr(eo_module, "ExternalObserver")
        assert hasattr(eo_module, "SystemMetrics")
        assert hasattr(eo_module, "BehaviorPattern")
        assert hasattr(eo_module, "ObservationReport")

        # Проверяем соответствие
        assert eo_module.ExternalObserver == ExternalObserver
        assert eo_module.SystemMetrics == SystemMetrics
        assert eo_module.BehaviorPattern == BehaviorPattern
        assert eo_module.ObservationReport == ObservationReport

    def test_external_observer_constants_immutability(self):
        """Проверка неизменности атрибутов ExternalObserver"""
        observer = ExternalObserver()

        # Запоминаем оригинальные значения
        original_logs_dir = observer.logs_directory
        original_snapshots_dir = observer.snapshots_directory

        # Выполняем некоторые операции (без фактического наблюдения)
        summary = observer.get_observation_history_summary()

        # Проверяем что атрибуты не изменились
        assert observer.logs_directory == original_logs_dir
        assert observer.snapshots_directory == original_snapshots_dir
        assert observer.observation_history == []  # Должен оставаться пустым

    def test_system_metrics_dataclass_behavior(self):
        """Проверка поведения SystemMetrics как dataclass"""
        import time

        # Создаем metrics с параметрами
        timestamp = time.time()
        metrics = SystemMetrics(
            timestamp=timestamp,
            cycle_count=1000,
            energy_level=0.85,
            error_count=5
        )

        assert metrics.timestamp == timestamp
        assert metrics.cycle_count == 1000
        assert metrics.energy_level == 0.85
        assert metrics.error_count == 5

        # Проверяем значения по умолчанию для остальных полей
        assert metrics.uptime_seconds == 0.0
        assert metrics.memory_entries_count == 0
        assert metrics.learning_effectiveness == 0.0
        assert metrics.integrity_score == 1.0  # Значение по умолчанию

    def test_behavior_pattern_dataclass_behavior(self):
        """Проверка поведения BehaviorPattern как dataclass"""
        import time

        timestamp = time.time()
        pattern = BehaviorPattern(
            pattern_type="learning_cycle",
            description="Regular learning cycles",
            frequency=0.75,
            impact_score=0.8,
            first_observed=timestamp - 100,
            last_observed=timestamp,
            metadata={"confidence": 0.9}
        )

        assert pattern.pattern_type == "learning_cycle"
        assert pattern.frequency == 0.75
        assert pattern.impact_score == 0.8
        assert pattern.metadata == {"confidence": 0.9}

    def test_observation_report_dataclass_behavior(self):
        """Проверка поведения ObservationReport как dataclass"""
        import time

        start_time = time.time() - 100
        end_time = time.time()

        report = ObservationReport(
            observation_period=(start_time, end_time),
            metrics_summary=SystemMetrics(cycle_count=100),
            behavior_patterns=[],
            trends={"energy_level": "stable"},
            anomalies=[],
            recommendations=["System performing well"]
        )

        assert report.observation_period == (start_time, end_time)
        assert report.trends == {"energy_level": "stable"}
        assert report.recommendations == ["System performing well"]

        # Проверяем метод to_dict
        data = report.to_dict()
        assert data["observation_period"] == (start_time, end_time)
        assert data["trends"] == {"energy_level": "stable"}
        assert data["recommendations"] == ["System performing well"]

    def test_external_observer_private_methods(self):
        """Проверка приватных методов ExternalObserver"""
        observer = ExternalObserver()

        # Проверяем наличие основных приватных методов
        private_methods = [
            "_extract_metrics_from_logs",
            "_analyze_behavior_patterns",
            "_calculate_trends",
            "_detect_anomalies",
            "_generate_recommendations",
            "_extract_metrics_from_snapshots",
            "_analyze_snapshot_patterns",
            "_calculate_snapshot_trends",
            "_detect_snapshot_anomalies",
            "_generate_snapshot_recommendations",
        ]

        for method_name in private_methods:
            assert hasattr(observer, method_name), f"Missing private method: {method_name}"
            method = getattr(observer, method_name)
            assert method.__name__.startswith("_"), f"Method {method_name} should be private"

    def test_observation_report_to_dict_completeness(self):
        """Проверка полноты метода to_dict в ObservationReport"""
        import time

        # Создаем полный отчет
        pattern = BehaviorPattern(
            pattern_type="test",
            description="Test pattern",
            frequency=0.8,
            impact_score=0.7,
            first_observed=time.time(),
            last_observed=time.time(),
        )

        report = ObservationReport(
            observation_period=(1000.0, 2000.0),
            metrics_summary=SystemMetrics(
                cycle_count=100,
                uptime_seconds=3600.0,
                learning_effectiveness=0.85,
                error_count=3
            ),
            behavior_patterns=[pattern],
            trends={"energy_level": "stable"},
            anomalies=[{"type": "high_error_rate", "severity": "medium"}],
            recommendations=["Check error handling"]
        )

        data = report.to_dict()

        # Проверяем что все поля включены
        assert "observation_period" in data
        assert "metrics_summary" in data
        assert "behavior_patterns" in data
        assert "trends" in data
        assert "anomalies" in data
        assert "recommendations" in data

        # Проверяем содержимое metrics_summary
        metrics_data = data["metrics_summary"]
        assert metrics_data["cycle_count"] == 100
        assert metrics_data["uptime_seconds"] == 3600.0
        assert metrics_data["learning_effectiveness"] == 0.85
        assert metrics_data["error_count"] == 3

        # Проверяем behavior_patterns
        assert len(data["behavior_patterns"]) == 1
        pattern_data = data["behavior_patterns"][0]
        assert pattern_data["pattern_type"] == "test"
        assert pattern_data["frequency"] == 0.8
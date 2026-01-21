"""
Статические тесты для TechnicalBehaviorMonitor

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

from src.technical_monitor import (
    TechnicalBehaviorMonitor,
    TechnicalSnapshot,
    TechnicalReport,
    ComponentInterface,
    MemoryInterface,
    DecisionEngineInterface
)
from abc import ABC


@pytest.mark.static
class TestTechnicalMonitorStatic:
    """Статические тесты для TechnicalBehaviorMonitor"""

    def test_technical_monitor_structure(self):
        """Проверка структуры TechnicalBehaviorMonitor"""
        monitor = TechnicalBehaviorMonitor()
        assert hasattr(TechnicalBehaviorMonitor, "__init__")
        assert hasattr(TechnicalBehaviorMonitor, "capture_system_snapshot")
        assert hasattr(TechnicalBehaviorMonitor, "analyze_snapshot")
        assert hasattr(TechnicalBehaviorMonitor, "save_report")
        assert hasattr(TechnicalBehaviorMonitor, "load_report")
        assert hasattr(TechnicalBehaviorMonitor, "get_trends")

        # Проверяем атрибуты экземпляра
        assert hasattr(monitor, "report_history")
        assert hasattr(monitor, "max_history_size")

    def test_technical_monitor_constants(self):
        """Проверка констант TechnicalBehaviorMonitor"""
        monitor = TechnicalBehaviorMonitor()

        # Проверяем наличие основных атрибутов
        assert hasattr(monitor, "max_history_size")

        # max_history_size должен быть положительным
        assert monitor.max_history_size > 0
        assert isinstance(monitor.max_history_size, int)

    def test_technical_monitor_method_signatures(self):
        """Проверка сигнатур методов TechnicalBehaviorMonitor"""
        monitor = TechnicalBehaviorMonitor()

        # capture_system_snapshot
        sig = inspect.signature(TechnicalBehaviorMonitor.capture_system_snapshot)
        assert len(sig.parameters) == 6  # self + 5 параметров
        assert "self_state" in sig.parameters
        assert "memory" in sig.parameters
        assert "learning_engine" in sig.parameters
        assert "adaptation_manager" in sig.parameters
        assert "decision_engine" in sig.parameters

        # analyze_snapshot
        sig = inspect.signature(monitor.analyze_snapshot)
        assert len(sig.parameters) == 2  # self + snapshot
        assert "snapshot" in sig.parameters

        # save_report
        sig = inspect.signature(monitor.save_report)
        assert len(sig.parameters) == 3  # self + report + file_path
        assert "report" in sig.parameters
        assert "file_path" in sig.parameters

        # load_report
        sig = inspect.signature(monitor.load_report)
        assert len(sig.parameters) == 2  # self + file_path
        assert "file_path" in sig.parameters

        # get_trends
        sig = inspect.signature(monitor.get_trends)
        assert "hours" in sig.parameters

    def test_technical_monitor_return_types(self):
        """Проверка типов возвращаемых значений TechnicalBehaviorMonitor"""
        monitor = TechnicalBehaviorMonitor()

        # capture_system_snapshot возвращает TechnicalSnapshot
        # (нужны mock объекты для тестирования)
        mock_self_state = Mock()
        mock_memory = Mock()
        mock_learning = Mock()
        mock_adaptation = Mock()
        mock_decision = Mock()

        # Настраиваем mock'и для корректной работы
        mock_self_state.__dict__.update({
            'life_id': 'test', 'age': 100.0, 'ticks': 1000,
            'energy': 0.8, 'stability': 0.9, 'integrity': 0.85,
            'adaptation_level': 0.7
        })
        mock_memory.get_statistics.return_value = {'total_entries': 10}
        mock_learning.get_parameters.return_value = {'learning_rate': 0.7}
        mock_adaptation.get_parameters.return_value = {'adaptation_rate': 0.6}
        mock_decision.get_recent_decisions.return_value = []
        mock_decision.get_statistics.return_value = {'total_decisions': 0}

        snapshot = monitor.capture_system_snapshot(
            mock_self_state, mock_memory, mock_learning, mock_adaptation, mock_decision
        )
        assert isinstance(snapshot, TechnicalSnapshot)

        # analyze_snapshot возвращает TechnicalReport
        report = monitor.analyze_snapshot(snapshot)
        assert isinstance(report, TechnicalReport)

        # save_report возвращает bool или str (путь к файлу)
        # load_report возвращает TechnicalReport или None

        # get_trends возвращает dict
        trends = monitor.get_trends(hours=1)
        assert isinstance(trends, dict)

    def test_technical_snapshot_structure(self):
        """Проверка структуры TechnicalSnapshot"""
        snapshot = TechnicalSnapshot()

        # Проверяем наличие всех полей
        assert hasattr(snapshot, "timestamp")
        assert hasattr(snapshot, "self_state")
        assert hasattr(snapshot, "memory_stats")
        assert hasattr(snapshot, "learning_params")
        assert hasattr(snapshot, "adaptation_params")
        assert hasattr(snapshot, "decision_history")
        assert hasattr(snapshot, "performance_metrics")

        # Проверяем типы полей
        assert isinstance(snapshot.timestamp, float)
        assert isinstance(snapshot.self_state, dict)
        assert isinstance(snapshot.memory_stats, dict)
        assert isinstance(snapshot.learning_params, dict)
        assert isinstance(snapshot.adaptation_params, dict)
        assert isinstance(snapshot.decision_history, list)
        assert isinstance(snapshot.performance_metrics, dict)

    def test_technical_report_structure(self):
        """Проверка структуры TechnicalReport"""
        report = TechnicalReport()

        # Проверяем наличие всех полей
        assert hasattr(report, "timestamp")
        assert hasattr(report, "snapshot")
        assert hasattr(report, "performance")
        assert hasattr(report, "stability")
        assert hasattr(report, "adaptability")
        assert hasattr(report, "integrity")
        assert hasattr(report, "overall_assessment")

        # Проверяем типы полей
        assert isinstance(report.timestamp, float)
        assert isinstance(report.snapshot, TechnicalSnapshot)
        assert isinstance(report.performance, dict)
        assert isinstance(report.stability, dict)
        assert isinstance(report.adaptability, dict)
        assert isinstance(report.integrity, dict)
        assert isinstance(report.overall_assessment, dict)

    def test_interface_classes_structure(self):
        """Проверка структуры интерфейсных классов"""
        # ComponentInterface
        assert hasattr(ComponentInterface, "get_parameters")
        assert hasattr(ComponentInterface, "validate_state")

        # Проверяем что методы абстрактные
        assert hasattr(ComponentInterface.get_parameters, '__isabstractmethod__')
        assert hasattr(ComponentInterface.validate_state, '__isabstractmethod__')

        # MemoryInterface
        assert hasattr(MemoryInterface, "get_statistics")
        assert hasattr(MemoryInterface, "validate_integrity")

        assert hasattr(MemoryInterface.get_statistics, '__isabstractmethod__')
        assert hasattr(MemoryInterface.validate_integrity, '__isabstractmethod__')

        # DecisionEngineInterface
        assert hasattr(DecisionEngineInterface, "get_recent_decisions")
        assert hasattr(DecisionEngineInterface, "get_statistics")

        assert hasattr(DecisionEngineInterface.get_recent_decisions, '__isabstractmethod__')
        assert hasattr(DecisionEngineInterface.get_statistics, '__isabstractmethod__')

    def test_technical_monitor_no_forbidden_patterns(self):
        """Проверка отсутствия запрещенных паттернов в TechnicalBehaviorMonitor"""
        source_code = inspect.getsource(TechnicalBehaviorMonitor)

        forbidden_patterns = [
            "print(",      # Не используем print
            "eval(",       # Не используем eval
            "exec(",       # Не используем exec
            "import os",   # Не используем os напрямую (кроме Path)
            "import sys",  # Не используем sys напрямую
            "import json", # JSON используется только для сериализации
        ]

        for pattern in forbidden_patterns:
            assert pattern not in source_code, f"Forbidden pattern '{pattern}' found in TechnicalBehaviorMonitor"

    def test_technical_monitor_docstrings(self):
        """Проверка наличия docstrings в TechnicalBehaviorMonitor"""
        assert TechnicalBehaviorMonitor.__doc__ is not None

        # Проверяем основные методы
        methods_with_docs = [
            "capture_system_snapshot",
            "analyze_snapshot",
            "save_report",
            "load_report",
            "get_trends",
        ]

        for method_name in methods_with_docs:
            method = getattr(TechnicalBehaviorMonitor, method_name)
            assert method.__doc__ is not None, f"Missing docstring for {method_name}"

    def test_technical_monitor_inheritance(self):
        """Проверка наследования TechnicalBehaviorMonitor"""
        assert TechnicalBehaviorMonitor.__bases__ == (object,)

        # Интерфейсы наследуются от ABC
        assert ComponentInterface.__bases__ == (ABC,)
        assert MemoryInterface.__bases__ == (ABC,)
        assert DecisionEngineInterface.__bases__ == (ABC,)

    def test_dataclass_imports(self):
        """Проверка структуры импортов для dataclasses"""
        import src.technical_monitor as tm_module

        # Проверяем что модуль экспортирует основные классы
        assert hasattr(tm_module, "TechnicalBehaviorMonitor")
        assert hasattr(tm_module, "TechnicalSnapshot")
        assert hasattr(tm_module, "TechnicalReport")
        assert hasattr(tm_module, "ComponentInterface")
        assert hasattr(tm_module, "MemoryInterface")
        assert hasattr(tm_module, "DecisionEngineInterface")

        # Проверяем соответствие
        assert tm_module.TechnicalBehaviorMonitor == TechnicalBehaviorMonitor
        assert tm_module.TechnicalSnapshot == TechnicalSnapshot
        assert tm_module.TechnicalReport == TechnicalReport

    def test_technical_monitor_attributes_immutability(self):
        """Проверка неизменности атрибутов TechnicalBehaviorMonitor"""
        monitor = TechnicalBehaviorMonitor()

        # Запоминаем оригинальные значения
        original_max_history = monitor.max_history_size

        # Выполняем некоторые операции
        mock_self_state = Mock()
        mock_memory = Mock()
        mock_learning = Mock()
        mock_adaptation = Mock()
        mock_decision = Mock()

        mock_self_state.__dict__.update({'life_id': 'test', 'age': 100.0, 'ticks': 1000})
        mock_memory.get_statistics.return_value = {}
        mock_learning.get_parameters.return_value = {}
        mock_adaptation.get_parameters.return_value = {}
        mock_decision.get_recent_decisions.return_value = []
        mock_decision.get_statistics.return_value = {}

        snapshot = monitor.capture_system_snapshot(
            mock_self_state, mock_memory, mock_learning, mock_adaptation, mock_decision
        )
        report = monitor.analyze_snapshot(snapshot)
        monitor.report_history.append(report)

        # Проверяем что атрибуты не изменились
        assert monitor.max_history_size == original_max_history

    def test_technical_snapshot_dataclass_behavior(self):
        """Проверка поведения TechnicalSnapshot как dataclass"""
        import time

        # Создаем snapshot с параметрами
        timestamp = time.time()
        snapshot = TechnicalSnapshot(
            timestamp=timestamp,
            self_state={"energy": 0.8},
            memory_stats={"total_entries": 10}
        )

        assert snapshot.timestamp == timestamp
        assert snapshot.self_state == {"energy": 0.8}
        assert snapshot.memory_stats == {"total_entries": 10}

        # Проверяем значения по умолчанию для остальных полей
        assert isinstance(snapshot.learning_params, dict)
        assert isinstance(snapshot.adaptation_params, dict)
        assert isinstance(snapshot.decision_history, list)
        assert isinstance(snapshot.performance_metrics, dict)

    def test_technical_report_dataclass_behavior(self):
        """Проверка поведения TechnicalReport как dataclass"""
        import time

        timestamp = time.time()
        snapshot = TechnicalSnapshot()

        report = TechnicalReport(
            timestamp=timestamp,
            snapshot=snapshot,
            performance={"overall_performance": 0.8},
            overall_assessment={"overall_score": 0.75}
        )

        assert report.timestamp == timestamp
        assert report.snapshot == snapshot
        assert report.performance == {"overall_performance": 0.8}
        assert report.overall_assessment == {"overall_score": 0.75}

        # Проверяем значения по умолчанию
        assert isinstance(report.stability, dict)
        assert isinstance(report.adaptability, dict)
        assert isinstance(report.integrity, dict)
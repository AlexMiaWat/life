"""
Статические тесты для ComponentMonitor

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

from src.observability.component_monitor import (
    ComponentMonitor,
    ComponentStats,
    SystemComponentStats,
)


@pytest.mark.static
class TestComponentMonitorStatic:
    """Статические тесты для ComponentMonitor"""

    def test_component_monitor_structure(self):
        """Проверка структуры ComponentMonitor"""
        assert hasattr(ComponentMonitor, "__init__")
        assert hasattr(ComponentMonitor, "collect_component_stats")
        assert hasattr(ComponentMonitor, "get_last_system_stats")
        assert hasattr(ComponentMonitor, "enable_monitoring")
        assert hasattr(ComponentMonitor, "disable_monitoring")

        # Проверяем сигнатуру метода collect_component_stats
        sig = inspect.signature(ComponentMonitor.collect_component_stats)
        assert 'self_state' in sig.parameters

    def test_component_stats_structure(self):
        """Проверка структуры ComponentStats"""
        assert hasattr(ComponentStats, "__init__")
        assert hasattr(ComponentStats, "to_dict")

        # Проверяем наличие всех полей
        stats = ComponentStats(component_name="test")
        assert hasattr(stats, 'component_name')
        assert hasattr(stats, 'timestamp')
        assert hasattr(stats, 'queue_size')
        assert hasattr(stats, 'memory_usage')
        assert hasattr(stats, 'active_threads')
        assert hasattr(stats, 'operations_count')
        assert hasattr(stats, 'error_count')
        assert hasattr(stats, 'success_count')
        assert hasattr(stats, 'avg_operation_time')
        assert hasattr(stats, 'last_operation_time')

    def test_system_component_stats_structure(self):
        """Проверка структуры SystemComponentStats"""
        assert hasattr(SystemComponentStats, "__init__")
        assert hasattr(SystemComponentStats, "to_dict")

        # Проверяем наличие всех полей
        stats = SystemComponentStats()
        memory_fields = ['memory_episodic_size', 'memory_archive_size', 'memory_recent_events']
        for field in memory_fields:
            assert hasattr(stats, field)

        learning_fields = ['learning_params_count', 'learning_operations']
        for field in learning_fields:
            assert hasattr(stats, field)

        adaptation_fields = ['adaptation_params_count', 'adaptation_operations']
        for field in adaptation_fields:
            assert hasattr(stats, field)

        decision_fields = ['decision_queue_size', 'decision_operations']
        for field in decision_fields:
            assert hasattr(stats, field)

        action_fields = ['action_queue_size', 'action_operations']
        for field in action_fields:
            assert hasattr(stats, field)

        environment_fields = ['environment_event_queue_size', 'environment_pending_events']
        for field in environment_fields:
            assert hasattr(stats, field)

        intelligence_fields = ['intelligence_processed_sources']
        for field in intelligence_fields:
            assert hasattr(stats, field)

    def test_component_monitor_constants(self):
        """Проверка констант ComponentMonitor"""
        monitor = ComponentMonitor()

        # Проверяем наличие основных атрибутов
        assert hasattr(monitor, "monitoring_enabled")
        assert hasattr(monitor, "last_system_stats")

        # Проверяем начальные значения
        assert monitor.monitoring_enabled is True
        assert monitor.last_system_stats is None

    def test_component_stats_constants(self):
        """Проверка констант ComponentStats"""
        stats = ComponentStats(component_name="test")

        # Проверяем начальные значения полей
        assert stats.component_name == "test"
        assert stats.queue_size == 0
        assert stats.memory_usage == 0
        assert stats.active_threads == 0
        assert stats.operations_count == 0
        assert stats.error_count == 0
        assert stats.success_count == 0
        assert stats.avg_operation_time == 0.0
        assert stats.last_operation_time == 0.0

    def test_system_component_stats_constants(self):
        """Проверка констант SystemComponentStats"""
        stats = SystemComponentStats()

        # Проверяем начальные значения всех полей
        assert stats.memory_episodic_size == 0
        assert stats.memory_archive_size == 0
        assert stats.memory_recent_events == 0
        assert stats.learning_params_count == 0
        assert stats.learning_operations == 0
        assert stats.adaptation_params_count == 0
        assert stats.adaptation_operations == 0
        assert stats.decision_queue_size == 0
        assert stats.decision_operations == 0
        assert stats.action_queue_size == 0
        assert stats.action_operations == 0
        assert stats.environment_event_queue_size == 0
        assert stats.environment_pending_events == 0
        assert stats.intelligence_processed_sources == 0

    def test_method_signatures(self):
        """Проверка сигнатур методов"""
        # ComponentMonitor методы
        sig = inspect.signature(ComponentMonitor.__init__)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(ComponentMonitor.collect_component_stats)
        assert len(sig.parameters) == 2  # self, self_state

        sig = inspect.signature(ComponentMonitor.get_last_system_stats)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(ComponentMonitor.enable_monitoring)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(ComponentMonitor.disable_monitoring)
        assert len(sig.parameters) == 1  # только self

        # ComponentStats методы
        sig = inspect.signature(ComponentStats.__init__)
        assert 'component_name' in sig.parameters

        sig = inspect.signature(ComponentStats.to_dict)
        assert len(sig.parameters) == 1  # только self

        # SystemComponentStats методы
        sig = inspect.signature(SystemComponentStats.__init__)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(SystemComponentStats.to_dict)
        assert len(sig.parameters) == 1  # только self

    def test_return_types(self):
        """Проверка типов возвращаемых значений"""
        monitor = ComponentMonitor()
        mock_state = Mock()

        # Проверяем тип возвращаемого значения collect_component_stats
        result = monitor.collect_component_stats(mock_state)
        assert isinstance(result, SystemComponentStats)

        # Проверяем тип возвращаемого значения get_last_system_stats
        result = monitor.get_last_system_stats()
        assert result is None or isinstance(result, SystemComponentStats)

        # Проверяем тип возвращаемого значения to_dict
        component_stats = ComponentStats(component_name="test")
        result = component_stats.to_dict()
        assert isinstance(result, dict)

        system_stats = SystemComponentStats()
        result = system_stats.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_structures(self):
        """Проверка структуры возвращаемых словарей to_dict"""
        # ComponentStats
        component_stats = ComponentStats(component_name="test")
        data = component_stats.to_dict()

        expected_keys = [
            'component_name', 'timestamp', 'queue_size', 'memory_usage',
            'active_threads', 'operations_count', 'error_count', 'success_count',
            'avg_operation_time', 'last_operation_time'
        ]

        for key in expected_keys:
            assert key in data

        # SystemComponentStats
        system_stats = SystemComponentStats()
        data = system_stats.to_dict()

        expected_keys = [
            'timestamp', 'memory_episodic_size', 'memory_archive_size', 'memory_recent_events',
            'learning_params_count', 'learning_operations', 'adaptation_params_count',
            'adaptation_operations', 'decision_queue_size', 'decision_operations',
            'action_queue_size', 'action_operations', 'environment_event_queue_size',
            'environment_pending_events', 'intelligence_processed_sources'
        ]

        for key in expected_keys:
            assert key in data

    def test_architecture_constraints(self):
        """Проверка архитектурных ограничений"""
        monitor = ComponentMonitor()

        # Проверяем отсутствие запрещенных методов/атрибутов
        forbidden_attrs = ['interpret', 'evaluate', 'analyze', 'consciousness', 'awareness']
        for attr in forbidden_attrs:
            assert not hasattr(monitor, attr), f"Найден запрещенный атрибут: {attr}"

        # Проверяем пассивность - отсутствие методов изменения состояния системы
        dangerous_methods = ['modify', 'change', 'update_system', 'inject']
        for method in dangerous_methods:
            assert not hasattr(monitor, method), f"Найден опасный метод: {method}"

    def test_monitoring_control(self):
        """Проверка контроля мониторинга"""
        monitor = ComponentMonitor()

        # По умолчанию мониторинг включен
        assert monitor.monitoring_enabled is True

        # Проверяем методы включения/выключения
        monitor.disable_monitoring()
        assert monitor.monitoring_enabled is False

        monitor.enable_monitoring()
        assert monitor.monitoring_enabled is True

    def test_error_handling(self):
        """Проверка обработки ошибок в статическом контексте"""
        monitor = ComponentMonitor()

        # Проверяем что метод не выбрасывает исключения при None
        try:
            result = monitor.collect_component_stats(None)
            assert isinstance(result, SystemComponentStats)
        except Exception as e:
            pytest.fail(f"Метод collect_component_stats не должен выбрасывать исключения при None: {e}")

    def test_passive_monitoring(self):
        """Проверка пассивности мониторинга"""
        monitor = ComponentMonitor()
        mock_state = Mock()

        # Метод должен только читать данные, не изменять состояние
        original_enabled = monitor.monitoring_enabled
        monitor.collect_component_stats(mock_state)

        # Состояние не должно измениться
        assert monitor.monitoring_enabled == original_enabled
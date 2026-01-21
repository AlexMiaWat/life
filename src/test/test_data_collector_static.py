"""
Статические тесты для DataCollector

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

from src.observability.data_collector import (
    DataCollector,
    ObservationData,
)


@pytest.mark.static
class TestDataCollectorStatic:
    """Статические тесты для DataCollector"""

    def test_data_collector_structure(self):
        """Проверка структуры DataCollector"""
        assert hasattr(DataCollector, "__init__")
        assert hasattr(DataCollector, "collect_state_data")
        assert hasattr(DataCollector, "collect_component_data")
        assert hasattr(DataCollector, "get_recent_data")
        assert hasattr(DataCollector, "get_data_count")
        assert hasattr(DataCollector, "clear_data")
        assert hasattr(DataCollector, "enable_collection")
        assert hasattr(DataCollector, "disable_collection")
        assert hasattr(DataCollector, "flush")

        # Проверяем сигнатуры методов
        sig = inspect.signature(DataCollector.collect_state_data)
        assert 'state_snapshot' in sig.parameters

        sig = inspect.signature(DataCollector.collect_component_data)
        assert 'component_stats' in sig.parameters

    def test_observation_data_structure(self):
        """Проверка структуры ObservationData"""
        assert hasattr(ObservationData, "__init__")
        assert hasattr(ObservationData, "to_dict")

        # Проверяем наличие всех полей
        data = ObservationData()
        assert hasattr(data, 'timestamp')
        assert hasattr(data, 'data_type')
        assert hasattr(data, 'data')

    def test_data_collector_constants(self):
        """Проверка констант DataCollector"""
        collector = DataCollector()

        # Проверяем наличие основных атрибутов
        assert hasattr(collector, "storage_path")
        assert hasattr(collector, "collection_enabled")
        assert hasattr(collector, "_buffer")
        assert hasattr(collector, "_buffer_size")

        # Проверяем начальные значения
        assert collector.collection_enabled is True
        assert isinstance(collector._buffer, list)
        assert collector._buffer_size == 100

    def test_observation_data_constants(self):
        """Проверка констант ObservationData"""
        data = ObservationData()

        # Проверяем начальные значения полей
        assert data.data_type == ""
        assert isinstance(data.data, dict)
        assert len(data.data) == 0

    def test_method_signatures(self):
        """Проверка сигнатур методов"""
        # DataCollector методы
        sig = inspect.signature(DataCollector.__init__)
        assert 'storage_path' in sig.parameters

        sig = inspect.signature(DataCollector.collect_state_data)
        assert len(sig.parameters) == 2  # self, state_snapshot

        sig = inspect.signature(DataCollector.collect_component_data)
        assert len(sig.parameters) == 2  # self, component_stats

        sig = inspect.signature(DataCollector.get_recent_data)
        assert 'data_type' in sig.parameters
        assert 'limit' in sig.parameters

        sig = inspect.signature(DataCollector.get_data_count)
        assert 'data_type' in sig.parameters

        sig = inspect.signature(DataCollector.clear_data)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(DataCollector.enable_collection)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(DataCollector.disable_collection)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(DataCollector.flush)
        assert len(sig.parameters) == 1  # только self

        # ObservationData методы
        sig = inspect.signature(ObservationData.__init__)
        # Проверяем что есть параметры с значениями по умолчанию

        sig = inspect.signature(ObservationData.to_dict)
        assert len(sig.parameters) == 1  # только self

    def test_return_types(self):
        """Проверка типов возвращаемых значений"""
        collector = DataCollector()
        mock_snapshot = Mock()
        mock_stats = Mock()

        # Проверяем тип возвращаемого значения collect_state_data
        collector.collect_state_data(mock_snapshot)  # void method

        # Проверяем тип возвращаемого значения collect_component_data
        collector.collect_component_data(mock_stats)  # void method

        # Проверяем тип возвращаемого значения get_recent_data
        result = collector.get_recent_data()
        assert isinstance(result, list)

        # Проверяем тип возвращаемого значения get_data_count
        result = collector.get_data_count()
        assert isinstance(result, int)

        # Проверяем тип возвращаемого значения to_dict
        data = ObservationData()
        result = data.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_structure(self):
        """Проверка структуры возвращаемого словаря to_dict"""
        data = ObservationData(data_type="test", data={"key": "value"})
        result = data.to_dict()

        expected_keys = ['timestamp', 'data_type', 'data']
        for key in expected_keys:
            assert key in result

        assert result['data_type'] == "test"
        assert result['data'] == {"key": "value"}

    def test_architecture_constraints(self):
        """Проверка архитектурных ограничений"""
        collector = DataCollector()

        # Проверяем отсутствие запрещенных методов/атрибутов
        forbidden_attrs = ['interpret', 'evaluate', 'analyze', 'consciousness', 'awareness']
        for attr in forbidden_attrs:
            assert not hasattr(collector, attr), f"Найден запрещенный атрибут: {attr}"

        # Проверяем пассивность - отсутствие методов изменения состояния системы
        dangerous_methods = ['modify', 'change', 'update_system', 'inject']
        for method in dangerous_methods:
            assert not hasattr(collector, method), f"Найден опасный метод: {method}"

    def test_collection_control(self):
        """Проверка контроля сбора данных"""
        collector = DataCollector()

        # По умолчанию сбор включен
        assert collector.collection_enabled is True

        # Проверяем методы включения/выключения
        collector.disable_collection()
        assert collector.collection_enabled is False

        collector.enable_collection()
        assert collector.collection_enabled is True

    def test_buffer_management(self):
        """Проверка управления буфером"""
        collector = DataCollector()

        # Проверяем начальное состояние буфера
        assert len(collector._buffer) == 0

        # Проверяем размер буфера
        assert collector._buffer_size == 100

    def test_storage_path_handling(self):
        """Проверка обработки пути хранения"""
        collector = DataCollector(storage_path="test/path.jsonl")

        # Проверяем что путь преобразуется в Path
        assert hasattr(collector.storage_path, 'exists')  # Path object methods

    def test_error_handling(self):
        """Проверка обработки ошибок в статическом контексте"""
        collector = DataCollector()

        # Проверяем что методы не выбрасывают исключения при None
        try:
            collector.collect_state_data(None)
            collector.collect_component_data(None)
            result = collector.get_recent_data()
            assert isinstance(result, list)
        except Exception as e:
            pytest.fail(f"Методы не должны выбрасывать исключения при None: {e}")

    def test_passive_collection(self):
        """Проверка пассивности сбора данных"""
        collector = DataCollector()
        mock_data = Mock()

        # Методы должны только собирать данные, не изменять состояние системы
        original_enabled = collector.collection_enabled
        collector.collect_state_data(mock_data)
        collector.collect_component_data(mock_data)

        # Состояние не должно измениться
        assert collector.collection_enabled == original_enabled
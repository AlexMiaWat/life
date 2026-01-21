"""
Статические тесты для StateTracker

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

from src.observability.state_tracker import (
    StateTracker,
    StateSnapshot,
)


@pytest.mark.static
class TestStateTrackerStatic:
    """Статические тесты для StateTracker"""

    def test_state_tracker_structure(self):
        """Проверка структуры StateTracker"""
        assert hasattr(StateTracker, "__init__")
        assert hasattr(StateTracker, "collect_state_data")
        assert hasattr(StateTracker, "get_last_snapshot")
        assert hasattr(StateTracker, "enable_collection")
        assert hasattr(StateTracker, "disable_collection")

        # Проверяем сигнатуру метода collect_state_data
        sig = inspect.signature(StateTracker.collect_state_data)
        assert 'self_state' in sig.parameters

    def test_state_snapshot_structure(self):
        """Проверка структуры StateSnapshot"""
        assert hasattr(StateSnapshot, "__init__")
        assert hasattr(StateSnapshot, "to_dict")

        # Проверяем наличие всех полей
        snapshot = StateSnapshot()
        assert hasattr(snapshot, 'timestamp')
        assert hasattr(snapshot, 'energy')
        assert hasattr(snapshot, 'stability')
        assert hasattr(snapshot, 'integrity')
        assert hasattr(snapshot, 'fatigue')
        assert hasattr(snapshot, 'tension')
        assert hasattr(snapshot, 'age')
        assert hasattr(snapshot, 'subjective_time')
        assert hasattr(snapshot, 'memory_size')
        assert hasattr(snapshot, 'recent_events_count')
        assert hasattr(snapshot, 'action_count')
        assert hasattr(snapshot, 'decision_count')
        assert hasattr(snapshot, 'feedback_count')
        assert hasattr(snapshot, 'learning_params_count')
        assert hasattr(snapshot, 'adaptation_params_count')

    def test_state_tracker_constants(self):
        """Проверка констант StateTracker"""
        tracker = StateTracker()

        # Проверяем наличие основных атрибутов
        assert hasattr(tracker, "last_snapshot")
        assert hasattr(tracker, "collection_enabled")

        # Проверяем начальные значения
        assert tracker.collection_enabled is True
        assert tracker.last_snapshot is None

    def test_state_snapshot_constants(self):
        """Проверка констант StateSnapshot"""
        snapshot = StateSnapshot()

        # Проверяем начальные значения полей
        assert snapshot.energy == 0.0
        assert snapshot.stability == 0.0
        assert snapshot.integrity == 0.0
        assert snapshot.fatigue == 0.0
        assert snapshot.tension == 0.0
        assert snapshot.age == 0.0
        assert snapshot.subjective_time == 0.0
        assert snapshot.memory_size == 0
        assert snapshot.recent_events_count == 0
        assert snapshot.action_count == 0
        assert snapshot.decision_count == 0
        assert snapshot.feedback_count == 0
        assert snapshot.learning_params_count == 0
        assert snapshot.adaptation_params_count == 0

    def test_method_signatures(self):
        """Проверка сигнатур методов"""
        # StateTracker методы
        sig = inspect.signature(StateTracker.__init__)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(StateTracker.collect_state_data)
        assert len(sig.parameters) == 2  # self, self_state

        sig = inspect.signature(StateTracker.get_last_snapshot)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(StateTracker.enable_collection)
        assert len(sig.parameters) == 1  # только self

        sig = inspect.signature(StateTracker.disable_collection)
        assert len(sig.parameters) == 1  # только self

        # StateSnapshot методы
        sig = inspect.signature(StateSnapshot.__init__)
        # Проверяем что есть много параметров с значениями по умолчанию
        assert len(sig.parameters) > 10

        sig = inspect.signature(StateSnapshot.to_dict)
        assert len(sig.parameters) == 1  # только self

    def test_return_types(self):
        """Проверка типов возвращаемых значений"""
        tracker = StateTracker()
        mock_state = Mock()

        # Проверяем тип возвращаемого значения collect_state_data
        result = tracker.collect_state_data(mock_state)
        assert isinstance(result, StateSnapshot)

        # Проверяем тип возвращаемого значения get_last_snapshot
        result = tracker.get_last_snapshot()
        assert result is None or isinstance(result, StateSnapshot)

        # Проверяем тип возвращаемого значения to_dict
        snapshot = StateSnapshot()
        result = snapshot.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_structure(self):
        """Проверка структуры возвращаемого словаря to_dict"""
        snapshot = StateSnapshot()
        data = snapshot.to_dict()

        expected_keys = [
            'timestamp', 'energy', 'stability', 'integrity', 'fatigue', 'tension',
            'age', 'subjective_time', 'memory_size', 'recent_events_count',
            'action_count', 'decision_count', 'feedback_count',
            'learning_params_count', 'adaptation_params_count'
        ]

        for key in expected_keys:
            assert key in data

    def test_architecture_constraints(self):
        """Проверка архитектурных ограничений"""
        tracker = StateTracker()

        # Проверяем отсутствие запрещенных методов/атрибутов
        forbidden_attrs = ['interpret', 'evaluate', 'analyze', 'consciousness', 'awareness']
        for attr in forbidden_attrs:
            assert not hasattr(tracker, attr), f"Найден запрещенный атрибут: {attr}"

        # Проверяем пассивность - отсутствие методов изменения состояния системы
        dangerous_methods = ['modify', 'change', 'update_system', 'inject']
        for method in dangerous_methods:
            assert not hasattr(tracker, method), f"Найден опасный метод: {method}"

    def test_data_collection_control(self):
        """Проверка контроля сбора данных"""
        tracker = StateTracker()

        # По умолчанию сбор включен
        assert tracker.collection_enabled is True

        # Проверяем методы включения/выключения
        tracker.disable_collection()
        assert tracker.collection_enabled is False

        tracker.enable_collection()
        assert tracker.collection_enabled is True

    def test_error_handling(self):
        """Проверка обработки ошибок в статическом контексте"""
        tracker = StateTracker()

        # Проверяем что метод не выбрасывает исключения при None
        try:
            result = tracker.collect_state_data(None)
            assert isinstance(result, StateSnapshot)
        except Exception as e:
            pytest.fail(f"Метод collect_state_data не должен выбрасывать исключения при None: {e}")

    def test_passive_observation(self):
        """Проверка пассивности наблюдения"""
        tracker = StateTracker()
        mock_state = Mock()

        # Метод должен только читать данные, не изменять состояние
        original_enabled = tracker.collection_enabled
        tracker.collect_state_data(mock_state)

        # Состояние не должно измениться
        assert tracker.collection_enabled == original_enabled
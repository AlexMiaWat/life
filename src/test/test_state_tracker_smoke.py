"""
Дымовые тесты для StateTracker

Проверяем:
- Создание экземпляров классов
- Базовую функциональность методов
- Отсутствие исключений при нормальной работе
- Корректность основных операций
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.state_tracker import (
    StateTracker,
    StateSnapshot,
)


@pytest.mark.smoke
class TestStateTrackerSmoke:
    """Дымовые тесты для StateTracker"""

    def test_state_tracker_creation(self):
        """Проверка создания StateTracker"""
        tracker = StateTracker()
        assert tracker is not None
        assert isinstance(tracker, StateTracker)

    def test_state_snapshot_creation(self):
        """Проверка создания StateSnapshot"""
        snapshot = StateSnapshot()
        assert snapshot is not None
        assert isinstance(snapshot, StateSnapshot)

        # Проверяем что timestamp установлен
        assert snapshot.timestamp > 0

    def test_state_snapshot_custom_creation(self):
        """Проверка создания StateSnapshot с кастомными значениями"""
        snapshot = StateSnapshot(
            energy=0.8,
            stability=0.9,
            integrity=0.7,
            fatigue=0.3,
            tension=0.4,
            age=100.0,
            subjective_time=95.0,
            memory_size=50,
            recent_events_count=10,
            action_count=5,
            decision_count=3,
            feedback_count=2,
            learning_params_count=8,
            adaptation_params_count=6
        )

        assert snapshot.energy == 0.8
        assert snapshot.stability == 0.9
        assert snapshot.memory_size == 50
        assert snapshot.action_count == 5

    def test_collect_state_data_basic(self):
        """Проверка базового сбора данных состояния"""
        tracker = StateTracker()
        mock_state = Mock()

        # Настраиваем mock с базовыми атрибутами
        mock_state.energy = 0.5
        mock_state.stability = 0.6
        mock_state.integrity = 0.7
        mock_state.fatigue = 0.2
        mock_state.tension = 0.3
        mock_state.age = 50.0
        mock_state.subjective_time = 45.0
        mock_state.action_count = 10
        mock_state.decision_count = 5
        mock_state.feedback_count = 3

        # Вызываем метод сбора данных
        result = tracker.collect_state_data(mock_state)

        # Проверяем результат
        assert isinstance(result, StateSnapshot)
        assert result.energy == 0.5
        assert result.stability == 0.6
        assert result.action_count == 10

    def test_collect_state_data_with_missing_attrs(self):
        """Проверка сбора данных при отсутствии некоторых атрибутов"""
        tracker = StateTracker()
        mock_state = Mock()

        # Настраиваем mock только с некоторыми атрибутами
        mock_state.energy = 0.8
        # Другие атрибуты отсутствуют

        # Метод должен работать без исключений
        result = tracker.collect_state_data(mock_state)

        assert isinstance(result, StateSnapshot)
        assert result.energy == 0.8
        # Отсутствующие атрибуты должны быть 0
        assert result.stability == 0.0
        assert result.action_count == 0

    def test_collect_state_data_with_memory(self):
        """Проверка сбора данных с памятью"""
        tracker = StateTracker()
        mock_state = Mock()

        # Настраиваем mock с памятью
        mock_memory = Mock()
        mock_memory.episodic_memory = [1, 2, 3, 4, 5]
        mock_memory.recent_events = ['event1', 'event2']

        mock_state.memory = mock_memory

        result = tracker.collect_state_data(mock_state)

        assert result.memory_size == 5
        assert result.recent_events_count == 2

    def test_collect_state_data_with_learning_engine(self):
        """Проверка сбора данных с learning engine"""
        tracker = StateTracker()
        mock_state = Mock()

        # Настраиваем mock с learning engine
        mock_learning = Mock()
        mock_learning.params = {'param1': 1, 'param2': 2, 'param3': 3}

        mock_state.learning_engine = mock_learning

        result = tracker.collect_state_data(mock_state)

        assert result.learning_params_count == 3

    def test_collect_state_data_with_adaptation_manager(self):
        """Проверка сбора данных с adaptation manager"""
        tracker = StateTracker()
        mock_state = Mock()

        # Настраиваем mock с adaptation manager
        mock_adaptation = Mock()
        mock_adaptation.params = {'adapt1': 10, 'adapt2': 20}

        mock_state.adaptation_manager = mock_adaptation

        result = tracker.collect_state_data(mock_state)

        assert result.adaptation_params_count == 2

    def test_get_last_snapshot(self):
        """Проверка получения последнего снимка"""
        tracker = StateTracker()

        # Изначально должен быть None
        assert tracker.get_last_snapshot() is None

        # После сбора данных должен быть snapshot
        mock_state = Mock()
        mock_state.energy = 1.0

        tracker.collect_state_data(mock_state)
        snapshot = tracker.get_last_snapshot()

        assert snapshot is not None
        assert isinstance(snapshot, StateSnapshot)
        assert snapshot.energy == 1.0

    def test_collection_enable_disable(self):
        """Проверка включения/выключения сбора данных"""
        tracker = StateTracker()

        # По умолчанию включено
        assert tracker.collection_enabled is True

        # Выключаем
        tracker.disable_collection()
        assert tracker.collection_enabled is False

        # При выключенном сборе возвращается пустой snapshot
        mock_state = Mock()
        mock_state.energy = 1.0

        result = tracker.collect_state_data(mock_state)
        assert isinstance(result, StateSnapshot)
        # При выключенном сборе возвращается пустой snapshot
        assert result.energy == 0.0

        # Включаем обратно
        tracker.enable_collection()
        assert tracker.collection_enabled is True

    def test_to_dict_functionality(self):
        """Проверка метода to_dict"""
        snapshot = StateSnapshot(
            energy=0.8,
            memory_size=25,
            action_count=7
        )

        data = snapshot.to_dict()

        assert isinstance(data, dict)
        assert data['energy'] == 0.8
        assert data['memory_size'] == 25
        assert data['action_count'] == 7
        assert 'timestamp' in data

    def test_error_handling(self):
        """Проверка обработки ошибок"""
        tracker = StateTracker()

        # Метод должен обрабатывать исключения gracefully
        mock_state = Mock()
        # Настраиваем mock чтобы он вызывал исключения
        mock_state.energy = Mock(side_effect=AttributeError("Test error"))

        # Метод не должен выбрасывать исключения
        result = tracker.collect_state_data(mock_state)
        assert isinstance(result, StateSnapshot)

    def test_multiple_collections(self):
        """Проверка множественного сбора данных"""
        tracker = StateTracker()

        # Первый сбор
        mock_state1 = Mock()
        mock_state1.energy = 0.5
        snapshot1 = tracker.collect_state_data(mock_state1)

        # Второй сбор
        mock_state2 = Mock()
        mock_state2.energy = 0.8
        snapshot2 = tracker.collect_state_data(mock_state2)

        # Последний snapshot должен быть от второго сбора
        last_snapshot = tracker.get_last_snapshot()
        assert last_snapshot.energy == 0.8

        # Оба snapshot должны существовать
        assert snapshot1.energy == 0.5
        assert snapshot2.energy == 0.8
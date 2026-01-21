"""
Подробные тесты для модуля Planning
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.planning.planning import record_potential_sequences
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestRecordPotentialSequences:
    """Тесты для функции record_potential_sequences"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        return SelfState()

    def test_record_potential_sequences_empty_recent_events(self, base_state):
        """Тест записи при пустом recent_events"""
        base_state.recent_events = []
        base_state.energy_history = []
        base_state.stability_history = []

        record_potential_sequences(base_state)

        assert "potential_sequences" in base_state.planning
        assert base_state.planning["potential_sequences"] == []
        assert "sources_used" in base_state.planning

    def test_record_potential_sequences_single_event(self, base_state):
        """Тест записи с одним событием в recent_events"""
        base_state.recent_events = ["event1"]
        base_state.energy_history = [50.0]
        base_state.stability_history = [0.7]

        record_potential_sequences(base_state)

        # С одним событием последовательность не создается (нужно минимум 2)
        assert base_state.planning["potential_sequences"] == []

    def test_record_potential_sequences_two_events(self, base_state):
        """Тест записи с двумя событиями"""
        base_state.recent_events = ["event1", "event2"]
        base_state.energy_history = [50.0, 49.0]
        base_state.stability_history = [0.7, 0.6]

        record_potential_sequences(base_state)

        assert len(base_state.planning["potential_sequences"]) == 1
        assert base_state.planning["potential_sequences"][0] == ["event1", "event2"]

    def test_record_potential_sequences_multiple_events(self, base_state):
        """Тест записи с несколькими событиями"""
        base_state.recent_events = ["event1", "event2", "event3", "event4"]
        base_state.energy_history = [50.0, 49.0, 48.0, 47.0]
        base_state.stability_history = [0.7, 0.6, 0.5, 0.4]

        record_potential_sequences(base_state)

        # Должна быть создана последовательность из последних 2 событий
        assert len(base_state.planning["potential_sequences"]) == 1
        assert base_state.planning["potential_sequences"][0] == ["event3", "event4"]

    def test_record_potential_sequences_sources_used(self, base_state):
        """Тест записи источников данных"""
        base_state.recent_events = ["e1", "e2", "e3"]
        base_state.energy_history = [50.0, 49.0, 48.0]
        base_state.stability_history = [0.7, 0.6]

        record_potential_sequences(base_state)

        assert "sources_used" in base_state.planning
        sources = base_state.planning["sources_used"]
        assert sources["memory_proxy"] == 3
        assert sources["learning_proxy"] == 2
        assert sources["adaptation_proxy"] == 3

    def test_record_potential_sequences_preserves_other_fields(self, base_state):
        """Тест, что функция не изменяет другие поля состояния"""
        base_state.energy = 50.0
        base_state.stability = 0.7
        base_state.integrity = 0.8
        base_state.recent_events = ["e1", "e2"]

        record_potential_sequences(base_state)

        # Эти поля не должны измениться
        assert base_state.energy == 50.0
        assert base_state.stability == 0.7
        assert base_state.integrity == 0.8
        assert base_state.recent_events == ["e1", "e2"]

    def test_record_potential_sequences_multiple_calls(self, base_state):
        """Тест нескольких вызовов функции"""
        base_state.recent_events = ["e1", "e2"]

        record_potential_sequences(base_state)
        first_sequences = base_state.planning["potential_sequences"].copy()

        base_state.recent_events = ["e3", "e4"]
        record_potential_sequences(base_state)

        # Последовательность должна обновиться
        assert base_state.planning["potential_sequences"][0] == ["e3", "e4"]
        assert base_state.planning["potential_sequences"][0] != first_sequences[0]

    def test_record_potential_sequences_empty_histories(self, base_state):
        """Тест записи при пустых историях"""
        base_state.recent_events = ["e1", "e2"]
        base_state.energy_history = []
        base_state.stability_history = []

        record_potential_sequences(base_state)

        assert len(base_state.planning["potential_sequences"]) == 1
        sources = base_state.planning["sources_used"]
        assert sources["learning_proxy"] == 0
        assert sources["adaptation_proxy"] == 0

    def test_record_potential_sequences_different_event_types(self, base_state):
        """Тест записи с разными типами событий"""
        base_state.recent_events = ["shock", "noise", "recovery"]
        base_state.energy_history = [50.0, 49.0, 51.0]
        base_state.stability_history = [0.7, 0.6, 0.8]

        record_potential_sequences(base_state)

        sequence = base_state.planning["potential_sequences"][0]
        assert sequence == ["noise", "recovery"]
        assert "shock" not in sequence  # Только последние 2

    def test_record_potential_sequences_subjective_time_accelerated(self, base_state):
        """Тест фиксации последовательностей при ускоренном восприятии времени"""
        base_state.recent_events = ["e1", "e2", "e3", "e4"]
        base_state.energy_history = [50.0, 49.0, 48.0]
        base_state.stability_history = [0.7, 0.6, 0.5]
        base_state.subjective_time = 2.2  # Ускоренное восприятие (ratio >= 1.1)
        base_state.age = 2.0

        record_potential_sequences(base_state)

        # При ускоренном восприятии - более длинные последовательности (min_length=3, max_sequences=2)
        sequences = base_state.planning["potential_sequences"]
        assert len(sequences) == 2  # Максимум 2 последовательности
        assert sequences[0] == ["e2", "e3", "e4"]  # Последние 3 события
        assert sequences[1] == ["e1", "e2", "e3", "e4"]  # Все 4 события

    def test_record_potential_sequences_subjective_time_slowed(self, base_state):
        """Тест фиксации последовательностей при замедленном восприятии времени"""
        base_state.recent_events = ["e1", "e2", "e3", "e4"]
        base_state.energy_history = [50.0, 49.0, 48.0]
        base_state.stability_history = [0.7, 0.6, 0.5]
        base_state.subjective_time = 0.8  # Замедленное восприятие (ratio <= 0.9)
        base_state.age = 2.0

        record_potential_sequences(base_state)

        # При замедленном восприятии - короткие последовательности (min_length=2, max_sequences=1)
        sequences = base_state.planning["potential_sequences"]
        assert len(sequences) == 1  # Только 1 последовательность
        assert sequences[0] == ["e3", "e4"]  # Только последние 2 события

    def test_record_potential_sequences_subjective_time_normal(self, base_state):
        """Тест фиксации последовательностей при нормальном восприятии времени"""
        base_state.recent_events = ["e1", "e2", "e3", "e4"]
        base_state.energy_history = [50.0, 49.0, 48.0]
        base_state.stability_history = [0.7, 0.6, 0.5]
        base_state.subjective_time = 1.0  # Нормальное восприятие (0.9 < ratio < 1.1)
        base_state.age = 1.0

        record_potential_sequences(base_state)

        # При нормальном восприятии - стандартные параметры (min_length=2, max_sequences=1)
        sequences = base_state.planning["potential_sequences"]
        assert len(sequences) == 1
        assert sequences[0] == ["e3", "e4"]  # Последние 2 события

    def test_record_potential_sequences_subjective_time_insufficient_events(self, base_state):
        """Тест при недостаточном количестве событий для разных режимов восприятия"""
        # Для ускоренного восприятия нужно минимум 3 события
        base_state.recent_events = ["e1", "e2"]  # Только 2 события
        base_state.subjective_time = 2.2
        base_state.age = 2.0

        record_potential_sequences(base_state)

        # Несмотря на ускоренное восприятие, последовательностей не создано
        assert base_state.planning["potential_sequences"] == []

    def test_record_potential_sequences_subjective_time_zero_age(self, base_state):
        """Тест фиксации последовательностей при нулевом возрасте"""
        base_state.recent_events = ["e1", "e2", "e3"]
        base_state.subjective_time = 1.0
        base_state.age = 0.0  # Нулевой возраст

        record_potential_sequences(base_state)

        # При нулевом возрасте должен быть нормальный режим (ratio = 1.0)
        sequences = base_state.planning["potential_sequences"]
        assert len(sequences) == 1
        assert sequences[0] == ["e2", "e3"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

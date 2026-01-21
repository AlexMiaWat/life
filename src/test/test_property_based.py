"""
Property-based тесты с использованием hypothesis - ROADMAP T.9

Тесты проверяют инварианты и свойства системы при различных входных данных.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.memory.memory import Memory, MemoryEntry
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestSelfStatePropertyBased:
    """Property-based тесты для SelfState"""

    @given(
        energy=st.floats(min_value=0.0, max_value=100.0),
        integrity=st.floats(min_value=0.0, max_value=1.0),
        stability=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_state_parameters_always_in_bounds(self, energy, integrity, stability):
        """Свойство: параметры состояния всегда в допустимых границах"""
        state = SelfState()
        state.energy = energy
        state.integrity = integrity
        state.stability = stability

        # Проверяем границы
        assert 0.0 <= state.energy <= 100.0
        assert 0.0 <= state.integrity <= 1.0
        assert 0.0 <= state.stability <= 1.0

    @given(
        energy_delta=st.floats(min_value=-200.0, max_value=200.0),
        integrity_delta=st.floats(min_value=-2.0, max_value=2.0),
        stability_delta=st.floats(min_value=-2.0, max_value=2.0),
    )
    def test_apply_delta_always_clamps(self, energy_delta, integrity_delta, stability_delta):
        """Свойство: apply_delta всегда ограничивает значения границами"""
        state = SelfState()

        state.apply_delta(
            {
                "energy": energy_delta,
                "integrity": integrity_delta,
                "stability": stability_delta,
            }
        )

        # Проверяем, что значения остались в границах
        assert 0.0 <= state.energy <= 100.0
        assert 0.0 <= state.integrity <= 1.0
        assert 0.0 <= state.stability <= 1.0

    @given(
        energy=st.floats(min_value=0.0, max_value=100.0),
        delta=st.floats(min_value=-150.0, max_value=150.0),
    )
    def test_energy_delta_idempotent(self, energy, delta):
        """Свойство: множественные применения delta дают тот же результат, что и одно"""
        state1 = SelfState()
        state1.energy = energy
        state1.apply_delta({"energy": delta})

        state2 = SelfState()
        state2.energy = energy
        state2.apply_delta({"energy": delta / 2})
        state2.apply_delta({"energy": delta / 2})

        # Результаты должны быть одинаковыми (с учетом округления)
        assert abs(state1.energy - state2.energy) < 0.0001


@pytest.mark.unit
@pytest.mark.order(1)
class TestMemoryPropertyBased:
    """Property-based тесты для Memory"""

    @given(
        num_entries=st.integers(min_value=0, max_value=200),
        event_type=st.text(min_size=1, max_size=20),
        significance=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_memory_size_always_limited(self, num_entries, event_type, significance):
        """Свойство: размер Memory всегда ограничен 50 записями"""
        memory = Memory()

        for i in range(num_entries):
            entry = MemoryEntry(
                event_type=event_type,
                meaning_significance=significance,
                timestamp=time.time() + i,
            )
            memory.append(entry)

        assert len(memory) <= 50

    @given(
        entries=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20),
                st.floats(min_value=0.0, max_value=1.0),
            ),
            min_size=0,
            max_size=100,
        )
    )
    def test_memory_preserves_order(self, entries):
        """Свойство: Memory сохраняет порядок добавления (FIFO)"""
        memory = Memory()

        for event_type, significance in entries:
            entry = MemoryEntry(
                event_type=event_type,
                meaning_significance=significance,
                timestamp=time.time(),
            )
            memory.append(entry)

        # Проверяем порядок последних записей
        if len(memory) > 1:
            # Последние N записей должны быть в том же порядке, что и последние N из entries
            last_n = min(len(memory), len(entries))
            expected_entries = entries[-last_n:]
            actual_entries = list(memory)[-last_n:]

            for i, (expected, actual) in enumerate(zip(expected_entries, actual_entries)):
                assert (
                    actual.event_type == expected[0]
                ), f"Order mismatch at position {i}: expected {expected[0]}, got {actual.event_type}"

    @given(
        event_type=st.text(min_size=1, max_size=20),
        significance=st.floats(min_value=0.0, max_value=1.0),
        num_appends=st.integers(min_value=1, max_value=100),
    )
    def test_memory_append_behavior(self, event_type, significance, num_appends):
        """Свойство: проверка поведения append с учетом clamp_size"""
        memory1 = Memory()
        memory2 = Memory()

        entry = MemoryEntry(
            event_type=event_type,
            meaning_significance=significance,
            timestamp=time.time(),
        )

        # Добавляем один раз
        memory1.append(entry)

        # Добавляем много раз
        for _ in range(num_appends):
            memory2.append(entry)

        # Проверяем корректное поведение
        assert len(memory1) == 1
        assert len(memory2) == min(num_appends, 50)  # ограничено clamp_size
        if len(memory1) > 0 and len(memory2) > 0:
            assert memory1[-1].event_type == memory2[-1].event_type


@pytest.mark.unit
@pytest.mark.order(1)
class TestMemoryEntryPropertyBased:
    """Property-based тесты для MemoryEntry"""

    @given(
        event_type=st.text(min_size=1, max_size=50),
        significance=st.floats(min_value=0.0, max_value=1.0),
        timestamp=st.floats(min_value=0.0, max_value=1e10),
    )
    def test_memory_entry_creation(self, event_type, significance, timestamp):
        """Свойство: MemoryEntry создается с любыми валидными параметрами"""
        entry = MemoryEntry(
            event_type=event_type,
            meaning_significance=significance,
            timestamp=timestamp,
        )

        assert entry.event_type == event_type
        assert entry.meaning_significance == significance
        assert entry.timestamp == timestamp
        assert entry.feedback_data is None

    @given(
        event_type=st.text(min_size=1, max_size=20),
        significance=st.floats(min_value=0.0, max_value=1.0),
        feedback_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.one_of(
                st.text(),
                st.integers(),
                st.floats(),
                st.booleans(),
            ),
            min_size=0,
            max_size=10,
        ),
    )
    def test_memory_entry_with_feedback(self, event_type, significance, feedback_data):
        """Свойство: MemoryEntry может содержать любые feedback_data"""
        entry = MemoryEntry(
            event_type=event_type,
            meaning_significance=significance,
            timestamp=time.time(),
            feedback_data=feedback_data if feedback_data else None,
        )

        assert entry.event_type == event_type
        assert entry.meaning_significance == significance
        if feedback_data:
            assert entry.feedback_data == feedback_data
        else:
            assert entry.feedback_data is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

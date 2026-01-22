"""
Упрощенные тесты для функции выбора паттерна реакции.

Тестируют простую логику decide_response без сложных компонентов.
"""
import pytest
import time

from src.decision.decision import decide_response
from src.state.self_state import SelfState
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry


class TestDecisionIntegration:
    """Интеграционные тесты для упрощенной функции выбора паттерна."""

    def test_basic_decision_flow(self):
        """Тест базового выбора паттерна."""
        # Создаем тестовые данные
        self_state = SelfState()
        self_state.energy = 50
        self_state.stability = 0.7
        self_state.integrity = 0.8

        meaning = Meaning()
        meaning.primary_emotion = "joy"

        # Принимаем решение
        pattern = decide_response(self_state, meaning, enable_performance_monitoring=False)

        # Проверяем, что вернулось корректное значение
        assert pattern in ["ignore", "absorb", "dampen", "amplify"]

    def test_low_energy_ignore(self):
        """Тест игнорирования при низкой энергии."""
        self_state = SelfState()
        self_state.energy = 20  # Низкая энергия
        self_state.stability = 0.5
        self_state.integrity = 0.8
        self_state.activated_memory = []  # Пустая память

        meaning = Meaning()
        meaning.primary_emotion = "neutral"

        pattern = decide_response(self_state, meaning)
        assert pattern == "ignore"

    def test_positive_event_amplify(self):
        """Тест усиления положительных событий."""
        self_state = SelfState()
        self_state.energy = 50
        self_state.stability = 0.2  # Низкая стабильность
        self_state.integrity = 0.8

        # Высокозначимая память
        memory_entry = MemoryEntry(
            event_type="positive_event",
            meaning_significance=0.8,
            weight=1.0,
            timestamp=time.time(),
            feedback_data={"type": "test"}
        )
        self_state.activated_memory = [memory_entry]

        meaning = Meaning()
        meaning.primary_emotion = "joy"  # Положительное событие

        pattern = decide_response(self_state, meaning)
        assert pattern == "amplify"

    def test_negative_event_dampen(self):
        """Тест смягчения негативных событий."""
        self_state = SelfState()
        self_state.energy = 50
        self_state.stability = 0.5
        self_state.integrity = 0.2  # Низкая целостность

        memory_entry = MemoryEntry(
            event_type="negative_event",
            meaning_significance=0.7,
            weight=1.0,
            timestamp=time.time(),
            feedback_data={"type": "test"}
        )
        self_state.activated_memory = [memory_entry]

        meaning = Meaning()
        meaning.primary_emotion = "fear"

        pattern = decide_response(self_state, meaning)
        assert pattern == "dampen"

    def test_default_absorb(self):
        """Тест поглощения по умолчанию."""
        self_state = SelfState()
        self_state.energy = 50
        self_state.stability = 0.7
        self_state.integrity = 0.8

        memory_entry = MemoryEntry(
            event_type="neutral_event",
            meaning_significance=0.6,  # Высокая значимость
            weight=1.0,
            timestamp=time.time(),
            feedback_data={"type": "test"}
        )
        self_state.activated_memory = [memory_entry]

        meaning = Meaning()
        meaning.primary_emotion = "neutral"

        pattern = decide_response(self_state, meaning)
        assert pattern == "absorb"

    def test_performance_monitoring(self):
        """Тест мониторинга производительности."""
        self_state = SelfState()
        meaning = Meaning()

        # Тест без мониторинга
        pattern1 = decide_response(self_state, meaning, enable_performance_monitoring=False)
        assert pattern1 in ["ignore", "absorb", "dampen", "amplify"]

        # Тест с мониторингом (не должно ломаться)
        pattern2 = decide_response(self_state, meaning, enable_performance_monitoring=True)
        assert pattern2 in ["ignore", "absorb", "dampen", "amplify"]
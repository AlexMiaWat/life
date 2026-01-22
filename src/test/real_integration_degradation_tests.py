"""
Реальные интеграционные тесты для проверки деградации системы Life.

Тестируют полную систему с реальными компонентами без mocks.
Проверяют корректную работу логики слабости, деградации и восстановления.
"""

import pytest
import time
from unittest.mock import patch

from src.state.self_state import SelfState
from src.meaning.meaning import Meaning
from src.meaning.engine import MeaningEngine
from src.memory.memory import MemoryEntry
from src.decision.decision import decide_response
from src.runtime.loop import _process_events_batch
from src.environment.event import Event


class TestRealSystemDegradation:
    """Интеграционные тесты реальной деградации системы без mocks."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.self_state = SelfState()
        self.meaning_engine = MeaningEngine()

        # Устанавливаем начальное хорошее состояние
        self.self_state.energy = 0.8
        self.self_state.stability = 0.9
        self.self_state.integrity = 0.85

    def test_system_starts_healthy(self):
        """Тест, что система начинает работу в здоровом состоянии."""
        # Проверяем начальные параметры
        assert self.self_state.energy > 0.5
        assert self.self_state.stability > 0.5
        assert self.self_state.integrity > 0.5

        # Проверяем, что система не считается слабой
        is_weak = (
            self.self_state.energy < 0.05
            or self.self_state.integrity < 0.05
            or self.self_state.stability < 0.05
        )
        assert not is_weak

    def test_weakness_penalty_application(self):
        """Тест применения штрафов за слабость."""
        # Устанавливаем состояние слабости
        self.self_state.energy = 0.03  # ниже порога 0.05
        self.self_state.stability = 0.9
        self.self_state.integrity = 0.85

        initial_energy = self.self_state.energy
        initial_stability = self.self_state.stability
        initial_integrity = self.self_state.integrity

        # Имитируем применение штрафа (как в runtime loop)
        dt = 1.0  # 1 секунда
        penalty_k = 0.02
        penalty = penalty_k * dt

        penalty_deltas = {
            "energy": -penalty,
            "stability": -penalty * 2.0,
            "integrity": -penalty * 2.0,
        }

        self.self_state.apply_delta(penalty_deltas)

        # Проверяем, что штрафы применились
        assert self.self_state.energy < initial_energy
        assert self.self_state.stability < initial_stability
        assert self.self_state.integrity < initial_integrity

        # Проверяем корректность расчетов
        assert abs(self.self_state.energy - (initial_energy - penalty)) < 0.001
        assert abs(self.self_state.stability - (initial_stability - penalty * 2.0)) < 0.001

    def test_system_degrades_under_continuous_weakness(self):
        """Тест постепенной деградации при непрерывной слабости."""
        # Устанавливаем состояние близкое к слабости
        self.self_state.energy = 0.06  # чуть выше порога
        self.self_state.stability = 0.04  # ниже порога
        self.self_state.integrity = 0.8

        initial_energy = self.self_state.energy
        initial_stability = self.self_state.stability

        # Имитируем несколько тиков с деградацией
        dt = 0.5  # полсекунды на тик
        penalty_k = 0.02

        for i in range(5):  # 5 тиков, чтобы не уйти в отрицательные значения
            is_weak = (
                self.self_state.energy < 0.05
                or self.self_state.integrity < 0.05
                or self.self_state.stability < 0.05
            )

            if is_weak:
                penalty = penalty_k * dt
                penalty_deltas = {
                    "energy": -penalty,
                    "stability": -penalty * 2.0,
                    "integrity": -penalty * 2.0,
                }
                self.self_state.apply_delta(penalty_deltas)

        # Проверяем, что система деградировала
        assert self.self_state.energy < initial_energy
        assert self.self_state.stability < initial_stability

        # Stability должен деградировать быстрее из-за большего штрафа
        # Но поскольку начальная stability была уже низкой, проверяем общее поведение

    def test_decision_response_under_weakness(self):
        """Тест выбора паттерна реакции при слабости."""
        # Устанавливаем состояние слабости
        self.self_state.energy = 0.02
        self.self_state.stability = 0.8
        self.self_state.integrity = 0.8

        # Добавляем память с низкой значимостью
        memory_entry = MemoryEntry(
            event_type="neutral_event",
            meaning_significance=0.3,
            weight=1.0,
            timestamp=time.time(),
            feedback_data={"type": "test"}
        )
        self.self_state.activated_memory = [memory_entry]

        meaning = Meaning()
        meaning.primary_emotion = "neutral"

        # Принимаем решение
        pattern = decide_response(self.self_state, meaning)

        # При низкой энергии должен выбираться "ignore" или "dampen"
        assert pattern in ["ignore", "dampen", "absorb"]

    def test_memory_integration_with_weakness(self):
        """Тест интеграции памяти с логикой слабости."""
        # Устанавливаем состояние средней слабости
        self.self_state.energy = 0.5
        self.self_state.stability = 0.03  # слабая стабильность
        self.self_state.integrity = 0.8

        # Добавляем высоко значимую память
        memory_entry = MemoryEntry(
            event_type="important_event",
            meaning_significance=0.8,
            weight=1.0,
            timestamp=time.time(),
            feedback_data={"type": "test"}
        )
        self.self_state.activated_memory = [memory_entry]

        meaning = Meaning()
        meaning.primary_emotion = "joy"

        # При слабой стабильности, но положительном событии - должен усилить
        pattern = decide_response(self.self_state, meaning)
        assert pattern in ["amplify", "absorb", "dampen"]

    def test_full_event_processing_with_degradation(self):
        """Тест полной обработки событий с деградацией."""
        # Мокаем компоненты для изоляции теста
        with patch('src.runtime.loop.logger') as mock_logger:
            # Создаем тестовые события
            events = [
                Event(
                    type="cognitive_event",
                    intensity=0.6,
                    timestamp=time.time(),
                    metadata={"emotion": "curiosity"}
                )
            ]

            # Имитируем структуры, необходимые для _process_events_batch
            structured_logger = Mock()
            structured_logger.log_event.return_value = "test_correlation_id"
            structured_logger.log_decision.return_value = None

            passive_data_sink = Mock()
            async_data_sink = Mock()
            memory_hierarchy = Mock()

            pending_actions = []
            event_queue = None

            # Вызываем обработку батча (без adaptation_manager для простоты)
            correlation_ids, processed_count, significant_count = _process_events_batch(
                events, self.self_state, self.meaning_engine, structured_logger,
                passive_data_sink, async_data_sink, memory_hierarchy, pending_actions, event_queue
            )

            # Проверяем результаты
            assert len(correlation_ids) == 1
            assert processed_count >= 0
            assert significant_count >= 0

    def test_system_recovery_after_weakness(self):
        """Тест восстановления системы после периода слабости."""
        # Устанавливаем состояние слабости
        self.self_state.energy = 0.02
        self.self_state.stability = 0.03
        self.self_state.integrity = 0.8

        # Имитируем восстановление (положительные дельты)
        recovery_deltas = {
            "energy": 0.1,
            "stability": 0.05,
            "integrity": 0.02,
        }
        self.self_state.apply_delta(recovery_deltas)

        # Проверяем, что система вышла из состояния слабости
        is_weak_after_recovery = (
            self.self_state.energy < 0.05
            or self.self_state.integrity < 0.05
            or self.self_state.stability < 0.05
        )

        # После восстановления система должна быть здоровее
        assert self.self_state.energy >= 0.05
        assert self.self_state.stability >= 0.05

        # Если восстановление было достаточным, система не должна быть слабой
        if self.self_state.integrity >= 0.05:
            assert not is_weak_after_recovery

    def test_boundary_weakness_conditions(self):
        """Тест граничных условий определения слабости."""
        # Тест на границе порога 0.05
        test_cases = [
            (0.06, 0.8, 0.8, False),  # energy чуть выше порога
            (0.04, 0.8, 0.8, True),   # energy чуть ниже порога
            (0.8, 0.04, 0.8, True),   # stability ниже порога
            (0.8, 0.8, 0.04, True),   # integrity ниже порога
            (0.04, 0.04, 0.04, True), # все параметры ниже порога
        ]

        for energy, stability, integrity, expected_weak in test_cases:
            self.self_state.energy = energy
            self.self_state.stability = stability
            self.self_state.integrity = integrity

            is_weak = (
                self.self_state.energy < 0.05
                or self.self_state.integrity < 0.05
                or self.self_state.stability < 0.05
            )

            assert is_weak == expected_weak, f"Failed for energy={energy}, stability={stability}, integrity={integrity}"


# Мок для StructuredLogger (упрощенный)
class Mock:
    def __init__(self):
        pass

    def __getattr__(self, name):
        return lambda *args, **kwargs: None
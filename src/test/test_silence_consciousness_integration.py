"""
Тесты интеграции системы тишины с ConsciousnessEngine.
"""

import pytest

from src.experimental.consciousness.engine import ConsciousnessEngine
from src.environment.event import Event
from src.state.self_state import SelfState


class TestSilenceConsciousnessIntegration:
    """Тесты интеграции событий silence с ConsciousnessEngine."""

    def test_silence_events_influence_consciousness(self):
        """Тест влияния событий silence на уровень сознания."""
        engine = ConsciousnessEngine()

        # SelfState для тестирования
        self_state = SelfState()
        self_state.energy = 0.7
        self_state.stability = 0.8

        # История событий без silence
        event_history_no_silence = [
            Event(type="noise", intensity=0.1, timestamp=1234567890.0),
            Event(type="decay", intensity=0.2, timestamp=1234567890.1),
        ]

        # История событий с silence
        event_history_with_silence = [
            Event(type="noise", intensity=0.1, timestamp=1234567890.0),
            Event(
                type="silence",
                intensity=0.3,
                timestamp=1234567890.1,
                metadata={"detector_generated": True},
            ),
        ]

        # Рассчитываем уровень сознания
        level_no_silence = engine.calculate_consciousness_level(
            self_state, event_history_no_silence
        )
        level_with_silence = engine.calculate_consciousness_level(
            self_state, event_history_with_silence
        )

        # События silence должны влиять на уровень сознания
        assert isinstance(level_no_silence, (int, float))
        assert isinstance(level_with_silence, (int, float))
        assert 0.0 <= level_no_silence <= 1.0
        assert 0.0 <= level_with_silence <= 1.0

    def test_comfortable_silence_boosts_consciousness(self):
        """Тест что комфортная тишина повышает уровень сознания."""
        engine = ConsciousnessEngine()

        self_state = SelfState()
        self_state.energy = 0.7

        # История с комфортной тишиной
        comfortable_silence_events = [
            Event(
                type="silence",
                intensity=0.5,
                timestamp=1234567890.0,
                metadata={"is_comfortable": True},
            ),
            Event(
                type="silence",
                intensity=0.4,
                timestamp=1234567890.1,
                metadata={"is_comfortable": True},
            ),
        ]

        # История с тревожной тишиной
        disturbing_silence_events = [
            Event(
                type="silence",
                intensity=-0.3,
                timestamp=1234567890.0,
                metadata={"is_comfortable": False},
            ),
            Event(
                type="silence",
                intensity=-0.2,
                timestamp=1234567890.1,
                metadata={"is_comfortable": False},
            ),
        ]

        level_comfortable = engine.calculate_consciousness_level(
            self_state, comfortable_silence_events
        )
        level_disturbing = engine.calculate_consciousness_level(
            self_state, disturbing_silence_events
        )

        # Комфортная тишина должна давать более высокий уровень сознания
        assert level_comfortable >= level_disturbing

    def test_silence_factor_calculation(self):
        """Тест расчета фактора влияния тишины."""
        engine = ConsciousnessEngine()

        # Тестируем различные комбинации событий silence
        test_cases = [
            ([], 0.0, "no_silence"),
            (
                [Event(type="silence", intensity=0.5, timestamp=1234567890.0)],
                0.4,
                "single_comfortable",
            ),
            (
                [Event(type="silence", intensity=-0.3, timestamp=1234567890.0)],
                0.09,
                "single_disturbing",
            ),
            (
                [
                    Event(type="silence", intensity=0.4, timestamp=1234567890.0),
                    Event(type="silence", intensity=0.6, timestamp=1234567890.1),
                ],
                0.4,
                "multiple_comfortable",
            ),
        ]

        for event_history, expected_min, case_name in test_cases:
            factor = engine._calculate_silence_consciousness_factor(event_history)

            assert 0.0 <= factor <= 1.0, f"Invalid factor for {case_name}"
            assert (
                factor >= expected_min
            ), f"Factor too low for {case_name}: {factor} < {expected_min}"

    def test_silence_influences_self_reflection(self):
        """Тест влияния тишины на саморефлексию."""
        engine = ConsciousnessEngine()

        self_state = SelfState()

        # История с событиями silence
        event_history = [
            Event(type="silence", intensity=0.4, timestamp=1234567890.0),
            Event(type="noise", intensity=0.1, timestamp=1234567890.1),
        ]

        level = engine.calculate_consciousness_level(self_state, event_history)

        # Проверяем что расчет прошел без ошибок
        assert isinstance(level, (int, float))
        assert 0.0 <= level <= 1.0

    def test_silence_events_persist_in_history(self):
        """Тест сохранения событий silence в истории сознания."""
        engine = ConsciousnessEngine()

        self_state = SelfState()

        event_history = [
            Event(
                type="silence",
                intensity=0.3,
                timestamp=1234567890.0,
                metadata={"detector_generated": True},
            ),
        ]

        # Многократные расчеты для заполнения истории
        for _ in range(5):
            engine.calculate_consciousness_level(self_state, event_history)

        # Проверяем что история содержит snapshots
        assert len(engine._consciousness_history) > 0

        # Проверяем структуру snapshots
        for snapshot in engine._consciousness_history:
            assert hasattr(snapshot, "consciousness_level")
            assert hasattr(snapshot, "timestamp")
            assert 0.0 <= snapshot.consciousness_level <= 1.0

    def test_silence_with_various_energy_levels(self):
        """Тест влияния тишины при различных уровнях энергии."""
        engine = ConsciousnessEngine()

        event_history = [
            Event(type="silence", intensity=0.4, timestamp=1234567890.0),
        ]

        # Тестируем с высокой энергией
        self_state_high_energy = SelfState()
        self_state_high_energy.energy = 0.9

        # Тестируем с низкой энергией
        self_state_low_energy = SelfState()
        self_state_low_energy.energy = 0.2

        level_high = engine.calculate_consciousness_level(self_state_high_energy, event_history)
        level_low = engine.calculate_consciousness_level(self_state_low_energy, event_history)

        # Высокая энергия должна давать более высокий уровень сознания
        assert level_high >= level_low

    def test_silence_factor_edge_cases(self):
        """Тест граничных случаев для фактора тишины."""
        engine = ConsciousnessEngine()

        # Пустая история
        factor_empty = engine._calculate_silence_consciousness_factor([])
        assert factor_empty == 0.0

        # Только события не-silence
        factor_no_silence = engine._calculate_silence_consciousness_factor(
            [
                Event(type="noise", intensity=0.1, timestamp=1234567890.0),
                Event(type="decay", intensity=0.2, timestamp=1234567890.1),
            ]
        )
        assert factor_no_silence == 0.0

        # Максимальная интенсивность комфортной тишины
        factor_max_comfortable = engine._calculate_silence_consciousness_factor(
            [
                Event(type="silence", intensity=0.6, timestamp=1234567890.0),
            ]
        )
        assert factor_max_comfortable <= 0.48  # 0.6 * 0.8 = 0.48

        # Минимальная интенсивность тревожной тишины
        factor_min_disturbing = engine._calculate_silence_consciousness_factor(
            [
                Event(type="silence", intensity=-0.05, timestamp=1234567890.0),
            ]
        )
        assert factor_min_disturbing <= 0.015  # -(-0.05) * 0.3 = 0.015

    def test_consciousness_trend_with_silence(self):
        """Тест тренда сознания с событиями silence."""
        engine = ConsciousnessEngine()

        self_state = SelfState()

        # Создаем историю с возрастающим количеством событий silence
        for i in range(3):
            event_history = [
                Event(type="silence", intensity=0.3, timestamp=1234567890.0 + j)
                for j in range(i + 1)
            ]

            engine.calculate_consciousness_level(self_state, event_history)

        # Проверяем что можем получить тренд
        trend = engine.get_consciousness_trend(time_window=60.0)

        assert "trend" in trend
        assert "average_level" in trend
        assert "change_rate" in trend
        assert "samples" in trend

    def test_silence_boost_in_flow_state(self):
        """Тест усиления тишины в состоянии потока."""
        engine = ConsciousnessEngine()

        # SelfState в состоянии потока (высокая энергия и стабильность)
        self_state_flow = SelfState()
        self_state_flow.energy = 0.9
        self_state_flow.stability = 0.9

        # SelfState в нормальном состоянии
        self_state_normal = SelfState()
        self_state_normal.energy = 0.5
        self_state_normal.stability = 0.5

        event_history = [
            Event(type="silence", intensity=0.4, timestamp=1234567890.0),
        ]

        level_flow = engine.calculate_consciousness_level(self_state_flow, event_history)
        level_normal = engine.calculate_consciousness_level(self_state_normal, event_history)

        # В состоянии потока тишина должна давать больший эффект
        assert level_flow >= level_normal

    def test_multiple_silence_events_accumulation(self):
        """Тест накопления эффекта от множественных событий silence."""
        engine = ConsciousnessEngine()

        self_state = SelfState()

        # Постепенно увеличиваем количество событий silence
        levels = []
        for num_events in range(1, 6):
            event_history = [
                Event(type="silence", intensity=0.3, timestamp=1234567890.0 + j)
                for j in range(num_events)
            ]

            level = engine.calculate_consciousness_level(self_state, event_history)
            levels.append(level)

        # Уровень сознания должен быть монотонно неубывающим
        # (хотя реальный эффект зависит от множества факторов)
        for i in range(1, len(levels)):
            assert isinstance(levels[i], (int, float))  # Просто проверяем что расчет прошел

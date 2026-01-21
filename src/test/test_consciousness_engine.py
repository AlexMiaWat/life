"""
Unit тесты для ConsciousnessEngine.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.experimental.consciousness.engine import ConsciousnessEngine, ConsciousnessSnapshot
from src.state.self_state import SelfState
from src.observability.structured_logger import StructuredLogger


class TestConsciousnessSnapshot:
    """Тесты для ConsciousnessSnapshot."""

    def test_snapshot_creation(self):
        """Тест создания снимка состояния сознания."""
        snapshot = ConsciousnessSnapshot(
            timestamp=1234567890.0,
            consciousness_level=0.75,
            self_reflection_score=0.6,
            meta_cognition_depth=0.4,
            current_state="reflective",
            neural_activity=0.8,
            energy_level=85.0,
            stability=0.9,
            recent_events_count=5,
        )

        assert snapshot.timestamp == 1234567890.0
        assert snapshot.consciousness_level == 0.75
        assert snapshot.self_reflection_score == 0.6
        assert snapshot.meta_cognition_depth == 0.4
        assert snapshot.current_state == "reflective"
        assert snapshot.neural_activity == 0.8
        assert snapshot.energy_level == 85.0
        assert snapshot.stability == 0.9
        assert snapshot.recent_events_count == 5


class TestConsciousnessEngine:
    """Тесты для ConsciousnessEngine."""

    @pytest.fixture
    def logger(self):
        """Фикстура для логгера."""
        return Mock(spec=StructuredLogger)

    @pytest.fixture
    def engine(self, logger):
        """Фикстура для движка сознания."""
        return ConsciousnessEngine(logger=logger)

    @pytest.fixture
    def self_state(self):
        """Фикстура для состояния системы."""
        state = SelfState()
        state.energy = 80.0
        state.stability = 0.85
        return state

    def test_engine_initialization(self, engine):
        """Тест инициализации движка сознания."""
        assert engine.BASELINE_CONSCIOUSNESS == 0.1
        assert len(engine._consciousness_history) == 0
        assert engine._cached_consciousness_level == engine.BASELINE_CONSCIOUSNESS
        assert engine._cached_self_reflection == 0.0
        assert engine._cached_meta_cognition == 0.0

    def test_calculate_consciousness_level_basic(self, engine, self_state, logger):
        """Тест базового расчета уровня сознания."""
        # Базовый расчет без истории событий
        level = engine.calculate_consciousness_level(self_state)

        # Должен быть выше базового уровня
        assert level >= engine.BASELINE_CONSCIOUSNESS
        assert level <= 1.0

        # Должны быть обновлены кэшированные значения
        assert engine._cached_consciousness_level == level

        # Должен быть создан снимок
        assert len(engine._consciousness_history) == 1

        # Должен быть вызван логгер
        logger.log_event.assert_called()

    def test_calculate_consciousness_level_with_events(self, engine, self_state):
        """Тест расчета уровня сознания с историей событий."""
        from src.environment.event import Event

        events = [
            Event(type="test_event_1", intensity=0.8, timestamp=time.time()),
            Event(type="test_event_2", intensity=0.6, timestamp=time.time()),
        ]

        level_with_events = engine.calculate_consciousness_level(self_state, events)

        # Уровень с событиями должен быть выше
        assert level_with_events >= engine.BASELINE_CONSCIOUSNESS

    def test_determine_consciousness_state(self, engine):
        """Тест определения состояния сознания."""
        # Тест различных уровней сознания
        test_cases = [
            (0.05, "unconscious"),
            (0.15, "awake"),
            (0.35, "reflective"),
            (0.55, "meta"),
        ]

        for level, expected_state in test_cases:
            state = engine.determine_consciousness_state(
                {"consciousness_level": level, "energy": 80.0, "stability": 0.8}
            )
            assert state == expected_state

    def test_determine_consciousness_state_flow(self, engine):
        """Тест состояния flow."""
        # Flow state требует высокой энергии и стабильности
        state = engine.determine_consciousness_state(
            {"consciousness_level": 0.4, "energy": 90.0, "stability": 0.9, "cognitive_load": 0.5}
        )
        assert state == "flow"

    def test_assess_self_reflection(self, engine):
        """Тест оценки саморефлексии."""
        # Без истории решений
        score = engine.assess_self_reflection([], [])
        assert score == 0.0

        # С историей решений (заглушка в реализации)
        decision_history = [{"success": True}, {"success": False}]
        behavior_patterns = [{"quality": 0.8}]

        score = engine.assess_self_reflection(decision_history, behavior_patterns)
        # В текущей реализации возвращается значение из _calculate_self_reflection
        assert isinstance(score, float)

    def test_evaluate_meta_cognition(self, engine):
        """Тест оценки метакогниции."""
        # Без когнитивных процессов
        depth = engine.evaluate_meta_cognition([], [])
        assert depth == 0.0

        # С историей процессов (заглушка в реализации)
        cognitive_processes = [{"type": "analysis"}]
        optimization_history = [{"success": True}]

        depth = engine.evaluate_meta_cognition(cognitive_processes, optimization_history)
        assert isinstance(depth, float)

    def test_get_consciousness_trend(self, engine, self_state):
        """Тест получения тренда сознания."""
        # Без истории
        trend = engine.get_consciousness_trend()
        assert trend["trend"] == "insufficient_data"

        # Создаем несколько снимков
        for i in range(5):
            time.sleep(0.01)  # Небольшая задержка
            engine.calculate_consciousness_level(self_state)

        # Теперь должен быть тренд
        trend = engine.get_consciousness_trend(time_window=1.0)
        assert "trend" in trend
        assert "average_level" in trend
        assert "change_rate" in trend
        assert trend["samples"] > 0

    def test_history_limit(self, engine, self_state):
        """Тест ограничения истории."""
        # Создаем больше снимков чем MAX_CONSCIOUSNESS_HISTORY
        max_history = engine.MAX_CONSCIOUSNESS_HISTORY
        for i in range(max_history + 10):
            engine.calculate_consciousness_level(self_state)

        # История должна быть ограничена
        assert len(engine._consciousness_history) <= max_history

    def test_performance_metrics(self, engine, self_state):
        """Тест метрик производительности."""
        initial_count = engine._calculation_count

        # Выполняем несколько расчетов
        for i in range(3):
            engine.calculate_consciousness_level(self_state)

        # Количество расчетов должно увеличиться
        assert engine._calculation_count == initial_count + 3
        assert engine._average_calculation_time > 0

    def test_reset_engine(self, engine, self_state):
        """Тест сброса движка."""
        # Создаем состояние
        engine.calculate_consciousness_level(self_state)

        # Сбрасываем
        engine.reset_engine()

        # Проверяем сброс
        assert len(engine._consciousness_history) == 0
        assert engine._calculation_count == 0
        assert engine._cached_consciousness_level == engine.BASELINE_CONSCIOUSNESS
        assert engine._cached_self_reflection == 0.0
        assert engine._cached_meta_cognition == 0.0

    @patch.object(time, "time")
    def test_neural_activity_calculation(self, mock_time, engine, self_state):
        """Тест расчета нейронной активности."""
        mock_time.return_value = 1000.0

        # Устанавливаем параметры для тестирования
        setattr(self_state, "tick_frequency", 2.0)
        setattr(self_state, "event_processing_rate", 50.0)
        setattr(self_state, "decision_complexity", 0.7)

        # Расчет через основной метод
        level = engine.calculate_consciousness_level(self_state)

        # Проверяем что уровень разумный
        assert engine.BASELINE_CONSCIOUSNESS <= level <= 1.0

    def test_state_cooldown(self, engine):
        """Тест cooldown между сменами состояний."""
        # Быстрая смена состояний
        state1 = engine.determine_consciousness_state(
            {"consciousness_level": 0.8, "energy": 90.0, "stability": 0.9}
        )
        state2 = engine.determine_consciousness_state(
            {"consciousness_level": 0.8, "energy": 90.0, "stability": 0.9}
        )

        # Второй вызов должен вернуть то же состояние из-за cooldown
        assert state1 == state2

    def test_get_performance_stats(self, engine, self_state):
        """Тест получения статистики производительности."""
        # Выполняем расчеты
        for i in range(3):
            engine.calculate_consciousness_level(self_state)

        stats = engine.get_performance_stats()

        assert "calculation_count" in stats
        assert "average_calculation_time" in stats
        assert "history_size" in stats
        assert stats["calculation_count"] == 3
        assert stats["history_size"] == 3

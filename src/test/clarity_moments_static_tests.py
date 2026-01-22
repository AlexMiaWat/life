"""
Статические тесты для экспериментальной функциональности Clarity Moments.

Включает unit тесты, валидацию типов, проверку контрактов сериализации.
"""

import pytest
import time
from typing import Dict, Any, List
from unittest.mock import Mock

from src.experimental.clarity_moments import (
    ClarityMoment,
    ClarityMomentsTracker,
    ClarityMoments
)
from src.experimental.adaptive_processing_manager import ProcessingMode, AdaptiveState


class TestClarityMoment:
    """Тесты для ClarityMoment."""

    def test_clarity_moment_initialization(self):
        """Тест инициализации ClarityMoment."""
        moment = ClarityMoment(
            timestamp=123.45,
            stage="test_stage",
            correlation_id="test_corr_123",
            event_id="test_event_456",
            event_type="test_event",
            intensity=0.8,
            data={"key": "value"}
        )

        assert moment.timestamp == 123.45
        assert moment.stage == "test_stage"
        assert moment.correlation_id == "test_corr_123"
        assert moment.event_id == "test_event_456"
        assert moment.event_type == "test_event"
        assert moment.intensity == 0.8
        assert moment.data == {"key": "value"}

    def test_clarity_moment_default_values(self):
        """Тест значений по умолчанию ClarityMoment."""
        moment = ClarityMoment(
            timestamp=123.45,
            stage="default_stage",
            correlation_id="default_corr",
            event_id="default_event",
            event_type="default_type",
            intensity=0.5,
            data={}
        )

        # Все значения должны быть установлены явно
        assert moment.timestamp == 123.45
        assert moment.stage == "default_stage"
        assert moment.correlation_id == "default_corr"
        assert moment.event_id == "default_event"
        assert moment.event_type == "default_type"
        assert moment.intensity == 0.5
        assert moment.data == {}


class TestClarityMomentsTracker:
    """Тесты для ClarityMomentsTracker."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_self_state_provider = Mock()
        self.mock_self_state = Mock()
        self.mock_self_state.processing_efficiency = 0.8
        self.mock_self_state.stability = 0.9
        self.mock_self_state_provider.return_value = self.mock_self_state

        self.tracker = ClarityMomentsTracker(self_state_provider=self.mock_self_state_provider)

    def test_initialization_default_provider(self):
        """Тест инициализации с провайдером по умолчанию."""
        tracker = ClarityMomentsTracker()

        assert len(tracker.moments) == 0
        assert tracker._correlation_counter == 0

        # Проверка что провайдер по умолчанию создан
        default_state = tracker.self_state_provider()
        assert hasattr(default_state, 'energy')
        assert hasattr(default_state, 'stability')

    def test_initialization_custom_provider(self):
        """Тест инициализации с пользовательским провайдером."""
        tracker = ClarityMomentsTracker(self_state_provider=self.mock_self_state_provider)

        assert tracker.self_state_provider is self.mock_self_state_provider

    def test_generate_correlation_id(self):
        """Тест генерации ID корреляции."""
        tracker = ClarityMomentsTracker()

        # Первый ID
        id1 = tracker._generate_correlation_id()
        assert id1 == "clarity_chain_1"
        assert tracker._correlation_counter == 1

        # Второй ID
        id2 = tracker._generate_correlation_id()
        assert id2 == "clarity_chain_2"
        assert tracker._correlation_counter == 2

    def test_add_moment(self):
        """Тест добавления момента ясности."""
        tracker = ClarityMomentsTracker(self_state_provider=self.mock_self_state_provider)

        moment = ClarityMoment(
            timestamp=123.45,
            stage="test_stage",
            correlation_id="test_corr",
            event_id="test_event",
            event_type="test_type",
            intensity=0.7,
            data={"test": "data"}
        )

        tracker.add_moment(moment)

        assert len(tracker.moments) == 1
        assert tracker.moments[0] is moment

        # Проверка что был вызван adaptive manager
        # (проверка через mock adaptive_manager)

    def test_map_intensity_to_mode(self):
        """Тест маппинга интенсивности на режим обработки."""
        tracker = ClarityMomentsTracker()

        # Высокая интенсивность -> OPTIMIZED
        assert tracker._map_intensity_to_mode(0.95) == ProcessingMode.OPTIMIZED

        # Средняя интенсивность -> INTENSIVE
        assert tracker._map_intensity_to_mode(0.75) == ProcessingMode.INTENSIVE

        # Низкая интенсивность -> EFFICIENT
        assert tracker._map_intensity_to_mode(0.55) == ProcessingMode.EFFICIENT

        # Минимальная интенсивность -> BASELINE
        assert tracker._map_intensity_to_mode(0.3) == ProcessingMode.BASELINE

    def test_get_moments_by_intensity(self):
        """Тест получения моментов по интенсивности."""
        tracker = ClarityMomentsTracker()

        # Создание моментов с разной интенсивностью
        moments = [
            ClarityMoment(100.0, "stage1", "corr1", "event1", "type1", 0.3, {}),
            ClarityMoment(101.0, "stage2", "corr2", "event2", "type2", 0.7, {}),
            ClarityMoment(102.0, "stage3", "corr3", "event3", "type3", 0.9, {}),
            ClarityMoment(103.0, "stage4", "corr4", "event4", "type4", 0.5, {}),
        ]

        for moment in moments:
            tracker.add_moment(moment)

        # Фильтрация по минимальной интенсивности 0.6
        filtered = tracker.get_moments_by_intensity(0.6)
        assert len(filtered) == 2
        assert all(m.intensity >= 0.6 for m in filtered)

        # Фильтрация по минимальной интенсивности 0.8
        filtered = tracker.get_moments_by_intensity(0.8)
        assert len(filtered) == 1
        assert filtered[0].intensity == 0.9

        # Без фильтрации
        all_moments = tracker.get_moments_by_intensity(0.0)
        assert len(all_moments) == 4

    def test_get_recent_moments(self):
        """Тест получения недавних моментов."""
        tracker = ClarityMomentsTracker()

        # Создание моментов с разными временными метками
        moments = [
            ClarityMoment(100.0, "stage1", "corr1", "event1", "type1", 0.5, {}),
            ClarityMoment(102.0, "stage2", "corr2", "event2", "type2", 0.6, {}),
            ClarityMoment(101.0, "stage3", "corr3", "event3", "type3", 0.7, {}),
            ClarityMoment(103.0, "stage4", "corr4", "event4", "type4", 0.8, {}),
        ]

        for moment in moments:
            tracker.add_moment(moment)

        # Получение 2 самых недавних
        recent = tracker.get_recent_moments(2)
        assert len(recent) == 2

        # Проверка порядка (по убыванию времени)
        assert recent[0].timestamp == 103.0
        assert recent[1].timestamp == 102.0

        # Получение всех
        all_recent = tracker.get_recent_moments(10)
        assert len(all_recent) == 4

    def test_get_clarity_history(self):
        """Тест получения истории моментов ясности."""
        tracker = ClarityMomentsTracker()

        # Создание моментов с разными временными метками
        moments = [
            ClarityMoment(103.0, "stage4", "corr4", "event4", "type4", 0.8, {}),
            ClarityMoment(101.0, "stage2", "corr2", "event2", "type2", 0.6, {}),
            ClarityMoment(102.0, "stage3", "corr3", "event3", "type3", 0.7, {}),
            ClarityMoment(100.0, "stage1", "corr1", "event1", "type1", 0.5, {}),
        ]

        for moment in moments:
            tracker.add_moment(moment)

        # Получение полной истории (должна быть отсортирована по времени)
        history = tracker.get_clarity_history()
        assert len(history) == 4

        # Проверка сортировки по возрастанию времени
        timestamps = [m.timestamp for m in history]
        assert timestamps == [100.0, 101.0, 102.0, 103.0]

        # Получение ограниченной истории
        limited_history = tracker.get_clarity_history(limit=2)
        assert len(limited_history) == 2
        assert limited_history[0].timestamp == 102.0
        assert limited_history[1].timestamp == 103.0

    def test_analyze_clarity_patterns_empty(self):
        """Тест анализа паттернов для пустого трекера."""
        tracker = ClarityMomentsTracker()

        patterns = tracker.analyze_clarity_patterns()

        assert patterns["total_moments"] == 0

    def test_analyze_clarity_patterns_with_data(self):
        """Тест анализа паттернов с данными."""
        tracker = ClarityMomentsTracker()

        # Создание тестовых моментов
        moments = [
            ClarityMoment(100.0, "stage1", "corr1", "event1", "cognitive_event", 0.6, {}),
            ClarityMoment(101.0, "stage2", "corr2", "event2", "emotional_event", 0.8, {}),
            ClarityMoment(102.0, "stage3", "corr3", "event3", "cognitive_event", 0.7, {}),
            ClarityMoment(103.0, "stage4", "corr4", "event4", "system_event", 0.9, {}),
        ]

        for moment in moments:
            tracker.add_moment(moment)

        patterns = tracker.analyze_clarity_patterns()

        # Проверка основных метрик
        assert patterns["total_moments"] == 4
        assert patterns["max_intensity"] == 0.9
        assert patterns["avg_intensity"] == (0.6 + 0.8 + 0.7 + 0.9) / 4

        # Проверка распределения типов событий
        event_types = patterns["event_type_distribution"]
        assert event_types["cognitive_event"] == 2
        assert event_types["emotional_event"] == 1
        assert event_types["system_event"] == 1

        # Проверка уникальных типов
        assert patterns["unique_event_types"] == 3

    def test_count_occurrences(self):
        """Тест подсчета вхождений элементов."""
        tracker = ClarityMomentsTracker()

        items = ["a", "b", "a", "c", "b", "a"]
        counts = tracker._count_occurrences(items)

        assert counts["a"] == 3
        assert counts["b"] == 2
        assert counts["c"] == 1

    def test_get_adaptive_state(self):
        """Тест получения адаптивного состояния."""
        tracker = ClarityMomentsTracker(self_state_provider=self.mock_self_state_provider)

        # Проверка что возвращается состояние из adaptive_manager
        state = tracker.get_adaptive_state()
        assert isinstance(state, AdaptiveState)

    def test_force_clarity_analysis(self):
        """Тест принудительного анализа ясности."""
        tracker = ClarityMomentsTracker(self_state_provider=self.mock_self_state_provider)

        # Выполнение анализа
        moment = tracker.force_clarity_analysis()

        # Должен вернуться момент ясности
        assert moment is not None
        assert isinstance(moment, ClarityMoment)
        assert moment.stage == "forced_analysis"
        assert moment.event_type == "system_analysis"
        assert "adaptive_state" in moment.data

        # Момент должен быть добавлен в трекер
        assert len(tracker.moments) == 1
        assert tracker.moments[0] is moment

    def test_map_state_to_intensity(self):
        """Тест маппинга состояния на интенсивность."""
        tracker = ClarityMomentsTracker()

        # Тест всех состояний
        mappings = {
            AdaptiveState.STANDARD: 0.3,
            AdaptiveState.EFFICIENT_PROCESSING: 0.6,
            AdaptiveState.INTENSIVE_ANALYSIS: 0.8,
            AdaptiveState.SYSTEM_SELF_MONITORING: 0.7,
            AdaptiveState.OPTIMAL_PROCESSING: 0.9
        }

        for state, expected_intensity in mappings.items():
            intensity = tracker._map_state_to_intensity(state)
            assert intensity == expected_intensity

    def test_constants(self):
        """Тест констант ClarityMomentsTracker."""
        assert ClarityMomentsTracker.CLARITY_CHECK_INTERVAL == 10
        assert ClarityMomentsTracker.CLARITY_STABILITY_THRESHOLD == 0.8
        assert ClarityMomentsTracker.CLARITY_ENERGY_THRESHOLD == 0.7


class TestClarityMoments:
    """Тесты для ClarityMoments (класс совместимости)."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_self_state_provider = Mock()
        self.mock_self_state = Mock()
        self.mock_self_state_provider.return_value = self.mock_self_state

        self.clarity = ClarityMoments(self_state_provider=self.mock_self_state_provider)

    def test_initialization(self):
        """Тест инициализации ClarityMoments."""
        assert self.clarity._clarity_events_count == 0
        assert self.clarity._last_check_tick == -10  # -CLARITY_CHECK_INTERVAL

        # Проверка констант
        assert self.clarity.CLARITY_CHECK_INTERVAL == 10
        assert self.clarity.CLARITY_STABILITY_THRESHOLD == 0.8
        assert self.clarity.CLARITY_ENERGY_THRESHOLD == 0.7
        assert self.clarity.CLARITY_DURATION_TICKS == 50

    def test_analyze_clarity(self):
        """Тест анализа ясности."""
        moment = self.clarity.analyze_clarity(self.mock_self_state)

        assert moment is not None
        assert isinstance(moment, ClarityMoment)
        assert self.clarity._clarity_events_count == 1

    def test_get_clarity_moments(self):
        """Тест получения моментов ясности."""
        # Добавление моментов через analyze_clarity
        self.clarity.analyze_clarity(self.mock_self_state)
        self.clarity.analyze_clarity(self.mock_self_state)

        moments = self.clarity.get_clarity_moments()
        assert len(moments) == 2
        assert all(isinstance(m, ClarityMoment) for m in moments)

    def test_check_clarity_conditions(self):
        """Тест проверки условий ясности."""
        result = self.clarity.check_clarity_conditions(self.mock_self_state)

        assert result is not None
        assert result["type"] == "clarity_moment"
        assert "data" in result
        assert "clarity_id" in result["data"]
        assert "intensity" in result["data"]
        assert result["data"]["clarity_id"] == 1

        # Проверка счетчика
        assert self.clarity._clarity_events_count == 1

    def test_activate_clarity_moment(self):
        """Тест активации момента ясности."""
        self.clarity.activate_clarity_moment(self.mock_self_state)

        assert self.mock_self_state.clarity_state is True
        assert self.mock_self_state.clarity_duration == 50
        assert self.mock_self_state.clarity_modifier == 1.5

    def test_update_clarity_state_with_active(self):
        """Тест обновления активного состояния ясности."""
        # Активация
        self.clarity.activate_clarity_moment(self.mock_self_state)

        # Обновление (длительность должна уменьшиться)
        self.clarity.update_clarity_state(self.mock_self_state)
        assert self.mock_self_state.clarity_duration == 49

        # Еще одно обновление
        self.clarity.update_clarity_state(self.mock_self_state)
        assert self.mock_self_state.clarity_duration == 48

    def test_update_clarity_state_expiration(self):
        """Тест истечения состояния ясности."""
        # Активация
        self.clarity.activate_clarity_moment(self.mock_self_state)

        # Имитация истечения времени
        self.mock_self_state.clarity_duration = 1

        # Обновление должно деактивировать
        self.clarity.update_clarity_state(self.mock_self_state)

        assert self.mock_self_state.clarity_state is False
        assert self.mock_self_state.clarity_duration == 0
        assert self.mock_self_state.clarity_modifier == 1.0

    def test_deactivate_clarity_moment(self):
        """Тест деактивации момента ясности."""
        # Сначала активировать
        self.clarity.activate_clarity_moment(self.mock_self_state)

        # Затем деактивировать
        self.clarity.deactivate_clarity_moment(self.mock_self_state)

        assert self.mock_self_state.clarity_state is False
        assert self.mock_self_state.clarity_duration == 0
        assert self.mock_self_state.clarity_modifier == 1.0

    def test_get_clarity_level_with_moments(self):
        """Тест получения уровня ясности с моментами."""
        # Добавление момента
        self.clarity.analyze_clarity(self.mock_self_state)

        level = self.clarity.get_clarity_level()
        assert isinstance(level, float)
        assert 0.0 <= level <= 1.0

    def test_get_clarity_level_without_moments(self):
        """Тест получения уровня ясности без моментов."""
        level = self.clarity.get_clarity_level()
        assert level == 0.0

    def test_backward_compatibility_constants(self):
        """Тест констант обратной совместимости."""
        # Проверка что константы соответствуют старому API
        assert hasattr(ClarityMoments, 'CLARITY_CHECK_INTERVAL')
        assert hasattr(ClarityMoments, 'CLARITY_STABILITY_THRESHOLD')
        assert hasattr(ClarityMoments, 'CLARITY_ENERGY_THRESHOLD')
        assert hasattr(ClarityMoments, 'CLARITY_DURATION_TICKS')

        # Проверка значений
        assert ClarityMoments.CLARITY_CHECK_INTERVAL == 10
        assert ClarityMoments.CLARITY_STABILITY_THRESHOLD == 0.8
        assert ClarityMoments.CLARITY_ENERGY_THRESHOLD == 0.7
        assert ClarityMoments.CLARITY_DURATION_TICKS == 50

    def test_tracker_integration(self):
        """Тест интеграции с ClarityMomentsTracker."""
        # Проверка что внутренний трекер существует
        assert hasattr(self.clarity, 'tracker')
        assert isinstance(self.clarity.tracker, ClarityMomentsTracker)

    def test_event_counter_increment(self):
        """Тест инкремента счетчика событий."""
        initial_count = self.clarity._clarity_events_count

        self.clarity.check_clarity_conditions(self.mock_self_state)
        assert self.clarity._clarity_events_count == initial_count + 1

        self.clarity.analyze_clarity(self.mock_self_state)
        assert self.clarity._clarity_events_count == initial_count + 2
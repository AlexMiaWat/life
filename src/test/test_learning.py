"""
Unit tests for Learning Engine (Этап 14).

Tests for:
- LearningEngine.process_statistics()
- LearningEngine.adjust_parameters()
- LearningEngine.record_changes()
- LearningEngine.calculate_adaptive_thresholds()
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch

from src.learning.learning import LearningEngine
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState


class TestLearningEngine:
    """Unit tests for LearningEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = LearningEngine()
        self.mock_self_state = Mock(spec=SelfState)
        self.mock_self_state.learning_params = {}
        self.mock_self_state.learning_params_history = []

    def test_init(self):
        """Test LearningEngine initialization."""
        engine = LearningEngine()
        assert hasattr(engine, '_lock')
        assert engine._lock is not None
        assert hasattr(engine, '_adaptive_thresholds')
        assert engine._adaptive_thresholds == {}

    def test_process_statistics_empty_memory(self):
        """Test process_statistics with empty memory."""
        memory = []
        result = self.engine.process_statistics(memory)

        expected = {
            "event_type_counts": {},
            "event_type_total_significance": {},
            "feedback_pattern_counts": {},
            "feedback_state_deltas": {"energy": [], "stability": [], "integrity": []},
            "total_entries": 0,
            "feedback_entries": 0,
            "memory_entries": [],
        }
        assert result == expected

    def test_process_statistics_with_events(self):
        """Test process_statistics with various event types."""
        memory = [
            MemoryEntry(
                event_type="test_event_1",
                meaning_significance=0.8,
                weight=0.9,
                timestamp=time.time(),
            ),
            MemoryEntry(
                event_type="test_event_1",
                meaning_significance=0.6,
                weight=0.7,
                timestamp=time.time(),
            ),
            MemoryEntry(
                event_type="test_event_2",
                meaning_significance=0.4,
                weight=0.5,
                timestamp=time.time(),
            ),
        ]

        result = self.engine.process_statistics(memory)

        assert result["total_entries"] == 3
        assert result["feedback_entries"] == 0
        assert result["event_type_counts"]["test_event_1"] == 2
        assert result["event_type_counts"]["test_event_2"] == 1
        assert abs(result["event_type_total_significance"]["test_event_1"] - 1.4) < 0.001
        assert abs(result["event_type_total_significance"]["test_event_2"] - 0.4) < 0.001

    def test_process_statistics_with_feedback(self):
        """Test process_statistics with feedback entries."""
        memory = [
            MemoryEntry(
                event_type="feedback",
                feedback_data={
                    "action_pattern": "pattern_A",
                    "state_delta": {"energy": -0.1, "stability": 0.05, "integrity": -0.02}
                },
                meaning_significance=0.5,
                weight=0.8,
                timestamp=time.time(),
            ),
            MemoryEntry(
                event_type="feedback",
                feedback_data={
                    "action_pattern": "pattern_B",
                    "state_delta": {"energy": 0.2, "stability": -0.1, "integrity": 0.1}
                },
                meaning_significance=0.3,
                weight=0.6,
                timestamp=time.time(),
            ),
        ]

        result = self.engine.process_statistics(memory)

        assert result["total_entries"] == 2
        assert result["feedback_entries"] == 2
        assert result["feedback_pattern_counts"]["pattern_A"] == 1
        assert result["feedback_pattern_counts"]["pattern_B"] == 1
        assert len(result["feedback_state_deltas"]["energy"]) == 2
        assert len(result["feedback_state_deltas"]["stability"]) == 2
        assert len(result["feedback_state_deltas"]["integrity"]) == 2

    def test_adjust_parameters_empty_params(self):
        """Test adjust_parameters with empty parameters."""
        statistics = {
            "event_type_counts": {"event_1": 10},
            "event_type_total_significance": {"event_1": 5.0},
            "feedback_pattern_counts": {},
            "total_entries": 10,
        }

        result = self.engine.adjust_parameters(statistics, {})
        assert result == {}

    def test_adjust_parameters_invalid_types(self):
        """Test adjust_parameters with invalid parameter types."""
        statistics = {
            "event_type_counts": {"event_1": 10},
            "event_type_total_significance": {"event_1": 5.0},
            "feedback_pattern_counts": {},
            "total_entries": 10,
        }

        # Test with non-dict current_params
        with pytest.raises(TypeError, match="current_params должен быть словарем"):
            self.engine.adjust_parameters(statistics, "not_a_dict")

        # Test with non-dict statistics
        with pytest.raises(TypeError, match="statistics должен быть словарем"):
            self.engine.adjust_parameters("not_a_dict", {})

    def test_adjust_parameters_with_event_sensitivity(self):
        """Test adjustment of event_type_sensitivity."""
        # Создаем статистику с очень высокой частотой для event_1 (25/30 = 83%)
        # и очень низкой для event_2 (5/30 = 17%)
        statistics = {
            "event_type_counts": {"event_1": 25, "event_2": 5},
            "event_type_total_significance": {"event_1": 12.5, "event_2": 2.5},
            "feedback_pattern_counts": {},
            "total_entries": 30,
        }

        current_params = {
            "event_type_sensitivity": {"event_1": 0.5, "event_2": 0.5}
        }

        result = self.engine.adjust_parameters(statistics, current_params)

        # event_1 должен увеличиться (частое событие > HIGH_FREQUENCY_THRESHOLD)
        assert "event_type_sensitivity" in result
        event_1_change = result["event_type_sensitivity"]["event_1"] - 0.5
        event_2_change = result["event_type_sensitivity"]["event_2"] - 0.5

        # event_1 должен увеличиться, event_2 может остаться без изменений или уменьшиться
        assert event_1_change >= 0  # Увеличение или без изменений

        # Изменение не должно превышать MAX_PARAMETER_DELTA (с допуском для плавающей точки)
        assert abs(event_1_change) <= LearningEngine.MAX_PARAMETER_DELTA + 1e-10
        assert abs(event_2_change) <= LearningEngine.MAX_PARAMETER_DELTA + 1e-10

    def test_adjust_parameters_with_significance_thresholds(self):
        """Test adjustment of significance_thresholds."""
        statistics = {
            "event_type_counts": {"event_1": 10},
            "event_type_total_significance": {"event_1": 8.0},  # Высокая средняя значимость
            "feedback_pattern_counts": {},
            "total_entries": 10,
        }

        current_params = {
            "significance_thresholds": {"event_1": 0.5}
        }

        result = self.engine.adjust_parameters(statistics, current_params)

        # Высокая значимость должна привести к снижению порога
        assert "significance_thresholds" in result
        assert result["significance_thresholds"]["event_1"] < 0.5

    def test_adjust_parameters_with_response_coefficients(self):
        """Test adjustment of response_coefficients."""
        statistics = {
            "event_type_counts": {},
            "event_type_total_significance": {},
            "feedback_pattern_counts": {"pattern_A": 15, "pattern_B": 3},  # pattern_A частый
            "total_entries": 18,
        }

        current_params = {
            "response_coefficients": {"pattern_A": 0.5, "pattern_B": 0.5}
        }

        result = self.engine.adjust_parameters(statistics, current_params)

        # pattern_A должен увеличиться или остаться без изменений (частый паттерн)
        assert "response_coefficients" in result
        pattern_A_change = result["response_coefficients"]["pattern_A"] - 0.5
        pattern_B_change = result["response_coefficients"]["pattern_B"] - 0.5

        assert pattern_A_change >= 0  # Увеличение или без изменений

        # Изменения не должны превышать MAX_PARAMETER_DELTA (с допуском для плавающей точки)
        assert abs(pattern_A_change) <= LearningEngine.MAX_PARAMETER_DELTA + 1e-10
        assert abs(pattern_B_change) <= LearningEngine.MAX_PARAMETER_DELTA + 1e-10

    def test_adjust_parameters_bounds_checking(self):
        """Test that parameters stay within [0.0, 1.0] bounds."""
        # Создаем параметры близкие к границам
        current_params = {
            "event_type_sensitivity": {"event_1": 0.99},  # Близко к максимуму
            "significance_thresholds": {"event_1": 0.01},  # Близко к минимуму
        }

        statistics = {
            "event_type_counts": {"event_1": 25},  # Частое событие
            "event_type_total_significance": {"event_1": 25.0},  # Высокая значимость
            "feedback_pattern_counts": {},
            "total_entries": 25,
        }

        result = self.engine.adjust_parameters(statistics, current_params)

        # Проверяем, что значения остались в допустимых границах
        sensitivity = result["event_type_sensitivity"]["event_1"]
        threshold = result["significance_thresholds"]["event_1"]

        assert 0.0 <= sensitivity <= 1.0
        assert 0.0 <= threshold <= 1.0

    def test_calculate_adaptive_thresholds(self):
        """Test calculate_adaptive_thresholds method."""
        # Создаем тестовые данные с различными весами
        memory_entries = [
            Mock(weight=0.8, event_type="event_1", meaning_significance=0.7),
            Mock(weight=0.6, event_type="event_1", meaning_significance=0.5),
            Mock(weight=0.4, event_type="event_2", meaning_significance=0.3),
        ]

        statistics = {
            "memory_entries": memory_entries,
            "event_type_counts": {"event_1": 10, "event_2": 5},
            "event_type_total_significance": {"event_1": 6.0, "event_2": 1.5},
            "feedback_pattern_counts": {"pattern_A": 8, "pattern_B": 2},
        }

        thresholds = self.engine.calculate_adaptive_thresholds(statistics)

        # Проверяем наличие рассчитанных порогов
        assert "high_frequency_threshold" in thresholds
        assert "low_frequency_threshold" in thresholds
        assert "high_significance_threshold" in thresholds
        assert "low_significance_threshold" in thresholds
        assert "high_pattern_frequency_threshold" in thresholds
        assert "low_pattern_frequency_threshold" in thresholds
        assert "adaptive_max_parameter_delta" in thresholds

        # Проверяем границы
        assert LearningEngine.MIN_FREQUENCY_THRESHOLD <= thresholds["high_frequency_threshold"] <= LearningEngine.MAX_FREQUENCY_THRESHOLD
        assert LearningEngine.MIN_FREQUENCY_THRESHOLD <= thresholds["low_frequency_threshold"] <= LearningEngine.MAX_FREQUENCY_THRESHOLD

    def test_record_changes_validation(self):
        """Test record_changes parameter validation."""
        old_params = {"event_type_sensitivity": {"event_1": 0.5}}
        new_params = {"event_type_sensitivity": {"event_1": 0.6}}  # Изменение > MAX_PARAMETER_DELTA

        with pytest.raises(ValueError, match="Изменение параметра .* слишком большое"):
            self.engine.record_changes(old_params, new_params, self.mock_self_state)

    def test_record_changes_success(self):
        """Test successful record_changes operation."""
        old_params = {"event_type_sensitivity": {"event_1": 0.5}}
        new_params = {"event_type_sensitivity": {"event_1": 0.502}}  # Маленькое изменение

        # Инициализируем learning_params в mock
        self.mock_self_state.learning_params = old_params.copy()
        self.mock_self_state.learning_params_history = []

        self.engine.record_changes(old_params, new_params, self.mock_self_state)

        # Проверяем, что параметры обновились
        assert self.mock_self_state.learning_params["event_type_sensitivity"]["event_1"] == 0.502

        # Проверяем, что история записалась
        assert len(self.mock_self_state.learning_params_history) == 1
        history_entry = self.mock_self_state.learning_params_history[0]
        assert "changes" in history_entry
        assert "timestamp" in history_entry
        assert "tick" in history_entry

    def test_record_changes_thread_safety(self):
        """Test thread safety of record_changes."""
        old_params = {"event_type_sensitivity": {"event_1": 0.5}}
        new_params = {"event_type_sensitivity": {"event_1": 0.502}}

        self.mock_self_state.learning_params = old_params.copy()
        self.mock_self_state.learning_params_history = []

        # Запускаем несколько потоков одновременно
        def update_params():
            self.engine.record_changes(old_params, new_params, self.mock_self_state)

        threads = [threading.Thread(target=update_params) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Проверяем, что финальное значение корректное (последнее изменение применилось)
        assert self.mock_self_state.learning_params["event_type_sensitivity"]["event_1"] == 0.502

    def test_calculate_stability_factor(self):
        """Test _calculate_stability_factor method."""
        # Тест с достаточными данными
        statistics = {
            "memory_entries": [
                Mock(weight=0.8),
                Mock(weight=0.6),
                Mock(weight=0.7),
            ]
        }
        stability = self.engine._calculate_stability_factor(statistics)
        assert 0.0 <= stability <= 1.0

        # Тест с недостаточными данными
        statistics_empty = {"memory_entries": []}
        stability_empty = self.engine._calculate_stability_factor(statistics_empty)
        assert stability_empty == 0.5  # Нейтральное значение

    def test_constants(self):
        """Test that constants are properly defined."""
        assert LearningEngine.MAX_PARAMETER_DELTA == 0.01
        assert LearningEngine.MIN_PARAMETER_DELTA == 0.001
        assert LearningEngine.HIGH_FREQUENCY_THRESHOLD == 0.2
        assert LearningEngine.LOW_FREQUENCY_THRESHOLD == 0.1
        assert LearningEngine.MAX_FREQUENCY_THRESHOLD == 0.8
        assert LearningEngine.MIN_FREQUENCY_THRESHOLD == 0.05
        assert LearningEngine.MAX_SIGNIFICANCE_THRESHOLD == 0.9
        assert LearningEngine.MIN_SIGNIFICANCE_THRESHOLD == 0.1
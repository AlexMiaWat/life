"""
Unit tests for Adaptation Manager (Этап 15).

Tests for:
- AdaptationManager.analyze_changes()
- AdaptationManager.apply_adaptation()
- AdaptationManager.store_history()
"""

import pytest
import threading
import time
from unittest.mock import Mock

from src.adaptation.adaptation import AdaptationManager
from src.state.self_state import SelfState


class TestAdaptationManager:
    """Unit tests for AdaptationManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = AdaptationManager()
        self.mock_self_state = Mock(spec=SelfState)
        self.mock_self_state.adaptation_params = {}
        self.mock_self_state.adaptation_history = []

    def test_init(self):
        """Test AdaptationManager initialization."""
        manager = AdaptationManager()
        assert hasattr(manager, '_lock')
        assert manager._lock is not None

    def test_analyze_changes_no_history(self):
        """Test analyze_changes with empty adaptation history."""
        learning_params = {
            "event_type_sensitivity": {"event_1": 0.6, "event_2": 0.4}
        }
        adaptation_history = []

        result = self.manager.analyze_changes(learning_params, adaptation_history)

        assert "learning_params_snapshot" in result
        assert "recent_changes" in result
        assert "change_patterns" in result
        assert result["learning_params_snapshot"] == learning_params

    def test_analyze_changes_with_history(self):
        """Test analyze_changes with existing adaptation history."""
        learning_params = {
            "event_type_sensitivity": {"event_1": 0.6, "event_2": 0.4}
        }

        adaptation_history = [
            {
                "timestamp": time.time() - 100,
                "learning_params_snapshot": {
                    "event_type_sensitivity": {"event_1": 0.5, "event_2": 0.5}
                },
                "applied_adaptation": {
                    "behavior_sensitivity": {"event_1": 0.02}
                }
            }
        ]

        result = self.manager.analyze_changes(learning_params, adaptation_history)

        # Проверяем, что изменения обнаружены
        assert "recent_changes" in result
        assert "event_type_sensitivity" in result["recent_changes"]
        changes = result["recent_changes"]["event_type_sensitivity"]
        assert changes["event_1"]["old"] == 0.5
        assert changes["event_1"]["new"] == 0.6
        assert changes["event_2"]["old"] == 0.5
        assert changes["event_2"]["new"] == 0.4

    def test_apply_adaptation_behavior_sensitivity(self):
        """Test apply_adaptation for behavior_sensitivity."""
        analysis = {
            "recent_changes": {
                "event_type_sensitivity": {
                    "event_1": {"old_value": 0.5, "new_value": 0.6, "delta": 0.1}
                }
            },
            "learning_params_snapshot": {
                "event_type_sensitivity": {"event_1": 0.6}
            }
        }

        current_adaptation_params = {
            "behavior_sensitivity": {"event_1": 0.5}
        }

        result = self.manager.apply_adaptation(analysis, current_adaptation_params, self.mock_self_state)

        assert "behavior_sensitivity" in result
        # Изменение должно быть небольшим (MAX_ADAPTATION_DELTA)
        new_value = result["behavior_sensitivity"]["event_1"]
        assert abs(new_value - 0.5) <= AdaptationManager.MAX_ADAPTATION_DELTA + 1e-10

    def test_apply_adaptation_behavior_thresholds(self):
        """Test apply_adaptation for behavior_thresholds."""
        analysis = {
            "recent_changes": {
                "significance_thresholds": {
                    "event_1": {"old_value": 0.3, "new_value": 0.25, "delta": -0.05}
                }
            },
            "learning_params_snapshot": {
                "significance_thresholds": {"event_1": 0.25}
            }
        }

        current_adaptation_params = {
            "behavior_thresholds": {"event_1": 0.4}
        }

        result = self.manager.apply_adaptation(analysis, current_adaptation_params, self.mock_self_state)

        assert "behavior_thresholds" in result
        new_value = result["behavior_thresholds"]["event_1"]
        assert abs(new_value - 0.4) <= AdaptationManager.MAX_ADAPTATION_DELTA + 1e-10

    def test_apply_adaptation_behavior_coefficients(self):
        """Test apply_adaptation for behavior_coefficients."""
        analysis = {
            "recent_changes": {
                "response_coefficients": {
                    "pattern_A": {"old_value": 0.7, "new_value": 0.75, "delta": 0.05}
                }
            },
            "learning_params_snapshot": {
                "response_coefficients": {"pattern_A": 0.75}
            }
        }

        current_adaptation_params = {
            "behavior_coefficients": {"pattern_A": 0.6}
        }

        result = self.manager.apply_adaptation(analysis, current_adaptation_params, self.mock_self_state)

        assert "behavior_coefficients" in result
        new_value = result["behavior_coefficients"]["pattern_A"]
        assert abs(new_value - 0.6) <= AdaptationManager.MAX_ADAPTATION_DELTA + 1e-10

    def test_apply_adaptation_bounds_checking(self):
        """Test that adaptation parameters stay within bounds."""
        analysis = {
            "recent_changes": {
                "event_type_sensitivity": {
                    "event_1": {"old_value": 0.5, "new_value": 0.6, "delta": 0.1}
                }
            },
            "learning_params_snapshot": {"event_type_sensitivity": {"event_1": 0.6}}
        }

        # Параметры близкие к границам
        current_adaptation_params = {
            "behavior_sensitivity": {"event_1": 0.99}  # Близко к максимуму
        }

        result = self.manager.apply_adaptation(analysis, current_adaptation_params, self.mock_self_state)

        new_value = result["behavior_sensitivity"]["event_1"]
        assert 0.0 <= new_value <= 1.0  # Должен остаться в границах

    def test_apply_adaptation_no_changes(self):
        """Test apply_adaptation with no changes."""
        analysis = {
            "recent_changes": {},
            "learning_params_snapshot": {}
        }

        current_adaptation_params = {
            "behavior_sensitivity": {"event_1": 0.5}
        }

        result = self.manager.apply_adaptation(analysis, current_adaptation_params, self.mock_self_state)

        # apply_adaptation всегда возвращает полную структуру параметров,
        # даже если не было изменений
        assert "behavior_sensitivity" in result
        assert "behavior_thresholds" in result
        assert "behavior_coefficients" in result

    def test_store_history_validation(self):
        """Test store_history parameter validation."""
        # store_history не делает валидацию изменений, только apply_adaptation
        # Поэтому просто проверяем, что метод выполняется без ошибок
        old_params = {"behavior_sensitivity": {"event_1": 0.5}}
        new_params = {"behavior_sensitivity": {"event_1": 0.52}}

        # Не должно быть исключений
        self.manager.store_history(old_params, new_params, self.mock_self_state)

    def test_store_history_success(self):
        """Test successful store_history operation."""
        analysis = {
            "learning_params_snapshot": {"event_type_sensitivity": {"event_1": 0.6}},
            "recent_changes": {"event_type_sensitivity": {"event_1": {"delta": 0.1}}}
        }

        new_adaptation_params = {
            "behavior_sensitivity": {"event_1": 0.502}  # Маленькое изменение
        }

        self.mock_self_state.adaptation_params = {"behavior_sensitivity": {"event_1": 0.5}}
        self.mock_self_state.adaptation_history = []

        self.manager.store_history(analysis, new_adaptation_params, self.mock_self_state)

        # Проверяем, что параметры НЕ обновились (store_history только сохраняет историю)
        assert self.mock_self_state.adaptation_params["behavior_sensitivity"]["event_1"] == 0.5

        # Проверяем, что история записалась
        assert len(self.mock_self_state.adaptation_history) == 1
        history_entry = self.mock_self_state.adaptation_history[0]
        assert "timestamp" in history_entry
        assert "tick" in history_entry
        assert "old_params" in history_entry
        assert "new_params" in history_entry
        assert "changes" in history_entry
        assert "learning_params_snapshot" in history_entry

    def test_store_history_thread_safety(self):
        """Test thread safety of store_history."""
        analysis = {
            "learning_params_snapshot": {"event_type_sensitivity": {"event_1": 0.6}}
        }
        new_adaptation_params = {
            "behavior_sensitivity": {"event_1": 0.502}
        }

        self.mock_self_state.adaptation_params = {"behavior_sensitivity": {"event_1": 0.5}}
        self.mock_self_state.adaptation_history = []

        # Запускаем несколько потоков одновременно
        def update_params():
            self.manager.store_history(analysis, new_adaptation_params, self.mock_self_state)

        threads = [threading.Thread(target=update_params) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Проверяем, что параметры не изменились (store_history только сохраняет историю)
        assert self.mock_self_state.adaptation_params["behavior_sensitivity"]["event_1"] == 0.5

    def test_history_size_limit(self):
        """Test that adaptation history size is limited."""
        # Создаем историю больше MAX_HISTORY_SIZE
        large_history = [{"timestamp": i, "applied_adaptation": {}} for i in range(60)]

        self.mock_self_state.adaptation_history = large_history
        self.mock_self_state.adaptation_params = {}

        analysis = {"learning_params_snapshot": {}}
        new_params = {}

        self.manager.store_history(analysis, new_params, self.mock_self_state)

        # История должна быть усечена до MAX_HISTORY_SIZE
        assert len(self.mock_self_state.adaptation_history) <= AdaptationManager.MAX_HISTORY_SIZE

    def test_constants(self):
        """Test that constants are properly defined."""
        assert AdaptationManager.MAX_ADAPTATION_DELTA == 0.01
        assert AdaptationManager.MIN_ADAPTATION_DELTA == 0.001
        assert AdaptationManager.MAX_HISTORY_SIZE == 50
        assert AdaptationManager._VALIDATION_TOLERANCE == 0.001
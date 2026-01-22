"""
Статические тесты для адаптивных порогов LearningEngine.

Проверяет базовую функциональность calculate_adaptive_thresholds().
"""

import pytest
from unittest.mock import Mock

from src.learning.learning import LearningEngine


class TestAdaptiveThresholds:
    """Тесты для адаптивных порогов LearningEngine"""

    def test_calculate_adaptive_thresholds_empty_statistics(self):
        """Тест расчета порогов для пустой статистики"""
        engine = LearningEngine()

        statistics = {}
        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert isinstance(thresholds, dict)
        assert len(thresholds) == 0

    def test_calculate_adaptive_thresholds_with_weights(self):
        """Тест расчета порогов на основе весов записей памяти"""
        engine = LearningEngine()

        # Создаем mock записи памяти с различными весами
        memory_entries = [
            Mock(weight=0.1),
            Mock(weight=0.2),
            Mock(weight=0.3),
            Mock(weight=0.4),
            Mock(weight=0.5),
        ]

        statistics = {"memory_entries": memory_entries}

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Среднее = 0.3, std ≈ 0.141
        expected_high_freq = min(0.8, max(0.05, 0.3 + 0.141))  # ≈ 0.441
        expected_low_freq = max(0.05, min(0.8, 0.3 - 0.141))  # ≈ 0.159

        assert "high_frequency_threshold" in thresholds
        assert "low_frequency_threshold" in thresholds
        assert thresholds["high_frequency_threshold"] == pytest.approx(expected_high_freq, rel=1e-3)
        assert thresholds["low_frequency_threshold"] == pytest.approx(expected_low_freq, rel=1e-3)

    def test_calculate_adaptive_thresholds_weights_bounds(self):
        """Тест ограничения порогов весов в допустимых границах"""
        engine = LearningEngine()

        # Очень маленькие веса
        memory_entries = [Mock(weight=0.01), Mock(weight=0.02), Mock(weight=0.03)]
        statistics = {"memory_entries": memory_entries}

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert thresholds["high_frequency_threshold"] >= 0.05
        assert thresholds["low_frequency_threshold"] >= 0.05

        # Очень большие веса
        memory_entries = [Mock(weight=0.9), Mock(weight=0.95), Mock(weight=0.99)]
        statistics = {"memory_entries": memory_entries}

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert thresholds["high_frequency_threshold"] <= 0.8
        assert thresholds["low_frequency_threshold"] <= 0.8

    def test_calculate_adaptive_thresholds_with_significance(self):
        """Тест расчета порогов значимости"""
        engine = LearningEngine()

        statistics = {
            "event_type_counts": {"positive": 5, "negative": 3, "neutral": 2},
            "event_type_total_significance": {
                "positive": 3.0,  # avg = 0.6
                "negative": 1.8,  # avg = 0.6
                "neutral": 0.8,  # avg = 0.4
            },
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Средняя значимость ≈ 0.533, std ≈ 0.096
        expected_high_sig = min(0.9, max(0.1, 0.5333 + 0.096 * 0.5))  # ≈ 0.581
        expected_low_sig = max(0.1, min(0.9, 0.5333 - 0.096 * 0.5))  # ≈ 0.485

        assert "high_significance_threshold" in thresholds
        assert "low_significance_threshold" in thresholds
        assert thresholds["high_significance_threshold"] == pytest.approx(
            expected_high_sig, rel=1e-3
        )
        assert thresholds["low_significance_threshold"] == pytest.approx(expected_low_sig, rel=1e-3)

    def test_calculate_adaptive_thresholds_significance_bounds(self):
        """Тест ограничения порогов значимости в допустимых границах"""
        engine = LearningEngine()

        # Очень маленькая значимость
        statistics = {
            "event_type_counts": {"event": 1},
            "event_type_total_significance": {"event": 0.05},
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert thresholds["high_significance_threshold"] >= 0.1
        assert thresholds["low_significance_threshold"] >= 0.1

        # Очень большая значимость
        statistics = {
            "event_type_counts": {"event": 1},
            "event_type_total_significance": {"event": 0.95},
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert thresholds["high_significance_threshold"] <= 0.9
        assert thresholds["low_significance_threshold"] <= 0.9

    def test_calculate_adaptive_thresholds_with_patterns(self):
        """Тест расчета порогов паттернов"""
        engine = LearningEngine()

        statistics = {"feedback_pattern_counts": {"pattern1": 10, "pattern2": 20, "pattern3": 30}}

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Частоты: 10/60≈0.167, 20/60≈0.333, 30/60≈0.5
        # Среднее ≈ 0.333, std ≈ 0.167
        expected_high_pat = min(0.8, max(0.05, 0.333 + 0.167))  # ≈ 0.5
        expected_low_pat = max(0.05, min(0.8, 0.333 - 0.167))  # ≈ 0.166

        assert "high_pattern_frequency_threshold" in thresholds
        assert "low_pattern_frequency_threshold" in thresholds
        assert thresholds["high_pattern_frequency_threshold"] == pytest.approx(
            expected_high_pat, rel=1e-3
        )
        assert thresholds["low_pattern_frequency_threshold"] == pytest.approx(
            expected_low_pat, rel=1e-3
        )

    def test_calculate_adaptive_thresholds_pattern_bounds(self):
        """Тест ограничения порогов паттернов в допустимых границах"""
        engine = LearningEngine()

        # Очень маленькие частоты паттернов
        statistics = {"feedback_pattern_counts": {"pattern": 1}}

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert thresholds["high_pattern_frequency_threshold"] >= 0.05
        assert thresholds["low_pattern_frequency_threshold"] >= 0.05

    def test_calculate_adaptive_thresholds_stability_adaptation(self):
        """Тест адаптации скорости изменения на основе стабильности"""
        engine = LearningEngine()

        # Стабильная система (низкая волатильность)
        statistics = {
            "memory_entries": [Mock(weight=0.5), Mock(weight=0.5), Mock(weight=0.5)],
            "stability_volatility": 0.1,  # Низкая волатильность
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert "learning_rate_multiplier" in thresholds
        # При низкой волатильности learning_rate_multiplier должен быть < 1.0
        assert thresholds["learning_rate_multiplier"] < 1.0

        # Нестабильная система (высокая волатильность)
        statistics["stability_volatility"] = 0.8  # Высокая волатильность

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # При высокой волатильности learning_rate_multiplier должен быть > 1.0
        assert thresholds["learning_rate_multiplier"] > 1.0

    def test_calculate_adaptive_thresholds_feedback_efficiency(self):
        """Тест адаптации на основе эффективности feedback"""
        engine = LearningEngine()

        # Высокая эффективность feedback
        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            "feedback_efficiency": 0.9,  # Высокая эффективность
            "feedback_success_rate": 0.85,
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert "feedback_learning_boost" in thresholds
        assert thresholds["feedback_learning_boost"] > 1.0

        # Низкая эффективность feedback
        statistics["feedback_efficiency"] = 0.2  # Низкая эффективность

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert thresholds["feedback_learning_boost"] < 1.0

    def test_calculate_adaptive_thresholds_time_patterns(self):
        """Тест адаптации на основе временных паттернов"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            "time_pattern_strength": 0.7,  # Сильные временные паттерны
            "temporal_consistency": 0.8,
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        assert "temporal_adaptation_factor" in thresholds
        assert thresholds["temporal_adaptation_factor"] > 1.0

    def test_calculate_adaptive_thresholds_combined_statistics(self):
        """Тест расчета всех порогов для комплексной статистики"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [
                Mock(weight=0.3),
                Mock(weight=0.4),
                Mock(weight=0.5),
                Mock(weight=0.6),
                Mock(weight=0.7),
            ],
            "event_type_counts": {"positive": 3, "negative": 2},
            "event_type_total_significance": {"positive": 1.8, "negative": 1.0},
            "feedback_pattern_counts": {"pat1": 5, "pat2": 10, "pat3": 15},
            "stability_volatility": 0.3,
            "feedback_efficiency": 0.75,
            "time_pattern_strength": 0.6,
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Проверяем, что все типы порогов рассчитаны
        expected_keys = [
            "high_frequency_threshold",
            "low_frequency_threshold",
            "high_significance_threshold",
            "low_significance_threshold",
            "high_pattern_frequency_threshold",
            "low_pattern_frequency_threshold",
            "learning_rate_multiplier",
            "feedback_learning_boost",
            "temporal_adaptation_factor",
        ]

        for key in expected_keys:
            assert key in thresholds
            assert isinstance(thresholds[key], float)
            assert 0.0 <= thresholds[key] <= 2.0  # Разумные границы

    def test_calculate_adaptive_thresholds_edge_cases(self):
        """Тест граничных случаев"""
        engine = LearningEngine()

        # Пустые массивы
        statistics = {"memory_entries": [], "event_type_counts": {}, "feedback_pattern_counts": {}}

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должны вернуться пустые пороги
        assert len(thresholds) == 0

        # Нулевые значения
        statistics = {
            "memory_entries": [Mock(weight=0.0)],
            "event_type_counts": {"event": 0},
            "event_type_total_significance": {"event": 0.0},
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должны быть рассчитаны базовые пороги
        assert "high_frequency_threshold" in thresholds
        assert "low_frequency_threshold" in thresholds

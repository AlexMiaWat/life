"""
Дымовые тесты для адаптивных порогов LearningEngine - проверка базовой функциональности "из коробки".
"""

import pytest
from unittest.mock import Mock

from src.learning.learning import LearningEngine


class TestAdaptiveThresholdsSmoke:
    """Дымовые тесты для адаптивных порогов"""

    def test_adaptive_thresholds_creation(self):
        """Создание и базовая функциональность"""
        engine = LearningEngine()

        # Проверяем наличие метода
        assert hasattr(engine, "calculate_adaptive_thresholds")
        assert callable(engine.calculate_adaptive_thresholds)

        # Проверяем константы
        assert hasattr(engine, "MIN_FREQUENCY_THRESHOLD")
        assert hasattr(engine, "MAX_FREQUENCY_THRESHOLD")
        assert hasattr(engine, "MIN_SIGNIFICANCE_THRESHOLD")
        assert hasattr(engine, "MAX_SIGNIFICANCE_THRESHOLD")

        # Проверяем диапазоны констант
        assert 0 < engine.MIN_FREQUENCY_THRESHOLD < engine.MAX_FREQUENCY_THRESHOLD
        assert 0 < engine.MIN_SIGNIFICANCE_THRESHOLD < engine.MAX_SIGNIFICANCE_THRESHOLD

    def test_basic_threshold_calculation(self):
        """Базовый расчет порогов с простыми данными"""
        engine = LearningEngine()

        # Создаем простую статистику
        statistics = {"memory_entries": [Mock(weight=0.3), Mock(weight=0.5), Mock(weight=0.7)]}

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Проверяем, что пороги рассчитаны
        assert isinstance(thresholds, dict)
        assert len(thresholds) > 0

        # Проверяем наличие основных порогов
        if "memory_entries" in statistics and statistics["memory_entries"]:
            assert "high_frequency_threshold" in thresholds
            assert "low_frequency_threshold" in thresholds

            # Проверяем разумные диапазоны
            assert 0 <= thresholds["high_frequency_threshold"] <= 1.0
            assert 0 <= thresholds["low_frequency_threshold"] <= 1.0
            assert thresholds["low_frequency_threshold"] <= thresholds["high_frequency_threshold"]

    def test_thresholds_with_significance_data(self):
        """Расчет порогов со статистикой значимости"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            "event_type_counts": {"positive": 5, "negative": 3},
            "event_type_total_significance": {
                "positive": 2.5,  # avg = 0.5
                "negative": 1.2,  # avg = 0.4
            },
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должны рассчитаться пороги значимости
        assert "high_significance_threshold" in thresholds
        assert "low_significance_threshold" in thresholds

        # Проверяем диапазоны
        assert 0 <= thresholds["high_significance_threshold"] <= 1.0
        assert 0 <= thresholds["low_significance_threshold"] <= 1.0
        assert thresholds["low_significance_threshold"] <= thresholds["high_significance_threshold"]

    def test_thresholds_with_pattern_data(self):
        """Расчет порогов со статистикой паттернов"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            "feedback_pattern_counts": {"pattern_a": 10, "pattern_b": 20, "pattern_c": 5},
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должны рассчитаться пороги паттернов
        assert "high_pattern_frequency_threshold" in thresholds
        assert "low_pattern_frequency_threshold" in thresholds

        # Проверяем диапазоны
        assert 0 <= thresholds["high_pattern_frequency_threshold"] <= 1.0
        assert 0 <= thresholds["low_pattern_frequency_threshold"] <= 1.0

    def test_thresholds_with_stability_data(self):
        """Расчет порогов с данными стабильности"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            "stability_volatility": 0.3,  # Средняя волатильность
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должен рассчитаться множитель скорости обучения
        assert "learning_rate_multiplier" in thresholds

        # Для средней волатильности должен быть близок к 1.0
        assert 0.5 <= thresholds["learning_rate_multiplier"] <= 1.5

    def test_thresholds_with_feedback_data(self):
        """Расчет порогов с данными feedback"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            "feedback_efficiency": 0.8,
            "feedback_success_rate": 0.75,
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должен рассчитаться буст обучения от feedback
        assert "feedback_learning_boost" in thresholds

        # При высокой эффективности должен быть > 1.0
        assert thresholds["feedback_learning_boost"] >= 1.0

    def test_thresholds_with_time_data(self):
        """Расчет порогов с временными данными"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            "time_pattern_strength": 0.7,
            "temporal_consistency": 0.8,
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должен рассчитаться фактор временной адаптации
        assert "temporal_adaptation_factor" in thresholds

        # При высокой силе паттернов должен быть > 1.0
        assert thresholds["temporal_adaptation_factor"] >= 1.0

    def test_thresholds_bounds_checking(self):
        """Проверка ограничения порогов в допустимых границах"""
        engine = LearningEngine()

        # Тест с экстремальными данными
        statistics = {
            "memory_entries": [
                Mock(weight=0.01),  # Очень маленькие веса
                Mock(weight=0.99),  # Очень большие веса
            ],
            "event_type_counts": {"extreme": 1},
            "event_type_total_significance": {"extreme": 0.95},
            "feedback_pattern_counts": {"extreme": 100},
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Все пороги должны быть в допустимых границах
        for key, value in thresholds.items():
            if "threshold" in key:
                if "frequency" in key:
                    assert engine.MIN_FREQUENCY_THRESHOLD <= value <= engine.MAX_FREQUENCY_THRESHOLD
                elif "significance" in key:
                    assert (
                        engine.MIN_SIGNIFICANCE_THRESHOLD
                        <= value
                        <= engine.MAX_SIGNIFICANCE_THRESHOLD
                    )
            else:
                # Другие параметры должны быть в разумных пределах
                assert 0 < value < 5.0

    def test_thresholds_empty_statistics(self):
        """Обработка пустой статистики"""
        engine = LearningEngine()

        thresholds = engine.calculate_adaptive_thresholds({})

        # Должен вернуть пустой словарь
        assert isinstance(thresholds, dict)
        assert len(thresholds) == 0

    def test_thresholds_partial_data(self):
        """Обработка частичных данных"""
        engine = LearningEngine()

        # Только некоторые типы данных
        statistics = {
            "memory_entries": [Mock(weight=0.5)],
            # Отсутствуют данные о значимости и паттернах
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Должны рассчитаться только доступные пороги
        assert "high_frequency_threshold" in thresholds
        assert "low_frequency_threshold" in thresholds

        # Не должны рассчитаться пороги значимости и паттернов
        assert "high_significance_threshold" not in thresholds
        assert "low_significance_threshold" not in thresholds
        assert "high_pattern_frequency_threshold" not in thresholds
        assert "low_pattern_frequency_threshold" not in thresholds

    def test_thresholds_consistency(self):
        """Проверка согласованности расчетов"""
        engine = LearningEngine()

        statistics = {
            "memory_entries": [Mock(weight=0.4), Mock(weight=0.6), Mock(weight=0.8)],
            "event_type_counts": {"test": 2},
            "event_type_total_significance": {"test": 1.0},
        }

        # Многократный расчет должен давать одинаковые результаты
        thresholds1 = engine.calculate_adaptive_thresholds(statistics)
        thresholds2 = engine.calculate_adaptive_thresholds(statistics)

        assert thresholds1 == thresholds2

    def test_thresholds_realistic_scenarios(self):
        """Тест с реалистичными сценариями данных"""
        engine = LearningEngine()

        # Сценарий: стабильная система с хорошим обучением
        statistics_stable = {
            "memory_entries": [
                Mock(weight=0.6),
                Mock(weight=0.7),
                Mock(weight=0.8),
                Mock(weight=0.5),
                Mock(weight=0.9),
            ],
            "event_type_counts": {"positive": 10, "negative": 5, "neutral": 8},
            "event_type_total_significance": {"positive": 6.0, "negative": 2.0, "neutral": 3.2},
            "feedback_pattern_counts": {"success": 15, "failure": 3},
            "stability_volatility": 0.2,  # Низкая волатильность
            "feedback_efficiency": 0.85,
            "time_pattern_strength": 0.6,
        }

        thresholds_stable = engine.calculate_adaptive_thresholds(statistics_stable)

        # Проверяем наличие всех типов порогов
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
            assert key in thresholds_stable
            assert isinstance(thresholds_stable[key], float)

        # Для стабильной системы learning_rate_multiplier должен быть < 1.0
        assert thresholds_stable["learning_rate_multiplier"] < 1.0

        # Для эффективного feedback boost должен быть > 1.0
        assert thresholds_stable["feedback_learning_boost"] > 1.0

    def test_thresholds_extreme_conditions(self):
        """Тест в экстремальных условиях"""
        engine = LearningEngine()

        # Сценарий: нестабильная система с плохим обучением
        statistics_unstable = {
            "memory_entries": [Mock(weight=0.1), Mock(weight=0.2), Mock(weight=0.15)],
            "event_type_counts": {"crisis": 20, "failure": 15},
            "event_type_total_significance": {"crisis": 18.0, "failure": 12.0},
            "feedback_pattern_counts": {"error": 25, "success": 2},
            "stability_volatility": 0.9,  # Высокая волатильность
            "feedback_efficiency": 0.3,  # Низкая эффективность
            "time_pattern_strength": 0.2,  # Слабые временные паттерны
        }

        thresholds_unstable = engine.calculate_adaptive_thresholds(statistics_unstable)

        # Для нестабильной системы learning_rate_multiplier должен быть > 1.0
        assert thresholds_unstable["learning_rate_multiplier"] > 1.0

        # Для неэффективного feedback boost должен быть < 1.0
        assert thresholds_unstable["feedback_learning_boost"] < 1.0

        # Все пороги должны оставаться в допустимых границах
        for key, value in thresholds_unstable.items():
            assert isinstance(value, float)
            assert value > 0

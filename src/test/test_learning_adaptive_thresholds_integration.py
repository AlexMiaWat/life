"""
Интеграционные тесты для адаптивных порогов LearningEngine - проверка взаимодействия с другими компонентами.
"""

import pytest
from unittest.mock import Mock

from src.learning.learning import LearningEngine
from src.state.self_state import SelfState
from src.memory.memory import ArchiveMemory


class TestAdaptiveThresholdsIntegration:
    """Интеграционные тесты для адаптивных порогов"""

    def test_adaptive_thresholds_with_memory_integration(self):
        """Интеграция адаптивных порогов с системой памяти"""
        engine = LearningEngine()

        # Создаем mock данные памяти, имитирующие реальную работу
        memory_entries = []

        # Имитируем записи с различными весами (более реалистичные данные)
        weights = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
        for i, weight in enumerate(weights):
            entry = Mock()
            entry.weight = weight
            entry.significance = 0.5 + (weight - 0.5) * 0.4  # Корреляция веса и значимости
            memory_entries.append(entry)

        # Создаем статистику на основе записей памяти
        statistics = {
            "memory_entries": memory_entries,
            "total_memory_entries": len(memory_entries),
            "average_weight": sum(weights) / len(weights),
            "weight_variance": sum((w - (sum(weights) / len(weights))) ** 2 for w in weights) / len(weights)
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Проверяем расчет порогов на основе реальных данных памяти
        assert "high_frequency_threshold" in thresholds
        assert "low_frequency_threshold" in thresholds

        # Проверяем, что пороги разумны для данного распределения весов
        avg_weight = statistics["average_weight"]  # ≈ 0.545
        std_weight = statistics["weight_variance"] ** 0.5  # ≈ 0.274

        expected_high = min(0.8, max(0.05, avg_weight + std_weight))
        expected_low = max(0.05, min(0.8, avg_weight - std_weight))

        assert abs(thresholds["high_frequency_threshold"] - expected_high) < 0.01
        assert abs(thresholds["low_frequency_threshold"] - expected_low) < 0.01

    def test_adaptive_thresholds_with_self_state_integration(self):
        """Интеграция с SelfState для адаптации порогов"""
        engine = LearningEngine()

        # Создаем состояние системы в различных условиях
        states = [
            {"energy": 0.9, "stability": 0.95, "integrity": 0.9},  # Стабильное состояние
            {"energy": 0.5, "stability": 0.6, "integrity": 0.7},   # Нестабильное состояние
            {"energy": 0.2, "stability": 0.3, "integrity": 0.4}    # Критическое состояние
        ]

        for state_data in states:
            # Создаем статистику с учетом состояния системы
            statistics = {
                "memory_entries": [Mock(weight=0.5) for _ in range(10)],
                "stability_volatility": 1.0 - state_data["stability"],  # Волатильность = 1 - стабильность
                "feedback_efficiency": min(1.0, state_data["energy"] * state_data["integrity"]),
                "time_pattern_strength": state_data["stability"] * 0.8
            }

            thresholds = engine.calculate_adaptive_thresholds(statistics)

            # Проверяем адаптацию к состоянию системы
            if state_data["stability"] > 0.8:  # Стабильное состояние
                assert "learning_rate_multiplier" in thresholds
                assert thresholds["learning_rate_multiplier"] < 1.0  # Замедленное обучение
            elif state_data["stability"] < 0.5:  # Нестабильное состояние
                assert thresholds["learning_rate_multiplier"] > 1.0  # Ускоренное обучение

            # Проверяем наличие всех типов порогов
            expected_keys = [
                "high_frequency_threshold", "low_frequency_threshold",
                "learning_rate_multiplier"
            ]

            for key in expected_keys:
                assert key in thresholds
                assert isinstance(thresholds[key], float)

    def test_adaptive_thresholds_with_feedback_patterns(self):
        """Интеграция с паттернами feedback для адаптации"""
        engine = LearningEngine()

        # Создаем статистику с различными паттернами feedback
        feedback_patterns = {
            "success": 50,    # Много успешных исходов
            "failure": 10,    # Мало неудач
            "timeout": 5,     # Некоторые таймауты
            "error": 2        # Мало ошибок
        }

        statistics = {
            "memory_entries": [Mock(weight=0.6) for _ in range(20)],
            "feedback_pattern_counts": feedback_patterns,
            "total_feedback_events": sum(feedback_patterns.values()),
            "feedback_success_rate": feedback_patterns["success"] / sum(feedback_patterns.values()),
            "feedback_efficiency": 0.85
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Проверяем расчет порогов паттернов
        assert "high_pattern_frequency_threshold" in thresholds
        assert "low_pattern_frequency_threshold" in thresholds

        # Вычисляем ожидаемые значения
        total_patterns = statistics["total_feedback_events"]
        pattern_freqs = [count / total_patterns for count in feedback_patterns.values()]
        pat_mean = sum(pattern_freqs) / len(pattern_freqs)
        pat_std = (sum((p - pat_mean) ** 2 for p in pattern_freqs) / len(pattern_freqs)) ** 0.5

        expected_high_pat = min(0.8, max(0.05, pat_mean + pat_std))
        expected_low_pat = max(0.05, min(0.8, pat_mean - pat_std))

        assert abs(thresholds["high_pattern_frequency_threshold"] - expected_high_pat) < 0.01
        assert abs(thresholds["low_pattern_frequency_threshold"] - expected_low_pat) < 0.01

        # При высокой эффективности feedback должен быть boost > 1.0
        assert "feedback_learning_boost" in thresholds
        assert thresholds["feedback_learning_boost"] > 1.0

    def test_adaptive_thresholds_realistic_scenario(self):
        """Реалистичный сценарий интеграции всех компонентов"""
        engine = LearningEngine()

        # Имитируем реальную статистику после периода работы системы
        statistics = {
            # Данные памяти
            "memory_entries": [
                Mock(weight=0.2, significance=0.3),
                Mock(weight=0.4, significance=0.5),
                Mock(weight=0.6, significance=0.7),
                Mock(weight=0.8, significance=0.8),
                Mock(weight=0.9, significance=0.9)
            ],

            # Статистика типов событий
            "event_type_counts": {
                "positive": 25,
                "negative": 15,
                "neutral": 30,
                "crisis": 5
            },
            "event_type_total_significance": {
                "positive": 15.0,   # avg = 0.6
                "negative": 7.5,    # avg = 0.5
                "neutral": 12.0,    # avg = 0.4
                "crisis": 4.0       # avg = 0.8
            },

            # Паттерны feedback
            "feedback_pattern_counts": {
                "learn_success": 40,
                "learn_failure": 8,
                "adapt_success": 25,
                "adapt_failure": 12
            },

            # Метрики состояния
            "stability_volatility": 0.25,      # Относительно стабильная система
            "feedback_efficiency": 0.75,       # Хорошая эффективность feedback
            "time_pattern_strength": 0.65,     # Умеренная сила временных паттернов
            "temporal_consistency": 0.7        # Хорошая временная согласованность
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Проверяем комплексный расчет всех порогов
        required_thresholds = [
            "high_frequency_threshold", "low_frequency_threshold",
            "high_significance_threshold", "low_significance_threshold",
            "high_pattern_frequency_threshold", "low_pattern_frequency_threshold",
            "learning_rate_multiplier", "feedback_learning_boost",
            "temporal_adaptation_factor"
        ]

        for threshold_name in required_thresholds:
            assert threshold_name in thresholds
            assert isinstance(thresholds[threshold_name], float)
            assert 0 < thresholds[threshold_name] < 5.0  # Разумные границы

        # Проверяем логику адаптации для стабильной системы
        assert thresholds["learning_rate_multiplier"] < 1.2  # Не слишком агрессивное обучение
        assert thresholds["feedback_learning_boost"] > 1.0   # Положительный буст от feedback
        assert thresholds["temporal_adaptation_factor"] > 1.0  # Использование временных паттернов

    def test_adaptive_thresholds_dynamic_adaptation(self):
        """Динамическая адаптация порогов при изменении условий"""
        engine = LearningEngine()

        # Исходное состояние: стабильная система
        stable_stats = {
            "memory_entries": [Mock(weight=0.7) for _ in range(10)],
            "stability_volatility": 0.1,
            "feedback_efficiency": 0.9
        }

        stable_thresholds = engine.calculate_adaptive_thresholds(stable_stats)

        # Изменение состояния: система становится нестабильной
        unstable_stats = {
            "memory_entries": [Mock(weight=0.3) for _ in range(10)],
            "stability_volatility": 0.8,
            "feedback_efficiency": 0.4
        }

        unstable_thresholds = engine.calculate_adaptive_thresholds(unstable_stats)

        # Проверяем адаптацию к изменившимся условиям
        # В нестабильном состоянии обучение должно ускориться
        assert unstable_thresholds["learning_rate_multiplier"] > stable_thresholds["learning_rate_multiplier"]

        # Эффективность feedback влияет на буст
        assert unstable_thresholds["feedback_learning_boost"] < stable_thresholds["feedback_learning_boost"]

        # Пороги частоты должны адаптироваться к распределению весов
        assert unstable_thresholds["high_frequency_threshold"] < stable_thresholds["high_frequency_threshold"]
        assert unstable_thresholds["low_frequency_threshold"] < stable_thresholds["low_frequency_threshold"]

    def test_adaptive_thresholds_with_learning_history(self):
        """Интеграция с историей обучения"""
        engine = LearningEngine()

        # Имитируем историю обучения с различными периодами
        learning_history = [
            {"period": "initial", "success_rate": 0.6, "adaptation_speed": 0.8},
            {"period": "learning", "success_rate": 0.75, "adaptation_speed": 0.9},
            {"period": "mature", "success_rate": 0.85, "adaptation_speed": 0.95}
        ]

        # Создаем статистику на основе истории обучения
        statistics = {
            "memory_entries": [Mock(weight=0.8) for _ in range(15)],
            "learning_success_trend": [h["success_rate"] for h in learning_history],
            "adaptation_effectiveness": sum(h["adaptation_speed"] for h in learning_history) / len(learning_history),
            "stability_volatility": 0.2,
            "feedback_efficiency": 0.8
        }

        thresholds = engine.calculate_adaptive_thresholds(statistics)

        # Проверяем, что пороги учитывают тренды обучения
        assert "learning_rate_multiplier" in thresholds

        # При хорошей истории обучения система должна быть консервативнее
        avg_success = sum(h["success_rate"] for h in learning_history) / len(learning_history)
        if avg_success > 0.7:
            # При высокой успешности обучения - более стабильные пороги
            assert thresholds["learning_rate_multiplier"] <= 1.0

    def test_adaptive_thresholds_error_handling_integration(self):
        """Обработка ошибок при интеграции с другими компонентами"""
        engine = LearningEngine()

        # Тест с неполными данными
        incomplete_stats = {
            "memory_entries": [Mock(weight=0.5)],
            # Отсутствуют другие поля
        }

        thresholds = engine.calculate_adaptive_thresholds(incomplete_stats)

        # Должны рассчитаться базовые пороги
        assert "high_frequency_threshold" in thresholds
        assert "low_frequency_threshold" in thresholds

        # Тест с некорректными данными
        invalid_stats = {
            "memory_entries": [Mock(weight=float('nan'))],  # Некорректные данные
        }

        # Должен обработать ошибку gracefully
        try:
            thresholds = engine.calculate_adaptive_thresholds(invalid_stats)
            # Если не выбросило исключение, проверяем базовую функциональность
            assert isinstance(thresholds, dict)
        except:
            # Если выбросило исключение, это тоже приемлемо
            pass

    def test_adaptive_thresholds_performance_integration(self):
        """Интеграция тестирования производительности"""
        import time

        engine = LearningEngine()

        # Создаем большой набор данных для тестирования производительности
        large_stats = {
            "memory_entries": [Mock(weight=0.5 + 0.1 * (i % 10)) for i in range(100)],
            "event_type_counts": {f"type_{i}": 10 + i for i in range(20)},
            "event_type_total_significance": {f"type_{i}": float(10 + i) for i in range(20)},
            "feedback_pattern_counts": {f"pattern_{i}": 5 + i for i in range(15)},
            "stability_volatility": 0.3,
            "feedback_efficiency": 0.7,
            "time_pattern_strength": 0.6
        }

        # Замеряем время расчета
        start_time = time.time()
        thresholds = engine.calculate_adaptive_thresholds(large_stats)
        end_time = time.time()

        duration = end_time - start_time

        # Проверяем, что расчет завершен
        assert len(thresholds) > 0

        # Проверяем разумное время выполнения (менее 0.1 секунды для 100 записей)
        assert duration < 0.1

        # Проверяем корректность результатов
        for key, value in thresholds.items():
            assert isinstance(value, float)
            assert not (value != value)  # Не NaN
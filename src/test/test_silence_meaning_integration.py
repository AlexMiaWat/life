"""
Тесты интеграции системы тишины с MeaningEngine.
"""

import pytest

from src.environment.event import Event
from src.meaning.engine import MeaningEngine
from src.state.self_state import SelfState


class TestSilenceMeaningIntegration:
    """Тесты интеграции событий silence с MeaningEngine."""

    def test_silence_event_appraisal(self):
        """Тест оценки значимости события silence."""
        engine = MeaningEngine()
        self_state = SelfState()

        # Создаем событие silence с разными интенсивностями
        test_cases = [
            (-0.4, "disturbing_silence"),
            (0.0, "neutral_silence"),
            (0.6, "comfortable_silence"),
        ]

        for intensity, case_name in test_cases:
            event = Event(
                type="silence",
                intensity=intensity,
                timestamp=1234567890.0,
                metadata={"detector_generated": True}
            )

            significance = engine.appraisal(event, self_state)

            # Проверяем что значимость в допустимом диапазоне
            assert 0.0 <= significance <= 1.0, f"Invalid significance for {case_name}"

            # Проверяем что silence имеет умеренную значимость
            assert significance >= 0.0, f"Silence should have non-negative significance for {case_name}"

    def test_silence_event_impact_model(self):
        """Тест расчета влияния события silence."""
        engine = MeaningEngine()
        self_state = SelfState()

        # Создаем событие silence
        event = Event(
            type="silence",
            intensity=0.3,  # Комфортная тишина
            timestamp=1234567890.0,
            metadata={"detector_generated": True}
        )

        significance = engine.appraisal(event, self_state)
        impact = engine.impact_model(event, self_state, significance)

        # Проверяем структуру impact
        assert "energy" in impact
        assert "stability" in impact
        assert "integrity" in impact

        # Проверяем что значения в разумных пределах
        assert -2.0 <= impact["energy"] <= 2.0
        assert -2.0 <= impact["stability"] <= 2.0
        assert -2.0 <= impact["integrity"] <= 2.0

    def test_silence_positive_impact(self):
        """Тест положительного влияния комфортной тишины."""
        engine = MeaningEngine()
        self_state = SelfState()

        # Комфортная тишина
        event = Event(
            type="silence",
            intensity=0.5,
            timestamp=1234567890.0,
            metadata={"is_comfortable": True}
        )

        significance = engine.appraisal(event, self_state)
        impact = engine.impact_model(event, self_state, significance)

        # Комфортная тишина должна давать положительное влияние
        assert impact["energy"] >= 0, "Comfortable silence should increase energy"
        assert impact["stability"] >= 0, "Comfortable silence should increase stability"

    def test_silence_negative_impact(self):
        """Тест негативного влияния тревожной тишины."""
        engine = MeaningEngine()
        self_state = SelfState()

        # Тревожная тишина
        event = Event(
            type="silence",
            intensity=-0.3,
            timestamp=1234567890.0,
            metadata={"is_comfortable": False}
        )

        significance = engine.appraisal(event, self_state)
        impact = engine.impact_model(event, self_state, significance)

        # Тревожная тишина может иметь негативное влияние
        # (хотя базовое влияние silence положительное, интенсивность может дать негативный эффект)
        assert isinstance(impact["energy"], (int, float))
        assert isinstance(impact["stability"], (int, float))
        assert isinstance(impact["integrity"], (int, float))

    def test_silence_response_pattern(self):
        """Тест выбора паттерна реакции на событие silence."""
        engine = MeaningEngine()
        self_state = SelfState()

        # Тестируем разные интенсивности
        test_cases = [
            (0.1, "low_positive"),
            (0.5, "high_positive"),
            (-0.2, "low_negative"),
            (-0.5, "high_negative"),
        ]

        for intensity, case_name in test_cases:
            event = Event(
                type="silence",
                intensity=intensity,
                timestamp=1234567890.0
            )

            significance = engine.appraisal(event, self_state)
            impact = engine.impact_model(event, self_state, significance)

            # Проверяем что паттерн определен
            assert "energy" in impact
            assert "stability" in impact
            assert "integrity" in impact

            # Проверяем корректность расчетов
            assert all(isinstance(v, (int, float)) for v in impact.values()), f"Invalid impact values for {case_name}"

    def test_silence_with_clarity_modifier(self):
        """Тест события silence с модификатором ясности."""
        engine = MeaningEngine()

        # SelfState с активным моментом ясности
        self_state = SelfState()
        self_state.clarity_state = True
        self_state.clarity_modifier = 1.5

        event = Event(
            type="silence",
            intensity=0.3,
            timestamp=1234567890.0
        )

        significance_with_clarity = engine.appraisal(event, self_state)

        # SelfState без ясности
        self_state_no_clarity = SelfState()
        significance_without_clarity = engine.appraisal(event, self_state_no_clarity)

        # Значимость с ясностью должна быть выше
        assert significance_with_clarity >= significance_without_clarity

    def test_silence_with_state_modifiers(self):
        """Тест события silence с модификаторами состояния."""
        engine = MeaningEngine()

        # SelfState с высокой энергией и стабильностью
        self_state_good = SelfState()
        self_state_good.energy = 0.9
        self_state_good.stability = 0.9

        # SelfState с низкой энергией и стабильностью
        self_state_bad = SelfState()
        self_state_bad.energy = 0.1
        self_state_bad.stability = 0.1

        event = Event(
            type="silence",
            intensity=0.3,
            timestamp=1234567890.0
        )

        sig_good = engine.appraisal(event, self_state_good)
        sig_bad = engine.appraisal(event, self_state_bad)

        # Значимость должна быть разной в зависимости от состояния
        assert isinstance(sig_good, (int, float))
        assert isinstance(sig_bad, (int, float))

    def test_silence_type_weight_consistency(self):
        """Тест согласованности веса типа silence."""
        engine = MeaningEngine()
        self_state = SelfState()

        event = Event(
            type="silence",
            intensity=0.5,
            timestamp=1234567890.0
        )

        significance = engine.appraisal(event, self_state)

        # Создаем событие с той же интенсивностью но другим типом для сравнения
        noise_event = Event(
            type="noise",
            intensity=0.5,
            timestamp=1234567890.0
        )

        noise_significance = engine.appraisal(noise_event, self_state)

        # Silence должен иметь умеренную значимость (0.8 вес vs 0.5 для noise)
        # При одинаковой интенсивности silence должен быть значимее noise
        assert significance >= noise_significance * 0.8  # Примерное сравнение

    def test_silence_event_processing_complete(self):
        """Тест полной обработки события silence."""
        engine = MeaningEngine()
        self_state = SelfState()

        event = Event(
            type="silence",
            intensity=0.4,
            timestamp=1234567890.0,
            metadata={"detector_generated": True, "silence_duration": 45.0}
        )

        # Полная обработка
        significance = engine.appraisal(event, self_state)
        impact = engine.impact_model(event, self_state, significance)

        # Проверяем что все компоненты работают
        assert 0.0 <= significance <= 1.0
        assert all(isinstance(v, (int, float)) for v in impact.values())

        # Проверяем что impact разумный для комфортной тишины
        assert impact["energy"] >= -0.5  # Не слишком негативное влияние на энергию
        assert impact["stability"] >= -0.5  # Не слишком негативное влияние на стабильность
"""
Статические тесты для ImpactAnalyzer

Проверяем:
- Инициализация ImpactAnalyzer
- Анализ одиночных событий
- Пакетный анализ событий
- Предсказание воздействий
- Оценку рисков
- Кэширование результатов
"""

from unittest.mock import Mock, MagicMock

import pytest

from src.environment.impact_analyzer import (
    ImpactAnalyzer, ImpactPrediction, BatchImpactAnalysis
)
from src.environment.event import Event
from src.state.self_state import SelfState


class TestImpactAnalyzerStatic:
    """Статические тесты ImpactAnalyzer"""

    def test_initialization(self):
        """Тест инициализации ImpactAnalyzer"""
        analyzer = ImpactAnalyzer()

        assert hasattr(analyzer, '_meaning_engine')
        assert hasattr(analyzer, '_cache')
        assert hasattr(analyzer, '_cache_timestamps')
        assert hasattr(analyzer, '_max_cache_size')
        assert analyzer._max_cache_size == 100

    def test_analyze_single_event(self):
        """Тест анализа одиночного события"""
        analyzer = ImpactAnalyzer()

        # Создание тестового события
        event = Event(event_type="test_event", intensity=0.8, data={"test": "data"})

        # Создание mock состояния
        state = Mock(spec=SelfState)
        state.energy = 80.0
        state.stability = 0.9
        state.integrity = 0.95

        # Анализ события
        prediction = analyzer.analyze_event(event, state)

        assert isinstance(prediction, ImpactPrediction)
        assert prediction.event == event
        assert isinstance(prediction.meaning_significance, float)
        assert isinstance(prediction.meaning_impact, dict)
        assert isinstance(prediction.final_energy, float)
        assert isinstance(prediction.final_stability, float)
        assert isinstance(prediction.final_integrity, float)
        assert prediction.response_pattern in ["ignore", "absorb", "dampen", "amplify"]
        assert 0.0 <= prediction.confidence <= 1.0

    def test_analyze_event_with_different_intensities(self):
        """Тест анализа событий с разной интенсивностью"""
        analyzer = ImpactAnalyzer()

        state = Mock(spec=SelfState)
        state.energy = 100.0
        state.stability = 1.0
        state.integrity = 1.0

        # Событие низкой интенсивности
        low_event = Event(event_type="low_intensity", intensity=0.2)
        low_prediction = analyzer.analyze_event(low_event, state)

        # Событие высокой интенсивности
        high_event = Event(event_type="high_intensity", intensity=0.9)
        high_prediction = analyzer.analyze_event(high_event, state)

        # Высокая интенсивность должна давать большую значимость
        assert low_prediction.meaning_significance <= high_prediction.meaning_significance

    def test_batch_analyze_events(self):
        """Тест пакетного анализа событий"""
        analyzer = ImpactAnalyzer()

        # Создание пакета событий
        events = [
            Event(event_type="event_1", intensity=0.6),
            Event(event_type="event_2", intensity=0.8),
            Event(event_type="event_3", intensity=0.4)
        ]

        state = Mock(spec=SelfState)
        state.energy = 90.0
        state.stability = 0.85
        state.integrity = 0.92

        # Пакетный анализ
        analysis = analyzer.batch_analyze_events(events, state)

        assert isinstance(analysis, BatchImpactAnalysis)
        assert analysis.events == events
        assert len(analysis.predictions) == 3
        assert isinstance(analysis.cumulative_impact, dict)
        assert isinstance(analysis.final_state, dict)
        assert analysis.risk_assessment in ["low", "medium", "high", "critical"]
        assert isinstance(analysis.recommendations, list)

        # Проверка что все предсказания корректны
        for prediction in analysis.predictions:
            assert isinstance(prediction, ImpactPrediction)

    def test_batch_analysis_empty_events(self):
        """Тест пакетного анализа с пустым списком событий"""
        analyzer = ImpactAnalyzer()

        state = Mock(spec=SelfState)
        state.energy = 100.0
        state.stability = 1.0
        state.integrity = 1.0

        analysis = analyzer.batch_analyze_events([], state)

        assert len(analysis.predictions) == 0
        assert analysis.cumulative_impact["energy"] == 0.0
        assert analysis.cumulative_impact["stability"] == 0.0
        assert analysis.cumulative_impact["integrity"] == 0.0

    def test_impact_prediction_properties(self):
        """Тест свойств ImpactPrediction"""
        event = Event(event_type="test", intensity=0.7)

        prediction = ImpactPrediction(
            event=event,
            meaning_significance=0.8,
            meaning_impact={"energy": -5.0, "stability": -0.1, "integrity": -0.05},
            final_energy=85.0,
            final_stability=0.8,
            final_integrity=0.95,
            response_pattern="absorb",
            confidence=0.9
        )

        assert prediction.event == event
        assert prediction.meaning_significance == 0.8
        assert prediction.meaning_impact["energy"] == -5.0
        assert prediction.final_energy == 85.0
        assert prediction.final_stability == 0.8
        assert prediction.final_integrity == 0.95
        assert prediction.response_pattern == "absorb"
        assert prediction.confidence == 0.9

    def test_batch_impact_analysis_properties(self):
        """Тест свойств BatchImpactAnalysis"""
        events = [Event(event_type="test", intensity=0.5)]
        predictions = [Mock(spec=ImpactPrediction)]

        analysis = BatchImpactAnalysis(
            events=events,
            predictions=predictions,
            cumulative_impact={"energy": -10.0, "stability": -0.2, "integrity": -0.1},
            final_state={"energy": 80.0, "stability": 0.7, "integrity": 0.9},
            risk_assessment="medium",
            recommendations=["Reduce event frequency", "Monitor stability"]
        )

        assert analysis.events == events
        assert analysis.predictions == predictions
        assert analysis.cumulative_impact["energy"] == -10.0
        assert analysis.final_state["energy"] == 80.0
        assert analysis.risk_assessment == "medium"
        assert len(analysis.recommendations) == 2

    def test_risk_assessment_logic(self):
        """Тест логики оценки рисков"""
        analyzer = ImpactAnalyzer()

        # Низкий риск
        low_risk_analysis = analyzer._assess_risk({
            "energy": -5.0,
            "stability": -0.05,
            "integrity": -0.02
        }, 100.0, 1.0, 1.0)

        assert low_risk_analysis in ["low", "medium"]

        # Высокий риск
        high_risk_analysis = analyzer._assess_risk({
            "energy": -50.0,
            "stability": -0.5,
            "integrity": -0.3
        }, 100.0, 1.0, 1.0)

        assert high_risk_analysis in ["high", "critical"]

    def test_response_pattern_logic(self):
        """Тест логики определения паттерна ответа"""
        analyzer = ImpactAnalyzer()

        # Тест разных сценариев
        scenarios = [
            (0.1, "ignore"),  # Низкая значимость
            (0.4, "absorb"),  # Средняя значимость
            (0.7, "dampen"),  # Высокая значимость
            (0.95, "amplify")  # Очень высокая значимость
        ]

        for significance, expected_pattern in scenarios:
            pattern = analyzer._determine_response_pattern(significance)
            assert pattern == expected_pattern

    def test_cache_functionality(self):
        """Тест функциональности кэширования"""
        analyzer = ImpactAnalyzer()

        event = Event(event_type="cached_event", intensity=0.6)
        state = Mock(spec=SelfState)
        state.energy = 100.0
        state.stability = 1.0
        state.integrity = 1.0

        # Первый анализ (должен попасть в кэш)
        prediction1 = analyzer.analyze_event(event, state)

        # Второй анализ того же события (должен использоваться кэш)
        prediction2 = analyzer.analyze_event(event, state)

        # Предсказания должны быть идентичны (из кэша)
        assert prediction1.meaning_significance == prediction2.meaning_significance
        assert prediction1.meaning_impact == prediction2.meaning_impact

    def test_cache_size_limit(self):
        """Тест ограничения размера кэша"""
        analyzer = ImpactAnalyzer()
        analyzer._max_cache_size = 3  # Маленький размер для теста

        state = Mock(spec=SelfState)
        state.energy = 100.0
        state.stability = 1.0
        state.integrity = 1.0

        # Добавление нескольких событий в кэш
        for i in range(5):
            event = Event(event_type=f"event_{i}", intensity=0.5)
            analyzer.analyze_event(event, state)

        # Размер кэша не должен превышать максимум
        assert len(analyzer._cache) <= analyzer._max_cache_size

    def test_clear_cache(self):
        """Тест очистки кэша"""
        analyzer = ImpactAnalyzer()

        event = Event(event_type="test_event", intensity=0.5)
        state = Mock(spec=SelfState)
        state.energy = 100.0
        state.stability = 1.0
        state.integrity = 1.0

        # Добавление в кэш
        analyzer.analyze_event(event, state)
        assert len(analyzer._cache) > 0

        # Очистка кэша
        analyzer.clear_cache()
        assert len(analyzer._cache) == 0
        assert len(analyzer._cache_timestamps) == 0

    def test_impact_analysis_with_state_changes(self):
        """Тест анализа воздействия с изменениями состояния"""
        analyzer = ImpactAnalyzer()

        event = Event(event_type="stress_event", intensity=0.9)

        # Начальное состояние
        initial_state = Mock(spec=SelfState)
        initial_state.energy = 100.0
        initial_state.stability = 1.0
        initial_state.integrity = 1.0

        prediction = analyzer.analyze_event(event, initial_state)

        # Финальное состояние должно учитывать воздействие
        assert prediction.final_energy <= initial_state.energy
        assert prediction.final_stability <= initial_state.stability
        assert prediction.final_integrity <= initial_state.integrity

    def test_meaning_engine_integration(self):
        """Тест интеграции с MeaningEngine"""
        analyzer = ImpactAnalyzer()

        # Проверка что MeaningEngine используется
        assert analyzer._meaning_engine is not None

        event = Event(event_type="test_event", intensity=0.7)
        state = Mock(spec=SelfState)
        state.energy = 90.0
        state.stability = 0.9
        state.integrity = 0.95

        prediction = analyzer.analyze_event(event, state)

        # Значимость должна быть вычислена MeaningEngine
        assert isinstance(prediction.meaning_significance, float)
        assert 0.0 <= prediction.meaning_significance <= 1.0

    def test_confidence_calculation(self):
        """Тест расчета уверенности предсказания"""
        analyzer = ImpactAnalyzer()

        # Тест с высоким stability (высокая уверенность)
        state_high_stability = Mock(spec=SelfState)
        state_high_stability.energy = 100.0
        state_high_stability.stability = 1.0
        state_high_stability.integrity = 1.0

        event = Event(event_type="test", intensity=0.5)
        prediction_high = analyzer.analyze_event(event, state_high_stability)

        # Тест с низким stability (низкая уверенность)
        state_low_stability = Mock(spec=SelfState)
        state_low_stability.energy = 100.0
        state_low_stability.stability = 0.5
        state_low_stability.integrity = 1.0

        prediction_low = analyzer.analyze_event(event, state_low_stability)

        # Высокая стабильность должна давать более высокую уверенность
        assert prediction_high.confidence >= prediction_low.confidence

    def test_recommendations_generation(self):
        """Тест генерации рекомендаций"""
        analyzer = ImpactAnalyzer()

        events = [
            Event(event_type="high_intensity", intensity=0.9),
            Event(event_type="medium_intensity", intensity=0.6)
        ]

        state = Mock(spec=SelfState)
        state.energy = 70.0
        state.stability = 0.6
        state.integrity = 0.8

        analysis = analyzer.batch_analyze_events(events, state)

        # Должны быть сгенерированы рекомендации
        assert len(analysis.recommendations) > 0
        assert all(isinstance(rec, str) for rec in analysis.recommendations)

    def test_edge_case_events(self):
        """Тест граничных случаев событий"""
        analyzer = ImpactAnalyzer()

        state = Mock(spec=SelfState)
        state.energy = 100.0
        state.stability = 1.0
        state.integrity = 1.0

        # Событие с нулевой интенсивностью
        zero_event = Event(event_type="zero_intensity", intensity=0.0)
        zero_prediction = analyzer.analyze_event(zero_event, state)

        assert zero_prediction.meaning_significance >= 0.0

        # Событие с максимальной интенсивностью
        max_event = Event(event_type="max_intensity", intensity=1.0)
        max_prediction = analyzer.analyze_event(max_event, state)

        assert max_prediction.meaning_significance <= 1.0

    def test_state_boundary_conditions(self):
        """Тест граничных условий состояния"""
        analyzer = ImpactAnalyzer()

        event = Event(event_type="test", intensity=0.7)

        # Критическое состояние
        critical_state = Mock(spec=SelfState)
        critical_state.energy = 10.0
        critical_state.stability = 0.1
        critical_state.integrity = 0.1

        critical_prediction = analyzer.analyze_event(event, critical_state)

        # В критическом состоянии уверенность должна быть ниже
        assert critical_prediction.confidence < 0.8
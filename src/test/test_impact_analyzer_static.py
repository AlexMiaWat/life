"""
Статические тесты для ImpactAnalyzer - анализатора воздействий.

Проверяет базовую функциональность анализа влияния событий на состояние системы.
"""

import pytest
from unittest.mock import Mock, patch

from src.environment.impact_analyzer import (
    ImpactAnalyzer, ImpactPrediction, BatchImpactAnalysis
)
from src.environment.event import Event
from src.state.self_state import SelfState


class TestImpactPrediction:
    """Тесты для ImpactPrediction"""

    def test_prediction_creation(self):
        """Тест создания предсказания влияния"""
        event = Event(type="test", intensity=0.5)

        prediction = ImpactPrediction(
            event=event,
            meaning_significance=0.8,
            meaning_impact={"energy": -0.1, "stability": -0.2, "integrity": 0.0},
            final_energy=0.9,
            final_stability=0.7,
            final_integrity=0.95,
            response_pattern="absorb",
            confidence=0.85
        )

        assert prediction.event == event
        assert prediction.meaning_significance == 0.8
        assert prediction.meaning_impact["energy"] == -0.1
        assert prediction.final_energy == 0.9
        assert prediction.final_stability == 0.7
        assert prediction.final_integrity == 0.95
        assert prediction.response_pattern == "absorb"
        assert prediction.confidence == 0.85


class TestBatchImpactAnalysis:
    """Тесты для BatchImpactAnalysis"""

    def test_batch_analysis_creation(self):
        """Тест создания пакетного анализа"""
        events = [
            Event(type="event1", intensity=0.3),
            Event(type="event2", intensity=0.7)
        ]

        predictions = [
            Mock(spec=ImpactPrediction),
            Mock(spec=ImpactPrediction)
        ]

        analysis = BatchImpactAnalysis(
            events=events,
            predictions=predictions,
            cumulative_impact={"energy": -0.2, "stability": -0.1, "integrity": 0.0},
            final_state={"energy": 0.8, "stability": 0.9, "integrity": 0.95},
            risk_assessment="medium",
            recommendations=["Reduce event frequency", "Monitor stability"]
        )

        assert len(analysis.events) == 2
        assert len(analysis.predictions) == 2
        assert analysis.cumulative_impact["energy"] == -0.2
        assert analysis.final_state["energy"] == 0.8
        assert analysis.risk_assessment == "medium"
        assert len(analysis.recommendations) == 2


class TestImpactAnalyzer:
    """Тесты для ImpactAnalyzer"""

    def test_analyzer_creation(self):
        """Тест создания анализатора"""
        analyzer = ImpactAnalyzer()

        assert analyzer.meaning_engine is not None
        assert analyzer.prediction_cache == {}
        assert analyzer.cache_max_size == 100

    @patch('src.environment.impact_analyzer.MeaningEngine')
    def test_analyze_event_basic(self, mock_meaning_engine_class):
        """Тест базового анализа события"""
        # Настройка mock для MeaningEngine
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.return_value = {
            'significance': 0.6,
            'impact': {'energy': -0.1, 'stability': -0.05, 'integrity': 0.0},
            'response_pattern': 'absorb'
        }
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()
        event = Event(type="test", intensity=0.5)
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        prediction = analyzer.analyze_event(event, state)

        assert isinstance(prediction, ImpactPrediction)
        assert prediction.event == event
        assert prediction.meaning_significance == 0.6
        assert prediction.meaning_impact['energy'] == -0.1
        assert prediction.final_energy == 0.9
        assert prediction.final_stability == 0.95
        assert prediction.final_integrity == 1.0
        assert prediction.response_pattern == 'absorb'
        assert prediction.confidence == 1.0  # Для базового анализа

    def test_analyze_event_with_cache(self):
        """Тест анализа события с использованием кэша"""
        analyzer = ImpactAnalyzer()

        # Создаем mock состояние
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        # Создаем mock предсказание для кэша
        cached_prediction = Mock(spec=ImpactPrediction)
        cached_prediction.meaning_significance = 0.8
        cached_prediction.meaning_impact = {'energy': -0.2, 'stability': 0.0, 'integrity': 0.0}
        cached_prediction.final_energy = 0.8
        cached_prediction.final_stability = 1.0
        cached_prediction.final_integrity = 1.0
        cached_prediction.response_pattern = 'dampen'
        cached_prediction.confidence = 0.9

        event = Event(type="test", intensity=0.5)
        cache_key = analyzer._get_cache_key(event, state)

        # Помещаем в кэш
        analyzer.prediction_cache[cache_key] = cached_prediction

        # Анализируем то же событие
        result = analyzer.analyze_event(event, state)

        # Должен вернуться кэшированный результат
        assert result == cached_prediction

    def test_analyze_event_cache_size_limit(self):
        """Тест ограничения размера кэша"""
        analyzer = ImpactAnalyzer()
        analyzer.cache_max_size = 2

        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        # Создаем 3 разных события
        events = [
            Event(type="test1", intensity=0.5),
            Event(type="test2", intensity=0.5),
            Event(type="test3", intensity=0.5)
        ]

        # Анализируем все события (с mock MeaningEngine)
        with patch('src.environment.impact_analyzer.MeaningEngine') as mock_me_class:
            mock_me = Mock()
            mock_me.analyze_meaning.return_value = {
                'significance': 0.5,
                'impact': {'energy': -0.1, 'stability': 0.0, 'integrity': 0.0},
                'response_pattern': 'ignore'
            }
            mock_me_class.return_value = mock_me

            for event in events:
                analyzer.analyze_event(event, state)

        # Кэш должен содержать только 2 последних записи
        assert len(analyzer.prediction_cache) == 2

    @patch('src.environment.impact_analyzer.MeaningEngine')
    def test_analyze_batch_events(self, mock_meaning_engine_class):
        """Тест пакетного анализа событий"""
        # Настройка mock для MeaningEngine
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.side_effect = [
            {
                'significance': 0.6,
                'impact': {'energy': -0.1, 'stability': -0.05, 'integrity': 0.0},
                'response_pattern': 'absorb'
            },
            {
                'significance': 0.4,
                'impact': {'energy': -0.05, 'stability': -0.1, 'integrity': 0.0},
                'response_pattern': 'ignore'
            }
        ]
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()
        events = [
            Event(type="event1", intensity=0.3),
            Event(type="event2", intensity=0.7)
        ]

        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        analysis = analyzer.analyze_batch_events(events, state)

        assert isinstance(analysis, BatchImpactAnalysis)
        assert len(analysis.events) == 2
        assert len(analysis.predictions) == 2
        assert analysis.cumulative_impact['energy'] == -0.15
        assert analysis.cumulative_impact['stability'] == -0.15
        assert analysis.cumulative_impact['integrity'] == 0.0
        assert analysis.final_state['energy'] == 0.85
        assert analysis.final_state['stability'] == 0.85
        assert analysis.final_state['integrity'] == 1.0

    @patch('src.environment.impact_analyzer.MeaningEngine')
    def test_analyze_batch_risk_assessment(self, mock_meaning_engine_class):
        """Тест оценки рисков в пакетном анализе"""
        mock_meaning_engine = Mock()
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()

        # Тест низкого риска
        mock_meaning_engine.analyze_meaning.return_value = {
            'significance': 0.1,
            'impact': {'energy': -0.01, 'stability': -0.01, 'integrity': 0.0},
            'response_pattern': 'ignore'
        }

        events = [Event(type="minor", intensity=0.1)]
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        analysis = analyzer.analyze_batch_events(events, state)
        assert analysis.risk_assessment == "low"

        # Тест критического риска
        mock_meaning_engine.analyze_meaning.return_value = {
            'significance': 0.9,
            'impact': {'energy': -0.5, 'stability': -0.5, 'integrity': -0.3},
            'response_pattern': 'amplify'
        }

        events = [Event(type="critical", intensity=0.9)]
        analysis = analyzer.analyze_batch_events(events, state)
        assert analysis.risk_assessment == "critical"

    def test_clear_cache(self):
        """Тест очистки кэша"""
        analyzer = ImpactAnalyzer()

        # Заполняем кэш
        analyzer.prediction_cache["key1"] = Mock()
        analyzer.prediction_cache["key2"] = Mock()

        assert len(analyzer.prediction_cache) == 2

        # Очищаем кэш
        analyzer.clear_cache()

        assert len(analyzer.prediction_cache) == 0

    def test_get_cache_stats(self):
        """Тест получения статистики кэша"""
        analyzer = ImpactAnalyzer()

        # Заполняем кэш
        analyzer.prediction_cache["key1"] = Mock()
        analyzer.prediction_cache["key2"] = Mock()
        analyzer.cache_max_size = 10

        stats = analyzer.get_cache_stats()

        assert stats['current_size'] == 2
        assert stats['max_size'] == 10
        assert stats['usage_percent'] == 20.0

    def test_get_cache_key(self):
        """Тест генерации ключа кэша"""
        analyzer = ImpactAnalyzer()

        event = Event(type="test", intensity=0.5)
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 0.8
        state.integrity = 0.9

        key = analyzer._get_cache_key(event, state)

        # Ключ должен содержать хэш от комбинации event и state
        assert isinstance(key, str)
        assert len(key) > 0

        # Одинаковые event и state должны давать одинаковый ключ
        key2 = analyzer._get_cache_key(event, state)
        assert key == key2
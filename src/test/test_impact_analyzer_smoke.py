"""
Дымовые тесты для ImpactAnalyzer - проверка базовой функциональности "из коробки".
"""

import pytest
from unittest.mock import Mock, patch

from src.environment.impact_analyzer import ImpactAnalyzer, ImpactPrediction
from src.environment.event import Event
from src.state.self_state import SelfState


class TestImpactAnalyzerSmoke:
    """Дымовые тесты для ImpactAnalyzer"""

    def test_impact_analyzer_creation(self):
        """Создание анализатора и проверка базовых свойств"""
        analyzer = ImpactAnalyzer()

        assert analyzer.meaning_engine is not None
        assert analyzer.prediction_cache == {}
        assert analyzer.cache_max_size == 100

    @patch('src.environment.impact_analyzer.MeaningEngine')
    def test_basic_event_analysis(self, mock_meaning_engine_class):
        """Базовый анализ одиночного события"""
        # Настройка mock для MeaningEngine
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.return_value = {
            'significance': 0.7,
            'impact': {'energy': -0.2, 'stability': -0.1, 'integrity': 0.0},
            'response_pattern': 'absorb'
        }
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()
        event = Event(type="smoke_test", intensity=0.6)
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 0.9
        state.integrity = 0.95

        prediction = analyzer.analyze_event(event, state)

        assert isinstance(prediction, ImpactPrediction)
        assert prediction.event == event
        assert prediction.meaning_significance == 0.7
        assert prediction.final_energy == 0.8
        assert prediction.final_stability == 0.8
        assert prediction.final_integrity == 0.95
        assert prediction.response_pattern == 'absorb'
        assert prediction.confidence > 0

    @patch('src.environment.impact_analyzer.MeaningEngine')
    def test_batch_analysis_smoke(self, mock_meaning_engine_class):
        """Базовый анализ пакета событий"""
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.side_effect = [
            {
                'significance': 0.6,
                'impact': {'energy': -0.1, 'stability': 0.0, 'integrity': -0.05},
                'response_pattern': 'absorb'
            },
            {
                'significance': 0.4,
                'impact': {'energy': -0.05, 'stability': -0.1, 'integrity': 0.0},
                'response_pattern': 'dampen'
            }
        ]
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()
        events = [
            Event(type="batch_test1", intensity=0.5),
            Event(type="batch_test2", intensity=0.3)
        ]

        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        analysis = analyzer.analyze_batch_events(events, state)

        assert analysis is not None
        assert len(analysis.events) == 2
        assert len(analysis.predictions) == 2
        assert analysis.cumulative_impact['energy'] < 0  # Должен быть отрицательным
        assert analysis.final_state['energy'] < 1.0
        assert analysis.risk_assessment in ['low', 'medium', 'high', 'critical']
        assert isinstance(analysis.recommendations, list)

    def test_cache_functionality(self):
        """Тест базовой функциональности кэша"""
        analyzer = ImpactAnalyzer()

        # Создаем mock состояние и событие
        state = Mock(spec=SelfState)
        state.energy = 0.8
        state.stability = 0.9
        state.integrity = 0.85

        event = Event(type="cache_test", intensity=0.4)

        # Первый анализ должен создать кэшированную запись
        with patch('src.environment.impact_analyzer.MeaningEngine') as mock_me_class:
            mock_me = Mock()
            mock_me.analyze_meaning.return_value = {
                'significance': 0.5,
                'impact': {'energy': -0.1, 'stability': 0.0, 'integrity': 0.0},
                'response_pattern': 'ignore'
            }
            mock_me_class.return_value = mock_me

            prediction1 = analyzer.analyze_event(event, state)

        # Второй анализ того же события должен использовать кэш
        with patch('src.environment.impact_analyzer.MeaningEngine') as mock_me_class:
            mock_me = Mock()
            mock_me_class.return_value = mock_me

            prediction2 = analyzer.analyze_event(event, state)

            # MeaningEngine не должен вызываться второй раз
            mock_me.analyze_meaning.assert_not_called()

        # Результаты должны быть одинаковыми
        assert prediction1.meaning_significance == prediction2.meaning_significance
        assert prediction1.response_pattern == prediction2.response_pattern

    def test_cache_operations(self):
        """Тест операций с кэшем"""
        analyzer = ImpactAnalyzer()

        # Заполняем кэш
        cache_key = "test_key"
        analyzer.prediction_cache[cache_key] = Mock(spec=ImpactPrediction)

        assert len(analyzer.prediction_cache) == 1

        # Получаем статистику кэша
        stats = analyzer.get_cache_stats()
        assert stats['current_size'] == 1
        assert stats['max_size'] == 100

        # Очищаем кэш
        analyzer.clear_cache()
        assert len(analyzer.prediction_cache) == 0

    @patch('src.environment.impact_analyzer.MeaningEngine')
    def test_different_event_types(self, mock_meaning_engine_class):
        """Тест анализа различных типов событий"""
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.side_effect = [
            {
                'significance': 0.8,
                'impact': {'energy': -0.3, 'stability': -0.2, 'integrity': -0.1},
                'response_pattern': 'amplify'
            },
            {
                'significance': 0.2,
                'impact': {'energy': 0.1, 'stability': 0.05, 'integrity': 0.0},
                'response_pattern': 'ignore'
            },
            {
                'significance': 0.5,
                'impact': {'energy': -0.1, 'stability': 0.0, 'integrity': 0.1},
                'response_pattern': 'absorb'
            }
        ]
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        event_types = ["crisis", "reward", "neutral"]
        predictions = []

        for event_type in event_types:
            event = Event(type=event_type, intensity=0.5)
            prediction = analyzer.analyze_event(event, state)
            predictions.append(prediction)

        # Проверяем, что все предсказания различны
        significances = [p.meaning_significance for p in predictions]
        assert len(set(significances)) == len(significances)  # Все значимости уникальны

        # Проверяем паттерны ответа
        response_patterns = [p.response_pattern for p in predictions]
        assert "amplify" in response_patterns
        assert "ignore" in response_patterns
        assert "absorb" in response_patterns

    def test_risk_assessment_various_scenarios(self):
        """Тест оценки рисков для различных сценариев"""
        analyzer = ImpactAnalyzer()

        # Тест низкого риска
        low_risk_analysis = Mock()
        low_risk_analysis.cumulative_impact = {'energy': -0.05, 'stability': -0.03, 'integrity': 0.0}
        risk = analyzer._assess_risk(low_risk_analysis)
        assert risk == "low"

        # Тест высокого риска
        high_risk_analysis = Mock()
        high_risk_analysis.cumulative_impact = {'energy': -0.6, 'stability': -0.4, 'integrity': -0.2}
        risk = analyzer._assess_risk(high_risk_analysis)
        assert risk in ["high", "critical"]

    def test_error_handling(self):
        """Тест обработки ошибок"""
        analyzer = ImpactAnalyzer()

        # Попытка анализа с некорректными данными
        with pytest.raises(AttributeError):
            analyzer.analyze_event(None, None)

        # Пакетный анализ с пустым списком
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        analysis = analyzer.analyze_batch_events([], state)
        assert len(analysis.events) == 0
        assert len(analysis.predictions) == 0

    def test_cache_key_generation(self):
        """Тест генерации ключей кэша"""
        analyzer = ImpactAnalyzer()

        event1 = Event(type="test", intensity=0.5)
        event2 = Event(type="test", intensity=0.5)  # Тот же тип и интенсивность
        state = Mock(spec=SelfState)
        state.energy = 1.0
        state.stability = 0.9
        state.integrity = 0.95

        key1 = analyzer._get_cache_key(event1, state)
        key2 = analyzer._get_cache_key(event2, state)

        # Ключи для одинаковых event и state должны совпадать
        assert key1 == key2

        # Ключи для разных событий должны отличаться
        event3 = Event(type="different", intensity=0.5)
        key3 = analyzer._get_cache_key(event3, state)
        assert key1 != key3
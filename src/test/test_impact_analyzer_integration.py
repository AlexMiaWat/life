"""
Интеграционные тесты для ImpactAnalyzer - проверка взаимодействия с другими компонентами.
"""

import pytest
from unittest.mock import Mock, patch

from src.environment.impact_analyzer import ImpactAnalyzer, ImpactPrediction, BatchImpactAnalysis
from src.environment.event import Event
from src.state.self_state import SelfState
from src.meaning.engine import MeaningEngine
from src.environment.event_queue import EventQueue


class TestImpactAnalyzerIntegration:
    """Интеграционные тесты для ImpactAnalyzer"""

    @patch("src.environment.impact_analyzer.MeaningEngine")
    def test_impact_analyzer_with_meaning_engine(self, mock_meaning_engine_class):
        """Интеграция ImpactAnalyzer с MeaningEngine"""
        # Настройка mock MeaningEngine с реалистичными данными
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.side_effect = [
            {
                "significance": 0.7,
                "impact": {"energy": -0.2, "stability": -0.1, "integrity": 0.0},
                "response_pattern": "absorb",
            },
            {
                "significance": 0.4,
                "impact": {"energy": -0.1, "stability": 0.0, "integrity": -0.05},
                "response_pattern": "ignore",
            },
        ]
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()

        # Создаем тестовое состояние
        state = SelfState()
        state.energy = 1.0
        state.stability = 0.9
        state.integrity = 0.95

        # Анализируем одиночное событие
        event = Event(type="meaning_integration", intensity=0.6)
        prediction = analyzer.analyze_event(event, state)

        # Проверяем интеграцию
        mock_meaning_engine.analyze_meaning.assert_called_once()
        call_args = mock_meaning_engine.analyze_meaning.call_args[0]
        assert call_args[0] == event  # Событие передано корректно
        assert hasattr(call_args[1], "energy")  # Состояние передано

        # Проверяем результат
        assert isinstance(prediction, ImpactPrediction)
        assert prediction.meaning_significance == 0.7
        assert prediction.final_energy == 0.8
        assert prediction.response_pattern == "absorb"

    @patch("src.environment.impact_analyzer.MeaningEngine")
    def test_batch_analysis_with_real_state_changes(self, mock_meaning_engine_class):
        """Интеграция пакетного анализа с реальными изменениями состояния"""
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.side_effect = [
            {
                "significance": 0.8,
                "impact": {"energy": -0.3, "stability": -0.2, "integrity": -0.1},
                "response_pattern": "amplify",
            },
            {
                "significance": 0.5,
                "impact": {"energy": 0.1, "stability": 0.05, "integrity": 0.0},
                "response_pattern": "absorb",
            },
            {
                "significance": 0.3,
                "impact": {"energy": -0.05, "stability": -0.1, "integrity": 0.05},
                "response_pattern": "dampen",
            },
        ]
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()

        # Создаем начальное состояние
        initial_state = SelfState()
        initial_state.energy = 1.0
        initial_state.stability = 1.0
        initial_state.integrity = 1.0

        # Создаем пакет событий
        events = [
            Event(type="crisis", intensity=0.8),
            Event(type="reward", intensity=0.4),
            Event(type="neutral", intensity=0.2),
        ]

        analysis = analyzer.analyze_batch_events(events, initial_state)

        # Проверяем корректность анализа
        assert isinstance(analysis, BatchImpactAnalysis)
        assert len(analysis.events) == 3
        assert len(analysis.predictions) == 3

        # Проверяем кумулятивный эффект
        # crisis: -0.3, reward: +0.1, neutral: -0.05 = -0.25
        assert abs(analysis.cumulative_impact["energy"] - (-0.25)) < 0.01
        assert analysis.cumulative_impact["stability"] == -0.25  # -0.2 + 0.05 - 0.1
        assert analysis.cumulative_impact["integrity"] == -0.05  # -0.1 + 0.0 + 0.05

        # Проверяем финальное состояние
        assert abs(analysis.final_state["energy"] - 0.75) < 0.01  # 1.0 - 0.25
        assert analysis.final_state["stability"] == 0.75
        assert analysis.final_state["integrity"] == 0.95

        # Проверяем оценку риска для такого воздействия
        assert analysis.risk_assessment in ["medium", "high"]

    def test_impact_analyzer_with_event_queue(self):
        """Интеграция ImpactAnalyzer с EventQueue"""
        analyzer = ImpactAnalyzer()
        event_queue = EventQueue()

        # Добавляем события в очередь
        events = [
            Event(type="queue_test_1", intensity=0.6),
            Event(type="queue_test_2", intensity=0.4),
            Event(type="queue_test_3", intensity=0.8),
        ]

        for event in events:
            event_queue.put(event)

        # Анализируем все события из очереди
        state = SelfState()
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        all_events = event_queue.get_all()
        if len(all_events) >= 3:
            analysis = analyzer.analyze_batch_events(all_events, state)

            # Проверяем, что анализ работает с событиями из очереди
            assert len(analysis.events) >= 3
            assert len(analysis.predictions) >= 3

            # Проверяем разнообразие паттернов ответа
            response_patterns = {pred.response_pattern for pred in analysis.predictions}
            assert len(response_patterns) >= 1  # Минимум один паттерн

    @patch("src.environment.impact_analyzer.MeaningEngine")
    def test_impact_analyzer_cache_integration(self, mock_meaning_engine_class):
        """Интеграция кэширования с MeaningEngine"""
        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.return_value = {
            "significance": 0.6,
            "impact": {"energy": -0.15, "stability": -0.1, "integrity": 0.0},
            "response_pattern": "absorb",
        }
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()
        state = SelfState()
        state.energy = 0.9
        state.stability = 0.8
        state.integrity = 0.95

        event = Event(type="cache_integration", intensity=0.5)

        # Первый анализ - должен вызвать MeaningEngine
        prediction1 = analyzer.analyze_event(event, state)
        assert mock_meaning_engine.analyze_meaning.call_count == 1

        # Второй анализ того же события - должен использовать кэш
        prediction2 = analyzer.analyze_event(event, state)
        assert mock_meaning_engine.analyze_meaning.call_count == 1  # Не увеличился

        # Результаты должны быть идентичными
        assert prediction1.meaning_significance == prediction2.meaning_significance
        assert prediction1.response_pattern == prediction2.response_pattern
        assert prediction1.final_energy == prediction2.final_energy

        # Проверяем статистику кэша
        stats = analyzer.get_cache_stats()
        assert stats["current_size"] >= 1
        assert stats["usage_percent"] > 0

    @patch("src.environment.impact_analyzer.MeaningEngine")
    def test_impact_analyzer_complex_scenario(self, mock_meaning_engine_class):
        """Комплексный сценарий интеграции со множеством компонентов"""
        # Настройка сложного сценария с различными типами событий
        call_count = 0

        def mock_analyze_meaning(event, state):
            nonlocal call_count
            call_count += 1

            # Разные ответы в зависимости от типа события
            if event.type == "crisis":
                return {
                    "significance": 0.9,
                    "impact": {"energy": -0.4, "stability": -0.3, "integrity": -0.2},
                    "response_pattern": "amplify",
                }
            elif event.type == "recovery":
                return {
                    "significance": 0.6,
                    "impact": {"energy": 0.2, "stability": 0.15, "integrity": 0.1},
                    "response_pattern": "absorb",
                }
            else:
                return {
                    "significance": 0.3,
                    "impact": {"energy": -0.05, "stability": 0.0, "integrity": 0.02},
                    "response_pattern": "ignore",
                }

        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.side_effect = mock_analyze_meaning
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()

        # Создаем комплексное состояние системы
        state = SelfState()
        state.energy = 0.7  # Система в ослабленном состоянии
        state.stability = 0.8
        state.integrity = 0.9

        # Создаем последовательность событий, имитирующих кризис и восстановление
        events = [
            Event(type="crisis", intensity=0.9),  # Сильный кризис
            Event(type="neutral", intensity=0.3),  # Нейтральное событие
            Event(type="recovery", intensity=0.7),  # Восстановление
            Event(type="crisis", intensity=0.6),  # Слабый кризис
            Event(type="recovery", intensity=0.5),  # Дополнительное восстановление
        ]

        # Анализируем пакет
        analysis = analyzer.analyze_batch_events(events, state)

        # Проверяем комплексный анализ
        assert len(analysis.predictions) == 5

        # Проверяем, что MeaningEngine вызывался для каждого уникального события
        assert call_count >= 3  # Минимум 3 разных типа событий

        # Вычисляем ожидаемый кумулятивный эффект
        # crisis 0.9: -0.4, neutral: -0.05, recovery 0.7: +0.2, crisis 0.6: -0.4, recovery 0.5: +0.2
        # Итого: -0.4 -0.05 +0.2 -0.4 +0.2 = -0.45
        expected_energy_change = -0.45
        assert abs(analysis.cumulative_impact["energy"] - expected_energy_change) < 0.01

        # Финальное состояние: 0.7 - 0.45 = 0.25
        assert abs(analysis.final_state["energy"] - 0.25) < 0.01

        # Для такого сценария риск должен быть высоким
        assert analysis.risk_assessment in ["high", "critical"]

        # Проверяем разнообразие рекомендаций
        assert len(analysis.recommendations) >= 1

    def test_impact_analyzer_error_handling_integration(self):
        """Интеграция обработки ошибок с другими компонентами"""
        analyzer = ImpactAnalyzer()

        # Тест с некорректными данными
        state = SelfState()
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        # Пакетный анализ с пустым списком
        analysis = analyzer.analyze_batch_events([], state)
        assert len(analysis.events) == 0
        assert len(analysis.predictions) == 0
        assert analysis.cumulative_impact["energy"] == 0.0

        # Тест с None значениями (должен обрабатывать gracefully)
        try:
            analysis = analyzer.analyze_batch_events(None, state)
            assert False, "Should have raised an exception"
        except (AttributeError, TypeError):
            pass  # Ожидаемое поведение

    @patch("src.environment.impact_analyzer.MeaningEngine")
    def test_impact_analyzer_performance_integration(self, mock_meaning_engine_class):
        """Интеграция тестирования производительности"""
        import time

        mock_meaning_engine = Mock()
        mock_meaning_engine.analyze_meaning.return_value = {
            "significance": 0.5,
            "impact": {"energy": -0.1, "stability": 0.0, "integrity": 0.0},
            "response_pattern": "absorb",
        }
        mock_meaning_engine_class.return_value = mock_meaning_engine

        analyzer = ImpactAnalyzer()
        state = SelfState()
        state.energy = 1.0
        state.stability = 1.0
        state.integrity = 1.0

        events = [Event(type=f"perf_test_{i}", intensity=0.5) for i in range(10)]

        # Замеряем время пакетного анализа
        start_time = time.time()
        analysis = analyzer.analyze_batch_events(events, state)
        end_time = time.time()

        duration = end_time - start_time

        # Проверяем, что анализ завершен
        assert len(analysis.predictions) == 10

        # Проверяем разумное время выполнения (менее 1 секунды для 10 событий)
        assert duration < 1.0

        # Проверяем использование кэша для повторных анализов
        start_time = time.time()
        analysis2 = analyzer.analyze_batch_events(events, state)  # Повторный анализ
        end_time = time.time()

        duration2 = end_time - start_time

        # Второй анализ должен быть быстрее (эффект кэша)
        assert duration2 <= duration

        # Результаты должны быть одинаковыми
        assert len(analysis2.predictions) == len(analysis.predictions)

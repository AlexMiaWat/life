"""
Тесты для философского анализатора поведения системы Life.
"""

import pytest
from unittest.mock import Mock, MagicMock

from src.philosophical.philosophical_analyzer import PhilosophicalAnalyzer
from src.philosophical.metrics import PhilosophicalMetrics


class TestPhilosophicalAnalyzer:
    """Тесты для PhilosophicalAnalyzer."""

    def test_initialization(self):
        """Тест инициализации анализатора."""
        analyzer = PhilosophicalAnalyzer()
        assert analyzer.self_awareness_analyzer is not None
        assert analyzer.adaptation_quality_analyzer is not None
        assert analyzer.ethical_behavior_analyzer is not None
        assert analyzer.conceptual_integrity_analyzer is not None
        assert analyzer.life_vitality_evaluator is not None
        assert analyzer.analysis_history == []

    def test_analyze_behavior_basic(self):
        """Тест базового анализа поведения."""
        analyzer = PhilosophicalAnalyzer()

        # Создаем mock объекты
        self_state = Mock()
        self_state.energy = 75.0
        self_state.integrity = 0.9
        self_state.stability = 0.8
        self_state.age = 100.0
        self_state.subjective_time = 120.0
        self_state.ticks = 1000
        self_state.energy_history = [70, 72, 75, 78, 75]
        self_state.stability_history = [0.7, 0.75, 0.8, 0.82, 0.8]
        self_state.fatigue = 20.0
        self_state.tension = 15.0

        memory = Mock()
        memory.get_statistics.return_value = {'total_entries': 150, 'archived_entries': 30}

        learning_engine = Mock()
        learning_engine.learning_params = {'event_type_sensitivity': 0.8, 'significance_thresholds': 0.3}
        learning_engine.learning_statistics = {'events_processed': 100, 'patterns_learned': 25}

        adaptation_manager = Mock()
        adaptation_manager.adaptation_params = {'behavior_sensitivity': 0.7, 'behavior_thresholds': 0.5}
        adaptation_manager.adaptation_history = [{'behavior_sensitivity': 0.6}, {'behavior_sensitivity': 0.65}, {'behavior_sensitivity': 0.7}]

        decision_engine = Mock()

        # Выполняем анализ
        metrics = analyzer.analyze_behavior(
            self_state, memory, learning_engine, adaptation_manager, decision_engine
        )

        # Проверяем, что метрики созданы
        assert isinstance(metrics, PhilosophicalMetrics)
        assert 0.0 <= metrics.philosophical_index <= 1.0
        assert len(analyzer.analysis_history) == 1

    def test_get_philosophical_insights(self):
        """Тест генерации философских insights."""
        analyzer = PhilosophicalAnalyzer()

        # Создаем тестовые метрики
        metrics = PhilosophicalMetrics()
        metrics.self_awareness.overall_self_awareness = 0.7
        metrics.adaptation_quality.overall_adaptation_quality = 0.8
        metrics.ethical_behavior.overall_ethical_score = 0.6
        metrics.conceptual_integrity.overall_integrity = 0.75
        metrics.life_vitality.overall_vitality = 0.65
        metrics.philosophical_index = 0.7

        insights = analyzer.get_philosophical_insights(metrics)

        assert isinstance(insights, dict)
        assert 'overall' in insights
        assert 'self_awareness' in insights
        assert 'adaptation' in insights
        assert 'ethics' in insights
        assert 'conceptual_integrity' in insights
        assert 'life_vitality' in insights

        # Проверяем, что insights содержат текст
        for key, value in insights.items():
            assert isinstance(value, str)
            assert len(value) > 10

    def test_analyze_trends_insufficient_data(self):
        """Тест анализа трендов при недостатке данных."""
        analyzer = PhilosophicalAnalyzer()
        trends = analyzer.analyze_trends()

        assert trends == {}

    def test_analyze_trends_with_data(self):
        """Тест анализа трендов с данными."""
        analyzer = PhilosophicalAnalyzer()

        # Добавляем тестовые данные в историю
        for i in range(5):
            metrics = PhilosophicalMetrics()
            metrics.philosophical_index = 0.5 + i * 0.1
            metrics.self_awareness.overall_self_awareness = 0.6 + i * 0.05
            analyzer.analysis_history.append(metrics.to_dict())

        trends = analyzer.analyze_trends()

        assert isinstance(trends, dict)
        assert 'philosophical_index' in trends
        assert 'self_awareness.overall_self_awareness' in trends

        # Проверяем структуру тренда
        philosophical_trend = trends['philosophical_index']
        assert 'trend' in philosophical_trend
        assert 'slope' in philosophical_trend
        assert 'volatility' in philosophical_trend

    def test_generate_philosophical_report(self):
        """Тест генерации философского отчета."""
        analyzer = PhilosophicalAnalyzer()

        # Создаем тестовые метрики
        metrics = PhilosophicalMetrics()
        metrics.self_awareness.overall_self_awareness = 0.7
        metrics.adaptation_quality.overall_adaptation_quality = 0.8
        metrics.ethical_behavior.overall_ethical_score = 0.6
        metrics.conceptual_integrity.overall_integrity = 0.75
        metrics.life_vitality.overall_vitality = 0.65
        metrics.philosophical_index = 0.7

        report = analyzer.generate_philosophical_report(metrics)

        assert isinstance(report, str)
        assert len(report) > 100
        assert "ФИЛОСОФСКИЙ АНАЛИЗ" in report
        assert "ОБЩИЙ ФИЛОСОФСКИЙ ИНДЕКС" in report
        assert "=" * 80 in report

    def test_extract_nested_value(self):
        """Тест извлечения вложенных значений."""
        analyzer = PhilosophicalAnalyzer()

        data = {
            'self_awareness': {
                'overall_self_awareness': 0.75
            },
            'philosophical_index': 0.8
        }

        # Тест успешного извлечения
        value = analyzer._extract_nested_value(data, 'self_awareness.overall_self_awareness')
        assert value == 0.75

        value = analyzer._extract_nested_value(data, 'philosophical_index')
        assert value == 0.8

        # Тест извлечения несуществующего значения
        value = analyzer._extract_nested_value(data, 'nonexistent.path')
        assert value is None

    def test_calculate_trend(self):
        """Тест вычисления тренда."""
        analyzer = PhilosophicalAnalyzer()

        # Тест возрастающего тренда
        values = [0.5, 0.6, 0.7, 0.8, 0.9]
        trend = analyzer._calculate_trend(values)

        assert trend['trend'] == 'improving'
        assert trend['slope'] > 0
        assert 'volatility' in trend
        assert trend['start_value'] == 0.5
        assert trend['end_value'] == 0.9
        assert trend['change'] == 0.4

        # Тест стабильного тренда
        values = [0.7, 0.69, 0.71, 0.7, 0.7]
        trend = analyzer._calculate_trend(values)

        assert trend['trend'] == 'stable'

        # Тест недостатка данных
        values = [0.5]
        trend = analyzer._calculate_trend(values)

        assert trend['trend'] == 'insufficient_data'
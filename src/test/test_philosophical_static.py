"""
Статические тесты для компонентов философского анализа.

Проверяют корректность работы отдельных компонентов без зависимостей от внешних систем.
"""

import pytest
from unittest.mock import Mock, MagicMock

from src.philosophical.self_awareness import SelfAwarenessAnalyzer
from src.philosophical.adaptation_quality import AdaptationQualityAnalyzer
from src.philosophical.ethical_behavior import EthicalBehaviorAnalyzer
from src.philosophical.conceptual_integrity import ConceptualIntegrityAnalyzer
from src.philosophical.life_vitality import LifeVitalityEvaluator
from src.philosophical.metrics import (
    SelfAwarenessMetrics,
    AdaptationQualityMetrics,
    EthicalBehaviorMetrics,
    ConceptualIntegrityMetrics,
    LifeVitalityMetrics,
    PhilosophicalMetrics
)


class TestSelfAwarenessAnalyzer:
    """Статические тесты для SelfAwarenessAnalyzer."""

    def test_initialization(self):
        """Тест инициализации анализатора самоосознания."""
        analyzer = SelfAwarenessAnalyzer()
        assert analyzer.history_window == 100
        assert hasattr(analyzer, 'analyze_self_awareness')

    def test_analyze_state_awareness_complete_data(self):
        """Тест анализа осознания состояния с полными данными."""
        analyzer = SelfAwarenessAnalyzer()

        # Создаем mock self_state с полными данными
        self_state = Mock()
        self_state.energy_history = [70, 72, 75, 78, 75, 80, 82, 85, 83, 80, 78, 75]
        self_state.stability_history = [0.7, 0.75, 0.8, 0.82, 0.8, 0.78, 0.75, 0.8, 0.82, 0.85, 0.83, 0.8]
        self_state.age = 1000.0
        self_state.subjective_time = 1200.0

        score = analyzer._analyze_state_awareness(self_state)

        assert 0.0 <= score <= 1.0
        assert score > 0.2  # Должен быть балл выше минимального при полных данных

    def test_analyze_state_awareness_minimal_data(self):
        """Тест анализа осознания состояния с минимальными данными."""
        analyzer = SelfAwarenessAnalyzer()

        # Создаем mock self_state с минимальными данными
        self_state = Mock()
        self_state.energy_history = [75]
        self_state.stability_history = []
        self_state.age = 10.0
        self_state.subjective_time = 5.0

        score = analyzer._analyze_state_awareness(self_state)

        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Должен быть низкий балл при минимальных данных

    def test_analyze_behavioral_reflection_with_memory(self):
        """Тест анализа рефлексии поведения с памятью."""
        analyzer = SelfAwarenessAnalyzer()

        self_state = Mock()
        self_state.recent_events = [{'type': 'decision', 'significance': 0.8}] * 25
        self_state.last_significance = 0.7

        memory = Mock()
        memory.get_statistics.return_value = {'total_entries': 100, 'archived_entries': 20}

        score = analyzer._analyze_behavioral_reflection(self_state, memory)

        assert 0.0 <= score <= 1.0
        assert score > 0.2  # Балл при хороших данных

    def test_analyze_temporal_awareness_complete(self):
        """Тест анализа временного осознания с полными данными."""
        analyzer = SelfAwarenessAnalyzer()

        self_state = Mock()
        self_state.age = 1000.0
        self_state.subjective_time = 1200.0
        self_state.ticks = 5000

        score = analyzer._analyze_temporal_awareness(self_state)

        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Балл при всех факторах

    def test_analyze_self_regulation_optimal(self):
        """Тест анализа саморегуляции при оптимальных параметрах."""
        analyzer = SelfAwarenessAnalyzer()

        self_state = Mock()
        self_state.energy = 60.0  # Оптимальный диапазон
        self_state.integrity = 0.85  # Высокая целостность
        self_state.stability = 0.8  # Хорошая стабильность
        self_state.fatigue = 30.0  # Низкая усталость

        score = analyzer._analyze_self_regulation(self_state)

        assert 0.0 <= score <= 1.0
        assert score > 0.2  # Балл при оптимальных параметрах

    def test_calculate_overall_self_awareness(self):
        """Тест вычисления общего уровня самоосознания."""
        analyzer = SelfAwarenessAnalyzer()

        metrics = SelfAwarenessMetrics()
        metrics.state_awareness = 0.8
        metrics.behavioral_reflection = 0.7
        metrics.temporal_awareness = 0.9
        metrics.self_regulation = 0.6

        overall = analyzer._calculate_overall_self_awareness(metrics)

        assert 0.0 <= overall <= 1.0
        # Проверка взвешенного среднего
        expected = (0.8 * 0.3 + 0.7 * 0.25 + 0.9 * 0.25 + 0.6 * 0.2)
        assert abs(overall - expected) < 0.01


class TestAdaptationQualityAnalyzer:
    """Статические тесты для AdaptationQualityAnalyzer."""

    def test_initialization(self):
        """Тест инициализации анализатора качества адаптации."""
        analyzer = AdaptationQualityAnalyzer()
        assert analyzer.history_window == 50
        assert hasattr(analyzer, 'analyze_adaptation_quality')

    def test_analyze_adaptation_effectiveness_high(self):
        """Тест анализа эффективности адаптации при высоких показателях."""
        analyzer = AdaptationQualityAnalyzer()

        self_state = Mock()
        self_state.stability = 0.85
        self_state.energy = 70.0

        adaptation_manager = Mock()
        adaptation_manager.get_adaptation_statistics.return_value = {
            'total_adaptations': 50,
            'successful_adaptations': 45,
            'avg_adaptation_time': 5.0
        }

        score = analyzer._analyze_adaptation_effectiveness(self_state, adaptation_manager)

        assert 0.0 <= score <= 1.0
        assert score > 0.05  # Балл при хороших показателях

    def test_analyze_adaptation_stability_stable(self):
        """Тест анализа стабильности адаптации при стабильных изменениях."""
        analyzer = AdaptationQualityAnalyzer()

        adaptation_manager = Mock()
        adaptation_manager.get_adaptation_history.return_value = [
            {'behavior_sensitivity': 0.7, 'threshold': 0.5},
            {'behavior_sensitivity': 0.72, 'threshold': 0.52},
            {'behavior_sensitivity': 0.71, 'threshold': 0.51},
            {'behavior_sensitivity': 0.69, 'threshold': 0.49},
            {'behavior_sensitivity': 0.7, 'threshold': 0.5}
        ]

        score = analyzer._analyze_adaptation_stability(adaptation_manager)

        assert 0.0 <= score <= 1.0
        assert score > 0.04  # Балл при стабильных изменениях

    def test_analyze_predictive_quality_good(self):
        """Тест анализа качества предсказания при хороших данных."""
        analyzer = AdaptationQualityAnalyzer()

        self_state = Mock()
        self_state.energy_history = [60, 65, 70, 68, 72, 75, 73, 78, 80, 82]
        self_state.stability_history = [0.7, 0.75, 0.8, 0.78, 0.82, 0.85, 0.83, 0.87, 0.9, 0.88]

        learning_engine = Mock()
        learning_engine.get_prediction_accuracy.return_value = 0.85

        score = analyzer._analyze_predictive_quality(self_state, learning_engine)

        assert 0.0 <= score <= 1.0
        assert score > 0.07  # Балл при хороших данных


class TestEthicalBehaviorAnalyzer:
    """Статические тесты для EthicalBehaviorAnalyzer."""

    def test_initialization(self):
        """Тест инициализации анализатора этического поведения."""
        analyzer = EthicalBehaviorAnalyzer()
        assert hasattr(analyzer, 'analyze_ethical_behavior')


class TestConceptualIntegrityAnalyzer:
    """Статические тесты для ConceptualIntegrityAnalyzer."""

    def test_initialization(self):
        """Тест инициализации анализатора концептуальной целостности."""
        analyzer = ConceptualIntegrityAnalyzer()
        assert hasattr(analyzer, 'analyze_conceptual_integrity')


class TestLifeVitalityEvaluator:
    """Статические тесты для LifeVitalityEvaluator."""

    def test_initialization(self):
        """Тест инициализации оценщика жизненной силы."""
        evaluator = LifeVitalityEvaluator()
        assert hasattr(evaluator, 'evaluate_life_vitality')


class TestPhilosophicalMetrics:
    """Статические тесты для структур метрик."""

    def test_self_awareness_metrics_creation(self):
        """Тест создания метрик самоосознания."""
        metrics = SelfAwarenessMetrics()

        assert 0.0 <= metrics.state_awareness <= 1.0
        assert 0.0 <= metrics.behavioral_reflection <= 1.0
        assert 0.0 <= metrics.temporal_awareness <= 1.0
        assert 0.0 <= metrics.self_regulation <= 1.0
        assert 0.0 <= metrics.overall_self_awareness <= 1.0
        assert isinstance(metrics.history, list)

    def test_adaptation_quality_metrics_creation(self):
        """Тест создания метрик качества адаптации."""
        metrics = AdaptationQualityMetrics()

        assert 0.0 <= metrics.adaptation_effectiveness <= 1.0
        assert 0.0 <= metrics.adaptation_stability <= 1.0
        assert 0.0 <= metrics.adaptation_speed <= 1.0
        assert 0.0 <= metrics.predictive_quality <= 1.0
        assert 0.0 <= metrics.overall_adaptation_quality <= 1.0
        assert isinstance(metrics.parameter_history, list)

    def test_ethical_behavior_metrics_creation(self):
        """Тест создания метрик этического поведения."""
        metrics = EthicalBehaviorMetrics()

        assert 0.0 <= metrics.norm_compliance <= 1.0
        assert 0.0 <= metrics.consequence_awareness <= 1.0
        assert 0.0 <= metrics.ethical_consistency <= 1.0
        assert 0.0 <= metrics.dilemma_resolution <= 1.0
        assert 0.0 <= metrics.overall_ethical_score <= 1.0
        assert isinstance(metrics.ethical_decisions_history, list)

    def test_conceptual_integrity_metrics_creation(self):
        """Тест создания метрик концептуальной целостности."""
        metrics = ConceptualIntegrityMetrics()

        assert 0.0 <= metrics.model_integrity <= 1.0
        assert 0.0 <= metrics.behavioral_consistency <= 1.0
        assert 0.0 <= metrics.conceptual_stability <= 1.0
        assert 0.0 <= metrics.conceptual_learning <= 1.0
        assert 0.0 <= metrics.overall_integrity <= 1.0
        assert isinstance(metrics.conceptual_changes_history, list)

    def test_life_vitality_metrics_creation(self):
        """Тест создания метрик жизненной силы."""
        metrics = LifeVitalityMetrics()

        assert 0.0 <= metrics.vitality_level <= 1.0
        assert 0.0 <= metrics.environmental_adaptability <= 1.0
        assert 0.0 <= metrics.internal_harmony <= 1.0
        assert 0.0 <= metrics.developmental_potential <= 1.0
        assert 0.0 <= metrics.overall_vitality <= 1.0
        assert isinstance(metrics.vitality_trends, list)

    def test_philosophical_metrics_creation(self):
        """Тест создания общих философских метрик."""
        metrics = PhilosophicalMetrics()

        assert isinstance(metrics.self_awareness, SelfAwarenessMetrics)
        assert isinstance(metrics.adaptation_quality, AdaptationQualityMetrics)
        assert isinstance(metrics.ethical_behavior, EthicalBehaviorMetrics)
        assert isinstance(metrics.conceptual_integrity, ConceptualIntegrityMetrics)
        assert isinstance(metrics.life_vitality, LifeVitalityMetrics)
        assert 0.0 <= metrics.philosophical_index <= 1.0

    def test_philosophical_metrics_to_dict_conversion(self):
        """Тест преобразования философских метрик в словарь."""
        metrics = PhilosophicalMetrics()
        metrics.philosophical_index = 0.75

        data = metrics.to_dict()

        assert isinstance(data, dict)
        assert 'philosophical_index' in data
        assert 'self_awareness' in data
        assert 'adaptation_quality' in data
        assert 'ethical_behavior' in data
        assert 'conceptual_integrity' in data
        assert 'life_vitality' in data
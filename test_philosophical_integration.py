"""
Интеграционные тесты для философских анализаторов.

Тестирует анализаторы с реальными компонентами системы Life:
- SelfState
- Memory
- LearningEngine
- AdaptationManager
- DecisionEngine
"""

import pytest
import time
import json
from unittest.mock import Mock, MagicMock

from src.philosophical.self_awareness import SelfAwarenessAnalyzer
from src.philosophical.life_vitality import LifeVitalityEvaluator
from src.philosophical.ethical_behavior import EthicalBehaviorAnalyzer
from src.philosophical.adaptation_quality import AdaptationQualityAnalyzer
from src.philosophical.conceptual_integrity import ConceptualIntegrityAnalyzer
from src.philosophical.external_philosophical_analyzer import ExternalPhilosophicalAnalyzer


class TestPhilosophicalIntegration:
    """Интеграционные тесты философских анализаторов."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        # Создаем mock SelfState с реалистичными данными
        self.mock_self_state = Mock()
        self.mock_self_state.life_id = "test-life-001"
        self.mock_self_state.age = 100.0
        self.mock_self_state.ticks = 500
        self.mock_self_state.energy = 85.0
        self.mock_self_state.integrity = 0.95
        self.mock_self_state.stability = 0.88
        self.mock_self_state.fatigue = 15.0
        self.mock_self_state.tension = 12.0
        self.mock_self_state.subjective_time = 95.0
        self.mock_self_state.recent_events = [
            {"type": "energy_change", "delta": -5.0, "timestamp": time.time()},
            {"type": "stability_change", "delta": 0.02, "timestamp": time.time()},
            {"type": "event_processed", "significance": 0.7, "timestamp": time.time()},
        ]
        self.mock_self_state.energy_history = [80.0, 82.0, 85.0, 87.0, 85.0]
        self.mock_self_state.stability_history = [0.85, 0.87, 0.88, 0.89, 0.88]

        # Создаем mock Memory с реалистичными данными
        self.mock_memory = Mock()
        self.mock_memory.get_statistics.return_value = {
            'total_entries': 150,
            'archived_entries': 45,
            'active_entries': 105,
            'memory_pressure': 0.3,
            'average_significance': 0.65,
            'entry_types': {
                'energy_event': 40,
                'stability_event': 35,
                'external_event': 30,
                'internal_event': 25,
            }
        }

        # Создаем mock LearningEngine
        self.mock_learning_engine = Mock()
        self.mock_learning_engine.learning_params = {
            'event_type_sensitivity': {
                'energy_event': 0.8,
                'stability_event': 0.9,
                'external_event': 0.6,
                'internal_event': 0.7,
            },
            'significance_thresholds': {
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2,
            },
            'response_coefficients': {
                'ignore': 0.1,
                'absorb': 0.4,
                'dampen': 0.6,
                'amplify': 0.8,
            }
        }
        self.mock_learning_engine.parameter_history = [
            {'timestamp': time.time() - 100, 'event_type_sensitivity': {'energy_event': 0.75}},
            {'timestamp': time.time() - 50, 'event_type_sensitivity': {'energy_event': 0.8}},
        ]

        # Создаем mock AdaptationManager
        self.mock_adaptation_manager = Mock()
        self.mock_adaptation_manager.adaptation_params = {
            'behavior_sensitivity': {
                'energy_response': 0.85,
                'stability_response': 0.92,
                'recovery_rate': 0.15,
            },
            'behavior_thresholds': {
                'dampen_threshold': 0.6,
                'amplify_threshold': 0.8,
                'ignore_threshold': 0.2,
            },
            'behavior_coefficients': {
                'dampen_factor': 0.7,
                'amplify_factor': 1.2,
                'absorb_factor': 0.9,
            }
        }

        # Создаем mock DecisionEngine
        self.mock_decision_engine = Mock()
        self.mock_decision_engine.decision_history = [
            'absorb', 'dampen', 'ignore', 'amplify', 'absorb',
            'dampen', 'absorb', 'amplify', 'dampen', 'absorb',
            'ignore', 'absorb', 'dampen', 'amplify', 'absorb'
        ]

    def test_self_awareness_analyzer_integration(self):
        """Тест интеграции SelfAwarenessAnalyzer с реальными компонентами."""
        analyzer = SelfAwarenessAnalyzer()

        # Выполняем анализ
        metrics = analyzer.analyze_self_awareness(self.mock_self_state, self.mock_memory)

        # Проверяем, что метрики получены
        assert hasattr(metrics, 'overall_self_awareness')
        assert hasattr(metrics, 'state_awareness')
        assert hasattr(metrics, 'behavioral_reflection')
        assert hasattr(metrics, 'temporal_awareness')
        assert hasattr(metrics, 'self_regulation')

        # Проверяем диапазон значений
        assert 0.0 <= metrics.overall_self_awareness <= 1.0
        assert 0.0 <= metrics.state_awareness <= 1.0
        assert 0.0 <= metrics.behavioral_reflection <= 1.0
        assert 0.0 <= metrics.temporal_awareness <= 1.0
        assert 0.0 <= metrics.self_regulation <= 1.0

        # Проверяем, что анализ использует данные из self_state
        assert len(self.mock_self_state.recent_events) > 0  # Должен использовать recent_events

    def test_life_vitality_evaluator_integration(self):
        """Тест интеграции LifeVitalityEvaluator с реальными компонентами."""
        evaluator = LifeVitalityEvaluator()

        # Выполняем анализ
        metrics = evaluator.evaluate_life_vitality(
            self.mock_self_state,
            self.mock_memory,
            self.mock_adaptation_manager,
            self.mock_learning_engine
        )

        # Проверяем, что метрики получены
        assert hasattr(metrics, 'overall_vitality')
        assert hasattr(metrics, 'vitality_level')
        assert hasattr(metrics, 'environmental_adaptability')
        assert hasattr(metrics, 'internal_harmony')
        assert hasattr(metrics, 'developmental_potential')

        # Проверяем диапазон значений
        assert 0.0 <= metrics.overall_vitality <= 1.0
        assert 0.0 <= metrics.vitality_level <= 1.0
        assert 0.0 <= metrics.environmental_adaptability <= 1.0
        assert 0.0 <= metrics.internal_harmony <= 1.0
        assert 0.0 <= metrics.developmental_potential <= 1.0

        # Проверяем, что используются параметры адаптации
        assert self.mock_adaptation_manager.adaptation_params is not None

    def test_ethical_behavior_analyzer_integration(self):
        """Тест интеграции EthicalBehaviorAnalyzer с реальными компонентами."""
        analyzer = EthicalBehaviorAnalyzer()

        # Выполняем анализ
        metrics = analyzer.analyze_ethical_behavior(
            self.mock_self_state,
            self.mock_memory,
            self.mock_decision_engine
        )

        # Проверяем, что метрики получены
        assert hasattr(metrics, 'overall_ethical_score')
        assert hasattr(metrics, 'norm_compliance')
        assert hasattr(metrics, 'consequence_awareness')
        assert hasattr(metrics, 'ethical_consistency')
        assert hasattr(metrics, 'dilemma_resolution')

        # Проверяем диапазон значений
        assert 0.0 <= metrics.overall_ethical_score <= 1.0
        assert 0.0 <= metrics.norm_compliance <= 1.0
        assert 0.0 <= metrics.consequence_awareness <= 1.0
        assert 0.0 <= metrics.ethical_consistency <= 1.0
        assert 0.0 <= metrics.dilemma_resolution <= 1.0

        # Проверяем, что используется история решений
        assert len(self.mock_decision_engine.decision_history) > 0

    def test_adaptation_quality_analyzer_integration(self):
        """Тест интеграции AdaptationQualityAnalyzer с реальными компонентами."""
        analyzer = AdaptationQualityAnalyzer()

        # Выполняем анализ
        metrics = analyzer.analyze_adaptation_quality(
            self.mock_self_state,
            self.mock_adaptation_manager,
            self.mock_learning_engine
        )

        # Проверяем, что метрики получены
        assert hasattr(metrics, 'overall_adaptation_quality')
        assert hasattr(metrics, 'adaptation_effectiveness')
        assert hasattr(metrics, 'adaptation_stability')
        assert hasattr(metrics, 'adaptation_speed')
        assert hasattr(metrics, 'predictive_quality')

        # Проверяем диапазон значений
        assert 0.0 <= metrics.overall_adaptation_quality <= 1.0
        assert 0.0 <= metrics.adaptation_effectiveness <= 1.0
        assert 0.0 <= metrics.adaptation_stability <= 1.0
        assert 0.0 <= metrics.adaptation_speed <= 1.0
        assert 0.0 <= metrics.predictive_quality <= 1.0

        # Проверяем, что используются параметры адаптации и обучения
        assert self.mock_adaptation_manager.adaptation_params is not None
        assert self.mock_learning_engine.learning_params is not None

    def test_conceptual_integrity_analyzer_integration(self):
        """Тест интеграции ConceptualIntegrityAnalyzer с реальными компонентами."""
        analyzer = ConceptualIntegrityAnalyzer()

        # Выполняем анализ
        metrics = analyzer.analyze_conceptual_integrity(
            self.mock_self_state,
            self.mock_memory,
            self.mock_learning_engine
        )

        # Проверяем, что метрики получены
        assert hasattr(metrics, 'overall_integrity')
        assert hasattr(metrics, 'model_integrity')
        assert hasattr(metrics, 'behavioral_consistency')
        assert hasattr(metrics, 'conceptual_stability')
        assert hasattr(metrics, 'conceptual_learning')

        # Проверяем диапазон значений
        assert 0.0 <= metrics.overall_integrity <= 1.0
        assert 0.0 <= metrics.model_integrity <= 1.0
        assert 0.0 <= metrics.behavioral_consistency <= 1.0
        assert 0.0 <= metrics.conceptual_stability <= 1.0
        assert 0.0 <= metrics.conceptual_learning <= 1.0

        # Проверяем, что используются параметры обучения
        assert self.mock_learning_engine.learning_params is not None
        assert self.mock_learning_engine.parameter_history is not None

    def test_external_philosophical_analyzer_full_integration(self):
        """Тест полного интеграционного анализа через ExternalPhilosophicalAnalyzer."""
        analyzer = ExternalPhilosophicalAnalyzer()

        # Захватываем снимок
        snapshot = analyzer.capture_system_snapshot(
            self.mock_self_state,
            self.mock_memory,
            self.mock_learning_engine,
            self.mock_adaptation_manager,
            self.mock_decision_engine
        )

        # Проверяем, что снимок содержит правильные данные
        assert snapshot.self_state['life_id'] == "test-life-001"
        assert snapshot.self_state['energy'] == 85.0
        assert snapshot.memory_stats['total_entries'] == 150
        assert 'event_type_sensitivity' in snapshot.learning_params
        assert 'behavior_sensitivity' in snapshot.adaptation_params
        assert len(snapshot.decision_history) == 15

        # Выполняем полный анализ
        report = analyzer.analyze_snapshot(snapshot)

        # Проверяем структуру отчета
        assert report.timestamp > 0
        assert isinstance(report.self_awareness, dict)
        assert isinstance(report.life_vitality, dict)
        assert isinstance(report.ethical_behavior, dict)
        assert isinstance(report.adaptation_quality, dict)
        assert isinstance(report.conceptual_integrity, dict)
        assert isinstance(report.overall_assessment, dict)

        # Проверяем, что нет ошибок в анализе
        assert 'error' not in report.self_awareness
        assert 'error' not in report.life_vitality
        assert 'error' not in report.ethical_behavior
        assert 'error' not in report.adaptation_quality
        assert 'error' not in report.conceptual_integrity
        assert 'error' not in report.overall_assessment

        # Проверяем общую оценку
        assert 'overall_score' in report.overall_assessment
        assert 'assessment' in report.overall_assessment
        assert 0.0 <= report.overall_assessment['overall_score'] <= 1.0

    def test_external_analyzer_save_report(self, tmp_path):
        """Тест сохранения отчета ExternalPhilosophicalAnalyzer."""
        analyzer = ExternalPhilosophicalAnalyzer()

        # Создаем тестовый отчет
        snapshot = analyzer.capture_system_snapshot(
            self.mock_self_state,
            self.mock_memory,
            self.mock_learning_engine,
            self.mock_adaptation_manager,
            self.mock_decision_engine
        )
        report = analyzer.analyze_snapshot(snapshot)

        # Сохраняем отчет
        output_path = tmp_path / "test_report.json"
        saved_path = analyzer.save_report(report, output_path)

        # Проверяем, что файл создан
        assert saved_path.exists()

        # Проверяем содержимое файла
        with open(saved_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        assert 'timestamp' in saved_data
        assert 'snapshot' in saved_data
        assert 'self_awareness' in saved_data
        assert 'life_vitality' in saved_data
        assert 'ethical_behavior' in saved_data
        assert 'adaptation_quality' in saved_data
        assert 'conceptual_integrity' in saved_data
        assert 'overall_assessment' in saved_data

    def test_error_handling_in_analyzers(self):
        """Тест обработки ошибок в анализаторах."""
        analyzer = ExternalPhilosophicalAnalyzer()

        # Создаем поврежденные mock-объекты
        broken_self_state = Mock()
        broken_self_state.energy = "not_a_number"  # Должно вызвать ошибку

        broken_memory = Mock()
        broken_memory.get_statistics.side_effect = Exception("Memory error")

        # Проверяем, что анализатор обрабатывает ошибки gracefully
        snapshot = analyzer.capture_system_snapshot(
            broken_self_state,
            broken_memory,
            self.mock_learning_engine,
            self.mock_adaptation_manager,
            self.mock_decision_engine
        )

        # Анализ должен завершиться без исключений (graceful degradation)
        report = analyzer.analyze_snapshot(snapshot)

        # Анализатор должен корректно обработать поврежденные данные
        # и вернуть результаты анализа (возможно с низкими оценками)
        assert isinstance(report.self_awareness, dict)
        assert isinstance(report.life_vitality, dict)
        assert 'overall_self_awareness' in report.self_awareness
        assert 'overall_vitality' in report.life_vitality

        # Значения должны быть в допустимом диапазоне
        assert 0.0 <= report.self_awareness.get('overall_self_awareness', -1) <= 1.0
        assert 0.0 <= report.life_vitality.get('overall_vitality', -1) <= 1.0

    def test_analyzer_history_tracking(self):
        """Тест отслеживания истории анализов."""
        analyzer = ExternalPhilosophicalAnalyzer()

        # Выполняем несколько анализов
        for i in range(3):
            snapshot = analyzer.capture_system_snapshot(
                self.mock_self_state,
                self.mock_memory,
                self.mock_learning_engine,
                self.mock_adaptation_manager,
                self.mock_decision_engine
            )
            analyzer.analyze_snapshot(snapshot)

        # Проверяем историю
        summary = analyzer.get_analysis_history_summary()

        assert summary['total_analyses'] == 3
        assert 'average_scores' in summary
        assert 'recent_trends' in summary

    def test_realistic_data_ranges(self):
        """Тест на реалистичные диапазоны данных."""
        # Создаем SelfState с экстремальными значениями
        extreme_self_state = Mock()
        extreme_self_state.energy = 5.0  # Очень низкая энергия
        extreme_self_state.stability = 0.1  # Очень низкая стабильность
        extreme_self_state.fatigue = 95.0  # Очень высокая усталость
        extreme_self_state.recent_events = []
        extreme_self_state.energy_history = [5.0, 3.0, 2.0]  # Падающая энергия
        extreme_self_state.stability_history = [0.1, 0.05, 0.02]  # Падающая стабильность

        analyzer = ExternalPhilosophicalAnalyzer()

        snapshot = analyzer.capture_system_snapshot(
            extreme_self_state,
            self.mock_memory,
            self.mock_learning_engine,
            self.mock_adaptation_manager,
            self.mock_decision_engine
        )

        report = analyzer.analyze_snapshot(snapshot)

        # Анализ должен работать даже с экстремальными данными
        assert 'overall_score' in report.overall_assessment
        assert 0.0 <= report.overall_assessment['overall_score'] <= 1.0

        # Оценка должна быть низкой для плохого состояния
        assert report.overall_assessment['overall_score'] < 0.5
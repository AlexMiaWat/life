"""
Внешний инструмент философского анализа системы Life.

Этот модуль предоставляет внешний инструмент наблюдения за системой Life,
который анализирует ее поведение без вмешательства в runtime.

Философский анализ включает:
- Самоосознание: анализ наблюдаемых характеристик поведения
- Жизненность: оценка энергичности и адаптивности
- Этическое поведение: анализ решений и последствий
- Качество адаптации: эффективность адаптационных процессов
- Концептуальная целостность: согласованность внутренней модели

Использование:
    analyzer = ExternalPhilosophicalAnalyzer()
    snapshot = analyzer.capture_system_snapshot(self_state, memory, learning_engine, adaptation_manager, decision_engine)
    analysis = analyzer.analyze_snapshot(snapshot)
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from .self_awareness import SelfAwarenessAnalyzer
from .life_vitality import LifeVitalityEvaluator
from .ethical_behavior import EthicalBehaviorAnalyzer
from .adaptation_quality import AdaptationQualityAnalyzer
from .conceptual_integrity import ConceptualIntegrityAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class SystemSnapshot:
    """Снимок состояния системы для анализа."""
    timestamp: float = field(default_factory=time.time)
    self_state: Dict[str, Any] = field(default_factory=dict)
    memory_stats: Dict[str, Any] = field(default_factory=dict)
    learning_params: Dict[str, Any] = field(default_factory=dict)
    adaptation_params: Dict[str, Any] = field(default_factory=dict)
    decision_history: List[Any] = field(default_factory=list)
    analysis_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhilosophicalAnalysisReport:
    """Полный отчет философского анализа."""
    timestamp: float = field(default_factory=time.time)
    snapshot: SystemSnapshot = field(default_factory=SystemSnapshot)
    self_awareness: Dict[str, Any] = field(default_factory=dict)
    life_vitality: Dict[str, Any] = field(default_factory=dict)
    ethical_behavior: Dict[str, Any] = field(default_factory=dict)
    adaptation_quality: Dict[str, Any] = field(default_factory=dict)
    conceptual_integrity: Dict[str, Any] = field(default_factory=dict)
    overall_assessment: Dict[str, Any] = field(default_factory=dict)


class ExternalPhilosophicalAnalyzer:
    """
    Внешний инструмент философского анализа системы Life.

    Предоставляет интерфейс для анализа системы без вмешательства в ее работу.
    """

    def __init__(self):
        """Инициализация внешнего анализатора."""
        self.self_awareness_analyzer = SelfAwarenessAnalyzer()
        self.life_vitality_evaluator = LifeVitalityEvaluator()
        self.ethical_behavior_analyzer = EthicalBehaviorAnalyzer()
        self.adaptation_quality_analyzer = AdaptationQualityAnalyzer()
        self.conceptual_integrity_analyzer = ConceptualIntegrityAnalyzer()

        # История анализов для трендов
        self.analysis_history: List[PhilosophicalAnalysisReport] = []
        self.max_history_size = 100

    def capture_system_snapshot(
        self,
        self_state,
        memory,
        learning_engine,
        adaptation_manager,
        decision_engine
    ) -> SystemSnapshot:
        """
        Захватить снимок текущего состояния системы.

        Args:
            self_state: Текущее состояние системы
            memory: Память системы
            learning_engine: Движок обучения
            adaptation_manager: Менеджер адаптации
            decision_engine: Движок принятия решений

        Returns:
            SystemSnapshot: Снимок состояния системы
        """
        try:
            snapshot = SystemSnapshot()

            # Захват состояния системы
            snapshot.self_state = {
                'life_id': getattr(self_state, 'life_id', None),
                'age': getattr(self_state, 'age', 0.0),
                'ticks': getattr(self_state, 'ticks', 0),
                'energy': getattr(self_state, 'energy', 0.0),
                'integrity': getattr(self_state, 'integrity', 0.0),
                'stability': getattr(self_state, 'stability', 0.0),
                'fatigue': getattr(self_state, 'fatigue', 0.0),
                'subjective_time': getattr(self_state, 'subjective_time', 0.0),
                'recent_events_count': len(getattr(self_state, 'recent_events', [])),
                'energy_history_length': len(getattr(self_state, 'energy_history', [])),
                'stability_history_length': len(getattr(self_state, 'stability_history', [])),
            }

            # Захват статистики памяти
            try:
                snapshot.memory_stats = memory.get_statistics()
            except Exception as e:
                logger.warning(f"Failed to capture memory stats: {e}")
                snapshot.memory_stats = {'error': str(e)}

            # Захват параметров обучения
            try:
                snapshot.learning_params = getattr(learning_engine, 'learning_params', {}).copy()
            except Exception as e:
                logger.warning(f"Failed to capture learning params: {e}")
                snapshot.learning_params = {'error': str(e)}

            # Захват параметров адаптации
            try:
                snapshot.adaptation_params = getattr(adaptation_manager, 'adaptation_params', {}).copy()
            except Exception as e:
                logger.warning(f"Failed to capture adaptation params: {e}")
                snapshot.adaptation_params = {'error': str(e)}

            # Захват истории решений
            try:
                snapshot.decision_history = getattr(decision_engine, 'decision_history', []).copy()
            except Exception as e:
                logger.warning(f"Failed to capture decision history: {e}")
                snapshot.decision_history = []

            return snapshot

        except Exception as e:
            logger.error(f"Failed to capture system snapshot: {e}")
            return SystemSnapshot()

    def analyze_snapshot(self, snapshot: SystemSnapshot) -> PhilosophicalAnalysisReport:
        """
        Проанализировать снимок состояния системы.

        Args:
            snapshot: Снимок состояния системы

        Returns:
            PhilosophicalAnalysisReport: Полный отчет анализа
        """
        report = PhilosophicalAnalysisReport(snapshot=snapshot)

        try:
            # Создаем mock-объекты для совместимости с существующими анализаторами
            mock_self_state = self._create_mock_self_state(snapshot.self_state)
            mock_memory = self._create_mock_memory(snapshot.memory_stats)
            mock_learning_engine = self._create_mock_learning_engine(snapshot.learning_params)
            mock_adaptation_manager = self._create_mock_adaptation_manager(snapshot.adaptation_params)
            mock_decision_engine = self._create_mock_decision_engine(snapshot.decision_history)

            # Анализ самоосознания
            try:
                self_awareness_metrics = self.self_awareness_analyzer.analyze_self_awareness(
                    mock_self_state, mock_memory
                )
                report.self_awareness = {
                    'overall_self_awareness': self_awareness_metrics.overall_self_awareness,
                    'state_awareness': self_awareness_metrics.state_awareness,
                    'behavioral_reflection': self_awareness_metrics.behavioral_reflection,
                    'temporal_awareness': self_awareness_metrics.temporal_awareness,
                    'self_regulation': self_awareness_metrics.self_regulation,
                }
            except Exception as e:
                logger.error(f"Self-awareness analysis failed: {e}")
                report.self_awareness = {'error': str(e)}

            # Анализ жизненности
            try:
                life_vitality_metrics = self.life_vitality_evaluator.evaluate_life_vitality(
                    mock_self_state, mock_memory, mock_adaptation_manager, mock_learning_engine
                )
                report.life_vitality = {
                    'overall_vitality': life_vitality_metrics.overall_vitality,
                    'vitality_level': life_vitality_metrics.vitality_level,
                    'environmental_adaptability': life_vitality_metrics.environmental_adaptability,
                    'internal_harmony': life_vitality_metrics.internal_harmony,
                    'developmental_potential': life_vitality_metrics.developmental_potential,
                }
            except Exception as e:
                logger.error(f"Life vitality analysis failed: {e}")
                report.life_vitality = {'error': str(e)}

            # Анализ этического поведения
            try:
                ethical_behavior_metrics = self.ethical_behavior_analyzer.analyze_ethical_behavior(
                    mock_self_state, mock_memory, mock_decision_engine
                )
                report.ethical_behavior = {
                    'overall_ethical_score': ethical_behavior_metrics.overall_ethical_score,
                    'norm_compliance': ethical_behavior_metrics.norm_compliance,
                    'consequence_awareness': ethical_behavior_metrics.consequence_awareness,
                    'ethical_consistency': ethical_behavior_metrics.ethical_consistency,
                    'dilemma_resolution': ethical_behavior_metrics.dilemma_resolution,
                }
            except Exception as e:
                logger.error(f"Ethical behavior analysis failed: {e}")
                report.ethical_behavior = {'error': str(e)}

            # Анализ качества адаптации
            try:
                adaptation_quality_metrics = self.adaptation_quality_analyzer.analyze_adaptation_quality(
                    mock_self_state, mock_adaptation_manager, mock_learning_engine
                )
                report.adaptation_quality = {
                    'overall_adaptation_quality': adaptation_quality_metrics.overall_adaptation_quality,
                    'adaptation_effectiveness': adaptation_quality_metrics.adaptation_effectiveness,
                    'adaptation_stability': adaptation_quality_metrics.adaptation_stability,
                    'adaptation_speed': adaptation_quality_metrics.adaptation_speed,
                    'predictive_quality': adaptation_quality_metrics.predictive_quality,
                }
            except Exception as e:
                logger.error(f"Adaptation quality analysis failed: {e}")
                report.adaptation_quality = {'error': str(e)}

            # Анализ концептуальной целостности
            try:
                conceptual_integrity_metrics = self.conceptual_integrity_analyzer.analyze_conceptual_integrity(
                    mock_self_state, mock_memory, mock_learning_engine
                )
                report.conceptual_integrity = {
                    'overall_integrity': conceptual_integrity_metrics.overall_integrity,
                    'model_integrity': conceptual_integrity_metrics.model_integrity,
                    'behavioral_consistency': conceptual_integrity_metrics.behavioral_consistency,
                    'conceptual_stability': conceptual_integrity_metrics.conceptual_stability,
                    'conceptual_learning': conceptual_integrity_metrics.conceptual_learning,
                }
            except Exception as e:
                logger.error(f"Conceptual integrity analysis failed: {e}")
                report.conceptual_integrity = {'error': str(e)}

            # Общая оценка
            report.overall_assessment = self._calculate_overall_assessment(report)

        except Exception as e:
            logger.error(f"Philosophical analysis failed: {e}")
            report.overall_assessment = {'error': str(e)}

        # Добавляем в историю
        self.analysis_history.append(report)
        if len(self.analysis_history) > self.max_history_size:
            self.analysis_history = self.analysis_history[-self.max_history_size:]

        return report

    def _create_mock_self_state(self, self_state_data: Dict[str, Any]):
        """Создать mock-объект SelfState для совместимости."""
        class MockSelfState:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)

        return MockSelfState(self_state_data)

    def _create_mock_memory(self, memory_stats: Dict[str, Any]):
        """Создать mock-объект Memory для совместимости."""
        class MockMemory:
            def __init__(self, stats):
                self._stats = stats

            def get_statistics(self):
                return self._stats

        return MockMemory(memory_stats)

    def _create_mock_learning_engine(self, learning_params: Dict[str, Any]):
        """Создать mock-объект LearningEngine для совместимости."""
        class MockLearningEngine:
            def __init__(self, params):
                self.learning_params = params
                self.parameter_history = []  # Mock history

        return MockLearningEngine(learning_params)

    def _create_mock_adaptation_manager(self, adaptation_params: Dict[str, Any]):
        """Создать mock-объект AdaptationManager для совместимости."""
        class MockAdaptationManager:
            def __init__(self, params):
                self.adaptation_params = params

        return MockAdaptationManager(adaptation_params)

    def _create_mock_decision_engine(self, decision_history: List[Any]):
        """Создать mock-объект DecisionEngine для совместимости."""
        class MockDecisionEngine:
            def __init__(self, history):
                self.decision_history = history

        return MockDecisionEngine(decision_history)

    def _calculate_overall_assessment(self, report: PhilosophicalAnalysisReport) -> Dict[str, Any]:
        """Вычислить общую оценку состояния системы."""
        assessment = {}

        try:
            # Собираем все метрики
            metrics = []
            weights = {
                'self_awareness': 0.20,
                'life_vitality': 0.25,
                'ethical_behavior': 0.20,
                'adaptation_quality': 0.20,
                'conceptual_integrity': 0.15
            }

            for category, weight in weights.items():
                category_data = getattr(report, category)
                if isinstance(category_data, dict) and 'error' not in category_data:
                    # Ищем overall метрику в категории
                    overall_key = f"overall_{category.replace('_', '_')}"
                    if overall_key in category_data:
                        metrics.append((category_data[overall_key], weight))
                    elif 'overall_score' in category_data:
                        metrics.append((category_data['overall_score'], weight))
                    elif 'overall_vitality' in category_data:
                        metrics.append((category_data['overall_vitality'], weight))
                    elif 'overall_integrity' in category_data:
                        metrics.append((category_data['overall_integrity'], weight))
                    elif 'overall_adaptation_quality' in category_data:
                        metrics.append((category_data['overall_adaptation_quality'], weight))
                    elif 'overall_self_awareness' in category_data:
                        metrics.append((category_data['overall_self_awareness'], weight))
                    elif 'overall_ethical_score' in category_data:
                        metrics.append((category_data['overall_ethical_score'], weight))

            if metrics:
                # Вычисляем взвешенную сумму
                total_score = sum(score * weight for score, weight in metrics)
                total_weight = sum(weight for _, weight in metrics)

                assessment['overall_score'] = total_score / total_weight if total_weight > 0 else 0.0
                assessment['metrics_count'] = len(metrics)
                assessment['assessment'] = self._interpret_score(assessment['overall_score'])
            else:
                assessment['overall_score'] = 0.0
                assessment['metrics_count'] = 0
                assessment['assessment'] = 'unable_to_assess'

        except Exception as e:
            logger.error(f"Failed to calculate overall assessment: {e}")
            assessment['error'] = str(e)

        return assessment

    def _interpret_score(self, score: float) -> str:
        """Интерпретировать числовую оценку."""
        if score >= 0.8:
            return 'excellent'
        elif score >= 0.6:
            return 'good'
        elif score >= 0.4:
            return 'adequate'
        elif score >= 0.2:
            return 'concerning'
        else:
            return 'critical'

    def save_report(self, report: PhilosophicalAnalysisReport, output_path: Optional[Path] = None) -> Path:
        """
        Сохранить отчет в файл.

        Args:
            report: Отчет для сохранения
            output_path: Путь для сохранения (опционально)

        Returns:
            Path: Путь к сохраненному файлу
        """
        if output_path is None:
            output_dir = Path('philosophical_reports')
            output_dir.mkdir(exist_ok=True)
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f'philosophical_analysis_{timestamp}.json'

        try:
            # Конвертируем в словарь для JSON
            report_dict = {
                'timestamp': report.timestamp,
                'snapshot': {
                    'timestamp': report.snapshot.timestamp,
                    'self_state': report.snapshot.self_state,
                    'memory_stats': report.snapshot.memory_stats,
                    'learning_params': report.snapshot.learning_params,
                    'adaptation_params': report.snapshot.adaptation_params,
                    'decision_history_length': len(report.snapshot.decision_history),
                },
                'self_awareness': report.self_awareness,
                'life_vitality': report.life_vitality,
                'ethical_behavior': report.ethical_behavior,
                'adaptation_quality': report.adaptation_quality,
                'conceptual_integrity': report.conceptual_integrity,
                'overall_assessment': report.overall_assessment,
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Philosophical analysis report saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise

    def get_analysis_history_summary(self) -> Dict[str, Any]:
        """Получить сводку по истории анализов."""
        if not self.analysis_history:
            return {'status': 'no_history'}

        try:
            recent_reports = self.analysis_history[-10:]  # Последние 10 отчетов

            summary = {
                'total_analyses': len(self.analysis_history),
                'recent_trends': {},
                'average_scores': {},
            }

            # Анализируем тренды
            categories = ['self_awareness', 'life_vitality', 'ethical_behavior', 'adaptation_quality', 'conceptual_integrity']

            for category in categories:
                scores = []
                for report in recent_reports:
                    category_data = getattr(report, category)
                    if isinstance(category_data, dict) and 'error' not in category_data:
                        # Ищем overall метрику
                        for key, value in category_data.items():
                            if key.startswith('overall_') and isinstance(value, (int, float)):
                                scores.append(value)
                                break

                if scores:
                    summary['average_scores'][category] = sum(scores) / len(scores)
                    if len(scores) > 1:
                        trend = 'stable'
                        if scores[-1] > scores[0] + 0.1:
                            trend = 'improving'
                        elif scores[-1] < scores[0] - 0.1:
                            trend = 'declining'
                        summary['recent_trends'][category] = trend

            return summary

        except Exception as e:
            logger.error(f"Failed to generate history summary: {e}")
            return {'error': str(e)}
"""
Метрики наблюдения за поведением системы Life.

Модуль определяет структуры данных и вычисления для метрик наблюдения
за поведением системы Life с философской точки зрения.

ВАЖНО: Это метрики ВНЕШНЕГО НАБЛЮДЕНИЯ, а не внутреннего состояния системы.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SelfAwarenessMetrics:
    """Метрики наблюдаемых характеристик поведения."""

    # Стабильность поддержания состояния (0.0 - 1.0)
    state_awareness: float = 0.0

    # Регулярность поведенческих паттернов (0.0 - 1.0)
    behavioral_reflection: float = 0.0

    # Осознание временного контекста (0.0 - 1.0)
    temporal_awareness: float = 0.0

    # Способность к саморегуляции (0.0 - 1.0)
    self_regulation: float = 0.0

    # Общий уровень наблюдаемых характеристик
    overall_self_awareness: float = 0.0

    # История метрик для анализа трендов
    history: List[Dict] = field(default_factory=list)


@dataclass
class AdaptationQualityMetrics:
    """Метрики качества адаптации."""

    # Эффективность адаптации к изменениям (0.0 - 1.0)
    adaptation_effectiveness: float = 0.0

    # Стабильность адаптационных изменений (0.0 - 1.0)
    adaptation_stability: float = 0.0

    # Скорость адаптации (нормализованная)
    adaptation_speed: float = 0.0

    # Качество предсказания будущих состояний (0.0 - 1.0)
    predictive_quality: float = 0.0

    # Общее качество адаптации
    overall_adaptation_quality: float = 0.0

    # История изменений параметров адаптации
    parameter_history: List[Dict] = field(default_factory=list)


@dataclass
class EthicalBehaviorMetrics:
    """Метрики этического поведения."""

    # Степень соблюдения внутренних норм (0.0 - 1.0)
    norm_compliance: float = 0.0

    # Способность к эмпатии и пониманию последствий (0.0 - 1.0)
    consequence_awareness: float = 0.0

    # Этическая последовательность поведения (0.0 - 1.0)
    ethical_consistency: float = 0.0

    # Способность к разрешению этических дилемм (0.0 - 1.0)
    dilemma_resolution: float = 0.0

    # Общий уровень этического поведения
    overall_ethical_score: float = 0.0

    # История этических решений
    ethical_decisions_history: List[Dict] = field(default_factory=list)


@dataclass
class ConceptualIntegrityMetrics:
    """Метрики концептуальной целостности."""

    # Целостность внутренней модели мира (0.0 - 1.0)
    model_integrity: float = 0.0

    # Согласованность поведения с концепцией (0.0 - 1.0)
    behavioral_consistency: float = 0.0

    # Стабильность концептуальных представлений (0.0 - 1.0)
    conceptual_stability: float = 0.0

    # Способность к концептуальному обучению (0.0 - 1.0)
    conceptual_learning: float = 0.0

    # Общая концептуальная целостность
    overall_integrity: float = 0.0

    # История концептуальных изменений
    conceptual_changes_history: List[Dict] = field(default_factory=list)


@dataclass
class LifeVitalityMetrics:
    """Метрики жизненности поведения."""

    # Энергичность и активность (0.0 - 1.0)
    vitality_level: float = 0.0

    # Адаптивность к среде (0.0 - 1.0)
    environmental_adaptability: float = 0.0

    # Внутренняя гармония и баланс (0.0 - 1.0)
    internal_harmony: float = 0.0

    # Потенциал развития и роста (0.0 - 1.0)
    developmental_potential: float = 0.0

    # Общий уровень жизненности
    overall_vitality: float = 0.0

    # Тренды жизненных показателей
    vitality_trends: List[Dict] = field(default_factory=list)


@dataclass
class PhilosophicalMetrics:
    """Обобщенные философские метрики системы Life."""

    # Метка времени анализа
    timestamp: float = field(default_factory=time.time)

    # Метрики самоосознания
    self_awareness: SelfAwarenessMetrics = field(default_factory=SelfAwarenessMetrics)

    # Метрики качества адаптации
    adaptation_quality: AdaptationQualityMetrics = field(default_factory=AdaptationQualityMetrics)

    # Метрики этического поведения
    ethical_behavior: EthicalBehaviorMetrics = field(default_factory=EthicalBehaviorMetrics)

    # Метрики концептуальной целостности
    conceptual_integrity: ConceptualIntegrityMetrics = field(default_factory=ConceptualIntegrityMetrics)

    # Метрики жизненности
    life_vitality: LifeVitalityMetrics = field(default_factory=LifeVitalityMetrics)

    # Обобщенный философский индекс (0.0 - 1.0)
    philosophical_index: float = 0.0

    # История всех метрик
    metrics_history: List[Dict] = field(default_factory=list)

    def calculate_overall_index(self) -> float:
        """
        Вычислить обобщенный философский индекс на основе всех метрик.

        Returns:
            float: Обобщенный индекс от 0.0 до 1.0
        """
        weights = {
            'self_awareness': 0.25,
            'adaptation_quality': 0.20,
            'ethical_behavior': 0.20,
            'conceptual_integrity': 0.20,
            'life_vitality': 0.15
        }

        self.philosophical_index = (
            self.self_awareness.overall_self_awareness * weights['self_awareness'] +
            self.adaptation_quality.overall_adaptation_quality * weights['adaptation_quality'] +
            self.ethical_behavior.overall_ethical_score * weights['ethical_behavior'] +
            self.conceptual_integrity.overall_integrity * weights['conceptual_integrity'] +
            self.life_vitality.overall_vitality * weights['life_vitality']
        )

        return self.philosophical_index

    def to_dict(self) -> Dict:
        """Преобразовать метрики в словарь для сериализации."""
        return {
            'timestamp': self.timestamp,
            'self_awareness': {
                'state_awareness': self.self_awareness.state_awareness,
                'behavioral_reflection': self.self_awareness.behavioral_reflection,
                'temporal_awareness': self.self_awareness.temporal_awareness,
                'self_regulation': self.self_awareness.self_regulation,
                'overall_self_awareness': self.self_awareness.overall_self_awareness
            },
            'adaptation_quality': {
                'adaptation_effectiveness': self.adaptation_quality.adaptation_effectiveness,
                'adaptation_stability': self.adaptation_quality.adaptation_stability,
                'adaptation_speed': self.adaptation_quality.adaptation_speed,
                'predictive_quality': self.adaptation_quality.predictive_quality,
                'overall_adaptation_quality': self.adaptation_quality.overall_adaptation_quality
            },
            'ethical_behavior': {
                'norm_compliance': self.ethical_behavior.norm_compliance,
                'consequence_awareness': self.ethical_behavior.consequence_awareness,
                'ethical_consistency': self.ethical_behavior.ethical_consistency,
                'dilemma_resolution': self.ethical_behavior.dilemma_resolution,
                'overall_ethical_score': self.ethical_behavior.overall_ethical_score
            },
            'conceptual_integrity': {
                'model_integrity': self.conceptual_integrity.model_integrity,
                'behavioral_consistency': self.conceptual_integrity.behavioral_consistency,
                'conceptual_stability': self.conceptual_integrity.conceptual_stability,
                'conceptual_learning': self.conceptual_integrity.conceptual_learning,
                'overall_integrity': self.conceptual_integrity.overall_integrity
            },
            'life_vitality': {
                'vitality_level': self.life_vitality.vitality_level,
                'environmental_adaptability': self.life_vitality.environmental_adaptability,
                'internal_harmony': self.life_vitality.internal_harmony,
                'developmental_potential': self.life_vitality.developmental_potential,
                'overall_vitality': self.life_vitality.overall_vitality
            },
            'philosophical_index': self.philosophical_index
        }
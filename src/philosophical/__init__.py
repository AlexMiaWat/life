"""
Философский анализатор поведения системы Life.

Модуль предоставляет инструменты для анализа поведения системы Life
с философской точки зрения, включая метрики самоосознания,
адаптации, этического поведения и концептуальной целостности.
"""

from .philosophical_analyzer import PhilosophicalAnalyzer
from .metrics import PhilosophicalMetrics
from .self_awareness import SelfAwarenessAnalyzer
from .adaptation_quality import AdaptationQualityAnalyzer
from .ethical_behavior import EthicalBehaviorAnalyzer
from .conceptual_integrity import ConceptualIntegrityAnalyzer
from .life_vitality import LifeVitalityEvaluator

__all__ = [
    'PhilosophicalAnalyzer',
    'PhilosophicalMetrics',
    'SelfAwarenessAnalyzer',
    'AdaptationQualityAnalyzer',
    'EthicalBehaviorAnalyzer',
    'ConceptualIntegrityAnalyzer',
    'LifeVitalityEvaluator'
]
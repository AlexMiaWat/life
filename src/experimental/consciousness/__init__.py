"""
Система сознания - Consciousness System.

Экспериментальная реализация модели сознания с уровнями осознанности и метриками.
Включает как последовательную, так и многопоточную реализацию.
"""

from .engine import ConsciousnessEngine
from .metrics import ConsciousnessMetrics
from .states import ConsciousnessStates
from .parallel_engine import (
    ParallelConsciousnessEngine,
    NeuralActivityMonitor,
    SelfReflectionProcessor,
    MetaCognitionAnalyzer,
    StateTransitionManager,
    ConsciousnessMetricsAggregator,
)

__all__ = [
    # Оригинальные компоненты
    "ConsciousnessEngine",
    "ConsciousnessMetrics",
    "ConsciousnessStates",
    # Многопоточная реализация
    "ParallelConsciousnessEngine",
    "NeuralActivityMonitor",
    "SelfReflectionProcessor",
    "MetaCognitionAnalyzer",
    "StateTransitionManager",
    "ConsciousnessMetricsAggregator",
]

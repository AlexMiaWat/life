"""
Система сознания - Consciousness System.

Экспериментальная реализация модели сознания с уровнями осознанности и метриками.
"""

from .engine import ConsciousnessEngine
from .metrics import ConsciousnessMetrics
from .states import ConsciousnessStates

__all__ = [
    'ConsciousnessEngine',
    'ConsciousnessMetrics',
    'ConsciousnessStates'
]
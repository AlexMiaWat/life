"""
Архитектурные контракты системы Life.

Определяет интерфейсы, диапазоны значений, гарантии и правила взаимодействия
между компонентами системы.
"""

from .base_contracts import BaseContract, ContractViolation
from .component_contracts import (
    EventGeneratorContract,
    IntensityCalculatorContract,
    PatternAnalyzerContract,
    SmoothingEngineContract,
    SelfStateContract,
    RuntimeLoopContract
)
from .validation import ContractValidator

__all__ = [
    'BaseContract',
    'ContractViolation',
    'EventGeneratorContract',
    'IntensityCalculatorContract',
    'PatternAnalyzerContract',
    'SmoothingEngineContract',
    'SelfStateContract',
    'RuntimeLoopContract',
    'ContractValidator'
]
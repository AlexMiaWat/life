"""
Экспериментальные возможности системы Life.

Этот модуль содержит экспериментальные компоненты, которые расширяют
внутренний мир системы Life без нарушения основной логики.
"""

from src.experimental.adaptive_processing_manager import (
    AdaptiveProcessingManager,
    AdaptiveProcessingConfig,
    ProcessingMode,
    AdaptiveState,
)
from src.experimental.memory_hierarchy import MemoryHierarchyManager, SensoryBuffer

__all__ = [
    "AdaptiveProcessingManager",
    "AdaptiveProcessingConfig",
    "ProcessingMode",
    "AdaptiveState",
    "MemoryHierarchyManager",
    "SensoryBuffer",
]

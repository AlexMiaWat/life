"""
Экспериментальные возможности системы Life.

Этот модуль содержит экспериментальные компоненты, которые расширяют
внутренний мир системы Life без нарушения основной логики.
"""

from src.experimental.clarity_moments import ClarityMoments
from src.experimental.memory_hierarchy import MemoryHierarchyManager, SensoryBuffer

__all__ = ["ClarityMoments", "MemoryHierarchyManager", "SensoryBuffer"]

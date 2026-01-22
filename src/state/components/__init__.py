"""
Компоненты состояния системы Life.

Модуль содержит специализированные компоненты состояния,
разбитые по аспектам для лучшей поддерживаемости и тестируемости.
"""

from .cognitive_state import CognitiveState
from .event_state import EventState
from .identity_state import IdentityState
from .memory_state import MemoryState
from .physical_state import PhysicalState
from .time_state import TimeState

__all__ = [
    "IdentityState",
    "PhysicalState",
    "TimeState",
    "MemoryState",
    "CognitiveState",
    "EventState",
]
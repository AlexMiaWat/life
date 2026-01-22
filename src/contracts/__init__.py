"""
Архитектурные контракты системы Life.

Определяют интерфейсы взаимодействия между компонентами,
обеспечивая loose coupling и testability.
"""

from .event_generator import (
    EventDependencyManagerProtocol,
    EventGeneratorProtocol,
    IntensityAdapterProtocol,
    PatternAnalyzerProtocol,
)
from .memory_system import (
    MemoryHierarchyManagerProtocol,
    ProceduralMemoryStoreProtocol,
    SemanticMemoryStoreProtocol,
    SensoryBufferProtocol,
)
from .state_management import (
    CircadianRhythmManagerProtocol,
    SelfStateProtocol,
    StateValidationProtocol,
    SubjectiveTimeManagerProtocol,
)

__all__ = [
    # Event generation contracts
    "EventGeneratorProtocol",
    "IntensityAdapterProtocol",
    "PatternAnalyzerProtocol",
    "EventDependencyManagerProtocol",

    # Memory system contracts
    "SensoryBufferProtocol",
    "MemoryHierarchyManagerProtocol",
    "SemanticMemoryStoreProtocol",
    "ProceduralMemoryStoreProtocol",

    # State management contracts
    "SelfStateProtocol",
    "StateValidationProtocol",
    "SubjectiveTimeManagerProtocol",
    "CircadianRhythmManagerProtocol",
]
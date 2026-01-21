from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Event:
    """
    Минимальная структура события из Environment
    """

    type: str  # Тип события: 'noise', 'decay', 'recovery', 'shock', 'idle', 'memory_echo', 'social_presence', 'social_conflict', 'social_harmony', 'cognitive_doubt', 'cognitive_clarity', 'cognitive_confusion', 'existential_void', 'existential_purpose', 'existential_finitude', 'connection', 'isolation', 'insight', 'confusion', 'curiosity', 'meaning_found', 'void', 'acceptance', 'clarity_moment'
    intensity: float  # Интенсивность: [-1.0, 1.0]
    timestamp: float  # time.time()
    metadata: Optional[Dict[str, Any]] = None  # Опционально: дополнительные данные

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

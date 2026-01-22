from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Event:
    """
    Минимальная структура события из Environment
    """

    type: str  # Тип события: 'noise', 'decay', 'recovery', 'shock', 'idle', 'memory_echo', 'social_presence', 'social_conflict', 'social_harmony', 'cognitive_doubt', 'cognitive_clarity', 'cognitive_confusion', 'existential_void', 'existential_purpose', 'existential_finitude', 'connection', 'isolation', 'insight', 'confusion', 'curiosity', 'meaning_found', 'void', 'acceptance', 'clarity_moment', 'joy', 'sadness', 'fear', 'calm', 'discomfort', 'comfort', 'fatigue', 'anticipation', 'boredom', 'inspiration', 'creative_dissonance'
    intensity: float  # Интенсивность: [-1.0, 1.0]
    timestamp: float  # time.time()
    metadata: Optional[Dict[str, Any]] = None  # Опционально: дополнительные данные
    event_type: Optional[str] = None  # Алиас для type для обратной совместимости
    source: Optional[str] = None  # Источник события для обратной совместимости

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Обеспечиваем обратную совместимость между type и event_type
        if self.event_type is None:
            self.event_type = self.type
        elif self.type != self.event_type:
            # Если передан event_type, синхронизируем type
            self.type = self.event_type

    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """
        Алиас для metadata для обратной совместимости.
        """
        return self.metadata

    @data.setter
    def data(self, value: Optional[Dict[str, Any]]) -> None:
        """
        Сеттер для data (устанавливает metadata).
        """
        self.metadata = value if value is not None else {}

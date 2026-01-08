from typing import Any, Dict, Optional
from dataclasses import dataclass
import time

@dataclass
class Event:
    """
    Минимальная структура события из Environment
    """
    type: str           # Тип события: 'noise', 'decay', 'recovery', 'shock', 'idle'
    intensity: float    # Интенсивность: [-1.0, 1.0]
    timestamp: float    # time.time()
    metadata: Optional[Dict[str, Any]] = None  # Опционально: дополнительные данные

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
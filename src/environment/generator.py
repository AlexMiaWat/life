import random
import time
from typing import Any

from .event import Event


class EventGenerator:
    def generate(self) -> Event:
        """
        Генерирует событие согласно спецификации этапа 07.

        Диапазоны интенсивности:
        - noise: [-0.3, 0.3]
        - decay: [-0.5, 0.0]
        - recovery: [0.0, 0.5]
        - shock: [-1.0, 1.0]
        - idle: 0.0
        """
        types = ["noise", "decay", "recovery", "shock", "idle", "memory_echo"]
        weights = [
            0.4,
            0.3,
            0.2,
            0.05,
            0.05,
            0.0,
        ]  # memory_echo генерируется только внутренне
        event_type = random.choices(types, weights=weights)[0]

        # Генерируем интенсивность согласно спецификации
        if event_type == "noise":
            intensity = random.uniform(-0.3, 0.3)
        elif event_type == "decay":
            intensity = random.uniform(-0.5, 0.0)
        elif event_type == "recovery":
            intensity = random.uniform(0.0, 0.5)
        elif event_type == "shock":
            intensity = random.uniform(-1.0, 1.0)
        elif event_type == "memory_echo":
            intensity = random.uniform(
                -0.2, 0.2
            )  # Мягкое влияние для внутренних воспоминаний
        else:  # idle
            intensity = 0.0

        timestamp = time.time()
        metadata: dict[str, Any] = {}
        return Event(
            type=event_type, intensity=intensity, timestamp=timestamp, metadata=metadata
        )

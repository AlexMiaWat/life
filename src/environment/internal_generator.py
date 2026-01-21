import random
import time
from typing import Any, Dict, Optional

from .event import Event


class InternalEventGenerator:
    """
    Генератор внутренних событий для системы Life.

    Отвечает за генерацию спонтанных внутренних событий,
    таких как memory echoes (всплывания воспоминаний).
    """

    def __init__(self, memory_echo_probability: float = 0.02):
        """
        Args:
            memory_echo_probability: Вероятность генерации memory_echo события на тик (0.02 = 2%)
        """
        self.memory_echo_probability = memory_echo_probability

    def generate_memory_echo(
        self, memory_stats: Optional[Dict[str, Any]] = None
    ) -> Optional[Event]:
        """
        Генерирует событие memory_echo на основе состояния памяти.

        Args:
            memory_stats: Статистика памяти для выбора воспоминания

        Returns:
            Event или None если событие не сгенерировано
        """
        # Проверяем вероятность генерации
        if random.random() > self.memory_echo_probability:
            return None

        # Генерируем мягкую интенсивность для внутренних воспоминаний
        intensity = random.uniform(-0.2, 0.2)

        # Создаем metadata с информацией о всплывшем воспоминании
        metadata = {
            "internal": True,
            "source": "spontaneous_recall",
            "echo_type": "random_memory",
        }

        # Если есть статистика памяти, добавляем дополнительную информацию
        if memory_stats:
            metadata.update(
                {
                    "memory_active_count": memory_stats.get("active_entries", 0),
                    "memory_archive_count": memory_stats.get("archive_entries", 0),
                    "memory_event_types": memory_stats.get("event_types", []),
                }
            )

        return Event(
            type="memory_echo",
            intensity=intensity,
            timestamp=time.time(),
            metadata=metadata,
        )

    def should_generate_echo(
        self, ticks_since_last_echo: int, memory_pressure: float
    ) -> bool:
        """
        Определяет, следует ли генерировать memory echo на основе контекста.

        Args:
            ticks_since_last_echo: Тиков с момента последнего echo
            memory_pressure: Давление памяти (0.0 - 1.0, где 1.0 = память полна)

        Returns:
            True если следует генерировать echo
        """
        # Базовая вероятность
        base_prob = self.memory_echo_probability

        # Увеличиваем вероятность если давно не было echo
        if ticks_since_last_echo > 50:  # Каждые ~50 тиков минимум
            base_prob *= 2.0

        # Увеличиваем вероятность при высоком давлении памяти
        if memory_pressure > 0.8:  # Память почти полна
            base_prob *= 1.5

        return random.random() < base_prob

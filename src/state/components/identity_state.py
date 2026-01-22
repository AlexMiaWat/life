import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any
from ...contracts.serialization_contract import Serializable


@dataclass
class IdentityState(Serializable):
    """
    Компонент состояния, отвечающий за идентичность и жизненный цикл системы Life.

    Включает уникальный идентификатор, временные метки и счетчики жизненного цикла.
    """

    # Уникальный идентификатор системы Life
    life_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Временные метки жизненного цикла
    birth_timestamp: float = field(default_factory=time.time)
    age: float = 0.0

    # Счетчик тиков (итераций жизненного цикла)
    ticks: int = 0

    # Флаг активности системы
    active: bool = True

    def increment_age(self, delta_time: float) -> None:
        """Увеличивает возраст системы на указанное время."""
        self.age += delta_time

    def increment_ticks(self) -> None:
        """Увеличивает счетчик тиков."""
        self.ticks += 1

    def get_lifespan(self) -> float:
        """Возвращает текущую продолжительность жизни в секундах."""
        return time.time() - self.birth_timestamp

    def is_active(self) -> bool:
        """Проверяет, активна ли система."""
        return self.active

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализует состояние идентичности.

        Returns:
            Dict[str, Any]: Словарь с состоянием компонента
        """
        return {
            "life_id": self.life_id,
            "birth_timestamp": self.birth_timestamp,
            "age": self.age,
            "ticks": self.ticks,
            "active": self.active,
            "lifespan": self.get_lifespan()
        }
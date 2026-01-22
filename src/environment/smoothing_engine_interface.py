from abc import ABC, abstractmethod
from typing import Dict, Optional


class SmoothingEngineInterface(ABC):
    """
    Интерфейс для движка сглаживания значений.

    Определяет контракт для компонентов, отвечающих за
    сглаживание модификаторов и интенсивностей событий.
    """

    @abstractmethod
    def smooth_modifier(self, event_type: str, current_modifier: float) -> float:
        """
        Применяет сглаживание к модификатору интенсивности.

        Args:
            event_type: Тип события
            current_modifier: Текущий модификатор

        Returns:
            Сглаженный модификатор
        """
        pass

    @abstractmethod
    def smooth_intensity(self, event_type: str, current_intensity: float) -> float:
        """
        Применяет сглаживание к интенсивности события.

        Args:
            event_type: Тип события
            current_intensity: Текущая интенсивность

        Returns:
            Сглаженная интенсивность
        """
        pass

    @abstractmethod
    def get_smoothing_stats(self) -> Dict[str, Dict[str, any]]:
        """
        Возвращает статистику сглаживания.

        Returns:
            Статистика по типам событий
        """
        pass

    @abstractmethod
    def reset_history(self, event_type: Optional[str] = None) -> None:
        """
        Сбрасывает историю сглаживания.

        Args:
            event_type: Тип события для сброса (None - все типы)
        """
        pass
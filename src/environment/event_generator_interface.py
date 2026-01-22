"""
Интерфейс для генераторов событий.

Определяет контракт для компонентов, отвечающих за генерацию событий
системы Life с адаптацией интенсивностей.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from .event import Event
from ..state.self_state import SelfState


class EventGeneratorInterface(ABC):
    """
    Абстрактный интерфейс для генераторов событий.

    Определяет контракт для компонентов, отвечающих за генерацию
    событий системы Life с учетом зависимостей и адаптации интенсивностей.
    """

    @abstractmethod
    def generate(self, context_state: Optional[SelfState] = None) -> Event:
        """
        Генерирует событие согласно спецификации системы.

        Args:
            context_state: Текущее состояние системы Life (опционально)

        Returns:
            Сгенерированное событие с адаптированной интенсивностью

        Raises:
            RuntimeError: Если генерация невозможна из-за внутренних ошибок
        """
        pass

    @abstractmethod
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику генерации событий для мониторинга.

        Returns:
            Статистика генерации:
            - Количество сгенерированных событий по типам
            - Средние интенсивности
            - Статистика зависимостей
            - Время генерации
        """
        pass

    @abstractmethod
    def reset_stats(self) -> None:
        """
        Сбрасывает внутреннюю статистику генератора.

        Используется для тестирования или периодической очистки метрик.
        """
        pass

    @property
    @abstractmethod
    def supported_event_types(self) -> list[str]:
        """
        Список поддерживаемых типов событий.

        Returns:
            Список строк с названиями типов событий
        """
        pass

    @abstractmethod
    def get_event_weights(self) -> Dict[str, float]:
        """
        Возвращает текущие веса вероятностей для типов событий.

        Returns:
            Словарь {тип_события: вес} с нормализованными весами
        """
        pass

    @abstractmethod
    def is_event_type_supported(self, event_type: str) -> bool:
        """
        Проверяет, поддерживается ли данный тип события.

        Args:
            event_type: Тип события для проверки

        Returns:
            True если тип поддерживается, False иначе
        """
        pass
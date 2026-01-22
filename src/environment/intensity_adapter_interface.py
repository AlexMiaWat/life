"""
Интерфейс для адаптеров интенсивности событий.

Определяет контракт для компонентов, отвечающих за адаптацию интенсивности
событий на основе состояния системы Life.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol
from ..state.self_state import SelfState


class IntensityModifier:
    """
    Структура для передачи модификаторов интенсивности между компонентами.

    Гарантирует типобезопасность и явный контракт для модификаторов.
    """

    def __init__(self,
                 state_modifier: float = 1.0,
                 pattern_modifier: float = 1.0,
                 dependency_modifier: float = 1.0,
                 category_modifier: float = 1.0,
                 subjective_time_modifier: float = 1.0,
                 smoothing_modifier: float = 1.0):
        """
        Инициализация модификаторов интенсивности.

        Args:
            state_modifier: Модификатор на основе состояния системы (0.1-3.0)
            pattern_modifier: Модификатор на основе паттернов событий (0.5-2.0)
            dependency_modifier: Модификатор на основе зависимостей (0.7-1.3)
            category_modifier: Модификатор для категории события (0.8-1.5)
            subjective_time_modifier: Модификатор субъективного времени (0.7-1.5)
            smoothing_modifier: Модификатор сглаживания (0.9-1.1)

        Raises:
            ValueError: Если модификаторы выходят за допустимые диапазоны
        """
        self._validate_modifier("state_modifier", state_modifier, 0.1, 3.0)
        self._validate_modifier("pattern_modifier", pattern_modifier, 0.5, 2.0)
        self._validate_modifier("dependency_modifier", dependency_modifier, 0.7, 1.3)
        self._validate_modifier("category_modifier", category_modifier, 0.8, 1.5)
        self._validate_modifier("subjective_time_modifier", subjective_time_modifier, 0.7, 1.5)
        self._validate_modifier("smoothing_modifier", smoothing_modifier, 0.9, 1.1)

        self.state_modifier = state_modifier
        self.pattern_modifier = pattern_modifier
        self.dependency_modifier = dependency_modifier
        self.category_modifier = category_modifier
        self.subjective_time_modifier = subjective_time_modifier
        self.smoothing_modifier = smoothing_modifier

    def _validate_modifier(self, name: str, value: float, min_val: float, max_val: float) -> None:
        """Валидация диапазона модификатора."""
        if not (min_val <= value <= max_val):
            raise ValueError(f"{name} должен быть в диапазоне [{min_val}, {max_val}], получено: {value}")

    @property
    def combined_modifier(self) -> float:
        """Комбинированный модификатор (произведение всех модификаторов)."""
        return (self.state_modifier *
                self.pattern_modifier *
                self.dependency_modifier *
                self.category_modifier *
                self.subjective_time_modifier *
                self.smoothing_modifier)

    def to_dict(self) -> Dict[str, float]:
        """Сериализация модификаторов в словарь."""
        return {
            "state_modifier": self.state_modifier,
            "pattern_modifier": self.pattern_modifier,
            "dependency_modifier": self.dependency_modifier,
            "category_modifier": self.category_modifier,
            "subjective_time_modifier": self.subjective_time_modifier,
            "smoothing_modifier": self.smoothing_modifier,
            "combined_modifier": self.combined_modifier
        }


class IntensityAdapterInterface(ABC):
    """
    Абстрактный интерфейс для адаптеров интенсивности событий.

    Определяет контракт для компонентов, отвечающих за модификацию
    базовой интенсивности события на основе различных факторов.
    """

    @abstractmethod
    def adapt_intensity(self,
                       event_type: str,
                       base_intensity: float,
                       context_state: Optional[SelfState] = None,
                       pattern_modifier: float = 1.0,
                       dependency_modifier: float = 1.0) -> float:
        """
        Адаптирует интенсивность события на основе всех факторов.

        Args:
            event_type: Тип события (например, "confusion", "joy")
            base_intensity: Базовая интенсивность из конфигурации (-1.0 до 1.0)
            context_state: Текущее состояние системы Life (энергия, стабильность, etc.)
            pattern_modifier: Модификатор на основе паттернов событий (0.5-2.0)
            dependency_modifier: Модификатор на основе зависимостей событий (0.7-1.3)

        Returns:
            Адаптированная интенсивность в диапазоне типа события

        Raises:
            ValueError: Если входные параметры выходят за допустимые диапазоны
            RuntimeError: Если адаптация невозможна из-за внутренних ошибок
        """
        pass

    @abstractmethod
    def get_modifiers(self,
                     event_type: str,
                     context_state: Optional[SelfState] = None,
                     pattern_modifier: float = 1.0,
                     dependency_modifier: float = 1.0) -> IntensityModifier:
        """
        Возвращает все модификаторы интенсивности для анализа и отладки.

        Args:
            event_type: Тип события
            context_state: Текущее состояние системы
            pattern_modifier: Модификатор паттернов
            dependency_modifier: Модификатор зависимостей

        Returns:
            Структура со всеми модификаторами

        Note:
            Этот метод предназначен для отладки и мониторинга.
            Не должен использоваться в горячем пути генерации событий.
        """
        pass

    @abstractmethod
    def get_intensity_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы адаптера для мониторинга.

        Returns:
            Статистика по типам событий:
            - Количество адаптаций
            - Средние модификаторы
            - Волатильность интенсивностей
            - Кэш-хиты/миссы (если применимо)
        """
        pass

    @abstractmethod
    def reset_stats(self) -> None:
        """
        Сбрасывает внутреннюю статистику адаптера.

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
    def is_event_type_supported(self, event_type: str) -> bool:
        """
        Проверяет, поддерживается ли данный тип события.

        Args:
            event_type: Тип события для проверки

        Returns:
            True если тип поддерживается, False иначе
        """
        pass
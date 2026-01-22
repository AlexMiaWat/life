"""
Архитектурные контракты для EventGenerator и связанных компонентов.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol

from ..environment.event import Event
from ..state.self_state import SelfState


class IntensityAdapterProtocol(Protocol):
    """
    Контракт для адаптера интенсивности событий.

    Определяет интерфейс для компонентов, отвечающих за адаптацию
    интенсивности событий на основе состояния системы.
    """

    def adapt_intensity(
        self,
        event_type: str,
        base_intensity: float,
        context_state: Optional[SelfState] = None,
        pattern_modifier: float = 1.0,
        dependency_modifier: float = 1.0
    ) -> float:
        """
        Адаптирует интенсивность события.

        Args:
            event_type: Тип события
            base_intensity: Базовая интенсивность
            context_state: Текущее состояние системы
            pattern_modifier: Модификатор на основе паттернов
            dependency_modifier: Модификатор на основе зависимостей

        Returns:
            Адаптированная интенсивность
        """
        ...

    def get_intensity_history_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает статистику истории интенсивностей.

        Returns:
            Статистика по типам событий
        """
        ...


class PatternAnalyzerProtocol(Protocol):
    """
    Контракт для анализатора паттернов событий.

    Определяет интерфейс для компонентов, анализирующих паттерны
    в последовательностях событий.
    """

    def analyze_pattern_modifier(self, event_type: str, recent_events: List) -> float:
        """
        Анализирует паттерны событий и возвращает модификатор интенсивности.

        Args:
            event_type: Тип события для анализа
            recent_events: Список последних событий

        Returns:
            Модификатор интенсивности на основе паттернов
        """
        ...


class EventGeneratorProtocol(Protocol):
    """
    Контракт для генератора событий.

    Определяет интерфейс для компонентов, отвечающих за генерацию
    событий системы Life.
    """

    def generate(self, context_state: Optional[SelfState] = None) -> Event:
        """
        Генерирует событие согласно спецификации.

        Args:
            context_state: Текущее состояние системы Life

        Returns:
            Сгенерированное событие
        """
        ...

    def get_dependency_stats(self) -> dict[str, Any]:
        """
        Получить статистику работы системы зависимостей событий.

        Returns:
            Статистика зависимостей
        """
        ...


class EventDependencyManagerProtocol(Protocol):
    """
    Контракт для менеджера зависимостей событий.

    Определяет интерфейс для компонентов, управляющих зависимостями
    между типами событий.
    """

    def get_probability_modifiers(self) -> Dict[str, float]:
        """
        Получить модификаторы вероятностей для типов событий.

        Returns:
            Словарь модификаторов вероятностей
        """
        ...

    def record_event(self, event: Event) -> None:
        """
        Записать событие для анализа зависимостей.

        Args:
            event: Событие для записи
        """
        ...

    def detect_pattern(self, events: List[Event]) -> Optional[str]:
        """
        Обнаружить паттерн в последовательности событий.

        Args:
            events: Список событий для анализа

        Returns:
            Название обнаруженного паттерна или None
        """
        ...


class EnvironmentConfigManagerProtocol(Protocol):
    """
    Контракт для менеджера конфигурации окружения.

    Определяет интерфейс для компонентов, управляющих конфигурацией
    параметров генерации событий.
    """

    def get_config(self) -> Any:
        """
        Получить текущую конфигурацию окружения.

        Returns:
            Объект конфигурации
        """
        ...
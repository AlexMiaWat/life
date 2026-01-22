"""
Архитектурные контракты для системы памяти.
"""

from typing import Any, Dict, List, Optional, Protocol

from ..environment.event import Event
from ..memory.memory_types import MemoryEntry


class SensoryBufferProtocol(Protocol):
    """
    Контракт для сенсорного буфера.

    Определяет интерфейс для компонентов, реализующих кольцевой буфер
    для кратковременного хранения сенсорных данных.
    """

    def add_event(self, event: Event) -> None:
        """
        Добавить событие в сенсорный буфер.

        Args:
            event: Событие для добавления
        """
        ...

    def get_events_for_processing(self, max_events: int) -> List[Event]:
        """
        Получить события для обработки (удаляет их из буфера).

        Args:
            max_events: Максимальное количество событий

        Returns:
            Список событий для обработки
        """
        ...

    def peek_events(self, max_events: Optional[int] = None) -> List[Event]:
        """
        Посмотреть события без удаления из буфера.

        Args:
            max_events: Максимальное количество событий

        Returns:
            Список событий
        """
        ...

    def get_buffer_status(self) -> Dict[str, Any]:
        """
        Получить статус буфера.

        Returns:
            Информация о состоянии буфера
        """
        ...

    def clear_buffer(self) -> None:
        """Очистить буфер."""
        ...


class MemoryHierarchyManagerProtocol(Protocol):
    """
    Контракт для менеджера иерархии памяти.

    Определяет интерфейс для компонентов, координирующих работу
    между уровнями памяти.
    """

    def add_sensory_event(self, event: Event) -> None:
        """
        Добавить событие в сенсорный буфер.

        Args:
            event: Событие для добавления
        """
        ...

    def get_events_for_processing(self, max_events: int) -> List[Event]:
        """
        Получить события из сенсорного буфера для обработки.

        Args:
            max_events: Максимальное количество событий

        Returns:
            Список событий для обработки
        """
        ...

    def consolidate_memory(self, self_state) -> Dict[str, Any]:
        """
        Выполнить консолидацию памяти между уровнями.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Результаты консолидации
        """
        ...

    def set_episodic_memory(self, memory) -> None:
        """
        Установить ссылку на эпизодическую память.

        Args:
            memory: Объект эпизодической памяти
        """
        ...

    def query_memory(self, level: str, **query_params) -> Any:
        """
        Запрос к конкретному уровню памяти.

        Args:
            level: Уровень памяти ("sensory", "episodic", "semantic", "procedural")
            **query_params: Параметры запроса

        Returns:
            Результаты запроса
        """
        ...

    def get_status(self) -> Dict[str, Any]:
        """
        Получить статус всей иерархии памяти.

        Returns:
            Статус всех уровней памяти
        """
        ...

    def reset_hierarchy(self) -> None:
        """Сбросить всю иерархию памяти."""
        ...


class SemanticMemoryStoreProtocol(Protocol):
    """
    Контракт для семантического хранилища памяти.

    Определяет интерфейс для компонентов, управляющих семантической памятью.
    """

    def store_concept(self, concept: str, attributes: Dict[str, Any]) -> None:
        """
        Сохранить семантическую концепцию.

        Args:
            concept: Название концепции
            attributes: Атрибуты концепции
        """
        ...

    def retrieve_concept(self, concept: str) -> Optional[Dict[str, Any]]:
        """
        Извлечь семантическую концепцию.

        Args:
            concept: Название концепции

        Returns:
            Атрибуты концепции или None
        """
        ...

    def get_related_concepts(self, concept: str, limit: int = 10) -> List[str]:
        """
        Найти связанные концепции.

        Args:
            concept: Базовая концепция
            limit: Максимальное количество результатов

        Returns:
            Список связанных концепций
        """
        ...


class ProceduralMemoryStoreProtocol(Protocol):
    """
    Контракт для процедурного хранилища памяти.

    Определяет интерфейс для компонентов, управляющих процедурной памятью.
    """

    def store_procedure(self, procedure_name: str, steps: List[Dict[str, Any]]) -> None:
        """
        Сохранить процедуру.

        Args:
            procedure_name: Название процедуры
            steps: Шаги процедуры
        """
        ...

    def retrieve_procedure(self, procedure_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Извлечь процедуру.

        Args:
            procedure_name: Название процедуры

        Returns:
            Шаги процедуры или None
        """
        ...

    def get_similar_procedures(self, context: Dict[str, Any], limit: int = 5) -> List[str]:
        """
        Найти похожие процедуры по контексту.

        Args:
            context: Контекст для поиска
            limit: Максимальное количество результатов

        Returns:
            Список названий похожих процедур
        """
        ...
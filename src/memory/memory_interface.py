"""
Интерфейсы для различных типов памяти в системе Life.

Предоставляет унифицированные интерфейсы для работы с разными уровнями памяти:
эпизодической, семантической, процедурной и архивной.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass

from .memory_types import MemoryEntry
from .index_engine import MemoryQuery


@dataclass
class MemoryStatistics:
    """Статистика использования памяти."""
    total_entries: int
    active_entries: int = 0
    archived_entries: int = 0
    average_significance: float = 0.0
    oldest_timestamp: Optional[float] = None
    newest_timestamp: Optional[float] = None
    memory_type: str = "unknown"


class MemoryInterface(ABC):
    """
    Базовый интерфейс для всех типов памяти.

    Определяет общие методы для работы с памятью независимо от ее типа
    (эпизодическая, семантическая, процедурная, архивная).
    """

    @abstractmethod
    def get_statistics(self) -> MemoryStatistics:
        """
        Получить статистику использования памяти.

        Returns:
            MemoryStatistics: Статистика памяти
        """
        pass

    @abstractmethod
    def validate_integrity(self) -> bool:
        """
        Проверить целостность данных памяти.

        Returns:
            bool: True если данные корректны
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Очистить память."""
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """
        Проверить, пустая ли память.

        Returns:
            bool: True если память пуста
        """
        pass

    @property
    @abstractmethod
    def size(self) -> int:
        """
        Получить размер памяти.

        Returns:
            int: Количество элементов в памяти
        """
        pass


class EpisodicMemoryInterface(MemoryInterface):
    """
    Интерфейс для эпизодической памяти.

    Работа с последовательностями событий и их значимости.
    """

    @abstractmethod
    def add_entry(self, entry: MemoryEntry) -> None:
        """
        Добавить запись в память.

        Args:
            entry: Запись памяти для добавления
        """
        pass

    @abstractmethod
    def get_entries(
        self,
        event_type: Optional[str] = None,
        min_significance: Optional[float] = None,
        start_timestamp: Optional[float] = None,
        end_timestamp: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[MemoryEntry]:
        """
        Получить записи из памяти с фильтрацией.

        Args:
            event_type: Фильтр по типу события
            min_significance: Минимальная значимость
            start_timestamp: Начало временного диапазона
            end_timestamp: Конец временного диапазона
            limit: Максимальное количество записей

        Returns:
            List[MemoryEntry]: Отфильтрованные записи
        """
        pass

    @abstractmethod
    def search_entries(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Поиск записей с использованием запроса.

        Args:
            query: Запрос для поиска

        Returns:
            List[MemoryEntry]: Найденные записи
        """
        pass

    @abstractmethod
    def archive_old_entries(
        self,
        max_age: Optional[float] = None,
        min_weight: Optional[float] = None,
        min_significance: Optional[float] = None,
    ) -> int:
        """
        Перенести старые записи в архив.

        Args:
            max_age: Максимальный возраст записи
            min_weight: Минимальный вес записи
            min_significance: Минимальная значимость

        Returns:
            int: Количество заархивированных записей
        """
        pass


class SemanticMemoryInterface(MemoryInterface):
    """
    Интерфейс для семантической памяти.

    Работа с концепциями и их взаимосвязями.
    """

    @abstractmethod
    def add_concept(self, concept) -> None:
        """
        Добавить концепцию в память.

        Args:
            concept: Концепция для добавления
        """
        pass

    @abstractmethod
    def get_concept(self, concept_id: str):
        """
        Получить концепцию по ID.

        Args:
            concept_id: Идентификатор концепции

        Returns:
            Концепция или None
        """
        pass

    @abstractmethod
    def search_concepts(self, query: str, limit: int = 10) -> List[Any]:
        """
        Поиск концепций по текстовому запросу.

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            List[Any]: Найденные концепции
        """
        pass

    @abstractmethod
    def find_related_concepts(self, concept_id: str, max_depth: int = 2) -> Dict[str, float]:
        """
        Найти связанные концепции.

        Args:
            concept_id: Исходная концепция
            max_depth: Максимальная глубина поиска

        Returns:
            Dict[str, float]: Концепции с оценками релевантности
        """
        pass


class ProceduralMemoryInterface(MemoryInterface):
    """
    Интерфейс для процедурной памяти.

    Работа с навыками и автоматизированными паттернами поведения.
    """

    @abstractmethod
    def add_pattern(self, pattern) -> None:
        """
        Добавить процедурный паттерн.

        Args:
            pattern: Паттерн для добавления
        """
        pass

    @abstractmethod
    def get_pattern(self, pattern_id: str):
        """
        Получить паттерн по ID.

        Args:
            pattern_id: Идентификатор паттерна

        Returns:
            Паттерн или None
        """
        pass

    @abstractmethod
    def learn_from_experience(
        self,
        context: Dict[str, Any],
        actions: List[Tuple[str, Dict[str, Any]]],
        outcome: str,
        success: bool,
    ) -> None:
        """
        Извлечь урок из опыта выполнения.

        Args:
            context: Контекст выполнения
            actions: Выполненные действия
            outcome: Результат выполнения
            success: Успешность выполнения
        """
        pass

    @abstractmethod
    def execute_best_pattern(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Выполнить наиболее подходящий паттерн.

        Args:
            context: Контекст выполнения

        Returns:
            Optional[Dict[str, Any]]: Результат выполнения или None
        """
        pass
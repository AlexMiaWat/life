"""
Архитектурные контракты для Memory Hierarchy API.

Определяет интерфейсы и гарантии для методов query_memory и consolidate_memory.
Обеспечивает типизацию, спецификацию форматов данных и контракты на поведение.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Protocol, Union, Optional
from dataclasses import dataclass


@dataclass
class MemoryQueryParams:
    """
    Параметры запроса к памяти.

    Определяет все возможные параметры для различных типов запросов.
    """

    # Общие параметры
    limit: Optional[int] = None  # Максимальное количество результатов
    offset: Optional[int] = None  # Смещение для пагинации

    # Параметры для семантического поиска
    query: Optional[str] = None  # Текстовая строка поиска
    confidence_threshold: Optional[float] = None  # Минимальный уровень уверенности

    # Параметры для сенсорного буфера
    max_events: Optional[int] = None  # Максимальное количество событий

    # Параметры для процедурной памяти
    context: Optional[Dict[str, Any]] = None  # Контекст для поиска паттернов

    # Параметры для эпизодической памяти
    time_range_start: Optional[float] = None  # Начало временного диапазона
    time_range_end: Optional[float] = None  # Конец временного диапазона
    event_types: Optional[List[str]] = None  # Фильтр по типам событий


@dataclass
class MemoryQueryResult:
    """
    Результат запроса к памяти.

    Стандартизированный формат ответа для всех уровней памяти.
    """

    level: str  # Уровень памяти ("sensory", "episodic", "semantic", "procedural")
    results: List[Any]  # Список результатов запроса
    total_count: int  # Общее количество доступных результатов
    query_params: MemoryQueryParams  # Параметры запроса
    execution_time: float  # Время выполнения запроса
    success: bool  # Успешность выполнения
    error_message: Optional[str] = None  # Сообщение об ошибке (если success=False)


@dataclass
class ConsolidationResult:
    """
    Результат консолидации памяти.

    Статистика переноса данных между уровнями памяти.
    """

    sensory_to_episodic_transfers: int  # Количество переносов sensory → episodic
    episodic_to_semantic_transfers: int  # Количество переносов episodic → semantic
    semantic_consolidations: int  # Количество семантических консолидаций
    procedural_optimizations: int  # Количество процедурных оптимизаций
    timestamp: float  # Время выполнения консолидации
    duration: float  # Длительность выполнения
    success: bool  # Успешность выполнения
    error_message: Optional[str] = None  # Сообщение об ошибке (если success=False)

    # Детальная статистика
    details: Dict[str, Any] = None  # Дополнительная информация


class MemoryHierarchyAPIContract(Protocol):
    """
    Контракт для Memory Hierarchy API.

    Определяет интерфейс для взаимодействия с иерархией памяти.
    """

    @abstractmethod
    def query_memory(self, level: str, **query_params) -> MemoryQueryResult:
        """
        Запрос к конкретному уровню памяти.

        Архитектурный контракт:
        1. Валидация входных параметров
        2. Thread-safety: Метод безопасен для конкурентного доступа
        3. Типизация: Возвращает стандартизированный MemoryQueryResult
        4. Обработка ошибок: Исключения не должны нарушать состояние
        5. Производительность: Запросы должны быть эффективными

        Args:
            level: Уровень памяти ("sensory", "episodic", "semantic", "procedural")
            **query_params: Параметры запроса (см. MemoryQueryParams)

        Returns:
            MemoryQueryResult: Стандартизированный результат запроса

        Raises:
            ValueError: Если уровень памяти неизвестен
            RuntimeError: Если запрос не может быть выполнен по системным причинам
        """

    @abstractmethod
    def consolidate_memory(self, self_state) -> ConsolidationResult:
        """
        Выполнить консолидацию памяти между уровнями.

        Архитектурный контракт:
        1. Атомарность: Все переносы выполняются как единая транзакция
        2. Thread-safety: Метод безопасен для конкурентного доступа
        3. Отказоустойчивость: Частичные сбои не нарушают общее состояние
        4. Типизация: Возвращает стандартизированный ConsolidationResult
        5. Логирование: Все операции должны быть залогированы

        Args:
            self_state: Текущее состояние системы (SelfState)

        Returns:
            ConsolidationResult: Статистика выполненной консолидации

        Raises:
            RuntimeError: Если консолидация не может быть выполнена
        """


class MemoryLevelContract(ABC):
    """
    Контракт для отдельного уровня памяти.

    Определяет интерфейс для компонентов, представляющих уровни памяти.
    """

    @property
    @abstractmethod
    def level_name(self) -> str:
        """Имя уровня памяти."""

    @abstractmethod
    def query(self, params: MemoryQueryParams) -> MemoryQueryResult:
        """
        Выполнить запрос к этому уровню памяти.

        Args:
            params: Параметры запроса

        Returns:
            MemoryQueryResult: Результат запроса
        """

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику уровня памяти.

        Returns:
            Dict со статистикой уровня
        """

    @abstractmethod
    def is_available(self) -> bool:
        """
        Проверить доступность уровня памяти.

        Returns:
            bool: True если уровень доступен
        """

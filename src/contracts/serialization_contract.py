"""
Архитектурный контракт для сериализации компонентов системы.

Определяет интерфейсы и гарантии для методов to_dict() во всех компонентах.
Обеспечивает thread-safety, эффективность и отказоустойчивость сериализации.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol
from threading import Lock


class Serializable(Protocol):
    """
    Протокол для сериализуемых компонентов.

    Все компоненты, поддерживающие сериализацию, должны реализовывать этот протокол.
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализовать состояние компонента в словарь.

        Returns:
            Dict[str, Any]: Словарь с состоянием компонента

        Архитектурные гарантии:
        - Thread-safe: Метод должен быть безопасен для вызова из разных потоков
        - Атомарный: Сериализация представляет собой консистентное состояние
        - Отказоустойчивый: Исключения не должны приводить к повреждению состояния
        - Детерминированный: Для одинакового состояния возвращает одинаковый результат
        """
        ...


class SerializationContract(ABC):
    """
    Архитектурный контракт для компонентов с поддержкой сериализации.

    Определяет стандартные гарантии и интерфейсы для всех сериализуемых компонентов.
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализовать состояние компонента.

        Архитектурный контракт:
        1. Thread-safety: Метод должен быть безопасен для конкурентного доступа
        2. Атомарность: Сериализация должна представлять консистентное состояние
        3. Отказоустойчивость: Исключения не должны повреждать внутреннее состояние
        4. Эффективность: Сериализация должна быть эффективной по ресурсам
        5. Детерминированность: Одинаковое состояние -> одинаковый результат

        Returns:
            Dict[str, Any]: Сериализованное состояние с гарантированной структурой

        Raises:
            SerializationError: Если сериализация невозможна по системным причинам
        """
        pass

    @abstractmethod
    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Получить метаданные сериализации для валидации и отладки.

        Returns:
            Dict[str, Any]: Метаданные содержащие:
            - version: str - версия формата сериализации
            - timestamp: float - время сериализации
            - checksum: str - контрольная сумма для валидации
            - component_type: str - тип компонента
        """
        pass


class SerializationError(Exception):
    """
    Исключение при ошибках сериализации.

    Указывает на проблемы с сериализацией состояния компонента.
    """
    pass


class ThreadSafeSerializer:
    """
    Thread-safe обертка для сериализации компонентов.

    Обеспечивает thread-safety для компонентов, которые не имеют встроенной защиты.
    """

    def __init__(self, component: Serializable, lock: Lock = None):
        self._component = component
        self._lock = lock or Lock()

    def to_dict(self) -> Dict[str, Any]:
        """
        Thread-safe сериализация компонента.

        Returns:
            Dict[str, Any]: Сериализованное состояние
        """
        with self._lock:
            return self._component.to_dict()

    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Thread-safe получение метаданных сериализации.

        Returns:
            Dict[str, Any]: Метаданные сериализации
        """
        with self._lock:
            if hasattr(self._component, 'get_serialization_metadata'):
                return self._component.get_serialization_metadata()
            else:
                # Минимальные метаданные для совместимости
                return {
                    "version": "1.0",
                    "component_type": type(self._component).__name__,
                    "timestamp": 0.0,
                    "checksum": ""
                }
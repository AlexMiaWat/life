"""
Базовые архитектурные контракты для системы Life.

Определяет фундаментальные интерфейсы и контракты для компонентов системы.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass


@dataclass
class ContractViolation:
    """
    Структура для описания нарушения контракта.

    Используется для документирования и обработки нарушений архитектурных контрактов.
    """
    component: str
    contract_name: str
    violation_type: str  # "range_violation", "type_error", "logic_error"
    expected: Any
    actual: Any
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}


class ContractValidator(ABC):
    """
    Базовый интерфейс для валидаторов контрактов.

    Определяет методы для проверки соблюдения архитектурных контрактов.
    """

    @abstractmethod
    def validate(self, component: Any, context: Dict[str, Any] = None) -> List[ContractViolation]:
        """
        Выполняет валидацию контракта для компонента.

        Args:
            component: Компонент для валидации
            context: Дополнительный контекст валидации

        Returns:
            Список нарушений контракта (пустой список означает успешную валидацию)
        """
        pass

    @abstractmethod
    def get_contract_name(self) -> str:
        """Возвращает имя контракта."""
        pass

    @abstractmethod
    def get_supported_components(self) -> List[str]:
        """Возвращает список поддерживаемых типов компонентов."""
        pass


class RangeContract:
    """
    Контракт для диапазонов значений.

    Определяет допустимые диапазоны для числовых параметров компонентов.
    """

    def __init__(self, field_ranges: Dict[str, tuple]):
        """
        Args:
            field_ranges: Словарь поле -> (min_value, max_value)
        """
        self.field_ranges = field_ranges

    def validate_field(self, field_name: str, value: float) -> Optional[ContractViolation]:
        """
        Валидирует значение поля на соответствие диапазону.

        Returns:
            ContractViolation если значение вне диапазона, None иначе
        """
        if field_name not in self.field_ranges:
            return None

        min_val, max_val = self.field_ranges[field_name]
        if not (min_val <= value <= max_val):
            return ContractViolation(
                component="unknown",
                contract_name=self.__class__.__name__,
                violation_type="range_violation",
                expected=f"[{min_val}, {max_val}]",
                actual=value,
                context={"field": field_name}
            )

        return None


class TypeContract:
    """
    Контракт для типов данных.

    Определяет ожидаемые типы для полей компонентов.
    """

    def __init__(self, field_types: Dict[str, type]):
        """
        Args:
            field_types: Словарь поле -> ожидаемый тип
        """
        self.field_types = field_types

    def validate_field(self, field_name: str, value: Any) -> Optional[ContractViolation]:
        """
        Валидирует тип значения поля.

        Returns:
            ContractViolation если тип не соответствует, None иначе
        """
        if field_name not in self.field_types:
            return None

        expected_type = self.field_types[field_name]
        if not isinstance(value, expected_type):
            return ContractViolation(
                component="unknown",
                contract_name=self.__class__.__name__,
                violation_type="type_error",
                expected=expected_type.__name__,
                actual=type(value).__name__,
                context={"field": field_name}
            )

        return None
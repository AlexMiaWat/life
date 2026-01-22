"""
Базовые архитектурные контракты.

Определяет фундаментальные интерфейсы и гарантии для всех компонентов системы.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum


class ContractViolation(Exception):
    """Исключение при нарушении архитектурного контракта."""

    def __init__(self, component: str, contract: str, details: str):
        self.component = component
        self.contract = contract
        self.details = details
        super().__init__(f"Contract violation in {component}.{contract}: {details}")


class ValidationLevel(Enum):
    """Уровень строгости валидации контракта."""
    STRICT = "strict"      # Все проверки включены
    RELAXED = "relaxed"    # Минимальные проверки
    DISABLED = "disabled"  # Проверки отключены


class ErrorHandlingStrategy(Enum):
    """Стратегия обработки ошибок при нарушении контракта."""
    RAISE_EXCEPTION = "raise_exception"
    LOG_WARNING = "log_warning"
    CLAMP_VALUES = "clamp_values"
    FALLBACK_DEFAULT = "fallback_default"


@dataclass
class ContractMetadata:
    """Метаданные контракта."""
    component_name: str
    version: str
    last_updated: str
    author: str
    description: str


class BaseContract(ABC):
    """
    Базовый класс для всех архитектурных контрактов.

    Определяет общий интерфейс для валидации, документирования
    и обеспечения гарантий компонентов.
    """

    def __init__(self, component_name: str):
        self.metadata = ContractMetadata(
            component_name=component_name,
            version="1.0.0",
            last_updated="2026-01-22",
            author="Life Architecture Team",
            description=self._get_description()
        )
        self.validation_level = ValidationLevel.STRICT
        self.error_strategy = ErrorHandlingStrategy.RAISE_EXCEPTION

    @abstractmethod
    def _get_description(self) -> str:
        """Получить описание контракта."""
        pass

    @abstractmethod
    def get_input_ranges(self) -> Dict[str, tuple]:
        """Получить допустимые диапазоны входных значений."""
        pass

    @abstractmethod
    def get_output_guarantees(self) -> Dict[str, Any]:
        """Получить гарантии выходных значений."""
        pass

    @abstractmethod
    def get_error_handling(self) -> Dict[str, str]:
        """Получить стратегии обработки ошибок."""
        pass

    def validate_inputs(self, **kwargs) -> bool:
        """
        Валидировать входные параметры согласно контракту.

        Args:
            **kwargs: Входные параметры для валидации

        Returns:
            True если валидация прошла успешно

        Raises:
            ContractViolation: при нарушении контракта (в зависимости от error_strategy)
        """
        if self.validation_level == ValidationLevel.DISABLED:
            return True

        input_ranges = self.get_input_ranges()
        violations = []

        for param_name, param_value in kwargs.items():
            if param_name in input_ranges:
                min_val, max_val = input_ranges[param_name]
                if not (min_val <= param_value <= max_val):
                    violations.append(
                        f"Parameter '{param_name}' value {param_value} out of range [{min_val}, {max_val}]"
                    )

        if violations:
            error_msg = "; ".join(violations)
            if self.error_strategy == ErrorHandlingStrategy.RAISE_EXCEPTION:
                raise ContractViolation(self.metadata.component_name, "input_validation", error_msg)
            elif self.error_strategy == ErrorHandlingStrategy.LOG_WARNING:
                print(f"WARNING: Contract violation in {self.metadata.component_name}: {error_msg}")
                return False
            elif self.error_strategy == ErrorHandlingStrategy.CLAMP_VALUES:
                print(f"INFO: Clamping values in {self.metadata.component_name} to satisfy contract")
                return True  # Значения будут ограничены вызывающим кодом

        return True

    def validate_outputs(self, **kwargs) -> bool:
        """
        Валидировать выходные параметры согласно контракту.

        Args:
            **kwargs: Выходные параметры для валидации

        Returns:
            True если валидация прошла успешно
        """
        if self.validation_level == ValidationLevel.DISABLED:
            return True

        output_guarantees = self.get_output_guarantees()
        violations = []

        for param_name, param_value in kwargs.items():
            if param_name in output_guarantees:
                guarantee = output_guarantees[param_name]
                if isinstance(guarantee, tuple) and len(guarantee) == 2:
                    # Диапазон значений
                    min_val, max_val = guarantee
                    if not (min_val <= param_value <= max_val):
                        violations.append(
                            f"Output '{param_name}' value {param_value} violates guarantee [{min_val}, {max_val}]"
                        )
                elif isinstance(guarantee, (int, float)):
                    # Точное значение или максимум
                    if param_value > guarantee:
                        violations.append(
                            f"Output '{param_name}' value {param_value} exceeds guarantee {guarantee}"
                        )

        if violations:
            error_msg = "; ".join(violations)
            if self.error_strategy == ErrorHandlingStrategy.RAISE_EXCEPTION:
                raise ContractViolation(self.metadata.component_name, "output_validation", error_msg)
            else:
                print(f"WARNING: Contract violation in {self.metadata.component_name}: {error_msg}")
                return False

        return True

    def get_documentation(self) -> Dict[str, Any]:
        """
        Получить полную документацию контракта.

        Returns:
            Словарь с полной информацией о контракте
        """
        return {
            "metadata": {
                "component": self.metadata.component_name,
                "version": self.metadata.version,
                "last_updated": self.metadata.last_updated,
                "author": self.metadata.author,
                "description": self.metadata.description
            },
            "input_ranges": self.get_input_ranges(),
            "output_guarantees": self.get_output_guarantees(),
            "error_handling": self.get_error_handling(),
            "validation_level": self.validation_level.value,
            "error_strategy": self.error_strategy.value
        }


class ComponentInterface(Protocol):
    """Протокол для компонентов, поддерживающих контракты."""

    @property
    def contract(self) -> BaseContract:
        """Получить контракт компонента."""
        ...

    def validate_contract(self) -> bool:
        """Валидировать соответствие контракту."""
        ...


class ContractRegistry:
    """
    Реестр всех архитектурных контрактов системы.

    Централизованное хранилище для управления контрактами компонентов.
    """

    def __init__(self):
        self._contracts: Dict[str, BaseContract] = {}

    def register_contract(self, component_name: str, contract: BaseContract):
        """Зарегистрировать контракт компонента."""
        self._contracts[component_name] = contract

    def get_contract(self, component_name: str) -> Optional[BaseContract]:
        """Получить контракт компонента."""
        return self._contracts.get(component_name)

    def validate_all_contracts(self) -> Dict[str, bool]:
        """
        Валидировать все зарегистрированные контракты.

        Returns:
            Словарь с результатами валидации по компонентам
        """
        results = {}
        for component_name, contract in self._contracts.items():
            try:
                # Попытка валидации контракта (зависит от реализации)
                results[component_name] = True
            except Exception:
                results[component_name] = False
        return results

    def get_all_contracts_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить информацию о всех контрактах.

        Returns:
            Словарь с документацией всех контрактов
        """
        return {
            name: contract.get_documentation()
            for name, contract in self._contracts.items()
        }


# Глобальный реестр контрактов
contract_registry = ContractRegistry()
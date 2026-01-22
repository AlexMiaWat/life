"""
Менеджер архитектурных контрактов.

Централизованно управляет валидацией всех архитектурных контрактов в системе.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from .base_contract import ContractValidator, ContractViolation
from .self_state_contract import SelfStateContract, self_state_contract
from .event_generator_contract import EventGeneratorContract, event_generator_contract
from .intensity_adapter_contract import IntensityAdapterContract, intensity_adapter_contract

logger = logging.getLogger(__name__)


class ContractManager:
    """
    Менеджер архитектурных контрактов.

    Предоставляет унифицированный интерфейс для валидации компонентов
    и мониторинга соблюдения архитектурных контрактов.
    """

    def __init__(self):
        """Инициализация менеджера контрактов."""
        self.contracts: Dict[str, ContractValidator] = {}
        self._register_builtin_contracts()

        # Статистика валидаций
        self.validation_stats = {
            "total_validations": 0,
            "violations_found": 0,
            "components_validated": set(),
            "contract_types_used": set()
        }

    def _register_builtin_contracts(self) -> None:
        """Регистрирует встроенные контракты."""
        self.register_contract(self_state_contract)
        self.register_contract(event_generator_contract)
        self.register_contract(intensity_adapter_contract)

    def register_contract(self, contract: ContractValidator) -> None:
        """
        Регистрирует новый контракт.

        Args:
            contract: Экземпляр контракта для регистрации
        """
        contract_name = contract.get_contract_name()
        self.contracts[contract_name] = contract
        logger.info(f"Registered contract: {contract_name}")

    def validate_component(self, component: Any, component_type: Optional[str] = None,
                          context: Dict[str, Any] = None) -> List[ContractViolation]:
        """
        Выполняет валидацию компонента с использованием подходящих контрактов.

        Args:
            component: Компонент для валидации
            component_type: Тип компонента (если известен)
            context: Дополнительный контекст валидации

        Returns:
            Список найденных нарушений контракта
        """
        self.validation_stats["total_validations"] += 1

        all_violations = []

        # Определяем подходящие контракты
        applicable_contracts = self._find_applicable_contracts(component, component_type)

        for contract in applicable_contracts:
            try:
                violations = contract.validate(component, context)
                if violations:
                    all_violations.extend(violations)
                    self.validation_stats["violations_found"] += len(violations)

                self.validation_stats["contract_types_used"].add(contract.get_contract_name())

            except Exception as e:
                logger.error(f"Error validating with contract {contract.get_contract_name()}: {e}")
                # Продолжаем с другими контрактами

        if component_type:
            self.validation_stats["components_validated"].add(component_type)
        else:
            self.validation_stats["components_validated"].add(type(component).__name__)

        return all_violations

    def _find_applicable_contracts(self, component: Any, component_type: Optional[str] = None) -> List[ContractValidator]:
        """
        Находит контракты, применимые к данному компоненту.

        Args:
            component: Компонент для анализа
            component_type: Явно указанный тип компонента

        Returns:
            Список применимых контрактов
        """
        applicable = []

        # Если тип указан явно, ищем контракты по типу
        if component_type:
            for contract in self.contracts.values():
                if component_type in contract.get_supported_components():
                    applicable.append(contract)
            return applicable

        # Иначе определяем тип по имени класса
        component_class_name = type(component).__name__

        for contract in self.contracts.values():
            if component_class_name in contract.get_supported_components():
                applicable.append(contract)

        return applicable

    def validate_system_state(self, self_state: Any, event_generator: Any = None,
                             context: Dict[str, Any] = None) -> Dict[str, List[ContractViolation]]:
        """
        Выполняет комплексную валидацию состояния системы.

        Args:
            self_state: Состояние системы (SelfState)
            event_generator: Генератор событий (опционально)
            context: Контекст валидации

        Returns:
            Словарь компонент -> список нарушений
        """
        results = {}

        # Валидация SelfState
        results["SelfState"] = self.validate_component(self_state, "SelfState", context)

        # Валидация EventGenerator
        if event_generator:
            results["EventGenerator"] = self.validate_component(event_generator, "EventGenerator", context)

        return results

    def get_validation_report(self) -> Dict[str, Any]:
        """
        Возвращает отчет о работе менеджера контрактов.

        Returns:
            Статистика валидаций и найденных нарушений
        """
        return {
            "validation_stats": {
                "total_validations": self.validation_stats["total_validations"],
                "violations_found": self.validation_stats["violations_found"],
                "violation_rate": (
                    self.validation_stats["violations_found"] / max(1, self.validation_stats["total_validations"])
                ),
                "unique_components_validated": len(self.validation_stats["components_validated"]),
                "unique_contracts_used": len(self.validation_stats["contract_types_used"])
            },
            "registered_contracts": list(self.contracts.keys()),
            "components_validated": list(self.validation_stats["components_validated"]),
            "contracts_used": list(self.validation_stats["contract_types_used"])
        }

    def reset_stats(self) -> None:
        """Сбрасывает статистику валидаций."""
        self.validation_stats = {
            "total_validations": 0,
            "violations_found": 0,
            "components_validated": set(),
            "contract_types_used": set()
        }

    def get_registered_contracts(self) -> Dict[str, ContractValidator]:
        """Возвращает все зарегистрированные контракты."""
        return self.contracts.copy()


# Глобальный экземпляр менеджера контрактов
contract_manager = ContractManager()
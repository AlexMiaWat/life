"""
Архитектурный контракт для EventGenerator компонента.

Определяет интерфейсы, диапазоны значений и гарантии для генератора событий.
"""

from typing import Any, Dict, List, Optional
from .base_contract import ContractValidator, ContractViolation, RangeContract, TypeContract


class EventGeneratorContract(ContractValidator):
    """
    Архитектурный контракт для EventGenerator.

    Гарантирует корректность генерации событий и взаимодействия с субкомпонентами.
    """

    def __init__(self):
        # Диапазоны значений для параметров генератора
        self.range_contract = RangeContract({
            "base_intensity": (0.0, 1.0),  # Базовая интенсивность события
            "adapted_intensity": (0.0, 3.0),  # Адаптированная интенсивность
            "pattern_modifier": (0.1, 2.0),  # Модификатор паттернов
            "dependency_modifier": (0.5, 2.0),  # Модификатор зависимостей
            "category_modifier": (0.5, 1.5),  # Категориальный модификатор
            "subjective_modifier": (0.5, 2.0),  # Модификатор субъективного времени
            "smoothing_modifier": (0.1, 3.0),  # Сглаженный модификатор
        })

        # Типы данных
        self.type_contract = TypeContract({
            "types": list,  # Список типов событий
            "base_weights": list,  # Базовые веса событий
            "dependency_manager": object,  # Менеджер зависимостей
            "config_manager": object,  # Менеджер конфигурации
            "intensity_adapter": object,  # Адаптер интенсивности
            "pattern_analyzer": object,  # Анализатор паттернов
            "smoothing_engine": object,  # Движок сглаживания
        })

    def validate(self, component: Any, context: Dict[str, Any] = None) -> List[ContractViolation]:
        """
        Выполняет комплексную валидацию EventGenerator.

        Args:
            component: Экземпляр EventGenerator для валидации
            context: Контекст валидации

        Returns:
            Список нарушений контракта
        """
        violations = []

        # Базовая структурная валидация
        structure_violations = self._validate_structure(component)
        violations.extend(structure_violations)

        # Валидация конфигурации событий
        config_violations = self._validate_event_configuration(component)
        violations.extend(config_violations)

        # Валидация субкомпонентов
        component_violations = self._validate_subcomponents(component)
        violations.extend(component_violations)

        return violations

    def _validate_structure(self, component: Any) -> List[ContractViolation]:
        """Валидирует базовую структуру компонента."""
        violations = []

        required_attributes = [
            "types", "base_weights", "dependency_manager",
            "config_manager", "intensity_calculator", "pattern_analyzer", "smoothing_engine"
        ]

        for attr in required_attributes:
            if not hasattr(component, attr):
                violations.append(ContractViolation(
                    component="EventGenerator",
                    contract_name="EventGeneratorContract",
                    violation_type="structure_error",
                    expected=f"has attribute '{attr}'",
                    actual="missing",
                    context={"attribute": attr}
                ))

        return violations

    def _validate_event_configuration(self, component: Any) -> List[ContractViolation]:
        """Валидирует конфигурацию событий."""
        violations = []

        # Проверка соответствия типов и весов
        if hasattr(component, 'types') and hasattr(component, 'base_weights'):
            types_count = len(component.types)
            weights_count = len(component.base_weights)

            if types_count != weights_count:
                violations.append(ContractViolation(
                    component="EventGenerator",
                    contract_name="EventGeneratorContract",
                    violation_type="configuration_error",
                    expected=f"equal lengths (types={types_count}, weights={weights_count})",
                    actual=f"types={types_count}, weights={weights_count}",
                    context={"reason": "types_and_weights_mismatch"}
                ))

            # Проверка диапазона весов
            for i, weight in enumerate(component.base_weights):
                if not (0.0 <= weight <= 1.0):
                    violations.append(ContractViolation(
                        component="EventGenerator",
                        contract_name="EventGeneratorContract",
                        violation_type="range_violation",
                        expected="[0.0, 1.0]",
                        actual=weight,
                        context={"field": f"base_weights[{i}]", "event_type": component.types[i] if i < len(component.types) else "unknown"}
                    ))

        return violations

    def _validate_subcomponents(self, component: Any) -> List[ContractViolation]:
        """Валидирует субкомпоненты."""
        violations = []

        # Проверка наличия интерфейсов у субкомпонентов
        subcomponents = {
            "dependency_manager": ["get_probability_modifiers", "get_dependency_stats"],
            "config_manager": ["get_config"],
            "intensity_calculator": ["calculate"],
            "pattern_analyzer": ["analyze"],
            "smoothing_engine": ["smooth_modifier", "smooth_intensity"]
        }

        for comp_name, required_methods in subcomponents.items():
            if hasattr(component, comp_name):
                subcomp = getattr(component, comp_name)
                for method in required_methods:
                    if not hasattr(subcomp, method):
                        violations.append(ContractViolation(
                            component=f"EventGenerator.{comp_name}",
                            contract_name="EventGeneratorContract",
                            violation_type="interface_error",
                            expected=f"has method '{method}'",
                            actual="missing",
                            context={"subcomponent": comp_name, "method": method}
                        ))

        return violations

    def get_contract_name(self) -> str:
        """Возвращает имя контракта."""
        return "EventGeneratorContract"

    def get_supported_components(self) -> List[str]:
        """Возвращает список поддерживаемых типов компонентов."""
        return ["EventGenerator"]


# Глобальный экземпляр контракта
event_generator_contract = EventGeneratorContract()
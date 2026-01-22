"""
Архитектурный контракт для IntensityAdapter компонента.

Определяет интерфейсы, диапазоны значений и гарантии для адаптера интенсивности.
"""

from typing import Any, Dict, List, Optional
from .base_contract import ContractValidator, ContractViolation, RangeContract, TypeContract


class IntensityAdapterContract(ContractValidator):
    """
    Архитектурный контракт для IntensityAdapter.

    Гарантирует корректность адаптации интенсивности событий.
    """

    def __init__(self):
        # Диапазоны значений для модификаторов
        self.range_contract = RangeContract({
            "state_modifier": (0.1, 3.0),      # Модификатор состояния
            "pattern_modifier": (0.1, 2.0),    # Модификатор паттернов
            "dependency_modifier": (0.5, 2.0), # Модификатор зависимостей
            "category_modifier": (0.5, 1.5),   # Категориальный модификатор
            "subjective_modifier": (0.5, 2.0), # Модификатор субъективного времени
            "smoothing_modifier": (0.1, 3.0),  # Сглаженный модификатор
            "combined_modifier": (0.01, 9.0),  # Комбинированный модификатор
            "adapted_intensity": (0.0, 3.0),   # Итоговая адаптированная интенсивность
        })

        # Типы данных
        self.type_contract = TypeContract({
            "smoothing_engine": object,  # Движок сглаживания
            "_modifier_history": dict,   # История модификаторов
            "_intensity_history": dict,  # История интенсивностей
            "_smoothing_alpha": float,   # Коэффициент сглаживания
        })

    def validate(self, component: Any, context: Dict[str, Any] = None) -> List[ContractViolation]:
        """
        Выполняет комплексную валидацию IntensityAdapter.

        Args:
            component: Экземпляр IntensityAdapter для валидации
            context: Контекст валидации

        Returns:
            Список нарушений контракта
        """
        violations = []

        # Валидация структуры
        structure_violations = self._validate_structure(component)
        violations.extend(structure_violations)

        # Валидация параметров сглаживания
        smoothing_violations = self._validate_smoothing_parameters(component)
        violations.extend(smoothing_violations)

        # Валидация истории
        history_violations = self._validate_history(component)
        violations.extend(history_violations)

        # Функциональная валидация
        if context and "test_adaptation" in context:
            functional_violations = self._validate_functional_behavior(component, context)
            violations.extend(functional_violations)

        return violations

    def _validate_structure(self, component: Any) -> List[ContractViolation]:
        """Валидирует структуру компонента."""
        violations = []

        required_attributes = [
            "smoothing_engine", "_modifier_history", "_intensity_history", "_smoothing_alpha"
        ]

        for attr in required_attributes:
            if not hasattr(component, attr):
                violations.append(ContractViolation(
                    component="IntensityAdapter",
                    contract_name="IntensityAdapterContract",
                    violation_type="structure_error",
                    expected=f"has attribute '{attr}'",
                    actual="missing",
                    context={"attribute": attr}
                ))
            else:
                # Валидация типов
                value = getattr(component, attr)
                violation = self.type_contract.validate_field(attr, value)
                if violation:
                    violation.component = "IntensityAdapter"
                    violations.append(violation)

        return violations

    def _validate_smoothing_parameters(self, component: Any) -> List[ContractViolation]:
        """Валидирует параметры сглаживания."""
        violations = []

        if hasattr(component, '_smoothing_alpha'):
            alpha = component._smoothing_alpha
            if not (0.0 <= alpha <= 1.0):
                violations.append(ContractViolation(
                    component="IntensityAdapter",
                    contract_name="IntensityAdapterContract",
                    violation_type="range_violation",
                    expected="[0.0, 1.0]",
                    actual=alpha,
                    context={"field": "_smoothing_alpha"}
                ))

        return violations

    def _validate_history(self, component: Any) -> List[ContractViolation]:
        """Валидирует историю модификаторов и интенсивностей."""
        violations = []

        # Проверка размера истории
        if hasattr(component, '_modifier_history'):
            for event_type, history in component._modifier_history.items():
                if len(history) > 15:  # Максимум 15 значений в истории
                    violations.append(ContractViolation(
                        component="IntensityAdapter",
                        contract_name="IntensityAdapterContract",
                        violation_type="logic_error",
                        expected="<= 15",
                        actual=len(history),
                        context={"field": "_modifier_history", "event_type": event_type}
                    ))

        if hasattr(component, '_intensity_history'):
            for event_type, history in component._intensity_history.items():
                if len(history) > 25:  # Максимум 25 значений в истории
                    violations.append(ContractViolation(
                        component="IntensityAdapter",
                        contract_name="IntensityAdapterContract",
                        violation_type="logic_error",
                        expected="<= 25",
                        actual=len(history),
                        context={"field": "_intensity_history", "event_type": event_type}
                    ))

        return violations

    def _validate_functional_behavior(self, component: Any, context: Dict[str, Any]) -> List[ContractViolation]:
        """Валидирует функциональное поведение адаптера."""
        violations = []

        # Тест адаптации интенсивности
        test_cases = context.get("test_adaptation", [])

        for test_case in test_cases:
            try:
                event_type = test_case.get("event_type", "test_event")
                base_intensity = test_case.get("base_intensity", 0.5)
                context_state = test_case.get("context_state")

                result = component.adapt_intensity(event_type, base_intensity, context_state)

                # Проверка диапазона результата
                if not (0.0 <= result <= 3.0):
                    violations.append(ContractViolation(
                        component="IntensityAdapter",
                        contract_name="IntensityAdapterContract",
                        violation_type="functional_error",
                        expected="[0.0, 3.0]",
                        actual=result,
                        context={"test_case": test_case, "operation": "adapt_intensity"}
                    ))

                # Проверка монотонности (результат должен быть положительным)
                if result < 0:
                    violations.append(ContractViolation(
                        component="IntensityAdapter",
                        contract_name="IntensityAdapterContract",
                        violation_type="functional_error",
                        expected=">= 0",
                        actual=result,
                        context={"test_case": test_case, "operation": "adapt_intensity"}
                    ))

            except Exception as e:
                violations.append(ContractViolation(
                    component="IntensityAdapter",
                    contract_name="IntensityAdapterContract",
                    violation_type="functional_error",
                    expected="no exception",
                    actual=str(e),
                    context={"test_case": test_case, "operation": "adapt_intensity"}
                ))

        return violations

    def get_contract_name(self) -> str:
        """Возвращает имя контракта."""
        return "IntensityAdapterContract"

    def get_supported_components(self) -> List[str]:
        """Возвращает список поддерживаемых типов компонентов."""
        return ["IntensityAdapter"]


# Глобальный экземпляр контракта
intensity_adapter_contract = IntensityAdapterContract()
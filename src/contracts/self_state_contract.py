"""
Архитектурный контракт для SelfState компонента.

Определяет интерфейсы, диапазоны значений и гарантии для состояния системы Life.
"""

from typing import Any, Dict, List, Optional
from .base_contract import ContractValidator, ContractViolation, RangeContract, TypeContract


class SelfStateContract(ContractValidator):
    """
    Архитектурный контракт для SelfState.

    Гарантирует целостность состояния системы и соблюдение диапазонов значений.
    """

    def __init__(self):
        # Диапазоны значений для полей состояния
        self.range_contract = RangeContract({
            # Identity
            "age": (0.0, float('inf')),
            "ticks": (0, int(1e9)),  # Максимум 1 млрд тиков

            # Physical state
            "energy": (0.0, 100.0),
            "integrity": (0.0, 1.0),
            "stability": (0.0, 2.0),
            "fatigue": (0.0, 100.0),
            "tension": (0.0, 100.0),

            # Time state
            "subjective_time": (0.0, float('inf')),
            "base_rate": (0.1, 3.0),
            "rate_min": (0.01, 1.0),
            "rate_max": (1.0, 10.0),
            "intensity_coeff": (0.0, 5.0),
            "stability_coeff": (-2.0, 2.0),
            "energy_coeff": (-2.0, 2.0),
            "circadian_phase": (0.0, 6.283185307179586),  # 2π
            "circadian_period": (3600.0, 86400.0 * 7),  # 1 час - 1 неделя
            "circadian_adaptivity": (0.0, 1.0),
            "day_length_modifier": (0.5, 2.0),
            "recovery_efficiency": (0.4, 1.6),
            "stability_modifier": (0.7, 1.3),

            # Cognitive state
            "consciousness_level": (0.0, 1.0),

            # Events
            "last_significance": (0.0, 1.0),
        })

        # Типы данных для полей
        self.type_contract = TypeContract({
            # Identity
            "life_id": str,
            "birth_timestamp": float,
            "age": float,
            "ticks": int,
            "active": bool,

            # Physical
            "energy": float,
            "integrity": float,
            "stability": float,
            "fatigue": float,
            "tension": float,

            # Time
            "subjective_time": float,
            "base_rate": float,
            "circadian_phase": float,

            # Cognitive
            "consciousness_level": float,
            "clarity_type": (str, type(None)),

            # Events
            "recent_events": list,
            "last_significance": float,

            # Collections
            "planning": dict,
            "intelligence": dict,
            "parameter_history": list,
        })

    def validate(self, component: Any, context: Dict[str, Any] = None) -> List[ContractViolation]:
        """
        Выполняет комплексную валидацию SelfState.

        Args:
            component: Экземпляр SelfState для валидации
            context: Контекст валидации (опционально)

        Returns:
            Список нарушений контракта
        """
        violations = []

        # Валидация диапазонов значений
        range_violations = self._validate_ranges(component)
        violations.extend(range_violations)

        # Валидация типов данных
        type_violations = self._validate_types(component)
        violations.extend(type_violations)

        # Логическая валидация
        logic_violations = self._validate_logic(component)
        violations.extend(logic_violations)

        return violations

    def _validate_ranges(self, component: Any) -> List[ContractViolation]:
        """Валидирует диапазоны значений."""
        violations = []

        # Проверяем основные поля напрямую
        fields_to_check = [
            "age", "ticks", "energy", "integrity", "stability", "fatigue", "tension",
            "subjective_time", "consciousness_level", "last_significance"
        ]

        for field_name in fields_to_check:
            if hasattr(component, field_name):
                value = getattr(component, field_name)
                violation = self.range_contract.validate_field(field_name, value)
                if violation:
                    violation.component = "SelfState"
                    violations.append(violation)

        # Проверяем поля компонентов
        if hasattr(component, 'time'):
            time_fields = [
                "base_rate", "rate_min", "rate_max", "intensity_coeff",
                "stability_coeff", "energy_coeff", "circadian_phase",
                "circadian_period", "circadian_adaptivity", "day_length_modifier",
                "recovery_efficiency", "stability_modifier"
            ]
            for field_name in time_fields:
                if hasattr(component.time, field_name):
                    value = getattr(component.time, field_name)
                    violation = self.range_contract.validate_field(field_name, value)
                    if violation:
                        violation.component = "SelfState.TimeState"
                        violations.append(violation)

        return violations

    def _validate_types(self, component: Any) -> List[ContractViolation]:
        """Валидирует типы данных."""
        violations = []

        fields_to_check = [
            "life_id", "birth_timestamp", "age", "ticks", "active",
            "energy", "integrity", "stability", "fatigue", "tension",
            "subjective_time", "consciousness_level", "clarity_type",
            "recent_events", "last_significance", "planning", "intelligence", "parameter_history"
        ]

        for field_name in fields_to_check:
            if hasattr(component, field_name):
                value = getattr(component, field_name)
                violation = self.type_contract.validate_field(field_name, value)
                if violation:
                    violation.component = "SelfState"
                    violations.append(violation)

        return violations

    def _validate_logic(self, component: Any) -> List[ContractViolation]:
        """Валидирует логическую целостность состояния."""
        violations = []

        # Проверка монотонности времени
        if hasattr(component, 'time') and hasattr(component.time, 'subjective_time'):
            if component.time.subjective_time < 0:
                violations.append(ContractViolation(
                    component="SelfState.TimeState",
                    contract_name="SelfStateContract",
                    violation_type="logic_error",
                    expected=">= 0",
                    actual=component.time.subjective_time,
                    context={"field": "subjective_time", "reason": "subjective_time_must_be_non_negative"}
                ))

        # Проверка связей между компонентами
        if hasattr(component, 'physical'):
            # Энергия и усталость должны быть в допустимых соотношениях
            if component.physical.energy < 20.0 and component.physical.fatigue < 30.0:
                violations.append(ContractViolation(
                    component="SelfState.PhysicalState",
                    contract_name="SelfStateContract",
                    violation_type="logic_error",
                    expected="energy < 20 should imply fatigue >= 30",
                    actual=f"energy={component.physical.energy}, fatigue={component.physical.fatigue}",
                    context={"reason": "low_energy_should_cause_high_fatigue"}
                ))

        # Проверка синхронизации устаревших полей
        if hasattr(component, 'identity') and hasattr(component, 'life_id'):
            if component.life_id != component.identity.life_id:
                violations.append(ContractViolation(
                    component="SelfState",
                    contract_name="SelfStateContract",
                    violation_type="logic_error",
                    expected="synced with identity.life_id",
                    actual=component.life_id,
                    context={"reason": "legacy_field_not_synced", "expected_value": component.identity.life_id}
                ))

        return violations

    def get_contract_name(self) -> str:
        """Возвращает имя контракта."""
        return "SelfStateContract"

    def get_supported_components(self) -> List[str]:
        """Возвращает список поддерживаемых типов компонентов."""
        return ["SelfState"]


# Глобальный экземпляр контракта для удобства использования
self_state_contract = SelfStateContract()
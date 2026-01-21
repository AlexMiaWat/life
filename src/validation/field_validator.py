"""
Валидатор полей для SelfState.
Предоставляет централизованную валидацию полей с поддержкой clamping.
"""

from typing import Optional, Tuple


class FieldValidator:
    """
    Валидатор полей SelfState с поддержкой различных типов валидации.
    """

    # Определения границ для полей
    FIELD_BOUNDS = {
        "energy": (0.0, 100.0),
        "integrity": (0.0, 1.0),
        "stability": (0.0, 1.0),
        "last_event_intensity": (0.0, 1.0),
        "subjective_time_intensity_smoothing": (0.0, 1.0),
    }

    # Поля с нижней границей 0.0
    NON_NEGATIVE_FIELDS = [
        "fatigue",
        "tension",
        "age",
        "subjective_time",
        "subjective_time_base_rate",
        "subjective_time_rate_min",
        "subjective_time_rate_max",
    ]

    # Поля типа int
    INT_FIELDS = ["ticks", "clarity_duration"]

    @classmethod
    def validate_field(cls, field_name: str, value: float, clamp: bool = False) -> float:
        """
        Валидация значения поля с учетом его границ.

        Args:
            field_name: Имя поля
            value: Значение для валидации
            clamp: Если True, обрезать значение до границ вместо выбрасывания ошибки

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если значение вне границ и clamp=False
        """
        # Валидация int полей
        if field_name in cls.INT_FIELDS:
            if not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be a number, got {type(value)}")
            if value < 0:
                if clamp:
                    return 0
                raise ValueError(f"{field_name} must be >= 0, got {value}")
            return int(value)

        # Валидация float полей
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number, got {type(value)}")

        # Поля с заданными границами [min, max]
        if field_name in cls.FIELD_BOUNDS:
            min_val, max_val = cls.FIELD_BOUNDS[field_name]
            if clamp:
                return max(min_val, min(max_val, float(value)))
            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"{field_name} must be between {min_val} and {max_val}, got {value}"
                )
            return float(value)

        # Поля с нижней границей >= 0
        if field_name in cls.NON_NEGATIVE_FIELDS:
            if clamp:
                return max(0.0, float(value))
            if value < 0.0:
                raise ValueError(f"{field_name} must be >= 0.0, got {value}")
            return float(value)

        # Для неизвестных полей возвращаем значение как есть
        return float(value)

    @classmethod
    def get_field_bounds(cls, field_name: str) -> Optional[Tuple[float, float]]:
        """Получить границы поля, если они определены"""
        return cls.FIELD_BOUNDS.get(field_name)

    @classmethod
    def is_field_validatable(cls, field_name: str) -> bool:
        """Проверить, поддерживается ли валидация для поля"""
        return (
            field_name in cls.FIELD_BOUNDS
            or field_name in cls.NON_NEGATIVE_FIELDS
            or field_name in cls.INT_FIELDS
        )

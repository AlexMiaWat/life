"""
Архитектурные контракты для управления состоянием системы.
"""

from typing import Any, Dict, List, Optional, Protocol

from ..memory.memory import Memory


class StateValidationProtocol(Protocol):
    """
    Контракт для валидации состояния.

    Определяет интерфейс для компонентов, отвечающих за валидацию
    и логирование изменений состояния.
    """

    def validate_field(self, field_name: str, value: float, clamp: bool = False) -> float:
        """
        Валидировать значение поля.

        Args:
            field_name: Имя поля
            value: Значение для валидации
            clamp: Обрезать ли значение до границ

        Returns:
            Валидированное значение
        """
        ...

    def apply_delta(self, deltas: dict[str, float]) -> None:
        """
        Применить дельты к полям состояния.

        Args:
            deltas: Словарь дельт по полям
        """
        ...


class SubjectiveTimeManagerProtocol(Protocol):
    """
    Контракт для менеджера субъективного времени.

    Определяет интерфейс для компонентов, управляющих субъективным
    восприятием времени.
    """

    @property
    def subjective_age(self) -> float:
        """Текущий субъективный возраст."""
        ...

    @subjective_age.setter
    def subjective_age(self, value: float) -> None:
        """Установить субъективный возраст."""
        ...

    def calculate_subjective_time_modifier(self, event_type: str) -> float:
        """
        Рассчитать модификатор субъективного времени для типа события.

        Args:
            event_type: Тип события

        Returns:
            Модификатор субъективного времени
        """
        ...


class CircadianRhythmManagerProtocol(Protocol):
    """
    Контракт для менеджера циркадных ритмов.

    Определяет интерфейс для компонентов, управляющих циркадными ритмами.
    """

    def update_circadian_rhythm(self, dt: float) -> None:
        """
        Обновить циркадный ритм.

        Args:
            dt: Время в секундах с последнего обновления
        """
        ...

    def get_current_phase_name(self) -> str:
        """
        Получить название текущей фазы.

        Returns:
            Название фазы: "dawn", "day", "dusk", "night"
        """
        ...

    def get_circadian_status(self) -> Dict[str, Any]:
        """
        Получить статус циркадного ритма.

        Returns:
            Информация о циркадном ритме
        """
        ...


class SelfStateProtocol(Protocol):
    """
    Контракт для состояния системы Life.

    Определяет интерфейс для компонентов, представляющих полное
    состояние системы Life.
    """

    # Core properties
    life_id: str
    birth_timestamp: float
    age: float
    ticks: int
    energy: float
    integrity: float
    stability: float

    # Memory
    memory: Optional[Memory]

    # Managers (composition)
    subjective_time_manager: SubjectiveTimeManagerProtocol
    circadian_rhythm_manager: CircadianRhythmManagerProtocol
    validation_manager: StateValidationProtocol

    def is_active(self) -> bool:
        """
        Проверить активность системы.

        Returns:
            True если система активна
        """
        ...

    def is_viable(self) -> bool:
        """
        Проверить жизнеспособность системы.

        Returns:
            True если система жизнеспособна
        """
        ...

    def update_vital_params(
        self,
        energy: Optional[float] = None,
        integrity: Optional[float] = None,
        stability: Optional[float] = None,
    ) -> None:
        """
        Обновить жизненно важные параметры.

        Args:
            energy: Новое значение энергии
            integrity: Новое значение целостности
            stability: Новое значение стабильности
        """
        ...

    def get_safe_status_dict(
        self,
        include_optional: bool = True,
        limits: Optional[dict] = None,
    ) -> dict:
        """
        Получить безопасный словарь состояния.

        Args:
            include_optional: Включать ли опциональные поля
            limits: Лимиты для больших структур

        Returns:
            Словарь состояния
        """
        ...

    def apply_delta(self, deltas: dict[str, float]) -> None:
        """
        Применить дельты к состоянию.

        Args:
            deltas: Дельты по полям
        """
        ...
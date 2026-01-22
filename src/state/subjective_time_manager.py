"""
Subjective Time Manager - управление субъективным восприятием времени.

Отвечает за расчет и модуляцию субъективного времени на основе
состояния системы и внешних факторов.
"""

from typing import Optional

from .core_state import CoreState


class SubjectiveTimeManager:
    """
    Менеджер субъективного времени.

    Управляет расчетом субъективного времени, его модуляцией
    и связанными параметрами.
    """

    def __init__(self, core_state: CoreState):
        """
        Инициализация менеджера субъективного времени.

        Args:
            core_state: Ссылка на базовое состояние
        """
        self.core_state = core_state

    # Subjective time modulation parameters (defaults)
    subjective_time_base_rate: float = 1.0
    subjective_time_rate_min: float = 0.1
    subjective_time_rate_max: float = 3.0
    subjective_time_intensity_coeff: float = 1.0
    subjective_time_stability_coeff: float = 0.5
    subjective_time_energy_coeff: float = 0.5
    subjective_time_intensity_smoothing: float = 0.3
    time_ratio_history: list = []

    @property
    def subjective_age(self) -> float:
        """Alias for subjective_time"""
        return self.core_state.subjective_time

    @subjective_age.setter
    def subjective_age(self, value: float) -> None:
        """Set subjective_time via subjective_age alias"""
        self.core_state.subjective_time = value

    @property
    def physical_age(self) -> float:
        """Alias for age"""
        return self.core_state.age

    @physical_age.setter
    def physical_age(self, value: float) -> None:
        """Set age via physical_age alias"""
        self.core_state.age = value

    def calculate_subjective_time_modifier(self, event_type: str) -> float:
        """
        Вычисляет модификатор субъективного времени для типа события.

        Args:
            event_type: Тип события

        Returns:
            Модификатор субъективного времени (0.7-1.5)
        """
        # Получаем параметры субъективного времени
        base_rate = self.subjective_time_base_rate
        intensity_coeff = self.subjective_time_intensity_coeff
        stability_coeff = self.subjective_time_stability_coeff
        energy_coeff = self.subjective_time_energy_coeff

        # Вычисляем текущий коэффициент субъективного времени
        stability_factor = self.core_state.stability * stability_coeff
        energy_factor = (self.core_state.energy / 100.0) * energy_coeff
        intensity_factor = self.core_state.last_event_intensity * intensity_coeff

        # Комбинированный фактор субъективного времени
        subjective_factor = base_rate * (1.0 + stability_factor + energy_factor + intensity_factor)

        # Ограничиваем разумными пределами
        subjective_factor = max(0.1, min(3.0, subjective_factor))

        # Разные типы событий по-разному реагируют на субъективное время
        if event_type in ["shock", "fear", "confusion", "cognitive_confusion"]:
            # Хаотичные события усиливаются при замедленном субъективном времени
            return 1.0 + (1.0 - subjective_factor) * 0.3  # 0.7-1.3

        elif event_type in ["calm", "acceptance", "silence", "comfort"]:
            # Спокойные события усиливаются при ускоренном субъективном времени
            return 1.0 + (subjective_factor - 1.0) * 0.2  # 0.8-1.4

        elif event_type in ["inspiration", "insight", "meaning_found", "joy"]:
            # Значимые события усиливаются при оптимальном субъективном времени
            optimal_range = (0.8, 1.5)
            if optimal_range[0] <= subjective_factor <= optimal_range[1]:
                return 1.3
            elif subjective_factor < optimal_range[0]:
                return 0.9
            else:
                return 1.1

        else:
            # Большинство событий слабо реагируют на субъективное времени
            return 0.95 + subjective_factor * 0.05  # 0.95-1.15

    def update_time_ratio_history(self, physical_dt: float, subjective_dt: float) -> None:
        """
        Обновляет историю соотношений физического и субъективного времени.

        Args:
            physical_dt: Физическое время в секундах
            subjective_dt: Субъективное время в секундах
        """
        if physical_dt > 0:
            ratio = subjective_dt / physical_dt
            self.time_ratio_history.append(ratio)

            # Ограничиваем размер истории
            if len(self.time_ratio_history) > 100:
                self.time_ratio_history = self.time_ratio_history[-100:]

    def get_average_time_ratio(self, window: int = 10) -> float:
        """
        Возвращает среднее соотношение субъективного к физическому времени.

        Args:
            window: Размер окна для усреднения

        Returns:
            Среднее соотношение времени
        """
        if not self.time_ratio_history:
            return 1.0

        recent_ratios = self.time_ratio_history[-window:]
        return sum(recent_ratios) / len(recent_ratios)
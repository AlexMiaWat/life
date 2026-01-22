from dataclasses import dataclass, field
from typing import List, Dict, Any
from ...contracts.serialization_contract import Serializable


@dataclass
class TimeState(Serializable):
    """
    Компонент состояния, отвечающий за субъективное восприятие времени.

    Включает субъективное время, параметры модуляции и циркадный ритм.
    """

    # Основные параметры субъективного времени
    subjective_time: float = 0.0  # Текущее субъективное время (монотонно возрастающее)

    # Параметры модуляции субъективного времени
    base_rate: float = 1.0        # Базовая скорость течения времени
    rate_min: float = 0.1         # Минимальная скорость
    rate_max: float = 3.0         # Максимальная скорость
    intensity_coeff: float = 1.0  # Коэффициент влияния интенсивности
    stability_coeff: float = 0.5  # Коэффициент влияния стабильности
    energy_coeff: float = 0.5     # Коэффициент влияния энергии
    intensity_smoothing: float = 0.3  # Коэффициент сглаживания интенсивности

    # Циркадный ритм
    circadian_phase: float = 0.0      # Текущая фаза [0, 2π]
    circadian_period: float = 24.0 * 3600.0  # Базовый период в секундах
    circadian_adaptivity: float = 0.5       # Адаптивность ритма [0.0, 1.0]
    day_length_modifier: float = 1.0        # Модификатор длины дня [0.5, 2.0]
    recovery_efficiency: float = 1.0        # Эффективность восстановления [0.4, 1.6]
    stability_modifier: float = 1.0         # Модификатор стабильности [0.7, 1.3]

    # История для анализа
    time_ratio_history: List[float] = field(default_factory=list)

    # Дополнительные параметры времени
    last_event_intensity: float = 0.0  # Интенсивность последнего события

    def advance_subjective_time(self, physical_dt: float, intensity: float = 0.0,
                              stability: float = 1.0, energy: float = 100.0) -> float:
        """
        Продвигает субъективное время на основе физического времени и состояния системы.

        Args:
            physical_dt: Физическое время в секундах
            intensity: Интенсивность событий [0, 1]
            stability: Стабильность системы [0, 2]
            energy: Уровень энергии [0, 100]

        Returns:
            Прирост субъективного времени
        """
        # Расчет коэффициента скорости
        rate = self.base_rate
        rate += self.intensity_coeff * intensity
        rate += self.stability_coeff * (stability - 1.0)  # отрицательный при stability < 1
        rate += self.energy_coeff * (energy / 100.0)

        # Ограничение диапазона
        rate = max(self.rate_min, min(self.rate_max, rate))

        # Прирост субъективного времени
        subjective_dt = physical_dt * rate
        self.subjective_time += subjective_dt

        # Обновление истории
        time_ratio = rate
        self.time_ratio_history.append(time_ratio)
        if len(self.time_ratio_history) > 100:
            self.time_ratio_history.pop(0)

        return subjective_dt

    def update_circadian_rhythm(self, dt: float) -> None:
        """
        Обновляет циркадный ритм.

        Args:
            dt: Время в секундах
        """
        # Увеличение фазы
        phase_increment = (dt / self.circadian_period) * 2 * 3.14159
        self.circadian_phase += phase_increment
        self.circadian_phase %= (2 * 3.14159)

        # Обновление модификаторов на основе фазы
        import math
        self.recovery_efficiency = 0.4 + 0.6 * math.sin(self.circadian_phase + 3.14159/2)
        self.stability_modifier = 0.7 + 0.6 * math.sin(self.circadian_phase)

    def get_current_time_ratio(self) -> float:
        """Возвращает текущее отношение субъективного времени к физическому."""
        return self.base_rate

    def get_time_acceleration(self) -> float:
        """Возвращает коэффициент ускорения времени (>1 - ускорение, <1 - замедление)."""
        return self.base_rate

    def is_time_dilated(self) -> float:
        """Проверяет, замедлено ли время (возвращает коэффициент замедления)."""
        return max(0.0, 1.0 - self.base_rate)

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализует состояние времени.

        Returns:
            Dict[str, Any]: Словарь с параметрами времени
        """
        return {
            "subjective_time": self.subjective_time,
            "base_rate": self.base_rate,
            "rate_min": self.rate_min,
            "rate_max": self.rate_max,
            "intensity_coeff": self.intensity_coeff,
            "stability_coeff": self.stability_coeff,
            "energy_coeff": self.energy_coeff,
            "intensity_smoothing": self.intensity_smoothing,
            "circadian_phase": self.circadian_phase,
            "circadian_period": self.circadian_period,
            "circadian_adaptivity": self.circadian_adaptivity,
            "day_length_modifier": self.day_length_modifier,
            "recovery_efficiency": self.recovery_efficiency,
            "stability_modifier": self.stability_modifier,
            "time_ratio_history": self.time_ratio_history[-10:] if self.time_ratio_history else [],
            "current_time_ratio": self.get_current_time_ratio(),
            "time_acceleration": self.get_time_acceleration(),
            "is_time_dilated": self.is_time_dilated()
        }
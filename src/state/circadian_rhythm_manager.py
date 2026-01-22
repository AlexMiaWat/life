"""
Circadian Rhythm Manager - управление циркадными ритмами.

Отвечает за адаптивный циркадный ритм с 4 фазами: рассвет/день/закат/ночь.
"""

import math
from typing import Optional

from .core_state import CoreState


class CircadianRhythmManager:
    """
    Менеджер циркадных ритмов.

    Управляет адаптивным циркадным ритмом на основе состояния системы.
    """

    def __init__(self, core_state: CoreState):
        """
        Инициализация менеджера циркадных ритмов.

        Args:
            core_state: Ссылка на базовое состояние
        """
        self.core_state = core_state

    # Circadian rhythm parameters
    circadian_phase: float = 0.0  # Фаза циркадного ритма [0, 2π]
    circadian_period: float = 24.0 * 3600.0  # Базовый период в секундах (24 часа)
    circadian_adaptivity: float = 0.5  # Адаптивность циркадного ритма [0.0, 1.0]
    day_length_modifier: float = 1.0  # Модификатор длины дня [0.5, 2.0]
    recovery_efficiency: float = 1.0  # Эффективность восстановления [0.4, 1.6]
    stability_modifier: float = 1.0  # Модификатор стабильности [0.7, 1.3]

    def update_circadian_rhythm(self, dt: float) -> None:
        """
        Обновить адаптивный циркадный ритм с 4 фазами: рассвет/день/закат/ночь.

        Длина "дня" адаптируется на основе стабильности и энергии системы.
        При высокой стабильности и энергии - более короткие циклы (активность).
        При низкой стабильности и энергии - более длинные циклы (восстановление).

        4 фазы ритма:
        - Рассвет (0-π/2): постепенное увеличение активности
        - День (π/2-π): максимальная активность и эффективность восстановления
        - Закат (π-3π/2): постепенное снижение активности
        - Ночь (3π/2-2π): минимальная активность, максимальная стабильность

        Args:
            dt: Время в секундах, прошедшее с последнего обновления
        """
        # === Адаптивный расчет длины "дня" ===
        # Базовый период: 24 часа
        base_period = 24.0 * 3600.0

        # Модификатор на основе состояния системы
        # При высокой стабильности (>0.8) и энергии (>70) - укорачиваем цикл (активность)
        # При низкой стабильности (<0.3) или энергии (<30) - удлиняем цикл (восстановление)
        stability_factor = max(0.5, min(2.0, 1.0 / max(0.1, self.core_state.stability)))
        energy_factor = max(0.5, min(2.0, 100.0 / max(10.0, self.core_state.energy)))

        # Комбинированный фактор (среднее арифметическое)
        state_factor = (stability_factor + energy_factor) / 2.0

        # Адаптивный период с учетом circadian_adaptivity
        # При adaptivity=0: фиксированный период, при adaptivity=1: максимальная адаптация
        adaptive_period = base_period * (
            1.0 + self.circadian_adaptivity * (state_factor - 1.0)
        ) * self.day_length_modifier

        # Ограничиваем период разумными пределами: 6-72 часа
        adaptive_period = max(6*3600, min(72*3600, adaptive_period))

        # === Обновление фазы ритма ===
        phase_increment = (dt / adaptive_period) * 2 * math.pi
        self.circadian_phase += phase_increment
        self.circadian_phase %= 2 * math.pi  # Нормализация в диапазон [0, 2π]

        # === Расчет коэффициентов для 4 фаз ===
        phase_rad = self.circadian_phase

        # Определяем текущую фазу
        if phase_rad < math.pi / 2:
            # Фаза 1: Рассвет (0-π/2) - постепенное увеличение активности
            phase_progress = phase_rad / (math.pi / 2)  # [0, 1]
            recovery_coeff = 0.5 + 0.3 * phase_progress  # [0.5, 0.8]
            stability_coeff = 0.8 + 0.1 * phase_progress  # [0.8, 0.9]
        elif phase_rad < math.pi:
            # Фаза 2: День (π/2-π) - максимальная активность
            phase_progress = (phase_rad - math.pi/2) / (math.pi / 2)  # [0, 1]
            recovery_coeff = 0.8 + 0.2 * phase_progress  # [0.8, 1.0]
            stability_coeff = 0.9 - 0.1 * phase_progress  # [0.9, 0.8]
        elif phase_rad < 3 * math.pi / 2:
            # Фаза 3: Закат (π-3π/2) - постепенное снижение активности
            phase_progress = (phase_rad - math.pi) / (math.pi / 2)  # [0, 1]
            recovery_coeff = 1.0 - 0.3 * phase_progress  # [1.0, 0.7]
            stability_coeff = 0.8 + 0.1 * phase_progress  # [0.8, 0.9]
        else:
            # Фаза 4: Ночь (3π/2-2π) - восстановление и стабилизация
            phase_progress = (phase_rad - 3*math.pi/2) / (math.pi / 2)  # [0, 1]
            recovery_coeff = 0.7 - 0.3 * phase_progress  # [0.7, 0.4]
            stability_coeff = 0.9 + 0.1 * phase_progress  # [0.9, 1.0]

        # Применяем коэффициенты с учетом состояния системы
        self.recovery_efficiency = max(0.4, min(1.6, recovery_coeff))
        self.stability_modifier = max(0.7, min(1.3, stability_coeff))

    def get_current_phase_name(self) -> str:
        """
        Возвращает название текущей фазы циркадного ритма.

        Returns:
            Название фазы: "dawn", "day", "dusk", "night"
        """
        phase_rad = self.circadian_phase

        if phase_rad < math.pi / 2:
            return "dawn"  # Рассвет
        elif phase_rad < math.pi:
            return "day"   # День
        elif phase_rad < 3 * math.pi / 2:
            return "dusk"  # Закат
        else:
            return "night" # Ночь

    def get_phase_progress(self) -> float:
        """
        Возвращает прогресс текущей фазы (0.0 - 1.0).

        Returns:
            Прогресс фазы от 0.0 до 1.0
        """
        phase_rad = self.circadian_phase

        if phase_rad < math.pi / 2:
            return phase_rad / (math.pi / 2)
        elif phase_rad < math.pi:
            return (phase_rad - math.pi/2) / (math.pi / 2)
        elif phase_rad < 3 * math.pi / 2:
            return (phase_rad - math.pi) / (math.pi / 2)
        else:
            return (phase_rad - 3*math.pi/2) / (math.pi / 2)

    def get_circadian_status(self) -> dict:
        """
        Возвращает полную информацию о состоянии циркадного ритма.

        Returns:
            Словарь с информацией о циркадном ритме
        """
        return {
            "phase": self.circadian_phase,
            "phase_name": self.get_current_phase_name(),
            "phase_progress": self.get_phase_progress(),
            "recovery_efficiency": self.recovery_efficiency,
            "stability_modifier": self.stability_modifier,
            "adaptivity": self.circadian_adaptivity,
            "day_length_modifier": self.day_length_modifier,
        }
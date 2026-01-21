import time

from src.memory.memory import MemoryEntry


def execute_action(pattern: str, self_state):
    """
    Execute action based on pattern.
    Minimal implementation: record action in memory and apply minor state update if applicable.

    ИНТЕГРАЦИЯ: Использует learning_params.response_coefficients и adaptation_params.behavior_coefficients
    для модификации эффектов действий.
    """
    # Record action in memory
    action_entry = MemoryEntry(
        event_type="action",
        meaning_significance=0.0,
        timestamp=time.time(),
        subjective_timestamp=self_state.subjective_time,
    )
    self_state.memory.append(action_entry)

    # ИНТЕГРАЦИЯ: Используем параметры для модификации эффектов действий
    learning_params = getattr(self_state, "learning_params", {})
    response_coefficients = learning_params.get("response_coefficients", {})
    adaptation_params = getattr(self_state, "adaptation_params", {})
    behavior_coefficients = adaptation_params.get("behavior_coefficients", {})

    # Получаем коэффициент для паттерна (приоритет adaptation_params)
    coefficient = behavior_coefficients.get(pattern, response_coefficients.get(pattern, 1.0))

    # Циркадная модификация интенсивности действий
    import math
    circadian_phase_rad = self_state.circadian_phase
    if circadian_phase_rad < math.pi / 2:
        circadian_intensity = 0.7  # Рассвет: пониженная интенсивность
    elif circadian_phase_rad < math.pi:
        circadian_intensity = 1.3  # День: повышенная интенсивность
    elif circadian_phase_rad < 3 * math.pi / 2:
        circadian_intensity = 0.9  # Закат: умеренная интенсивность
    else:
        circadian_intensity = 0.6  # Ночь: минимальная интенсивность

    # Модификация интенсивности на основе субъективного времени
    time_ratio = self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
    time_intensity_modifier = 1.0
    if time_ratio > 1.1:  # Ускоренное восприятие времени
        time_intensity_modifier = 1.2  # Более интенсивные действия
    elif time_ratio < 0.9:  # Замедленное восприятие времени
        time_intensity_modifier = 0.8  # Более мягкие действия

    # Комбинированный коэффициент действия
    action_coefficient = coefficient * circadian_intensity * time_intensity_modifier

    # Minimal state update for dampen
    if pattern == "dampen":
        # Minor fatigue effect (assuming energy represents vitality)
        # Модифицируем эффект на основе базового коэффициента (без модификаторов)
        fatigue_effect = 0.01 * (1.0 - coefficient)  # Чем выше коэффициент, тем меньше усталость
        new_energy = max(0.0, self_state.energy - fatigue_effect)
        self_state.update_energy(new_energy)

    # Для absorb: если базовый коэффициент низкий, может быть небольшой эффект усталости
    elif pattern == "absorb":
        # Небольшой эффект усталости, если коэффициент низкий
        if coefficient < 0.8:
            fatigue_effect = 0.005 * (1.0 - coefficient)
            new_energy = max(0.0, self_state.energy - fatigue_effect)
            self_state.update_energy(new_energy)

    # For ignore, no additional state changes
    # Для amplify: небольшой положительный эффект энергии при высокой циркадной интенсивности
    elif pattern == "amplify":
        if action_coefficient > 1.2:
            energy_boost = 0.005 * (action_coefficient - 1.0)
            new_energy = min(100.0, self_state.energy + energy_boost)
            self_state.update_energy(new_energy)

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
        event_type="action", meaning_significance=0.0, timestamp=time.time()
    )
    self_state.memory.append(action_entry)

    # ИНТЕГРАЦИЯ: Используем параметры для модификации эффектов действий
    learning_params = getattr(self_state, "learning_params", {})
    response_coefficients = learning_params.get("response_coefficients", {})
    adaptation_params = getattr(self_state, "adaptation_params", {})
    behavior_coefficients = adaptation_params.get("behavior_coefficients", {})

    # Получаем коэффициент для паттерна (приоритет adaptation_params)
    coefficient = behavior_coefficients.get(
        pattern, response_coefficients.get(pattern, 1.0)
    )

    # Minimal state update for dampen
    if pattern == "dampen":
        # Minor fatigue effect (assuming energy represents vitality)
        # Модифицируем эффект на основе коэффициента
        fatigue_effect = 0.01 * (
            1.0 - coefficient
        )  # Чем выше коэффициент, тем меньше усталость
        new_energy = max(0.0, self_state.energy - fatigue_effect)
        self_state.update_energy(new_energy)

    # Для absorb: если коэффициент низкий, может быть небольшой эффект усталости
    elif pattern == "absorb":
        # Небольшой эффект усталости, если коэффициент низкий
        if coefficient < 0.8:
            fatigue_effect = 0.005 * (1.0 - coefficient)
            new_energy = max(0.0, self_state.energy - fatigue_effect)
            self_state.update_energy(new_energy)

    # For ignore, no additional state changes

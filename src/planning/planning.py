from typing import List

from src.state.self_state import SelfState


def record_potential_sequences(self_state: SelfState) -> None:
    """
    Минимальная нейтральная фиксация потенциальных последовательностей.

    Использует данные из self_state как proxy для memory_data, learning_statistics, adaptation_parameters.

    Не оценивает, не выбирает, не влияет на другие слои.

    ИНТЕГРАЦИЯ: Модифицирует параметры фиксации последовательностей на основе восприятия времени.
    При ускоренном восприятии времени фиксирует более длинные последовательности,
    при замедленном - более короткие.
    """
    # Получаем нейтральные источники
    recent_events = self_state.recent_events
    energy_history = self_state.energy_history
    stability_history = self_state.stability_history

    # Расчет метрик восприятия времени
    time_ratio = self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
    time_perception = (
        "accelerated" if time_ratio >= 1.1 else "normal" if time_ratio > 0.9 else "slowed"
    )

    # Циркадные метрики для планирования
    import math
    circadian_phase_rad = self_state.circadian_phase
    if circadian_phase_rad < math.pi / 2:
        circadian_phase = "dawn"
        planning_horizon = 0.7  # Короткий горизонт планирования
    elif circadian_phase_rad < math.pi:
        circadian_phase = "day"
        planning_horizon = 1.5  # Длинный горизонт планирования
    elif circadian_phase_rad < 3 * math.pi / 2:
        circadian_phase = "dusk"
        planning_horizon = 1.0  # Средний горизонт планирования
    else:
        circadian_phase = "night"
        planning_horizon = 0.5  # Минимальный горизонт планирования

    # Модификация параметров фиксации на основе восприятия времени и циркадных ритмов
    base_min_length = 2
    base_max_sequences = 1

    # Корректировка на основе восприятия времени с учетом моментов ясности
    time_modifier = 1.0
    clarity_modifier = 1.0

    # Проверяем, активен ли момент ясности
    clarity_active = getattr(self_state, 'clarity_moment_active', False)
    if clarity_active:
        clarity_modifier = 1.3  # Моменты ясности расширяют горизонты планирования

    # Более плавная корректировка на основе конкретного значения time_ratio
    if time_ratio > 1.2:
        time_modifier = 1.6 * clarity_modifier  # Значительно ускоренное восприятие
    elif time_ratio > 1.1:
        time_modifier = 1.3 * clarity_modifier  # Умеренно ускоренное восприятие
    elif time_ratio < 0.8:
        time_modifier = 0.5 * clarity_modifier  # Значительно замедленное восприятие
    elif time_ratio < 0.9:
        time_modifier = 0.8 * clarity_modifier  # Умеренно замедленное восприятие

    # Финальные параметры с учетом циркадного горизонта
    min_sequence_length = max(1, int(base_min_length * time_modifier * planning_horizon))
    max_sequences = max(1, int(base_max_sequences * time_modifier * planning_horizon))

    # Фиксация последовательностей с модифицированными параметрами
    potential_sequences: List[List[str]] = []

    if len(recent_events) >= min_sequence_length:
        # Создаем последовательности разной длины
        for length in range(min_sequence_length, len(recent_events) + 1):
            if len(potential_sequences) >= max_sequences:
                break
            potential_sequences.append(recent_events[-length:])

    # Записываем в self_state без изменений других полей
    self_state.planning = {
        "potential_sequences": potential_sequences,
        "sources_used": {
            "memory_proxy": len(recent_events),
            "learning_proxy": len(stability_history),
            "adaptation_proxy": len(energy_history),
        },
        "circadian_phase": circadian_phase,
        "planning_horizon": planning_horizon,
        "time_perception": time_perception,
        "clarity_influenced": clarity_active,
        "subjective_time_integration": {
            "time_ratio": time_ratio,
            "time_modifier": time_modifier,
            "clarity_modifier": clarity_modifier,
        },
        "parameters": {
            "min_sequence_length": min_sequence_length,
            "max_sequences": max_sequences,
        },
    }

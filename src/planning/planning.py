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
    time_perception = "accelerated" if time_ratio >= 1.1 else "normal" if time_ratio > 0.9 else "slowed"

    # Модификация параметров фиксации на основе восприятия времени
    if time_perception == "accelerated":
        # При ускоренном восприятии - более длинные последовательности, больше вариантов
        min_sequence_length = 3
        max_sequences = 2
    elif time_perception == "slowed":
        # При замедленном восприятии - более короткие последовательности, меньше вариантов
        min_sequence_length = 2
        max_sequences = 1
    else:
        # Нормальное восприятие - стандартные параметры
        min_sequence_length = 2
        max_sequences = 1

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
    }

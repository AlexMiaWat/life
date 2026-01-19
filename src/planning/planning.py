from typing import List

from state.self_state import SelfState


def record_potential_sequences(self_state: SelfState) -> None:
    """
    Минимальная нейтральная фиксация потенциальных последовательностей.

    Использует данные из self_state как proxy для memory_data, learning_statistics, adaptation_parameters.

    Не оценивает, не выбирает, не влияет на другие слои.
    """
    # Получаем нейтральные источники
    recent_events = self_state.recent_events
    energy_history = self_state.energy_history
    stability_history = self_state.stability_history

    # Фиксируем простую potential sequence на основе последних событий
    potential_sequences: List[List[str]] = []

    if len(recent_events) >= 2:
        potential_sequences.append(recent_events[-2:])

    # Записываем в self_state без изменений других полей
    self_state.planning = {
        "potential_sequences": potential_sequences,
        "sources_used": {
            "memory_proxy": len(recent_events),
            "learning_proxy": len(stability_history),
            "adaptation_proxy": len(energy_history),
        },
    }

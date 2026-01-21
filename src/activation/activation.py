from typing import List, Optional

from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState


def activate_memory(
    current_event_type: str,
    memory: List[MemoryEntry],
    limit: Optional[int] = None,
    self_state: Optional[SelfState] = None
) -> List[MemoryEntry]:
    """
    Минимальная активация: возвращает топ-N воспоминаний с совпадающим event_type,
    отсортированных по significance (desc).
    Если нет совпадений — пустой список.

    ИНТЕГРАЦИЯ: Использует субъективное время для динамического расчета лимита активации.
    При ускоренном восприятии времени активирует больше воспоминаний,
    при замедленном - меньше.
    """
    matching = [entry for entry in memory if entry.event_type == current_event_type]
    matching.sort(key=lambda e: e.meaning_significance, reverse=True)

    # Расчет лимита активации с учетом субъективного времени
    if limit is None and self_state is not None:
        # Динамический расчет лимита на основе субъективного времени
        time_ratio = (
            self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
        )

        if time_ratio >= 1.1:
            # Ускоренное восприятие времени - активировать больше воспоминаний (система внимательнее)
            activation_limit = min(5, len(matching))
        elif time_ratio <= 0.9:
            # Замедленное восприятие времени - активировать меньше воспоминаний (система рассеяннее)
            activation_limit = min(2, len(matching))
        else:
            # Нормальное восприятие времени - стандартный лимит
            activation_limit = min(3, len(matching))
    else:
        # Использовать переданный лимит или значение по умолчанию
        activation_limit = limit if limit is not None else min(3, len(matching))

    return matching[:activation_limit]

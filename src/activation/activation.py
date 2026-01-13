from typing import List
from memory.memory import MemoryEntry

def activate_memory(current_event_type: str, memory: List[MemoryEntry], limit: int = 3) -> List[MemoryEntry]:
    """
    Минимальная активация: возвращает топ-N воспоминаний с совпадающим event_type,
    отсортированных по significance (desc).
    Если нет совпадений — пустой список.
    """
    matching = [entry for entry in memory if entry.event_type == current_event_type]
    matching.sort(key=lambda e: e.meaning_significance, reverse=True)
    return matching[:limit]
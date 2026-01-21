"""
Общие типы для модуля памяти.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MemoryEntry:
    event_type: str
    meaning_significance: float
    timestamp: float
    weight: float = 1.0  # Вес записи для механизма забывания
    feedback_data: Optional[Dict] = None  # Для Feedback записей (сериализованный FeedbackRecord)
    subjective_timestamp: Optional[float] = None  # Субъективное время в момент создания записи

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MemoryEntry:
    event_type: str
    meaning_significance: float
    timestamp: float
    feedback_data: Optional[
        Dict
    ] = None  # Для Feedback записей (сериализованный FeedbackRecord)


class Memory(list):
    def append(self, item):
        super().append(item)
        self.clamp_size()

    def clamp_size(self):
        while len(self) > 50:
            self.pop(0)

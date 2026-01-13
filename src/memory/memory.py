from dataclasses import dataclass
import time


@dataclass
class MemoryEntry:
    event_type: str
    meaning_significance: float
    timestamp: float


class Memory(list):
    def append(self, item):
        super().append(item)
        self.clamp_size()

    def clamp_size(self):
        while len(self) > 50:
            self.pop(0)
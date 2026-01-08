import queue
from .event import Event

class EventQueue:
    def __init__(self):
        self._queue = queue.Queue(maxsize=100)

    def push(self, event: Event) -> None:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            pass  # silently drop if full

    def pop(self) -> Event | None:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def is_empty(self) -> bool:
        return self._queue.empty()

    def size(self) -> int:
        return self._queue.qsize()
    
    def pop_all(self) -> list[Event]:
        """
        Извлечь все события из очереди.
        
        Returns:
            list[Event]: список всех событий из очереди (FIFO порядок)
        """
        events = []
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                events.append(event)
            except queue.Empty:
                break
        return events
import logging
import queue

from .event import Event

logger = logging.getLogger(__name__)


class EventQueue:
    def __init__(self):
        self._queue = queue.Queue(maxsize=100)
        self._dropped_events_count = 0  # Счетчик потерянных событий

    def push(self, event: Event) -> None:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            # Логируем потерю события вместо молчаливого игнорирования
            self._dropped_events_count += 1
            logger.warning(
                f"EventQueue переполнена, событие потеряно (тип: {event.type}, "
                f"интенсивность: {event.intensity}). Всего потеряно: {self._dropped_events_count}"
            )

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
        Извлечь все события из очереди атомарно.

        Исправляет race condition: вместо проверки empty() + get_nowait()
        используем цикл с обработкой исключения Empty, что устраняет
        проблему между проверкой и извлечением.

        Returns:
            list[Event]: список всех событий из очереди (FIFO порядок)
        """
        events = []
        # Используем цикл с обработкой Empty вместо проверки empty()
        # Это устраняет race condition между проверкой и извлечением
        while True:
            try:
                event = self._queue.get_nowait()
                events.append(event)
            except queue.Empty:
                # Очередь пуста, выходим из цикла
                break
        return events
    
    def get_dropped_events_count(self) -> int:
        """
        Получить количество потерянных событий.
        
        Returns:
            int: количество событий, потерянных из-за переполнения очереди
        """
        return self._dropped_events_count
    
    def reset_dropped_events_count(self) -> None:
        """Сбросить счетчик потерянных событий."""
        self._dropped_events_count = 0

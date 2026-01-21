import logging
import queue
from typing import Optional, Dict, Any

from .event import Event
from .silence_detector import SilenceDetector

logger = logging.getLogger(__name__)


class EventQueue:
    def __init__(self, enable_silence_detection: bool = True):
        self._queue = queue.Queue(maxsize=100)
        self._dropped_events_count = 0  # Счетчик потерянных событий

        # Система осознания тишины
        self.silence_detector = SilenceDetector() if enable_silence_detection else None

    def push(self, event: Event) -> None:
        try:
            self._queue.put_nowait(event)

            # Уведомляем детектор тишины о новом событии
            if self.silence_detector is not None:
                self.silence_detector.update_last_event_time(event.timestamp)

        except queue.Full:
            # Логируем потерю события вместо молчаливого игнорирования
            self._dropped_events_count += 1
            logger.warning(
                f"EventQueue full, event dropped (type: {event.type}, count: {self._dropped_events_count})"
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

        # Если извлекли события, уведомляем детектор тишины
        if events and self.silence_detector is not None:
            # Используем время последнего извлеченного события
            last_event_time = max(event.timestamp for event in events)
            self.silence_detector.update_last_event_time(last_event_time)

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

    def check_and_generate_silence(self) -> Optional[Event]:
        """
        Проверить состояние тишины и сгенерировать событие silence если нужно.

        Returns:
            Event типа 'silence' если период тишины достиг порога, None иначе
        """
        if self.silence_detector is None:
            return None

        return self.silence_detector.check_silence_period()

    def get_silence_status(self) -> Dict[str, Any]:
        """
        Получить статус системы осознания тишины.

        Returns:
            Dict со статусом silence detector
        """
        if self.silence_detector is None:
            return {"silence_detection_enabled": False}

        status = self.silence_detector.get_silence_status()
        status["silence_detection_enabled"] = True
        return status

    def is_silence_detection_enabled(self) -> bool:
        """
        Проверить, включена ли система осознания тишины.

        Returns:
            True если silence detection активна
        """
        return self.silence_detector is not None

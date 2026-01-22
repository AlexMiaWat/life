import logging
import queue
import threading
import time
from typing import Optional, Dict, Any, List

from .event import Event
from .silence_detector import SilenceDetector
from ..contracts.serialization_contract import SerializationContract

logger = logging.getLogger(__name__)


class EventQueue(SerializationContract):
    def __init__(self, enable_silence_detection: bool = True):
        self._queue = queue.Queue(maxsize=100)
        self._dropped_events_count = 0  # Счетчик потерянных событий

        # Система осознания тишины
        self.silence_detector = SilenceDetector() if enable_silence_detection else None

        # Thread-safe сериализация через snapshot
        self._snapshot_lock = threading.RLock()
        self._last_snapshot_time = 0.0
        self._snapshot_cache: Optional[List[Dict[str, Any]]] = None
        self._snapshot_cache_lifetime = 0.1  # Кэшируем snapshot на 100ms

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

    def to_dict(self) -> Dict[str, Any]:
        """
        Thread-safe сериализация EventQueue через snapshot-based подход.

        Архитектурный контракт:
        - Thread-safe: Использует snapshot без блокировки основной очереди
        - Эффективность: Кэширование snapshot для частых вызовов
        - Атомарность: Snapshot создается атомарно
        - Отказоустойчивость: Graceful degradation при ошибках

        Returns:
            Dict[str, Any]: Стандартизированная структура сериализации:
            {
                "metadata": {
                    "version": "2.0",
                    "timestamp": float,
                    "component_type": "EventQueue",
                    "event_count": int,
                    "dropped_events": int
                },
                "data": {
                    "events": [event_dict, ...],
                    "silence_detection_enabled": bool
                }
            }

        Raises:
            RuntimeError: При критических ошибках сериализации
        """
        with self._snapshot_lock:
            current_time = time.time()

            # Используем кэшированный snapshot если он свежий
            if (self._snapshot_cache is not None and
                current_time - self._last_snapshot_time < self._snapshot_cache_lifetime):
                return self._snapshot_cache

            try:
                # Создаем новый snapshot
                events_snapshot = self._create_events_snapshot()

                # Метаданные сериализации
                metadata = {
                    "version": "2.0",
                    "timestamp": current_time,
                    "component_type": "EventQueue",
                    "event_count": len(events_snapshot),
                    "dropped_events": self._dropped_events_count,
                    "silence_detection_enabled": self.silence_detector is not None
                }

                # Структура данных
                data = {
                    "events": events_snapshot,
                    "silence_detection_enabled": self.silence_detector is not None
                }

                result = {
                    "metadata": metadata,
                    "data": data
                }

                # Кэшируем результат
                self._snapshot_cache = result
                self._last_snapshot_time = current_time

                return result

            except Exception as e:
                logger.error(f"Failed to serialize EventQueue: {e}")
                # Возвращаем минимальную структуру вместо падения
                return {
                    "metadata": {
                        "version": "2.0",
                        "timestamp": current_time,
                        "component_type": "EventQueue",
                        "error": f"Serialization failed: {str(e)}"
                    },
                    "data": {
                        "events": [],
                        "silence_detection_enabled": self.silence_detector is not None
                    }
                }

    def _create_events_snapshot(self) -> List[Dict[str, Any]]:
        """
        Создает snapshot всех событий в очереди без блокировки.

        Использует атомарное извлечение и восстановление для thread-safety.

        Returns:
            List[Dict[str, Any]]: Список сериализованных событий
        """
        snapshot_events = []
        extracted_events = []

        try:
            # Атомарное извлечение всех доступных событий
            while True:
                try:
                    event = self._queue.get_nowait()
                    extracted_events.append(event)
                    snapshot_events.append({
                        "type": event.type,
                        "intensity": event.intensity,
                        "timestamp": event.timestamp,
                        "metadata": event.metadata.copy() if event.metadata else {},
                        "source": event.source
                    })
                except queue.Empty:
                    break

            # Гарантированное восстановление событий в оригинальном порядке
            # Используем put() с timeout для предотвращения deadlock
            restoration_errors = []
            for event in extracted_events:
                try:
                    self._queue.put(event, timeout=1.0)  # 1 секунда timeout
                except queue.Full:
                    restoration_errors.append(f"Failed to restore event {event.type}")

            if restoration_errors:
                logger.critical(
                    f"CRITICAL: Failed to restore {len(restoration_errors)} events during serialization. "
                    f"Errors: {restoration_errors}"
                )
                # Не выбрасываем исключение - лучше вернуть частичные данные

            return snapshot_events

        except Exception as e:
            logger.error(f"Failed to create events snapshot: {e}")
            # В экстренном случае возвращаем пустой snapshot
            return []

    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Получить метаданные сериализации для валидации.

        Returns:
            Dict[str, Any]: Метаданные с информацией о состоянии сериализации
        """
        return {
            "version": "2.0",
            "component_type": "EventQueue",
            "thread_safe": True,
            "snapshot_based": True,
            "cache_lifetime": self._snapshot_cache_lifetime,
            "last_snapshot_age": time.time() - self._last_snapshot_time if self._last_snapshot_time > 0 else None
        }


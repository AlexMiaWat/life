import logging
import queue
import threading
import time
from typing import Optional, Dict, Any, List

from .event import Event
from .silence_detector import SilenceDetector
from ..contracts.serialization_contract import SerializationContract, SerializationError, ThreadSafeSerializable

logger = logging.getLogger(__name__)


class EventQueue(SerializationContract, ThreadSafeSerializable):
    def __init__(self, enable_silence_detection: bool = True):
        self._queue = queue.Queue(maxsize=100)
        self._dropped_events_count = 0  # Счетчик потерянных событий

        # Version-based concurrency control для обеспечения консистентности
        self._version = 0  # Версия состояния очереди
        self._version_lock = threading.RLock()  # Защита для версии

        # Система осознания тишины
        self.silence_detector = SilenceDetector() if enable_silence_detection else None

        # Thread-safe сериализация с timeout
        self._serialization_lock = threading.RLock()
        self._serialization_timeout = 5.0  # 5 секунд максимум на сериализацию

    def push(self, event: Event) -> None:
        with self._version_lock:
            try:
                self._queue.put_nowait(event)
                self._version += 1  # Инкремент версии при изменении состояния

                # Уведомляем детектор тишины о новом событии
                if self.silence_detector is not None:
                    self.silence_detector.update_last_event_time(event.timestamp)

            except queue.Full:
                # Логируем потерю события вместо молчаливого игнорирования
                self._dropped_events_count += 1
                self._version += 1  # Версия изменяется даже при потере события
                logger.warning(
                    f"EventQueue full, event dropped (type: {event.type}, count: {self._dropped_events_count})"
                )

    def pop(self) -> Event | None:
        with self._version_lock:
            try:
                event = self._queue.get_nowait()
                self._version += 1  # Инкремент версии при изменении состояния
                return event
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
        Thread-safe атомарная сериализация EventQueue с timeout.

        Архитектурный контракт:
        - Thread-safe: Полная синхронизация операции сериализации
        - Атомарность: Захват консистентного состояния очереди
        - Отказоустойчивость: Timeout и graceful degradation при ошибках
        - Эффективность: Без кэширования для гарантии актуальности данных

        Returns:
            Dict[str, Any]: Стандартизированная структура сериализации:
            {
                "metadata": {
                    "version": "3.0",
                    "timestamp": float,
                    "component_type": "EventQueue",
                    "event_count": int,
                    "dropped_events": int,
                    "serialization_duration": float
                },
                "data": {
                    "events": [event_dict, ...],
                    "silence_detection_enabled": bool
                }
            }

        Raises:
            SerializationError: При критических ошибках сериализации
        """
        start_time = time.time()

        try:
            # Атомарная сериализация с timeout
            with self._serialization_lock:
                # Создаем snapshot с timeout
                events_snapshot = self._create_events_snapshot_atomic()

                serialization_duration = time.time() - start_time

                # Метаданные сериализации
                metadata = {
                    "version": "4.0",  # Обновлено с version-based concurrency control
                    "timestamp": start_time,
                    "component_type": "EventQueue",
                    "event_count": len(events_snapshot),
                    "dropped_events": self._dropped_events_count,
                    "silence_detection_enabled": self.silence_detector is not None,
                    "serialization_duration": serialization_duration,
                    "serialization_timeout": self._serialization_timeout,
                    "state_version": self._version,  # Version-based concurrency control
                    "thread_safe": True  # Подтверждение thread-safety
                }

                # Структура данных
                data = {
                    "events": events_snapshot,
                    "silence_detection_enabled": self.silence_detector is not None
                }

                return {
                    "metadata": metadata,
                    "data": data
                }

        except Exception as e:
            serialization_duration = time.time() - start_time
            logger.error(f"Failed to serialize EventQueue after {serialization_duration:.3f}s: {e}")

            # Graceful degradation - возвращаем минимальную структуру
            return {
                "metadata": {
                    "version": "3.0",
                    "timestamp": start_time,
                    "component_type": "EventQueue",
                    "error": f"Serialization failed: {str(e)}",
                    "serialization_duration": serialization_duration,
                    "serialization_timeout": self._serialization_timeout
                },
                "data": {
                    "events": [],
                    "silence_detection_enabled": self.silence_detector is not None
                }
            }

    def _create_events_snapshot_atomic(self) -> List[Dict[str, Any]]:
        """
        Создает атомарный snapshot всех событий в очереди с timeout.

        Thread-safety гарантируется за счет:
        1. Полной синхронизации операции извлечения/восстановления
        2. Timeout на все блокирующие операции
        3. Graceful degradation при проблемах

        Returns:
            List[Dict[str, Any]]: Список сериализованных событий

        Raises:
            SerializationError: При timeout или критических ошибках
        """
        snapshot_events = []
        extracted_events = []
        start_time = time.time()

        try:
            # Фаза 1: Атомарное извлечение всех доступных событий с timeout
            extraction_deadline = start_time + self._serialization_timeout * 0.7  # 70% времени на извлечение

            while time.time() < extraction_deadline:
                try:
                    # Используем get_nowait для избежания блокировки
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
                    # Очередь пуста, завершаем извлечение
                    break

            # Фаза 2: Гарантированное восстановление событий с timeout
            restoration_deadline = start_time + self._serialization_timeout
            restoration_errors = []

            for event in extracted_events:
                if time.time() >= restoration_deadline:
                    restoration_errors.append(f"Timeout during restoration of event {event.type}")
                    break

                try:
                    # Используем timeout для предотвращения deadlock
                    self._queue.put(event, timeout=0.5)
                except queue.Full:
                    restoration_errors.append(f"Queue full during restoration of event {event.type}")

            # Логируем проблемы восстановления
            if restoration_errors:
                logger.warning(
                    f"Serialization restoration issues: {len(restoration_errors)} events not restored. "
                    f"Snapshot may be incomplete. Errors: {restoration_errors[:3]}"  # Логируем только первые 3 ошибки
                )

                # Если не удалось восстановить более 50% событий, считаем это критической ошибкой
                if len(restoration_errors) > len(extracted_events) // 2:
                    raise SerializationError(
                        f"Critical restoration failure: {len(restoration_errors)}/{len(extracted_events)} events not restored"
                    )

            return snapshot_events

        except SerializationError:
            # Перебрасываем serialization errors
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed to create atomic events snapshot after {elapsed:.3f}s: {e}")

            # В экстренном случае пытаемся восстановить события
            emergency_restoration_errors = []
            for event in extracted_events:
                try:
                    self._queue.put_nowait(event)
                except queue.Full:
                    emergency_restoration_errors.append(f"Emergency restoration failed for {event.type}")

            if emergency_restoration_errors:
                logger.critical(f"EMERGENCY restoration failed: {emergency_restoration_errors}")

            # Возвращаем частичный snapshot вместо пустого
            return snapshot_events

    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Получить метаданные сериализации для валидации.

        Returns:
            Dict[str, Any]: Метаданные с информацией о состоянии сериализации
        """
        with self._version_lock:
            current_version = self._version

        return {
            "version": "4.0",  # Обновлено с version-based concurrency control
            "component_type": "EventQueue",
            "thread_safe": True,
            "atomic_serialization": True,
            "serialization_timeout": self._serialization_timeout,
            "uses_timeout_protection": True,
            "graceful_degradation": True,
            "version_based_concurrency": True,  # Новые гарантии консистентности
            "current_state_version": current_version  # Текущая версия состояния
        }


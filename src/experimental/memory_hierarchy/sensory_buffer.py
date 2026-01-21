"""
Сенсорный буфер - Sensory Buffer.

Кратковременное хранение сырых сенсорных данных (событий) до их обработки
MeaningEngine. Реализует кольцевой буфер с TTL-based автоматической очисткой.
"""

import time
import logging
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional

from src.environment.event import Event
from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


@dataclass
class SensoryEntry:
    """
    Запись в сенсорном буфере.

    Содержит сырое событие и метаданные для управления временем жизни.
    """

    event: Event
    entry_timestamp: float  # Время добавления в буфер
    ttl_seconds: float = 2.0  # Время жизни по умолчанию (2 секунды)

    def is_expired(self, current_time: float) -> bool:
        """Проверить, истекло ли время жизни записи."""
        return current_time - self.entry_timestamp > self.ttl_seconds

    def time_remaining(self, current_time: float) -> float:
        """Получить оставшееся время жизни в секундах."""
        elapsed = current_time - self.entry_timestamp
        return max(0.0, self.ttl_seconds - elapsed)


class SensoryBuffer:
    """
    Кольцевой буфер для кратковременного хранения сенсорных данных.

    Отвечает за:
    - Хранение сырых событий до обработки MeaningEngine
    - Автоматическую очистку по TTL (Time To Live)
    - Управление размером буфера (кольцевой буфер)
    - Интеграцию с EventQueue для прозрачной работы
    """

    # Константы
    DEFAULT_BUFFER_SIZE = 256  # Размер кольцевого буфера
    DEFAULT_TTL_SECONDS = 2.0  # Время жизни записей по умолчанию
    CLEANUP_INTERVAL_SECONDS = 0.5  # Интервал очистки в секундах

    def __init__(
        self,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        default_ttl: float = DEFAULT_TTL_SECONDS,
        logger: Optional[StructuredLogger] = None,
    ):
        """
        Инициализация сенсорного буфера.

        Args:
            buffer_size: Максимальный размер буфера
            default_ttl: Время жизни записей по умолчанию
            logger: Логгер для структурированного логирования
        """
        self.buffer_size = buffer_size
        self.default_ttl = default_ttl
        self.logger = logger or StructuredLogger(__name__)

        # Кольцевой буфер на основе deque для эффективного добавления/удаления
        self._buffer: Deque[SensoryEntry] = deque(maxlen=buffer_size)

        # Статистика
        self._total_entries_added = 0
        self._total_entries_expired = 0
        self._total_entries_processed = 0
        self._last_cleanup_time = time.time()

        self.logger.log_event(
            {
                "event_type": "sensory_buffer_initialized",
                "buffer_size": buffer_size,
                "default_ttl": default_ttl,
            }
        )

    def add_event(self, event: Event, custom_ttl: Optional[float] = None) -> None:
        """
        Добавить событие в сенсорный буфер.

        Args:
            event: Событие для добавления
            custom_ttl: Пользовательское время жизни (если None, используется default_ttl)
        """
        ttl = custom_ttl if custom_ttl is not None else self.default_ttl
        entry_timestamp = time.time()

        entry = SensoryEntry(event=event, entry_timestamp=entry_timestamp, ttl_seconds=ttl)

        # Добавляем в буфер (deque автоматически удалит старые записи при переполнении)
        self._buffer.append(entry)
        self._total_entries_added += 1

        # Логируем добавление события (только значимые события)
        if abs(event.intensity) > 0.1:  # Фильтр для значимых событий
            self.logger.log_event(
                {
                    "event_type": "sensory_event_added",
                    "event_type": event.type,
                    "event_intensity": event.intensity,
                    "buffer_size_current": len(self._buffer),
                    "ttl": ttl,
                }
            )

    def get_events_for_processing(self, max_events: Optional[int] = None) -> List[Event]:
        """
        Получить события для обработки MeaningEngine.

        Возвращает события, готовые для обработки, и автоматически удаляет
        их из буфера после извлечения.

        Args:
            max_events: Максимальное количество событий для возврата (None = все)

        Returns:
            Список событий для обработки
        """
        # Сначала выполняем очистку истекших записей
        self._cleanup_expired_entries()

        # Получаем события для обработки
        events_to_process = []
        entries_to_remove = []

        for entry in self._buffer:
            if max_events is not None and len(events_to_process) >= max_events:
                break
            events_to_process.append(entry.event)
            entries_to_remove.append(entry)

        # Удаляем обработанные записи
        for entry in entries_to_remove:
            try:
                self._buffer.remove(entry)
                self._total_entries_processed += 1
            except ValueError:
                # Запись уже была удалена (возможно, при очистке)
                pass

        if events_to_process:
            self.logger.log_event(
                {
                    "event_type": "sensory_events_processed",
                    "events_count": len(events_to_process),
                    "buffer_size_after": len(self._buffer),
                }
            )

        return events_to_process

    def peek_events(self, max_events: Optional[int] = None) -> List[Event]:
        """
        Просмотреть события в буфере без их удаления.

        Args:
            max_events: Максимальное количество событий для просмотра

        Returns:
            Список событий в буфере
        """
        # Очистка перед просмотром
        self._cleanup_expired_entries()

        events = []
        for entry in self._buffer:
            if max_events is not None and len(events) >= max_events:
                break
            events.append(entry.event)

        return events

    def _cleanup_expired_entries(self) -> int:
        """
        Очистить истекшие записи из буфера.

        Returns:
            Количество удаленных записей
        """
        current_time = time.time()

        # Проверяем, пора ли выполнять очистку
        if current_time - self._last_cleanup_time < self.CLEANUP_INTERVAL_SECONDS:
            return 0

        self._last_cleanup_time = current_time

        # Находим истекшие записи
        expired_entries = []
        remaining_entries = deque(maxlen=self.buffer_size)

        for entry in self._buffer:
            if entry.is_expired(current_time):
                expired_entries.append(entry)
            else:
                remaining_entries.append(entry)

        # Обновляем буфер
        self._buffer = remaining_entries
        expired_count = len(expired_entries)
        self._total_entries_expired += expired_count

        if expired_count > 0:
            self.logger.log_event(
                {
                    "event_type": "sensory_buffer_cleanup",
                    "expired_count": expired_count,
                    "buffer_size_after": len(self._buffer),
                }
            )

        return expired_count

    def get_buffer_status(self) -> dict:
        """
        Получить статус сенсорного буфера.

        Returns:
            Dict со статистикой буфера
        """
        current_time = time.time()
        self._cleanup_expired_entries()  # Обновляем статус перед возвратом

        # Вычисляем статистику TTL
        ttl_stats = []
        for entry in self._buffer:
            ttl_stats.append(entry.time_remaining(current_time))

        avg_ttl_remaining = sum(ttl_stats) / len(ttl_stats) if ttl_stats else 0.0
        min_ttl_remaining = min(ttl_stats) if ttl_stats else 0.0
        max_ttl_remaining = max(ttl_stats) if ttl_stats else 0.0

        return {
            "buffer_size": len(self._buffer),
            "buffer_capacity": self.buffer_size,
            "utilization_percent": (len(self._buffer) / self.buffer_size) * 100,
            "total_entries_added": self._total_entries_added,
            "total_entries_processed": self._total_entries_processed,
            "total_entries_expired": self._total_entries_expired,
            "avg_ttl_remaining": avg_ttl_remaining,
            "min_ttl_remaining": min_ttl_remaining,
            "max_ttl_remaining": max_ttl_remaining,
            "oldest_entry_age": ttl_stats[-1] - self.default_ttl if ttl_stats else 0.0,
        }

    def clear_buffer(self) -> None:
        """Очистить буфер полностью."""
        cleared_count = len(self._buffer)
        self._buffer.clear()

        self.logger.log_event(
            {"event_type": "sensory_buffer_cleared", "cleared_count": cleared_count}
        )

    def is_empty(self) -> bool:
        """
        Проверить, пуст ли буфер.

        Returns:
            True если буфер пуст
        """
        self._cleanup_expired_entries()  # Очистка перед проверкой
        return len(self._buffer) == 0

    def __len__(self) -> int:
        """Получить текущее количество записей в буфере."""
        self._cleanup_expired_entries()
        return len(self._buffer)

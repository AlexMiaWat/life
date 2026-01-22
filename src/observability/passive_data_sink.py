"""
Passive Data Sink - истинно пассивный компонент для сбора данных наблюдений.

Не имеет фоновых потоков, очередей или активного поведения.
Просто принимает данные при явных вызовах и хранит их в памяти.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class ObservationData:
    """
    Структура данных для хранения одного наблюдения.
    """

    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = time.time()


class PassiveDataSink:
    """
    Истинно пассивный компонент для сбора данных наблюдений.

    - Не имеет фоновых потоков
    - Не имеет очередей
    - Только принимает данные при явных вызовах
    - Хранит данные в памяти до явного запроса
    - Полностью синхронный
    """

    def __init__(self, max_entries: int = 1000):
        """
        Инициализация пассивного data sink.

        Args:
            max_entries: Максимальное количество записей в памяти
        """
        self.max_entries = max_entries
        self._entries: List[ObservationData] = []
        self._lock = Lock()

        logger.info(f"PassiveDataSink initialized with max_entries={max_entries}")

    def receive_data(self, event_type: str, data: Dict[str, Any], source: str = "unknown",
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Принять данные наблюдения.

        Этот метод должен вызываться явно внешними компонентами.
        PassiveDataSink не инициирует сбор данных самостоятельно.

        Args:
            event_type: Тип события
            data: Данные наблюдения
            source: Источник данных
            metadata: Дополнительные метаданные
        """
        entry = ObservationData(event_type, data, source, metadata)

        with self._lock:
            self._entries.append(entry)

            # Ограничение размера - удаляем старые записи
            if len(self._entries) > self.max_entries:
                removed_count = len(self._entries) - self.max_entries
                self._entries = self._entries[removed_count:]
                logger.debug(f"PassiveDataSink: removed {removed_count} old entries")

        logger.debug(f"PassiveDataSink: received {event_type} from {source}")

    def get_entries(self, limit: Optional[int] = None, source_filter: Optional[str] = None,
                   event_type_filter: Optional[str] = None) -> List[ObservationData]:
        """
        Получить записи наблюдений.

        Args:
            limit: Максимальное количество записей (None для всех)
            source_filter: Фильтр по источнику
            event_type_filter: Фильтр по типу события

        Returns:
            Список записей наблюдений
        """
        with self._lock:
            entries = self._entries.copy()

        # Применяем фильтры
        if source_filter:
            entries = [e for e in entries if e.source == source_filter]
        if event_type_filter:
            entries = [e for e in entries if e.event_type == event_type_filter]

        # Применяем лимит
        if limit:
            entries = entries[-limit:]  # Берем последние записи

        return entries

    def clear_entries(self) -> int:
        """
        Очистить все записи.

        Returns:
            Количество удаленных записей
        """
        with self._lock:
            count = len(self._entries)
            self._entries.clear()

        logger.info(f"PassiveDataSink: cleared {count} entries")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику по хранимым данным.

        Returns:
            Статистика использования
        """
        with self._lock:
            return {
                "total_entries": len(self._entries),
                "max_entries": self.max_entries,
                "usage_percent": (len(self._entries) / self.max_entries) * 100,
                "sources": list(set(e.source for e in self._entries)),
                "event_types": list(set(e.event_type for e in self._entries)),
                "oldest_timestamp": min((e.timestamp for e in self._entries), default=None),
                "newest_timestamp": max((e.timestamp for e in self._entries), default=None),
            }

    # Методы для обратной совместимости с тестами
    def get_recent_data(self, limit: int = 10) -> List[ObservationData]:
        """
        Получить недавние данные (для обратной совместимости).

        Args:
            limit: Максимальное количество записей

        Returns:
            Список недавних записей
        """
        return self.get_entries(limit=limit)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику (для обратной совместимости).

        Returns:
            Статистика использования
        """
        stats = self.get_stats()
        # Добавляем поля для совместимости с тестами
        stats["total_received"] = stats["total_entries"]
        stats["current_entries"] = stats["total_entries"]
        return stats

    def get_data_by_type(self, event_type: str) -> List[ObservationData]:
        """
        Получить данные по типу события (для обратной совместимости).

        Args:
            event_type: Тип события для фильтрации

        Returns:
            Список записей указанного типа
        """
        return self.get_entries(event_type_filter=event_type)

    def get_data_by_source(self, source: str) -> List[ObservationData]:
        """
        Получить данные по источнику (для обратной совместимости).

        Args:
            source: Источник данных для фильтрации

        Returns:
            Список записей от указанного источника
        """
        return self.get_entries(source_filter=source)
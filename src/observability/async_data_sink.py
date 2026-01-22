"""
Async Data Sink - Асинхронный сборщик данных наблюдений.

Использует AsyncDataQueue для асинхронной обработки данных без блокировки runtime loop.
Обновлен для улучшения совместимости с тестами.
"""

import logging
import time
import threading
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.runtime.async_data_queue import AsyncDataQueue
from .passive_data_sink import ObservationData

logger = logging.getLogger(__name__)


class AsyncDataSink:
    """
    Асинхронный сборщик данных наблюдений.

    Использует AsyncDataQueue для асинхронной обработки данных без блокировки
    основного runtime loop. Обеспечивает высокую производительность и надежность.
    """

    def __init__(
        self,
        data_directory: str = "data",
        enabled: bool = True,
        max_queue_size: int = 1000,
        flush_interval: float = 5.0,
        processing_interval: Optional[float] = None
    ):
        """
        Инициализировать асинхронный сборщик данных.

        Args:
            data_directory: Директория для хранения данных
            enabled: Включено ли логирование
            max_queue_size: Максимальный размер очереди
            flush_interval: Интервал сброса данных (секунды)
            processing_interval: Интервал обработки (для совместимости с тестами)
        """
        self.data_directory = Path(data_directory)
        self.enabled = enabled
        self.max_queue_size = max_queue_size
        self.flush_interval = flush_interval
        self.processing_interval = processing_interval or flush_interval

        # Создать директорию если не существует
        self.data_directory.mkdir(parents=True, exist_ok=True)

        # Инициализировать асинхронную очередь
        self.async_queue = AsyncDataQueue(
            queue_name="async_data_sink",
            max_size=max_queue_size,
            processing_interval=self.processing_interval
        )

        # Счетчики статистики
        self._stats = {
            "events_logged": 0,
            "events_processed": 0,
            "queue_overflows": 0,
            "processing_errors": 0,
            "start_time": time.time()
        }

        # Настроить обработчик данных
        self.async_queue.set_data_handler(self._process_observation)

        # Запустить обработку если включено
        if self.enabled:
            self.async_queue.start()

        logger.info(f"AsyncDataSink initialized: enabled={enabled}, queue_size={max_queue_size}")

    def log_event(self, data: Any, event_type: str = "generic", source: str = "async_sink") -> None:
        """
        Логировать событие асинхронно.

        Args:
            data: Данные события
            event_type: Тип события
            source: Источник события
        """
        if not self.enabled:
            return

        observation = ObservationData(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            source=source
        )

        try:
            # Добавить в асинхронную очередь
            success = self.async_queue.add_data(observation)

            if success:
                self._stats["events_logged"] += 1
            else:
                self._stats["queue_overflows"] += 1
                logger.warning("AsyncDataSink queue overflow - dropping observation")

        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            self._stats["processing_errors"] += 1

    def get_recent_data(self, limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить недавние данные из очереди.

        Args:
            limit: Максимальное количество записей

        Returns:
            Список недавних наблюдений
        """
        try:
            # Получить данные из очереди
            raw_data = self.async_queue.get_recent_data(limit=limit)

            # Преобразовать в ObservationData
            observations = []
            for item in raw_data:
                if isinstance(item, ObservationData):
                    observations.append(item)
                elif isinstance(item, dict):
                    observations.append(ObservationData.from_dict(item))

            return observations

        except Exception as e:
            logger.error(f"Failed to get recent data: {e}")
            return []

    def _process_observation(self, observation: ObservationData) -> None:
        """
        Обработать наблюдение (сохранить или передать дальше).

        Args:
            observation: Наблюдение для обработки
        """
        try:
            self._stats["events_processed"] += 1

            # В базовой реализации просто логируем факт обработки
            # В продакшене здесь может быть сохранение в файл или БД
            logger.debug(f"Processed observation: {observation.event_type} from {observation.source}")

        except Exception as e:
            logger.error(f"Failed to process observation: {e}")
            self._stats["processing_errors"] += 1

    def flush(self) -> None:
        """Принудительный сброс буферов."""
        if self.async_queue:
            self.async_queue.flush()

    def shutdown(self) -> None:
        """Корректное завершение работы."""
        logger.info("Shutting down AsyncDataSink...")

        if self.async_queue:
            self.async_queue.shutdown()

        logger.info("AsyncDataSink shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику работы.

        Returns:
            Словарь со статистикой
        """
        base_stats = self._stats.copy()

        # Добавить статистику очереди
        if self.async_queue:
            queue_stats = self.async_queue.get_stats()
            base_stats.update({
                "queue_size": queue_stats.get("current_size", 0),
                "queue_max_size": queue_stats.get("max_size", 0),
                "processing_active": queue_stats.get("processing_active", False)
            })

        runtime = time.time() - base_stats["start_time"]
        base_stats["runtime_seconds"] = runtime
        base_stats["events_per_second"] = base_stats["events_logged"] / runtime if runtime > 0 else 0

        return base_stats


def create_async_data_sink(
    data_directory: str = "data",
    enabled: bool = True,
    max_queue_size: int = 1000,
    flush_interval: float = 5.0,
    processing_interval: Optional[float] = None
) -> AsyncDataSink:
    """
    Фабричная функция для создания AsyncDataSink.

    Args:
        data_directory: Директория для хранения данных
        enabled: Включено ли логирование
        max_queue_size: Максимальный размер очереди
        flush_interval: Интервал сброса данных
        processing_interval: Интервал обработки (для совместимости с тестами)

    Returns:
        AsyncDataSink instance
    """
    return AsyncDataSink(
        data_directory=data_directory,
        enabled=enabled,
        max_queue_size=max_queue_size,
        flush_interval=flush_interval,
        processing_interval=processing_interval
    )
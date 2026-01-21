"""
Async Data Sink - AsyncDataSink

Асинхронная версия PassiveDataSink для высокопроизводительных сценариев.
Использует очередь и фоновую обработку для неблокирующего приема данных.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from collections import deque
import threading
import logging
from pathlib import Path

from .passive_data_sink import ObservationData

logger = logging.getLogger(__name__)


@dataclass
class RawObservationData:
    """Raw данные наблюдения для AsyncDataSink."""
    event_type: str
    data: Dict[str, Any]
    source: str
    metadata: Optional[Dict[str, Any]] = None


class AsyncDataSink:
    """
    Асинхронная версия PassiveDataSink.

    Особенности:
    - Использует asyncio.Queue для неблокирующего приема
    - Фоновая обработка данных в отдельной задаче
    - Поддержка коллбэков для обработки данных
    - Автоматическое управление памятью
    """

    def __init__(self,
                 max_queue_size: int = 1000,
                 processing_interval: float = 0.1,
                 enabled: bool = True,
                 data_directory: Optional[str] = None,
                 queue_size: Optional[int] = None,
                 batch_size: Optional[int] = None):
        """
        Инициализация AsyncDataSink.

        Args:
            max_queue_size: Максимальный размер очереди
            processing_interval: Интервал обработки данных (секунды)
            enabled: Включен ли компонент
            data_directory: Директория для хранения данных (для совместимости)
            queue_size: Альтернативное имя для max_queue_size (для совместимости)
            batch_size: Размер батча обработки (для совместимости)
        """
        # Handle backward compatibility parameters
        if queue_size is not None:
            max_queue_size = queue_size
        if batch_size is not None:
            # batch_size parameter is stored but not used in current implementation
            pass

        self.max_queue_size = max_queue_size
        self.processing_interval = processing_interval
        self.enabled = enabled
        self.data_directory = data_directory
        self.data_dir = Path(data_directory) if data_directory else None  # Alias for backward compatibility
        self.queue_size = max_queue_size  # Alias for backward compatibility
        self.batch_size = batch_size or 1  # Default batch size

        # Asyncio queue для неблокирующего приема
        self._queue: Optional[asyncio.Queue] = None
        self._processing_task: Optional[asyncio.Task] = None

        # Хранение обработанных данных
        self._processed_data: deque[ObservationData] = deque(maxlen=10000)

        # Статистика
        self._total_received = 0
        self._total_processed = 0
        self._queue_overflows = 0

        # Backward compatibility: stats object
        self._stats = type('Stats', (), {
            'queued_items': 0,
            'processed_items': 0,
            'overflow_count': 0
        })()

        # Коллбэки для обработки
        self._data_callbacks: List[Callable[[ObservationData], None]] = []

        # Синхронизация для многопоточной среды
        self._lock = threading.Lock()

    async def start(self) -> None:
        """Запустить фоновую обработку данных."""
        if not self.enabled or self._queue is not None:
            return

        self._queue = asyncio.Queue(maxsize=self.max_queue_size)
        self._processing_task = asyncio.create_task(self._process_queue())

        logger.info("AsyncDataSink started")

    async def stop(self) -> None:
        """Остановить фоновую обработку."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None

        self._queue = None
        logger.info("AsyncDataSink stopped")

    async def receive_data_async(self,
                                 event_type: str,
                                 data: Dict[str, Any],
                                 source: str,
                                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Асинхронно принять данные наблюдения.

        Args:
            event_type: Тип события
            data: Данные события
            source: Источник данных
            metadata: Дополнительные метаданные

        Returns:
            True если данные приняты, False если очередь переполнена
        """
        if not self.enabled or not self._queue:
            return False

        raw_data = RawObservationData(
            event_type=event_type,
            data=data,
            source=source,
            metadata=metadata
        )

        try:
            self._queue.put_nowait(raw_data)
            with self._lock:
                self._total_received += 1
                self._stats.queued_items += 1
            return True
        except asyncio.QueueFull:
            with self._lock:
                self._queue_overflows += 1
            logger.warning("AsyncDataSink queue overflow")
            return False

    def receive_data_sync(self,
                          event_type: str,
                          data: Dict[str, Any],
                          source: str,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Синхронно принять данные наблюдения (блокирующий вызов).

        Args:
            event_type: Тип события
            data: Данные события
            source: Источник данных
            metadata: Дополнительные метаданные

        Returns:
            True если данные приняты
        """
        if not self.enabled or not self._queue:
            return False

        raw_data = RawObservationData(
            event_type=event_type,
            data=data,
            source=source,
            metadata=metadata
        )

        try:
            # Используем asyncio.create_task для неблокирующего добавления
            asyncio.create_task(self._queue.put(raw_data))
            with self._lock:
                self._total_received += 1
                self._stats.queued_items += 1
            return True
        except Exception:
            logger.error("Failed to receive data synchronously", exc_info=True)
            return False

    async def _process_queue(self) -> None:
        """Фоновая обработка данных из очереди."""
        while True:
            try:
                # Обработка всех доступных элементов
                while not self._queue.empty():
                    raw_data = self._queue.get_nowait()

                    # Преобразование в ObservationData
                    observation = ObservationData(
                        timestamp=time.time(),
                        event_type=raw_data.event_type,
                        data=raw_data.data,
                        source=raw_data.source,
                        metadata=raw_data.metadata
                    )

                    # Сохранение в обработанные данные
                    self._processed_data.append(observation)

                    # Вызов коллбэков
                    for callback in self._data_callbacks:
                        try:
                            callback(observation)
                        except Exception as e:
                            logger.error(f"Data callback error: {e}", exc_info=True)

                    with self._lock:
                        self._total_processed += 1
                        self._stats.processed_items += 1
                        self._stats.queued_items = max(0, self._stats.queued_items - 1)

                    self._queue.task_done()

                # Ожидание следующего интервала
                await asyncio.sleep(self.processing_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {e}", exc_info=True)
                await asyncio.sleep(1.0)  # Ожидание перед повторной попыткой

    def add_data_callback(self, callback: Callable[[ObservationData], None]) -> None:
        """
        Добавить коллбэк для обработки данных.

        Args:
            callback: Функция, принимающая ObservationData
        """
        self._data_callbacks.append(callback)

    def remove_data_callback(self, callback: Callable[[ObservationData], None]) -> None:
        """
        Удалить коллбэк обработки данных.

        Args:
            callback: Коллбэк для удаления
        """
        if callback in self._data_callbacks:
            self._data_callbacks.remove(callback)

    def get_recent_data(self, limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить недавние обработанные данные.

        Args:
            limit: Максимальное количество записей

        Returns:
            Список обработанных записей
        """
        data_list = list(self._processed_data)
        if limit:
            data_list = data_list[-limit:]
        return data_list

    def clear_processed_data(self) -> None:
        """Очистить обработанные данные."""
        self._processed_data.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику компонента.

        Returns:
            Dict со статистикой
        """
        with self._lock:
            queue_size = self._queue.qsize() if self._queue else 0

            return {
                "enabled": self.enabled,
                "queue_size": queue_size,
                "max_queue_size": self.max_queue_size,
                "total_received": self._total_received,
                "total_processed": self._total_processed,
                "queue_overflows": self._queue_overflows,
                "processed_data_count": len(self._processed_data),
                "processing_active": self._processing_task is not None and not self._processing_task.done(),
                "data_callbacks_count": len(self._data_callbacks)
            }


def create_async_data_sink(max_queue_size: int = 1000,
                          processing_interval: float = 0.1,
                          enabled: bool = True,
                          data_directory: Optional[str] = None,
                          queue_size: Optional[int] = None,
                          batch_size: Optional[int] = None) -> AsyncDataSink:
    """
    Фабричная функция для создания AsyncDataSink.

    Args:
        max_queue_size: Максимальный размер очереди
        processing_interval: Интервал обработки данных (секунды)
        enabled: Включен ли компонент
        data_directory: Директория для хранения данных
        queue_size: Альтернативное имя для max_queue_size
        batch_size: Размер батча обработки

    Returns:
        AsyncDataSink: Настроенный экземпляр AsyncDataSink
    """
    return AsyncDataSink(
        max_queue_size=max_queue_size,
        processing_interval=processing_interval,
        enabled=enabled,
        data_directory=data_directory,
        queue_size=queue_size,
        batch_size=batch_size
    )
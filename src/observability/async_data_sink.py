"""
Async Data Sink - асинхронный компонент для сбора данных наблюдений.

Использует AsyncDataQueue для асинхронной обработки данных без блокировки runtime loop.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable
from threading import Lock

from src.runtime.async_data_queue import AsyncDataQueue, DataOperation, DataOperationType

logger = logging.getLogger(__name__)


class RawObservationData:
    """
    Структура данных для хранения одного наблюдения в AsyncDataSink.
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


class AsyncDataSink:
    """
    Асинхронный компонент для сбора данных наблюдений.

    - Использует AsyncDataQueue для неблокирующей обработки
    - Поддерживает высокую производительность
    - Может работать с большими объемами данных
    - Имеет встроенную буферизацию и обработку ошибок
    """

    def __init__(
        self,
        data_directory: str = "data",
        enabled: bool = True,
        max_queue_size: int = 1000,
        flush_interval: float = 5.0,
        async_queue: Optional[AsyncDataQueue] = None
    ):
        """
        Инициализация асинхронного data sink.

        Args:
            data_directory: Директория для хранения данных
            enabled: Включен ли sink
            max_queue_size: Максимальный размер внутренней очереди
            flush_interval: Интервал сброса данных
            async_queue: Внешняя AsyncDataQueue (если None, создаст свою)
        """
        self.data_directory = data_directory
        self.enabled = enabled
        self.max_queue_size = max_queue_size
        self.flush_interval = flush_interval

        # Используем предоставленную очередь или создаем свою
        if async_queue:
            self._async_queue = async_queue
            self._owns_queue = False
        else:
            self._async_queue = AsyncDataQueue(
                max_size=max_queue_size,
                flush_interval=flush_interval
            )
            self._owns_queue = True

        self._lock = Lock()
        self._stats = {
            "operations_queued": 0,
            "operations_processed": 0,
            "operations_failed": 0,
            "last_flush": time.time()
        }

        # Запускаем очередь если мы ее создали
        if self._owns_queue:
            self._async_queue.start()

        logger.info(f"AsyncDataSink initialized: directory={data_directory}, enabled={enabled}")

    def accept_data_point_async(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        Асинхронно принять точку данных.

        Args:
            event_type: Тип события
            data: Данные наблюдения
            source: Источник данных
            metadata: Дополнительные метаданные
            callback: Функция обратного вызова

        Returns:
            True если данные поставлены в очередь, False иначе
        """
        if not self.enabled:
            return False

        try:
            # Создаем запись наблюдения
            observation = RawObservationData(event_type, data, source, metadata)

            # Создаем операцию для асинхронного сохранения
            operation = DataOperation(
                operation_type=DataOperationType.SAVE_JSON_REPORT,
                data={
                    "filepath": f"{self.data_directory}/async_observations_{int(time.time())}.jsonl",
                    "data": {
                        "timestamp": observation.timestamp,
                        "event_type": observation.event_type,
                        "source": observation.source,
                        "data": observation.data,
                        "metadata": observation.metadata
                    }
                },
                callback=callback
            )

            # Ставим в очередь
            success = self._async_queue.put_nowait(operation)

            if success:
                with self._lock:
                    self._stats["operations_queued"] += 1
                logger.debug(f"AsyncDataSink: queued {event_type} from {source}")
            else:
                logger.warning(f"AsyncDataSink: queue full, dropped {event_type} from {source}")
                with self._lock:
                    self._stats["operations_failed"] += 1

            return success

        except Exception as e:
            logger.error(f"AsyncDataSink: failed to accept data point: {e}")
            with self._lock:
                self._stats["operations_failed"] += 1
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику AsyncDataSink.

        Returns:
            Статистика использования
        """
        with self._lock:
            stats = self._stats.copy()

        # Добавляем статистику очереди
        if hasattr(self._async_queue, 'get_stats'):
            queue_stats = self._async_queue.get_stats()
            stats.update({
                "queue_size": queue_stats.get("queue_size_current", 0),
                "queue_running": queue_stats.get("is_running", False)
            })

        return stats

    def flush(self) -> None:
        """
        Принудительный сброс буферов.
        """
        if hasattr(self._async_queue, 'get_stats'):
            # Очередь сама управляет сбросом
            pass

    def shutdown(self) -> None:
        """
        Корректное завершение работы.
        """
        if self._owns_queue and hasattr(self._async_queue, 'stop'):
            self._async_queue.stop()
            logger.info("AsyncDataSink: shutdown complete")
"""
Async Data Sink - Асинхронный компонент сбора данных наблюдений.

Предоставляет асинхронный интерфейс для сбора и обработки данных наблюдений
с фоновой записью на диск.
"""

import asyncio
import json
import logging
import threading
import time
import queue
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator
from uuid import uuid4

from .raw_data_access import ObservationData

logger = logging.getLogger(__name__)


class AsyncDataSink:
    """
    Async Data Sink для асинхронного сбора и обработки данных наблюдений.

    Использует отдельный поток для фоновой обработки и записи данных на диск.
    """

    def __init__(
        self,
        data_directory: str = "./data/observations",
        observations_file: str = "async_observations.jsonl",
        enabled: bool = True,
        buffer_size: int = 1000,
        flush_interval: float = 1.0
    ):
        """
        Инициализация AsyncDataSink.

        Args:
            data_directory: Директория для хранения данных
            observations_file: Имя файла для хранения наблюдений
            enabled: Включен ли сбор данных
            buffer_size: Размер буфера в памяти
            flush_interval: Интервал сброса на диск
        """
        self.data_directory = Path(data_directory)
        self.observations_file = observations_file
        self.enabled = enabled
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        # Создаем директорию если не существует
        self.data_directory.mkdir(parents=True, exist_ok=True)

        # Очередь для данных
        self._queue: queue.Queue[ObservationData] = queue.Queue(maxsize=buffer_size)

        # Буфер обработанных данных
        self._processed_data: List[ObservationData] = []

        # Статистика
        self._stats = {
            "enabled": enabled,
            "events_logged": 0,
            "events_processed": 0,
            "buffer_size": buffer_size,
            "data_directory": str(data_directory),
            "observations_file": observations_file
        }

        # Поток обработки
        self._processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        if enabled:
            self._start_processing()

        logger.info(f"AsyncDataSink initialized: {data_directory}/{observations_file}")

    def _start_processing(self) -> None:
        """Запустить поток обработки данных."""
        if self._processing_thread is not None:
            return

        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self._processing_thread.start()

    def _processing_loop(self) -> None:
        """Основной цикл обработки данных."""
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                # Обрабатываем доступные данные
                processed_count = 0
                while not self._queue.empty() and processed_count < 10:
                    try:
                        observation = self._queue.get_nowait()
                        self._processed_data.append(observation)
                        self._stats["events_processed"] += 1
                        processed_count += 1
                    except queue.Empty:
                        break

                # Периодическая запись на диск
                current_time = time.time()
                if current_time - last_flush >= self.flush_interval:
                    self._flush_to_disk()
                    last_flush = current_time

                # Небольшая пауза для снижения нагрузки CPU
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")

        # Финальная запись при остановке
        self._flush_to_disk()

    def log_event(
        self,
        data: Any,
        event_type: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Логировать событие асинхронно.

        Args:
            data: Данные события
            event_type: Тип события
            source: Источник данных
            metadata: Дополнительные метаданные

        Returns:
            True если событие принято, False если отключено или очередь полна
        """
        if not self.enabled:
            return False

        if metadata is None:
            metadata = {}

        try:
            # Создаем объект наблюдения
            observation = ObservationData(
                timestamp=time.time(),
                event_type=event_type,
                data=data,
                source=source,
                metadata=metadata
            )

            # Добавляем в очередь
            self._queue.put_nowait(observation)
            self._stats["events_logged"] += 1
            return True

        except queue.Full:
            logger.warning("AsyncDataSink queue is full, dropping event")
            return False

    def get_recent_data(self, limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить недавние обработанные данные.

        Args:
            limit: Максимальное количество записей

        Returns:
            Список обработанных наблюдений
        """
        data = self._processed_data.copy()
        if limit is not None:
            data = data[-limit:]
        return data

    def flush(self) -> None:
        """Принудительная запись всех данных на диск."""
        if self.enabled:
            self._flush_to_disk()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику AsyncDataSink.

        Returns:
            Словарь со статистикой
        """
        return self._stats.copy()

    def stop(self) -> None:
        """Остановить обработку данных."""
        if not self.enabled:
            return

        self._stop_event.set()

        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)

        # Финальная запись
        self._flush_to_disk()

    def _flush_to_disk(self) -> None:
        """
        Записать данные на диск.
        """
        try:
            file_path = self.data_directory / self.observations_file
            with open(file_path, 'a', encoding='utf-8') as f:
                # Записываем обработанные данные
                for observation in self._processed_data:
                    f.write(observation.to_json_line())

            # Очищаем обработанные данные после записи
            self._processed_data.clear()

        except Exception as e:
            logger.error(f"Failed to flush data to disk: {e}")

    def __len__(self) -> int:
        """Количество обработанных записей."""
        return len(self._processed_data)
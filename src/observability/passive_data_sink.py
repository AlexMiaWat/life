"""
Passive Data Sink - Компонент пассивного сбора данных наблюдений.

Предоставляет интерфейс для сбора, хранения и доступа к данным наблюдений
из различных источников системы Life.
"""

import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator
from uuid import uuid4

from .raw_data_access import ObservationData

logger = logging.getLogger(__name__)


class PassiveDataSink:
    """
    Passive Data Sink для сбора и хранения данных наблюдений.

    Собирает данные из различных источников, хранит их в памяти и на диске,
    предоставляет интерфейс для доступа к историческим данным.
    """

    def __init__(
        self,
        data_directory: str = "./data/observations",
        observations_file: str = "observations.jsonl",
        max_entries: int = 10000,
        enabled: bool = True,
        auto_flush: bool = True
    ):
        """
        Инициализация PassiveDataSink.

        Args:
            data_directory: Директория для хранения данных
            observations_file: Имя файла для хранения наблюдений
            max_entries: Максимальное количество записей в памяти
            enabled: Включен ли сбор данных
            auto_flush: Автоматическая запись на диск
        """
        self.data_directory = Path(data_directory)
        self.observations_file = observations_file
        self.max_entries = max_entries
        self.enabled = enabled
        self.auto_flush = auto_flush

        # Создаем директорию если не существует
        self.data_directory.mkdir(parents=True, exist_ok=True)

        # Буфер в памяти
        self._buffer: deque[ObservationData] = deque(maxlen=max_entries)

        # Статистика
        self._stats = {
            "enabled": enabled,
            "total_entries": 0,
            "buffer_size": 0,
            "data_directory": str(data_directory),
            "observations_file": observations_file
        }

        logger.info(f"PassiveDataSink initialized: {data_directory}/{observations_file}")

    def receive_data(
        self,
        event_type: str,
        data: Any,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Принять данные наблюдения.

        Args:
            event_type: Тип события
            data: Данные события
            source: Источник данных
            metadata: Дополнительные метаданные

        Returns:
            True если данные приняты, False если sink отключен
        """
        if not self.enabled:
            return False

        if metadata is None:
            metadata = {}

        # Создаем объект наблюдения
        observation = ObservationData(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            source=source,
            metadata=metadata
        )

        # Добавляем в буфер
        self._buffer.append(observation)

        # Обновляем статистику
        self._stats["total_entries"] += 1
        self._stats["buffer_size"] = len(self._buffer)

        # Автоматическая запись на диск если включено
        if self.auto_flush:
            self._flush_to_disk()

        return True

    def get_recent_data(self, limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить недавние данные наблюдений.

        Args:
            limit: Максимальное количество записей (None для всех)

        Returns:
            Список наблюдений
        """
        data = list(self._buffer)
        if limit is not None:
            data = data[-limit:]
        return data

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику sink.

        Returns:
            Словарь со статистикой
        """
        return self._stats.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику sink (алиас для get_stats).

        Returns:
            Словарь со статистикой
        """
        return self.get_stats()

    def clear_old_data(self, keep_recent: int = 100) -> int:
        """
        Очистить старые данные, оставив только недавние.

        Args:
            keep_recent: Количество недавних записей для сохранения

        Returns:
            Количество удаленных записей
        """
        if len(self._buffer) <= keep_recent:
            return 0

        removed_count = len(self._buffer) - keep_recent
        # Оставляем только последние keep_recent записей
        while len(self._buffer) > keep_recent:
            self._buffer.popleft()

        self._stats["buffer_size"] = len(self._buffer)
        return removed_count

    def _flush_to_disk(self) -> None:
        """
        Записать данные на диск.
        """
        try:
            file_path = self.data_directory / self.observations_file
            with open(file_path, 'a', encoding='utf-8') as f:
                # Записываем только последние записи из буфера
                for observation in self._buffer:
                    f.write(observation.to_json_line())
        except Exception as e:
            logger.error(f"Failed to flush data to disk: {e}")

    def __len__(self) -> int:
        """Количество записей в буфере."""
        return len(self._buffer)
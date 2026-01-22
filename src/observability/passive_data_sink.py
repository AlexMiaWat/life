"""
Passive Data Sink - Пассивный приемник данных наблюдений.

Предоставляет интерфейс для пассивного сбора данных без активной обработки.
Обеспечивает хранение сырых данных наблюдений в JSONL формате.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ObservationData:
    """
    Структура данных наблюдения для пассивного хранения.
    """
    timestamp: float
    event_type: str
    data: Any
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json_line(self) -> str:
        """Преобразовать в JSONL строку."""
        entry = {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "metadata": self.metadata
        }
        return json.dumps(entry, ensure_ascii=False, default=str) + "\n"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObservationData':
        """Создать объект из словаря."""
        return cls(
            timestamp=data.get("timestamp", time.time()),
            event_type=data.get("event_type", "unknown"),
            data=data.get("data", {}),
            source=data.get("source", "unknown"),
            metadata=data.get("metadata", {})
        )


class PassiveDataSink:
    """
    Пассивный приемник данных наблюдений.

    Обеспечивает:
    - Хранение сырых данных без обработки
    - JSONL формат для эффективного хранения
    - Автоматическое управление размером файлов
    - Простой интерфейс для добавления данных
    """

    def __init__(
        self,
        data_directory: str = "data",
        observations_file: str = "passive_observations.jsonl",
        max_file_age_days: int = 30,
        max_entries: Optional[int] = None,
        enabled: bool = True
    ):
        """
        Инициализировать пассивный приемник данных.

        Args:
            data_directory: Директория для хранения данных
            observations_file: Имя файла для наблюдений
            max_file_age_days: Максимальный возраст файла (дни)
            max_entries: Максимальное количество записей в памяти (для совместимости с тестами)
            enabled: Включено ли логирование
        """
        self.data_directory = Path(data_directory)
        self.observations_file = observations_file
        self.max_file_age_days = max_file_age_days
        self.max_entries = max_entries
        self.enabled = enabled

        # Создать директорию если не существует
        self.data_directory.mkdir(parents=True, exist_ok=True)

        # Полный путь к файлу наблюдений
        self.observations_path = self.data_directory / observations_file

        logger.info(f"PassiveDataSink initialized: {self.observations_path}")

    def add_observation(
        self,
        event_type: str,
        data: Any,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Добавить наблюдение в пассивный sink.

        Args:
            event_type: Тип события
            data: Данные наблюдения
            source: Источник данных
            metadata: Дополнительные метаданные
        """
        if not self.enabled:
            return

        observation = ObservationData(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            source=source,
            metadata=metadata or {}
        )

        try:
            with open(self.observations_path, "a", encoding="utf-8") as f:
                f.write(observation.to_json_line())
        except Exception as e:
            logger.error(f"Failed to write observation: {e}")

    def receive_data(
        self,
        event_type: str,
        data: Any,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Принять данные (алиас для add_observation для совместимости с тестами).

        Args:
            event_type: Тип события
            data: Данные наблюдения
            source: Источник данных
            metadata: Дополнительные метаданные
        """
        self.add_observation(event_type, data, source, metadata)

    def get_recent_data(self, limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить недавние данные наблюдений.

        Args:
            limit: Максимальное количество записей (None - все)

        Returns:
            Список наблюдений
        """
        if not self.observations_path.exists():
            return []

        observations = []
        try:
            with open(self.observations_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line.strip())
                            observations.append(ObservationData.from_dict(data))
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON line: {line.strip()}")

            # Сортировать по времени (новые первыми)
            observations.sort(key=lambda x: x.timestamp, reverse=True)

            if limit:
                observations = observations[:limit]

        except Exception as e:
            logger.error(f"Failed to read observations: {e}")
            observations = []

        return observations

    def get_entries(self) -> List[ObservationData]:
        """
        Получить все записи наблюдений.

        Returns:
            Список всех наблюдений
        """
        return self.get_recent_data(limit=None)

    def clear_old_data(self) -> None:
        """Очистить старые данные на основе max_file_age_days."""
        if not self.observations_path.exists():
            return

        try:
            # Проверить возраст файла
            stat = self.observations_path.stat()
            file_age_days = (time.time() - stat.st_mtime) / (24 * 3600)

            if file_age_days > self.max_file_age_days:
                # Создать backup и очистить файл
                backup_name = f"{self.observations_file}.{int(time.time())}.backup"
                backup_path = self.data_directory / backup_name

                self.observations_path.rename(backup_path)
                logger.info(f"Archived old observations to {backup_path}")

        except Exception as e:
            logger.error(f"Failed to clear old data: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику приемника данных.

        Returns:
            Словарь со статистикой
        """
        if not self.observations_path.exists():
            return {
                "enabled": self.enabled,
                "file_exists": False,
                "total_entries": 0,
                "file_size_bytes": 0
            }

        try:
            stat = self.observations_path.stat()
            entries = self.get_entries()

            return {
                "enabled": self.enabled,
                "file_exists": True,
                "total_entries": len(entries),
                "file_size_bytes": stat.st_size,
                "file_age_seconds": time.time() - stat.st_mtime
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "enabled": self.enabled,
                "error": str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику (алиас для get_stats для совместимости с тестами).

        Returns:
            Словарь со статистикой
        """
        return self.get_stats()


# Глобальный экземпляр для совместимости
_default_passive_sink: Optional[PassiveDataSink] = None


def get_passive_data_sink() -> PassiveDataSink:
    """
    Получить глобальный экземпляр пассивного приемника данных.

    Returns:
        PassiveDataSink instance
    """
    global _default_passive_sink

    if _default_passive_sink is None:
        from src.config.observability_config import get_observability_config
        config = get_observability_config()

        _default_passive_sink = PassiveDataSink(
            data_directory=config.passive_data_sink.data_directory,
            observations_file=config.passive_data_sink.observations_file,
            max_file_age_days=config.passive_data_sink.max_file_age_days,
            enabled=config.passive_data_sink.enabled
        )

    return _default_passive_sink
"""
Raw Data Access - Компонент доступа к raw данным наблюдений.

Предоставляет унифицированный интерфейс для агрегации, фильтрации и экспорта
данных из множественных источников наблюдений.
"""

import json
import csv
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ObservationData:
    """
    Структура данных наблюдения для хранения.
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


@dataclass
class DataSource:
    """
    Источник данных для RawDataAccess.
    """
    name: str
    get_entries: callable
    get_recent_data: Optional[callable] = None

    def get_data(self, limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить данные из источника.

        Args:
            limit: Ограничение количества записей

        Returns:
            Список наблюдений
        """
        try:
            if self.get_recent_data:
                data = self.get_recent_data()
                if limit:
                    return data[:limit]
                return data
            else:
                data = self.get_entries()
                if limit:
                    return data[:limit]
                return data
        except Exception as e:
            logger.error(f"Failed to get data from {self.name}: {e}")
            return []


class RawDataAccess:
    """
    Компонент доступа к raw данным наблюдений.

    Предоставляет унифицированный интерфейс для:
    - Агрегации данных из множественных источников
    - Фильтрации по типам, источникам и времени
    - Экспорта данных в различные форматы
    """

    def __init__(self):
        """Инициализировать компонент доступа к данным."""
        self.data_sources: Dict[str, DataSource] = {}
        logger.info("RawDataAccess initialized")

    def add_data_source(self, source: Any, name: Optional[str] = None) -> None:
        """
        Добавить источник данных.

        Args:
            source: Объект источника данных (должен иметь get_entries или get_recent_data)
            name: Имя источника (автогенерируется если None)
        """
        if name is None:
            name = f"source_{len(self.data_sources)}"

        # Проверить наличие необходимых методов
        if not hasattr(source, 'get_entries') and not hasattr(source, 'get_recent_data'):
            logger.error(f"Source {name} missing required methods (get_entries or get_recent_data)")
            return

        data_source = DataSource(
            name=name,
            get_entries=getattr(source, 'get_entries', lambda: []),
            get_recent_data=getattr(source, 'get_recent_data', None)
        )

        self.data_sources[name] = data_source
        logger.info(f"Added data source: {name}")

    def remove_data_source(self, name: str) -> None:
        """
        Удалить источник данных.

        Args:
            name: Имя источника для удаления
        """
        if name in self.data_sources:
            del self.data_sources[name]
            logger.info(f"Removed data source: {name}")
        else:
            logger.warning(f"Data source not found: {name}")

    def get_raw_data(
        self,
        source_filter: Optional[str] = None,
        event_type_filter: Optional[str] = None,
        time_window: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[ObservationData]:
        """
        Получить raw данные с фильтрами.

        Args:
            source_filter: Фильтр по источнику
            event_type_filter: Фильтр по типу события
            time_window: Временное окно в секундах (от текущего времени)
            limit: Ограничение количества записей

        Returns:
            Список отфильтрованных наблюдений
        """
        all_data = []

        # Собрать данные из всех источников
        for source in self.data_sources.values():
            try:
                source_data = source.get_data()

                # Применить фильтры
                filtered_data = self._apply_filters(
                    source_data,
                    source_filter=source_filter,
                    event_type_filter=event_type_filter,
                    time_window=time_window
                )

                all_data.extend(filtered_data)

            except Exception as e:
                logger.error(f"Failed to get data from {source.name}: {e}")

        # Сортировать по времени (новые первыми)
        all_data.sort(key=lambda x: x.timestamp, reverse=True)

        # Применить глобальный limit
        if limit:
            all_data = all_data[:limit]

        return all_data

    def get_data_by_time_window(self, time_window_seconds: float) -> List[ObservationData]:
        """
        Получить данные за временной интервал.

        Args:
            time_window_seconds: Временное окно в секундах

        Returns:
            Список наблюдений за указанный период
        """
        return self.get_raw_data(time_window=time_window_seconds)

    def _apply_filters(
        self,
        data: List[ObservationData],
        source_filter: Optional[str] = None,
        event_type_filter: Optional[str] = None,
        time_window: Optional[float] = None
    ) -> List[ObservationData]:
        """
        Применить фильтры к данным.

        Args:
            data: Исходные данные
            source_filter: Фильтр по источнику
            event_type_filter: Фильтр по типу события
            time_window: Временное окно

        Returns:
            Отфильтрованные данные
        """
        filtered = data

        # Фильтр по источнику
        if source_filter:
            filtered = [d for d in filtered if d.source == source_filter]

        # Фильтр по типу события
        if event_type_filter:
            filtered = [d for d in filtered if d.event_type == event_type_filter]

        # Фильтр по времени
        if time_window:
            cutoff_time = time.time() - time_window
            filtered = [d for d in filtered if d.timestamp >= cutoff_time]

        return filtered

    def export_data(
        self,
        format_type: str = "json",
        filepath: Optional[str] = None,
        source_filter: Optional[str] = None,
        event_type_filter: Optional[str] = None,
        time_window: Optional[float] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        Экспортировать данные в файл.

        Args:
            format_type: Формат экспорта (json, jsonl, csv)
            filepath: Путь к файлу (автогенерируется если None)
            source_filter: Фильтр по источнику
            event_type_filter: Фильтр по типу события
            time_window: Временное окно
            limit: Ограничение количества

        Returns:
            Путь к созданному файлу
        """
        # Получить данные
        data = self.get_raw_data(
            source_filter=source_filter,
            event_type_filter=event_type_filter,
            time_window=time_window,
            limit=limit
        )

        # Автогенерация пути если не указан
        if filepath is None:
            timestamp = int(time.time())
            filepath = f"data/export_{timestamp}.{format_type}"

        # Создать директорию если нужно
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        try:
            if format_type == "json":
                self._export_json(data, filepath)
            elif format_type == "jsonl":
                self._export_jsonl(data, filepath)
            elif format_type == "csv":
                self._export_csv(data, filepath)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            logger.info(f"Exported {len(data)} records to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            raise

    def _export_json(self, data: List[ObservationData], filepath: str) -> None:
        """Экспорт в JSON формат."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([self._observation_to_dict(d) for d in data], f, indent=2, ensure_ascii=False, default=str)

    def _export_jsonl(self, data: List[ObservationData], filepath: str) -> None:
        """Экспорт в JSONL формат."""
        with open(filepath, "w", encoding="utf-8") as f:
            for observation in data:
                f.write(json.dumps(self._observation_to_dict(observation), ensure_ascii=False, default=str) + "\n")

    def _export_csv(self, data: List[ObservationData], filepath: str) -> None:
        """Экспорт в CSV формат."""
        if not data:
            return

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Заголовки
            headers = ["timestamp", "event_type", "source", "data", "metadata"]
            writer.writerow(headers)

            # Данные
            for observation in data:
                row = [
                    observation.timestamp,
                    observation.event_type,
                    observation.source,
                    json.dumps(observation.data, ensure_ascii=False, default=str),
                    json.dumps(observation.metadata, ensure_ascii=False, default=str)
                ]
                writer.writerow(row)

    def _observation_to_dict(self, observation: ObservationData) -> Dict[str, Any]:
        """Преобразовать ObservationData в словарь."""
        return {
            "timestamp": observation.timestamp,
            "event_type": observation.event_type,
            "data": observation.data,
            "source": observation.source,
            "metadata": observation.metadata
        }

    def get_event_type_distribution(self) -> Dict[str, int]:
        """
        Получить распределение по типам событий.

        Returns:
            Словарь {event_type: count}
        """
        data = self.get_raw_data()
        distribution = {}

        for observation in data:
            event_type = observation.event_type
            distribution[event_type] = distribution.get(event_type, 0) + 1

        return distribution

    def get_source_distribution(self) -> Dict[str, int]:
        """
        Получить распределение по источникам.

        Returns:
            Словарь {source: count}
        """
        data = self.get_raw_data()
        distribution = {}

        for observation in data:
            source = observation.source
            distribution[source] = distribution.get(source, 0) + 1

        return distribution

    def iterate_data(self, chunk_size: int = 100) -> Iterator[List[ObservationData]]:
        """
        Итерация по данным батчами.

        Args:
            chunk_size: Размер батча

        Yields:
            Батчи данных
        """
        data = self.get_raw_data()

        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]

    def get_data_summary(self) -> Dict[str, Any]:
        """
        Получить сводную информацию о данных.

        Returns:
            Словарь со сводной статистикой
        """
        data = self.get_raw_data()

        if not data:
            return {
                "total_records": 0,
                "sources": [],
                "event_types": [],
                "time_range": None
            }

        # Собираем уникальные значения
        sources = set()
        event_types = set()
        timestamps = []

        for observation in data:
            sources.add(observation.source)
            event_types.add(observation.event_type)
            timestamps.append(observation.timestamp)

        # Вычисляем временной диапазон
        timestamps.sort()
        time_range = {
            "oldest": timestamps[0],
            "newest": timestamps[-1],
            "duration": timestamps[-1] - timestamps[0]
        } if timestamps else None

        return {
            "total_records": len(data),
            "sources": list(sources),
            "event_types": list(event_types),
            "time_range": time_range
        }
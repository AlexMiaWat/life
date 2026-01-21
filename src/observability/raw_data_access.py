"""
Raw Data Access - RawDataAccess

Компонент для доступа к raw данным наблюдений без интерпретации.
Предоставляет прямой доступ к хранимым данным в различных форматах.
"""

import json
import time
from typing import Dict, List, Any, Optional, Iterator, Union
from pathlib import Path
from dataclasses import asdict
from collections import defaultdict

from .passive_data_sink import ObservationData
from .async_data_sink import RawObservationData


class RawDataAccess:
    """
    Доступ к raw данным наблюдений без интерпретации.

    Предоставляет:
    - Прямой доступ к данным в различных форматах
    - Фильтрацию и поиск по критериям
    - Экспорт данных
    - Агрегацию и анализ без модификации оригинальных данных
    """

    def __init__(self, data_sources: Optional[List[Union['PassiveDataSink', 'AsyncDataSink']]] = None):
        """
        Инициализация RawDataAccess.

        Args:
            data_sources: Список источников данных для доступа
        """
        self.data_sources = data_sources or []

    def add_data_source(self, source: Union['PassiveDataSink', 'AsyncDataSink']) -> None:
        """
        Добавить источник данных.

        Args:
            source: Источник данных (PassiveDataSink или AsyncDataSink)
        """
        if source not in self.data_sources:
            self.data_sources.append(source)

    def remove_data_source(self, source: Union['PassiveDataSink', 'AsyncDataSink']) -> None:
        """
        Удалить источник данных.

        Args:
            source: Источник данных для удаления
        """
        if source in self.data_sources:
            self.data_sources.remove(source)

    def get_raw_data(self,
                    source_filter: Optional[str] = None,
                    event_type_filter: Optional[str] = None,
                    time_range: Optional[tuple[float, float]] = None,
                    limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить raw данные с фильтрами.

        Args:
            source_filter: Фильтр по источнику
            event_type_filter: Фильтр по типу события
            time_range: Диапазон времени (start, end)
            limit: Максимальное количество записей

        Returns:
            Список записей наблюдений
        """
        all_data = []

        for source in self.data_sources:
            if hasattr(source, 'get_recent_data'):
                # PassiveDataSink
                source_data = source.get_recent_data()
            elif hasattr(source, 'get_recent_data'):
                # AsyncDataSink
                source_data = source.get_recent_data()
            else:
                continue

            all_data.extend(source_data)

        # Применение фильтров
        filtered_data = []
        for obs in all_data:
            # Фильтр по источнику
            if source_filter and obs.source != source_filter:
                continue

            # Фильтр по типу события
            if event_type_filter and obs.event_type != event_type_filter:
                continue

            # Фильтр по времени
            if time_range:
                start_time, end_time = time_range
                if not (start_time <= obs.timestamp <= end_time):
                    continue

            filtered_data.append(obs)

        # Сортировка по времени (новые сначала)
        filtered_data.sort(key=lambda x: x.timestamp, reverse=True)

        # Применение лимита
        if limit:
            filtered_data = filtered_data[:limit]

        return filtered_data

    def get_data_summary(self) -> Dict[str, Any]:
        """
        Получить сводку по всем данным.

        Returns:
            Dict со сводной информацией
        """
        all_data = self.get_raw_data()
        if not all_data:
            return {
                "total_entries": 0,
                "sources": [],
                "event_types": [],
                "time_range": None
            }

        sources = set()
        event_types = set()
        timestamps = []

        for obs in all_data:
            sources.add(obs.source)
            event_types.add(obs.event_type)
            timestamps.append(obs.timestamp)

        return {
            "total_entries": len(all_data),
            "sources": list(sources),
            "event_types": list(event_types),
            "time_range": {
                "earliest": min(timestamps),
                "latest": max(timestamps)
            },
            "data_sources_count": len(self.data_sources)
        }

    def export_data(self,
                   format: str = 'json',
                   file_path: Optional[Union[str, Path]] = None,
                   **filters) -> Union[str, None]:
        """
        Экспортировать данные в указанном формате.

        Args:
            format: Формат экспорта ('json', 'jsonl', 'csv')
            file_path: Путь для сохранения файла (None = вернуть строку)
            **filters: Фильтры для данных

        Returns:
            Экспортированные данные как строка, или None если сохранено в файл
        """
        data = self.get_raw_data(**filters)

        if format == 'json':
            export_data = [asdict(obs) for obs in data]
            result = json.dumps(export_data, indent=2, default=str)

        elif format == 'jsonl':
            lines = []
            for obs in data:
                obs_dict = asdict(obs)
                lines.append(json.dumps(obs_dict, default=str))
            result = '\n'.join(lines)

        elif format == 'csv':
            if not data:
                result = "timestamp,event_type,source,data,metadata\n"
            else:
                lines = ["timestamp,event_type,source,data,metadata"]
                for obs in data:
                    line = [
                        str(obs.timestamp),
                        obs.event_type,
                        obs.source,
                        json.dumps(obs.data),
                        json.dumps(obs.metadata) if obs.metadata else ""
                    ]
                    lines.append(','.join(f'"{item}"' for item in line))
                result = '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")

        if file_path:
            Path(file_path).write_text(result, encoding='utf-8')
            return None
        else:
            return result

    def get_data_by_time_window(self,
                               window_seconds: float,
                               end_time: Optional[float] = None) -> List[ObservationData]:
        """
        Получить данные за указанный временной интервал.

        Args:
            window_seconds: Длительность интервала в секундах
            end_time: Конечное время (по умолчанию - текущее время)

        Returns:
            Данные за указанный интервал
        """
        if end_time is None:
            end_time = time.time()

        start_time = end_time - window_seconds
        return self.get_raw_data(time_range=(start_time, end_time))

    def get_event_type_distribution(self) -> Dict[str, int]:
        """
        Получить распределение типов событий.

        Returns:
            Dict с количеством событий каждого типа
        """
        all_data = self.get_raw_data()
        distribution = defaultdict(int)

        for obs in all_data:
            distribution[obs.event_type] += 1

        return dict(distribution)

    def get_source_distribution(self) -> Dict[str, int]:
        """
        Получить распределение по источникам.

        Returns:
            Dict с количеством событий от каждого источника
        """
        all_data = self.get_raw_data()
        distribution = defaultdict(int)

        for obs in all_data:
            distribution[obs.source] += 1

        return dict(distribution)

    def iterate_data(self, chunk_size: int = 100) -> Iterator[List[ObservationData]]:
        """
        Итератор для обработки данных порциями.

        Args:
            chunk_size: Размер порции

        Yields:
            Порции данных
        """
        all_data = self.get_raw_data()
        for i in range(0, len(all_data), chunk_size):
            yield all_data[i:i + chunk_size]
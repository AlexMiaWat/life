"""
Passive Data Sink - PassiveDataSink

Истинно пассивный компонент для сбора данных наблюдений.
Принимает данные только при явном вызове методов, без фоновых потоков или таймеров.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class ObservationData:
    """Структура данных наблюдения."""
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    source: str
    metadata: Optional[Dict[str, Any]] = None


class PassiveDataSink:
    """
    Истинно пассивный сборщик данных наблюдений.

    Отличия от активных компонентов:
    - Не запускает фоновые потоки
    - Не имеет таймеров или периодических задач
    - Принимает данные только при явных вызовах методов
    - Не зависит от runtime loop
    """

    def __init__(self, max_entries: int = 10000):
        """
        Инициализация PassiveDataSink.

        Args:
            max_entries: Максимальное количество хранимых записей
        """
        self.max_entries = max_entries
        self._data: deque[ObservationData] = deque(maxlen=max_entries)
        self._total_received = 0
        self._last_receive_time: Optional[float] = None

    def receive_data(self, event_type: str, data: Dict[str, Any],
                    source: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Принять данные наблюдения.

        Args:
            event_type: Тип события
            data: Данные события
            source: Источник данных
            metadata: Дополнительные метаданные
        """
        observation = ObservationData(
            timestamp=time.time(),
            event_type=event_type,
            data=data,
            source=source,
            metadata=metadata
        )

        self._data.append(observation)
        self._total_received += 1
        self._last_receive_time = observation.timestamp

    def get_recent_data(self, limit: Optional[int] = None) -> List[ObservationData]:
        """
        Получить недавние данные наблюдений.

        Args:
            limit: Максимальное количество записей (None = все)

        Returns:
            Список записей наблюдений
        """
        data_list = list(self._data)
        if limit:
            data_list = data_list[-limit:]
        return data_list

    def get_data_by_type(self, event_type: str) -> List[ObservationData]:
        """
        Получить данные по типу события.

        Args:
            event_type: Тип события для фильтрации

        Returns:
            Список записей указанного типа
        """
        return [obs for obs in self._data if obs.event_type == event_type]

    def get_data_by_source(self, source: str) -> List[ObservationData]:
        """
        Получить данные по источнику.

        Args:
            source: Источник для фильтрации

        Returns:
            Список записей от указанного источника
        """
        return [obs for obs in self._data if obs.source == source]

    def clear_data(self) -> None:
        """Очистить все хранимые данные."""
        self._data.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику компонента.

        Returns:
            Dict со статистикой
        """
        if not self._data:
            return {
                "total_received": self._total_received,
                "current_entries": 0,
                "max_entries": self.max_entries,
                "last_receive_time": self._last_receive_time,
                "event_types": [],
                "sources": []
            }

        event_types = set(obs.event_type for obs in self._data)
        sources = set(obs.source for obs in self._data)

        return {
            "total_received": self._total_received,
            "current_entries": len(self._data),
            "max_entries": self.max_entries,
            "last_receive_time": self._last_receive_time,
            "event_types": list(event_types),
            "sources": list(sources)
        }
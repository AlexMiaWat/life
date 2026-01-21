"""
Сборщик сырых данных системы Life.

Этот модуль предоставляет инструменты для сбора исключительно сырых счетчиков
системы Life на основе логов, метрик и сохраненных состояний.

Не вмешивается в runtime системы, работает только с внешними данными.
Собирает только raw counters без какой-либо интерпретации или анализа.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class RawSystemCounters:
    """Сырые счетчики состояния системы - только raw данные без интерпретации."""

    timestamp: float = field(default_factory=time.time)

    # Только raw counters - никаких расчетов rate/frequency
    cycle_count: int = 0
    uptime_seconds: float = 0.0
    memory_entries_count: int = 0
    error_count: int = 0
    action_count: int = 0
    event_count: int = 0
    state_change_count: int = 0






@dataclass
class RawDataReport:
    """Отчет с сырыми данными - только counters без интерпретации."""

    observation_period: Tuple[float, float]  # start_time, end_time
    raw_counters: RawSystemCounters

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать отчет в словарь для сериализации."""
        return {
            "observation_period": self.observation_period,
            "raw_counters": {
                "timestamp": self.raw_counters.timestamp,
                "cycle_count": self.raw_counters.cycle_count,
                "uptime_seconds": self.raw_counters.uptime_seconds,
                "memory_entries_count": self.raw_counters.memory_entries_count,
                "error_count": self.raw_counters.error_count,
                "action_count": self.raw_counters.action_count,
                "event_count": self.raw_counters.event_count,
                "state_change_count": self.raw_counters.state_change_count,
            },
        }


class RawDataCollector:
    """
    Сборщик сырых данных системы Life.

    Собирает исключительно raw counters из логов и снимков без какой-либо интерпретации.
    """

    def __init__(
        self, logs_directory: Optional[Path] = None, snapshots_directory: Optional[Path] = None
    ):
        self.logs_directory = logs_directory or Path("logs")
        self.snapshots_directory = snapshots_directory or Path("data/snapshots")
        self.raw_data_history: List[RawDataReport] = []

    def collect_raw_counters_from_logs(
        self, start_time: Optional[float] = None, end_time: Optional[float] = None
    ) -> RawDataReport:
        """
        Собрать сырые счетчики из логов.

        Args:
            start_time: Начало периода сбора (timestamp)
            end_time: Конец периода сбора (timestamp)

        Returns:
            Отчет с сырыми данными
        """
        if start_time is None:
            start_time = time.time() - 3600  # Последний час по умолчанию
        if end_time is None:
            end_time = time.time()

        # Собираем raw counters из логов
        counters = self._extract_raw_counters_from_logs(start_time, end_time)

        report = RawDataReport(
            observation_period=(start_time, end_time),
            raw_counters=counters,
        )

        self.raw_data_history.append(report)
        return report

    def collect_raw_counters_from_snapshots(self, snapshot_paths: List[Path]) -> RawDataReport:
        """
        Собрать сырые счетчики из снимков состояний.

        Args:
            snapshot_paths: Список путей к файлам снимков

        Returns:
            Отчет с сырыми данными
        """
        if not snapshot_paths:
            raise ValueError("Необходимо указать хотя бы один файл снимка")

        # Загружаем снимки
        snapshots_data = []
        for path in snapshot_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    snapshots_data.append(data)
            except Exception as e:
                logger.warning(f"Не удалось загрузить снимок {path}: {e}")

        if not snapshots_data:
            raise ValueError("Не удалось загрузить ни один снимок")

        # Определяем временной диапазон
        start_time = min(s["timestamp"] for s in snapshots_data)
        end_time = max(s["timestamp"] for s in snapshots_data)

        # Собираем raw counters из снимков
        counters = self._extract_raw_counters_from_snapshots(snapshots_data)

        report = RawDataReport(
            observation_period=(start_time, end_time),
            raw_counters=counters,
        )

        self.raw_data_history.append(report)
        return report

    def save_raw_data_report(self, report: RawDataReport, output_path: Path) -> Path:
        """Сохранить отчет с сырыми данными в файл."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Отчет с сырыми данными сохранен: {output_path}")
        return output_path


    def _extract_raw_counters_from_logs(self, start_time: float, end_time: float) -> RawSystemCounters:
        """
        Извлечь сырые счетчики из логов.

        Args:
            start_time: Начало периода сбора
            end_time: Конец периода сбора

        Returns:
            RawSystemCounters с извлеченными raw данными или значениями по умолчанию при ошибках
        """
        try:
            # Извлекаем только raw counters из логов
            logs_data = self._read_logs_safely(start_time, end_time)

            if logs_data:
                return RawSystemCounters(
                    timestamp=end_time,
                    cycle_count=logs_data.get("cycle_count", 0),
                    uptime_seconds=end_time - start_time,
                    memory_entries_count=logs_data.get("memory_count", 0),
                    error_count=logs_data.get("error_count", 0),
                    action_count=logs_data.get("action_count", 0),
                    event_count=logs_data.get("event_count", 0),
                    state_change_count=logs_data.get("state_change_count", 0),
                )
            else:
                logger.warning("Не удалось прочитать логи, используем значения по умолчанию")
                return self._get_default_raw_counters(start_time, end_time)

        except Exception as e:
            logger.error(f"Ошибка при извлечении raw counters из логов: {e}")
            return self._get_default_raw_counters(start_time, end_time)

    def _read_logs_safely(self, start_time: float, end_time: float) -> Optional[Dict[str, Any]]:
        """
        Безопасно прочитать логи за указанный период с улучшенной обработкой ошибок.

        Returns:
            Словарь с данными логов или None при ошибке
        """
        try:
            import os
            import time

            # Проверяем существование директории логов
            if not self.logs_directory.exists():
                logger.debug(f"Директория логов не существует: {self.logs_directory}")
                return None

            if not self.logs_directory.is_dir():
                logger.warning(f"Путь логов не является директорией: {self.logs_directory}")
                return None

            # Проверяем права доступа
            if not os.access(self.logs_directory, os.R_OK):
                logger.warning(f"Нет прав на чтение директории логов: {self.logs_directory}")
                return None

            # Проверяем, что временной диапазон разумный
            time_range = end_time - start_time
            if time_range <= 0:
                logger.warning(f"Некорректный временной диапазон: {start_time} - {end_time}")
                return None

            if time_range > 30 * 24 * 3600:  # 30 дней
                logger.warning(f"Слишком большой временной диапазон: {time_range} секунд")
                return None

            # TODO: Реализовать чтение и анализ реальных логов
            # Пока имитируем успешное чтение с проверкой времени
            current_time = time.time()
            if abs(end_time - current_time) > 3600:  # Не более часа в будущее/прошлое
                logger.warning(f"Время сбора данных слишком далеко от текущего: {end_time} vs {current_time}")
                return None

            # Имитируем данные только для разумных запросов
            return {
                "cycle_count": 1000,
                "memory_count": 500,
                "error_count": 5,
                "action_count": 200,
                "event_count": 150,
                "state_change_count": 75,
            }

        except (OSError, PermissionError) as e:
            logger.warning(f"Ошибка файловой системы при чтении логов: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при чтении логов: {e}")
            return None

    def _get_default_raw_counters(self, start_time: float, end_time: float) -> RawSystemCounters:
        """Получить raw counters по умолчанию при ошибках."""
        return RawSystemCounters(
            timestamp=end_time,
            cycle_count=0,
            uptime_seconds=end_time - start_time,
            memory_entries_count=0,
            error_count=0,
            action_count=0,
            event_count=0,
            state_change_count=0,
        )

    def _extract_raw_counters_from_snapshots(self, snapshots: List[Dict]) -> RawSystemCounters:
        """Извлечь сырые счетчики из снимков."""
        # Извлекаем только raw counters из snapshots
        total_cycles = len(snapshots)
        uptime = snapshots[-1]["timestamp"] - snapshots[0]["timestamp"]

        # Суммируем счетчики по всем snapshots
        memory_total = 0
        error_total = 0
        action_total = 0
        event_total = 0
        state_change_total = 0

        for snapshot in snapshots:
            memory_total += snapshot.get("memory_size", 0)
            error_total += snapshot.get("error_count", 0)
            action_total += snapshot.get("action_count", 0)
            event_total += snapshot.get("event_count", 0)
            state_change_total += snapshot.get("state_change_count", 0)

        return RawSystemCounters(
            timestamp=snapshots[-1]["timestamp"],
            cycle_count=total_cycles,
            uptime_seconds=uptime,
            memory_entries_count=memory_total,
            error_count=error_total,
            action_count=action_total,
            event_count=event_total,
            state_change_count=state_change_total,
        )










# Алиас для обратной совместимости с тестами
ExternalObserver = RawDataCollector

"""
Unified Observation API for Life system.

Единая точка входа для пассивного наблюдения с четким API.
Объединяет все компоненты наблюдения: PassiveDataSink, RawDataCollector,
StructuredLogger и DeveloperReports.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from .async_passive_observer import PassiveDataSink
from .external_observer import RawDataCollector, RawDataReport
from .structured_logger import StructuredLogger
from .developer_reports import RawDataAccess
from src.config.observability_config import get_observability_config, ObservabilityConfig

logger = logging.getLogger(__name__)


class UnifiedObservationAPI:
    """
    Единая точка входа для пассивного наблюдения системы Life.

    Предоставляет унифицированный интерфейс для всех операций наблюдения:
    - Прием данных (пассивный)
    - Сбор сырых счетчиков
    - Структурированное логирование
    - Доступ к историческим данным
    """

    def __init__(
        self,
        config: Optional[ObservabilityConfig] = None,
        data_directory: Optional[str] = None,
        logs_directory: Optional[str] = None,
        snapshots_directory: Optional[str] = None,
        structured_log_file: Optional[str] = None,
        enabled: Optional[bool] = None
    ):
        """
        Инициализация Unified Observation API.

        Args:
            config: Конфигурация observability (если None - загрузит из файла)
            data_directory: Базовая директория для данных (override config)
            logs_directory: Директория с логами (override config)
            snapshots_directory: Директория со снимками (override config)
            structured_log_file: Путь к файлу структурированных логов (override config)
            enabled: Включено ли наблюдение (override config)
        """
        # Загрузить конфигурацию
        self._config = config or get_observability_config()

        # Override из параметров конструктора
        self.enabled = enabled if enabled is not None else self._config.enabled
        self.data_directory = Path(data_directory or self._config.data_directory)

        # Инициализируем компоненты с настройками из конфигурации
        self._data_sink = PassiveDataSink(
            data_directory=str(self.data_directory),
            enabled=self.enabled
        )

        self._raw_collector = RawDataCollector(
            logs_directory=Path(logs_directory or self._config.logs_directory),
            snapshots_directory=Path(snapshots_directory or self._config.raw_data_collector.snapshots_directory)
        )

        self._structured_logger = StructuredLogger(
            log_file=structured_log_file or self._config.structured_logging.log_file,
            enabled=self.enabled
        )

        self._data_access = RawDataAccess(data_directory=str(self.data_directory))

        logger.info("UnifiedObservationAPI initialized with configuration")

    # ===== ПАССИВНЫЙ ПРИЕМ ДАННЫХ =====

    def accept_data_point(self, data: Dict[str, Any]) -> bool:
        """
        Принять точку данных для пассивного хранения.

        Args:
            data: Данные для хранения

        Returns:
            True если данные приняты, False иначе
        """
        if not self.enabled:
            return False

        try:
            return self._data_sink.accept_data_point(data)
        except Exception as e:
            logger.warning(f"Failed to accept data point via data sink: {e}")
            # Graceful degradation: try to log directly if sink fails
            try:
                self._structured_logger.log_error("data_acceptance", e)
                return False  # Data not stored but error logged
            except Exception as log_error:
                logger.error(f"Failed to log data acceptance error: {log_error}")
                return False

    def accept_snapshot_data(self, snapshot_data: Dict[str, Any]) -> bool:
        """
        Принять данные снимка состояния.

        Args:
            snapshot_data: Данные снимка

        Returns:
            True если данные приняты, False иначе
        """
        if not self.enabled:
            return False

        try:
            return self._data_sink.accept_snapshot_data(snapshot_data)
        except Exception as e:
            logger.warning(f"Failed to accept snapshot data via data sink: {e}")
            # Graceful degradation: log error and continue
            try:
                self._structured_logger.log_error("snapshot_acceptance", e)
            except Exception as log_error:
                logger.error(f"Failed to log snapshot acceptance error: {log_error}")
            return False

    # ===== СТРУКТУРИРОВАННОЕ ЛОГИРОВАНИЕ =====

    def log_event(self, event: Any, correlation_id: Optional[str] = None) -> str:
        """
        Залогировать событие.

        Args:
            event: Объект события
            correlation_id: ID корреляции (генерируется если None)

        Returns:
            ID корреляции для цепочки
        """
        if not self.enabled:
            return correlation_id or "disabled"

        try:
            return self._structured_logger.log_event(event, correlation_id)
        except Exception as e:
            logger.warning(f"Failed to log event: {e}")
            # Graceful degradation: return fallback correlation_id
            return correlation_id or f"error_{int(time.time())}"

    def log_meaning(self, event: Any, meaning: Any, correlation_id: str) -> None:
        """
        Залогировать обработку смысла.

        Args:
            event: Исходное событие
            meaning: Объект смысла
            correlation_id: ID корреляции
        """
        if not self.enabled:
            return

        try:
            self._structured_logger.log_meaning(event, meaning, correlation_id)
        except Exception as e:
            logger.warning(f"Failed to log meaning processing: {e}")

    def log_decision(self, correlation_id: str) -> None:
        """
        Залогировать решение.

        Args:
            correlation_id: ID корреляции
        """
        if not self.enabled:
            return

        try:
            self._structured_logger.log_decision(correlation_id)
        except Exception as e:
            logger.warning(f"Failed to log decision: {e}")

    def log_action(self, action_id: str, correlation_id: str) -> None:
        """
        Залогировать действие.

        Args:
            action_id: ID действия
            correlation_id: ID корреляции
        """
        if not self.enabled:
            return

        try:
            self._structured_logger.log_action(action_id, correlation_id)
        except Exception as e:
            logger.warning(f"Failed to log action: {e}")

    def log_feedback(self, feedback: Any, correlation_id: str) -> None:
        """
        Залогировать обратную связь.

        Args:
            feedback: Объект обратной связи
            correlation_id: ID корреляции
        """
        if not self.enabled:
            return

        try:
            self._structured_logger.log_feedback(feedback, correlation_id)
        except Exception as e:
            logger.warning(f"Failed to log feedback: {e}")

    def log_tick_start(self, tick_number: int, queue_size: int) -> None:
        """
        Залогировать начало тика.

        Args:
            tick_number: Номер тика
            queue_size: Размер очереди
        """
        self._structured_logger.log_tick_start(tick_number, queue_size)

    def log_tick_end(self, tick_number: int) -> None:
        """
        Залогировать конец тика.

        According to ADR 001, only raw counters are allowed. Duration and events
        processed are derived metrics that should be calculated externally.

        Args:
            tick_number: Номер тика (raw counter)
        """
        self._structured_logger.log_tick_end(tick_number)

    def log_error(self, stage: str, error: Exception, correlation_id: Optional[str] = None) -> None:
        """
        Залогировать ошибку.

        Args:
            stage: Стадия где произошла ошибка
            error: Объект исключения
            correlation_id: ID корреляции
        """
        self._structured_logger.log_error(stage, error, correlation_id)

    # ===== СБОР СЫРЫХ ДАННЫХ =====

    def collect_raw_counters_from_logs(
        self, start_time: Optional[float] = None, end_time: Optional[float] = None
    ) -> RawDataReport:
        """
        Собрать сырые счетчики из логов.

        Args:
            start_time: Начало периода
            end_time: Конец периода

        Returns:
            Отчет с сырыми данными
        """
        try:
            return self._raw_collector.collect_raw_counters_from_logs(start_time, end_time)
        except Exception as e:
            logger.warning(f"Failed to collect raw counters from logs: {e}")
            # Graceful degradation: return empty report
            from src.observability.external_observer import RawDataReport, RawSystemCounters
            return RawDataReport(
                observation_period=(start_time or time.time() - 3600, end_time or time.time()),
                raw_counters=RawSystemCounters()
            )

    def collect_raw_counters_from_snapshots(self, snapshot_paths: List[Path]) -> RawDataReport:
        """
        Собрать сырые счетчики из снимков.

        Args:
            snapshot_paths: Пути к файлам снимков

        Returns:
            Отчет с сырыми данными
        """
        try:
            return self._raw_collector.collect_raw_counters_from_snapshots(snapshot_paths)
        except Exception as e:
            logger.warning(f"Failed to collect raw counters from snapshots: {e}")
            # Graceful degradation: return empty report
            from src.observability.external_observer import RawDataReport, RawSystemCounters
            return RawDataReport(
                observation_period=(time.time() - 3600, time.time()),
                raw_counters=RawSystemCounters()
            )

    def save_raw_data_report(self, report: RawDataReport, output_path: Path) -> Path:
        """
        Сохранить отчет с сырыми данными.

        Args:
            report: Отчет для сохранения
            output_path: Путь для сохранения

        Returns:
            Путь к сохраненному файлу
        """
        try:
            return self._raw_collector.save_raw_data_report(report, output_path)
        except Exception as e:
            logger.warning(f"Failed to save raw data report: {e}")
            # Graceful degradation: return original path
            return output_path

    # ===== ДОСТУП К ДАННЫМ =====

    def get_raw_observation_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Получить сырые данные наблюдений.

        Args:
            hours: Часы для поиска данных

        Returns:
            Список записей наблюдений
        """
        try:
            return self._data_access.get_raw_observation_data(hours)
        except Exception as e:
            logger.warning(f"Failed to get raw observation data: {e}")
            return []

    def get_raw_snapshot_data(self) -> Optional[Dict[str, Any]]:
        """
        Получить последние данные снимка.

        Returns:
            Данные снимка или None
        """
        try:
            return self._data_access.get_raw_snapshot_data()
        except Exception as e:
            logger.warning(f"Failed to get raw snapshot data: {e}")
            return None

    def export_raw_data(self, hours: int = 24, output_path: Optional[Path] = None) -> Path:
        """
        Экспортировать сырые данные.

        Args:
            hours: Часы данных для экспорта
            output_path: Путь для сохранения

        Returns:
            Путь к экспортированному файлу
        """
        try:
            return self._data_access.export_raw_data(hours, output_path)
        except Exception as e:
            logger.warning(f"Failed to export raw data: {e}")
            # Graceful degradation: return fallback path
            return output_path or Path("data/export_failed.json")

    # ===== СТАТУС И УПРАВЛЕНИЕ =====

    def get_status(self) -> Dict[str, Any]:
        """
        Получить статус всех компонентов наблюдения.

        Returns:
            Словарь со статусом
        """
        return {
            "enabled": self.enabled,
            "data_directory": str(self.data_directory),
            "components": {
                "data_sink": self._data_sink.get_status(),
                "data_access": self._data_access.get_data_collection_status(),
                "structured_logger": {
                    "enabled": self._structured_logger.enabled,
                    "log_file": self._structured_logger.log_file
                }
            },
            "timestamp": time.time()
        }

    def enable(self) -> None:
        """Включить наблюдение."""
        self.enabled = True
        self._data_sink.enable()
        self._structured_logger.enabled = True
        logger.info("UnifiedObservationAPI enabled")

    def disable(self) -> None:
        """Отключить наблюдение."""
        self.enabled = False
        self._data_sink.disable()
        self._structured_logger.enabled = False
        logger.info("UnifiedObservationAPI disabled")

    # ===== УДОБНЫЕ МЕТОДЫ =====

    def quick_status_report(self) -> Dict[str, Any]:
        """
        Быстрый отчет о статусе системы.

        Returns:
            Краткий статус системы
        """
        # Получить последние данные
        latest_snapshot = self.get_raw_snapshot_data()
        recent_observations = self.get_raw_observation_data(hours=1)

        return {
            "timestamp": time.time(),
            "enabled": self.enabled,
            "latest_snapshot_available": latest_snapshot is not None,
            "recent_observations_count": len(recent_observations),
            "data_directory_exists": self.data_directory.exists(),
            "structured_log_exists": Path(self._structured_logger.log_file).exists()
        }

    def emergency_data_collection(self) -> Dict[str, Any]:
        """
        Экстренный сбор данных для диагностики.

        Returns:
            Словарь с диагностическими данными
        """
        try:
            # Собираем данные за последний час
            report = self.collect_raw_counters_from_logs(
                start_time=time.time() - 3600,
                end_time=time.time()
            )

            # Добавляем последние наблюдения
            observations = self.get_raw_observation_data(hours=1)

            # Добавляем статус
            status = self.get_status()

            return {
                "emergency_report": report.to_dict(),
                "recent_observations": observations[-10:] if observations else [],  # Последние 10
                "system_status": status,
                "collected_at": time.time()
            }

        except Exception as e:
            logger.error(f"Ошибка экстренного сбора данных: {e}")
            return {
                "error": str(e),
                "collected_at": time.time()
            }
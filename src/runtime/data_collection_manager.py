"""
Менеджер сбора данных для координации асинхронных операций.

Предоставляет высокоуровневый интерфейс для сбора различных типов данных
с автоматической буферизацией и асинхронной записью.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

from src.runtime.async_data_queue import AsyncDataQueue, DataOperation, DataOperationType

logger = logging.getLogger(__name__)


@dataclass
class DataCollectionConfig:
    """
    Конфигурация менеджера сбора данных.

    Attributes:
        queue_max_size: Максимальный размер очереди операций
        flush_interval: Интервал автоматического сброса (сек)
        max_retries: Максимальное количество повторных попыток
        retry_delay: Задержка между повторными попытками (сек)
        buffer_max_size: Максимальный размер буфера перед принудительным сбросом
        auto_flush_threshold: Порог для автоматического сброса (% от buffer_max_size)
    """
    queue_max_size: int = 1000
    flush_interval: float = 5.0
    max_retries: int = 3
    retry_delay: float = 1.0
    buffer_max_size: int = 100
    auto_flush_threshold: float = 0.8


@dataclass
class BufferedData:
    """
    Буферизованные данные для периодического сброса.

    Attributes:
        data_type: Тип данных (например, 'technical_reports', 'metrics')
        buffer: Список записей данных
        last_flush: Время последнего сброса
        flush_interval: Интервал сброса (сек)
        filepath_template: Шаблон пути к файлу
    """
    data_type: str
    buffer: List[Dict[str, Any]] = field(default_factory=list)
    last_flush: float = field(default_factory=time.time)
    flush_interval: float = 30.0  # 30 секунд по умолчанию
    filepath_template: str = ""

    def should_flush(self, current_time: float = None) -> bool:
        """Проверить необходимость сброса буфера."""
        if current_time is None:
            current_time = time.time()

        time_based = (current_time - self.last_flush) >= self.flush_interval
        size_based = len(self.buffer) >= 10  # Минимум 10 записей

        return time_based or size_based

    def add_record(self, record: Dict[str, Any]) -> None:
        """Добавить запись в буфер."""
        self.buffer.append(record)

    def clear_buffer(self) -> List[Dict[str, Any]]:
        """Очистить буфер и вернуть содержимое."""
        data = self.buffer.copy()
        self.buffer.clear()
        self.last_flush = time.time()
        return data


class DataCollectionManager:
    """
    Менеджер сбора данных с асинхронной записью.

    Координирует сбор различных типов данных, буферизует их в памяти
    и выполняет запись через асинхронную очередь.
    """

    def __init__(self, config: Optional[DataCollectionConfig] = None):
        """
        Инициализация менеджера сбора данных.

        Args:
            config: Конфигурация менеджера
        """
        self.config = config or DataCollectionConfig()

        # Асинхронная очередь операций
        self._queue = AsyncDataQueue(
            max_size=self.config.queue_max_size,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            flush_interval=self.config.flush_interval
        )

        # Передаем ссылку на себя для периодического обслуживания
        self._queue.set_data_collection_manager(self)

        # Буферы для различных типов данных
        self._buffers: Dict[str, BufferedData] = {}

        # Статистика
        self._stats = {
            "total_operations": 0,
            "buffered_records": 0,
            "flushed_buffers": 0,
            "failed_operations": 0,
        }

        # Флаг активности
        self._is_active = False

        # Инициализировать стандартные буферы
        self._initialize_buffers()

        logger.info("DataCollectionManager initialized")

    def start(self) -> None:
        """Запустить менеджер сбора данных."""
        if self._is_active:
            logger.warning("DataCollectionManager is already running")
            return

        self._queue.start()
        self._is_active = True
        logger.info("DataCollectionManager started")

    def stop(self) -> None:
        """Остановить менеджер сбора данных."""
        if not self._is_active:
            return

        # Выполнить финальный сброс всех буферов
        self._flush_all_buffers()

        self._queue.stop()
        self._is_active = False
        logger.info("DataCollectionManager stopped")

    def save_technical_report(
        self,
        report_data: Dict[str, Any],
        base_dir: str = "metrics",
        filename_prefix: str = "technical_report"
    ) -> bool:
        """
        Сохранить технический отчет.

        Args:
            report_data: Данные отчета
            base_dir: Базовая директория для сохранения
            filename_prefix: Префикс имени файла

        Returns:
            True если операция поставлена в очередь, False иначе
        """
        if not self._is_active:
            logger.warning("DataCollectionManager is not active")
            return False

        # Создать timestamped filename
        timestamp = int(time.time())
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = str(Path(base_dir) / filename)

        # Создать операцию
        operation = DataOperation(
            operation_type=DataOperationType.SAVE_JSON_REPORT,
            data={
                "filepath": filepath,
                "data": report_data,
            },
            priority=7  # Высокий приоритет для технических отчетов
        )

        success = self._queue.put_nowait(operation)
        if success:
            with self._queue._lock:  # Используем lock из очереди для статистики
                self._stats["total_operations"] += 1

        return success

    def buffer_metrics_data(
        self,
        metrics_data: Dict[str, Any],
        data_type: str = "metrics",
        flush_interval: float = 30.0
    ) -> None:
        """
        Буферизовать данные метрик для периодического сброса.

        Args:
            metrics_data: Данные метрик
            data_type: Тип данных для группировки
            flush_interval: Интервал сброса (сек)
        """
        if not self._is_active:
            logger.warning("DataCollectionManager is not active")
            return

        # Получить или создать буфер
        if data_type not in self._buffers:
            self._buffers[data_type] = BufferedData(
                data_type=data_type,
                flush_interval=flush_interval,
                filepath_template=f"data/{data_type}_{{timestamp}}.json"
            )

        buffer = self._buffers[data_type]
        buffer.add_record(metrics_data)
        self._stats["buffered_records"] += 1

        # Проверить необходимость сброса
        if buffer.should_flush():
            self._flush_buffer(buffer)

    def save_csv_data(
        self,
        headers: List[str],
        rows: List[Dict[str, Any]],
        base_dir: str = "data",
        filename_prefix: str = "export"
    ) -> bool:
        """
        Сохранить данные в CSV формате.

        Args:
            headers: Заголовки CSV
            rows: Строки данных
            base_dir: Базовая директория
            filename_prefix: Префикс имени файла

        Returns:
            True если операция поставлена в очередь, False иначе
        """
        if not self._is_active:
            logger.warning("DataCollectionManager is not active")
            return False

        # Создать timestamped filename
        timestamp = int(time.time())
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = str(Path(base_dir) / filename)

        # Создать операцию
        operation = DataOperation(
            operation_type=DataOperationType.SAVE_CSV_DATA,
            data={
                "filepath": filepath,
                "headers": headers,
                "rows": rows,
            },
            priority=5  # Средний приоритет для CSV
        )

        success = self._queue.put_nowait(operation)
        if success:
            with self._queue._lock:
                self._stats["total_operations"] += 1

        return success

    def write_file(
        self,
        filepath: str,
        content: str,
        mode: str = "w",
        priority: int = 3
    ) -> bool:
        """
        Записать файл асинхронно.

        Args:
            filepath: Путь к файлу
            content: Содержимое файла
            mode: Режим открытия файла
            priority: Приоритет операции

        Returns:
            True если операция поставлена в очередь, False иначе
        """
        if not self._is_active:
            logger.warning("DataCollectionManager is not active")
            return False

        # Создать операцию
        operation = DataOperation(
            operation_type=DataOperationType.WRITE_FILE,
            data={
                "filepath": filepath,
                "content": content,
                "mode": mode,
            },
            priority=priority
        )

        success = self._queue.put_nowait(operation)
        if success:
            with self._queue._lock:
                self._stats["total_operations"] += 1

        return success

    def collect_technical_metrics(
        self,
        self_state,
        memory,
        learning_engine,
        adaptation_manager,
        decision_engine,
        base_dir: str = "metrics",
        filename_prefix: str = "technical_report",
        priority: int = 6
    ) -> bool:
        """
        Асинхронно собрать технические метрики системы.

        Args:
            self_state: Текущее состояние системы
            memory: Компонент памяти
            learning_engine: Движок обучения
            adaptation_manager: Менеджер адаптации
            decision_engine: Движок принятия решений
            base_dir: Базовая директория для сохранения
            filename_prefix: Префикс имени файла
            priority: Приоритет операции

        Returns:
            True если операция поставлена в очередь, False иначе
        """
        if not self._is_active:
            logger.warning("DataCollectionManager is not active")
            return False

        # Создать операцию сбора технических метрик
        operation = DataOperation(
            operation_type=DataOperationType.COLLECT_TECHNICAL_METRICS,
            data={
                "self_state": self_state,
                "memory": memory,
                "learning_engine": learning_engine,
                "adaptation_manager": adaptation_manager,
                "decision_engine": decision_engine,
                "base_dir": base_dir,
                "filename_prefix": filename_prefix,
            },
            priority=priority
        )

        success = self._queue.put_nowait(operation)
        if success:
            with self._queue._lock:
                self._stats["total_operations"] += 1

        return success

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику менеджера.

        Returns:
            Словарь со статистикой
        """
        stats = self._stats.copy()
        stats.update(self._queue.get_stats())

        # Добавить информацию о буферах
        buffer_info = {}
        for data_type, buffer in self._buffers.items():
            buffer_info[data_type] = {
                "size": len(buffer.buffer),
                "last_flush": buffer.last_flush,
                "should_flush": buffer.should_flush(),
            }
        stats["buffers"] = buffer_info

        return stats

    def _initialize_buffers(self) -> None:
        """Инициализировать стандартные буферы."""
        # Буфер для технических метрик
        self._buffers["technical_metrics"] = BufferedData(
            data_type="technical_metrics",
            flush_interval=60.0,  # Сброс каждую минуту
            filepath_template="metrics/technical_metrics_{timestamp}.json"
        )

        # Буфер для состояния системы
        self._buffers["system_state"] = BufferedData(
            data_type="system_state",
            flush_interval=30.0,  # Сброс каждые 30 секунд
            filepath_template="data/system_state_{timestamp}.json"
        )

    def _flush_buffer(self, buffer: BufferedData) -> None:
        """
        Сбросить буфер в файл.

        Args:
            buffer: Буфер для сброса
        """
        if not buffer.buffer:
            return

        # Получить данные из буфера
        data = buffer.clear_buffer()

        # Создать timestamp для имени файла
        timestamp = int(time.time())
        filepath = buffer.filepath_template.format(timestamp=timestamp)

        # Создать операцию сохранения JSON
        operation = DataOperation(
            operation_type=DataOperationType.SAVE_JSON_REPORT,
            data={
                "filepath": filepath,
                "data": {
                    "data_type": buffer.data_type,
                    "timestamp": timestamp,
                    "records": data,
                },
            },
            priority=4  # Средний приоритет для буферизованных данных
        )

        success = self._queue.put_nowait(operation)
        if success:
            with self._queue._lock:
                self._stats["total_operations"] += 1
                self._stats["flushed_buffers"] += 1
            logger.debug(f"Buffer flushed: {buffer.data_type}, records: {len(data)}")
        else:
            logger.warning(f"Failed to flush buffer: {buffer.data_type}")
            # Вернуть данные обратно в буфер
            buffer.buffer.extend(data)
            buffer.last_flush = time.time()  # Не обновлять время последнего сброса

    def _flush_all_buffers(self) -> None:
        """Сбросить все буферы."""
        for buffer in self._buffers.values():
            if buffer.buffer:
                self._flush_buffer(buffer)

    def periodic_maintenance(self) -> None:
        """
        Периодическое обслуживание - проверка и сброс буферов.

        Вызывается периодически из runtime loop.
        """
        if not self._is_active:
            return

        current_time = time.time()

        # Проверить все буферы
        for buffer in list(self._buffers.values()):
            if buffer.should_flush(current_time):
                self._flush_buffer(buffer)

    def __enter__(self):
        """Контекстный менеджер - запуск."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - остановка."""
        self.stop()
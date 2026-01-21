"""
Асинхронная очередь для операций сбора данных.

Предоставляет механизм буферизации операций сбора данных,
позволяя runtime loop работать без блокировки на I/O операциях.
"""

import threading
import time
import logging
from typing import Any, Callable, Dict, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum
from queue import Queue, Empty, Full
from pathlib import Path

logger = logging.getLogger(__name__)


class DataOperationType(Enum):
    """Типы операций сбора данных."""
    SAVE_JSON_REPORT = "save_json_report"
    SAVE_CSV_DATA = "save_csv_data"
    COLLECT_METRICS = "collect_metrics"
    COLLECT_TECHNICAL_METRICS = "collect_technical_metrics"
    WRITE_FILE = "write_file"


@dataclass
class DataOperation:
    """
    Операция сбора данных для асинхронного выполнения.

    Attributes:
        operation_type: Тип операции
        data: Данные для обработки
        callback: Функция обратного вызова (опционально)
        priority: Приоритет операции (0-10, 10 - максимальный)
        timestamp: Время постановки в очередь
        retry_count: Количество попыток выполнения
    """
    operation_type: DataOperationType
    data: Dict[str, Any]
    callback: Optional[Callable] = None
    priority: int = 5
    timestamp: float = None
    retry_count: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class AsyncDataQueue:
    """
    Асинхронная очередь для операций сбора данных.

    Предоставляет thread-safe очередь с приоритетами и механизмом
    повторных попыток для надежного выполнения операций.
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        flush_interval: float = 5.0
    ):
        """
        Инициализация асинхронной очереди.

        Args:
            max_size: Максимальный размер очереди
            max_retries: Максимальное количество повторных попыток
            retry_delay: Задержка между повторными попытками (сек)
            flush_interval: Интервал автоматического сброса (сек)
        """
        self.max_size = max_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.flush_interval = flush_interval

        # Основная очередь операций
        self._queue = Queue(maxsize=max_size)

        # Очередь для повторных попыток
        self._retry_queue = Queue(maxsize=max_size)

        # Статистика
        self._stats = {
            "operations_queued": 0,
            "operations_processed": 0,
            "operations_failed": 0,
            "operations_retried": 0,
            "queue_size": 0,
            "retry_queue_size": 0,
        }

        # Синхронизация
        self._lock = threading.RLock()
        self._stop_event = threading.Event()

        # Фоновый поток обработки
        self._worker_thread = None
        self._last_flush = time.time()
        self._last_maintenance = time.time()

        # Ссылка на DataCollectionManager для периодического обслуживания
        self._data_collection_manager = None

        logger.info(
            f"AsyncDataQueue initialized: max_size={max_size}, "
            f"max_retries={max_retries}, flush_interval={flush_interval}s"
        )

    def start(self) -> None:
        """Запустить фоновую обработку очереди."""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("AsyncDataQueue is already running")
            return

        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._process_queue_loop,
            name="AsyncDataQueue-Worker",
            daemon=True
        )
        self._worker_thread.start()
        logger.info("AsyncDataQueue worker thread started")

    def set_data_collection_manager(self, manager) -> None:
        """
        Установить ссылку на DataCollectionManager для периодического обслуживания.

        Args:
            manager: Экземпляр DataCollectionManager
        """
        self._data_collection_manager = manager
        logger.debug("DataCollectionManager reference set for periodic maintenance")

    def stop(self, timeout: float = 5.0) -> None:
        """Остановить фоновую обработку очереди."""
        if not self._worker_thread or not self._worker_thread.is_alive():
            return

        logger.info("Stopping AsyncDataQueue worker thread...")
        self._stop_event.set()

        # Подождать завершения потока
        self._worker_thread.join(timeout=timeout)

        if self._worker_thread.is_alive():
            logger.warning("AsyncDataQueue worker thread did not stop gracefully")
        else:
            logger.info("AsyncDataQueue worker thread stopped")

    def put(
        self,
        operation: DataOperation,
        block: bool = False,
        timeout: float = None
    ) -> bool:
        """
        Поставить операцию в очередь.

        Args:
            operation: Операция для выполнения
            block: Блокировать если очередь полна
            timeout: Таймаут блокировки

        Returns:
            True если операция поставлена в очередь, False иначе
        """
        try:
            self._queue.put(operation, block=block, timeout=timeout)
            with self._lock:
                self._stats["operations_queued"] += 1
                self._stats["queue_size"] = self._queue.qsize()
            return True
        except Full:
            logger.warning(
                f"AsyncDataQueue is full (size={self._queue.qsize()}), "
                "dropping operation"
            )
            with self._lock:
                self._stats["operations_failed"] += 1
            return False

    def put_nowait(self, operation: DataOperation) -> bool:
        """
        Поставить операцию в очередь без блокировки.

        Args:
            operation: Операция для выполнения

        Returns:
            True если операция поставлена в очередь, False иначе
        """
        return self.put(operation, block=False)

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику очереди.

        Returns:
            Словарь со статистикой
        """
        with self._lock:
            stats = self._stats.copy()
            stats["is_running"] = (
                self._worker_thread is not None and
                self._worker_thread.is_alive()
            )
            stats["queue_size_current"] = self._queue.qsize()
            stats["retry_queue_size_current"] = self._retry_queue.qsize()
            return stats

    def _process_queue_loop(self) -> None:
        """Основной цикл обработки очереди."""
        logger.info("AsyncDataQueue processing loop started")

        while not self._stop_event.is_set():
            try:
                # Обработка основной очереди
                self._process_main_queue()

                # Обработка очереди повторных попыток
                self._process_retry_queue()

                # Периодический сброс статистики
                self._periodic_flush()

                # Периодическое обслуживание DataCollectionManager
                self._periodic_maintenance()

                # Небольшая пауза для снижения нагрузки CPU
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in AsyncDataQueue processing loop: {e}")
                time.sleep(1.0)  # Пауза при ошибке

        logger.info("AsyncDataQueue processing loop stopped")

    def _process_main_queue(self) -> None:
        """Обработать операции из основной очереди."""
        try:
            # Получить операцию без блокировки
            operation = self._queue.get_nowait()

            # Выполнить операцию
            success = self._execute_operation(operation)

            if success:
                with self._lock:
                    self._stats["operations_processed"] += 1
                    self._stats["queue_size"] = self._queue.qsize()
                self._queue.task_done()
            else:
                # Переместить в очередь повторных попыток
                self._handle_failed_operation(operation)

        except Empty:
            # Очередь пуста - ничего не делаем
            pass
        except Exception as e:
            logger.error(f"Error processing main queue: {e}")

    def _process_retry_queue(self) -> None:
        """Обработать операции из очереди повторных попыток."""
        try:
            # Проверить очередь повторных попыток
            if self._retry_queue.empty():
                return

            # Получить операцию без блокировки
            operation = self._retry_queue.get_nowait()

            # Проверить время задержки
            if time.time() - operation.timestamp < self.retry_delay:
                # Слишком рано для повторной попытки
                self._retry_queue.put(operation)  # Вернуть обратно
                return

            # Выполнить повторную попытку
            success = self._execute_operation(operation)

            if success:
                with self._lock:
                    self._stats["operations_processed"] += 1
                logger.debug(f"Operation retried successfully: {operation.operation_type}")
            else:
                # Повторная попытка не удалась
                self._handle_failed_operation(operation)

            self._retry_queue.task_done()

        except Empty:
            pass
        except Exception as e:
            logger.error(f"Error processing retry queue: {e}")

    def _execute_operation(self, operation: DataOperation) -> bool:
        """
        Выполнить операцию сбора данных.

        Args:
            operation: Операция для выполнения

        Returns:
            True если выполнение успешно, False иначе
        """
        try:
            if operation.operation_type == DataOperationType.SAVE_JSON_REPORT:
                return self._execute_save_json_report(operation)
            elif operation.operation_type == DataOperationType.SAVE_CSV_DATA:
                return self._execute_save_csv_data(operation)
            elif operation.operation_type == DataOperationType.WRITE_FILE:
                return self._execute_write_file(operation)
            elif operation.operation_type == DataOperationType.COLLECT_METRICS:
                return self._execute_collect_metrics(operation)
            elif operation.operation_type == DataOperationType.COLLECT_TECHNICAL_METRICS:
                return self._execute_collect_technical_metrics(operation)
            else:
                logger.warning(f"Unknown operation type: {operation.operation_type}")
                return False

        except Exception as e:
            logger.error(f"Error executing operation {operation.operation_type}: {e}")
            return False

    def _execute_save_json_report(self, operation: DataOperation) -> bool:
        """Выполнить сохранение JSON отчета."""
        try:
            import json
            import os

            filepath = operation.data["filepath"]
            data = operation.data["data"]

            # Создать директорию если не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Сохранить JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"JSON report saved: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save JSON report: {e}")
            return False

    def _execute_save_csv_data(self, operation: DataOperation) -> bool:
        """Выполнить сохранение CSV данных."""
        try:
            import csv
            import os

            filepath = operation.data["filepath"]
            headers = operation.data["headers"]
            rows = operation.data["rows"]

            # Создать директорию если не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Сохранить CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)

            logger.debug(f"CSV data saved: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save CSV data: {e}")
            return False

    def _execute_write_file(self, operation: DataOperation) -> bool:
        """Выполнить запись файла."""
        try:
            import os

            filepath = operation.data["filepath"]
            content = operation.data["content"]
            mode = operation.data.get("mode", "w")

            # Создать директорию если не существует
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Записать файл
            with open(filepath, mode, encoding="utf-8") as f:
                f.write(content)

            logger.debug(f"File written: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            return False

    def _execute_collect_technical_metrics(self, operation: DataOperation) -> bool:
        """Выполнить сбор технических метрик."""
        try:
            # Импортируем здесь чтобы избежать циклических зависимостей
            from src.technical_monitor import TechnicalBehaviorMonitor

            # Извлекаем данные из операции
            self_state = operation.data["self_state"]
            memory = operation.data["memory"]
            learning_engine = operation.data["learning_engine"]
            adaptation_manager = operation.data["adaptation_manager"]
            decision_engine = operation.data["decision_engine"]
            base_dir = operation.data.get("base_dir", "metrics")
            filename_prefix = operation.data.get("filename_prefix", "technical_report")

            # Создаем монитор и выполняем сбор метрик
            monitor = TechnicalBehaviorMonitor()

            # Захватываем снимок состояния
            snapshot = monitor.capture_system_snapshot(
                self_state, memory, learning_engine, adaptation_manager, decision_engine
            )

            # Анализируем снимок
            report = monitor.analyze_snapshot(snapshot)

            # Сохраняем отчет
            timestamp = int(time.time())
            filename = f"{filename_prefix}_{timestamp}.json"
            filepath = str(Path(base_dir) / filename)

            monitor.save_report(report, filepath, async_save=False)  # Синхронное сохранение в async контексте

            logger.debug(f"Technical metrics collected and saved: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to collect technical metrics: {e}")
            return False

    def _execute_collect_metrics(self, operation: DataOperation) -> bool:
        """Выполнить сбор метрик (заглушка для будущих расширений)."""
        # Пока просто логируем - конкретная логика будет в DataCollectionManager
        logger.debug(f"Metrics collection operation: {operation.data}")
        return True

    def _handle_failed_operation(self, operation: DataOperation) -> None:
        """Обработать неудачную операцию."""
        operation.retry_count += 1

        if operation.retry_count < self.max_retries:
            # Поставить в очередь повторных попыток
            try:
                operation.timestamp = time.time()  # Обновить timestamp
                self._retry_queue.put_nowait(operation)
                with self._lock:
                    self._stats["operations_retried"] += 1
                    self._stats["retry_queue_size"] = self._retry_queue.qsize()
                logger.debug(
                    f"Operation scheduled for retry {operation.retry_count}/{self.max_retries}: "
                    f"{operation.operation_type}"
                )
            except Full:
                logger.error(
                    f"Retry queue is full, dropping operation after {operation.retry_count} retries: "
                    f"{operation.operation_type}"
                )
                with self._lock:
                    self._stats["operations_failed"] += 1
        else:
            # Превышено количество повторных попыток
            logger.error(
                f"Operation failed permanently after {operation.retry_count} retries: "
                f"{operation.operation_type}"
            )
            with self._lock:
                self._stats["operations_failed"] += 1

            # Вызвать callback с ошибкой если есть
            if operation.callback:
                try:
                    operation.callback(success=False, error="Max retries exceeded")
                except Exception as e:
                    logger.error(f"Error in operation callback: {e}")

    def _periodic_flush(self) -> None:
        """Периодический сброс внутренней статистики."""
        current_time = time.time()
        if current_time - self._last_flush >= self.flush_interval:
            # Логировать статистику
            stats = self.get_stats()
            logger.info(
                f"AsyncDataQueue stats: queued={stats['operations_queued']}, "
                f"processed={stats['operations_processed']}, "
                f"failed={stats['operations_failed']}, "
                f"retried={stats['operations_retried']}, "
                f"queue_size={stats['queue_size_current']}, "
                f"retry_queue_size={stats['retry_queue_size_current']}"
            )

            # Сбросить счетчики
            with self._lock:
                self._stats["operations_queued"] = 0
                self._stats["operations_processed"] = 0
                self._stats["operations_failed"] = 0
                self._stats["operations_retried"] = 0

            self._last_flush = current_time

    def _periodic_maintenance(self) -> None:
        """
        Периодическое обслуживание DataCollectionManager.
        Выполняется каждые 10 секунд.
        """
        if not self._data_collection_manager:
            return

        current_time = time.time()
        maintenance_interval = 10.0  # 10 секунд

        if current_time - self._last_maintenance >= maintenance_interval:
            try:
                self._data_collection_manager.periodic_maintenance()
                logger.debug("Periodic maintenance executed")
            except Exception as e:
                logger.error(f"Error in periodic maintenance: {e}")

            self._last_maintenance = current_time

    def __enter__(self):
        """Контекстный менеджер - запуск."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - остановка."""
        self.stop()
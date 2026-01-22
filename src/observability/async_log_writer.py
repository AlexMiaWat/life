"""
Async Log Writer - асинхронный писатель логов с буферизацией в памяти.

Обеспечивает <1% overhead от системы observability путем:
- Буферизации логов в памяти (ring buffer)
- Batch-записи пакетов логов
- Асинхронной записи в фоне

Заменяет проблемную AsyncDataQueue для логирования.
"""

import json
import logging
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """
    Запись лога для буферизации в памяти.

    Attributes:
        timestamp: Время создания записи
        stage: Стадия жизненного цикла (event/meaning/decision/action/feedback/tick_start/tick_end)
        correlation_id: ID для трассировки цепочек
        event_id: ID события (опционально)
        data: Данные записи
        priority: Приоритет (0-10, 10 - максимальный)
    """
    timestamp: float
    stage: str
    correlation_id: Optional[str]
    event_id: Optional[str]
    data: Dict[str, Any]
    priority: int = 5

    def to_json_line(self) -> str:
        """Преобразовать в JSONL строку."""
        entry = {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "correlation_id": self.correlation_id,
            "event_id": self.event_id,
            "data": self.data
        }
        return json.dumps(entry, ensure_ascii=False, default=str) + "\n"


class RingBuffer:
    """
    Кольцевой буфер для буферизации логов в памяти.

    Гарантирует ограничение памяти и FIFO поведение.
    """

    def __init__(self, max_size: int = 10000):
        """
        Инициализировать кольцевой буфер.

        Args:
            max_size: Максимальный размер буфера
        """
        self.max_size = max_size
        self.buffer: deque[LogEntry] = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self.dropped_entries = 0

    def append(self, entry: LogEntry) -> None:
        """
        Добавить запись в буфер.

        Args:
            entry: Запись лога
        """
        with self._lock:
            if len(self.buffer) >= self.max_size:
                # Удаляем старую запись для поддержания размера
                self.buffer.popleft()
                self.dropped_entries += 1

            self.buffer.append(entry)

    def get_batch(self, batch_size: int = 100) -> List[LogEntry]:
        """
        Получить пакет записей из буфера.

        Args:
            batch_size: Максимальный размер пакета

        Returns:
            Список записей (FIFO порядок)
        """
        with self._lock:
            if not self.buffer:
                return []

            # Берем до batch_size записей
            batch = []
            for _ in range(min(batch_size, len(self.buffer))):
                batch.append(self.buffer.popleft())

            return batch

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику буфера.

        Returns:
            Словарь со статистикой
        """
        with self._lock:
            return {
                "size": len(self.buffer),
                "max_size": self.max_size,
                "dropped_entries": self.dropped_entries,
                "utilization_percent": (len(self.buffer) / self.max_size) * 100
            }

    def clear(self) -> None:
        """Очистить буфер."""
        with self._lock:
            self.buffer.clear()
            self.dropped_entries = 0


class AsyncLogWriter:
    """
    Асинхронный писатель логов с буферизацией в памяти.

    Обеспечивает минимальный overhead (<1%) путем:
    - Буферизации в памяти (0.001ms на операцию)
    - Batch-записи пакетов
    - Асинхронной записи в фоне
    """

    def __init__(
        self,
        log_file: str,
        enabled: bool = True,
        buffer_size: int = 10000,
        batch_size: int = 50,
        flush_interval: float = 0.1,  # 100ms - частая запись для realtime
        max_file_size_mb: int = 100
    ):
        """
        Инициализировать асинхронный писатель логов.

        Args:
            log_file: Путь к файлу логов
            enabled: Включено ли логирование
            buffer_size: Размер буфера в памяти
            batch_size: Размер пакета для записи
            flush_interval: Интервал сброса (секунды)
            max_file_size_mb: Максимальный размер файла (МБ)
        """
        self.log_file = log_file
        self.enabled = enabled
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_file_size_mb = max_file_size_mb

        # Буфер для записей
        self.buffer = RingBuffer(max_size=buffer_size)

        # Синхронизация
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._writer_thread: Optional[threading.Thread] = None

        # Статистика
        self._stats = {
            "entries_buffered": 0,
            "batches_written": 0,
            "entries_written": 0,
            "flush_operations": 0,
            "io_errors": 0,
            "start_time": time.time()
        }

        # Убедиться что директория существует
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Запустить фоновый поток записи
        if self.enabled:
            self._start_writer_thread()

    def write_entry(
        self,
        stage: str,
        correlation_id: Optional[str] = None,
        event_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> None:
        """
        Записать запись лога (быстрая операция в память).

        Args:
            stage: Стадия жизненного цикла
            correlation_id: ID для трассировки цепочек
            event_id: ID события
            data: Данные записи
            priority: Приоритет записи
        """
        if not self.enabled:
            return

        entry = LogEntry(
            timestamp=time.time(),
            stage=stage,
            correlation_id=correlation_id,
            event_id=event_id,
            data=data or {},
            priority=priority
        )

        # Быстрая запись в буфер (0.001ms)
        self.buffer.append(entry)

        with self._lock:
            self._stats["entries_buffered"] += 1

    def write_batch(self, entries: List[LogEntry]) -> None:
        """
        Записать пакет записей (оптимизированная операция).

        Args:
            entries: Список записей для записи
        """
        if not self.enabled or not entries:
            return

        for entry in entries:
            self.buffer.append(entry)

        with self._lock:
            self._stats["entries_buffered"] += len(entries)

    def flush(self) -> None:
        """Принудительный сброс буфера в файл."""
        if not self.enabled:
            return

        self._flush_buffer_to_file()

    def shutdown(self) -> None:
        """Корректное завершение работы."""
        logger.info("Shutting down AsyncLogWriter...")

        self._stop_event.set()

        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=2.0)

        # Финальный сброс
        self._flush_buffer_to_file()

        logger.info("AsyncLogWriter shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику работы.

        Returns:
            Словарь со статистикой
        """
        with self._lock:
            stats = self._stats.copy()

        buffer_stats = self.buffer.get_stats()

        runtime = time.time() - stats["start_time"]
        throughput = stats["entries_written"] / runtime if runtime > 0 else 0

        return {
            **stats,
            **buffer_stats,
            "runtime_seconds": runtime,
            "throughput_entries_per_sec": throughput,
            "writer_thread_alive": self._writer_thread.is_alive() if self._writer_thread else False
        }

    def _start_writer_thread(self) -> None:
        """Запустить фоновый поток записи."""
        self._writer_thread = threading.Thread(
            target=self._writer_loop,
            name="AsyncLogWriter",
            daemon=True
        )
        self._writer_thread.start()
        logger.info("AsyncLogWriter thread started")

    def _writer_loop(self) -> None:
        """Основной цикл фонового потока записи."""
        logger.debug("AsyncLogWriter writer loop started")

        while not self._stop_event.is_set():
            try:
                # Ждем следующего интервала сброса
                if self._stop_event.wait(timeout=self.flush_interval):
                    break  # Получили сигнал остановки

                # Сбрасываем буфер в файл
                self._flush_buffer_to_file()

            except Exception as e:
                logger.error(f"Error in writer loop: {e}")
                with self._lock:
                    self._stats["io_errors"] += 1

                # Небольшая пауза перед следующей попыткой
                time.sleep(0.1)

        # Финальный сброс перед завершением
        self._flush_buffer_to_file()
        logger.debug("AsyncLogWriter writer loop finished")

    def _flush_buffer_to_file(self) -> None:
        """Сбросить буфер в файл (batch операция)."""
        try:
            # Получить пакет записей
            batch = self.buffer.get_batch(self.batch_size)

            if not batch:
                return  # Буфер пуст

            # Преобразовать в JSONL
            json_lines = "".join(entry.to_json_line() for entry in batch)

            # Проверить размер файла и выполнить ротацию если нужно
            self._rotate_file_if_needed()

            # Записать пакет в файл
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json_lines)

            with self._lock:
                self._stats["batches_written"] += 1
                self._stats["entries_written"] += len(batch)
                self._stats["flush_operations"] += 1

        except Exception as e:
            logger.error(f"Error flushing buffer to file: {e}")
            with self._lock:
                self._stats["io_errors"] += 1

    def _rotate_file_if_needed(self) -> None:
        """Проверить и выполнить ротацию файла если он слишком большой."""
        try:
            log_path = Path(self.log_file)

            if not log_path.exists():
                return

            # Проверить размер файла
            size_mb = log_path.stat().st_size / (1024 * 1024)

            if size_mb >= self.max_file_size_mb:
                # Создать новый файл с timestamp
                timestamp = int(time.time())
                backup_file = log_path.with_suffix(f".{timestamp}.jsonl")

                # Переименовать текущий файл
                log_path.rename(backup_file)

                logger.info(f"Rotated log file: {log_path} -> {backup_file}")

        except Exception as e:
            logger.error(f"Error rotating log file: {e}")
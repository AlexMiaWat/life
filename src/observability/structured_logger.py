"""
Structured Logger for Life system observability.

Provides JSONL-formatted logging for key stages:
event → meaning → decision → action → feedback
"""

import json
import logging
import threading
import time
from typing import Any, Dict, Optional
from uuid import uuid4
from pathlib import Path

from src.config.observability_config import get_observability_config
from src.observability.async_log_writer import AsyncLogWriter

logger = logging.getLogger(__name__)




class StructuredLogger:
    """
    Structured logger for Life system observability.

    Logs key processing stages in JSONL format for analysis and debugging.
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        enabled: Optional[bool] = None,
        config=None,
        log_tick_interval: int = 10000,  # Увеличен до 10000 для <1% overhead (был 10)
        enable_detailed_logging: bool = False,  # Отключить детальное логирование для производительности
        buffer_size: int = 10000,  # Размер буфера в памяти
        batch_size: int = 50,  # Размер пакета для batch-записи
        flush_interval: float = 1.0  # Увеличен до 1s для лучшей производительности (был 0.1)
    ):
        """
        Initialize structured logger with AsyncLogWriter.

        Args:
            log_file: Path to JSONL log file (uses config if None)
            enabled: Whether logging is enabled (uses config if None)
            config: Observability config (loads from file if None)
            log_tick_interval: Интервал логирования тиков (каждый N-й тик)
            enable_detailed_logging: Включить детальное логирование всех этапов
            buffer_size: Размер буфера в памяти для AsyncLogWriter
            batch_size: Размер пакета для batch-записи
            flush_interval: Интервал сброса буфера (секунды)
        """
        if config is None:
            config = get_observability_config()

        self.log_file = log_file or config.structured_logging.log_file
        self.enabled = enabled if enabled is not None else config.structured_logging.enabled
        self.log_tick_interval = log_tick_interval
        self.enable_detailed_logging = enable_detailed_logging

        # Синхронизация
        self._lock = threading.Lock()
        self._correlation_counter = 0
        self._tick_counter = 0  # Счетчик тиков для интервального логирования

        # AsyncLogWriter для буферизации и batch-записи (<1% overhead)
        self._async_writer = AsyncLogWriter(
            log_file=self.log_file,
            enabled=self.enabled,
            buffer_size=buffer_size,
            batch_size=batch_size,
            flush_interval=flush_interval
        )

    def _get_next_correlation_id(self) -> str:
        """Get next correlation ID for tracing chains."""
        with self._lock:
            self._correlation_counter += 1
            # Prevent counter overflow (wrap around after 1 billion)
            if self._correlation_counter > 1000000000:
                self._correlation_counter = 1
            return f"chain_{self._correlation_counter}"

    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Write a single log entry via AsyncLogWriter (ultra-fast in-memory buffering)."""
        if not self.enabled:
            return

        # Быстрая запись в буфер памяти (0.001ms) - <1% overhead
        self._async_writer.write_entry(
            stage=entry.get("stage", "unknown"),
            correlation_id=entry.get("correlation_id"),
            event_id=entry.get("event_id"),
            data=entry.get("data", {})
        )

    def log_event(self, event: Any, correlation_id: Optional[str] = None) -> str:
        """
        Log event stage.

        Args:
            event: Event object to log
            correlation_id: Correlation ID for tracing (generated if None)

        Returns:
            Correlation ID for this event chain
        """
        if correlation_id is None:
            correlation_id = self._get_next_correlation_id()

        entry = {
            "timestamp": time.time(),
            "stage": "event",
            "correlation_id": correlation_id,
            "event_id": getattr(event, "id", str(uuid4())),
            "event_type": getattr(event, "type", "unknown"),
            "intensity": getattr(event, "intensity", 0.0),
            "data": getattr(event, "data", {}),
        }

        self._write_log_entry(entry)
        return correlation_id

    def log_meaning(self, event: Any, meaning: Any, correlation_id: str) -> None:
        """
        Log meaning processing stage.

        Args:
            event: Original event
            meaning: Meaning object from MeaningEngine
            correlation_id: Correlation ID from event stage
        """
        # Пропускаем детальное логирование если отключено
        if not self.enable_detailed_logging:
            return

        # Убираем derived metrics (significance, impact) - логируем только факт обработки
        entry = {
            "timestamp": time.time(),
            "stage": "meaning",
            "correlation_id": correlation_id,
            "event_id": getattr(event, "id", str(uuid4())),
            "event_type": getattr(event, "type", "unknown"),
            "data": {
                "meaning_type": type(meaning).__name__,
                "processed": True,  # Только факт обработки, без интерпретации
            },
        }

        self._write_log_entry(entry)

    def log_decision(self, correlation_id: str) -> None:
        """
        Log decision stage.

        Args:
            correlation_id: Correlation ID from event chain
        """
        # Пропускаем детальное логирование если отключено
        if not self.enable_detailed_logging:
            return

        # Убираем derived metrics (pattern, additional_data) - логируем только факт принятия решения
        entry = {
            "timestamp": time.time(),
            "stage": "decision",
            "correlation_id": correlation_id,
            "data": {
                "decision_made": True,  # Только факт принятия решения
            },
        }

        self._write_log_entry(entry)

    def log_action(self, action_id: str, correlation_id: str) -> None:
        """
        Log action execution stage.

        Args:
            action_id: Unique action identifier
            correlation_id: Correlation ID from event chain
        """
        # Пропускаем детальное логирование если отключено
        if not self.enable_detailed_logging:
            return

        # Убираем derived metrics (pattern, state_before) - логируем только факт выполнения действия
        entry = {
            "timestamp": time.time(),
            "stage": "action",
            "correlation_id": correlation_id,
            "action_id": action_id,
            "data": {
                "action_executed": True,  # Только факт выполнения
            },
        }

        self._write_log_entry(entry)

    def log_feedback(self, feedback: Any, correlation_id: str) -> None:
        """
        Log feedback observation stage.

        Args:
            feedback: Feedback object from observe_consequences
            correlation_id: Correlation ID from action chain
        """
        # Убираем derived metrics - логируем только факт получения обратной связи
        entry = {
            "timestamp": time.time(),
            "stage": "feedback",
            "correlation_id": correlation_id,
            "data": {
                "feedback_received": True,  # Только факт получения обратной связи
                "feedback_type": type(feedback).__name__,
            },
        }

        self._write_log_entry(entry)

    def log_tick_start(self, tick_number: int, queue_size: int) -> None:
        """
        Log start of a tick for performance monitoring.
        Логируется только каждый N-й тик для оптимизации производительности.

        Args:
            tick_number: Current tick number
            queue_size: Size of event queue
        """
        with self._lock:
            self._tick_counter += 1

        # Логируем только каждый N-й тик для снижения overhead
        if self._tick_counter % self.log_tick_interval != 0:
            return

        entry = {
            "timestamp": time.time(),
            "stage": "tick_start",
            "tick_number": tick_number,
            "queue_size": queue_size,
            "data": {},
        }

        self._write_log_entry(entry)

    def log_tick_end(self, tick_number: int) -> None:
        """
        Log end of a tick - only raw counter (tick_number).

        According to ADR 001 "Passive Observation Boundaries", we only collect
        raw counters without any derived metrics like duration_ms or events_processed.

        Args:
            tick_number: Current tick number (raw counter)
        """
        entry = {
            "timestamp": time.time(),
            "stage": "tick_end",
            "tick_number": tick_number,
            "data": {},
        }

        self._write_log_entry(entry)

    def log_error(self, stage: str, error: Exception, correlation_id: Optional[str] = None) -> None:
        """
        Log errors in processing stages.

        Args:
            stage: Stage where error occurred
            error: Exception object
            correlation_id: Correlation ID if available
        """
        entry = {
            "timestamp": time.time(),
            "stage": f"error_{stage}",
            "correlation_id": correlation_id or "system_error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "data": {},
        }

        self._write_log_entry(entry)

    def log_adaptation_rollback(
        self,
        rollback_result: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Log adaptation rollback operation.

        Args:
            rollback_result: Result from rollback operation
            correlation_id: Correlation ID for tracing
        """
        if correlation_id is None:
            correlation_id = self._get_next_correlation_id()

        entry = {
            "timestamp": time.time(),
            "stage": "adaptation_rollback",
            "correlation_id": correlation_id,
            "success": rollback_result.get("success", False),
            "target_timestamp": rollback_result.get("target_timestamp"),
            "actual_timestamp": rollback_result.get("actual_timestamp"),
            "tick": rollback_result.get("tick"),
            "error": rollback_result.get("error"),
            "rolled_back_params": rollback_result.get("rolled_back_params"),
        }

        self._write_log_entry(entry)

    def shutdown(self) -> None:
        """Shutdown the structured logger and cleanup resources."""
        logger.info("Shutting down StructuredLogger...")
        if hasattr(self, '_async_writer') and self._async_writer:
            self._async_writer.shutdown()
        logger.info("StructuredLogger shutdown complete")

    def flush(self) -> None:
        """Force flush all buffered log entries to disk."""
        if hasattr(self, '_async_writer') and self._async_writer:
            self._async_writer.flush()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.

        Returns:
            Dictionary with logging statistics
        """
        if hasattr(self, '_async_writer') and self._async_writer:
            return self._async_writer.get_stats()
        else:
            return {
                "enabled": self.enabled,
                "correlation_counter": self._correlation_counter,
                "tick_counter": self._tick_counter
            }

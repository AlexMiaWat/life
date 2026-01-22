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

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout exception for thread-safe timeouts."""
    pass


def timeout_context(seconds: float):
    """
    Context manager for operation timeouts using threading.Timer.

    Args:
        seconds: Timeout in seconds

    Returns:
        Context manager
    """
    class TimeoutContext:
        def __init__(self, timeout_seconds: float):
            self.timeout_seconds = timeout_seconds
            self.timer = None

        def __enter__(self):
            self.timer = threading.Timer(self.timeout_seconds, self._timeout)
            self.timer.start()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.timer:
                self.timer.cancel()

        def _timeout(self):
            raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")

    return TimeoutContext(seconds)


class StructuredLogger:
    """
    Structured logger for Life system observability.

    Logs key processing stages in JSONL format for analysis and debugging.
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        enabled: Optional[bool] = None,
        config=None
    ):
        """
        Initialize structured logger.

        Args:
            log_file: Path to JSONL log file (uses config if None)
            enabled: Whether logging is enabled (uses config if None)
            config: Observability config (loads from file if None)
        """
        if config is None:
            config = get_observability_config()

        self.log_file = log_file or config.structured_logging.log_file
        self.enabled = enabled if enabled is not None else config.structured_logging.enabled
        self._lock = threading.Lock()
        self._correlation_counter = 0

        # Убедиться что директория существует
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_next_correlation_id(self) -> str:
        """Get next correlation ID for tracing chains."""
        with self._lock:
            self._correlation_counter += 1
            # Prevent counter overflow (wrap around after 1 billion)
            if self._correlation_counter > 1000000000:
                self._correlation_counter = 1
            return f"chain_{self._correlation_counter}"

    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Write a single log entry to the file with timeout and graceful error handling."""
        if not self.enabled:
            return

        try:
            with self._lock:
                # Ensure directory exists with timeout
                with timeout_context(0.5):  # 500ms timeout for directory operations
                    log_path = Path(self.log_file)
                    log_path.parent.mkdir(parents=True, exist_ok=True)

                # Write entry with timeout
                with timeout_context(0.2):  # 200ms timeout for file write
                    with open(self.log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
                        f.flush()  # Ensure data is written

        except TimeoutError as e:
            logger.warning(f"Timeout during structured logging: {e}")
            # Graceful degradation: skip this entry but keep logging enabled
        except (OSError, IOError) as e:
            logger.warning(f"Failed to write structured log entry (I/O error): {e}")
            # Try fallback logging
            self._try_fallback_logging(entry)
            # Disable logging temporarily to prevent spam
            self.enabled = False
            logger.error("Structured logging disabled due to persistent I/O errors")
        except Exception as e:
            logger.warning(f"Failed to write structured log entry (unexpected error): {e}")
            # Try fallback logging but keep main logging enabled
            self._try_fallback_logging(entry)

    def _try_fallback_logging(self, entry: Dict[str, Any]) -> None:
        """
        Attempt fallback logging when primary logging fails.

        Args:
            entry: Log entry to store
        """
        try:
            # Try to log to system temp directory as fallback
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "life_structured_logs_fallback"
            temp_dir.mkdir(exist_ok=True)

            fallback_file = temp_dir / f"fallback_{int(time.time())}.json"
            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, default=str)

            logger.info(f"Log entry stored in fallback location: {fallback_file}")

        except Exception as fallback_error:
            logger.error(f"Fallback logging also failed: {fallback_error}")
            # Final graceful degradation: log entry is lost but system continues

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

        Args:
            tick_number: Current tick number
            queue_size: Size of event queue
        """
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

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

logger = logging.getLogger(__name__)


class StructuredLogger:
    """
    Structured logger for Life system observability.

    Logs key processing stages in JSONL format for analysis and debugging.
    """

    def __init__(self, log_file: str = "data/structured_log.jsonl", enabled: bool = True):
        """
        Initialize structured logger.

        Args:
            log_file: Path to JSONL log file
            enabled: Whether logging is enabled (for performance control)
        """
        self.log_file = log_file
        self.enabled = enabled
        self._lock = threading.Lock()
        self._correlation_counter = 0

    def _get_next_correlation_id(self) -> str:
        """Get next correlation ID for tracing chains."""
        with self._lock:
            self._correlation_counter += 1
            return f"chain_{self._correlation_counter}"

    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Write a single log entry to the file."""
        if not self.enabled:
            return

        try:
            with self._lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write structured log entry: {e}")

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
        entry = {
            "timestamp": time.time(),
            "stage": "meaning",
            "correlation_id": correlation_id,
            "event_id": getattr(event, "id", str(uuid4())),
            "event_type": getattr(event, "type", "unknown"),
            "significance": getattr(meaning, "significance", 0.0),
            "impact": getattr(meaning, "impact", {}),
            "data": {
                "meaning_type": type(meaning).__name__,
                "has_impact": bool(getattr(meaning, "impact", {})),
            },
        }

        self._write_log_entry(entry)

    def log_decision(
        self, pattern: str, correlation_id: str, additional_data: Optional[Dict] = None
    ) -> None:
        """
        Log decision stage.

        Args:
            pattern: Decision pattern (ignore/dampen/absorb)
            correlation_id: Correlation ID from event chain
            additional_data: Additional decision context
        """
        entry = {
            "timestamp": time.time(),
            "stage": "decision",
            "correlation_id": correlation_id,
            "pattern": pattern,
            "data": additional_data or {},
        }

        self._write_log_entry(entry)

    def log_action(
        self,
        action_id: str,
        pattern: str,
        correlation_id: str,
        state_before: Optional[Dict] = None,
    ) -> None:
        """
        Log action execution stage.

        Args:
            action_id: Unique action identifier
            pattern: Action pattern executed
            correlation_id: Correlation ID from event chain
            state_before: State snapshot before action
        """
        entry = {
            "timestamp": time.time(),
            "stage": "action",
            "correlation_id": correlation_id,
            "action_id": action_id,
            "pattern": pattern,
            "data": {
                "state_before": state_before or {},
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
        entry = {
            "timestamp": time.time(),
            "stage": "feedback",
            "correlation_id": correlation_id,
            "action_id": getattr(feedback, "action_id", "unknown"),
            "delay_ticks": getattr(feedback, "delay_ticks", 0),
            "data": {
                "state_delta": getattr(feedback, "state_delta", {}),
                "associated_events": getattr(feedback, "associated_events", []),
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

    def log_tick_end(self, tick_number: int, duration_ms: float, events_processed: int) -> None:
        """
        Log end of a tick for performance monitoring.

        Args:
            tick_number: Current tick number
            duration_ms: Tick duration in milliseconds
            events_processed: Number of events processed this tick
        """
        entry = {
            "timestamp": time.time(),
            "stage": "tick_end",
            "tick_number": tick_number,
            "duration_ms": duration_ms,
            "events_processed": events_processed,
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

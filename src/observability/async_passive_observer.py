"""
Passive Data Sink for Life system.

Provides truly passive data collection without any active polling or timing.
Only accepts data when explicitly provided or when external events occur.
"""

import json
import logging
import time
import signal
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager

from src.config.observability_config import get_observability_config

logger = logging.getLogger(__name__)


@contextmanager
def timeout_context(seconds: float):
    """
    Context manager for operation timeouts.

    Args:
        seconds: Timeout in seconds
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))
    try:
        yield
    finally:
        signal.alarm(0)


class PassiveDataSink:
    """
    Passive data sink for Life system observability.

    Only accepts data when explicitly provided. No active polling,
    no timing, no background threads. Truly passive observation.
    """

    def __init__(
        self,
        data_directory: Optional[str] = None,
        enabled: Optional[bool] = None,
        config=None
    ):
        """
        Initialize passive data sink.

        Args:
            data_directory: Directory for storing observation data (uses config if None)
            enabled: Whether data sink is enabled (uses config if None)
            config: Observability config (loads from file if None)
        """
        if config is None:
            config = get_observability_config()

        self.data_dir = Path(data_directory or config.passive_data_sink.data_directory)
        self.enabled = enabled if enabled is not None else config.passive_data_sink.enabled

        # Убедиться что директория существует
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def accept_data_point(self, data: Dict[str, Any]) -> bool:
        """
        Accept a single data point for storage.

        Args:
            data: Raw data point to store

        Returns:
            True if data was accepted and stored, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = time.time()

            # Store the data point
            self._store_data_point(data)
            logger.debug("Accepted passive data point")
            return True

        except Exception as e:
            logger.warning(f"Failed to accept data point: {e}")
            return False

    def accept_snapshot_data(self, snapshot_data: Dict[str, Any]) -> bool:
        """
        Accept snapshot data for observation.

        Args:
            snapshot_data: Raw snapshot data

        Returns:
            True if snapshot was accepted and stored
        """
        if not self.enabled:
            return False

        try:
            observation = self._create_observation_from_snapshot(snapshot_data)
            return self.accept_data_point(observation)

        except Exception as e:
            logger.warning(f"Failed to accept snapshot data: {e}")
            return False

    def _create_observation_from_snapshot(self, snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create observation record from snapshot data.

        Args:
            snapshot_data: Raw snapshot data

        Returns:
            Observation record
        """
        # Extract raw data without interpretation
        record = {
            "timestamp": time.time(),
            "observation_type": "snapshot_observation",
            "snapshot_timestamp": snapshot_data.get("timestamp"),
            "raw_data": snapshot_data  # Store raw snapshot as-is
        }

        return record

    def _store_data_point(self, data: Dict[str, Any]) -> None:
        """
        Store data point to persistent storage with timeout and error handling.

        Args:
            data: Data point to store
        """
        try:
            # Create directory with timeout protection
            with timeout_context(1.0):  # 1 second timeout for directory creation
                observations_file = self.data_dir / "passive_observations.jsonl"
                observations_file.parent.mkdir(parents=True, exist_ok=True)

            # Write data with timeout protection
            with timeout_context(0.5):  # 500ms timeout for file write
                with open(observations_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")
                    f.flush()  # Ensure data is written

        except TimeoutError as e:
            logger.warning(f"Timeout during data storage: {e}")
            # Graceful degradation: data not stored but operation continues
        except (OSError, IOError) as e:
            logger.warning(f"Failed to store data point (I/O error): {e}")
            # Try fallback: write to temporary location if possible
            self._try_fallback_storage(data)
        except Exception as e:
            logger.warning(f"Failed to store data point (unexpected error): {e}")
            # Try fallback storage
            self._try_fallback_storage(data)

    def _try_fallback_storage(self, data: Dict[str, Any]) -> None:
        """
        Attempt fallback storage when primary storage fails.

        Args:
            data: Data point to store
        """
        try:
            # Try to store in system temp directory as fallback
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "life_observability_fallback"
            temp_dir.mkdir(exist_ok=True)

            fallback_file = temp_dir / f"fallback_{int(time.time())}.json"
            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, default=str)

            logger.info(f"Data stored in fallback location: {fallback_file}")

        except Exception as fallback_error:
            logger.error(f"Fallback storage also failed: {fallback_error}")
            # Final graceful degradation: data is lost but system continues

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of data sink.

        Returns:
            Status information
        """
        observations_file = self.data_dir / "passive_observations.jsonl"

        status = {
            "enabled": self.enabled,
            "data_directory": str(self.data_dir),
            "observations_file_exists": observations_file.exists()
        }

        if observations_file.exists():
            try:
                status["observations_file_size_bytes"] = observations_file.stat().st_size
                status["observations_file_age_seconds"] = time.time() - observations_file.stat().st_mtime
            except Exception as e:
                logger.warning(f"Failed to get file stats: {e}")

        return status

    def enable(self):
        """Enable the data sink."""
        self.enabled = True
        logger.info("PassiveDataSink enabled")

    def disable(self):
        """Disable the data sink."""
        self.enabled = False
        logger.info("PassiveDataSink disabled")


# Backward compatibility alias
AsyncPassiveObserver = PassiveDataSink
"""
Async Passive Observer for Life system.

Provides truly passive observation without any runtime loop interference.
Uses separate thread for periodic data collection from external sources.
"""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AsyncPassiveObserver:
    """
    Asynchronous passive observer for Life system.

    Collects data periodically without interfering with runtime loop.
    Logs observation data directly to JSONL file for analysis.
    """

    def __init__(
        self,
        collection_interval: float = 300.0,  # 5 minutes default
        snapshots_dir: str = "data/snapshots",
        log_file: str = "data/passive_observations.jsonl",
        enabled: bool = True
    ):
        """
        Initialize async passive observer.

        Args:
            collection_interval: How often to collect data (seconds)
            snapshots_dir: Directory with snapshot files
            log_file: Path to observation log file
            enabled: Whether observer is enabled
        """
        self.collection_interval = collection_interval
        self.snapshots_dir = snapshots_dir
        self.log_file = log_file
        self.enabled = enabled

        # Threading
        self._observer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Start observer thread if enabled
        if self.enabled:
            self._start_observer_thread()

    def _start_observer_thread(self):
        """Start the background observer thread."""
        if self._observer_thread and self._observer_thread.is_alive():
            return

        self._stop_event.clear()
        self._observer_thread = threading.Thread(
            target=self._observer_loop,
            name="AsyncPassiveObserver",
            daemon=True
        )
        self._observer_thread.start()
        logger.info(f"AsyncPassiveObserver started with {self.collection_interval}s interval")

    def _observer_loop(self):
        """Main observer loop - runs in background thread."""
        while not self._stop_event.is_set():
            try:
                self._collect_data_point()
                # Wait for next collection interval or stop event
                self._stop_event.wait(timeout=self.collection_interval)

            except Exception as e:
                logger.error(f"Error in observer loop: {e}")
                # Brief pause before retry
                self._stop_event.wait(timeout=1.0)

    def _collect_data_point(self):
        """
        Collect a single data point from available sources.

        This method attempts to collect data from external sources without
        accessing runtime objects directly.
        """
        try:
            # Try to load latest snapshot from file
            latest_snapshot = self._load_latest_snapshot()
            if latest_snapshot:
                # Create observation record
                observation = self._create_observation_record(latest_snapshot)
                self._log_observation(observation)
                logger.debug("Collected passive observation data point")

        except Exception as e:
            logger.warning(f"Failed to collect passive observation data: {e}")

    def _create_observation_record(self, snapshot_data: dict) -> Dict[str, Any]:
        """
        Create an observation record from snapshot data.

        Args:
            snapshot_data: Raw snapshot data

        Returns:
            Observation record for logging
        """
        # Extract key metrics from snapshot
        record = {
            "timestamp": time.time(),
            "observation_type": "passive_snapshot",
            "snapshot_timestamp": snapshot_data.get("timestamp"),
            "system_state": {
                "energy": snapshot_data.get("energy", 0.0),
                "stability": snapshot_data.get("stability", 0.0),
                "integrity": snapshot_data.get("integrity", 0.0),
                "fatigue": snapshot_data.get("fatigue", 0.0),
                "tension": snapshot_data.get("tension", 0.0),
                "age": snapshot_data.get("age", 0),
                "ticks": snapshot_data.get("ticks", 0),
            },
            "memory": {
                "episodic_size": snapshot_data.get("memory_episodic_size", 0),
                "archive_size": snapshot_data.get("memory_archive_size", 0),
                "recent_events": snapshot_data.get("memory_recent_events", 0),
            },
            "processing": {
                "learning_params": snapshot_data.get("learning_params_count", 0),
                "adaptation_params": snapshot_data.get("adaptation_params_count", 0),
                "decision_queue": snapshot_data.get("decision_queue_size", 0),
                "action_queue": snapshot_data.get("action_queue_size", 0),
            }
        }

        return record

    def _log_observation(self, observation: Dict[str, Any]) -> None:
        """
        Log observation record to JSONL file.

        Args:
            observation: Observation record to log
        """
        if not self.enabled:
            return

        try:
            with self._lock:
                # Ensure directory exists
                log_path = Path(self.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(observation, ensure_ascii=False, default=str) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write observation log entry: {e}")

    def _load_latest_snapshot(self) -> Optional[dict]:
        """
        Load the latest snapshot from snapshots directory.

        Returns:
            Latest snapshot data or None if not available
        """
        try:
            snapshots_path = Path(self.snapshots_dir)

            # Check if directory exists and is readable
            if not snapshots_path.exists():
                logger.debug(f"Snapshots directory does not exist: {snapshots_path}")
                return None

            if not snapshots_path.is_dir():
                logger.warning(f"Snapshots path is not a directory: {snapshots_path}")
                return None

            # Find JSON snapshot files
            snapshot_files = list(snapshots_path.glob("*.json"))
            if not snapshot_files:
                logger.debug("No snapshot files found")
                return None

            # Get latest file by modification time
            latest_file = max(snapshot_files, key=lambda f: f.stat().st_mtime)

            # Check file size (prevent loading huge files)
            file_size = latest_file.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                logger.warning(f"Snapshot file too large: {file_size} bytes")
                return None
            if file_size == 0:
                logger.warning("Snapshot file is empty")
                return None

            # Load the snapshot
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Basic validation
            if not isinstance(data, dict):
                logger.warning("Snapshot is not a valid JSON object")
                return None

            if 'timestamp' not in data:
                logger.warning("Snapshot missing timestamp field")
                return None

            return data

        except Exception as e:
            logger.warning(f"Failed to load latest snapshot: {e}")
            return None

    def get_status(self) -> dict:
        """Get observer status."""
        log_file_exists = Path(self.log_file).exists()
        log_file_size = 0
        if log_file_exists:
            try:
                log_file_size = Path(self.log_file).stat().st_size
            except:
                pass

        return {
            "enabled": self.enabled,
            "collection_interval": self.collection_interval,
            "log_file": self.log_file,
            "log_file_exists": log_file_exists,
            "log_file_size_bytes": log_file_size,
            "thread_alive": self._observer_thread.is_alive() if self._observer_thread else False,
            "snapshots_dir": self.snapshots_dir
        }

    def enable(self):
        """Enable passive observation."""
        self.enabled = True
        self._start_observer_thread()

    def disable(self):
        """Disable passive observation."""
        self.enabled = False

    def shutdown(self, timeout: float = 5.0):
        """Shutdown the observer gracefully."""
        logger.info("Shutting down AsyncPassiveObserver")
        self._stop_event.set()
        self.enabled = False

        if self._observer_thread and self._observer_thread.is_alive():
            self._observer_thread.join(timeout=timeout)

        logger.info("AsyncPassiveObserver shutdown complete")
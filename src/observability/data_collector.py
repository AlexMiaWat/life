"""
Data Collector for Life system observation.

Collects and stores raw observation data without interpretation.
Provides basic storage and retrieval functionality.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ObservationData:
    """Container for collected observation data."""

    timestamp: float = field(default_factory=time.time)
    data_type: str = ""  # 'state' or 'component'
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'data_type': self.data_type,
            'data': self.data,
        }


class DataCollector:
    """
    Collector and storage for observation data.

    Stores raw data without interpretation or analysis.
    """

    def __init__(self, storage_path: str = "data/observation_data.jsonl"):
        """
        Initialize data collector.

        Args:
            storage_path: Path to JSONL file for data storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(exist_ok=True)
        self.collection_enabled = True
        self._buffer: List[ObservationData] = []
        self._buffer_size = 100  # Flush buffer when reaches this size

    def collect_state_data(self, state_snapshot) -> None:
        """
        Collect state snapshot data.

        Args:
            state_snapshot: StateSnapshot instance
        """
        if not self.collection_enabled:
            return

        try:
            observation = ObservationData(
                data_type="state",
                data=state_snapshot.to_dict()
            )
            self._add_to_buffer(observation)
        except Exception as e:
            logger.warning(f"Failed to collect state data: {e}")

    def collect_component_data(self, component_stats) -> None:
        """
        Collect component statistics data.

        Args:
            component_stats: SystemComponentStats instance
        """
        if not self.collection_enabled:
            return

        try:
            observation = ObservationData(
                data_type="component",
                data=component_stats.to_dict()
            )
            self._add_to_buffer(observation)
        except Exception as e:
            logger.warning(f"Failed to collect component data: {e}")

    def _add_to_buffer(self, observation: ObservationData) -> None:
        """
        Add observation to buffer and flush if needed.

        Args:
            observation: ObservationData to add
        """
        self._buffer.append(observation)

        if len(self._buffer) >= self._buffer_size:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffer to storage file."""
        if not self._buffer:
            return

        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                for observation in self._buffer:
                    json.dump(observation.to_dict(), f, ensure_ascii=False)
                    f.write('\n')
            self._buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush observation buffer: {e}")

    def get_recent_data(self, data_type: Optional[str] = None, limit: int = 100) -> List[ObservationData]:
        """
        Get recent observation data.

        Args:
            data_type: Filter by data type ('state' or 'component')
            limit: Maximum number of records to return

        Returns:
            List of recent ObservationData
        """
        try:
            if not self.storage_path.exists():
                return []

            data = []
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if data_type is None or record.get('data_type') == data_type:
                            observation = ObservationData(
                                timestamp=record.get('timestamp', 0),
                                data_type=record.get('data_type', ''),
                                data=record.get('data', {})
                            )
                            data.append(observation)
                            if len(data) >= limit:
                                break

            # Include buffer data
            for observation in self._buffer[-limit:]:
                if data_type is None or observation.data_type == data_type:
                    data.append(observation)

            return data[-limit:]  # Return most recent

        except Exception as e:
            logger.warning(f"Failed to read observation data: {e}")
            return []

    def get_data_count(self, data_type: Optional[str] = None) -> int:
        """
        Get count of stored data records.

        Args:
            data_type: Filter by data type

        Returns:
            Number of records
        """
        try:
            count = 0

            # Count records in storage file
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            if data_type is None or record.get('data_type') == data_type:
                                count += 1

            # Add buffer count
            for observation in self._buffer:
                if data_type is None or observation.data_type == data_type:
                    count += 1

            return count

        except Exception as e:
            logger.warning(f"Failed to count observation data: {e}")
            return 0

    def clear_data(self) -> None:
        """Clear all stored data."""
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
            self._buffer.clear()
        except Exception as e:
            logger.error(f"Failed to clear observation data: {e}")

    def enable_collection(self):
        """Enable data collection."""
        self.collection_enabled = True

    def disable_collection(self):
        """Disable data collection."""
        self.collection_enabled = False

    def flush(self) -> None:
        """Force flush buffer to storage."""
        self._flush_buffer()
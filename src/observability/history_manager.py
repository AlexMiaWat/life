"""
History Manager for Life system observation.

Manages time series data storage and retrieval without interpretation.
Provides basic time-based data organization.
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """Single entry in the history time series."""

    timestamp: float = field(default_factory=time.time)
    component: str = ""  # 'state' or component name
    action: str = ""     # 'snapshot', 'create', 'update', 'delete'
    old_value: Any = None
    new_value: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'component': self.component,
            'action': self.action,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'metadata': self.metadata,
        }


class HistoryManager:
    """
    Manager for time series history data.

    Stores raw history entries without analysis or interpretation.
    """

    def __init__(self, storage_path: str = "data/history_data.jsonl", max_entries: int = 10000):
        """
        Initialize history manager.

        Args:
            storage_path: Path to JSONL file for history storage
            max_entries: Maximum number of entries to keep in memory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(exist_ok=True)
        self.max_entries = max_entries
        self._entries: List[HistoryEntry] = []
        self._component_index: Dict[str, List[int]] = defaultdict(list)  # component -> list of indices
        self.collection_enabled = True

    def add_entry(self, entry: HistoryEntry) -> None:
        """
        Add history entry to storage.

        Args:
            entry: HistoryEntry to add
        """
        if not self.collection_enabled:
            return

        try:
            # Add to memory buffer
            self._entries.append(entry)
            self._component_index[entry.component].append(len(self._entries) - 1)

            # Maintain size limits
            if len(self._entries) > self.max_entries:
                # Remove oldest entries
                removed_count = len(self._entries) - self.max_entries
                self._entries = self._entries[removed_count:]

                # Rebuild index
                self._rebuild_index()

            # Periodic flush to disk
            if len(self._entries) % 100 == 0:  # Flush every 100 entries
                self._flush_to_disk()

        except Exception as e:
            logger.warning(f"Failed to add history entry: {e}")

    def add_state_change(self, component: str, old_value: Any, new_value: Any,
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add state change entry.

        Args:
            component: Component name
            old_value: Previous value
            new_value: New value
            metadata: Additional metadata
        """
        entry = HistoryEntry(
            component=component,
            action="state_change",
            old_value=old_value,
            new_value=new_value,
            metadata=metadata or {}
        )
        self.add_entry(entry)

    def add_snapshot(self, component: str, data: Dict[str, Any],
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add snapshot entry.

        Args:
            component: Component name
            data: Snapshot data
            metadata: Additional metadata
        """
        entry = HistoryEntry(
            component=component,
            action="snapshot",
            new_value=data,
            metadata=metadata or {}
        )
        self.add_entry(entry)

    def get_entries(self, component: Optional[str] = None, limit: int = 100,
                   start_time: Optional[float] = None, end_time: Optional[float] = None) -> List[HistoryEntry]:
        """
        Get history entries with optional filtering.

        Args:
            component: Filter by component name
            limit: Maximum number of entries to return
            start_time: Filter entries after this timestamp
            end_time: Filter entries before this timestamp

        Returns:
            List of matching HistoryEntry objects
        """
        try:
            # Start with all entries or component-specific entries
            if component:
                indices = self._component_index.get(component, [])
                candidates = [self._entries[i] for i in indices]
            else:
                candidates = self._entries

            # Apply time filters
            if start_time is not None:
                candidates = [e for e in candidates if e.timestamp >= start_time]
            if end_time is not None:
                candidates = [e for e in candidates if e.timestamp <= end_time]

            # Sort by timestamp (newest first) and limit
            candidates.sort(key=lambda e: e.timestamp, reverse=True)
            return candidates[:limit]

        except Exception as e:
            logger.warning(f"Failed to get history entries: {e}")
            return []

    def get_component_stats(self, component: str, start_time: Optional[float] = None,
                           end_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Get basic statistics for a component.

        Args:
            component: Component name
            start_time: Start time for statistics
            end_time: End time for statistics

        Returns:
            Dictionary with basic counts and statistics
        """
        entries = self.get_entries(component=component, limit=self.max_entries,
                                  start_time=start_time, end_time=end_time)

        stats = {
            'component': component,
            'total_entries': len(entries),
            'actions': defaultdict(int),
            'time_range': None,
        }

        if entries:
            timestamps = [e.timestamp for e in entries]
            stats['time_range'] = {
                'start': min(timestamps),
                'end': max(timestamps),
                'duration': max(timestamps) - min(timestamps)
            }

            for entry in entries:
                stats['actions'][entry.action] += 1

        return dict(stats)  # Convert defaultdict to regular dict

    def get_recent_activity(self, minutes: int = 60) -> List[HistoryEntry]:
        """
        Get entries from the last N minutes.

        Args:
            minutes: Number of minutes to look back

        Returns:
            List of recent entries
        """
        start_time = time.time() - (minutes * 60)
        return self.get_entries(start_time=start_time, limit=self.max_entries)

    def export_to_json(self, filepath: str, component: Optional[str] = None,
                      start_time: Optional[float] = None, end_time: Optional[float] = None) -> Optional[str]:
        """
        Export history data to JSON file.

        Args:
            filepath: Path to output JSON file
            component: Filter by component
            start_time: Start time filter
            end_time: End time filter

        Returns:
            Path to exported file or None if failed
        """
        try:
            entries = self.get_entries(component=component, limit=self.max_entries,
                                      start_time=start_time, end_time=end_time)

            data = {
                'export_time': time.time(),
                'total_entries': len(entries),
                'component_filter': component,
                'time_filters': {
                    'start_time': start_time,
                    'end_time': end_time
                },
                'entries': [entry.to_dict() for entry in entries]
            }

            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(entries)} history entries to {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to export history data: {e}")
            return None

    def clear_history(self, component: Optional[str] = None) -> None:
        """
        Clear history data.

        Args:
            component: Clear only specific component (None for all)
        """
        try:
            if component:
                # Remove entries for specific component
                self._entries = [e for e in self._entries if e.component != component]
                self._component_index.pop(component, None)
                self._rebuild_index()
            else:
                # Clear all
                self._entries.clear()
                self._component_index.clear()

            # Clear disk storage
            if self.storage_path.exists():
                self.storage_path.unlink()

        except Exception as e:
            logger.error(f"Failed to clear history: {e}")

    def _rebuild_index(self) -> None:
        """Rebuild component index after entries modification."""
        self._component_index = defaultdict(list)
        for i, entry in enumerate(self._entries):
            self._component_index[entry.component].append(i)

    def _flush_to_disk(self) -> None:
        """Flush current entries to disk storage."""
        if not self._entries:
            return

        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                for entry in self._entries[-100:]:  # Flush last 100 entries
                    json.dump(entry.to_dict(), f, ensure_ascii=False)
                    f.write('\n')
        except Exception as e:
            logger.warning(f"Failed to flush history to disk: {e}")

    def enable_collection(self):
        """Enable history collection."""
        self.collection_enabled = True

    def disable_collection(self):
        """Disable history collection."""
        self.collection_enabled = False
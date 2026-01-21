"""
Component Monitor for Life system.

Monitors component statistics without interpretation.
Tracks sizes, counts, and basic operational data.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ComponentStats:
    """Raw statistics for a single component."""

    component_name: str
    timestamp: float = field(default_factory=time.time)

    # Size metrics
    queue_size: int = 0
    memory_usage: int = 0
    active_threads: int = 0

    # Operation counters
    operations_count: int = 0
    error_count: int = 0
    success_count: int = 0

    # Timing metrics
    avg_operation_time: float = 0.0
    last_operation_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            'component_name': self.component_name,
            'timestamp': self.timestamp,
            'queue_size': self.queue_size,
            'memory_usage': self.memory_usage,
            'active_threads': self.active_threads,
            'operations_count': self.operations_count,
            'error_count': self.error_count,
            'success_count': self.success_count,
            'avg_operation_time': self.avg_operation_time,
            'last_operation_time': self.last_operation_time,
        }


@dataclass
class SystemComponentStats:
    """Raw statistics for all system components."""

    timestamp: float = field(default_factory=time.time)

    # Memory component
    memory_episodic_size: int = 0
    memory_archive_size: int = 0
    memory_recent_events: int = 0

    # Learning component
    learning_params_count: int = 0
    learning_operations: int = 0

    # Adaptation component
    adaptation_params_count: int = 0
    adaptation_operations: int = 0

    # Decision component
    decision_queue_size: int = 0
    decision_operations: int = 0

    # Action component
    action_queue_size: int = 0
    action_operations: int = 0

    # Environment component
    environment_event_queue_size: int = 0
    environment_pending_events: int = 0

    # Intelligence component
    intelligence_processed_sources: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        def safe_value(value):
            """Convert value to JSON-serializable type."""
            if isinstance(value, (int, float, str, bool, type(None))):
                return value
            elif isinstance(value, (list, tuple)):
                return [safe_value(item) for item in value]
            elif isinstance(value, dict):
                return {str(k): safe_value(v) for k, v in value.items()}
            else:
                # Convert any other type to string representation
                return str(value)

        return {
            'timestamp': safe_value(self.timestamp),
            'memory_episodic_size': safe_value(self.memory_episodic_size),
            'memory_archive_size': safe_value(self.memory_archive_size),
            'memory_recent_events': safe_value(self.memory_recent_events),
            'learning_params_count': safe_value(self.learning_params_count),
            'learning_operations': safe_value(self.learning_operations),
            'adaptation_params_count': safe_value(self.adaptation_params_count),
            'adaptation_operations': safe_value(self.adaptation_operations),
            'decision_queue_size': safe_value(self.decision_queue_size),
            'decision_operations': safe_value(self.decision_operations),
            'action_queue_size': safe_value(self.action_queue_size),
            'action_operations': safe_value(self.action_operations),
            'environment_event_queue_size': safe_value(self.environment_event_queue_size),
            'environment_pending_events': safe_value(self.environment_pending_events),
            'intelligence_processed_sources': safe_value(self.intelligence_processed_sources),
        }


class ComponentMonitor:
    """
    Passive monitor of system components.

    Collects raw statistics without interpretation.
    """

    def __init__(self):
        """Initialize component monitor."""
        self.monitoring_enabled = True
        self.last_system_stats: Optional[SystemComponentStats] = None

    def collect_component_stats(self, self_state) -> SystemComponentStats:
        """
        Collect raw statistics from all components.

        Args:
            self_state: SelfState instance

        Returns:
            SystemComponentStats with raw component data
        """
        if not self.monitoring_enabled:
            return SystemComponentStats()

        stats = SystemComponentStats()

        try:
            # Memory statistics
            memory = getattr(self_state, 'memory', None)
            if memory:
                episodic = getattr(memory, 'episodic_memory', [])
                archive = getattr(memory, 'archive_memory', None)
                recent = getattr(memory, 'recent_events', [])

                # Safely get lengths with type checking
                if hasattr(episodic, '__len__'):
                    try:
                        stats.memory_episodic_size = len(episodic)
                    except (TypeError, AttributeError):
                        stats.memory_episodic_size = 0
                else:
                    stats.memory_episodic_size = 0

                if archive and hasattr(archive, 'episodic_memory'):
                    archive_memory = getattr(archive, 'episodic_memory', [])
                    if hasattr(archive_memory, '__len__'):
                        try:
                            stats.memory_archive_size = len(archive_memory)
                        except (TypeError, AttributeError):
                            stats.memory_archive_size = 0
                    else:
                        stats.memory_archive_size = 0

                if hasattr(recent, '__len__'):
                    try:
                        stats.memory_recent_events = len(recent)
                    except (TypeError, AttributeError):
                        stats.memory_recent_events = 0
                else:
                    stats.memory_recent_events = 0
        except Exception as e:
            logger.warning(f"Failed to collect memory statistics: {e}")

        try:
            # Learning statistics
            learning_engine = getattr(self_state, 'learning_engine', None)
            if learning_engine:
                params = getattr(learning_engine, 'params', {})
                if isinstance(params, dict):
                    stats.learning_params_count = len(params)
                elif hasattr(params, '__len__'):
                    try:
                        stats.learning_params_count = len(params)
                    except (TypeError, AttributeError):
                        stats.learning_params_count = 0
                else:
                    stats.learning_params_count = 0
                stats.learning_operations = getattr(learning_engine, 'operation_count', 0)
        except Exception as e:
            logger.warning(f"Failed to collect learning statistics: {e}")

        try:
            # Adaptation statistics
            adaptation_manager = getattr(self_state, 'adaptation_manager', None)
            if adaptation_manager:
                params = getattr(adaptation_manager, 'params', {})
                if isinstance(params, dict):
                    stats.adaptation_params_count = len(params)
                elif hasattr(params, '__len__'):
                    try:
                        stats.adaptation_params_count = len(params)
                    except (TypeError, AttributeError):
                        stats.adaptation_params_count = 0
                else:
                    stats.adaptation_params_count = 0
                stats.adaptation_operations = getattr(adaptation_manager, 'operation_count', 0)
        except Exception as e:
            logger.warning(f"Failed to collect adaptation statistics: {e}")

        try:
            # Decision statistics
            decision_engine = getattr(self_state, 'decision_engine', None)
            if decision_engine:
                queue = getattr(decision_engine, 'decision_queue', [])
                if hasattr(queue, '__len__'):
                    try:
                        stats.decision_queue_size = len(queue)
                    except (TypeError, AttributeError):
                        stats.decision_queue_size = 0
                else:
                    stats.decision_queue_size = 0
                stats.decision_operations = getattr(decision_engine, 'operation_count', 0)
        except Exception as e:
            logger.warning(f"Failed to collect decision statistics: {e}")

        try:
            # Action statistics
            action_executor = getattr(self_state, 'action_executor', None)
            if action_executor:
                queue = getattr(action_executor, 'action_queue', [])
                if hasattr(queue, '__len__'):
                    try:
                        stats.action_queue_size = len(queue)
                    except (TypeError, AttributeError):
                        stats.action_queue_size = 0
                else:
                    stats.action_queue_size = 0
                stats.action_operations = getattr(action_executor, 'operation_count', 0)
        except Exception as e:
            logger.warning(f"Failed to collect action statistics: {e}")

        try:
            # Environment statistics
            environment = getattr(self_state, 'environment', None)
            if environment:
                event_queue = getattr(environment, 'event_queue', None)
                if event_queue:
                    stats.environment_event_queue_size = getattr(event_queue, 'qsize', lambda: 0)()
                    event_queue_list = getattr(event_queue, 'queue', [])
                    if hasattr(event_queue_list, '__len__'):
                        try:
                            stats.environment_pending_events = len(event_queue_list)
                        except (TypeError, AttributeError):
                            stats.environment_pending_events = 0
                    else:
                        stats.environment_pending_events = 0
        except Exception as e:
            logger.warning(f"Failed to collect environment statistics: {e}")

        try:
            # Intelligence statistics
            intelligence = getattr(self_state, 'intelligence', {})
            if isinstance(intelligence, dict):
                processed = intelligence.get('processed_sources', {})
                if isinstance(processed, dict):
                    stats.intelligence_processed_sources = len(processed)
                elif hasattr(processed, '__len__'):
                    try:
                        stats.intelligence_processed_sources = len(processed)
                    except (TypeError, AttributeError):
                        stats.intelligence_processed_sources = 0
                else:
                    stats.intelligence_processed_sources = 0
        except Exception as e:
            logger.warning(f"Failed to collect intelligence statistics: {e}")

        self.last_system_stats = stats
        return stats

    def get_last_system_stats(self) -> Optional[SystemComponentStats]:
        """Get the last collected system statistics."""
        return self.last_system_stats

    def enable_monitoring(self):
        """Enable component monitoring."""
        self.monitoring_enabled = True

    def disable_monitoring(self):
        """Disable component monitoring."""
        self.monitoring_enabled = False
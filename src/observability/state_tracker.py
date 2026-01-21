"""
State Tracker for Life system.

Collects raw SelfState data without interpretation or evaluation.
Provides passive monitoring of system parameters.
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    """Raw snapshot of SelfState parameters."""

    timestamp: float = field(default_factory=time.time)

    # Core vital parameters
    energy: float = 0.0
    stability: float = 0.0
    integrity: float = 0.0
    fatigue: float = 0.0
    tension: float = 0.0

    # Age and timing
    age: float = 0.0
    subjective_time: float = 0.0

    # Memory statistics
    memory_size: int = 0
    recent_events_count: int = 0

    # Component counters
    action_count: int = 0
    decision_count: int = 0
    feedback_count: int = 0

    # Learning and adaptation
    learning_params_count: int = 0
    adaptation_params_count: int = 0

    # Additional counters
    ticks: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
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
            'energy': safe_value(self.energy),
            'stability': safe_value(self.stability),
            'integrity': safe_value(self.integrity),
            'fatigue': safe_value(self.fatigue),
            'tension': safe_value(self.tension),
            'age': safe_value(self.age),
            'subjective_time': safe_value(self.subjective_time),
            'memory_size': safe_value(self.memory_size),
            'recent_events_count': safe_value(self.recent_events_count),
            'action_count': safe_value(self.action_count),
            'decision_count': safe_value(self.decision_count),
            'feedback_count': safe_value(self.feedback_count),
            'learning_params_count': safe_value(self.learning_params_count),
            'adaptation_params_count': safe_value(self.adaptation_params_count),
            'ticks': safe_value(self.ticks),
        }


class StateTracker:
    """
    Passive tracker of SelfState parameters.

    Collects raw data without interpretation or evaluation.
    """

    def __init__(self):
        """Initialize state tracker."""
        self.last_snapshot: Optional[StateSnapshot] = None
        self.collection_enabled = True

    def collect_state_data(self, self_state) -> StateSnapshot:
        """
        Collect raw data from SelfState.

        Args:
            self_state: SelfState instance

        Returns:
            StateSnapshot with raw parameter values
        """
        if not self.collection_enabled:
            return StateSnapshot()

        snapshot = StateSnapshot()

        try:
            # Collect core parameters
            snapshot.energy = getattr(self_state, 'energy', 0.0)
            snapshot.stability = getattr(self_state, 'stability', 0.0)
            snapshot.integrity = getattr(self_state, 'integrity', 0.0)
            snapshot.fatigue = getattr(self_state, 'fatigue', 0.0)
            snapshot.tension = getattr(self_state, 'tension', 0.0)

            # Collect timing data
            snapshot.age = getattr(self_state, 'age', 0.0)
            snapshot.subjective_time = getattr(self_state, 'subjective_time', 0.0)

            # Collect component counters
            snapshot.action_count = getattr(self_state, 'action_count', 0)
            snapshot.decision_count = getattr(self_state, 'decision_count', 0)
            snapshot.feedback_count = getattr(self_state, 'feedback_count', 0)
            snapshot.ticks = getattr(self_state, 'ticks', 0)

        except Exception as e:
            logger.warning(f"Failed to collect basic state data: {e}")
            # Return partial snapshot with collected data so far
            self.last_snapshot = snapshot
            return snapshot

        try:
            # Collect memory statistics
            memory = getattr(self_state, 'memory', None)
            if memory:
                episodic_memory = getattr(memory, 'episodic_memory', [])
                recent_events = getattr(memory, 'recent_events', [])

                # Safely get lengths with type checking
                if hasattr(episodic_memory, '__len__'):
                    try:
                        snapshot.memory_size = len(episodic_memory)
                    except (TypeError, AttributeError):
                        snapshot.memory_size = 0
                else:
                    snapshot.memory_size = 0

                if hasattr(recent_events, '__len__'):
                    try:
                        snapshot.recent_events_count = len(recent_events)
                    except (TypeError, AttributeError):
                        snapshot.recent_events_count = 0
                else:
                    snapshot.recent_events_count = 0
        except Exception as e:
            logger.warning(f"Failed to collect memory statistics: {e}")
            # Continue with partial data

        try:
            # Collect parameter counts
            learning_engine = getattr(self_state, 'learning_engine', None)
            if learning_engine:
                learning_params = getattr(learning_engine, 'params', {})
                if isinstance(learning_params, dict):
                    snapshot.learning_params_count = len(learning_params)
                elif hasattr(learning_params, '__len__'):
                    try:
                        snapshot.learning_params_count = len(learning_params)
                    except (TypeError, AttributeError):
                        snapshot.learning_params_count = 0
                else:
                    snapshot.learning_params_count = 0
        except Exception as e:
            logger.warning(f"Failed to collect learning parameters: {e}")

        try:
            adaptation_manager = getattr(self_state, 'adaptation_manager', None)
            if adaptation_manager:
                adaptation_params = getattr(adaptation_manager, 'params', {})
                if isinstance(adaptation_params, dict):
                    snapshot.adaptation_params_count = len(adaptation_params)
                elif hasattr(adaptation_params, '__len__'):
                    try:
                        snapshot.adaptation_params_count = len(adaptation_params)
                    except (TypeError, AttributeError):
                        snapshot.adaptation_params_count = 0
                else:
                    snapshot.adaptation_params_count = 0
        except Exception as e:
            logger.warning(f"Failed to collect adaptation parameters: {e}")

        self.last_snapshot = snapshot
        return snapshot

    def get_last_snapshot(self) -> Optional[StateSnapshot]:
        """Get the last collected snapshot."""
        return self.last_snapshot

    def enable_collection(self):
        """Enable data collection."""
        self.collection_enabled = True

    def disable_collection(self):
        """Disable data collection."""
        self.collection_enabled = False
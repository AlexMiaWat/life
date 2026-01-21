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

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'timestamp': self.timestamp,
            'energy': self.energy,
            'stability': self.stability,
            'integrity': self.integrity,
            'fatigue': self.fatigue,
            'tension': self.tension,
            'age': self.age,
            'subjective_time': self.subjective_time,
            'memory_size': self.memory_size,
            'recent_events_count': self.recent_events_count,
            'action_count': self.action_count,
            'decision_count': self.decision_count,
            'feedback_count': self.feedback_count,
            'learning_params_count': self.learning_params_count,
            'adaptation_params_count': self.adaptation_params_count,
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

        try:
            snapshot = StateSnapshot()

            # Collect core parameters
            snapshot.energy = getattr(self_state, 'energy', 0.0)
            snapshot.stability = getattr(self_state, 'stability', 0.0)
            snapshot.integrity = getattr(self_state, 'integrity', 0.0)
            snapshot.fatigue = getattr(self_state, 'fatigue', 0.0)
            snapshot.tension = getattr(self_state, 'tension', 0.0)

            # Collect timing data
            snapshot.age = getattr(self_state, 'age', 0.0)
            snapshot.subjective_time = getattr(self_state, 'subjective_time', 0.0)

            # Collect memory statistics
            memory = getattr(self_state, 'memory', None)
            if memory:
                snapshot.memory_size = len(getattr(memory, 'episodic_memory', []))
                snapshot.recent_events_count = len(getattr(memory, 'recent_events', []))

            # Collect component counters
            snapshot.action_count = getattr(self_state, 'action_count', 0)
            snapshot.decision_count = getattr(self_state, 'decision_count', 0)
            snapshot.feedback_count = getattr(self_state, 'feedback_count', 0)

            # Collect parameter counts
            learning_engine = getattr(self_state, 'learning_engine', None)
            if learning_engine:
                learning_params = getattr(learning_engine, 'params', {})
                snapshot.learning_params_count = len(learning_params) if isinstance(learning_params, dict) else 0

            adaptation_manager = getattr(self_state, 'adaptation_manager', None)
            if adaptation_manager:
                adaptation_params = getattr(adaptation_manager, 'params', {})
                snapshot.adaptation_params_count = len(adaptation_params) if isinstance(adaptation_params, dict) else 0

            self.last_snapshot = snapshot
            return snapshot

        except Exception as e:
            logger.warning(f"Failed to collect state data: {e}")
            return StateSnapshot()

    def get_last_snapshot(self) -> Optional[StateSnapshot]:
        """Get the last collected snapshot."""
        return self.last_snapshot

    def enable_collection(self):
        """Enable data collection."""
        self.collection_enabled = True

    def disable_collection(self):
        """Disable data collection."""
        self.collection_enabled = False
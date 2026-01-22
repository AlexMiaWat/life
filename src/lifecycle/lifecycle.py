"""
Lifecycle Manager - System Lifecycle Management

This module contains the LifecycleManager class that manages system lifecycle states:
- INIT: Initial state before birth
- RUN: Normal running state
- DEGRADE: Degraded state due to weakness
- DEAD: Final state after death
"""

import time
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class LifecycleState(Enum):
    """Enumeration of possible lifecycle states."""
    INIT = "init"
    RUN = "run"
    DEGRADE = "degrade"
    DEAD = "dead"


@dataclass
class LifecycleTransition:
    """Represents a lifecycle state transition."""
    from_state: LifecycleState
    to_state: LifecycleState
    timestamp: float
    reason: str
    metadata: Optional[Dict[str, Any]] = None


class LifecycleManager:
    """
    Manages the lifecycle of a system instance.

    Tracks state transitions, monitors weakness, and provides lifecycle hooks.
    """

    MAX_HISTORY_SIZE = 100
    DEFAULT_WEAKNESS_THRESHOLD = 0.05
    WEAKNESS_THRESHOLD = DEFAULT_WEAKNESS_THRESHOLD

    def __init__(self, self_state, weakness_threshold: float = DEFAULT_WEAKNESS_THRESHOLD):
        """
        Initialize LifecycleManager.

        Args:
            self_state: SelfState object to monitor
            weakness_threshold: Threshold for weakness detection
        """
        self.self_state = self_state
        self.weakness_threshold = weakness_threshold

        self.current_state = LifecycleState.INIT
        self.birth_timestamp: Optional[float] = time.time()  # Set at initialization
        self.last_transition_timestamp = time.time()
        self.transition_history: List[Dict[str, Any]] = []

        # Lifecycle properties
        self.is_active = False

    def on_birth(self) -> bool:
        """
        Handle birth event - transition from INIT to RUN.

        Returns:
            True if transition successful
        """
        if self.current_state != LifecycleState.INIT:
            return False  # Can only be born from INIT state

        return self._transition_to(LifecycleState.RUN, "birth_event")

    def on_tick(self) -> bool:
        """
        Handle tick event - check for state changes based on self-state.

        Returns:
            True if transition occurred
        """
        if self.current_state == LifecycleState.INIT:
            return False  # Can't tick in INIT state

        if self.current_state == LifecycleState.DEAD:
            return False  # Can't tick when dead

        # Check for degradation
        if self.current_state == LifecycleState.RUN and self._is_weak():
            return self._transition_to(LifecycleState.DEGRADE, "weakness_detected")

        # Check for death - only transition if critically weak AND has been degrading for a while
        if self.current_state == LifecycleState.DEGRADE:
            # Count how many transitions we've had in DEGRADE state
            degrade_transitions = sum(1 for t in self.transition_history
                                    if t["to_state"] == LifecycleState.DEGRADE)
            # Require at least 2 ticks in DEGRADE state before allowing death
            if self._is_critically_weak() and degrade_transitions >= 2:
                return self._transition_to(LifecycleState.DEAD, "critical_weakness")

        return False  # No transition needed

    def on_degrade(self) -> bool:
        """
        Force degradation transition (for testing/manual control).

        Returns:
            True if transition successful
        """
        if self.current_state not in [LifecycleState.RUN, LifecycleState.DEGRADE]:
            return False

        return self._transition_to(LifecycleState.DEGRADE, "manual_degradation")

    def _transition_to(self, new_state: LifecycleState, reason: str,
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Internal method to handle state transitions.

        Args:
            new_state: Target state
            reason: Reason for transition
            metadata: Additional metadata

        Returns:
            True if transition successful
        """
        if not self._is_valid_transition(self.current_state, new_state):
            return False

        old_state = self.current_state
        self.current_state = new_state
        self.last_transition_timestamp = time.time()

        # Update lifecycle properties
        self.is_active = new_state in [LifecycleState.RUN, LifecycleState.DEGRADE]

        # Set birth timestamp on first RUN transition
        if new_state == LifecycleState.RUN and self.birth_timestamp is None:
            self.birth_timestamp = self.last_transition_timestamp

        # Record transition
        self._record_transition(old_state, new_state, reason, metadata)

        return True

    def _is_weak(self) -> bool:
        """
        Check if system is weak based on self-state parameters.

        Returns:
            True if system is considered weak
        """
        return (self.self_state.energy < self.weakness_threshold or
                self.self_state.integrity < self.weakness_threshold or
                self.self_state.stability < self.weakness_threshold)

    def _is_critically_weak(self) -> bool:
        """
        Check if system is critically weak (close to death).

        Returns:
            True if system should die (all parameters critically low)
        """
        critical_threshold = self.weakness_threshold * 3  # Much more strict threshold for death
        return (self.self_state.energy < critical_threshold and
                self.self_state.integrity < critical_threshold and
                self.self_state.stability < critical_threshold)

    def _is_valid_transition(self, from_state: LifecycleState, to_state: LifecycleState) -> bool:
        """
        Check if a state transition is valid.

        Args:
            from_state: Current state
            to_state: Target state

        Returns:
            True if transition is valid
        """
        valid_transitions = {
            LifecycleState.INIT: [LifecycleState.RUN],
            LifecycleState.RUN: [LifecycleState.DEGRADE, LifecycleState.DEAD],
            LifecycleState.DEGRADE: [LifecycleState.DEAD],
            LifecycleState.DEAD: []  # No transitions from DEAD
        }

        return to_state in valid_transitions.get(from_state, [])

    def _record_transition(self, from_state: LifecycleState, to_state: LifecycleState,
                          reason: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Record a state transition in history.

        Args:
            from_state: Previous state
            to_state: New state
            reason: Reason for transition
            metadata: Additional metadata
        """
        transition_record = {
            "from_state": from_state,
            "to_state": to_state,
            "timestamp": self.last_transition_timestamp,
            "reason": reason,
            "metadata": metadata or {}
        }

        self.transition_history.append(transition_record)

        # Maintain history size limit
        if len(self.transition_history) > self.MAX_HISTORY_SIZE:
            self.transition_history.pop(0)

    def get_lifecycle_info(self) -> Dict[str, Any]:
        """
        Get comprehensive lifecycle information.

        Returns:
            Dictionary with lifecycle information
        """
        age = None
        if self.birth_timestamp:
            age = time.time() - self.birth_timestamp

        return {
            "current_state": self.current_state,
            "is_active": self.is_active,
            "birth_timestamp": self.birth_timestamp,
            "age_seconds": age,
            "last_transition_timestamp": self.last_transition_timestamp,
            "transition_count": len(self.transition_history),
            "transition_history": self.transition_history.copy(),
            "weakness_threshold": self.weakness_threshold,
            "is_weak": self._is_weak(),
            "is_critically_weak": self._is_critically_weak()
        }
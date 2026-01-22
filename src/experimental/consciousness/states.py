"""
Consciousness States - Compatibility Layer

Backward compatibility for consciousness states API.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.experimental.adaptive_processing_manager import AdaptiveState


class ConsciousnessState(Enum):
    """Enumeration of possible consciousness states."""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    REFLECTING = "reflecting"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class ConsciousnessStateData:
    """Data associated with a consciousness state."""
    state: ConsciousnessState
    timestamp: float
    metadata: Dict[str, Any]
    metrics: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert state data to dictionary."""
        result = {
            'state': self.state.value,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }

        if self.metrics:
            result['metrics'] = self.metrics
        if self.error_message:
            result['error_message'] = self.error_message

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsciousnessStateData':
        """Create state data from dictionary."""
        # Convert string representation back to enum
        state_str = data['state']
        state_enum = None
        for enum_member in ConsciousnessState:
            if enum_member.value == state_str:
                state_enum = enum_member
                break

        if state_enum is None:
            raise ValueError(f"Unknown consciousness state: {state_str}")

        return cls(
            state=state_enum,
            timestamp=data['timestamp'],
            metadata=data['metadata'],
            metrics=data.get('metrics'),
            error_message=data.get('error_message')
        )


class ConsciousnessStateManager:
    """Manages consciousness state transitions."""

    def __init__(self):
        self.current_state = ConsciousnessState.INACTIVE
        self.state_history: List[ConsciousnessStateData] = []
        self.transition_handlers: Dict[tuple[ConsciousnessState, ConsciousnessState], callable] = {}

    def transition_to(self, new_state: ConsciousnessState,
                     metadata: Optional[Dict[str, Any]] = None,
                     metrics: Optional[Dict[str, float]] = None,
                     error_message: Optional[str] = None) -> bool:
        """Transition to a new state."""
        if not self._is_valid_transition(self.current_state, new_state):
            return False

        # Execute transition handler if exists
        handler_key = (self.current_state, new_state)
        if handler_key in self.transition_handlers:
            try:
                self.transition_handlers[handler_key](self.current_state, new_state)
            except Exception:
                # Log error but don't fail transition
                pass

        # Create state data
        state_data = ConsciousnessStateData(
            state=new_state,
            timestamp=time.time(),
            metadata=metadata or {},
            metrics=metrics,
            error_message=error_message
        )

        # Update state and history
        self.current_state = new_state
        self.state_history.append(state_data)

        return True

    def _is_valid_transition(self, from_state: ConsciousnessState,
                           to_state: ConsciousnessState) -> bool:
        """Check if a state transition is valid."""
        # Define valid transitions
        valid_transitions = {
            ConsciousnessState.INACTIVE: [ConsciousnessState.INITIALIZING],
            ConsciousnessState.INITIALIZING: [ConsciousnessState.ACTIVE, ConsciousnessState.ERROR],
            ConsciousnessState.ACTIVE: [ConsciousnessState.PROCESSING, ConsciousnessState.ERROR, ConsciousnessState.SHUTDOWN],
            ConsciousnessState.PROCESSING: [ConsciousnessState.ACTIVE, ConsciousnessState.ANALYZING, ConsciousnessState.ERROR],
            ConsciousnessState.ANALYZING: [ConsciousnessState.ACTIVE, ConsciousnessState.REFLECTING, ConsciousnessState.ERROR],
            ConsciousnessState.REFLECTING: [ConsciousnessState.ACTIVE, ConsciousnessState.ERROR],
            ConsciousnessState.ERROR: [ConsciousnessState.INACTIVE, ConsciousnessState.INITIALIZING],
            ConsciousnessState.SHUTDOWN: [ConsciousnessState.INACTIVE]
        }

        return to_state in valid_transitions.get(from_state, [])

    def add_transition_handler(self, from_state: ConsciousnessState,
                              to_state: ConsciousnessState, handler: callable):
        """Add a handler for state transitions."""
        self.transition_handlers[(from_state, to_state)] = handler

    def get_state_history(self, limit: Optional[int] = None) -> List[ConsciousnessStateData]:
        """Get state history."""
        if limit:
            return self.state_history[-limit:]
        return self.state_history.copy()

    def get_current_state_info(self) -> Dict[str, Any]:
        """Get information about current state."""
        latest_data = self.state_history[-1] if self.state_history else None

        return {
            'current_state': self.current_state.value,
            'state_since': latest_data.timestamp if latest_data else None,
            'total_transitions': len(self.state_history),
            'latest_metadata': latest_data.metadata if latest_data else {}
        }


# Global state manager instance - commented out to avoid import issues
# state_manager = ConsciousnessStateManager()
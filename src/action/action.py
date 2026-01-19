import time

from memory.memory import MemoryEntry


def execute_action(pattern: str, self_state):
    """
    Execute action based on pattern.
    Minimal implementation: record action in memory and apply minor state update if applicable.
    """
    # Record action in memory
    action_entry = MemoryEntry(
        event_type="action", meaning_significance=0.0, timestamp=time.time()
    )
    self_state.memory.append(action_entry)

    # Minimal state update for dampen
    if pattern == "dampen":
        # Minor fatigue effect (assuming energy represents vitality)
        self_state.energy = max(0.0, self_state.energy - 0.01)

    # For absorb and ignore, no additional state changes

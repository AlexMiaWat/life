from meaning.meaning import Meaning
from state.self_state import SelfState


def decide_response(self_state: SelfState, meaning: Meaning) -> str:
    """
    Минимальный выбор паттерна на основе activated_memory.
    - Если max sig в activated >0.5 — "dampen" (опыт учит смягчать).
    - Else return Meaning's pattern (absorb/ignore).
    """
    activated = self_state.activated_memory
    if activated and max(e.meaning_significance for e in activated) > 0.5:
        return "dampen"
    # Fallback to Meaning's logic
    if meaning.significance < 0.1:
        return "ignore"
    return "absorb"

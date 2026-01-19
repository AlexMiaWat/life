from meaning.meaning import Meaning
from state.self_state import SelfState


def decide_response(self_state: SelfState, meaning: Meaning) -> str:
    """
    Минимальный выбор паттерна на основе activated_memory.
    - Если max sig в activated >0.5 — "dampen" (опыт учит смягчать).
    - Else return Meaning's pattern (absorb/ignore).
    
    ИНТЕГРАЦИЯ: Использует learning_params и adaptation_params для модификации порогов.
    """
    # ИНТЕГРАЦИЯ: Используем adaptation_params.behavior_thresholds для модификации порога
    adaptation_params = getattr(self_state, "adaptation_params", {})
    behavior_thresholds = adaptation_params.get("behavior_thresholds", {})
    
    # Базовый порог для dampen (0.5)
    dampen_threshold = 0.5
    
    # Модифицируем порог на основе параметров, если доступны
    # Используем среднее значение порогов для всех типов событий как модификатор
    if behavior_thresholds:
        avg_threshold = sum(behavior_thresholds.values()) / len(behavior_thresholds)
        # Модифицируем порог: если пороги низкие, dampen срабатывает чаще
        dampen_threshold = 0.5 - (0.5 - avg_threshold) * 0.3  # Мягкая модификация
    
    activated = self_state.activated_memory
    if activated and max(e.meaning_significance for e in activated) > dampen_threshold:
        return "dampen"
    
    # ИНТЕГРАЦИЯ: Используем learning_params.significance_thresholds для ignore
    learning_params = getattr(self_state, "learning_params", {})
    significance_thresholds = learning_params.get("significance_thresholds", {})
    ignore_threshold = 0.1
    
    # Используем среднее значение порогов, если доступны
    if significance_thresholds:
        avg_sig_threshold = sum(significance_thresholds.values()) / len(significance_thresholds)
        ignore_threshold = avg_sig_threshold
    
    # Fallback to Meaning's logic
    if meaning.significance < ignore_threshold:
        return "ignore"
    return "absorb"

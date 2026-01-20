from src.meaning.meaning import Meaning
from src.state.self_state import SelfState


def decide_response(self_state: SelfState, meaning: Meaning) -> str:
    """
    Минимальный выбор паттерна на основе activated_memory.
    - Если max sig в activated >0.5 — "dampen" (опыт учит смягчать).
    - Else return Meaning's pattern (absorb/ignore).

    ИНТЕГРАЦИЯ: Использует learning_params, adaptation_params и субъективное время для модификации порогов.
    """
    # ИНТЕГРАЦИЯ: Используем субъективное время для модификации поведения
    # Если субъективное время течет быстрее физического, система более осторожная
    time_ratio = self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
    # Нормализуем ratio: при ratio > 1 (ускоренное восприятие) - более осторожная
    # при ratio < 1 (замедленное восприятие) - более смелая
    time_modifier = min(max(time_ratio - 1.0, -0.3), 0.3)  # Ограничение [-0.3, 0.3]

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

    # Применяем модификатор субъективного времени
    # Если time_modifier > 0 (ускоренное восприятие), понижаем порог - dampen чаще
    # Если time_modifier < 0 (замедленное восприятие), повышаем порог - dampen реже
    dampen_threshold = max(0.1, min(0.9, dampen_threshold - time_modifier * 0.2))

    activated = self_state.activated_memory
    if activated and max(e.meaning_significance for e in activated) > dampen_threshold:
        return "dampen"

    # ИНТЕГРАЦИЯ: Используем learning_params.significance_thresholds для ignore
    learning_params = getattr(self_state, "learning_params", {})
    significance_thresholds = learning_params.get("significance_thresholds", {})
    ignore_threshold = 0.1

    # Используем среднее значение порогов, если доступны
    if significance_thresholds:
        avg_sig_threshold = sum(significance_thresholds.values()) / len(
            significance_thresholds
        )
        ignore_threshold = avg_sig_threshold

    # Fallback to Meaning's logic
    if meaning.significance < ignore_threshold:
        return "ignore"
    return "absorb"

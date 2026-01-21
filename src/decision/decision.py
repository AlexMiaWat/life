from typing import List

from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState


def decide_response(self_state: SelfState, meaning: Meaning) -> str:
    """
    Улучшенный выбор паттерна реакции на основе комплексного анализа.

    Новая логика:
    1. Взвешенный анализ активированной памяти (учитывает веса и распределение)
    2. Контекстно-зависимый выбор с учетом состояния системы
    3. Специфические правила для типов событий
    4. Поддержка всех паттернов: ignore, absorb, dampen, amplify

    ИНТЕГРАЦИЯ: Использует learning_params, adaptation_params и субъективное время.
    """
    activated = self_state.activated_memory or []

    # === ФАЗА 1: Анализ активированной памяти ===
    memory_analysis = _analyze_activated_memory(activated)

    # === ФАЗА 2: Анализ контекста системы ===
    context_analysis = _analyze_system_context(self_state, meaning)

    # === ФАЗА 3: Специфические правила по типу события ===
    event_type_rules = _get_event_type_rules(meaning)

    # === ФАЗА 4: Взвешенный выбор паттерна ===
    return _select_response_pattern(
        memory_analysis, context_analysis, event_type_rules, meaning, self_state
    )


def _analyze_activated_memory(activated: List[MemoryEntry]) -> dict:
    """
    Комплексный анализ активированной памяти.

    Returns:
        dict: {
            'weighted_avg': средневзвешенная значимость,
            'max_sig': максимальная значимость,
            'high_count': количество высоко значимых записей (>0.7),
            'distribution': распределение значимостей
        }
    """
    if not activated:
        return {
            "weighted_avg": 0.0,
            "max_sig": 0.0,
            "high_count": 0,
            "distribution": "empty",
        }

    # Взвешенная средняя значимость
    total_weight = sum(entry.weight for entry in activated)
    if total_weight > 0:
        weighted_avg = (
            sum(entry.meaning_significance * entry.weight for entry in activated)
            / total_weight
        )
    else:
        weighted_avg = sum(entry.meaning_significance for entry in activated) / len(
            activated
        )

    # Максимальная значимость
    max_sig = max(entry.meaning_significance for entry in activated)

    # Количество высоко значимых записей
    high_count = sum(1 for entry in activated if entry.meaning_significance > 0.7)

    # Распределение
    if weighted_avg < 0.3:
        distribution = "low"
    elif weighted_avg < 0.6:
        distribution = "medium"
    elif high_count >= len(activated) * 0.5:
        distribution = "high_concentrated"
    else:
        distribution = "high_scattered"

    return {
        "weighted_avg": weighted_avg,
        "max_sig": max_sig,
        "high_count": high_count,
        "distribution": distribution,
    }


def _analyze_system_context(self_state: SelfState, meaning: Meaning) -> dict:
    """
    Анализ контекста системы для принятия решения.

    Returns:
        dict: параметры контекста влияющие на выбор паттерна
    """
    # Состояние системы
    energy_level = "low" if self_state.energy < 30 else "high"
    stability_level = (
        "low"
        if self_state.stability < 0.3
        else "high"
        if self_state.stability > 0.8
        else "medium"
    )
    integrity_level = "low" if self_state.integrity < 0.3 else "high"

    # Субъективное время
    time_ratio = (
        self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
    )
    time_perception = (
        "accelerated"
        if time_ratio > 1.1
        else "normal"
        if time_ratio > 0.9
        else "slowed"
    )

    # Модификаторы из параметров
    adaptation_params = getattr(self_state, "adaptation_params", {})
    behavior_thresholds = adaptation_params.get("behavior_thresholds", {})

    learning_params = getattr(self_state, "learning_params", {})
    significance_thresholds = learning_params.get("significance_thresholds", {})

    return {
        "energy_level": energy_level,
        "stability_level": stability_level,
        "integrity_level": integrity_level,
        "time_perception": time_perception,
        "behavior_thresholds": behavior_thresholds,
        "significance_thresholds": significance_thresholds,
        "meaning_significance": meaning.significance,
    }


def _get_event_type_rules(meaning: Meaning) -> dict:
    """
    Специфические правила для типов событий.

    Returns:
        dict: правила выбора паттернов для данного типа события
    """
    # Извлекаем тип события из meaning (если доступен)
    event_type = getattr(meaning, "event_type", "unknown")

    rules = {
        "shock": {
            "can_amplify": False,  # Шоки не усиливаем
            "prefer_dampen": True,  # Предпочитаем смягчать
            "conservative_threshold": 0.3,  # Более низкий порог для реакции
        },
        "noise": {
            "can_ignore": True,  # Шум можно игнорировать
            "ignore_threshold": 0.15,  # Более высокий порог игнорирования
            "can_amplify": False,
        },
        "recovery": {
            "can_amplify": True,  # Восстановление можно усиливать
            "prefer_absorb": True,  # Предпочитаем полное поглощение
            "positive_event": True,
        },
        "decay": {
            "can_amplify": False,  # Распад не усиливаем
            "prefer_dampen": True,  # Предпочитаем смягчать
            "negative_event": True,
        },
        "idle": {
            "can_ignore": True,  # Бездействие часто игнорируем
            "ignore_threshold": 0.05,
            "can_amplify": False,
        },
        "social_presence": {
            "context_sensitive": True,  # Зависит от стабильности
            "can_amplify": True,
            "positive_event": True,
        },
        "social_conflict": {
            "can_amplify": False,
            "prefer_dampen": True,
            "negative_event": True,
        },
        "cognitive_doubt": {
            "can_ignore": True,
            "context_sensitive": True,
            "ignore_threshold": 0.2,
        },
        "cognitive_clarity": {
            "can_amplify": True,
            "prefer_absorb": True,
            "positive_event": True,
        },
        "existential_void": {
            "can_amplify": False,
            "prefer_dampen": True,
            "conservative_threshold": 0.2,
        },
        "existential_purpose": {
            "can_amplify": True,
            "prefer_absorb": True,
            "positive_event": True,
        },
    }

    return rules.get(
        event_type, {"can_amplify": True, "can_ignore": True, "prefer_absorb": True}
    )


def _select_response_pattern(
    memory_analysis: dict,
    context_analysis: dict,
    event_rules: dict,
    meaning: Meaning,
    self_state: SelfState,
) -> str:
    """
    Финальный выбор паттерна реакции на основе всех анализов.
    """
    weighted_avg = memory_analysis["weighted_avg"]
    max_sig = memory_analysis["max_sig"]
    distribution = memory_analysis["distribution"]

    energy_level = context_analysis["energy_level"]
    stability_level = context_analysis["stability_level"]
    integrity_level = context_analysis["integrity_level"]
    time_perception = context_analysis["time_perception"]
    meaning_sig = context_analysis["meaning_significance"]

    # === Правило 1: Высокая концентрация значимых воспоминаний ===
    if distribution == "high_concentrated" or max_sig > 0.8:
        if (
            event_rules.get("can_amplify", True)
            and stability_level == "low"
            and energy_level == "low"
        ):
            # При низкой стабильности и энергии можем усилить положительные эффекты
            if event_rules.get("positive_event", False):
                return "amplify"
        return "dampen"

    # === Правило 2: Низкая энергия - консервативный подход ===
    # Но для положительных событий при низкой стабильности делаем исключение
    if energy_level == "low":
        is_positive_and_unstable = (
            stability_level == "low"
            and event_rules.get("positive_event", False)
            and event_rules.get("can_amplify", True)
            and meaning_sig > 0.4
        )

        if is_positive_and_unstable:
            return "amplify"  # Исключение для положительных событий при низкой стабильности
        elif weighted_avg > 0.4 or meaning_sig > 0.3:
            return "dampen"
        elif meaning_sig < 0.1 and event_rules.get("can_ignore", True):
            return "ignore"

    # === Правило 3: Высокая стабильность - смягчение эффектов ===
    if stability_level == "high":
        if weighted_avg > 0.3 or meaning_sig > 0.2:
            return "dampen"

    # === Правило 4: Низкая стабильность - усиление положительных эффектов ===
    if stability_level == "low" and event_rules.get("can_amplify", True):
        if event_rules.get("positive_event", False) and meaning_sig > 0.4:
            return "amplify"

    # === Правило 5: Ускоренное восприятие времени - более осторожный ===
    if time_perception == "accelerated":
        if weighted_avg > 0.35 or meaning_sig > 0.25:
            return "dampen"

    # === Правило 6: Низкая целостность - осторожный подход ===
    if integrity_level == "low":
        if weighted_avg > 0.5 or meaning_sig > 0.4:
            return "dampen"

    # === Правило 7: Специфические правила по типу события ===
    if event_rules.get("prefer_dampen", False):
        if weighted_avg > 0.3 or meaning_sig > 0.2:
            return "dampen"

    if event_rules.get("prefer_absorb", False) and weighted_avg <= 0.6:
        return "absorb"

    if event_rules.get("can_ignore", True):
        ignore_threshold = event_rules.get("ignore_threshold", 0.1)
        if weighted_avg < ignore_threshold and meaning_sig < ignore_threshold:
            return "ignore"

    # === Правило 8: Взвешенный анализ средней значимости ===
    if weighted_avg < 0.2 and meaning_sig < 0.15:
        return "ignore"
    elif weighted_avg < 0.5 and meaning_sig < 0.3:
        return "absorb"
    elif weighted_avg >= 0.5 or meaning_sig >= 0.4:
        return "dampen"
    else:
        return "absorb"

from typing import List, Dict, Any

from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState


class DecisionEngine:
    """
    Движок принятия решений для системы Life.

    Обеспечивает интерфейс для анализа решений и их последствий.
    """

    def __init__(self):
        """Инициализация движка принятия решений."""
        self.decision_history = []


def _analyze_adaptation_history(self_state: SelfState) -> dict:
    """
    Анализ истории адаптаций для контекстной осведомленности.

    Returns:
        dict: анализ трендов и паттернов адаптаций
    """
    adaptation_history = getattr(self_state, "adaptation_history", [])
    if not adaptation_history:
        return {
            "trend_direction": "neutral",
            "recent_changes_count": 0,
            "avg_change_magnitude": 0.0,
            "most_changed_param": None,
            "adaptation_stability": "unknown",
        }

    # Анализ последних 10 адаптаций
    recent_history = adaptation_history[-10:]

    # Подсчет общего направления изменений
    positive_changes = 0
    negative_changes = 0
    total_magnitude = 0.0
    param_change_counts = {}

    for entry in recent_history:
        changes = entry.get("changes", {})
        for param_group, param_changes in changes.items():
            if isinstance(param_changes, dict):
                for param_name, change_info in param_changes.items():
                    if isinstance(change_info, dict):
                        old_val = change_info.get("old", 0)
                        new_val = change_info.get("new", 0)
                        delta = new_val - old_val

                        total_magnitude += abs(delta)

                        if delta > 0.01:
                            positive_changes += 1
                        elif delta < -0.01:
                            negative_changes += 1

                        # Подсчет изменений по параметрам
                        param_key = f"{param_group}.{param_name}"
                        param_change_counts[param_key] = param_change_counts.get(param_key, 0) + 1

    # Определение тренда
    if positive_changes > negative_changes * 1.5:
        trend_direction = "increasing"
    elif negative_changes > positive_changes * 1.5:
        trend_direction = "decreasing"
    else:
        trend_direction = "stable"

    # Средняя величина изменений
    avg_change_magnitude = total_magnitude / len(recent_history) if recent_history else 0.0

    # Наиболее изменяемый параметр
    most_changed_param = (
        max(param_change_counts.keys(), key=lambda k: param_change_counts[k])
        if param_change_counts
        else None
    )

    # Стабильность адаптаций
    if avg_change_magnitude < 0.02:
        adaptation_stability = "stable"
    elif avg_change_magnitude < 0.05:
        adaptation_stability = "moderate"
    else:
        adaptation_stability = "volatile"

    return {
        "trend_direction": trend_direction,
        "recent_changes_count": len(recent_history),
        "avg_change_magnitude": avg_change_magnitude,
        "most_changed_param": most_changed_param,
        "adaptation_stability": adaptation_stability,
        "positive_changes": positive_changes,
        "negative_changes": negative_changes,
    }


def _calculate_dynamic_threshold(
    base_threshold: float, sensitivity: float, energy_level: str, stability_level: str
) -> float:
    """
    Вычисление динамического порога на основе обученной чувствительности и состояния системы.

    Args:
        base_threshold: Базовое значение порога
        sensitivity: Чувствительность к типу события (0.0-1.0)
        energy_level: Уровень энергии ("low", "high")
        stability_level: Уровень стабильности ("low", "medium", "high")

    Returns:
        float: Адаптивный порог
    """
    # Модификатор на основе чувствительности (0.5-1.5)
    sensitivity_modifier = 0.5 + sensitivity

    # Модификаторы состояния системы
    energy_modifier = 0.8 if energy_level == "low" else 1.2
    stability_modifier = (
        0.9 if stability_level == "low" else 1.1 if stability_level == "high" else 1.0
    )

    # Расчет адаптивного порога
    adaptive_threshold = (
        base_threshold * sensitivity_modifier * energy_modifier * stability_modifier
    )

    # Ограничение диапазона для стабильности
    return max(0.05, min(0.8, adaptive_threshold))


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
            sum(entry.meaning_significance * entry.weight for entry in activated) / total_weight
        )
    else:
        weighted_avg = sum(entry.meaning_significance for entry in activated) / len(activated)

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
    Анализ контекста системы для принятия решения с интеграцией Learning/Adaptation параметров.

    Returns:
        dict: параметры контекста влияющие на выбор паттерна
    """
    # Состояние системы
    energy_level = "low" if self_state.energy < 30 else "high"
    stability_level = (
        "low" if self_state.stability < 0.3 else "high" if self_state.stability > 0.8 else "medium"
    )
    integrity_level = "low" if self_state.integrity < 0.3 else "high"

    # Субъективное время
    time_ratio = self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
    time_perception = (
        "accelerated" if time_ratio > 1.1 else "normal" if time_ratio > 0.9 else "slowed"
    )

    # Циркадные ритмы
    import math
    circadian_phase_rad = self_state.circadian_phase
    # Определяем текущую фазу циркадного ритма
    if circadian_phase_rad < math.pi / 2:
        circadian_phase = "dawn"  # Рассвет
        circadian_modifier = 0.8  # Более осторожный
    elif circadian_phase_rad < math.pi:
        circadian_phase = "day"  # День
        circadian_modifier = 1.2  # Более активный
    elif circadian_phase_rad < 3 * math.pi / 2:
        circadian_phase = "dusk"  # Закат
        circadian_modifier = 0.9  # Умеренный
    else:
        circadian_phase = "night"  # Ночь
        circadian_modifier = 0.7  # Консервативный

    # Модификаторы из параметров Learning/Adaptation
    adaptation_params = getattr(self_state, "adaptation_params", {})
    behavior_thresholds = adaptation_params.get("behavior_thresholds", {})
    behavior_sensitivity = adaptation_params.get("behavior_sensitivity", {})
    behavior_coefficients = adaptation_params.get("behavior_coefficients", {})

    learning_params = getattr(self_state, "learning_params", {})
    significance_thresholds = learning_params.get("significance_thresholds", {})
    event_type_sensitivity = learning_params.get("event_type_sensitivity", {})
    response_coefficients = learning_params.get("response_coefficients", {})

    # Анализ истории адаптаций для контекстной осведомленности
    adaptation_analysis = _analyze_adaptation_history(self_state)

    # Вычисление динамических порогов на основе обученных параметров
    event_type = getattr(meaning, "event_type", "unknown")
    base_sensitivity = event_type_sensitivity.get(event_type, 0.2)

    # Модификация чувствительности на основе тренда адаптаций
    adapted_sensitivity = base_sensitivity
    if adaptation_analysis["trend_direction"] == "increasing":
        adapted_sensitivity = min(
            0.9, base_sensitivity * 1.2
        )  # Увеличение чувствительности при росте адаптаций
    elif adaptation_analysis["trend_direction"] == "decreasing":
        adapted_sensitivity = max(
            0.1, base_sensitivity * 0.8
        )  # Уменьшение чувствительности при снижении адаптаций

    # Адаптивные пороги на основе чувствительности, состояния и истории адаптаций
    dynamic_ignore_threshold = _calculate_dynamic_threshold(
        base_threshold=0.1,
        sensitivity=adapted_sensitivity,
        energy_level=energy_level,
        stability_level=stability_level,
    )

    dynamic_dampen_threshold = _calculate_dynamic_threshold(
        base_threshold=0.3,
        sensitivity=adapted_sensitivity,
        energy_level=energy_level,
        stability_level=stability_level,
    )

    # Корректировка порогов на основе стабильности адаптаций
    if adaptation_analysis["adaptation_stability"] == "volatile":
        # При волатильных адаптациях делаем пороги более строгими
        dynamic_ignore_threshold *= 0.8
        dynamic_dampen_threshold *= 0.9
    elif adaptation_analysis["adaptation_stability"] == "stable":
        # При стабильных адаптациях делаем пороги более мягкими
        dynamic_ignore_threshold *= 1.2
        dynamic_dampen_threshold *= 1.1

    return {
        "energy_level": energy_level,
        "stability_level": stability_level,
        "integrity_level": integrity_level,
        "time_perception": time_perception,
        "circadian_phase": circadian_phase,
        "circadian_modifier": circadian_modifier,
        "recovery_efficiency": self_state.recovery_efficiency,
        "stability_modifier": self_state.stability_modifier,
        "behavior_thresholds": behavior_thresholds,
        "behavior_sensitivity": behavior_sensitivity,
        "behavior_coefficients": behavior_coefficients,
        "significance_thresholds": significance_thresholds,
        "event_type_sensitivity": event_type_sensitivity,
        "response_coefficients": response_coefficients,
        "meaning_significance": meaning.significance,
        "event_type": event_type,
        "dynamic_ignore_threshold": dynamic_ignore_threshold,
        "dynamic_dampen_threshold": dynamic_dampen_threshold,
        "adaptation_analysis": adaptation_analysis,
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

    return rules.get(event_type, {"can_amplify": True, "can_ignore": True, "prefer_absorb": True})


def _select_response_pattern(
    memory_analysis: dict,
    context_analysis: dict,
    event_rules: dict,
    meaning: Meaning,
    self_state: SelfState,
) -> str:
    """
    Финальный выбор паттерна реакции на основе всех анализов с интеграцией Learning/Adaptation.
    """
    weighted_avg = memory_analysis["weighted_avg"]
    max_sig = memory_analysis["max_sig"]
    distribution = memory_analysis["distribution"]

    # Извлечение параметров из контекста
    energy_level = context_analysis["energy_level"]
    stability_level = context_analysis["stability_level"]
    integrity_level = context_analysis["integrity_level"]
    time_perception = context_analysis["time_perception"]
    circadian_phase = context_analysis["circadian_phase"]
    circadian_modifier = context_analysis["circadian_modifier"]
    meaning_sig = context_analysis["meaning_significance"]

    # Параметры Learning/Adaptation
    behavior_coefficients = context_analysis.get("behavior_coefficients", {})
    response_coefficients = context_analysis.get("response_coefficients", {})
    behavior_sensitivity = context_analysis.get("behavior_sensitivity", {})
    event_type = context_analysis.get("event_type", "unknown")
    adaptation_analysis = context_analysis.get("adaptation_analysis", {})

    # Динамические пороги
    dynamic_ignore_threshold = context_analysis.get("dynamic_ignore_threshold", 0.1)
    dynamic_dampen_threshold = context_analysis.get("dynamic_dampen_threshold", 0.3)

    # Коэффициенты для паттернов (приоритет: behavior_coefficients > response_coefficients)
    dampen_coeff = behavior_coefficients.get("dampen", response_coefficients.get("dampen", 0.5))
    absorb_coeff = behavior_coefficients.get("absorb", response_coefficients.get("absorb", 1.0))
    amplify_coeff = behavior_coefficients.get("amplify", response_coefficients.get("amplify", 1.0))
    ignore_coeff = behavior_coefficients.get("ignore", response_coefficients.get("ignore", 0.0))

    # Модификация коэффициентов на основе субъективного времени
    # При ускоренном времени уменьшаем absorb/amplify для более консервативного поведения
    # При замедленном времени увеличиваем absorb/amplify для более вдумчивого подхода
    time_ratio = self_state.subjective_time / self_state.age if self_state.age > 0 else 1.0
    if time_ratio > 1.1:  # Ускоренное восприятие
        absorb_coeff *= 0.9
        amplify_coeff *= 0.8
        dampen_coeff *= 1.1
    elif time_ratio < 0.9:  # Замедленное восприятие
        absorb_coeff *= 1.2
        amplify_coeff *= 1.1
        dampen_coeff *= 0.9

    # Чувствительность к типу события для дополнительных модификаций
    event_sensitivity = behavior_sensitivity.get(event_type, 0.2)

    # === Правило 1: Высокая концентрация значимых воспоминаний ===
    if distribution == "high_concentrated" or max_sig > 0.8:
        # Учитываем коэффициент dampen при высокой концентрации
        if (
            event_rules.get("can_amplify", True)
            and stability_level == "low"
            and energy_level == "low"
            and amplify_coeff > absorb_coeff
        ):
            # При низкой стабильности и энергии можем усилить положительные эффекты
            if event_rules.get("positive_event", False) and meaning_sig > dynamic_dampen_threshold:
                return "amplify"
        return "dampen"

    # === Правило 2: Низкая энергия - консервативный подход ===
    # Учитываем адаптивные коэффициенты и динамические пороги
    if energy_level == "low":
        is_positive_and_unstable = (
            stability_level == "low"
            and event_rules.get("positive_event", False)
            and event_rules.get("can_amplify", True)
            and meaning_sig > dynamic_dampen_threshold * (1 + event_sensitivity)
        )

        if is_positive_and_unstable and amplify_coeff > dampen_coeff:
            return "amplify"  # Исключение для положительных событий при низкой стабильности
        elif weighted_avg > dynamic_dampen_threshold or meaning_sig > dynamic_dampen_threshold:
            return "dampen"
        elif meaning_sig < dynamic_ignore_threshold and event_rules.get("can_ignore", True):
            return "ignore"

    # === Правило 3: Высокая стабильность - смягчение эффектов ===
    # Учитываем коэффициент dampen при высокой стабильности
    if stability_level == "high":
        adjusted_dampen_threshold = dynamic_dampen_threshold * dampen_coeff
        if weighted_avg > adjusted_dampen_threshold or meaning_sig > adjusted_dampen_threshold:
            return "dampen"

    # === Правило 4: Низкая стабильность - усиление положительных эффектов ===
    if stability_level == "low" and event_rules.get("can_amplify", True):
        amplify_threshold = dynamic_dampen_threshold * (1 + event_sensitivity)
        if (
            event_rules.get("positive_event", False)
            and meaning_sig > amplify_threshold
            and amplify_coeff > absorb_coeff
        ):
            return "amplify"

    # === Правило 5: Восприятие времени влияет на пороги принятия решений ===
    # Субъективное время напрямую влияет на чувствительность к изменениям
    time_sensitivity_modifier = 1.0
    if time_perception == "accelerated":
        # При ускоренном времени система более чувствительна, быстрее реагирует
        time_sensitivity_modifier = 0.7  # Понижаем пороги для более быстрой реакции
        accelerated_threshold = dynamic_dampen_threshold * time_sensitivity_modifier
        if weighted_avg > accelerated_threshold or meaning_sig > accelerated_threshold:
            return "dampen"
    elif time_perception == "slowed":
        # При замедленном времени система более вдумчива, использует более строгие пороги
        time_sensitivity_modifier = 1.3  # Повышаем пороги для более осторожных решений
        slowed_threshold = dynamic_dampen_threshold * time_sensitivity_modifier
        if weighted_avg > slowed_threshold or meaning_sig > slowed_threshold:
            return "dampen"

    # === Правило 6: Низкая целостность - осторожный подход ===
    if integrity_level == "low":
        integrity_threshold = dynamic_dampen_threshold * 0.9  # Немного мягче для целостности
        if weighted_avg > integrity_threshold or meaning_sig > integrity_threshold:
            return "dampen"

    # === Правило 7: Циркадные ритмы - модификация поведения по фазам ===
    # Учитываем циркадную фазу для корректировки порогов и предпочтений
    circadian_adjusted_ignore_threshold = dynamic_ignore_threshold * circadian_modifier
    circadian_adjusted_dampen_threshold = dynamic_dampen_threshold * circadian_modifier

    if circadian_phase == "dawn":
        # Рассвет: более осторожный подход, пониженные пороги
        if weighted_avg > circadian_adjusted_dampen_threshold * 0.9:
            return "dampen"
    elif circadian_phase == "day":
        # День: более активный подход, повышенные пороги для действий
        if (event_rules.get("can_amplify", True) and
            event_rules.get("positive_event", False) and
            meaning_sig > circadian_adjusted_dampen_threshold * 1.1 and
            energy_level == "high"):
            return "amplify"
    elif circadian_phase == "dusk":
        # Закат: умеренный подход, баланс между активностью и осторожностью
        pass  # Используем базовые правила без модификации
    elif circadian_phase == "night":
        # Ночь: консервативный подход, пониженные пороги для игнорирования
        if (weighted_avg < circadian_adjusted_ignore_threshold * 1.2 and
            meaning_sig < circadian_adjusted_ignore_threshold * 1.2 and
            event_rules.get("can_ignore", True)):
            return "ignore"

    # === Правило 8: Специфические правила по типу события с учетом коэффициентов ===
    if event_rules.get("prefer_dampen", False):
        if (
            weighted_avg > dynamic_dampen_threshold * dampen_coeff
            or meaning_sig > dynamic_dampen_threshold * dampen_coeff
        ):
            return "dampen"

    if (
        event_rules.get("prefer_absorb", False)
        and weighted_avg <= dynamic_dampen_threshold * absorb_coeff
    ):
        return "absorb"

    if event_rules.get("can_ignore", True):
        ignore_threshold = event_rules.get("ignore_threshold", dynamic_ignore_threshold)
        if (
            weighted_avg < ignore_threshold * ignore_coeff
            and meaning_sig < ignore_threshold * ignore_coeff
        ):
            return "ignore"

    # === Правило 7.5: Контекстная осведомленность на основе истории адаптаций ===
    # Анализ трендов адаптаций для корректировки поведения
    trend_direction = adaptation_analysis.get("trend_direction", "neutral")
    adaptation_stability = adaptation_analysis.get("adaptation_stability", "unknown")
    avg_change_magnitude = adaptation_analysis.get("avg_change_magnitude", 0.0)

    # Корректировка коэффициентов на основе тренда адаптаций
    trend_modifier = 1.0
    if trend_direction == "increasing" and adaptation_stability == "volatile":
        # При росте и волатильности - более осторожный подход
        trend_modifier = 0.9
        if event_rules.get("can_amplify", True) and meaning_sig > dynamic_dampen_threshold:
            # В условиях волатильности уменьшаем вероятность усиления
            amplify_coeff *= trend_modifier
    elif trend_direction == "stable" and adaptation_stability == "stable":
        # При стабильности - более уверенный подход
        trend_modifier = 1.1
        if event_rules.get("positive_event", False) and stability_level == "medium":
            # В стабильных условиях можем быть более смелыми с положительными событиями
            absorb_coeff *= trend_modifier

    # === Правило 8: Взвешенный анализ средней значимости с адаптивными коэффициентами ===
    adjusted_ignore_threshold = dynamic_ignore_threshold * ignore_coeff
    adjusted_absorb_threshold = dynamic_dampen_threshold * absorb_coeff
    adjusted_dampen_threshold = dynamic_dampen_threshold * dampen_coeff

    # Финальная корректировка порогов на основе контекста адаптаций
    if adaptation_stability == "volatile":
        # При волатильных адаптациях смещаем пороги к более осторожному поведению
        adjusted_ignore_threshold *= 1.1
        adjusted_absorb_threshold *= 0.95
        adjusted_dampen_threshold *= 0.9

    if weighted_avg < adjusted_ignore_threshold and meaning_sig < adjusted_ignore_threshold:
        return "ignore"
    elif weighted_avg < adjusted_absorb_threshold and meaning_sig < adjusted_absorb_threshold:
        return "absorb"
    elif weighted_avg >= adjusted_dampen_threshold or meaning_sig >= adjusted_dampen_threshold:
        return "dampen"
    else:
        return "absorb"

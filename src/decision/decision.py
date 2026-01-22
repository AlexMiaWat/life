"""
Простая функция выбора паттерна реакции.

Упрощенная версия DecisionEngine без декомпозиции на компоненты.
"""
from typing import List, Dict, Any

from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState






def decide_response(self_state: SelfState, meaning: Meaning, enable_performance_monitoring: bool = False, adaptation_manager=None) -> str:
    """
    Простой выбор паттерна реакции на основе базовых условий.

    Упрощенная логика без декомпозиции на компоненты.

    Args:
        self_state: Текущее состояние системы
        meaning: Текущий meaning
        enable_performance_monitoring: Включить мониторинг производительности
        adaptation_manager: AdaptationManager (игнорируется для простоты)

    Returns:
        Выбранный паттерн реакции: "ignore", "absorb", "dampen", "amplify"
    """
    import time

    start_time = time.time() if enable_performance_monitoring else None

    # Простая логика выбора паттерна
    pattern = _simple_pattern_selection(self_state, meaning)

    # Мониторинг производительности
    if enable_performance_monitoring and start_time is not None:
        execution_time = time.time() - start_time
        if execution_time > 0.01:
            print(f"Decision performance: {execution_time:.4f}s")

    return pattern


def _simple_pattern_selection(self_state: SelfState, meaning: Meaning) -> str:
    """
    Простая логика выбора паттерна реакции.

    Args:
        self_state: Текущее состояние системы
        meaning: Текущий meaning

    Returns:
        Паттерн реакции
    """
    # Базовые условия
    energy_low = self_state.energy < 30
    stability_low = self_state.stability < 0.3
    integrity_low = self_state.integrity < 0.3

    # Анализ активированной памяти
    activated = self_state.activated_memory or []
    if activated:
        max_significance = max(entry.meaning_significance for entry in activated)
        avg_significance = sum(entry.meaning_significance for entry in activated) / len(activated)
        high_significance = max_significance > 0.5
    else:
        max_significance = 0.0
        avg_significance = 0.0
        high_significance = False

    # Определение типа события из meaning
    event_type = getattr(meaning, 'primary_emotion', 'neutral')
    is_positive = event_type in ['joy', 'hope', 'love', 'curiosity', 'insight']
    is_negative = event_type in ['fear', 'anger', 'sadness', 'confusion', 'void']

    # Анализ significance из meaning
    meaning_high_significance = meaning.significance >= 0.5

    # Простые правила выбора паттерна

    # 1. При низкой энергии и стабильности - консервативный подход
    if energy_low and stability_low and not (is_positive and high_significance):
        return "dampen"

    # 3. При низкой целостности - осторожный подход
    if integrity_low and avg_significance > 0.4:
        return "dampen"

    # 4. Положительные события - усиливать
    if is_positive and (high_significance or meaning_high_significance):
        return "amplify"

    # 5. Негативные события - гасить
    if is_negative:
        return "dampen"

    # 6. Высокая значимость в meaning - гасить
    if meaning_high_significance:
        return "dampen"

    # 7. Высокая значимость в памяти - гасить
    if high_significance:
        return "dampen"

    # 6. По умолчанию - поглощать
    return "absorb"









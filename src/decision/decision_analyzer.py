"""
Decision Analyzer - анализ паттернов и контекста

Отвечает за анализ активированной памяти, системного контекста и паттернов адаптаций.
"""
import math
from typing import List, Dict, Any, Optional
from src.meaning.meaning import Meaning
from src.memory.memory import MemoryEntry
from src.state.self_state import SelfState


class DecisionAnalyzer:
    """
    Анализирует контекст для принятия решений.

    Отвечает за:
    - Анализ активированной памяти
    - Анализ системного контекста
    """

    def __init__(self, adaptation_manager=None):
        """
        Инициализация анализатора.

        Args:
            adaptation_manager: AdaptationManager для анализа адаптаций
        """
        self.adaptation_manager = adaptation_manager

    def analyze_activated_memory(self, activated: List[MemoryEntry]) -> Dict[str, Any]:
        """
        Комплексный анализ активированной памяти.

        Args:
            activated: Список активированных записей памяти

        Returns:
            Анализ памяти с метриками
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

    def analyze_system_context(self, self_state: SelfState, meaning: Meaning, adaptation_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Анализ контекста системы для принятия решения.

        Args:
            self_state: Текущее состояние системы
            meaning: Текущий meaning
            adaptation_analysis: Предварительный анализ адаптаций (опционально)

        Returns:
            Параметры контекста
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
        circadian_phase_rad = self_state.circadian_phase
        if circadian_phase_rad < math.pi / 2:
            circadian_phase = "dawn"
            circadian_modifier = 0.8
        elif circadian_phase_rad < math.pi:
            circadian_phase = "day"
            circadian_modifier = 1.2
        elif circadian_phase_rad < 3 * math.pi / 2:
            circadian_phase = "dusk"
            circadian_modifier = 0.9
        else:
            circadian_phase = "night"
            circadian_modifier = 0.7

        # Параметры Learning/Adaptation
        adaptation_params = getattr(self_state, "adaptation_params", {})
        behavior_thresholds = adaptation_params.get("behavior_thresholds", {})
        behavior_sensitivity = adaptation_params.get("behavior_sensitivity", {})

        learning_params = getattr(self_state, "learning_params", {})
        significance_thresholds = learning_params.get("significance_thresholds", {})
        event_type_sensitivity = learning_params.get("event_type_sensitivity", {})

        # Анализ истории адаптаций через AdaptationManager
        if self.adaptation_manager:
            adaptation_analysis = self.adaptation_manager.analyze_adaptation_trends(
                getattr(self_state, "adaptation_history", [])
            )
        else:
            # Fallback: локальный анализ (для обратной совместимости)
            adaptation_analysis = self._analyze_adaptation_history(self_state)

        # Динамические пороги
        event_type = getattr(meaning, "event_type", "unknown")
        base_sensitivity = event_type_sensitivity.get(event_type, 0.2)

        # Адаптивные пороги
        dynamic_ignore_threshold = self._calculate_dynamic_threshold(
            base_threshold=0.1,
            sensitivity=base_sensitivity,
            energy_level=energy_level,
            stability_level=stability_level,
        )

        dynamic_dampen_threshold = self._calculate_dynamic_threshold(
            base_threshold=0.3,
            sensitivity=base_sensitivity,
            energy_level=energy_level,
            stability_level=stability_level,
        )

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
            "significance_thresholds": significance_thresholds,
            "event_type_sensitivity": event_type_sensitivity,
            "meaning_significance": meaning.significance,
            "event_type": event_type,
            "dynamic_ignore_threshold": dynamic_ignore_threshold,
            "dynamic_dampen_threshold": dynamic_dampen_threshold,
            "adaptation_analysis": adaptation_analysis,
        }

    def _analyze_adaptation_history(self, self_state: SelfState) -> Dict[str, Any]:
        """
        Анализ истории адаптаций.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Анализ трендов адаптаций
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

                            param_key = f"{param_group}.{param_name}"
                            param_change_counts[param_key] = param_change_counts.get(param_key, 0) + 1

        # Определение тренда
        if positive_changes > negative_changes * 1.5:
            trend_direction = "increasing"
        elif negative_changes > positive_changes * 1.5:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"

        avg_change_magnitude = total_magnitude / len(recent_history) if recent_history else 0.0

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
        self,
        base_threshold: float,
        sensitivity: float,
        energy_level: str,
        stability_level: str,
    ) -> float:
        """
        Вычисление динамического порога.

        Args:
            base_threshold: Базовое значение порога
            sensitivity: Чувствительность к типу события
            energy_level: Уровень энергии
            stability_level: Уровень стабильности

        Returns:
            Адаптивный порог
        """
        # Модификатор на основе чувствительности
        sensitivity_modifier = 0.5 + sensitivity

        # Модификаторы состояния системы
        energy_modifier = 0.8 if energy_level == "low" else 1.2
        stability_modifier = (
            0.9 if stability_level == "low" else 1.1 if stability_level == "high" else 1.0
        )

        adaptive_threshold = (
            base_threshold * sensitivity_modifier * energy_modifier * stability_modifier
        )

        return max(0.05, min(0.8, adaptive_threshold))
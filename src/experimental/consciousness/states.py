"""
Состояния сознания - Consciousness States.

Компонент для управления различными состояниями сознания и переходами между ними.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


@dataclass
class ConsciousnessState:
    """
    Определение состояния сознания.
    """

    name: str
    description: str
    entry_conditions: Dict[str, Any] = field(default_factory=dict)
    maintenance_conditions: Dict[str, Any] = field(default_factory=dict)
    exit_conditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)  # Эффекты на систему
    transition_logic: Optional[Callable] = None  # Логика перехода

    def can_enter(self, metrics: Dict[str, float]) -> bool:
        """
        Проверить, можно ли войти в это состояние.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если вход возможен
        """
        for condition_key, condition_value in self.entry_conditions.items():
            metric_value = metrics.get(condition_key, 0.0)

            if isinstance(condition_value, dict):
                # Сложное условие с оператором
                operator = condition_value.get("operator", ">=")
                threshold = condition_value.get("value", 0.0)

                if operator == ">=" and not (metric_value >= threshold):
                    return False
                elif operator == ">" and not (metric_value > threshold):
                    return False
                elif operator == "<=" and not (metric_value <= threshold):
                    return False
                elif operator == "<" and not (metric_value < threshold):
                    return False
                elif operator == "==" and not (metric_value == threshold):
                    return False
            else:
                # Простое условие
                if metric_value < condition_value:
                    return False

        return True

    def should_maintain(self, metrics: Dict[str, float]) -> bool:
        """
        Проверить, следует ли поддерживать это состояние.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если состояние следует поддерживать
        """
        for condition_key, condition_value in self.maintenance_conditions.items():
            metric_value = metrics.get(condition_key, 0.0)
            if metric_value < condition_value:
                return False
        return True

    def should_exit(self, metrics: Dict[str, float]) -> bool:
        """
        Проверить, следует ли выйти из этого состояния.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если следует выйти
        """
        for condition_key, condition_value in self.exit_conditions.items():
            metric_value = metrics.get(condition_key, 0.0)
            if metric_value < condition_value:
                return True
        return False


class ConsciousnessStates:
    """
    Управление различными состояниями сознания.

    Определяет состояния сознания, управляет переходами между ними,
    и координирует эффекты состояний на систему.
    """

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Инициализация управления состояниями сознания.

        Args:
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)

        # Текущее состояние
        self.current_state: Optional[ConsciousnessState] = None
        self.state_entry_time = 0.0
        self.state_duration = 0.0

        # История переходов
        self._state_history: List[Dict[str, Any]] = []

        # Определение состояний сознания
        self._states = self._define_states()

        # Статистика
        self._transition_count = 0
        self._state_durations: Dict[str, float] = {}

        # Инициализация в состоянии awake
        self.enter_state("awake", {})

        self.logger.log_event(
            {
                "event_type": "consciousness_states_initialized",
                "available_states": list(self._states.keys()),
            }
        )

    def _define_states(self) -> Dict[str, ConsciousnessState]:
        """
        Определить все возможные состояния сознания.

        Returns:
            Словарь состояний сознания
        """
        return {
            "unconscious": ConsciousnessState(
                name="unconscious",
                description="Отсутствие активного сознания, минимальная обработка",
                entry_conditions={
                    "consciousness_level": {"operator": "<", "value": 0.1},
                    "energy": {"operator": "<", "value": 0.3},
                },
                maintenance_conditions={"consciousness_level": 0.05, "energy": 0.2},
                effects={
                    "processing_speed": 0.1,
                    "decision_quality": 0.1,
                    "learning_rate": 0.0,
                    "response_time": 2.0,
                },
            ),
            "dreaming": ConsciousnessState(
                name="dreaming",
                description="Сниженное сознание, фоновые процессы, низкая энергия",
                entry_conditions={
                    "consciousness_level": {"operator": "<", "value": 0.2},
                    "energy": {"operator": "<", "value": 0.5},
                },
                maintenance_conditions={"consciousness_level": 0.1, "energy": 0.3},
                exit_conditions={"energy": 0.6},  # Выход при восстановлении энергии
                effects={
                    "processing_speed": 0.3,
                    "decision_quality": 0.3,
                    "learning_rate": 0.2,
                    "creativity": 1.2,
                    "response_time": 1.5,
                },
            ),
            "awake": ConsciousnessState(
                name="awake",
                description="Базовое бодрствование, нормальная обработка событий",
                entry_conditions={"consciousness_level": {"operator": ">=", "value": 0.1}},
                maintenance_conditions={"consciousness_level": 0.1, "energy": 0.4},
                effects={
                    "processing_speed": 0.8,
                    "decision_quality": 0.7,
                    "learning_rate": 0.6,
                    "response_time": 1.0,
                },
            ),
            "flow": ConsciousnessState(
                name="flow",
                description="Состояние потока: высокая концентрация и эффективность",
                entry_conditions={
                    "consciousness_level": {"operator": ">=", "value": 0.3},
                    "energy": {"operator": ">=", "value": 0.7},
                    "stability": {"operator": ">=", "value": 0.8},
                    "cognitive_load": {"operator": "<=", "value": 0.6},
                },
                maintenance_conditions={"energy": 0.6, "stability": 0.7, "attention_focus": 0.8},
                exit_conditions={
                    "energy": 0.4,  # Выход при снижении энергии
                    "cognitive_load": 0.8,  # Выход при перегрузке
                },
                effects={
                    "processing_speed": 1.2,
                    "decision_quality": 1.1,
                    "learning_rate": 1.0,
                    "creativity": 1.1,
                    "error_rate": 0.7,
                    "response_time": 0.8,
                },
            ),
            "reflective": ConsciousnessState(
                name="reflective",
                description="Рефлексивное состояние: анализ поведения и самооценка",
                entry_conditions={
                    "consciousness_level": {"operator": ">=", "value": 0.3},
                    "self_reflection_score": {"operator": ">=", "value": 0.4},
                    "cognitive_load": {"operator": "<=", "value": 0.7},
                },
                maintenance_conditions={"self_reflection_score": 0.3, "energy": 0.5},
                exit_conditions={
                    "cognitive_load": 0.9,  # Выход при перегрузке
                    "self_reflection_score": 0.2,  # Выход при снижении рефлексии
                },
                effects={
                    "processing_speed": 0.7,
                    "decision_quality": 1.0,
                    "learning_rate": 1.2,
                    "self_analysis": 1.5,
                    "response_time": 1.2,
                },
            ),
            "meta": ConsciousnessState(
                name="meta",
                description="Метакогнитивное состояние: анализ собственных процессов мышления",
                entry_conditions={
                    "consciousness_level": {"operator": ">=", "value": 0.5},
                    "meta_cognition_depth": {"operator": ">=", "value": 0.4},
                    "energy": {"operator": ">=", "value": 0.6},
                    "cognitive_load": {"operator": "<=", "value": 0.5},
                },
                maintenance_conditions={
                    "meta_cognition_depth": 0.3,
                    "energy": 0.5,
                    "stability": 0.7,
                },
                exit_conditions={
                    "energy": 0.4,  # Выход при снижении энергии
                    "cognitive_load": 0.7,  # Выход при перегрузке
                    "meta_cognition_depth": 0.2,  # Выход при снижении метакогниции
                },
                effects={
                    "processing_speed": 0.6,
                    "decision_quality": 1.3,
                    "learning_rate": 1.4,
                    "optimization_capability": 1.5,
                    "abstract_reasoning": 1.3,
                    "response_time": 1.5,
                },
            ),
        }

    def get_current_state(self) -> Optional[ConsciousnessState]:
        """
        Получить текущее состояние сознания.

        Returns:
            Текущее состояние или None
        """
        return self.current_state

    def get_current_state_name(self) -> str:
        """
        Получить имя текущего состояния сознания.

        Returns:
            Имя текущего состояния
        """
        return self.current_state.name if self.current_state else "unknown"

    def can_enter_flow_state(self, metrics: Dict[str, float]) -> bool:
        """
        Проверить возможность входа в состояние потока.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если вход в flow state возможен
        """
        flow_state = self._states.get("flow")
        return flow_state.can_enter(metrics) if flow_state else False

    def can_enter_reflective_state(self, metrics: Dict[str, float]) -> bool:
        """
        Проверить возможность входа в рефлексивное состояние.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если вход в reflective state возможен
        """
        reflective_state = self._states.get("reflective")
        return reflective_state.can_enter(metrics) if reflective_state else False

    def can_enter_meta_state(self, metrics: Dict[str, float]) -> bool:
        """
        Проверить возможность входа в метакогнитивное состояние.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если вход в meta state возможен
        """
        meta_state = self._states.get("meta")
        return meta_state.can_enter(metrics) if meta_state else False

    def enter_flow_state(self, metrics: Dict[str, float]) -> bool:
        """
        Попытаться войти в состояние потока.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если вход успешен
        """
        return self.enter_state("flow", metrics)

    def enter_reflective_state(self, metrics: Dict[str, float]) -> bool:
        """
        Попытаться войти в рефлексивное состояние.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если вход успешен
        """
        return self.enter_state("reflective", metrics)

    def enter_meta_state(self, metrics: Dict[str, float]) -> bool:
        """
        Попытаться войти в метакогнитивное состояние.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если вход успешен
        """
        return self.enter_state("meta", metrics)

    def enter_state(self, state_name: str, metrics: Dict[str, float]) -> bool:
        """
        Попытаться войти в указанное состояние.

        Args:
            state_name: Имя состояния
            metrics: Текущие метрики сознания

        Returns:
            True если вход успешен
        """
        if state_name not in self._states:
            self.logger.log_event(
                {
                    "event_type": "state_transition_failed",
                    "target_state": state_name,
                    "reason": "unknown_state",
                }
            )
            return False

        target_state = self._states[state_name]

        # Проверяем условия входа
        if not target_state.can_enter(metrics):
            self.logger.log_event(
                {
                    "event_type": "state_transition_failed",
                    "target_state": state_name,
                    "reason": "entry_conditions_not_met",
                    "metrics": metrics,
                }
            )
            return False

        # Выходим из текущего состояния
        old_state_name = self.current_state.name if self.current_state else "none"
        if self.current_state:
            self._exit_current_state()

        # Входим в новое состояние
        self.current_state = target_state
        self.state_entry_time = time.time()
        self._transition_count += 1

        # Применяем эффекты состояния
        self._apply_state_effects(target_state)

        # Логируем переход
        transition_record = {
            "from_state": old_state_name,
            "to_state": state_name,
            "timestamp": self.state_entry_time,
            "trigger": "manual" if old_state_name != "none" else "initialization",
            "metrics": metrics.copy(),
        }
        self._state_history.append(transition_record)

        self.logger.log_event({"event_type": "state_transition_successful", **transition_record})

        return True

    def handle_state_transitions(self, metrics: Dict[str, float]) -> bool:
        """
        Автоматически обработать переходы между состояниями на основе метрик.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            True если произошел переход состояния
        """
        if not self.current_state:
            # Инициализация состояния
            return self.enter_state("awake", metrics)

        current_state_name = self.current_state.name

        # Проверяем условия поддержания текущего состояния
        if not self.current_state.should_maintain(metrics):
            # Определяем приоритетное состояние для перехода
            target_state = self._find_best_transition_target(metrics)

            if target_state and target_state != current_state_name:
                return self.enter_state(target_state, metrics)

        # Проверяем условия выхода
        elif self.current_state.should_exit(metrics):
            # Переходим в состояние по умолчанию (awake)
            return self.enter_state("awake", metrics)

        return False

    def _find_best_transition_target(self, metrics: Dict[str, float]) -> Optional[str]:
        """
        Найти лучшее целевое состояние для перехода.

        Args:
            metrics: Текущие метрики сознания

        Returns:
            Имя целевого состояния или None
        """
        # Приоритет состояний (от высшего к низшему)
        state_priority = ["meta", "reflective", "flow", "awake", "dreaming", "unconscious"]

        for state_name in state_priority:
            state = self._states.get(state_name)
            if state and state.can_enter(metrics):
                return state_name

        return "awake"  # Fallback

    def _exit_current_state(self) -> None:
        """Выйти из текущего состояния."""
        if self.current_state:
            # Рассчитываем длительность пребывания в состоянии
            duration = time.time() - self.state_entry_time
            self.state_duration = duration

            # Обновляем статистику длительностей
            state_name = self.current_state.name
            if state_name not in self._state_durations:
                self._state_durations[state_name] = 0.0
            self._state_durations[state_name] += duration

            # Сбрасываем эффекты состояния
            self._reset_state_effects(self.current_state)

    def _apply_state_effects(self, state: ConsciousnessState) -> None:
        """
        Применить эффекты состояния к системе.

        Args:
            state: Состояние, эффекты которого нужно применить
        """
        # Заглушка: в реальной реализации здесь будут применяться
        # эффекты к различным компонентам системы
        self.logger.log_event(
            {"event_type": "state_effects_applied", "state": state.name, "effects": state.effects}
        )

    def _reset_state_effects(self, state: ConsciousnessState) -> None:
        """
        Сбросить эффекты состояния.

        Args:
            state: Состояние, эффекты которого нужно сбросить
        """
        # Заглушка: в реальной реализации здесь будут сбрасываться
        # эффекты к различным компонентам системы
        self.logger.log_event({"event_type": "state_effects_reset", "state": state.name})

    def get_state_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику по состояниям сознания.

        Returns:
            Статистика использования состояний
        """
        total_transitions = len(self._state_history)
        total_time = sum(self._state_durations.values())

        state_stats = {}
        for state_name, duration in self._state_durations.items():
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            state_stats[state_name] = {
                "total_duration": duration,
                "percentage": percentage,
                "transitions_to": sum(
                    1 for h in self._state_history if h["to_state"] == state_name
                ),
            }

        return {
            "total_transitions": total_transitions,
            "total_time_in_states": total_time,
            "current_state": self.get_current_state_name(),
            "current_state_duration": time.time() - self.state_entry_time,
            "state_breakdown": state_stats,
        }

    def get_state_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить историю переходов состояний.

        Args:
            limit: Максимальное количество записей

        Returns:
            История переходов (последние limit записей)
        """
        return self._state_history[-limit:] if self._state_history else []

    def reset_states(self) -> None:
        """Сбросить управление состояниями."""
        self._exit_current_state()
        self.current_state = None
        self.state_entry_time = 0.0
        self.state_duration = 0.0
        self._state_history.clear()
        self._transition_count = 0
        self._state_durations.clear()

        self.logger.log_event({"event_type": "consciousness_states_reset"})

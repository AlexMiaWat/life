"""
Lifecycle Manager - управление жизненным циклом системы Life.

Реализует формальное управление этапами жизни системы:
- INIT: инициализация компонентов
- RUN: основной цикл работы
- DEGRADE: деградация при слабости
- DEAD: критическое состояние

Жизненный цикл интегрирован с runtime loop, но предоставляет
явные хуки для управления состояниями.
"""

import time
from enum import Enum
from typing import Dict, List, Any, Optional

from src.state.self_state import SelfState


class LifecycleState(Enum):
    """Состояния жизненного цикла системы Life."""

    INIT = "init"      # Инициализация компонентов
    RUN = "run"        # Основной цикл работы
    DEGRADE = "degrade"  # Деградация при слабости
    DEAD = "dead"      # Критическое состояние


class LifecycleManager:
    """
    Менеджер жизненного цикла системы Life.

    Отвечает за:
    - Управление состояниями жизненного цикла
    - Детекцию слабости и деградации
    - Автоматические переходы между состояниями
    - Ведение истории переходов
    """

    # Константы
    WEAKNESS_THRESHOLD = 0.05        # Порог слабости
    CRITICAL_WEAKNESS_THRESHOLD = 0.0  # Критический порог (все параметры = 0)
    MAX_HISTORY_SIZE = 100           # Максимальный размер истории переходов

    def __init__(
        self,
        self_state: SelfState,
        weakness_threshold: float = WEAKNESS_THRESHOLD
    ):
        """
        Инициализация Lifecycle Manager.

        Args:
            self_state: Состояние системы Life
            weakness_threshold: Порог для определения слабости
        """
        self.self_state = self_state
        self.weakness_threshold = weakness_threshold

        # Текущее состояние
        self.current_state = LifecycleState.INIT
        self.birth_timestamp = time.time()
        self.last_transition_timestamp = time.time()

        # История переходов
        self.transition_history: List[Dict[str, Any]] = []

    @property
    def is_active(self) -> bool:
        """Проверяет, активна ли система (в RUN или DEGRADE состоянии)."""
        return self.current_state in [LifecycleState.RUN, LifecycleState.DEGRADE]

    def on_birth(self) -> None:
        """
        Хук инициализации системы.

        Переводит систему из INIT в RUN состояние.
        Вызывается один раз при запуске системы.
        """
        if self.current_state == LifecycleState.INIT:
            self._transition_to(
                LifecycleState.RUN,
                "system_initialization"
            )

    def on_tick(self) -> None:
        """
        Хук для каждого тика жизненного цикла.

        Выполняет автоматические переходы на основе состояния:
        - RUN -> DEGRADE при детекции слабости
        - DEGRADE -> DEAD при критической слабости
        """
        if self.current_state == LifecycleState.RUN:
            if self._is_weak():
                self._transition_to(
                    LifecycleState.DEGRADE,
                    "weakness_detected"
                )
        elif self.current_state == LifecycleState.DEGRADE:
            if self._is_critically_weak():
                self._transition_to(
                    LifecycleState.DEAD,
                    "critical_weakness_detected"
                )

    def on_degrade(self) -> None:
        """
        Хук принудительной деградации.

        Переводит систему в DEGRADE состояние независимо
        от текущего состояния (кроме DEAD).
        """
        if self.current_state == LifecycleState.DEAD:
            return  # Нельзя деградировать мертвую систему

        if self.current_state != LifecycleState.DEGRADE:
            self._transition_to(
                LifecycleState.DEGRADE,
                "forced_degradation"
            )

    def get_lifecycle_info(self) -> Dict[str, Any]:
        """
        Получить информацию о жизненном цикле.

        Returns:
            Dict с информацией о текущем состоянии жизненного цикла
        """
        current_time = time.time()

        return {
            "current_state": self.current_state,
            "birth_timestamp": self.birth_timestamp,
            "last_transition_timestamp": self.last_transition_timestamp,
            "age_seconds": current_time - self.birth_timestamp,
            "transition_count": len(self.transition_history),
            "transition_history": self.transition_history[-10:],  # Последние 10 переходов
            "is_active": self.is_active,
            "weakness_threshold": self.weakness_threshold,
        }

    def _is_weak(self) -> bool:
        """
        Проверить, находится ли система в состоянии слабости.

        Returns:
            True если хотя бы один параметр < weakness_threshold
        """
        return (
            self.self_state.energy < self.weakness_threshold
            or self.self_state.integrity < self.weakness_threshold
            or self.self_state.stability < self.weakness_threshold
        )

    def _is_critically_weak(self) -> bool:
        """
        Проверить критическую слабость (все параметры = 0).

        Returns:
            True если все параметры равны 0
        """
        return (
            self.self_state.energy == self.CRITICAL_WEAKNESS_THRESHOLD
            and self.self_state.integrity == self.CRITICAL_WEAKNESS_THRESHOLD
            and self.self_state.stability == self.CRITICAL_WEAKNESS_THRESHOLD
        )

    def _transition_to(self, new_state: LifecycleState, reason: str) -> None:
        """
        Выполнить переход в новое состояние.

        Args:
            new_state: Новое состояние
            reason: Причина перехода
        """
        if not self._is_valid_transition(self.current_state, new_state):
            raise ValueError(
                f"Invalid transition from {self.current_state} to {new_state}"
            )

        old_state = self.current_state
        self.current_state = new_state
        self.last_transition_timestamp = time.time()

        # Записываем переход в историю
        self._record_transition(old_state, new_state, reason)

    def _is_valid_transition(self, from_state: LifecycleState, to_state: LifecycleState) -> bool:
        """
        Проверить допустимость перехода между состояниями.

        Допустимые переходы:
        INIT -> RUN
        RUN -> DEGRADE
        DEGRADE -> DEAD

        Returns:
            True если переход допустим
        """
        valid_transitions = {
            LifecycleState.INIT: [LifecycleState.RUN],
            LifecycleState.RUN: [LifecycleState.DEGRADE],
            LifecycleState.DEGRADE: [LifecycleState.DEAD],
            LifecycleState.DEAD: [],  # Из DEAD состояния нет выхода
        }

        return to_state in valid_transitions.get(from_state, [])

    def _record_transition(
        self,
        from_state: LifecycleState,
        to_state: LifecycleState,
        reason: str
    ) -> None:
        """
        Записать переход в историю.

        Args:
            from_state: Исходное состояние
            to_state: Новое состояние
            reason: Причина перехода
        """
        transition_record = {
            "timestamp": time.time(),
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
        }

        self.transition_history.append(transition_record)

        # Ограничиваем размер истории
        if len(self.transition_history) > self.MAX_HISTORY_SIZE:
            self.transition_history = self.transition_history[-self.MAX_HISTORY_SIZE:]
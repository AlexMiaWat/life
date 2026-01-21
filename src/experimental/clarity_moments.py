"""
Система моментов ясности - Clarity Moments System.

Моменты ясности - это особые состояния системы Life, которые возникают при
определенных условиях (высокая стабильность, энергия) и временно повышают
восприимчивость к событиям.
"""

import logging
import time
from typing import Any, Dict, Optional

from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


class ClarityMoments:
    """
    Детектор и менеджер моментов ясности.

    Отвечает за:
    - Детекцию условий для активации моментов ясности
    - Управление состоянием clarity_state и clarity_duration
    - Создание событий clarity_moment
    - Логирование состояний
    """

    # Константы для условий активации
    CLARITY_STABILITY_THRESHOLD = 0.8  # Минимальная стабильность
    CLARITY_ENERGY_THRESHOLD = 0.7  # Минимальная энергия
    CLARITY_DURATION_TICKS = 50  # Длительность в тиках (примерно 5 секунд)
    CLARITY_CHECK_INTERVAL = 10  # Проверка условий каждые N тиков

    # Коэффициент усиления значимости событий во время clarity
    CLARITY_SIGNIFICANCE_BOOST = 1.5

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Инициализация ClarityMoments.

        Args:
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)
        self._last_check_tick = -self.CLARITY_CHECK_INTERVAL  # Начинаем с готовности к проверке
        self._clarity_events_count = 0

    def check_clarity_conditions(self, self_state) -> Optional[Dict[str, Any]]:
        """
        Проверить условия для активации момента ясности.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Dict с данными события clarity_moment если условия выполнены,
            None если условия не выполнены или clarity уже активен
        """
        # Проверяем условия только каждые CLARITY_CHECK_INTERVAL тиков
        if self_state.ticks - self._last_check_tick < self.CLARITY_CHECK_INTERVAL:
            return None

        self._last_check_tick = self_state.ticks

        # Проверяем, не активен ли уже момент ясности
        if getattr(self_state, "clarity_state", False):
            return None

        # Проверяем условия активации
        stability_ok = self_state.stability >= self.CLARITY_STABILITY_THRESHOLD
        energy_ok = self_state.energy >= self.CLARITY_ENERGY_THRESHOLD

        if stability_ok and energy_ok:
            # Создаем событие clarity_moment
            self._clarity_events_count += 1

            clarity_event = {
                "type": "clarity_moment",
                "data": {
                    "clarity_id": self._clarity_events_count,
                    "trigger_conditions": {
                        "stability": self_state.stability,
                        "energy": self_state.energy,
                        "tick": self_state.ticks,
                    },
                    "duration_ticks": self.CLARITY_DURATION_TICKS,
                    "significance_boost": self.CLARITY_SIGNIFICANCE_BOOST,
                },
                "timestamp": time.time(),
                "subjective_timestamp": self_state.subjective_time,
            }

            self.logger.log_event(
                {
                    "event_type": "clarity_moment_activated",
                    "clarity_id": self._clarity_events_count,
                    "stability": self_state.stability,
                    "energy": self_state.energy,
                    "tick": self_state.ticks,
                }
            )

            return clarity_event

        return None

    def activate_clarity_moment(self, self_state) -> None:
        """
        Активировать момент ясности в SelfState.

        Args:
            self_state: Состояние системы для модификации
        """
        # Устанавливаем флаг clarity_state
        self_state.clarity_state = True
        # Устанавливаем длительность
        self_state.clarity_duration = self.CLARITY_DURATION_TICKS
        # Устанавливаем модификатор значимости
        self_state.clarity_modifier = self.CLARITY_SIGNIFICANCE_BOOST

        logger.info(
            "Clarity moment state activated",
            extra={
                "duration": self.CLARITY_DURATION_TICKS,
                "significance_boost": self.CLARITY_SIGNIFICANCE_BOOST,
            },
        )

    def update_clarity_state(self, self_state) -> bool:
        """
        Обновить состояние момента ясности в тике.

        Args:
            self_state: Текущее состояние системы

        Returns:
            True если момент ясности был активен в этом тике
        """
        if not getattr(self_state, "clarity_state", False):
            return False

        # Уменьшаем длительность
        self_state.clarity_duration -= 1

        # Проверяем, не закончился ли момент ясности
        if self_state.clarity_duration <= 0:
            self.deactivate_clarity_moment(self_state)
            return False

        return True

    def deactivate_clarity_moment(self, self_state) -> None:
        """
        Деактивировать момент ясности.

        Args:
            self_state: Состояние системы для модификации
        """
        was_active = getattr(self_state, "clarity_state", False)

        if was_active:
            self_state.clarity_state = False
            self_state.clarity_duration = 0
            self_state.clarity_modifier = 1.0  # Сбрасываем модификатор

            logger.info(
                "Clarity moment deactivated",
                extra={"total_clarity_events": self._clarity_events_count},
            )

    def get_clarity_modifier(self, self_state) -> float:
        """
        Получить модификатор значимости для текущего состояния.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Коэффициент усиления значимости (1.0 если clarity не активен)
        """
        if getattr(self_state, "clarity_state", False):
            return self.CLARITY_SIGNIFICANCE_BOOST
        return 1.0

    def is_clarity_active(self, self_state) -> bool:
        """
        Проверить, активен ли момент ясности.

        Args:
            self_state: Текущее состояние системы

        Returns:
            True если clarity активен
        """
        return getattr(self_state, "clarity_state", False)

    def get_clarity_status(self, self_state) -> Dict[str, Any]:
        """
        Получить текущий статус моментов ясности.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Dict со статусом clarity
        """
        return {
            "active": self.is_clarity_active(self_state),
            "duration_remaining": getattr(self_state, "clarity_duration", 0),
            "total_events": self._clarity_events_count,
            "modifier": self.get_clarity_modifier(self_state),
        }

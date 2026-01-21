"""
Система осознания тишины - Silence Awareness System.

SilenceDetector отслеживает периоды отсутствия событий и генерирует события типа 'silence'
для осознания тишины как значимого состояния внешнего мира.
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .event import Event
from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


@dataclass
class SilenceState:
    """
    Состояние детектора тишины.
    """

    last_event_timestamp: float  # Время последнего события
    silence_start_timestamp: Optional[float] = None  # Начало текущего периода тишины
    silence_events_generated: int = 0  # Количество сгенерированных событий silence
    total_silence_duration: float = 0.0  # Общая длительность периодов тишины


class SilenceDetector:
    """
    Детектор периодов тишины в системе событий.

    Отвечает за:
    - Отслеживание времени последнего события
    - Детекцию периодов тишины
    - Генерацию событий типа 'silence'
    - Управление состоянием тишины
    """

    # Константы для детекции тишины
    SILENCE_THRESHOLD_SECONDS = 30.0  # Минимальная длительность тишины для генерации события
    MAX_SILENCE_EVENTS_PER_HOUR = 12  # Максимум 1 событие каждые 5 минут
    SILENCE_CHECK_INTERVAL_SECONDS = 5.0  # Частота проверки тишины

    # Диапазоны интенсивности для событий silence
    COMFORTABLE_SILENCE_MIN = 0.1  # Минимальная интенсивность комфортной тишины
    COMFORTABLE_SILENCE_MAX = 0.6  # Максимальная интенсивность комфортной тишины
    DISTURBING_SILENCE_MIN = -0.4  # Минимальная интенсивность тревожной тишины
    DISTURBING_SILENCE_MAX = -0.05  # Максимальная интенсивность тревожной тишины

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Инициализация детектора тишины.

        Args:
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)
        self.state = SilenceState(last_event_timestamp=time.time())
        self._last_check_timestamp = time.time()
        self._last_silence_event_timestamp = 0.0

        self.logger.log_event(
            {
                "event_type": "silence_detector_initialized",
                "silence_threshold": self.SILENCE_THRESHOLD_SECONDS,
                "check_interval": self.SILENCE_CHECK_INTERVAL_SECONDS,
            }
        )

    def update_last_event_time(self, event_timestamp: Optional[float] = None) -> None:
        """
        Обновить время последнего события.

        Args:
            event_timestamp: Время события (текущее время, если None)
        """
        current_time = event_timestamp or time.time()
        self.state.last_event_timestamp = current_time

        # Сбросить период тишины при получении события
        if self.state.silence_start_timestamp is not None:
            silence_duration = current_time - self.state.silence_start_timestamp
            self.state.total_silence_duration += silence_duration

            self.logger.log_event(
                {
                    "event_type": "silence_period_ended",
                    "silence_duration": silence_duration,
                    "total_silence_duration": self.state.total_silence_duration,
                }
            )

        self.state.silence_start_timestamp = None

    def check_silence_period(self, current_time: Optional[float] = None) -> Optional[Event]:
        """
        Проверить, не наступил ли период тишины, требующий генерации события.

        Args:
            current_time: Текущее время (time.time() если None)

        Returns:
            Event типа 'silence' если нужно сгенерировать, None иначе
        """
        current_time = current_time or time.time()

        # Проверяем только каждые SILENCE_CHECK_INTERVAL_SECONDS
        if current_time - self._last_check_timestamp < self.SILENCE_CHECK_INTERVAL_SECONDS:
            return None

        self._last_check_timestamp = current_time

        # Проверяем лимит на частоту генерации событий
        time_since_last_silence_event = current_time - self._last_silence_event_timestamp
        min_interval = 3600.0 / self.MAX_SILENCE_EVENTS_PER_HOUR  # секунды между событиями

        if time_since_last_silence_event < min_interval:
            return None

        # Вычисляем длительность текущего периода тишины
        time_since_last_event = current_time - self.state.last_event_timestamp

        # Если тишина только началась, отмечаем начало периода
        if (
            self.state.silence_start_timestamp is None
            and time_since_last_event >= self.SILENCE_THRESHOLD_SECONDS
        ):
            self.state.silence_start_timestamp = (
                self.state.last_event_timestamp + self.SILENCE_THRESHOLD_SECONDS
            )

        # Проверяем, достаточно ли длительная тишина
        if time_since_last_event >= self.SILENCE_THRESHOLD_SECONDS:
            silence_duration = time_since_last_event

            # Генерируем событие silence
            event = self._generate_silence_event(silence_duration, current_time)

            # Обновляем статистику
            self._last_silence_event_timestamp = current_time
            self.state.silence_events_generated += 1

            self.logger.log_event(
                {
                    "event_type": "silence_event_generated",
                    "silence_duration": silence_duration,
                    "event_intensity": event.intensity,
                    "total_silence_events": self.state.silence_events_generated,
                }
            )

            return event

        return None

    def _generate_silence_event(self, silence_duration: float, current_time: float) -> Event:
        """
        Сгенерировать событие типа silence на основе длительности тишины.

        Args:
            silence_duration: Длительность периода тишины в секундах
            current_time: Текущее время

        Returns:
            Event типа 'silence'
        """
        # Определяем тип тишины на основе длительности и случайности
        # Более длительная тишина чаще бывает комфортной (система адаптируется)
        comfort_probability = min(0.7, silence_duration / 300.0)  # 70% при 5+ минутах тишины

        import random

        is_comfortable = random.random() < comfort_probability

        if is_comfortable:
            # Комфортная тишина - положительная интенсивность
            intensity = random.uniform(self.COMFORTABLE_SILENCE_MIN, self.COMFORTABLE_SILENCE_MAX)
        else:
            # Тревожная тишина - отрицательная интенсивность
            intensity = random.uniform(self.DISTURBING_SILENCE_MIN, self.DISTURBING_SILENCE_MAX)

        # Метаданные о тишине
        metadata = {
            "silence_duration": silence_duration,
            "is_comfortable": is_comfortable,
            "comfort_probability": comfort_probability,
            "detector_generated": True,
            "source": "silence_detector",
        }

        return Event(type="silence", intensity=intensity, timestamp=current_time, metadata=metadata)

    def get_silence_status(self) -> Dict[str, Any]:
        """
        Получить текущий статус детектора тишины.

        Returns:
            Dict со статусом silence detector
        """
        current_time = time.time()
        current_silence_duration = 0.0

        if self.state.silence_start_timestamp is not None:
            current_silence_duration = current_time - self.state.silence_start_timestamp
        elif current_time - self.state.last_event_timestamp >= self.SILENCE_THRESHOLD_SECONDS:
            current_silence_duration = current_time - self.state.last_event_timestamp

        return {
            "last_event_timestamp": self.state.last_event_timestamp,
            "current_silence_duration": current_silence_duration,
            "silence_start_timestamp": self.state.silence_start_timestamp,
            "silence_events_generated": self.state.silence_events_generated,
            "total_silence_duration": self.state.total_silence_duration,
            "is_silence_active": current_silence_duration > 0,
            "threshold_reached": current_silence_duration >= self.SILENCE_THRESHOLD_SECONDS,
        }

    def reset_detector(self) -> None:
        """Сбросить состояние детектора тишины."""
        self.state = SilenceState(last_event_timestamp=time.time())
        self._last_check_timestamp = time.time()
        self._last_silence_event_timestamp = 0.0

        self.logger.log_event({"event_type": "silence_detector_reset"})

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Получить статистику производительности детектора.

        Returns:
            Статистика работы детектора
        """
        return {
            "silence_events_generated": self.state.silence_events_generated,
            "total_silence_duration": self.state.total_silence_duration,
            "average_silence_duration": (
                self.state.total_silence_duration / max(1, self.state.silence_events_generated)
                if self.state.silence_events_generated > 0
                else 0.0
            ),
            "silence_threshold": self.SILENCE_THRESHOLD_SECONDS,
            "check_interval": self.SILENCE_CHECK_INTERVAL_SECONDS,
        }

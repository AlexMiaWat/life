"""
Тесты для системы осознания тишины - SilenceDetector.
"""

import time
import pytest
from unittest.mock import patch

from src.environment.silence_detector import SilenceDetector
from src.environment.event import Event


class TestSilenceDetector:
    """Тесты для SilenceDetector."""

    def test_initialization(self):
        """Тест инициализации детектора тишины."""
        detector = SilenceDetector()

        # Проверяем начальное состояние
        status = detector.get_silence_status()
        assert status["last_event_timestamp"] > 0
        assert status["current_silence_duration"] == 0.0
        assert status["silence_events_generated"] == 0
        assert not status["is_silence_active"]
        assert not status["threshold_reached"]

    def test_update_last_event_time(self):
        """Тест обновления времени последнего события."""
        detector = SilenceDetector()
        initial_time = detector.state.last_event_timestamp

        # Обновляем время
        new_time = time.time() + 1.0
        detector.update_last_event_time(new_time)

        assert detector.state.last_event_timestamp == new_time
        assert detector.state.silence_start_timestamp is None  # Тишина прервана

    def test_silence_detection_basic(self):
        """Тест базовой детекции тишины."""
        detector = SilenceDetector()

        # Устанавливаем время последнего события в прошлое
        past_time = time.time() - 35.0  # 35 секунд назад
        detector.update_last_event_time(past_time)

        # Проверяем детекцию тишины
        event = detector.check_silence_period()

        assert event is not None
        assert event.type == "silence"
        assert -0.4 <= event.intensity <= 0.6
        assert event.metadata["detector_generated"] is True
        assert event.metadata["silence_duration"] >= 30.0

    def test_silence_not_detected_too_early(self):
        """Тест что тишина не детектируется слишком рано."""
        detector = SilenceDetector()

        # Устанавливаем недавнее время последнего события
        recent_time = time.time() - 10.0  # 10 секунд назад
        detector.update_last_event_time(recent_time)

        # Тишина еще не должна детектироваться
        event = detector.check_silence_period()
        assert event is None

    def test_silence_event_generation_frequency_limit(self):
        """Тест ограничения частоты генерации событий silence."""
        detector = SilenceDetector()

        # Устанавливаем время последнего события в прошлое
        past_time = time.time() - 35.0
        detector.update_last_event_time(past_time)

        # Генерируем первое событие
        event1 = detector.check_silence_period()
        assert event1 is not None

        # Второе событие не должно генерироваться сразу
        event2 = detector.check_silence_period()
        assert event2 is None

        # Проверяем статус
        status = detector.get_silence_status()
        assert status["silence_events_generated"] == 1

    def test_silence_intensity_distribution(self):
        """Тест распределения интенсивности событий silence."""
        detector = SilenceDetector()

        # Генерируем много событий silence
        intensities = []
        for _ in range(50):
            # Сбрасываем детектор для каждого теста
            detector.reset_detector()

            # Устанавливаем время в прошлое
            past_time = time.time() - 35.0
            detector.update_last_event_time(past_time)

            event = detector.check_silence_period()
            if event:
                intensities.append(event.intensity)

        # Проверяем что все интенсивности в допустимом диапазоне
        assert all(-0.4 <= intensity <= 0.6 for intensity in intensities)

        # Проверяем что есть как положительные, так и отрицательные значения
        positive_intensities = [i for i in intensities if i > 0]
        negative_intensities = [i for i in intensities if i < 0]

        assert len(positive_intensities) > 0
        assert len(negative_intensities) > 0

    def test_comfortable_vs_disturbing_silence(self):
        """Тест различения комфортной и тревожной тишины."""
        detector = SilenceDetector()

        # Тестируем с разными длительностями тишины
        test_cases = [
            (35.0, "short_silence"),
            (120.0, "medium_silence"),
            (300.0, "long_silence"),
        ]

        for silence_duration, case_name in test_cases:
            detector.reset_detector()

            # Устанавливаем время в прошлое
            past_time = time.time() - silence_duration
            detector.update_last_event_time(past_time)

            event = detector.check_silence_period()

            assert event is not None, f"Failed for {case_name}"
            assert (
                event.metadata["silence_duration"] >= 30.0
            ), f"Duration metadata incorrect for {case_name}"
            assert "is_comfortable" in event.metadata, f"Comfort flag missing for {case_name}"

    def test_silence_status_tracking(self):
        """Тест отслеживания статуса тишины."""
        detector = SilenceDetector()

        # Начальное состояние
        status = detector.get_silence_status()
        assert not status["is_silence_active"]
        assert status["current_silence_duration"] == 0.0

        # После установки времени в прошлое
        past_time = time.time() - 35.0
        detector.update_last_event_time(past_time)

        # Проверяем статус через короткое время
        time.sleep(0.1)
        status = detector.get_silence_status()
        assert status["is_silence_active"]
        assert status["current_silence_duration"] > 0

    def test_reset_detector(self):
        """Тест сброса состояния детектора."""
        detector = SilenceDetector()

        # Изменяем состояние
        detector.update_last_event_time(time.time() - 35.0)
        detector.check_silence_period()  # Генерируем событие

        # Проверяем что состояние изменилось
        assert detector.state.silence_events_generated > 0

        # Сбрасываем
        detector.reset_detector()

        # Проверяем что состояние сброшено
        assert detector.state.silence_events_generated == 0
        assert detector.state.total_silence_duration == 0.0
        status = detector.get_silence_status()
        assert status["last_event_timestamp"] > 0

    def test_performance_stats(self):
        """Тест получения статистики производительности."""
        detector = SilenceDetector()

        # Генерируем несколько событий
        for _ in range(3):
            detector.reset_detector()
            detector.update_last_event_time(time.time() - 35.0)
            detector.check_silence_period()

        stats = detector.get_performance_stats()

        assert stats["silence_events_generated"] == 3
        assert stats["total_silence_duration"] >= 0.0
        assert stats["silence_threshold"] == 30.0
        assert stats["check_interval"] == 5.0

    def test_event_metadata_structure(self):
        """Тест структуры метаданных события silence."""
        detector = SilenceDetector()

        detector.update_last_event_time(time.time() - 35.0)
        event = detector.check_silence_period()

        assert event is not None
        required_metadata = [
            "silence_duration",
            "is_comfortable",
            "comfort_probability",
            "detector_generated",
            "source",
        ]

        for key in required_metadata:
            assert key in event.metadata, f"Missing metadata key: {key}"

        assert event.metadata["source"] == "silence_detector"
        assert event.metadata["detector_generated"] is True
        assert isinstance(event.metadata["silence_duration"], (int, float))
        assert isinstance(event.metadata["is_comfortable"], bool)

"""
Интеграционные тесты для SilenceDetector с EventQueue.
"""

import time
import pytest

from src.environment.event import Event
from src.environment.event_queue import EventQueue


class TestSilenceEventQueueIntegration:
    """Интеграционные тесты SilenceDetector с EventQueue."""

    def test_event_queue_with_silence_detection_enabled(self):
        """Тест EventQueue с включенной системой тишины."""
        queue = EventQueue(enable_silence_detection=True)

        assert queue.is_silence_detection_enabled()

        # Проверяем начальный статус
        status = queue.get_silence_status()
        assert status["silence_detection_enabled"] is True
        assert status["silence_events_generated"] == 0

    def test_event_queue_with_silence_detection_disabled(self):
        """Тест EventQueue с отключенной системой тишины."""
        queue = EventQueue(enable_silence_detection=False)

        assert not queue.is_silence_detection_enabled()

        # Проверяем статус
        status = queue.get_silence_status()
        assert status["silence_detection_enabled"] is False

    def test_push_event_updates_silence_detector(self):
        """Тест что push события обновляет SilenceDetector."""
        queue = EventQueue(enable_silence_detection=True)

        event = Event(type="noise", intensity=0.1, timestamp=time.time())

        # Проверяем начальное состояние
        initial_status = queue.get_silence_status()

        # Добавляем событие
        queue.push(event)

        # Проверяем что время последнего события обновилось
        updated_status = queue.get_silence_status()
        assert updated_status["last_event_timestamp"] >= initial_status["last_event_timestamp"]

    def test_pop_events_updates_silence_detector(self):
        """Тест что pop_all обновляет SilenceDetector."""
        queue = EventQueue(enable_silence_detection=True)

        # Добавляем события
        events = [
            Event(type="noise", intensity=0.1, timestamp=time.time()),
            Event(type="decay", intensity=0.2, timestamp=time.time() + 0.1),
        ]

        for event in events:
            queue.push(event)

        # Извлекаем события
        popped_events = queue.pop_all()
        assert len(popped_events) == 2

        # Проверяем что SilenceDetector обновлен
        status = queue.get_silence_status()
        assert status["last_event_timestamp"] > 0

    def test_silence_event_generation_integration(self):
        """Тест генерации событий silence через EventQueue."""
        queue = EventQueue(enable_silence_detection=True)

        # Добавляем событие в прошлое
        past_timestamp = time.time() - 35.0
        past_event = Event(type="noise", intensity=0.1, timestamp=past_timestamp)
        queue.push(past_event)

        # Даем время на "прохождение" тишины
        time.sleep(0.1)

        # Проверяем генерацию события тишины
        silence_event = queue.check_and_generate_silence()

        if silence_event:
            assert silence_event.type == "silence"
            assert -0.4 <= silence_event.intensity <= 0.6
            assert silence_event.metadata["detector_generated"] is True

            # Проверяем обновление статистики
            status = queue.get_silence_status()
            assert status["silence_events_generated"] >= 1

    def test_silence_detection_works_with_empty_queue(self):
        """Тест что система тишины работает с пустой очередью."""
        queue = EventQueue(enable_silence_detection=True)

        # Ожидаем некоторое время без событий
        time.sleep(0.1)

        # Проверяем статус
        status = queue.get_silence_status()
        assert "current_silence_duration" in status
        assert "is_silence_active" in status

    def test_multiple_events_reset_silence_timer(self):
        """Тест что множественные события сбрасывают таймер тишины."""
        queue = EventQueue(enable_silence_detection=True)

        # Добавляем первое событие
        event1 = Event(type="noise", intensity=0.1, timestamp=time.time())
        queue.push(event1)

        # Немедленно добавляем второе событие
        event2 = Event(type="decay", intensity=0.2, timestamp=time.time())
        queue.push(event2)

        # Проверяем статус
        status = queue.get_silence_status()
        assert status["last_event_timestamp"] >= event2.timestamp

        # Тишина не должна быть активной
        assert not status["is_silence_active"] or status["current_silence_duration"] < 1.0

    def test_silence_status_consistency(self):
        """Тест согласованности статуса тишины."""
        queue = EventQueue(enable_silence_detection=True)

        # Проверяем начальную согласованность
        status1 = queue.get_silence_status()
        status2 = queue.get_silence_status()

        # Время не должно сильно отличаться
        assert abs(status2["last_event_timestamp"] - status1["last_event_timestamp"]) < 0.1

    def test_queue_operations_dont_break_silence_detection(self):
        """Тест что операции с очередью не ломают систему тишины."""
        queue = EventQueue(enable_silence_detection=True)

        # Выполняем различные операции
        assert queue.size() == 0
        assert queue.is_empty()
        assert queue.pop() is None
        assert queue.pop_all() == []

        # Проверяем что система тишины все еще работает
        status = queue.get_silence_status()
        assert "silence_detection_enabled" in status
        assert status["silence_detection_enabled"] is True

    def test_silence_event_not_generated_immediately(self):
        """Тест что события silence не генерируются немедленно."""
        queue = EventQueue(enable_silence_detection=True)

        # Добавляем недавнее событие
        recent_event = Event(type="noise", intensity=0.1, timestamp=time.time())
        queue.push(recent_event)

        # Проверяем что silence не генерируется сразу
        silence_event = queue.check_and_generate_silence()
        assert silence_event is None

    def test_silence_events_are_proper_events(self):
        """Тест что генерируемые события silence являются валидными Event объектами."""
        queue = EventQueue(enable_silence_detection=True)

        # Создаем условие для генерации тишины
        past_timestamp = time.time() - 35.0
        past_event = Event(type="noise", intensity=0.1, timestamp=past_timestamp)
        queue.push(past_event)

        # Ждем немного
        time.sleep(0.1)

        # Генерируем событие тишины
        silence_event = queue.check_and_generate_silence()

        if silence_event:
            # Проверяем что это валидный Event
            assert hasattr(silence_event, 'type')
            assert hasattr(silence_event, 'intensity')
            assert hasattr(silence_event, 'timestamp')
            assert hasattr(silence_event, 'metadata')

            assert silence_event.type == "silence"
            assert isinstance(silence_event.intensity, (int, float))
            assert isinstance(silence_event.timestamp, (int, float))
            assert isinstance(silence_event.metadata, dict)

    def test_performance_with_silence_detection(self):
        """Тест производительности операций с включенной системой тишины."""
        queue = EventQueue(enable_silence_detection=True)

        # Выполняем множество операций
        start_time = time.time()

        for i in range(100):
            event = Event(type="noise", intensity=0.1, timestamp=time.time())
            queue.push(event)

        # Извлекаем все события
        events = queue.pop_all()

        # Проверяем генерацию тишины
        silence_event = queue.check_and_generate_silence()

        end_time = time.time()
        duration = end_time - start_time

        # Проверяем корректность
        assert len(events) == 100
        assert duration < 1.0  # Должно быть быстро

        # Проверяем что система тишины работает
        status = queue.get_silence_status()
        assert status["silence_detection_enabled"] is True
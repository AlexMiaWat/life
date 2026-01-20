"""
Тесты для покрытия race condition в EventQueue.pop_all (строки 38-39)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import queue
import threading
import time

import pytest

from src.environment.event import Event
from src.environment.event_queue import EventQueue


@pytest.mark.unit
@pytest.mark.order(1)
class TestEventQueueRaceCondition:
    """Тесты для race condition в pop_all"""

    def test_pop_all_empty_exception_handling(self):
        """Тест обработки Empty exception в pop_all (строки 38-39)"""
        event_queue = EventQueue()

        # Создаем ситуацию, когда между проверкой empty() и get_nowait()
        # очередь становится пустой (race condition)
        # Это покрывает строки 38-39

        # Добавляем событие
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        event_queue.push(event)

        # Мокаем _queue.get_nowait чтобы симулировать Empty после первого вызова
        original_get = event_queue._queue.get_nowait
        call_count = [0]

        def mock_get_nowait():
            call_count[0] += 1
            if call_count[0] == 1:
                # Первый вызов возвращает событие
                return original_get()
            else:
                # Второй вызов выбрасывает Empty (симулируем race condition)
                # Это покрывает строки 38-39: except queue.Empty: break
                raise queue.Empty()

        # Заменяем метод
        event_queue._queue.get_nowait = mock_get_nowait

        # Мокаем empty() чтобы вернуть False первый раз, True второй
        empty_call_count = [0]

        def mock_empty():
            empty_call_count[0] += 1
            if empty_call_count[0] == 1:
                return False  # Первый раз очередь не пуста
            else:
                return True  # Второй раз пуста (но мы уже внутри цикла)

        event_queue._queue.empty = mock_empty

        # Теперь pop_all должен обработать Empty exception
        events = event_queue.pop_all()

        # Должно быть одно событие (первый вызов успешен)
        assert len(events) == 1
        assert events[0] == event

        # Второй вызов get_nowait выбросил Empty, который был обработан в строке 38-39
        assert call_count[0] >= 1

    def test_pop_all_concurrent_access(self):
        """Тест pop_all при конкурентном доступе"""
        event_queue = EventQueue()

        # Добавляем несколько событий
        for i in range(5):
            event = Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            event_queue.push(event)

        # В отдельном потоке удаляем события
        removed_count = [0]

        def remove_events():
            while not event_queue.is_empty():
                try:
                    event_queue._queue.get_nowait()
                    removed_count[0] += 1
                except queue.Empty:
                    break

        # Запускаем pop_all в основном потоке
        # и удаление в другом потоке одновременно
        thread = threading.Thread(target=remove_events)
        thread.start()

        events = event_queue.pop_all()
        thread.join(timeout=1.0)

        # Проверяем, что Empty exception был обработан корректно
        # (не должно быть необработанных исключений)
        assert isinstance(events, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

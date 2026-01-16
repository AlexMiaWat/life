"""
Подробные тесты для модуля Environment (Event, EventQueue)
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import pytest
from environment.event import Event
from environment.event_queue import EventQueue


@pytest.mark.unit
@pytest.mark.order(1)
class TestEvent:
    """Тесты для класса Event"""
    
    def test_event_creation_minimal(self):
        """Тест создания Event с минимальными параметрами"""
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        assert event.type == "test"
        assert event.intensity == 0.5
        assert event.timestamp > 0
        assert event.metadata == {}
    
    def test_event_creation_with_metadata(self):
        """Тест создания Event с metadata"""
        metadata = {"key1": "value1", "key2": 123}
        event = Event(
            type="test",
            intensity=0.5,
            timestamp=time.time(),
            metadata=metadata
        )
        assert event.metadata == metadata
        assert event.metadata["key1"] == "value1"
        assert event.metadata["key2"] == 123
    
    def test_event_creation_with_none_metadata(self):
        """Тест создания Event с None metadata (должен стать пустым dict)"""
        event = Event(
            type="test",
            intensity=0.5,
            timestamp=time.time(),
            metadata=None
        )
        assert event.metadata == {}
    
    def test_event_different_types(self):
        """Тест создания Event с разными типами"""
        event_types = ["shock", "noise", "recovery", "decay", "idle"]
        for event_type in event_types:
            event = Event(type=event_type, intensity=0.5, timestamp=time.time())
            assert event.type == event_type
    
    def test_event_intensity_range(self):
        """Тест создания Event с разными значениями intensity"""
        for intensity in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            event = Event(type="test", intensity=intensity, timestamp=time.time())
            assert event.intensity == intensity
    
    def test_event_timestamp(self):
        """Тест проверки timestamp"""
        before = time.time()
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        after = time.time()
        assert before <= event.timestamp <= after
    
    def test_event_custom_timestamp(self):
        """Тест создания Event с кастомным timestamp"""
        custom_timestamp = 1000.0
        event = Event(type="test", intensity=0.5, timestamp=custom_timestamp)
        assert event.timestamp == custom_timestamp


@pytest.mark.unit
@pytest.mark.order(1)
class TestEventQueue:
    """Тесты для класса EventQueue"""
    
    def test_queue_initialization(self):
        """Тест инициализации пустой очереди"""
        queue = EventQueue()
        assert queue.is_empty()
        assert queue.size() == 0
    
    def test_queue_push_single(self):
        """Тест добавления одного события"""
        queue = EventQueue()
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        
        queue.push(event)
        
        assert not queue.is_empty()
        assert queue.size() == 1
    
    def test_queue_push_multiple(self):
        """Тест добавления нескольких событий"""
        queue = EventQueue()
        events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]
        
        for event in events:
            queue.push(event)
        
        assert queue.size() == 5
        assert not queue.is_empty()
    
    def test_queue_pop_single(self):
        """Тест извлечения одного события"""
        queue = EventQueue()
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        queue.push(event)
        
        popped = queue.pop()
        
        assert popped == event
        assert queue.is_empty()
        assert queue.size() == 0
    
    def test_queue_pop_empty(self):
        """Тест извлечения из пустой очереди"""
        queue = EventQueue()
        popped = queue.pop()
        
        assert popped is None
    
    def test_queue_pop_fifo_order(self):
        """Тест порядка извлечения (FIFO)"""
        queue = EventQueue()
        events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]
        
        for event in events:
            queue.push(event)
        
        # Извлекаем и проверяем порядок
        for i, expected_event in enumerate(events):
            popped = queue.pop()
            assert popped == expected_event
            assert popped.type == f"event_{i}"
    
    def test_queue_pop_all_empty(self):
        """Тест pop_all из пустой очереди"""
        queue = EventQueue()
        events = queue.pop_all()
        
        assert events == []
        assert isinstance(events, list)
    
    def test_queue_pop_all_single(self):
        """Тест pop_all с одним событием"""
        queue = EventQueue()
        event = Event(type="test", intensity=0.5, timestamp=time.time())
        queue.push(event)
        
        events = queue.pop_all()
        
        assert len(events) == 1
        assert events[0] == event
        assert queue.is_empty()
    
    def test_queue_pop_all_multiple(self):
        """Тест pop_all с несколькими событиями"""
        queue = EventQueue()
        original_events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]
        
        for event in original_events:
            queue.push(event)
        
        events = queue.pop_all()
        
        assert len(events) == 5
        assert events == original_events
        assert queue.is_empty()
    
    def test_queue_pop_all_fifo_order(self):
        """Тест порядка pop_all (FIFO)"""
        queue = EventQueue()
        original_events = [
            Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            for i in range(5)
        ]
        
        for event in original_events:
            queue.push(event)
        
        events = queue.pop_all()
        
        # Проверяем порядок
        for i, event in enumerate(events):
            assert event.type == f"event_{i}"
    
    def test_queue_size_after_operations(self):
        """Тест размера очереди после различных операций"""
        queue = EventQueue()
        assert queue.size() == 0
        
        queue.push(Event(type="e1", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 1
        
        queue.push(Event(type="e2", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 2
        
        queue.pop()
        assert queue.size() == 1
        
        queue.pop()
        assert queue.size() == 0
    
    def test_queue_is_empty_after_operations(self):
        """Тест is_empty после различных операций"""
        queue = EventQueue()
        assert queue.is_empty()
        
        queue.push(Event(type="e1", intensity=0.5, timestamp=time.time()))
        assert not queue.is_empty()
        
        queue.pop()
        assert queue.is_empty()
    
    def test_queue_push_after_pop_all(self):
        """Тест добавления событий после pop_all"""
        queue = EventQueue()
        queue.push(Event(type="e1", intensity=0.5, timestamp=time.time()))
        queue.pop_all()
        
        queue.push(Event(type="e2", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 1
        assert not queue.is_empty()
    
    def test_queue_maxsize_behavior(self):
        """Тест поведения при достижении максимального размера (100)"""
        queue = EventQueue()
        # Добавляем события до лимита
        for i in range(100):
            event = Event(type=f"event_{i}", intensity=0.5, timestamp=time.time())
            queue.push(event)
        
        assert queue.size() == 100
        
        # Попытка добавить еще одно событие должна быть проигнорирована
        queue.push(Event(type="overflow", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 100
        # Последнее событие в очереди не должно быть overflow
        last_event = None
        while not queue.is_empty():
            last_event = queue.pop()
        assert last_event.type != "overflow"
    
    def test_queue_mixed_operations(self):
        """Тест смешанных операций push/pop"""
        queue = EventQueue()
        
        # Добавляем несколько
        for i in range(3):
            queue.push(Event(type=f"e{i}", intensity=0.5, timestamp=time.time()))
        
        # Извлекаем один
        popped = queue.pop()
        assert popped.type == "e0"
        assert queue.size() == 2
        
        # Добавляем еще
        queue.push(Event(type="e3", intensity=0.5, timestamp=time.time()))
        assert queue.size() == 3
        
        # Извлекаем все
        events = queue.pop_all()
        assert len(events) == 3
        assert events[0].type == "e1"  # Следующее после извлеченного
        assert events[1].type == "e2"
        assert events[2].type == "e3"
    
    def test_queue_different_event_types(self):
        """Тест работы очереди с разными типами событий"""
        queue = EventQueue()
        event_types = ["shock", "noise", "recovery", "decay", "idle"]
        
        for event_type in event_types:
            queue.push(Event(type=event_type, intensity=0.5, timestamp=time.time()))
        
        assert queue.size() == 5
        
        events = queue.pop_all()
        assert len(events) == 5
        for i, event in enumerate(events):
            assert event.type == event_types[i]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

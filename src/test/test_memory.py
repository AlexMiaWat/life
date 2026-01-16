"""
Подробные тесты для модуля Memory
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import pytest
from memory.memory import MemoryEntry, Memory


class TestMemoryEntry:
    """Тесты для класса MemoryEntry"""
    
    def test_memory_entry_creation(self):
        """Тест создания MemoryEntry с базовыми полями"""
        entry = MemoryEntry(
            event_type="test_event",
            meaning_significance=0.5,
            timestamp=time.time()
        )
        assert entry.event_type == "test_event"
        assert entry.meaning_significance == 0.5
        assert entry.timestamp > 0
        assert entry.feedback_data is None
    
    def test_memory_entry_with_feedback_data(self):
        """Тест создания MemoryEntry с feedback_data"""
        feedback_data = {
            "action_id": "action_123",
            "action_pattern": "dampen",
            "state_delta": {"energy": -1.0}
        }
        entry = MemoryEntry(
            event_type="feedback",
            meaning_significance=0.0,
            timestamp=time.time(),
            feedback_data=feedback_data
        )
        assert entry.feedback_data == feedback_data
        assert entry.feedback_data["action_id"] == "action_123"
    
    def test_memory_entry_different_event_types(self):
        """Тест создания MemoryEntry с разными типами событий"""
        event_types = ["shock", "noise", "recovery", "decay", "idle", "feedback"]
        for event_type in event_types:
            entry = MemoryEntry(
                event_type=event_type,
                meaning_significance=0.3,
                timestamp=time.time()
            )
            assert entry.event_type == event_type
    
    def test_memory_entry_significance_range(self):
        """Тест создания MemoryEntry с разными значениями significance"""
        for sig in [0.0, 0.1, 0.5, 0.9, 1.0]:
            entry = MemoryEntry(
                event_type="test",
                meaning_significance=sig,
                timestamp=time.time()
            )
            assert entry.meaning_significance == sig


class TestMemory:
    """Тесты для класса Memory"""
    
    def test_memory_initialization(self):
        """Тест инициализации пустой Memory"""
        memory = Memory()
        assert len(memory) == 0
        assert isinstance(memory, list)
    
    def test_memory_append_single(self):
        """Тест добавления одного элемента"""
        memory = Memory()
        entry = MemoryEntry(
            event_type="test",
            meaning_significance=0.5,
            timestamp=time.time()
        )
        memory.append(entry)
        assert len(memory) == 1
        assert memory[0] == entry
    
    def test_memory_append_multiple(self):
        """Тест добавления нескольких элементов"""
        memory = Memory()
        for i in range(5):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time()
            )
            memory.append(entry)
        assert len(memory) == 5
        assert memory[0].event_type == "event_0"
        assert memory[4].event_type == "event_4"
    
    def test_memory_clamp_size_at_limit(self):
        """Тест автоматического ограничения размера при достижении лимита (50)"""
        memory = Memory()
        # Добавляем ровно 50 элементов
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time()
            )
            memory.append(entry)
        assert len(memory) == 50
        
        # Добавляем еще один - первый должен быть удален
        entry_51 = MemoryEntry(
            event_type="event_51",
            meaning_significance=0.5,
            timestamp=time.time()
        )
        memory.append(entry_51)
        assert len(memory) == 50
        assert memory[0].event_type == "event_1"  # Первый удален
        assert memory[-1].event_type == "event_51"  # Последний добавлен
    
    def test_memory_clamp_size_over_limit(self):
        """Тест ограничения размера при превышении лимита"""
        memory = Memory()
        # Добавляем 60 элементов
        for i in range(60):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time()
            )
            memory.append(entry)
        # Должно остаться только 50 последних
        assert len(memory) == 50
        assert memory[0].event_type == "event_10"  # Первые 10 удалены
        assert memory[-1].event_type == "event_59"
    
    def test_memory_preserves_order(self):
        """Тест сохранения порядка элементов (FIFO)"""
        memory = Memory()
        entries = []
        for i in range(10):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time()
            )
            entries.append(entry)
            memory.append(entry)
        
        # Проверяем порядок
        for i, entry in enumerate(memory):
            assert entry.event_type == f"event_{i}"
    
    def test_memory_with_feedback_entries(self):
        """Тест работы Memory с Feedback записями"""
        memory = Memory()
        feedback_entry = MemoryEntry(
            event_type="feedback",
            meaning_significance=0.0,
            timestamp=time.time(),
            feedback_data={
                "action_id": "action_1",
                "action_pattern": "dampen",
                "state_delta": {"energy": -1.0}
            }
        )
        memory.append(feedback_entry)
        assert len(memory) == 1
        assert memory[0].event_type == "feedback"
        assert memory[0].feedback_data is not None
    
    def test_memory_mixed_entries(self):
        """Тест работы Memory со смешанными типами записей"""
        memory = Memory()
        # Добавляем разные типы
        types = ["shock", "noise", "feedback", "recovery"]
        for event_type in types:
            entry = MemoryEntry(
                event_type=event_type,
                meaning_significance=0.5 if event_type != "feedback" else 0.0,
                timestamp=time.time(),
                feedback_data={"test": "data"} if event_type == "feedback" else None
            )
            memory.append(entry)
        
        assert len(memory) == 4
        assert memory[0].event_type == "shock"
        assert memory[3].event_type == "recovery"
    
    def test_memory_list_operations(self):
        """Тест стандартных операций списка"""
        memory = Memory()
        entry1 = MemoryEntry("event1", 0.5, time.time())
        entry2 = MemoryEntry("event2", 0.6, time.time())
        
        memory.append(entry1)
        memory.append(entry2)
        
        # Проверка индексации
        assert memory[0] == entry1
        assert memory[1] == entry2
        
        # Проверка итерации
        types = [e.event_type for e in memory]
        assert types == ["event1", "event2"]
        
        # Проверка проверки наличия
        assert entry1 in memory
        assert entry2 in memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

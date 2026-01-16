"""
Подробные тесты для модуля Activation
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import pytest
from activation.activation import activate_memory
from memory.memory import MemoryEntry


class TestActivateMemory:
    """Тесты для функции activate_memory"""
    
    def test_activate_memory_empty_memory(self):
        """Тест активации памяти при пустой памяти"""
        memory = []
        activated = activate_memory("test_event", memory)
        assert activated == []
        assert isinstance(activated, list)
    
    def test_activate_memory_no_matches(self):
        """Тест активации памяти без совпадений по типу"""
        memory = [
            MemoryEntry("event_a", 0.8, time.time()),
            MemoryEntry("event_b", 0.6, time.time()),
            MemoryEntry("event_c", 0.4, time.time())
        ]
        activated = activate_memory("event_x", memory)
        assert activated == []
    
    def test_activate_memory_single_match(self):
        """Тест активации памяти с одним совпадением"""
        memory = [
            MemoryEntry("event_a", 0.5, time.time()),
            MemoryEntry("target_event", 0.8, time.time()),
            MemoryEntry("event_b", 0.3, time.time())
        ]
        activated = activate_memory("target_event", memory)
        assert len(activated) == 1
        assert activated[0].event_type == "target_event"
        assert activated[0].meaning_significance == 0.8
    
    def test_activate_memory_multiple_matches(self):
        """Тест активации памяти с несколькими совпадениями"""
        memory = [
            MemoryEntry("target", 0.3, time.time()),
            MemoryEntry("other", 0.5, time.time()),
            MemoryEntry("target", 0.8, time.time()),
            MemoryEntry("target", 0.6, time.time())
        ]
        activated = activate_memory("target", memory)
        assert len(activated) == 3
        # Должны быть отсортированы по significance (desc)
        assert activated[0].meaning_significance == 0.8
        assert activated[1].meaning_significance == 0.6
        assert activated[2].meaning_significance == 0.3
    
    def test_activate_memory_sorted_by_significance(self):
        """Тест сортировки активированных записей по significance"""
        memory = [
            MemoryEntry("event", 0.1, time.time()),
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("event", 0.3, time.time()),
            MemoryEntry("event", 0.7, time.time())
        ]
        activated = activate_memory("event", memory, limit=10)  # Увеличиваем лимит
        assert len(activated) == 5
        # Проверяем сортировку по убыванию
        for i in range(len(activated) - 1):
            assert activated[i].meaning_significance >= activated[i + 1].meaning_significance
    
    def test_activate_memory_limit_default(self):
        """Тест ограничения количества результатов (по умолчанию limit=3)"""
        memory = [
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.8, time.time()),
            MemoryEntry("event", 0.7, time.time()),
            MemoryEntry("event", 0.6, time.time()),
            MemoryEntry("event", 0.5, time.time())
        ]
        activated = activate_memory("event", memory)
        assert len(activated) == 3
        assert activated[0].meaning_significance == 0.9
        assert activated[1].meaning_significance == 0.8
        assert activated[2].meaning_significance == 0.7
    
    def test_activate_memory_custom_limit(self):
        """Тест активации с кастомным лимитом"""
        memory = [
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.8, time.time()),
            MemoryEntry("event", 0.7, time.time())
        ]
        # Лимит больше количества совпадений
        activated = activate_memory("event", memory, limit=10)
        assert len(activated) == 3
        
        # Лимит меньше количества совпадений
        activated = activate_memory("event", memory, limit=2)
        assert len(activated) == 2
        assert activated[0].meaning_significance == 0.9
        assert activated[1].meaning_significance == 0.8
    
    def test_activate_memory_limit_one(self):
        """Тест активации с лимитом 1"""
        memory = [
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("event", 0.9, time.time()),
            MemoryEntry("event", 0.3, time.time())
        ]
        activated = activate_memory("event", memory, limit=1)
        assert len(activated) == 1
        assert activated[0].meaning_significance == 0.9
    
    def test_activate_memory_limit_zero(self):
        """Тест активации с лимитом 0"""
        memory = [
            MemoryEntry("event", 0.9, time.time())
        ]
        activated = activate_memory("event", memory, limit=0)
        assert len(activated) == 0
    
    def test_activate_memory_preserves_original_memory(self):
        """Тест, что активация не изменяет исходную память"""
        memory = [
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("other", 0.8, time.time())
        ]
        original_length = len(memory)
        activated = activate_memory("event", memory)
        
        assert len(memory) == original_length
        assert memory[0].event_type == "event"
        assert memory[1].event_type == "other"
    
    def test_activate_memory_different_event_types(self):
        """Тест активации для разных типов событий"""
        memory = [
            MemoryEntry("shock", 0.9, time.time()),
            MemoryEntry("noise", 0.3, time.time()),
            MemoryEntry("recovery", 0.7, time.time()),
            MemoryEntry("shock", 0.8, time.time()),
            MemoryEntry("decay", 0.5, time.time())
        ]
        
        # Активация для "shock"
        activated_shock = activate_memory("shock", memory)
        assert len(activated_shock) == 2
        assert all(e.event_type == "shock" for e in activated_shock)
        
        # Активация для "noise"
        activated_noise = activate_memory("noise", memory)
        assert len(activated_noise) == 1
        assert activated_noise[0].event_type == "noise"
    
    def test_activate_memory_with_feedback_entries(self):
        """Тест активации памяти с Feedback записями"""
        memory = [
            MemoryEntry("feedback", 0.0, time.time(), feedback_data={"action_id": "1"}),
            MemoryEntry("event", 0.5, time.time()),
            MemoryEntry("feedback", 0.0, time.time(), feedback_data={"action_id": "2"})
        ]
        # Feedback записи не должны активироваться для обычных событий
        activated = activate_memory("event", memory)
        assert len(activated) == 1
        assert activated[0].event_type == "event"
        
        # Но должны активироваться для "feedback"
        activated_feedback = activate_memory("feedback", memory)
        assert len(activated_feedback) == 2
        assert all(e.event_type == "feedback" for e in activated_feedback)
    
    def test_activate_memory_equal_significance(self):
        """Тест активации при одинаковой significance"""
        memory = [
            MemoryEntry("event", 0.5, time.time() - 2),
            MemoryEntry("event", 0.5, time.time() - 1),
            MemoryEntry("event", 0.5, time.time())
        ]
        activated = activate_memory("event", memory)
        # При одинаковой significance порядок может быть любым, но все должны быть включены
        assert len(activated) == 3
        assert all(e.meaning_significance == 0.5 for e in activated)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

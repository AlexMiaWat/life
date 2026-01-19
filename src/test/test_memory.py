"""
Подробные тесты для модуля Memory
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time

import pytest

from memory.memory import Memory, MemoryEntry


@pytest.mark.unit
@pytest.mark.order(1)
class TestMemoryEntry:
    """Тесты для класса MemoryEntry"""

    def test_memory_entry_creation(self):
        """Тест создания MemoryEntry с базовыми полями"""
        entry = MemoryEntry(
            event_type="test_event", meaning_significance=0.5, timestamp=time.time()
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
            "state_delta": {"energy": -1.0},
        }
        entry = MemoryEntry(
            event_type="feedback",
            meaning_significance=0.0,
            timestamp=time.time(),
            feedback_data=feedback_data,
        )
        assert entry.feedback_data == feedback_data
        assert entry.feedback_data["action_id"] == "action_123"

    def test_memory_entry_different_event_types(self):
        """Тест создания MemoryEntry с разными типами событий"""
        event_types = ["shock", "noise", "recovery", "decay", "idle", "feedback"]
        for event_type in event_types:
            entry = MemoryEntry(
                event_type=event_type, meaning_significance=0.3, timestamp=time.time()
            )
            assert entry.event_type == event_type

    def test_memory_entry_significance_range(self):
        """Тест создания MemoryEntry с разными значениями significance"""
        for sig in [0.0, 0.1, 0.5, 0.9, 1.0]:
            entry = MemoryEntry(
                event_type="test", meaning_significance=sig, timestamp=time.time()
            )
            assert entry.meaning_significance == sig


@pytest.mark.unit
@pytest.mark.order(1)
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
            event_type="test", meaning_significance=0.5, timestamp=time.time()
        )
        memory.append(entry)
        assert len(memory) == 1
        assert memory[0] == entry

    def test_memory_append_multiple(self):
        """Тест добавления нескольких элементов"""
        memory = Memory()
        for i in range(5):
            entry = MemoryEntry(
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
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
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
            )
            memory.append(entry)
        assert len(memory) == 50

        # Добавляем еще один - первый должен быть удален
        entry_51 = MemoryEntry(
            event_type="event_51", meaning_significance=0.5, timestamp=time.time()
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
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
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
                event_type=f"event_{i}", meaning_significance=0.5, timestamp=time.time()
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
                "state_delta": {"energy": -1.0},
            },
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
                feedback_data={"test": "data"} if event_type == "feedback" else None,
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


@pytest.mark.integration
@pytest.mark.order(2)
@pytest.mark.slow
class TestMemoryLoad:
    """Нагрузочные тесты для Memory с большим объемом данных - ROADMAP T.4"""

    def test_memory_performance_with_1000_entries(self):
        """Тест производительности Memory при добавлении 1000 записей"""
        memory = Memory()
        start_time = time.time()

        # Добавляем 1000 записей
        for i in range(1000):
            entry = MemoryEntry(
                event_type=f"event_{i % 10}",  # 10 разных типов
                meaning_significance=0.5,
                timestamp=time.time() + i
            )
            memory.append(entry)

        elapsed = time.time() - start_time

        # Проверяем, что операция выполнилась быстро (< 1 секунда)
        assert elapsed < 1.0, f"Memory append took too long: {elapsed:.3f}s"

        # Проверяем, что осталось только 50 последних записей
        assert len(memory) == 50
        assert memory[0].event_type == "event_0"  # Первая из последних 50
        assert memory[-1].event_type == "event_9"  # Последняя

    def test_memory_performance_with_10000_entries(self):
        """Тест производительности Memory при добавлении 10000 записей"""
        memory = Memory()
        start_time = time.time()

        # Добавляем 10000 записей
        for i in range(10000):
            entry = MemoryEntry(
                event_type=f"event_{i % 20}",
                meaning_significance=0.3 + (i % 10) * 0.07,
                timestamp=time.time() + i
            )
            memory.append(entry)

        elapsed = time.time() - start_time

        # Проверяем производительность (< 5 секунд для 10000 записей)
        assert elapsed < 5.0, f"Memory append took too long: {elapsed:.3f}s"

        # Проверяем корректность ограничения размера
        assert len(memory) == 50
        # Первая запись должна быть из последних 50
        assert memory[0].event_type.startswith("event_")

    def test_memory_iteration_performance(self):
        """Тест производительности итерации по Memory"""
        memory = Memory()

        # Заполняем память до лимита
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time() + i
            )
            memory.append(entry)

        # Тестируем итерацию
        start_time = time.time()
        count = 0
        for entry in memory:
            count += 1
            assert entry is not None
        elapsed = time.time() - start_time

        assert count == 50
        assert elapsed < 0.01, f"Iteration took too long: {elapsed:.3f}s"

    def test_memory_search_performance(self):
        """Тест производительности поиска в Memory"""
        memory = Memory()

        # Заполняем память
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i % 5}",  # 5 разных типов
                meaning_significance=0.5,
                timestamp=time.time() + i
            )
            memory.append(entry)

        # Тестируем поиск всех записей определенного типа
        start_time = time.time()
        shock_entries = [e for e in memory if e.event_type == "event_0"]
        elapsed = time.time() - start_time

        # Должно быть около 10 записей типа "event_0" (50 / 5)
        assert len(shock_entries) == 10
        assert elapsed < 0.01, f"Search took too long: {elapsed:.3f}s"

    def test_memory_memory_usage(self):
        """Тест использования памяти (проверка, что размер ограничен)"""
        memory = Memory()

        # Добавляем много записей
        for i in range(200):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time() + i,
                feedback_data={"data": "x" * 100} if i % 2 == 0 else None
            )
            memory.append(entry)

        # Размер должен быть ограничен 50 записями
        assert len(memory) == 50

        # Проверяем, что старые записи удалены
        # Последние 50 записей должны быть с event_type от "event_150" до "event_199"
        assert memory[0].event_type == "event_150"
        assert memory[-1].event_type == "event_199"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

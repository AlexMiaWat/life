"""
Интеграционные тесты для многоуровневой системы памяти (Memory Hierarchy)
"""

import sys
from pathlib import Path
import time

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.experimental.memory_hierarchy import MemoryHierarchyManager
from src.environment.event import Event
from src.memory.memory import Memory
from src.observability.structured_logger import StructuredLogger


@pytest.mark.integration
class TestMemoryHierarchyIntegration:
    """Интеграционные тесты для многоуровневой системы памяти"""

    def test_episodic_memory_integration(self):
        """Тест интеграции эпизодической памяти с MemoryHierarchyManager"""
        # Создаем компоненты
        memory = Memory()
        logger = StructuredLogger(__name__)
        hierarchy = MemoryHierarchyManager(logger=logger)

        # Подключаем эпизодическую память
        hierarchy.set_episodic_memory(memory)

        # Проверяем, что интеграция работает
        assert hierarchy.episodic_memory is memory

        # Проверяем статус иерархии
        status = hierarchy.get_hierarchy_status()
        assert status["episodic_memory"]["available"] is True
        assert status["episodic_memory"]["status"] == "integrated"

    def test_sensory_to_episodic_transfer_high_intensity(self):
        """Тест переноса событий с высокой интенсивностью из сенсорного буфера в эпизодическую память"""
        # Создаем компоненты
        memory = Memory()
        logger = StructuredLogger(__name__)
        hierarchy = MemoryHierarchyManager(logger=logger)
        hierarchy.set_episodic_memory(memory)

        # Создаем состояние системы
        class MockSelfState:
            def __init__(self):
                self.memory = memory
                self.subjective_time = 1.0

        self_state = MockSelfState()

        # Создаем событие с высокой интенсивностью
        high_intensity_event = Event(
            type="shock", intensity=0.9, timestamp=time.time(), metadata={"source": "test"}
        )

        # Добавляем событие в сенсорный буфер
        hierarchy.add_sensory_event(high_intensity_event)

        # Выполняем консолидацию (анализирует события в буфере)
        consolidation_stats = hierarchy.consolidate_memory(self_state)

        # Проверяем, что событие было перенесено
        assert consolidation_stats["sensory_to_episodic_transfers"] == 1
        assert len(memory) == 1

        # Проверяем содержимое перенесенной записи
        entry = memory[0]
        assert entry.event_type == "shock"
        assert abs(entry.meaning_significance - 0.9) < 0.01

    def test_sensory_to_episodic_transfer_by_repetitions(self):
        """Тест переноса событий по количеству повторений"""
        # Создаем компоненты
        memory = Memory()
        logger = StructuredLogger(__name__)
        hierarchy = MemoryHierarchyManager(logger=logger)
        hierarchy.set_episodic_memory(memory)

        # Создаем состояние системы
        class MockSelfState:
            def __init__(self):
                self.memory = memory
                self.subjective_time = 1.0

        self_state = MockSelfState()

        # Создаем событие со средней интенсивностью
        medium_intensity_event = Event(
            type="noise", intensity=0.3, timestamp=time.time(), metadata={"source": "test"}
        )

        # Добавляем событие в сенсорный буфер SENSORY_TO_EPISODIC_THRESHOLD раз
        threshold = hierarchy.SENSORY_TO_EPISODIC_THRESHOLD
        for i in range(threshold):
            event_copy = Event(
                type=medium_intensity_event.type,
                intensity=medium_intensity_event.intensity,
                timestamp=medium_intensity_event.timestamp
                + i * 0.001,  # Небольшое смещение времени
                metadata={"source": "test"},
            )
            hierarchy.add_sensory_event(event_copy)

        # Выполняем консолидацию
        consolidation_stats = hierarchy.consolidate_memory(self_state)

        # Проверяем, что событие было перенесено
        assert consolidation_stats["sensory_to_episodic_transfers"] == 1
        assert len(memory) == 1

    def test_hierarchy_status_reporting(self):
        """Тест отчетности статуса иерархии памяти"""
        # Создаем компоненты
        memory = Memory()
        logger = StructuredLogger(__name__)
        hierarchy = MemoryHierarchyManager(logger=logger)
        hierarchy.set_episodic_memory(memory)

        # Получаем статус
        status = hierarchy.get_hierarchy_status()

        # Проверяем структуру статуса
        assert "hierarchy_manager" in status
        assert "sensory_buffer" in status
        assert "episodic_memory" in status
        assert "semantic_store" in status
        assert "procedural_store" in status

        # Проверяем конкретные значения
        assert status["episodic_memory"]["available"] is True
        assert status["sensory_buffer"]["available"] is True
        assert status["semantic_store"]["available"] is True
        assert status["procedural_store"]["available"] is True

    def test_memory_hierarchy_reset(self):
        """Тест сброса иерархии памяти"""
        # Создаем компоненты
        memory = Memory()
        logger = StructuredLogger(__name__)
        hierarchy = MemoryHierarchyManager(logger=logger)
        hierarchy.set_episodic_memory(memory)

        # Добавляем событие и проверяем
        event = Event(
            type="test", intensity=0.9, timestamp=time.time(), metadata={"source": "test"}
        )
        hierarchy.add_sensory_event(event)

        assert hierarchy.sensory_buffer.buffer_size > 0

        # Сбрасываем иерархию
        hierarchy.reset_hierarchy()

        # Проверяем, что все очищено
        status = hierarchy.get_hierarchy_status()
        assert status["sensory_buffer"]["buffer_size"] == 0

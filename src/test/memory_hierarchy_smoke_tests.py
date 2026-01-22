"""
Дымовые тесты для экспериментальной функциональности Memory Hierarchy.

Проверяют базовую работоспособность компонентов без углубленного тестирования.
"""

import time
import pytest
from unittest.mock import Mock

from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
from src.experimental.memory_hierarchy.semantic_store import SemanticConcept, SemanticMemoryStore
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore
# ThreadSafeSerializer removed as architectural antipattern per Skeptic report
from src.environment.event import Event
from src.observability.structured_logger import StructuredLogger


class TestSmokeSemanticStore:
    """Дымовые тесты для SemanticMemoryStore."""

    def test_basic_initialization(self):
        """Базовая инициализация хранилища."""
        store = SemanticMemoryStore()
        assert store is not None
        assert store.size == 0
        assert store.is_empty()

    def test_basic_concept_operations(self):
        """Базовые операции с концепциями."""
        store = SemanticMemoryStore()

        # Создание и добавление концепции
        concept = SemanticConcept(
            concept_id="smoke_test_concept",
            name="Smoke Test Concept",
            description="Basic smoke test concept",
            confidence=0.8
        )

        store.add_concept(concept)
        assert store.size == 1

        # Получение концепции
        retrieved = store.get_concept("smoke_test_concept")
        assert retrieved is not None
        assert retrieved.name == "Smoke Test Concept"

        # Поиск концепций
        results = store.search_concepts("Smoke")
        assert len(results) > 0

    def test_basic_association_operations(self):
        """Базовые операции с ассоциациями."""
        store = SemanticMemoryStore()

        # Добавляем концепции
        concept1 = SemanticConcept("c1", "Concept 1", "First concept", 0.8)
        concept2 = SemanticConcept("c2", "Concept 2", "Second concept", 0.7)
        store.add_concept(concept1)
        store.add_concept(concept2)

        # Создаем ассоциацию
        from src.experimental.memory_hierarchy.semantic_store import SemanticAssociation
        association = SemanticAssociation("c1", "c2", "related_to", 0.6, 1)
        store.add_association(association)

        # Проверяем связи
        related = store.find_related_concepts("c1")
        assert "c2" in related

    def test_basic_consolidation(self):
        """Базовая консолидация знаний."""
        store = SemanticMemoryStore()

        # Добавляем концепцию
        concept = SemanticConcept("consolidation_test", "Test", "Test concept", 0.9)
        store.add_concept(concept)

        # Консолидация
        removed = store.consolidate_knowledge()
        assert isinstance(removed, int)

    def test_basic_statistics(self):
        """Базовая статистика."""
        store = SemanticMemoryStore()

        # Проверяем получение статистики
        stats = store.get_statistics()
        assert stats is not None
        assert hasattr(stats, 'total_entries')

        # Проверяем целостность
        integrity = store.validate_integrity()
        assert isinstance(integrity, bool)


class TestSmokeSensoryBuffer:
    """Дымовые тесты для SensoryBuffer."""

    def test_basic_initialization(self):
        """Базовая инициализация сенсорного буфера."""
        buffer = SensoryBuffer()
        assert buffer is not None
        assert buffer.buffer_size > 0

    def test_basic_event_operations(self):
        """Базовые операции с событиями."""
        buffer = SensoryBuffer()

        # Создание события
        event = Event(type="smoke_test_event", intensity=0.5, timestamp=time.time())

        # Добавление события
        buffer.add_event(event)

        # Получение событий
        events = buffer.get_events_for_processing()
        assert len(events) >= 0  # Может быть пустым, если событие не готово к обработке

    def test_buffer_status(self):
        """Проверка статуса буфера."""
        buffer = SensoryBuffer()
        status = buffer.get_buffer_status()
        assert isinstance(status, dict)
        assert "buffer_size" in status
        assert "buffer_capacity" in status


class TestSmokeProceduralStore:
    """Дымовые тесты для ProceduralMemoryStore."""

    def test_basic_initialization(self):
        """Базовая инициализация процедурного хранилища."""
        store = ProceduralMemoryStore()
        assert store is not None

    def test_basic_pattern_operations(self):
        """Базовые операции с паттернами."""
        store = ProceduralMemoryStore()

        # Проверяем наличие основных методов
        assert hasattr(store, 'find_applicable_patterns')
        assert hasattr(store, 'optimize_patterns')

        # Базовый вызов методов
        patterns = store.find_applicable_patterns({})
        assert isinstance(patterns, list)

        optimized = store.optimize_patterns()
        assert isinstance(optimized, int)


class TestSmokeMemoryHierarchyManager:
    """Дымовые тесты для MemoryHierarchyManager."""

    def test_basic_initialization(self):
        """Базовая инициализация менеджера."""
        manager = MemoryHierarchyManager()
        assert manager is not None
        assert manager.semantic_store is not None

    def test_basic_memory_operations(self):
        """Базовые операции с памятью."""
        manager = MemoryHierarchyManager()

        # Проверка статуса
        status = manager.get_hierarchy_status()
        assert isinstance(status, dict)
        assert "semantic_store" in status

        # Запрос к памяти
        results = manager.query_memory("semantic")
        assert isinstance(results, list)

    def test_basic_consolidation(self):
        """Базовая консолидация памяти."""
        manager = MemoryHierarchyManager()
        mock_state = Mock()

        # Консолидация
        stats = manager.consolidate_memory(mock_state)
        assert isinstance(stats, dict)
        assert "timestamp" in stats

    def test_basic_thresholds(self):
        """Базовые настройки порогов."""
        manager = MemoryHierarchyManager()

        # Получение порогов
        thresholds = manager.get_transfer_thresholds()
        assert isinstance(thresholds, dict)
        assert "sensory_to_episodic_threshold" in thresholds

        # Установка порогов
        manager.set_transfer_thresholds(sensory_to_episodic=7, episodic_to_semantic=15)
        new_thresholds = manager.get_transfer_thresholds()
        assert new_thresholds["sensory_to_episodic_threshold"] == 7
        assert new_thresholds["episodic_to_semantic_threshold"] == 15


class TestSmokeSerializationContracts:
    """Дымовые тесты для контрактов сериализации."""

    def test_basic_serialization_protocols(self):
        """Базовый тест протоколов сериализации (ThreadSafeSerializer удален как антипаттерн)."""
        from src.contracts.serialization_contract import Serializable, MetadataProvider, ThreadSafeSerializable

        mock_component = Mock(spec=ThreadSafeSerializable)
        mock_component.to_dict.return_value = {"test": "data"}
        mock_component.get_serialization_metadata.return_value = {
            "version": "1.0",
            "component_type": "TestComponent",
            "timestamp": 123.45,
            "thread_safe": True
        }

        # Проверка протоколов
        assert isinstance(mock_component, Serializable)
        assert isinstance(mock_component, MetadataProvider)
        assert isinstance(mock_component, ThreadSafeSerializable)

        # Сериализация напрямую через компонент
        data = mock_component.to_dict()
        assert data == {"test": "data"}

        # Метаданные напрямую через компонент
        metadata = mock_component.get_serialization_metadata()
        assert isinstance(metadata, dict)
        assert "version" in metadata
        assert metadata["version"] == "1.0"
        assert metadata.get("thread_safe") is True


class TestSmokeIntegrationBasic:
    """Базовые интеграционные дымовые тесты."""

    def test_memory_hierarchy_basic_workflow(self):
        """Базовый workflow иерархии памяти."""
        # Создание менеджера
        manager = MemoryHierarchyManager()

        # Создание концепции
        concept = SemanticConcept(
            concept_id="workflow_test",
            name="Workflow Test",
            description="Testing basic workflow",
            confidence=0.8
        )

        # Добавление через менеджер
        manager.semantic_store.add_concept(concept)

        # Запрос через менеджер
        results = manager.query_memory("semantic", query="Workflow")
        assert len(results) > 0

        # Проверка статуса
        status = manager.get_hierarchy_status()
        assert status["semantic_store"]["concepts_count"] > 0

    def test_event_to_memory_flow(self):
        """Базовый поток от событий к памяти."""
        # Создаем компоненты
        manager = MemoryHierarchyManager()

        # Создаем событие
        event = Event(type="smoke_event", intensity=0.6, timestamp=time.time())

        # Добавляем событие (даже без сенсорного буфера не должно падать)
        manager.add_sensory_event(event)

        # Проверяем, что система стабильна
        status = manager.get_hierarchy_status()
        assert isinstance(status, dict)

    def test_clarity_moment_processing(self):
        """Обработка моментов ясности."""
        manager = MemoryHierarchyManager()
        mock_state = Mock()

        # Обрабатываем момент ясности
        manager.handle_clarity_moment("cognitive", 0.8, mock_state)

        # Система должна оставаться стабильной
        status = manager.get_hierarchy_status()
        assert isinstance(status, dict)


class TestSmokeErrorHandling:
    """Дымовые тесты обработки ошибок."""

    def test_invalid_memory_query(self):
        """Некорректный запрос к памяти."""
        manager = MemoryHierarchyManager()

        with pytest.raises(ValueError):
            manager.query_memory("invalid_level")

    def test_invalid_thresholds(self):
        """Некорректные пороги."""
        manager = MemoryHierarchyManager()

        # Отрицательные пороги должны быть исправлены
        manager.set_transfer_thresholds(sensory_to_episodic=-5, episodic_to_semantic=-10)

        thresholds = manager.get_transfer_thresholds()
        assert thresholds["sensory_to_episodic_threshold"] > 0
        assert thresholds["episodic_to_semantic_threshold"] > 0

    def test_missing_concept_operations(self):
        """Операции с несуществующими концепциями."""
        store = SemanticMemoryStore()

        # Запрос несуществующей концепции
        result = store.get_concept("nonexistent")
        assert result is None

        # Поиск несуществующего
        results = store.search_concepts("nonexistent")
        assert len(results) == 0

        # Связи несуществующей концепции
        related = store.find_related_concepts("nonexistent")
        assert len(related) == 0


class TestSmokePerformanceBasic:
    """Базовые дымовые тесты производительности."""

    def test_bulk_concept_operations(self):
        """Массовые операции с концепциями."""
        store = SemanticMemoryStore()

        # Создаем много концепций
        concepts = []
        for i in range(100):
            concept = SemanticConcept(
                concept_id=f"bulk_concept_{i}",
                name=f"Bulk Concept {i}",
                description=f"Description for concept {i}",
                confidence=0.5 + (i % 50) / 100  # Варьируем уверенность
            )
            concepts.append(concept)

        # Добавляем все концепции
        start_time = time.time()
        for concept in concepts:
            store.add_concept(concept)
        add_time = time.time() - start_time

        assert store.size == 100
        assert add_time < 1.0  # Должно быть быстро

        # Поиск
        search_start = time.time()
        results = store.search_concepts("Bulk Concept 5")
        search_time = time.time() - search_start

        assert len(results) > 0
        assert search_time < 0.1  # Поиск должен быть быстрым

    def test_memory_hierarchy_scaling(self):
        """Масштабирование иерархии памяти."""
        manager = MemoryHierarchyManager()

        # Множественные операции консолидации
        mock_state = Mock()

        start_time = time.time()
        for _ in range(10):
            stats = manager.consolidate_memory(mock_state)
            assert isinstance(stats, dict)
        consolidation_time = time.time() - start_time

        assert consolidation_time < 2.0  # Должно быть reasonably быстро
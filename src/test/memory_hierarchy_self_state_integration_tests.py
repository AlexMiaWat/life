"""
Интеграционные тесты взаимодействия Memory Hierarchy с SelfState.

Тестируют:
- Интеграцию memory hierarchy в композитную сериализацию SelfState
- Восстановление состояния после сериализации/десериализации
- Thread-safety при работе с SelfState
- Graceful degradation при отключенных компонентах
"""

import time
import pytest
import threading
from unittest.mock import Mock, MagicMock
import concurrent.futures
from dataclasses import dataclass

from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager
from src.experimental.memory_hierarchy.semantic_store import SemanticConcept
from src.experimental.memory_hierarchy.sensory_buffer import SensoryBuffer
from src.experimental.memory_hierarchy.procedural_store import ProceduralMemoryStore
from src.state.self_state import SelfState
from src.environment.event import Event
from src.observability.structured_logger import StructuredLogger
from src.config.feature_flags import FeatureFlags
from src.contracts.memory_hierarchy_api_contract import ConsolidationResult


class TestMemoryHierarchySelfStateIntegration:
    """Интеграционные тесты взаимодействия Memory Hierarchy с SelfState."""

    def setup_method(self):
        """Настройка тестового окружения."""
        self.logger = Mock(spec=StructuredLogger)
        self.feature_flags = FeatureFlags()

    def test_memory_hierarchy_integration_in_self_state_serialization(self):
        """Тест интеграции memory hierarchy в композитную сериализацию SelfState."""
        # Создаем SelfState с memory hierarchy
        self_state = SelfState()
        memory_hierarchy = MemoryHierarchyManager(logger=self.logger)
        self_state.memory_hierarchy = memory_hierarchy

        # Добавляем данные в memory hierarchy
        concept = SemanticConcept(
            concept_id="test_concept_1",
            name="Test Concept",
            description="A test concept for integration testing",
            confidence=0.8
        )
        memory_hierarchy.semantic_store.add_concept(concept)

        # Выполняем композитную сериализацию
        components, metrics = self_state._serialize_components_isolated()

        # Проверяем, что memory hierarchy включен в сериализацию
        assert "memory_hierarchy" in components
        assert components["memory_hierarchy"] is not None

        # Проверяем структуру сериализованных данных
        mh_data = components["memory_hierarchy"]
        assert "semantic_store" in mh_data
        assert "concepts" in mh_data["semantic_store"]
        assert "test_concept_1" in mh_data["semantic_store"]["concepts"]

        # Проверяем метрики сериализации
        assert "memory_hierarchy" in metrics
        assert metrics["memory_hierarchy"]["success"] is True

    def test_self_state_deserialization_with_memory_hierarchy(self):
        """Тест восстановления SelfState с memory hierarchy из сериализованных данных."""
        # Создаем исходное состояние
        original_state = SelfState()
        original_hierarchy = MemoryHierarchyManager(logger=self.logger)

        # Добавляем тестовые данные
        concept = SemanticConcept(
            concept_id="restored_concept",
            name="Restored Concept",
            description="Concept for deserialization testing",
            confidence=0.9
        )
        original_hierarchy.semantic_store.add_concept(concept)
        original_state.memory_hierarchy = original_hierarchy

        # Сериализуем состояние
        components, _ = original_state._serialize_components_isolated()

        # Создаем новое состояние и восстанавливаем его
        restored_state = SelfState()
        restored_hierarchy = MemoryHierarchyManager(logger=self.logger)
        restored_state.memory_hierarchy = restored_hierarchy

        # Имитируем восстановление из сериализованных данных
        # (в реальной системе это делает десериализатор)
        mh_data = components["memory_hierarchy"]
        restored_hierarchy._restore_from_dict(mh_data)

        # Проверяем восстановление данных
        restored_concept = restored_hierarchy.semantic_store.get_concept("restored_concept")
        assert restored_concept is not None
        assert restored_concept.name == "Restored Concept"
        assert restored_concept.confidence == 0.9

    def test_graceful_degradation_when_memory_hierarchy_disabled(self):
        """Тест graceful degradation при отключенной memory hierarchy."""
        # Создаем SelfState без memory hierarchy
        self_state = SelfState()
        self_state.memory_hierarchy = None

        # Выполняем сериализацию - должна работать без ошибок
        components, metrics = self_state._serialize_components_isolated()

        # Проверяем, что memory_hierarchy отсутствует в компонентах
        assert "memory_hierarchy" not in components

        # Проверяем, что остальные компоненты сериализованы корректно
        assert "identity" in components
        assert "physical" in components
        assert "time" in components

        # Проверяем статистику SelfState при отключенной memory hierarchy
        stats = self_state.get_statistics()
        assert "memory_hierarchy_size" in stats
        assert stats["memory_hierarchy_size"] == 0

    def test_thread_safety_memory_hierarchy_with_self_state(self):
        """Тест thread-safety при одновременном доступе к memory hierarchy через SelfState."""
        self_state = SelfState()
        memory_hierarchy = MemoryHierarchyManager(logger=self.logger)
        self_state.memory_hierarchy = memory_hierarchy

        errors = []
        results = []

        def worker(worker_id):
            """Рабочий поток для тестирования конкурентного доступа."""
            try:
                # Каждый поток добавляет свои концепции
                for i in range(10):
                    concept = SemanticConcept(
                        concept_id=f"worker_{worker_id}_concept_{i}",
                        name=f"Worker {worker_id} Concept {i}",
                        description=f"Concept created by worker {worker_id}",
                        confidence=0.7
                    )
                    memory_hierarchy.semantic_store.add_concept(concept)

                # Выполняем консолидацию
                consolidation_result = memory_hierarchy.consolidate_memory(self_state)
                results.append(consolidation_result)

                # Выполняем запрос
                query_result = memory_hierarchy.query_memory("semantic", query=f"Worker {worker_id}")
                results.append(query_result)

            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Запускаем несколько потоков
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()

        # Проверяем, что не было ошибок
        assert len(errors) == 0, f"Thread safety errors: {errors}"

        # Проверяем, что данные были добавлены корректно
        status = memory_hierarchy.get_hierarchy_status()
        assert status["semantic_store"]["concepts_count"] == 50  # 5 workers * 10 concepts

    def test_memory_hierarchy_serialization_consistency(self):
        """Тест консистентности сериализации memory hierarchy."""
        # Создаем memory hierarchy с данными
        memory_hierarchy = MemoryHierarchyManager(logger=self.logger)

        # Добавляем концепции
        concepts = []
        for i in range(5):
            concept = SemanticConcept(
                concept_id=f"consistency_concept_{i}",
                name=f"Consistency Concept {i}",
                description=f"Concept for consistency testing {i}",
                confidence=0.8
            )
            concepts.append(concept)
            memory_hierarchy.semantic_store.add_concept(concept)

        # Выполняем несколько сериализаций подряд
        serializations = []
        for _ in range(3):
            data = memory_hierarchy.to_dict()
            serializations.append(data)
            time.sleep(0.01)  # Небольшая задержка

        # Проверяем консистентность сериализаций
        for i in range(1, len(serializations)):
            assert serializations[i]["semantic_store"]["concepts"] == serializations[0]["semantic_store"]["concepts"]

        # Проверяем метаданные сериализации
        metadata = memory_hierarchy.get_serialization_metadata()
        assert metadata["component_type"] == "memory_hierarchy_manager"
        assert metadata["thread_safe"] is True
        assert metadata["concepts_count"] == 5

    def test_memory_hierarchy_state_persistence_across_restart(self):
        """Тест сохранения состояния memory hierarchy при перезапуске системы."""
        # Создаем исходную иерархию с данными
        original_hierarchy = MemoryHierarchyManager(logger=self.logger)

        # Добавляем разнообразные данные
        concept = SemanticConcept(
            concept_id="persistence_test",
            name="Persistence Test",
            description="Concept for persistence testing",
            confidence=0.85
        )
        original_hierarchy.semantic_store.add_concept(concept)

        # Имитируем некоторую активность
        original_hierarchy.consolidate_memory(Mock())

        # Сериализуем состояние
        serialized_state = original_hierarchy.to_dict()

        # Создаем новую иерархию и восстанавливаем состояние
        restored_hierarchy = MemoryHierarchyManager(logger=self.logger)

        # Имитируем восстановление (в реальной системе это делает загрузчик)
        # Восстанавливаем основные структуры данных
        if "semantic_store" in serialized_state:
            semantic_data = serialized_state["semantic_store"]
            if "concepts" in semantic_data:
                for concept_data in semantic_data["concepts"].values():
                    concept = SemanticConcept(
                        concept_id=concept_data["concept_id"],
                        name=concept_data["name"],
                        description=concept_data["description"],
                        confidence=concept_data["confidence"],
                        activation_count=concept_data["activation_count"],
                        last_activation=concept_data["last_activation"],
                        related_concepts=concept_data["related_concepts"],
                        properties=concept_data["properties"],
                        created_at=concept_data["created_at"]
                    )
                    restored_hierarchy.semantic_store.add_concept(concept)

        # Проверяем восстановление
        restored_concept = restored_hierarchy.semantic_store.get_concept("persistence_test")
        assert restored_concept is not None
        assert restored_concept.name == "Persistence Test"
        assert restored_concept.confidence == 0.85

        # Проверяем, что новая иерархия функционирует
        status = restored_hierarchy.get_hierarchy_status()
        assert status["semantic_store"]["available"] is True
        assert status["semantic_store"]["concepts_count"] == 1

    @pytest.mark.parametrize("component_disabled", ["sensory_buffer", "semantic_store", "procedural_store"])
    def test_partial_memory_hierarchy_degradation(self, component_disabled):
        """Тест degradation при частичном отключении компонентов memory hierarchy."""
        # Создаем memory hierarchy с частично отключенными компонентами
        if component_disabled == "sensory_buffer":
            memory_hierarchy = MemoryHierarchyManager(
                sensory_buffer=None,
                logger=self.logger,
                feature_flags=self.feature_flags
            )
        else:
            memory_hierarchy = MemoryHierarchyManager(logger=self.logger)

            if component_disabled == "semantic_store":
                memory_hierarchy.semantic_store = None
            elif component_disabled == "procedural_store":
                memory_hierarchy.procedural_store = None

        # Создаем SelfState
        self_state = SelfState()
        self_state.memory_hierarchy = memory_hierarchy

        # Выполняем сериализацию - должна работать без ошибок
        components, metrics = self_state._serialize_components_isolated()

        # Проверяем, что сериализация прошла успешно
        assert "memory_hierarchy" in components
        assert metrics["memory_hierarchy"]["success"] is True

        # Проверяем статус иерархии
        status = memory_hierarchy.get_hierarchy_status()

        if component_disabled == "sensory_buffer":
            assert status["sensory_buffer"]["available"] is False
        elif component_disabled == "semantic_store":
            assert status["semantic_store"]["available"] is False
        elif component_disabled == "procedural_store":
            assert status["procedural_store"]["available"] is False

        # Проверяем, что система остается функциональной


"""
Unit тесты для SemanticMemoryStore.
"""

import pytest
import time
from unittest.mock import Mock

from src.experimental.memory_hierarchy.semantic_store import (
    SemanticMemoryStore,
    SemanticConcept,
    SemanticAssociation,
)
from src.observability.structured_logger import StructuredLogger


class TestSemanticConcept:
    """Тесты для SemanticConcept."""

    def test_concept_creation(self):
        """Тест создания концепции."""
        concept = SemanticConcept(
            concept_id="test_concept_1",
            name="Test Concept",
            description="A test concept",
            confidence=0.8,
        )

        assert concept.concept_id == "test_concept_1"
        assert concept.name == "Test Concept"
        assert concept.description == "A test concept"
        assert concept.confidence == 0.8
        assert concept.activation_count == 0
        assert concept.related_concepts == set()

    def test_concept_activation(self):
        """Тест активации концепции."""
        concept = SemanticConcept(
            concept_id="test_concept_1", name="Test Concept", description="A test concept"
        )

        initial_count = concept.activation_count
        initial_time = concept.last_activation

        time.sleep(0.001)  # Небольшая задержка
        concept.activate()

        assert concept.activation_count == initial_count + 1
        assert concept.last_activation > initial_time

    def test_activation_strength(self):
        """Тест расчета силы активации."""
        concept = SemanticConcept(
            concept_id="test_concept_1",
            name="Test Concept",
            description="A test concept",
            confidence=0.8,
        )

        # Без активаций сила должна быть низкой
        strength = concept.get_activation_strength(time.time())
        assert strength < 0.1

        # После активации сила должна быть выше
        concept.activate()
        strength = concept.get_activation_strength(time.time())
        assert strength > 0.5

    def test_add_relation(self):
        """Тест добавления связей между концепциями."""
        concept = SemanticConcept(
            concept_id="test_concept_1", name="Test Concept", description="A test concept"
        )

        concept.add_relation("related_concept_1")
        concept.add_relation("related_concept_2")
        concept.add_relation("related_concept_1")  # Дубликат

        assert "related_concept_1" in concept.related_concepts
        assert "related_concept_2" in concept.related_concepts
        assert len(concept.related_concepts) == 2


class TestSemanticAssociation:
    """Тесты для SemanticAssociation."""

    def test_association_creation(self):
        """Тест создания ассоциации."""
        association = SemanticAssociation(
            source_id="concept_1", target_id="concept_2", association_type="is_a", strength=0.7
        )

        assert association.source_id == "concept_1"
        assert association.target_id == "concept_2"
        assert association.association_type == "is_a"
        assert association.strength == 0.7
        assert association.evidence_count == 0

    def test_association_strengthen(self):
        """Тест усиления ассоциации."""
        association = SemanticAssociation(
            source_id="concept_1",
            target_id="concept_2",
            association_type="related_to",
            strength=0.5,
        )

        initial_strength = association.strength
        initial_evidence = association.evidence_count
        initial_time = association.last_updated

        time.sleep(0.001)
        association.strengthen(0.2)

        assert association.strength > initial_strength
        assert association.evidence_count == initial_evidence + 1
        assert association.last_updated > initial_time


class TestSemanticMemoryStore:
    """Тесты для SemanticMemoryStore."""

    @pytest.fixture
    def logger(self):
        """Фикстура для логгера."""
        return Mock(spec=StructuredLogger)

    @pytest.fixture
    def store(self, logger):
        """Фикстура для хранилища."""
        return SemanticMemoryStore(logger=logger)

    def test_store_initialization(self, store):
        """Тест инициализации хранилища."""
        assert len(store._concepts) == 0
        assert len(store._associations) == 0
        assert len(store._name_to_id) == 0
        assert store._stats["total_concepts"] == 0
        assert store._stats["total_associations"] == 0

    def test_add_concept(self, store, logger):
        """Тест добавления концепции."""
        concept = SemanticConcept(
            concept_id="test_concept_1",
            name="Test Concept",
            description="A test concept",
            confidence=0.8,
        )

        store.add_concept(concept)

        assert "test_concept_1" in store._concepts
        assert store._concepts["test_concept_1"] == concept
        assert store._name_to_id["Test Concept"] == "test_concept_1"
        assert store._stats["total_concepts"] == 1
        logger.log_event.assert_called_once()

    def test_add_duplicate_concept(self, store):
        """Тест добавления дублирующейся концепции."""
        concept1 = SemanticConcept(
            concept_id="test_concept_1",
            name="Test Concept",
            description="A test concept",
            confidence=0.6,
        )

        concept2 = SemanticConcept(
            concept_id="test_concept_1",
            name="Test Concept",
            description="Updated description",
            confidence=0.9,
        )

        store.add_concept(concept1)
        store.add_concept(concept2)

        # Концепция должна быть обновлена
        assert store._concepts["test_concept_1"].confidence == 0.9
        assert store._concepts["test_concept_1"].description == "Updated description"
        assert store._stats["total_concepts"] == 1

    def test_get_concept(self, store):
        """Тест получения концепции."""
        concept = SemanticConcept(
            concept_id="test_concept_1", name="Test Concept", description="A test concept"
        )
        store.add_concept(concept)

        retrieved = store.get_concept("test_concept_1")
        assert retrieved == concept

        # Несуществующая концепция
        assert store.get_concept("nonexistent") is None

    def test_get_concept_by_name(self, store):
        """Тест получения концепции по имени."""
        concept = SemanticConcept(
            concept_id="test_concept_1", name="Test Concept", description="A test concept"
        )
        store.add_concept(concept)

        retrieved = store.get_concept_by_name("Test Concept")
        assert retrieved == concept

        # Несуществующее имя
        assert store.get_concept_by_name("Nonexistent Concept") is None

    def test_add_association(self, store, logger):
        """Тест добавления ассоциации."""
        association = SemanticAssociation(
            source_id="concept_1", target_id="concept_2", association_type="is_a", strength=0.8
        )

        store.add_association(association)

        key = ("concept_1", "concept_2")
        assert key in store._associations
        assert store._associations[key] == association
        assert "concept_2" in store._concept_relations["concept_1"]
        assert "concept_1" in store._concept_relations["concept_2"]
        assert store._stats["total_associations"] == 1
        logger.log_event.assert_called_once()

    def test_add_duplicate_association(self, store):
        """Тест добавления дублирующейся ассоциации."""
        association1 = SemanticAssociation(
            source_id="concept_1", target_id="concept_2", association_type="is_a", strength=0.6
        )

        association2 = SemanticAssociation(
            source_id="concept_1", target_id="concept_2", association_type="is_a", strength=0.4
        )

        store.add_association(association1)
        store.add_association(association2)

        key = ("concept_1", "concept_2")
        assert store._associations[key].strength > 0.6  # Усилилась
        assert store._associations[key].evidence_count == 1
        assert store._stats["total_associations"] == 1

    def test_find_related_concepts(self, store):
        """Тест поиска связанных концепций."""
        # Добавляем концепции
        concept1 = SemanticConcept(concept_id="c1", name="Concept 1", description="Desc 1")
        concept2 = SemanticConcept(concept_id="c2", name="Concept 2", description="Desc 2")
        concept3 = SemanticConcept(concept_id="c3", name="Concept 3", description="Desc 3")

        store.add_concept(concept1)
        store.add_concept(concept2)
        store.add_concept(concept3)

        # Добавляем связи
        store.add_association(SemanticAssociation("c1", "c2", "related_to", 0.8))
        store.add_association(SemanticAssociation("c2", "c3", "related_to", 0.6))

        # Ищем связанные концепции
        related = store.find_related_concepts("c1", max_depth=2)

        assert "c1" in related
        assert "c2" in related
        assert "c3" in related
        assert related["c1"] == 1.0  # Начальная концепция
        assert related["c2"] > 0  # Прямая связь
        assert related["c3"] > 0  # Косвенная связь

    def test_search_concepts(self, store):
        """Тест поиска концепций по тексту."""
        concept1 = SemanticConcept(concept_id="c1", name="Apple", description="A red fruit")
        concept2 = SemanticConcept(concept_id="c2", name="Banana", description="A yellow fruit")
        concept3 = SemanticConcept(concept_id="c3", name="Car", description="A vehicle")

        store.add_concept(concept1)
        store.add_concept(concept2)
        store.add_concept(concept3)

        # Поиск по имени
        results = store.search_concepts("Apple")
        assert len(results) == 1
        assert results[0] == concept1

        # Поиск по описанию
        results = store.search_concepts("fruit")
        assert len(results) == 2
        assert concept1 in results
        assert concept2 in results

        # Поиск без результатов
        results = store.search_concepts("nonexistent")
        assert len(results) == 0

    def test_consolidate_knowledge(self, store):
        """Тест консолидации знаний."""
        # Добавляем концепции с разной уверенностью
        concept1 = SemanticConcept(
            concept_id="c1", name="Good Concept", description="Good", confidence=0.9
        )
        concept2 = SemanticConcept(
            concept_id="c2", name="Bad Concept", description="Bad", confidence=0.1
        )

        store.add_concept(concept1)
        store.add_concept(concept2)

        # Активируем хорошую концепцию
        concept1.activate()

        # Добавляем ассоциацию
        store.add_association(SemanticAssociation("c1", "c2", "related_to", 0.9))

        initial_concepts = len(store._concepts)
        initial_associations = len(store._associations)

        # Консолидируем
        removed = store.consolidate_knowledge()

        # Плохая концепция должна быть удалена
        assert "c2" not in store._concepts
        assert len(store._concepts) == initial_concepts - 1
        assert removed > 0

    def test_get_statistics(self, store):
        """Тест получения статистики."""
        # Добавляем концепции
        concept1 = SemanticConcept(
            concept_id="c1", name="Concept 1", description="Desc 1", confidence=0.8
        )
        concept2 = SemanticConcept(
            concept_id="c2", name="Concept 2", description="Desc 2", confidence=0.6
        )

        store.add_concept(concept1)
        store.add_concept(concept2)

        # Активируем концепции
        concept1.activate()
        concept2.activate()

        stats = store.get_statistics()

        assert stats["total_concepts"] == 2
        assert stats["total_associations"] == 0
        assert stats["average_confidence"] == 0.7  # (0.8 + 0.6) / 2
        assert stats["average_activation"] > 0

    def test_clear_store(self, store):
        """Тест очистки хранилища."""
        # Добавляем данные
        concept = SemanticConcept(concept_id="c1", name="Concept 1", description="Desc 1")
        store.add_concept(concept)
        store.add_association(SemanticAssociation("c1", "c2", "related_to", 0.5))

        # Очищаем
        store.clear_store()

        assert len(store._concepts) == 0
        assert len(store._associations) == 0
        assert len(store._name_to_id) == 0
        assert store._stats["total_concepts"] == 0
        assert store._stats["total_associations"] == 0

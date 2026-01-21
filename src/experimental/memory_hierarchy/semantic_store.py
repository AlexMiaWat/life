"""
Семантическая память - Semantic Memory Store.

Хранит концепции, знания и онтологию понятий, извлеченные из эпизодического опыта.
Реализует долгосрочное хранение абстрактных знаний и связей между ними.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict

from src.observability.structured_logger import StructuredLogger
import sys
# Import interfaces through sys.modules to ensure we get the same object
_memory_interface_module = sys.modules.get('src.memory.memory_interface')
if _memory_interface_module is None:
    from src.memory import memory_interface as _memory_interface_module
SemanticMemoryInterface = _memory_interface_module.SemanticMemoryInterface
MemoryStatistics = _memory_interface_module.MemoryStatistics

logger = logging.getLogger(__name__)


@dataclass
class SemanticConcept:
    """
    Семантическая концепция - единица знаний в семантической памяти.

    Представляет абстрактное понятие или знание, извлеченное из повторяющихся паттернов.
    """

    concept_id: str  # Уникальный идентификатор концепции
    name: str  # Читаемое имя концепции
    description: str  # Описание концепции
    confidence: float  # Уровень уверенности в концепции (0.0-1.0)
    activation_count: int = 0  # Количество активаций
    last_activation: float = field(default_factory=time.time)  # Время последней активации
    related_concepts: Set[str] = field(default_factory=set)  # Связанные концепции
    properties: Dict[str, Any] = field(default_factory=dict)  # Дополнительные свойства
    created_at: float = field(default_factory=time.time)

    def activate(self) -> None:
        """Активировать концепцию (увеличить счетчик и обновить время)."""
        self.activation_count += 1
        self.last_activation = time.time()

    def add_relation(self, concept_id: str) -> None:
        """Добавить связь с другой концепцией."""
        self.related_concepts.add(concept_id)

    def get_activation_strength(self, current_time: float) -> float:
        """
        Получить силу активации концепции с учетом времени.

        Args:
            current_time: Текущее время

        Returns:
            Сила активации (0.0-1.0)
        """
        # Простая модель забывания: экспоненциальное затухание
        time_since_activation = current_time - self.last_activation
        decay_factor = 0.99 ** (time_since_activation / 3600)  # Каждый час 1% затухания
        return min(1.0, self.confidence * decay_factor)


@dataclass
class SemanticAssociation:
    """
    Ассоциация между концепциями или концепцией и свойством.
    """

    source_id: str
    target_id: str
    association_type: str  # "is_a", "has_property", "related_to", etc.
    strength: float  # Сила ассоциации (0.0-1.0)
    evidence_count: int  # Количество подтверждений
    last_updated: float = field(default_factory=time.time)

    def strengthen(self, amount: float = 0.1) -> None:
        """Усилить ассоциацию."""
        self.strength = min(1.0, self.strength + amount)
        self.evidence_count += 1
        self.last_updated = time.time()


class SemanticMemoryStore(SemanticMemoryInterface):
    """
    Хранилище семантической памяти.

    Управляет концепциями и их взаимосвязями, обеспечивая:
    - Хранение и извлечение концепций
    - Управление ассоциациями между концепциями
    - Консолидацию знаний из эпизодического опыта
    - Поиск и推理 на основе семантических связей
    """

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Инициализация семантического хранилища.

        Args:
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)

        # Хранилище концепций: concept_id -> SemanticConcept
        self._concepts: Dict[str, SemanticConcept] = {}

        # Хранилище ассоциаций: (source_id, target_id) -> SemanticAssociation
        self._associations: Dict[tuple, SemanticAssociation] = {}

        # Индексы для быстрого поиска
        self._name_to_id: Dict[str, str] = {}  # name -> concept_id
        self._concept_relations: Dict[str, Set[str]] = defaultdict(set)  # concept_id -> related_ids

        # Статистика
        self._stats = {
            "total_concepts": 0,
            "total_associations": 0,
            "last_consolidation": time.time(),
        }

        self.logger.log_event({"event_type": "semantic_store_initialized"})

    def add_concept(self, concept: SemanticConcept) -> None:
        """
        Добавить новую концепцию в хранилище.

        Args:
            concept: Концепция для добавления
        """
        if concept.concept_id in self._concepts:
            # Обновляем существующую концепцию
            existing = self._concepts[concept.concept_id]
            existing.confidence = max(existing.confidence, concept.confidence)
            existing.activation_count += concept.activation_count
            existing.related_concepts.update(concept.related_concepts)
            existing.properties.update(concept.properties)
            existing.last_activation = concept.last_activation
        else:
            # Добавляем новую концепцию
            self._concepts[concept.concept_id] = concept
            self._name_to_id[concept.name] = concept.concept_id
            self._stats["total_concepts"] += 1

        self.logger.log_event(
            {
                "event_type": "semantic_concept_added",
                "concept_id": concept.concept_id,
                "concept_name": concept.name,
                "confidence": concept.confidence,
            }
        )

    def get_concept(self, concept_id: str) -> Optional[SemanticConcept]:
        """
        Получить концепцию по ID.

        Args:
            concept_id: Идентификатор концепции

        Returns:
            Концепция или None если не найдена
        """
        return self._concepts.get(concept_id)

    def get_concept_by_name(self, name: str) -> Optional[SemanticConcept]:
        """
        Получить концепцию по имени.

        Args:
            name: Имя концепции

        Returns:
            Концепция или None если не найдена
        """
        concept_id = self._name_to_id.get(name)
        return self.get_concept(concept_id) if concept_id else None

    def add_association(self, association: SemanticAssociation) -> None:
        """
        Добавить ассоциацию между концепциями.

        Args:
            association: Ассоциация для добавления
        """
        key = (association.source_id, association.target_id)

        if key in self._associations:
            # Усиливаем существующую ассоциацию
            existing = self._associations[key]
            existing.strengthen(association.strength)
        else:
            # Добавляем новую ассоциацию
            self._associations[key] = association
            self._stats["total_associations"] += 1

            # Обновляем индексы связей
            self._concept_relations[association.source_id].add(association.target_id)
            self._concept_relations[association.target_id].add(association.source_id)

        self.logger.log_event(
            {
                "event_type": "semantic_association_added",
                "source_id": association.source_id,
                "target_id": association.target_id,
                "association_type": association.association_type,
                "strength": association.strength,
            }
        )

    def find_related_concepts(self, concept_id: str, max_depth: int = 2) -> Dict[str, float]:
        """
        Найти связанные концепции с учетом глубины связей.

        Args:
            concept_id: Исходная концепция
            max_depth: Максимальная глубина поиска

        Returns:
            Dict[concept_id, relevance_score]
        """
        if concept_id not in self._concepts:
            return {}

        visited = set()
        relevance_scores = {}

        def explore(current_id: str, depth: int, current_relevance: float):
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)
            relevance_scores[current_id] = max(
                relevance_scores.get(current_id, 0), current_relevance
            )

            # Исследуем связи
            for related_id in self._concept_relations[current_id]:
                key = (current_id, related_id)
                association = self._associations.get(key)

                if association:
                    # Сила связи уменьшается с глубиной
                    link_strength = association.strength * (0.8**depth)
                    explore(related_id, depth + 1, current_relevance * link_strength)

        explore(concept_id, 0, 1.0)
        return relevance_scores

    def search_concepts(self, query: str, limit: int = 10) -> List[SemanticConcept]:
        """
        Поиск концепций по текстовому запросу.

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            Список найденных концепций
        """
        query_lower = query.lower()
        results = []

        for concept in self._concepts.values():
            # Простой текстовый поиск по имени и описанию
            score = 0.0

            if query_lower in concept.name.lower():
                score += 1.0
            if query_lower in concept.description.lower():
                score += 0.5

            # Учитываем силу активации
            activation_strength = concept.get_activation_strength(time.time())
            score *= activation_strength

            if score > 0:
                results.append((concept, score))

        # Сортируем по релевантности и возвращаем топ результатов
        results.sort(key=lambda x: x[1], reverse=True)
        return [concept for concept, score in results[:limit]]

    def consolidate_knowledge(self) -> int:
        """
        Консолидировать знания - оптимизировать связи и удалить слабые концепции.

        Returns:
            Количество оптимизированных элементов
        """
        current_time = time.time()
        optimizations = 0

        # Удаляем концепции с очень низкой уверенностью и активацией
        concepts_to_remove = []
        for concept_id, concept in self._concepts.items():
            activation_strength = concept.get_activation_strength(current_time)
            if concept.confidence < 0.1 and activation_strength < 0.05:
                concepts_to_remove.append(concept_id)

        for concept_id in concepts_to_remove:
            self._remove_concept(concept_id)
            optimizations += 1

        # Ослабляем старые ассоциации
        associations_to_remove = []
        for key, association in self._associations.items():
            time_since_update = current_time - association.last_updated
            # Ослабляем ассоциации старше недели
            if time_since_update > 604800:  # 7 дней
                association.strength *= 0.9
                if association.strength < 0.05:
                    associations_to_remove.append(key)

        for key in associations_to_remove:
            self._remove_association(key)
            optimizations += 1

        self._stats["last_consolidation"] = current_time

        if optimizations > 0:
            self.logger.log_event(
                {"event_type": "semantic_knowledge_consolidated", "optimizations": optimizations}
            )

        return optimizations

    def _remove_concept(self, concept_id: str) -> None:
        """Удалить концепцию и все связанные ассоциации."""
        if concept_id in self._concepts:
            concept = self._concepts[concept_id]

            # Удаляем из индексов
            if concept.name in self._name_to_id:
                del self._name_to_id[concept.name]

            # Удаляем связанные ассоциации
            related_ids = list(self._concept_relations[concept_id])
            for related_id in related_ids:
                key1 = (concept_id, related_id)
                key2 = (related_id, concept_id)

                if key1 in self._associations:
                    del self._associations[key1]
                    self._stats["total_associations"] -= 1

                if key2 in self._associations:
                    del self._associations[key2]
                    self._stats["total_associations"] -= 1

            # Удаляем концепцию
            del self._concepts[concept_id]
            del self._concept_relations[concept_id]
            self._stats["total_concepts"] -= 1

    def _remove_association(self, key: tuple) -> None:
        """Удалить ассоциацию."""
        if key in self._associations:
            del self._associations[key]
            self._stats["total_associations"] -= 1

            # Обновляем индексы связей
            source_id, target_id = key
            if target_id in self._concept_relations[source_id]:
                self._concept_relations[source_id].remove(target_id)
            if source_id in self._concept_relations[target_id]:
                self._concept_relations[target_id].remove(source_id)

    def get_statistics(self) -> MemoryStatistics:
        """
        Получить статистику семантического хранилища.

        Returns:
            MemoryStatistics: Статистика использования
        """
        current_time = time.time()

        # Вычисляем среднюю уверенность и активацию
        total_confidence = 0.0
        total_activation = 0.0
        concept_count = len(self._concepts)

        if concept_count > 0:
            for concept in self._concepts.values():
                total_confidence += concept.confidence
                total_activation += concept.get_activation_strength(current_time)

            avg_confidence = total_confidence / concept_count
            avg_activation = total_activation / concept_count
        else:
            avg_confidence = 0.0
            avg_activation = 0.0

        return MemoryStatistics(
            total_entries=concept_count,
            average_significance=avg_confidence,  # Используем confidence как значимость
            memory_type="semantic"
        )

    def validate_integrity(self) -> bool:
        """
        Проверить целостность семантического хранилища.

        Returns:
            bool: True если данные корректны
        """
        try:
            # Проверяем концепции
            for concept_id, concept in self._concepts.items():
                if not hasattr(concept, 'concept_id') or concept.concept_id != concept_id:
                    return False
                if not isinstance(concept.confidence, (int, float)):
                    return False

            # Проверяем ассоциации
            for key, association in self._associations.items():
                source_id, target_id = key
                if source_id not in self._concepts or target_id not in self._concepts:
                    return False
                if not isinstance(association.strength, (int, float)):
                    return False

            return True
        except Exception:
            return False

    @property
    def size(self) -> int:
        """Получить размер семантической памяти."""
        return len(self._concepts)

    def is_empty(self) -> bool:
        """
        Проверить, пустое ли семантическое хранилище.

        Returns:
            bool: True если хранилище пустое
        """
        return len(self._concepts) == 0

    def clear(self) -> None:
        """Очистить семантическое хранилище."""
        self.clear_store()

    def clear_store(self) -> None:
        """Очистить все данные хранилища."""
        self._concepts.clear()
        self._associations.clear()
        self._name_to_id.clear()
        self._concept_relations.clear()
        self._stats = {
            "total_concepts": 0,
            "total_associations": 0,
            "last_consolidation": time.time(),
        }

        self.logger.log_event({"event_type": "semantic_store_cleared"})

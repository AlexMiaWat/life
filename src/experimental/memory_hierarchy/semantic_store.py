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
from src.contracts.serialization_contract import SerializationContract
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


class SemanticMemoryStore(SemanticMemoryInterface, SerializationContract):
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

    def get_all_concepts(self) -> List[SemanticConcept]:
        """
        Получить все концепции из семантического хранилища.

        Returns:
            Список всех концепций
        """
        return list(self._concepts.values())

    def get_concepts_count(self) -> int:
        """
        Получить количество концепций в хранилище.

        Returns:
            Количество концепций
        """
        return len(self._concepts)

    def get_all_associations(self) -> List[SemanticAssociation]:
        """
        Получить все ассоциации из семантического хранилища.

        Returns:
            Список всех ассоциаций
        """
        return list(self._associations.values())

    def get_associations_count(self) -> int:
        """
        Получить количество ассоциаций в хранилище.

        Returns:
            Количество ассоциаций
        """
        return len(self._associations)

    def get_concept_statistics(self) -> Dict[str, Any]:
        """
        Получить подробную статистику по концепциям.

        Returns:
            Dict со статистикой концепций
        """
        current_time = time.time()

        if not self._concepts:
            return {
                "total_concepts": 0,
                "avg_confidence": 0.0,
                "avg_activation_count": 0.0,
                "avg_activation_strength": 0.0,
                "oldest_concept_age": 0.0,
                "newest_concept_age": 0.0,
                "concepts_by_confidence": {},
                "most_activated_concepts": [],
            }

        confidences = []
        activation_counts = []
        activation_strengths = []
        ages = []

        for concept in self._concepts.values():
            confidences.append(concept.confidence)
            activation_counts.append(concept.activation_count)
            activation_strengths.append(concept.get_activation_strength(current_time))
            ages.append(current_time - concept.created_at)

        # Распределение по уровням уверенности
        confidence_ranges = {
            "high": len([c for c in confidences if c >= 0.8]),
            "medium": len([c for c in confidences if 0.5 <= c < 0.8]),
            "low": len([c for c in confidences if c < 0.5]),
        }

        # Топ наиболее активируемых концепций
        most_activated = sorted(
            self._concepts.values(),
            key=lambda c: c.activation_count,
            reverse=True
        )[:5]

        return {
            "total_concepts": len(self._concepts),
            "avg_confidence": sum(confidences) / len(confidences),
            "avg_activation_count": sum(activation_counts) / len(activation_counts),
            "avg_activation_strength": sum(activation_strengths) / len(activation_strengths),
            "oldest_concept_age": max(ages) if ages else 0.0,
            "newest_concept_age": min(ages) if ages else 0.0,
            "concepts_by_confidence": confidence_ranges,
            "most_activated_concepts": [
                {
                    "concept_id": c.concept_id,
                    "name": c.name,
                    "activation_count": c.activation_count,
                    "confidence": c.confidence,
                }
                for c in most_activated
            ],
        }

    def get_association_statistics(self) -> Dict[str, Any]:
        """
        Получить подробную статистику по ассоциациям.

        Returns:
            Dict со статистикой ассоциаций
        """
        if not self._associations:
            return {
                "total_associations": 0,
                "avg_strength": 0.0,
                "avg_evidence_count": 0.0,
                "associations_by_type": {},
                "associations_by_strength": {},
            }

        strengths = []
        evidence_counts = []
        types_count = {}

        for association in self._associations.values():
            strengths.append(association.strength)
            evidence_counts.append(association.evidence_count)
            types_count[association.association_type] = types_count.get(association.association_type, 0) + 1

        # Распределение по уровням силы
        strength_ranges = {
            "strong": len([s for s in strengths if s >= 0.8]),
            "medium": len([s for s in strengths if 0.5 <= s < 0.8]),
            "weak": len([s for s in strengths if s < 0.5]),
        }

        return {
            "total_associations": len(self._associations),
            "avg_strength": sum(strengths) / len(strengths),
            "avg_evidence_count": sum(evidence_counts) / len(evidence_counts),
            "associations_by_type": types_count,
            "associations_by_strength": strength_ranges,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализовать состояние семантического хранилища.

        Returns:
            Dict[str, Any]: Словарь с состоянием компонента
        """
        import time
        current_time = time.time()

        return {
            "concepts": {
                concept_id: {
                    "concept_id": concept.concept_id,
                    "name": concept.name,
                    "description": concept.description,
                    "confidence": concept.confidence,
                    "activation_count": concept.activation_count,
                    "last_activation": concept.last_activation,
                    "related_concepts": list(concept.related_concepts),
                    "properties": concept.properties,
                    "created_at": concept.created_at,
                }
                for concept_id, concept in self._concepts.items()
            },
            "associations": [
                {
                    "source_id": association.source_id,
                    "target_id": association.target_id,
                    "association_type": association.association_type,
                    "strength": association.strength,
                    "evidence_count": association.evidence_count,
                    "last_updated": association.last_updated,
                }
                for association in self._associations.values()
            ],
            "name_to_id": dict(self._name_to_id),
            "stats": dict(self._stats),
            "last_consolidation": self._stats.get("last_consolidation", current_time),
            "timestamp": current_time,
        }

    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Получить метаданные сериализации семантического хранилища.

        Returns:
            Dict[str, Any]: Метаданные сериализации
        """
        import time
        current_time = time.time()

        return {
            "version": "1.0",
            "timestamp": current_time,
            "component_type": "semantic_memory_store",
            "thread_safe": True,  # SemanticMemoryStore thread-safe для чтения
            "concepts_count": len(self._concepts),
            "associations_count": len(self._associations),
            "total_size_bytes": self._estimate_size(),
        }

    def _estimate_size(self) -> int:
        """Оценить размер хранилища в байтах."""
        # Грубая оценка: каждый концепт ~1KB, каждая ассоциация ~100B
        concepts_size = len(self._concepts) * 1024
        associations_size = len(self._associations) * 100
        return concepts_size + associations_size

    def get_full_statistics(self) -> Dict[str, Any]:
        """
        Получить полную статистику семантического хранилища.

        Returns:
            Dict с полной статистикой
        """
        base_stats = self.get_statistics()
        concept_stats = self.get_concept_statistics()
        association_stats = self.get_association_statistics()

        return {
            "overview": base_stats,
            "concepts": concept_stats,
            "associations": association_stats,
            "memory_usage": {
                "concepts_count": len(self._concepts),
                "associations_count": len(self._associations),
                "relations_count": sum(len(rels) for rels in self._concept_relations.values()),
            },
            "last_consolidation": self._stats["last_consolidation"],
            "timestamp": time.time(),
        }

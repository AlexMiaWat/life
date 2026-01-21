"""
Менеджер иерархии памяти - Memory Hierarchy Manager.

Координирует работу между уровнями памяти: сенсорным, эпизодическим,
семантическим и процедурным. Управляет переносом данных между уровнями.
"""

import logging
import time
from typing import Dict, List, Optional, Any

from src.environment.event import Event
from src.memory.memory_types import MemoryEntry
from src.observability.structured_logger import StructuredLogger

from .sensory_buffer import SensoryBuffer
from .semantic_store import SemanticMemoryStore
from .procedural_store import ProceduralMemoryStore

logger = logging.getLogger(__name__)


class MemoryHierarchyManager:
    """
    Центральный менеджер для координации многоуровневой системы памяти.

    Отвечает за:
    - Управление переносом данных между уровнями памяти
    - Координацию консолидации (sensory → episodic → semantic)
    - Управление procedural learning из опыта
    - API для запросов к разным уровням памяти
    """

    # Константы для управления переносом данных
    SENSORY_TO_EPISODIC_THRESHOLD = 5  # Количество обработок события для переноса
    EPISODIC_TO_SEMANTIC_THRESHOLD = 10  # Порог повторений для семантизации
    SEMANTIC_CONSOLIDATION_INTERVAL = 60.0  # Интервал консолидации семантических знаний (секунды)

    def __init__(
        self,
        sensory_buffer: Optional[SensoryBuffer] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        """
        Инициализация менеджера иерархии памяти.

        Args:
            sensory_buffer: Сенсорный буфер (если None, будет создан автоматически)
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)

        # Инициализация уровней памяти
        self.sensory_buffer = sensory_buffer or SensoryBuffer()

        # Интеграция с эпизодической памятью
        self.episodic_memory = None  # Будет установлено при вызове set_episodic_memory
        self.semantic_store = SemanticMemoryStore(logger=self.logger)  # SemanticMemoryStore
        self.procedural_store = ProceduralMemoryStore(logger=self.logger)  # ProceduralMemoryStore

        # Статистика переноса данных
        self._transfer_stats = {
            "sensory_to_episodic": 0,
            "episodic_to_semantic": 0,
            "semantic_to_procedural": 0,
            "last_semantic_consolidation": time.time(),
        }

        # Кэш для оптимизации
        self._event_processing_counts: Dict[str, int] = {}  # event_hash -> count

        self.logger.log_event(
            {
                "event_type": "memory_hierarchy_initialized",
                "sensory_buffer_size": self.sensory_buffer.buffer_size,
            }
        )

    def set_episodic_memory(self, memory) -> None:
        """
        Установить ссылку на эпизодическую память для интеграции.

        Args:
            memory: Экземпляр Memory (эпизодическая память)
        """
        self.episodic_memory = memory
        self.logger.log_event(
            {
                "event_type": "episodic_memory_integrated",
                "memory_entries_count": len(memory) if memory else 0,
            }
        )

    def add_sensory_event(self, event: Event) -> None:
        """
        Добавить событие в сенсорный буфер.

        Args:
            event: Событие для добавления
        """
        self.sensory_buffer.add_event(event)

    def process_sensory_events(self, max_events: Optional[int] = None) -> List[Event]:
        """
        Обработать события из сенсорного буфера для передачи в MeaningEngine.

        Args:
            max_events: Максимальное количество событий для обработки

        Returns:
            Список событий для обработки MeaningEngine
        """
        return self.sensory_buffer.get_events_for_processing(max_events)

    def consolidate_memory(self, self_state) -> Dict[str, Any]:
        """
        Выполнить консолидацию памяти между уровнями.

        Этот метод вызывается периодически для переноса данных между уровнями:
        - sensory → episodic (на основе повторений)
        - episodic → semantic (на основе паттернов)
        - semantic → procedural (на основе автоматизации)

        Args:
            self_state: Текущее состояние системы

        Returns:
            Статистика консолидации
        """
        consolidation_stats = {
            "sensory_to_episodic_transfers": 0,
            "episodic_to_semantic_transfers": 0,
            "semantic_consolidations": 0,
            "timestamp": time.time(),
        }

        # Консолидация sensory → episodic
        sensory_transfers = self._consolidate_sensory_to_episodic(self_state)
        consolidation_stats["sensory_to_episodic_transfers"] = sensory_transfers

        # Консолидация episodic → semantic (пока заглушка)
        if self.episodic_memory and self.semantic_store:
            semantic_transfers = self._consolidate_episodic_to_semantic(self_state)
            consolidation_stats["episodic_to_semantic_transfers"] = semantic_transfers

        # Периодическая консолидация semantic (раз в минуту)
        if (
            time.time() - self._transfer_stats["last_semantic_consolidation"]
            > self.SEMANTIC_CONSOLIDATION_INTERVAL
        ):
            semantic_consolidations = self._consolidate_semantic_knowledge()
            consolidation_stats["semantic_consolidations"] = semantic_consolidations
            self._transfer_stats["last_semantic_consolidation"] = time.time()

        self.logger.log_event(
            {"event_type": "memory_consolidation_completed", **consolidation_stats}
        )

        return consolidation_stats

    def _consolidate_sensory_to_episodic(self, self_state) -> int:
        """
        Консолидация от сенсорного буфера к эпизодической памяти.

        Реализует автоматический перенос событий из сенсорного буфера в эпизодическую память
        на основе порога повторений и значимости.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Количество перенесенных записей
        """
        transfers_count = 0

        # Получаем события для анализа консолидации (не удаляем из буфера)
        sensory_events = self.sensory_buffer.peek_events(max_events=None)

        # Отладка
        if sensory_events:
            self.logger.log_event(
                {
                    "event_type": "debug_sensory_consolidation",
                    "events_count": len(sensory_events),
                    "episodic_memory_available": self.episodic_memory is not None,
                }
            )

        for event in sensory_events:
            # Создаем идентификатор события для отслеживания повторений по типу
            event_hash = event.type

            # Увеличиваем счетчик "видов" события (сколько раз оно наблюдалось в буфере)
            self._event_processing_counts[event_hash] = (
                self._event_processing_counts.get(event_hash, 0) + 1
            )
            processing_count = self._event_processing_counts[event_hash]

            # Проверяем условия для переноса в эпизодическую память:
            # 1. Достигнут порог повторений ИЛИ
            # 2. Высокая интенсивность (даже при первой обработке)
            should_transfer = (
                processing_count >= self.SENSORY_TO_EPISODIC_THRESHOLD
                or abs(event.intensity) > 0.8  # Порог высокой интенсивности
            )

            # Отладка
            self.logger.log_event(
                {
                    "event_type": "debug_transfer_check",
                    "event_type": event.type,
                    "intensity": event.intensity,
                    "processing_count": processing_count,
                    "threshold": self.SENSORY_TO_EPISODIC_THRESHOLD,
                    "should_transfer": should_transfer,
                    "episodic_memory_available": self.episodic_memory is not None,
                }
            )

            if should_transfer:
                # Создаем MemoryEntry для эпизодической памяти
                memory_entry = MemoryEntry(
                    event_type=event.type,
                    meaning_significance=abs(event.intensity),
                    timestamp=event.timestamp,
                    subjective_timestamp=getattr(self_state, "subjective_time", 0.0),
                )

                # Добавляем в эпизодическую память (если доступна)
                if self.episodic_memory is not None:
                    self.episodic_memory.append(memory_entry)
                    transfers_count += 1
                    self._transfer_stats["sensory_to_episodic"] += 1

                    self.logger.log_event(
                        {
                            "event_type": "sensory_to_episodic_transfer",
                            "event_type": event.type,
                            "significance": memory_entry.meaning_significance,
                            "processing_count": processing_count,
                            "transfer_reason": (
                                "threshold_reached"
                                if processing_count >= self.SENSORY_TO_EPISODIC_THRESHOLD
                                else "high_intensity"
                            ),
                        }
                    )

                    # Очищаем счетчик для этого события (оно уже перенесено)
                    del self._event_processing_counts[event_hash]

        return transfers_count

    def _consolidate_episodic_to_semantic(self, self_state) -> int:
        """
        Консолидация от эпизодической к семантической памяти.

        Извлекает концепции и паттерны из повторяющихся эпизодов.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Количество перенесенных концепций
        """
        if not self.semantic_store or not self_state.memory:
            return 0

        transferred_concepts = 0

        # Анализируем эпизодическую память на предмет повторяющихся паттернов
        event_types = {}
        for entry in self_state.memory:
            event_type = entry.event_type
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # Извлекаем концепции из часто повторяющихся событий
        for event_type, count in event_types.items():
            if count >= self.EPISODIC_TO_SEMANTIC_THRESHOLD:
                # Создаем семантическую концепцию
                concept_id = f"concept_{event_type}_{int(time.time())}"

                concept = self.semantic_store.SemanticConcept(
                    concept_id=concept_id,
                    name=f"Pattern of {event_type}",
                    description=f"Recurring pattern of {event_type} events (observed {count} times)",
                    confidence=min(
                        0.8, count / 20.0
                    ),  # Уверенность растет с количеством наблюдений
                    activation_count=1,
                )

                self.semantic_store.add_concept(concept)
                transferred_concepts += 1

                self.logger.log_event(
                    {
                        "event_type": "episodic_to_semantic_transfer",
                        "concept_id": concept_id,
                        "source_event_type": event_type,
                        "observation_count": count,
                        "confidence": concept.confidence,
                    }
                )

        return transferred_concepts

    def _consolidate_semantic_knowledge(self) -> int:
        """
        Периодическая консолидация семантических знаний.

        Returns:
            Количество консолидированных концепций
        """
        if not self.semantic_store:
            return 0

        return self.semantic_store.consolidate_knowledge()

    def get_hierarchy_status(self) -> Dict[str, Any]:
        """
        Получить статус всей иерархии памяти.

        Returns:
            Dict со статусом всех уровней памяти
        """
        status = {
            "hierarchy_manager": {
                "transfers_sensory_to_episodic": self._transfer_stats["sensory_to_episodic"],
                "transfers_episodic_to_semantic": self._transfer_stats["episodic_to_semantic"],
                "transfers_semantic_to_procedural": self._transfer_stats["semantic_to_procedural"],
                "last_semantic_consolidation": self._transfer_stats["last_semantic_consolidation"],
            },
            "sensory_buffer": {
                **self.sensory_buffer.get_buffer_status(),
                "available": self.sensory_buffer is not None,
            },
            "episodic_memory": {
                "available": self.episodic_memory is not None,
                "status": "integrated" if self.episodic_memory is not None else "not_integrated",
            },
            "semantic_store": {
                "available": self.semantic_store is not None,
                "status": "implemented" if self.semantic_store else "not_implemented",
                "concepts_count": len(self.semantic_store._concepts) if self.semantic_store else 0,
            },
            "procedural_store": {
                "available": self.procedural_store is not None,
                "status": "implemented" if self.procedural_store else "not_implemented",
                "patterns_count": (
                    len(self.procedural_store._patterns) if self.procedural_store else 0
                ),
            },
        }

        return status

    def query_memory(self, level: str, **query_params) -> List[Any]:
        """
        Запрос к конкретному уровню памяти.

        Args:
            level: Уровень памяти ("sensory", "episodic", "semantic", "procedural")
            **query_params: Параметры запроса

        Returns:
            Результаты запроса
        """
        if level == "sensory":
            return self.sensory_buffer.peek_events(query_params.get("max_events"))
        elif level == "episodic":
            if self.episodic_memory:
                # TODO: Реализовать запрос к эпизодической памяти
                return []
            else:
                return []
        elif level == "semantic":
            if self.semantic_store:
                query_str = query_params.get("query", "")
                limit = query_params.get("limit", 10)
                return self.semantic_store.search_concepts(query_str, limit)
            else:
                return []
        elif level == "procedural":
            if self.procedural_store:
                context = query_params.get("context", {})
                return self.procedural_store.find_applicable_patterns(context)
            else:
                return []
        else:
            raise ValueError(f"Unknown memory level: {level}")

    def reset_hierarchy(self) -> None:
        """Сбросить всю иерархию памяти (для тестирования или перезапуска)."""
        self.sensory_buffer.clear_buffer()
        self._event_processing_counts.clear()
        self._transfer_stats = {
            "sensory_to_episodic": 0,
            "episodic_to_semantic": 0,
            "semantic_to_procedural": 0,
            "last_semantic_consolidation": time.time(),
        }

        self.logger.log_event({"event_type": "memory_hierarchy_reset"})

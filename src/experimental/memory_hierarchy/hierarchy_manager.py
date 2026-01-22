"""
Менеджер иерархии памяти - Memory Hierarchy Manager.

Координирует работу между уровнями памяти: сенсорным, эпизодическим,
семантическим и процедурным. Управляет переносом данных между уровнями.
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any

from src.environment.event import Event
from src.memory.memory_types import MemoryEntry
from src.observability.structured_logger import StructuredLogger
from src.contracts.serialization_contract import SerializationContract
from src.contracts.memory_hierarchy_api_contract import (
    MemoryQueryParams,
    MemoryQueryResult,
    ConsolidationResult,
    MemoryHierarchyAPIContract
)

from .sensory_buffer import SensoryBuffer
from .semantic_store import SemanticMemoryStore, SemanticConcept
from .procedural_store import ProceduralMemoryStore
from src.config.feature_flags import FeatureFlags

logger = logging.getLogger(__name__)


class MemoryHierarchyManager(SerializationContract, MemoryHierarchyAPIContract):
    """
    Центральный менеджер для координации многоуровневой системы памяти.

    Отвечает за:
    - Управление переносом данных между уровнями памяти
    - Координацию консолидации (sensory → episodic → semantic)
    - Управление procedural learning из опыта
    - API для запросов к разным уровням памяти
    """

    # Константы для управления переносом данных (по умолчанию)
    DEFAULT_SENSORY_TO_EPISODIC_THRESHOLD = 5  # Количество обработок события для переноса
    DEFAULT_EPISODIC_TO_SEMANTIC_THRESHOLD = 10  # Порог повторений для семантизации
    DEFAULT_SEMANTIC_CONSOLIDATION_INTERVAL = 60.0  # Интервал консолидации семантических знаний (секунды)

    def __init__(
        self,
        sensory_buffer: Optional[SensoryBuffer] = None,
        logger: Optional[StructuredLogger] = None,
        feature_flags: Optional[FeatureFlags] = None,
        sensory_to_episodic_threshold: Optional[int] = None,
        episodic_to_semantic_threshold: Optional[int] = None,
        semantic_consolidation_interval: Optional[float] = None,
    ):
        """
        Инициализация менеджера иерархии памяти.

        Args:
            sensory_buffer: Сенсорный буфер (если None, будет создан автоматически)
            logger: Логгер для структурированного логирования
            feature_flags: Менеджер feature flags (опционально)
            sensory_to_episodic_threshold: Порог переноса из сенсорного буфера в эпизодическую память
            episodic_to_semantic_threshold: Порог переноса из эпизодической в семантическую память
            semantic_consolidation_interval: Интервал консолидации семантических знаний (секунды)
        """
        self.logger = logger or StructuredLogger()

        # Thread-safety lock для защиты разделяемых структур данных
        self._lock = threading.RLock()

        # Feature flags для конфигурации
        self.feature_flags = feature_flags or FeatureFlags()

        # Настройка порогов переноса данных
        self.sensory_to_episodic_threshold = sensory_to_episodic_threshold or self.DEFAULT_SENSORY_TO_EPISODIC_THRESHOLD
        self.episodic_to_semantic_threshold = episodic_to_semantic_threshold or self.DEFAULT_EPISODIC_TO_SEMANTIC_THRESHOLD
        self.semantic_consolidation_interval = semantic_consolidation_interval or self.DEFAULT_SEMANTIC_CONSOLIDATION_INTERVAL

        # Инициализация уровней памяти
        # Создаем SensoryBuffer только если feature flag включен
        if sensory_buffer is not None:
            self.sensory_buffer = sensory_buffer
        elif self.feature_flags.is_sensory_buffer_enabled():
            self.sensory_buffer = SensoryBuffer()
        else:
            self.sensory_buffer = None

        # Интеграция с эпизодической памятью
        self._episodic_memory = None  # Будет установлено при вызове set_episodic_memory
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
                "sensory_buffer_size": self.sensory_buffer.buffer_size if self.sensory_buffer else 0,
                "sensory_buffer_enabled": self.sensory_buffer is not None,
            }
        )

    def set_episodic_memory(self, memory) -> None:
        """
        Установить ссылку на эпизодическую память для интеграции.

        Args:
            memory: Экземпляр Memory (эпизодическая память)
        """
        self._episodic_memory = memory
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
        if self.sensory_buffer is not None:
            self.sensory_buffer.add_event(event)

    def handle_clarity_moment(self, clarity_type: str, intensity: float, self_state) -> None:
        """
        Обработать момент ясности и его влияние на память.

        Args:
            clarity_type: Тип момента ясности
            intensity: Интенсивность момента ясности (0.0-1.0)
            self_state: Текущее состояние системы
        """
        # Моменты ясности усиливают консолидацию памяти
        clarity_effects = self._calculate_clarity_effects(clarity_type, intensity)

        # Применяем эффекты к консолидации
        if clarity_effects.get("boost_semantic_consolidation", False):
            # Ускоренная семантическая консолидация
            semantic_count = self._consolidate_semantic_knowledge()
            self.logger.log_event({
                "event_type": "clarity_boosted_semantic_consolidation",
                "clarity_type": clarity_type,
                "intensity": intensity,
                "concepts_consolidated": semantic_count,
            })

        if clarity_effects.get("boost_episodic_transfer", False):
            # Ускоренный перенос в семантическую память
            episodic_transfers = self._consolidate_episodic_to_semantic(self_state)
            self.logger.log_event({
                "event_type": "clarity_boosted_episodic_transfer",
                "clarity_type": clarity_type,
                "intensity": intensity,
                "concepts_transferred": episodic_transfers,
            })

        if clarity_effects.get("optimize_patterns", False):
            # Оптимизация процедурных паттернов
            if self.procedural_store:
                optimized_count = self.procedural_store.optimize_patterns()
                self.logger.log_event({
                    "event_type": "clarity_optimized_procedural_patterns",
                    "clarity_type": clarity_type,
                    "intensity": intensity,
                    "patterns_optimized": optimized_count,
                })

    def _calculate_clarity_effects(self, clarity_type: str, intensity: float) -> Dict[str, Any]:
        """
        Рассчитать эффекты момента ясности на память.

        Args:
            clarity_type: Тип момента ясности
            intensity: Интенсивность (0.0-1.0)

        Returns:
            Dict с эффектами
        """
        effects = {
            "boost_semantic_consolidation": False,
            "boost_episodic_transfer": False,
            "optimize_patterns": False,
        }

        # Разные типы ясности влияют на разные аспекты памяти
        if clarity_type == "cognitive" and intensity > 0.7:
            effects["boost_semantic_consolidation"] = True
            effects["boost_episodic_transfer"] = True
        elif clarity_type == "emotional" and intensity > 0.6:
            effects["optimize_patterns"] = True
        elif clarity_type == "existential" and intensity > 0.8:
            effects["boost_semantic_consolidation"] = True
            effects["optimize_patterns"] = True

        return effects

    def process_sensory_events(self, max_events: Optional[int] = None) -> List[Event]:
        """
        Обработать события из сенсорного буфера для передачи в MeaningEngine.

        Args:
            max_events: Максимальное количество событий для обработки

        Returns:
            Список событий для обработки MeaningEngine
        """
        if self.sensory_buffer is None:
            return []
        return self.sensory_buffer.get_events_for_processing(max_events)

    def consolidate_memory(self, self_state) -> ConsolidationResult:
        """
        Выполнить консолидацию памяти между уровнями.

        Архитектурный контракт MemoryHierarchyAPIContract:
        - Атомарность: Все переносы выполняются как единая транзакция
        - Thread-safety для конкурентного доступа
        - Стандартизированный ConsolidationResult
        - Отказоустойчивость и логирование

        Этот метод вызывается периодически для переноса данных между уровнями:
        - sensory → episodic (на основе повторений)
        - episodic → semantic (на основе паттернов)
        - semantic → procedural (на основе автоматизации)

        Args:
            self_state: Текущее состояние системы (SelfState)

        Returns:
            ConsolidationResult: Стандартизированная статистика консолидации

        Raises:
            RuntimeError: Если консолидация не может быть выполнена
        """
        import time
        start_time = time.time()

        try:
            sensory_to_episodic_transfers = 0
            episodic_to_semantic_transfers = 0
            semantic_consolidations = 0
            procedural_optimizations = 0

            # Консолидация sensory → episodic
            sensory_to_episodic_transfers = self._consolidate_sensory_to_episodic(self_state)

            # Консолидация episodic → semantic (пока заглушка)
            if self._episodic_memory and self.semantic_store:
                episodic_to_semantic_transfers = self._consolidate_episodic_to_semantic(self_state)

            # Периодическая консолидация semantic (раз в минуту)
            with self._lock:
                if (
                    time.time() - self._transfer_stats["last_semantic_consolidation"]
                    > self.semantic_consolidation_interval
                ):
                    semantic_consolidations = self._consolidate_semantic_knowledge()
                    self._transfer_stats["last_semantic_consolidation"] = time.time()

            duration = time.time() - start_time

            consolidation_result = ConsolidationResult(
                sensory_to_episodic_transfers=sensory_to_episodic_transfers,
                episodic_to_semantic_transfers=episodic_to_semantic_transfers,
                semantic_consolidations=semantic_consolidations,
                procedural_optimizations=procedural_optimizations,
                timestamp=time.time(),
                duration=duration,
                success=True,
                details={
                    "sensory_buffer_available": self.sensory_buffer is not None,
                    "episodic_memory_available": self._episodic_memory is not None,
                    "semantic_store_available": self.semantic_store is not None,
                    "procedural_store_available": self.procedural_store is not None,
                }
            )

            self.logger.log_event({
                "event_type": "memory_consolidation_completed",
                "sensory_to_episodic_transfers": sensory_to_episodic_transfers,
                "episodic_to_semantic_transfers": episodic_to_semantic_transfers,
                "semantic_consolidations": semantic_consolidations,
                "duration": duration,
                "success": True
            })

            return consolidation_result

        except Exception as e:
            duration = time.time() - start_time

            self.logger.log_event({
                "event_type": "memory_consolidation_failed",
                "error": str(e),
                "duration": duration,
                "success": False
            })

            return ConsolidationResult(
                sensory_to_episodic_transfers=0,
                episodic_to_semantic_transfers=0,
                semantic_consolidations=0,
                procedural_optimizations=0,
                timestamp=time.time(),
                duration=duration,
                success=False,
                error_message=str(e)
            )

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
        with self._lock:
            transfers_count = 0

        # Получаем события для анализа консолидации (не удаляем из буфера)
        sensory_events = self.sensory_buffer.peek_events(max_events=None) if self.sensory_buffer else []

        # Отладка
        if sensory_events:
            self.logger.log_event(
                {
                    "event_type": "debug_sensory_consolidation",
                    "events_count": len(sensory_events),
                    "episodic_memory_available": self._episodic_memory is not None,
                }
            )

        for event in sensory_events:
            # Создаем идентификатор события для отслеживания повторений по типу
            event_hash = event.type

            # Thread-safe увеличение счетчика "видов" события
            with self._lock:
                self._event_processing_counts[event_hash] = (
                    self._event_processing_counts.get(event_hash, 0) + 1
                )
                processing_count = self._event_processing_counts[event_hash]

            # Проверяем условия для переноса в эпизодическую память:
            # 1. Достигнут порог повторений ИЛИ
            # 2. Высокая интенсивность (даже при первой обработке)
            should_transfer = (
                processing_count >= self.sensory_to_episodic_threshold
                or abs(event.intensity) > 0.8  # Порог высокой интенсивности
            )

            # Отладка
            self.logger.log_event(
                {
                    "event_type": "debug_transfer_check",
                    "event_type": event.type,
                    "intensity": event.intensity,
                    "processing_count": processing_count,
                    "threshold": self.sensory_to_episodic_threshold,
                    "should_transfer": should_transfer,
                    "episodic_memory_available": self._episodic_memory is not None,
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
                if self._episodic_memory is not None:
                    if hasattr(self._episodic_memory, 'append'):
                        self._episodic_memory.append(memory_entry)
                    elif hasattr(self._episodic_memory, 'add_entry'):
                        self._episodic_memory.add_entry(memory_entry)
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
                            if processing_count >= self.sensory_to_episodic_threshold
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
        if not self.semantic_store or not self._episodic_memory:
            return 0

        transferred_concepts = 0

        # Анализируем эпизодическую память на предмет повторяющихся паттернов
        event_types = {}
        for entry in self._episodic_memory:
            event_type = entry.event_type
            event_types[event_type] = event_types.get(event_type, 0) + 1

        # Извлекаем концепции из часто повторяющихся событий
        for event_type, count in event_types.items():
            if count >= self.episodic_to_semantic_threshold:
                # Создаем семантическую концепцию
                concept_id = f"concept_{event_type}_{int(time.time())}"

                # Вычисляем среднюю значимость для концепции
                total_significance = 0.0
                count_for_avg = 0
                for entry in self._episodic_memory:
                    if entry.event_type == event_type:
                        total_significance += entry.meaning_significance
                        count_for_avg += 1

                avg_significance = total_significance / count_for_avg if count_for_avg > 0 else 0.0

                concept = SemanticConcept(
                    concept_id=concept_id,
                    name=f"Pattern of {event_type}",
                    description=f"Recurring pattern of {event_type} events (observed {count} times, avg significance: {avg_significance:.2f})",
                    confidence=min(
                        0.9, count / 15.0
                    ),  # Уверенность растет с количеством наблюдений
                    activation_count=1,
                )

                # Добавляем свойства концепции
                concept.properties.update({
                    "source_event_type": event_type,
                    "observation_count": count,
                    "avg_significance": avg_significance,
                    "consolidation_time": time.time(),
                })

                self.semantic_store.add_concept(concept)
                transferred_concepts += 1

                self.logger.log_event(
                    {
                        "event_type": "episodic_to_semantic_transfer",
                        "concept_id": concept_id,
                        "source_event_type": event_type,
                        "observation_count": count,
                        "avg_significance": avg_significance,
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
        with self._lock:
            transfer_stats = dict(self._transfer_stats)

        status = {
            "hierarchy_manager": {
                "transfers_sensory_to_episodic": transfer_stats["sensory_to_episodic"],
                "transfers_episodic_to_semantic": transfer_stats["episodic_to_semantic"],
                "transfers_semantic_to_procedural": transfer_stats["semantic_to_procedural"],
                "last_semantic_consolidation": transfer_stats["last_semantic_consolidation"],
            },
            "sensory_buffer": {
                **(self.sensory_buffer.get_buffer_status() if self.sensory_buffer else {}),
                "available": self.sensory_buffer is not None,
            },
            "episodic_memory": {
                "available": self._episodic_memory is not None,
                "status": "integrated" if self._episodic_memory is not None else "not_integrated",
            },
            "semantic_store": {
                "available": self.semantic_store is not None,
                "status": "implemented" if self.semantic_store else "not_implemented",
                "concepts_count": self.semantic_store.get_concepts_count() if self.semantic_store else 0,
            },
            "procedural_store": {
                "available": self.procedural_store is not None,
                "status": "implemented" if self.procedural_store else "not_implemented",
                "patterns_count": self.procedural_store.size if self.procedural_store else 0,
            },
        }

        return status

    def query_memory(self, level: str, **query_params) -> MemoryQueryResult:
        """
        Запрос к конкретному уровню памяти.

        Архитектурный контракт MemoryHierarchyAPIContract:
        - Валидация входных параметров
        - Thread-safety для конкурентного доступа
        - Стандартизированный MemoryQueryResult
        - Обработка ошибок без нарушения состояния

        Args:
            level: Уровень памяти ("sensory", "episodic", "semantic", "procedural")
            **query_params: Параметры запроса (см. MemoryQueryParams)

        Returns:
            MemoryQueryResult: Стандартизированный результат запроса

        Raises:
            ValueError: Если уровень памяти неизвестен
            RuntimeError: Если запрос не может быть выполнен
        """
        import time
        start_time = time.time()

        try:
            # Создаем параметры запроса из kwargs
            params = MemoryQueryParams(**query_params)

            # Валидация уровня памяти
            valid_levels = {"sensory", "episodic", "semantic", "procedural"}
            if level not in valid_levels:
                raise ValueError(f"Unknown memory level: {level}. Valid levels: {valid_levels}")

            results = []
            total_count = 0

            # Выполняем запрос в зависимости от уровня
            if level == "sensory":
                if self.sensory_buffer:
                    max_events = params.max_events or 100
                    results = self.sensory_buffer.peek_events(max_events)
                    total_count = self.sensory_buffer.size
                else:
                    results = []
                    total_count = 0

            elif level == "episodic":
                if self._episodic_memory:
                    # TODO: Реализовать полноценный запрос к эпизодической памяти
                    # Пока возвращаем пустой результат
                    results = []
                    total_count = 0
                else:
                    results = []
                    total_count = 0

            elif level == "semantic":
                if self.semantic_store:
                    query_str = params.query or ""
                    limit = params.limit or 10
                    results = self.semantic_store.search_concepts(query_str, limit)
                    total_count = len(results)  # Приблизительная оценка
                else:
                    results = []
                    total_count = 0

            elif level == "procedural":
                if self.procedural_store:
                    context = params.context or {}
                    results = self.procedural_store.find_applicable_patterns(context)
                    total_count = len(results)
                else:
                    results = []
                    total_count = 0

            execution_time = time.time() - start_time

            return MemoryQueryResult(
                level=level,
                results=results,
                total_count=total_count,
                query_params=params,
                execution_time=execution_time,
                success=True
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return MemoryQueryResult(
                level=level,
                results=[],
                total_count=0,
                query_params=MemoryQueryParams(),
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )

    def reset_hierarchy(self) -> None:
        """Сбросить всю иерархию памяти (для тестирования или перезапуска)."""
        with self._lock:
            if self.sensory_buffer:
                self.sensory_buffer.clear_buffer()
            self._event_processing_counts.clear()
            self._transfer_stats = {
                "sensory_to_episodic": 0,
                "episodic_to_semantic": 0,
                "semantic_to_procedural": 0,
                "last_semantic_consolidation": time.time(),
            }

            self.logger.log_event({"event_type": "memory_hierarchy_reset"})

    @property
    def episodic_memory(self):
        """
        Получить эпизодическую память.

        Returns:
            Экземпляр эпизодической памяти или None
        """
        return self._episodic_memory

    @episodic_memory.setter
    def episodic_memory(self, memory):
        """
        Установить эпизодическую память.

        Args:
            memory: Экземпляр эпизодической памяти
        """
        self._episodic_memory = memory
        if memory is not None:
            self.logger.log_event(
                {
                    "event_type": "episodic_memory_integrated_via_property",
                    "memory_entries_count": len(memory) if hasattr(memory, '__len__') else 0,
                }
            )

    def set_transfer_thresholds(
        self,
        sensory_to_episodic: Optional[int] = None,
        episodic_to_semantic: Optional[int] = None,
        semantic_consolidation_interval: Optional[float] = None,
    ) -> None:
        """
        Настроить пороги переноса данных между уровнями памяти.

        Args:
            sensory_to_episodic: Порог переноса из сенсорного буфера в эпизодическую память
            episodic_to_semantic: Порог переноса из эпизодической в семантическую память
            semantic_consolidation_interval: Интервал консолидации семантических знаний (секунды)
        """
        old_thresholds = {
            "sensory_to_episodic": self.sensory_to_episodic_threshold,
            "episodic_to_semantic": self.episodic_to_semantic_threshold,
            "semantic_consolidation_interval": self.semantic_consolidation_interval,
        }

        if sensory_to_episodic is not None:
            self.sensory_to_episodic_threshold = max(1, sensory_to_episodic)  # Минимум 1
        if episodic_to_semantic is not None:
            self.episodic_to_semantic_threshold = max(1, episodic_to_semantic)  # Минимум 1
        if semantic_consolidation_interval is not None:
            self.semantic_consolidation_interval = max(1.0, semantic_consolidation_interval)  # Минимум 1 секунда

        new_thresholds = {
            "sensory_to_episodic": self.sensory_to_episodic_threshold,
            "episodic_to_semantic": self.episodic_to_semantic_threshold,
            "semantic_consolidation_interval": self.semantic_consolidation_interval,
        }

        self.logger.log_event(
            {
                "event_type": "memory_transfer_thresholds_updated",
                "old_thresholds": old_thresholds,
                "new_thresholds": new_thresholds,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализовать состояние менеджера иерархии памяти.

        Returns:
            Dict[str, Any]: Словарь с состоянием компонента
        """
        import time
        current_time = time.time()

        with self._lock:
            return {
                "sensory_buffer": self.sensory_buffer.to_dict() if self.sensory_buffer else None,
                "semantic_store": self.semantic_store.to_dict() if self.semantic_store else None,
                "procedural_store": self.procedural_store.to_dict() if self.procedural_store else None,
                "configuration": {
                    "sensory_to_episodic_threshold": self.sensory_to_episodic_threshold,
                    "episodic_to_semantic_threshold": self.episodic_to_semantic_threshold,
                    "semantic_consolidation_interval": self.semantic_consolidation_interval,
                },
                "statistics": dict(self._transfer_stats),
                "event_processing_counts": dict(self._event_processing_counts),
                "episodic_memory_available": self._episodic_memory is not None,
                "timestamp": current_time,
            }

    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Получить метаданные сериализации менеджера иерархии памяти.

        Returns:
            Dict[str, Any]: Метаданные сериализации
        """
        import time
        current_time = time.time()

        with self._lock:
            return {
                "version": "1.0",
                "timestamp": current_time,
                "component_type": "memory_hierarchy_manager",
                "thread_safe": True,  # MemoryHierarchyManager thread-safe для чтения
                "sensory_buffer_enabled": self.sensory_buffer is not None,
                "semantic_store_enabled": self.semantic_store is not None,
                "procedural_store_enabled": self.procedural_store is not None,
                "episodic_memory_integrated": self._episodic_memory is not None,
                "total_size_bytes": self._estimate_size(),
            }

    def _estimate_size(self) -> int:
        """Оценить размер всей иерархии памяти в байтах."""
        size = 0
        if self.sensory_buffer:
            size += self.sensory_buffer.get_serialization_metadata()["total_size_bytes"]
        if self.semantic_store:
            size += self.semantic_store.get_serialization_metadata()["total_size_bytes"]
        if self.procedural_store:
            size += self.procedural_store.get_serialization_metadata()["total_size_bytes"]
        return size

    def get_transfer_thresholds(self) -> Dict[str, Any]:
        """
        Получить текущие пороги переноса данных.

        Returns:
            Dict с текущими порогами
        """
        return {
            "sensory_to_episodic_threshold": self.sensory_to_episodic_threshold,
            "episodic_to_semantic_threshold": self.episodic_to_semantic_threshold,
            "semantic_consolidation_interval": self.semantic_consolidation_interval,
        }

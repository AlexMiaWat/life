"""
Адаптивный менеджер обработки - Adaptive Processing Manager.

Техническая система для детекции и управления адаптивными состояниями обработки,
оптимизирующими производительность системы Life в различных условиях.
Заменяет старую систему моментов ясности и состояний сознания.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.observability.structured_logger import StructuredLogger
from src.experimental.memory_hierarchy.hierarchy_manager import MemoryHierarchyManager

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Технические режимы обработки данных."""
    BASELINE = "baseline"           # Базовый режим обработки
    EFFICIENT = "efficient"         # Эффективный режим (быстрая обработка)
    INTENSIVE = "intensive"         # Интенсивный анализ (глубокий анализ)
    OPTIMIZED = "optimized"         # Оптимизированный режим (высокая эффективность)
    SELF_MONITORING = "self_monitoring"  # Режим самоконтроля системы


class AdaptiveState(Enum):
    """Адаптивные состояния системы."""
    STANDARD = "standard"           # Стандартное состояние
    EFFICIENT_PROCESSING = "efficient_processing"  # Эффективная обработка
    INTENSIVE_ANALYSIS = "intensive_analysis"      # Интенсивный анализ
    SYSTEM_SELF_MONITORING = "system_self_monitoring"  # Самоконтроль системы
    OPTIMAL_PROCESSING = "optimal_processing"      # Оптимальная обработка


@dataclass
class ProcessingEvent:
    """Событие изменения режима обработки."""
    processing_mode: ProcessingMode
    intensity: float = 1.0
    duration_ticks: int = 50
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class AdaptiveProcessingConfig:
    """Конфигурация адаптивного менеджера обработки."""

    # Пороги детекции режимов
    stability_threshold: float = 0.8
    energy_threshold: float = 0.7
    processing_efficiency_threshold: float = 0.6
    cognitive_load_max: float = 0.7

    # Настройки состояний
    enable_efficient_processing: bool = True
    enable_intensive_analysis: bool = True
    enable_system_self_monitoring: bool = True
    enable_optimal_processing: bool = True

    # Настройки производительности
    check_interval: float = 1.0  # секунды
    state_transition_cooldown: float = 5.0  # секунды
    max_history_size: int = 100
    max_transition_history_size: int = 50

    # Настройки интеграции
    integrate_with_memory: bool = True
    adaptive_thresholds_enabled: bool = True


class AdaptiveProcessingManager:
    """
    Адаптивный менеджер обработки.

    Управляет техническими режимами обработки для оптимизации производительности
    системы Life в различных условиях функционирования.

    Заменяет ClarityConsciousnessManager с технической терминологией.
    """

    def __init__(
        self,
        self_state_provider: Callable,
        config: Optional[AdaptiveProcessingConfig] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        """
        Инициализация адаптивного менеджера обработки.

        Args:
            self_state_provider: Функция для получения SelfState
            config: Конфигурация системы
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)
        self.config = config or AdaptiveProcessingConfig()
        self.self_state_provider = self_state_provider

        # Компоненты системы
        self._memory_hierarchy = self._create_memory_hierarchy()

        # Состояние менеджера
        self._is_active = False
        self._last_update_time = 0.0
        self._update_interval = 0.5  # 2 Hz

        # История обработки
        self.processing_history: List[ProcessingEvent] = []
        self.state_transitions: List[Dict[str, Any]] = []

        # Статистика
        self._stats = {
            "total_updates": 0,
            "processing_events_triggered": 0,
            "state_transitions": 0,
            "memory_integrations": 0,
            "start_time": time.time(),
        }

        # Валидация конфигурации
        self._validate_config()

        self.logger.log_event({
            "event_type": "adaptive_processing_manager_initialized",
            "config": self._config_to_dict(),
        })

    def _validate_config(self) -> None:
        """Валидация конфигурации."""
        if not isinstance(self.config.stability_threshold, (int, float)):
            raise ValueError("stability_threshold must be numeric")
        if not (0.0 <= self.config.stability_threshold <= 1.0):
            raise ValueError("stability_threshold must be between 0.0 and 1.0")

        if not isinstance(self.config.energy_threshold, (int, float)):
            raise ValueError("energy_threshold must be numeric")
        if not (0.0 <= self.config.energy_threshold <= 1.0):
            raise ValueError("energy_threshold must be between 0.0 and 1.0")

        # Проверка других параметров...

    def _create_memory_hierarchy(self) -> Optional[MemoryHierarchyManager]:
        """Создать менеджер иерархии памяти."""
        if not self.config.integrate_with_memory:
            return None

        try:
            return MemoryHierarchyManager(logger=self.logger)
        except Exception as e:
            self.logger.log_event({
                "event_type": "memory_hierarchy_creation_failed",
                "error": str(e),
            })
            return None

    def _config_to_dict(self) -> Dict[str, Any]:
        """Конвертировать конфигурацию в словарь для логирования."""
        return {
            "stability_threshold": self.config.stability_threshold,
            "energy_threshold": self.config.energy_threshold,
            "processing_efficiency_threshold": self.config.processing_efficiency_threshold,
            "enable_efficient_processing": self.config.enable_efficient_processing,
            "enable_intensive_analysis": self.config.enable_intensive_analysis,
            "enable_system_self_monitoring": self.config.enable_system_self_monitoring,
            "enable_optimal_processing": self.config.enable_optimal_processing,
            "integrate_with_memory": self.config.integrate_with_memory,
        }

    def start(self) -> None:
        """Запустить адаптивную систему обработки."""
        if self._is_active:
            return

        self._is_active = True
        self.logger.log_event({"event_type": "adaptive_processing_manager_started"})

    def stop(self) -> None:
        """Остановить адаптивную систему обработки."""
        if not self._is_active:
            return

        self._is_active = False
        self.logger.log_event({"event_type": "adaptive_processing_manager_stopped"})

    def update(self, self_state) -> Dict[str, Any]:
        """
        Обновить состояние адаптивной системы обработки.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Dict с результатами обновления
        """
        if not self._is_active:
            return {"status": "inactive"}

        current_time = time.time()
        if current_time - self._last_update_time < self._update_interval:
            return {"status": "too_early"}

        self._last_update_time = current_time
        self._stats["total_updates"] += 1

        results = {
            "status": "updated",
            "processing_events": [],
            "state_transitions": [],
            "memory_operations": [],
            "timestamp": current_time,
        }

        # Детекция режимов обработки
        processing_event = self._detect_processing_conditions(self_state)
        if processing_event:
            self._apply_processing_effects(self_state, processing_event)
            results["processing_events"].append({
                "mode": processing_event.processing_mode.value,
                "intensity": processing_event.intensity,
                "duration": processing_event.duration_ticks,
            })
            self._stats["processing_events_triggered"] += 1

            # Обновить SelfState
            self_state.processing_mode = processing_event.processing_mode.value
            self_state.processing_intensity = processing_event.intensity
            self._add_to_processing_history(self_state, processing_event)

        # Обновление состояний обработки
        self._update_state_transitions(self_state)

        # Интеграция с памятью
        if self._memory_hierarchy and self.config.integrate_with_memory:
            memory_result = self._update_memory_integration(self_state)
            results["memory_operations"].append(memory_result)
            self._stats["memory_integrations"] += 1

        # Обновление метрик SelfState
        self._update_self_state_metrics(self_state)

        # Логирование результатов (не на каждом обновлении)
        if self._stats["total_updates"] % 20 == 0:  # Каждые 20 обновлений
            self.logger.log_event({
                "event_type": "adaptive_processing_update_summary",
                "total_updates": self._stats["total_updates"],
                "processing_events": self._stats["processing_events_triggered"],
                "state_transitions": self._stats["state_transitions"],
                "memory_integrations": self._stats["memory_integrations"],
            })

        return results

    def _detect_processing_conditions(self, self_state) -> Optional[ProcessingEvent]:
        """
        Детекция условий для активации режима обработки.

        Args:
            self_state: Текущее состояние системы

        Returns:
            ProcessingEvent если условия выполнены, None иначе
        """
        current_time = time.time()

        # Проверяем частоту проверок
        if current_time - getattr(self, '_last_check_time', 0) < self.config.check_interval:
            return None

        setattr(self, '_last_check_time', current_time)

        # Проверяем, не активен ли уже режим обработки
        if getattr(self_state, "processing_state", False):
            return None

        # Собираем метрики для анализа
        metrics = self._gather_processing_metrics(self_state)

        # Проверяем базовые условия
        if not self._check_basic_processing_conditions(metrics):
            return None

        # Определяем режим обработки
        processing_mode = self._determine_processing_mode(metrics)

        # Проверяем специфические условия для режима
        if not self._check_processing_mode_conditions(processing_mode, metrics):
            return None

        # Создаем событие режима обработки
        processing_event = ProcessingEvent(
            processing_mode=processing_mode,
            intensity=self._calculate_processing_intensity(metrics),
            duration_ticks=self._calculate_processing_duration(processing_mode),
            trigger_conditions=metrics,
        )

        self.processing_history.append(processing_event)

        self.logger.log_event({
            "event_type": "processing_conditions_detected",
            "processing_mode": processing_mode.value,
            "intensity": processing_event.intensity,
            "duration": processing_event.duration_ticks,
            "trigger_metrics": metrics,
        })

        return processing_event

    def _gather_processing_metrics(self, self_state) -> Dict[str, float]:
        """Собирает метрики для анализа режимов обработки."""
        return {
            "stability": getattr(self_state, "stability", 0.5),
            "energy": getattr(self_state, "energy", 0.5),
            "processing_efficiency": getattr(self_state, "processing_efficiency", 0.0),
            "cognitive_load": getattr(self_state, "cognitive_load", 0.3),
            "self_reflection_score": getattr(self_state, "self_reflection_score", 0.0),
            "meta_cognition_depth": getattr(self_state, "meta_cognition_depth", 0.0),
        }

    def _check_basic_processing_conditions(self, metrics: Dict[str, float]) -> bool:
        """Проверяет базовые условия для режима обработки."""
        stability_ok = metrics["stability"] >= self.config.stability_threshold
        energy_ok = metrics["energy"] >= self.config.energy_threshold
        efficiency_ok = metrics["processing_efficiency"] >= self.config.processing_efficiency_threshold
        cognitive_ok = metrics["cognitive_load"] <= self.config.cognitive_load_max

        return stability_ok and energy_ok and efficiency_ok and cognitive_ok

    def _determine_processing_mode(self, metrics: Dict[str, float]) -> ProcessingMode:
        """Определяет режим обработки на основе метрик."""
        efficiency = metrics["processing_efficiency"]
        reflection = metrics["self_reflection_score"]
        meta = metrics["meta_cognition_depth"]

        # Оптимальный режим (высший уровень)
        if efficiency > 0.9 and meta > 0.8:
            return ProcessingMode.OPTIMIZED

        # Режим самоконтроля
        elif efficiency > 0.7 and meta > 0.6:
            return ProcessingMode.SELF_MONITORING

        # Интенсивный анализ
        elif efficiency > 0.6 and reflection > 0.7:
            return ProcessingMode.INTENSIVE

        # Эффективный режим
        elif efficiency > 0.5 and metrics["stability"] > 0.7:
            return ProcessingMode.EFFICIENT

        # Базовый режим (по умолчанию)
        else:
            return ProcessingMode.BASELINE

    def _check_processing_mode_conditions(self, mode: ProcessingMode, metrics: Dict[str, float]) -> bool:
        """Проверяет специфические условия для режима обработки."""
        if mode == ProcessingMode.OPTIMIZED:
            return (
                metrics["processing_efficiency"] > 0.8
                and metrics["meta_cognition_depth"] > 0.7
            )

        elif mode == ProcessingMode.SELF_MONITORING:
            return (
                metrics["processing_efficiency"] > 0.6
                and metrics["meta_cognition_depth"] > 0.5
            )

        elif mode == ProcessingMode.INTENSIVE:
            return (
                metrics["processing_efficiency"] > 0.5
                and metrics["self_reflection_score"] > 0.6
            )

        elif mode == ProcessingMode.EFFICIENT:
            return (
                metrics["processing_efficiency"] > 0.4
                and metrics["stability"] > 0.6
            )

        # Базовый режим - уже проверен в _check_basic_processing_conditions
        return True

    def _calculate_processing_intensity(self, metrics: Dict[str, float]) -> float:
        """Вычисляет интенсивность режима обработки."""
        base_intensity = (
            metrics["stability"] * 0.3 +
            metrics["energy"] * 0.3 +
            metrics["processing_efficiency"] * 0.4
        )

        return min(1.0, max(0.1, base_intensity))

    def _calculate_processing_duration(self, mode: ProcessingMode) -> int:
        """Вычисляет длительность режима обработки в зависимости от типа."""
        base_duration = 50  # тиков

        if mode == ProcessingMode.OPTIMIZED:
            return int(base_duration * 1.5)  # 75 тиков
        elif mode == ProcessingMode.INTENSIVE:
            return int(base_duration * 1.2)  # 60 тиков
        elif mode == ProcessingMode.SELF_MONITORING:
            return int(base_duration * 1.1)  # 55 тиков
        else:
            return base_duration

    def _apply_processing_effects(self, self_state, processing_event: ProcessingEvent) -> None:
        """
        Применяет эффекты режима обработки к состоянию системы.

        Args:
            self_state: Состояние системы
            processing_event: Событие режима обработки
        """
        mode = processing_event.processing_mode
        intensity = processing_event.intensity

        # Базовые эффекты
        self_state.processing_state = True
        self_state.processing_duration = processing_event.duration_ticks
        base_modifier = 1.0 + (0.5 * intensity)
        self_state.processing_modifier = base_modifier

        # Дополнительные эффекты в зависимости от режима
        if mode == ProcessingMode.EFFICIENT:
            # Улучшение эффективности обработки
            if hasattr(self_state, "cognitive_load"):
                self_state.cognitive_load = max(0.0, self_state.cognitive_load - 0.2 * intensity)

        elif mode == ProcessingMode.INTENSIVE:
            # Углубленный анализ
            if hasattr(self_state, "self_reflection_score"):
                self_state.self_reflection_score = min(1.0, self_state.self_reflection_score + 0.15 * intensity)

        elif mode == ProcessingMode.SELF_MONITORING:
            # Улучшение самоконтроля
            if hasattr(self_state, "meta_cognition_depth"):
                self_state.meta_cognition_depth = min(1.0, self_state.meta_cognition_depth + 0.1 * intensity)

        elif mode == ProcessingMode.OPTIMIZED:
            # Оптимизация всех параметров
            if hasattr(self_state, "meta_cognition_depth"):
                self_state.meta_cognition_depth = min(1.0, self_state.meta_cognition_depth + 0.2 * intensity)
            self_state.processing_modifier = base_modifier * 1.2

        # Эффекты на память
        self._apply_memory_effects(self_state, processing_event)

        self.logger.log_event({
            "event_type": "processing_effects_applied",
            "processing_mode": mode.value,
            "intensity": intensity,
            "duration": processing_event.duration_ticks,
            "modifier": self_state.processing_modifier,
        })

    def _apply_memory_effects(self, self_state, processing_event: ProcessingEvent) -> None:
        """Применить эффекты режима обработки на память."""
        if not self._memory_hierarchy:
            return

        mode = processing_event.processing_mode
        intensity = processing_event.intensity

        try:
            if mode == ProcessingMode.OPTIMIZED:
                # Оптимизированный режим вызывает интенсивную консолидацию
                consolidation_stats = self._memory_hierarchy.consolidate_memory(self_state)
                self.logger.log_event({
                    "event_type": "memory_consolidation_boosted_by_optimized_mode",
                    "processing_mode": mode.value,
                    "intensity": intensity,
                    "consolidation_stats": consolidation_stats,
                })

            elif mode == ProcessingMode.INTENSIVE:
                # Интенсивный анализ улучшает обработку сенсорной информации
                if hasattr(self_state, "recent_events") and self_state.recent_events:
                    for event in self_state.recent_events[-3:]:
                        self._memory_hierarchy.add_sensory_event(event)

            # Во всех режимах обработки повышается эффективность консолидации
            if hasattr(self_state, "memory"):
                for entry in self_state.memory[-10:]:
                    entry.weight = min(1.0, entry.weight + 0.1 * intensity)

        except Exception as e:
            self.logger.log_event({
                "event_type": "memory_effects_application_error",
                "error": str(e),
                "processing_mode": processing_event.processing_mode.value,
            })

    def _update_state_transitions(self, self_state) -> None:
        """Обновляет переходы между адаптивными состояниями."""
        if not hasattr(self_state, 'current_adaptive_state'):
            self_state.current_adaptive_state = AdaptiveState.STANDARD.value

        # Определяем желаемое состояние
        target_state = self._determine_adaptive_state(self_state)

        # Проверяем необходимость перехода
        if self_state.current_adaptive_state != target_state.value:
            # Создаем запись о переходе
            transition = {
                "timestamp": time.time(),
                "from_state": self_state.current_adaptive_state,
                "to_state": target_state.value,
                "trigger": "automatic_transition",
            }

            self.state_transitions.append(transition)
            self_state.current_adaptive_state = target_state.value
            self._stats["state_transitions"] += 1

            # Применяем эффекты перехода
            self._apply_state_transition_effects(self_state, target_state)

            self.logger.log_event({
                "event_type": "adaptive_state_transition",
                "from_state": transition["from_state"],
                "to_state": target_state.value,
                "trigger": "automatic_transition",
            })

    def _determine_adaptive_state(self, self_state) -> AdaptiveState:
        """Определяет адаптивное состояние на основе метрик."""
        efficiency = getattr(self_state, "processing_efficiency", 0.0)
        stability = getattr(self_state, "stability", 0.5)
        meta_depth = getattr(self_state, "meta_cognition_depth", 0.0)

        # Приоритет состояний (от высшего к низшему)
        if efficiency > 0.9 and meta_depth > 0.8:
            return AdaptiveState.OPTIMAL_PROCESSING
        elif efficiency > 0.7 and meta_depth > 0.6:
            return AdaptiveState.SYSTEM_SELF_MONITORING
        elif efficiency > 0.6 and stability > 0.8:
            return AdaptiveState.EFFICIENT_PROCESSING
        elif efficiency > 0.5:
            return AdaptiveState.INTENSIVE_ANALYSIS
        else:
            return AdaptiveState.STANDARD

    def _apply_state_transition_effects(self, self_state, target_state: AdaptiveState) -> None:
        """Применить эффекты перехода состояния."""
        if not self._memory_hierarchy:
            return

        try:
            if target_state == AdaptiveState.EFFICIENT_PROCESSING:
                # Эффективная обработка ускоряет консолидацию сенсорной информации
                if hasattr(self_state, "recent_events") and self_state.recent_events:
                    for event in self_state.recent_events[-5:]:
                        self._memory_hierarchy.add_sensory_event(event)

            elif target_state == AdaptiveState.INTENSIVE_ANALYSIS:
                # Интенсивный анализ усиливает консолидацию
                consolidation_stats = self._memory_hierarchy.consolidate_memory(self_state)
                self.logger.log_event({
                    "event_type": "memory_intensive_analysis_effects",
                    "to_state": target_state.value,
                    "consolidation_stats": consolidation_stats,
                })

            elif target_state == AdaptiveState.SYSTEM_SELF_MONITORING:
                # Самоконтроль улучшает семантическую консолидацию
                if hasattr(self_state, "memory"):
                    for entry in self_state.memory[-20:]:
                        if hasattr(entry, "event_type"):
                            entry.weight = min(1.0, entry.weight + 0.05)

            elif target_state == AdaptiveState.OPTIMAL_PROCESSING:
                # Оптимальная обработка вызывает полную консолидацию
                consolidation_stats = self._memory_hierarchy.consolidate_memory(self_state)
                self.logger.log_event({
                    "event_type": "memory_optimal_processing_effects",
                    "to_state": target_state.value,
                    "consolidation_stats": consolidation_stats,
                })

        except Exception as e:
            self.logger.log_event({
                "event_type": "state_transition_effects_error",
                "error": str(e),
                "target_state": target_state.value,
            })

    def _add_to_processing_history(self, self_state, processing_event: ProcessingEvent) -> None:
        """Добавить событие обработки в историю SelfState."""
        history_entry = {
            "timestamp": processing_event.timestamp,
            "mode": processing_event.processing_mode.value,
            "intensity": processing_event.intensity,
            "duration": processing_event.duration_ticks,
            "trigger_conditions": processing_event.trigger_conditions,
        }

        if not hasattr(self_state, "processing_history"):
            self_state.processing_history = []

        self_state.processing_history.append(history_entry)

        # Ограничить размер истории
        if len(self_state.processing_history) > self.config.max_history_size:
            self_state.processing_history = self_state.processing_history[-self.config.max_history_size:]

    def _update_memory_integration(self, self_state) -> Dict[str, Any]:
        """Обновить интеграцию с многоуровневой памятью."""
        try:
            if hasattr(self_state, "recent_events") and self_state.recent_events:
                for event in self_state.recent_events[-5:]:
                    self._memory_hierarchy.add_sensory_event(event)

            consolidation_stats = self._memory_hierarchy.consolidate_memory(self_state)

            return {
                "operation": "consolidation",
                "stats": consolidation_stats,
                "success": True,
            }
        except Exception as e:
            self.logger.log_event({
                "event_type": "memory_integration_error",
                "error": str(e),
            })
            return {
                "operation": "consolidation",
                "error": str(e),
                "success": False,
            }

    def _update_self_state_metrics(self, self_state) -> None:
        """Обновить метрики в SelfState."""
        # Обновление метрик обработки
        self_state.processing_efficiency = getattr(self_state, "processing_efficiency", 0.0)

        # Обновление состояния обработки
        current_state = getattr(self_state, "current_adaptive_state", AdaptiveState.STANDARD.value)
        if self_state.current_adaptive_state != current_state:
            self_state.current_adaptive_state = current_state
            self._stats["state_transitions"] += 1

    def trigger_processing_event(self, self_state, processing_mode: ProcessingMode, intensity: float = 1.0) -> bool:
        """
        Принудительно вызвать режим обработки указанного типа.

        Args:
            self_state: Состояние системы
            processing_mode: Режим обработки
            intensity: Интенсивность (0.0-1.0)

        Returns:
            True если событие было вызвано успешно
        """
        try:
            # Создать искусственное событие обработки
            processing_event = ProcessingEvent(
                processing_mode=processing_mode,
                intensity=min(1.0, max(0.0, intensity)),
                trigger_conditions={"manual_trigger": True, "requested_mode": processing_mode.value},
            )

            # Применить эффекты
            self._apply_processing_effects(self_state, processing_event)

            # Добавить в историю
            self._add_to_processing_history(self_state, processing_event)
            self._stats["processing_events_triggered"] += 1

            self.logger.log_event({
                "event_type": "manual_processing_event_triggered",
                "processing_mode": processing_mode.value,
                "intensity": intensity,
            })

            return True

        except Exception as e:
            self.logger.log_event({
                "event_type": "manual_processing_trigger_failed",
                "error": str(e),
                "processing_mode": processing_mode.value,
            })
            return False

    def force_adaptive_state(self, self_state, target_state: AdaptiveState) -> bool:
        """
        Принудительно перевести систему в указанное адаптивное состояние.

        Args:
            self_state: Состояние системы
            target_state: Целевое адаптивное состояние

        Returns:
            True если переход выполнен успешно
        """
        try:
            old_state = getattr(self_state, "current_adaptive_state", AdaptiveState.STANDARD.value)
            self_state.current_adaptive_state = target_state.value

            # Записать переход
            transition = {
                "timestamp": time.time(),
                "from_state": old_state,
                "to_state": target_state.value,
                "trigger": "manual",
            }
            self.state_transitions.append(transition)
            self._stats["state_transitions"] += 1

            self.logger.log_event({
                "event_type": "manual_adaptive_state_change",
                "from_state": old_state,
                "to_state": target_state.value,
            })

            return True

        except Exception as e:
            self.logger.log_event({
                "event_type": "manual_state_change_failed",
                "error": str(e),
                "target_state": target_state.value,
            })
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """
        Получить полный статус адаптивной системы обработки.

        Returns:
            Dict с полным статусом всех компонентов
        """
        status = {
            "manager": {
                "is_active": self._is_active,
                "config": self._config_to_dict(),
                "stats": self._stats.copy(),
                "uptime": time.time() - self._stats["start_time"],
            },
            "components": {
                "memory_hierarchy": self._memory_hierarchy is not None,
            }
        }

        if self._memory_hierarchy:
            status["memory_hierarchy"] = self._memory_hierarchy.get_hierarchy_status()

        return status

    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику режимов обработки.

        Returns:
            Dict со статистикой обработки
        """
        return {
            "total_processing_events": self._stats["processing_events_triggered"],
            "active_processing": getattr(self.self_state_provider(), "processing_state", False) if self.self_state_provider else False,
            "processing_modes_distribution": self._get_processing_modes_distribution(),
            "average_intensity": self._calculate_average_processing_intensity(),
        }

    def _get_processing_modes_distribution(self) -> Dict[str, int]:
        """Получить распределение режимов обработки."""
        distribution = {}
        for event in self.processing_history:
            mode = event.processing_mode.value
            distribution[mode] = distribution.get(mode, 0) + 1
        return distribution

    def _calculate_average_processing_intensity(self) -> float:
        """Вычислить среднюю интенсивность режимов обработки."""
        if not self.processing_history:
            return 0.0

        total_intensity = sum(event.intensity for event in self.processing_history)
        return total_intensity / len(self.processing_history)

    def get_adaptive_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику адаптивных состояний.

        Returns:
            Dict со статистикой состояний
        """
        return {
            "total_state_transitions": self._stats["state_transitions"],
            "current_state": getattr(self.self_state_provider(), "current_adaptive_state", "standard") if self.self_state_provider else "unknown",
            "state_distribution": self._get_state_distribution(),
            "average_processing_efficiency": self._calculate_average_processing_efficiency(),
        }

    def _get_state_distribution(self) -> Dict[str, int]:
        """Получить распределение адаптивных состояний."""
        distribution = {}
        for transition in self.state_transitions:
            to_state = transition.get("to_state", "unknown")
            distribution[to_state] = distribution.get(to_state, 0) + 1
        return distribution

    def _calculate_average_processing_efficiency(self) -> float:
        """Вычислить среднюю эффективность обработки."""
        self_state = self.self_state_provider()
        return getattr(self_state, "processing_efficiency", 0.0) if self_state else 0.0

    def reset_statistics(self) -> None:
        """Сбросить статистику системы."""
        self._stats = {
            "total_updates": 0,
            "processing_events_triggered": 0,
            "state_transitions": 0,
            "memory_integrations": 0,
            "start_time": time.time(),
        }

        self.logger.log_event({"event_type": "adaptive_processing_statistics_reset"})

    def update_configuration(self, new_config: Dict[str, Any]) -> None:
        """
        Обновить конфигурацию системы.

        Args:
            new_config: Новые параметры конфигурации
        """
        # Валидация новых параметров
        for key, value in new_config.items():
            if hasattr(self.config, key):
                if key.endswith('_threshold') or key.endswith('_max'):
                    if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                        raise ValueError(f"{key} must be a number between 0.0 and 1.0")
                setattr(self.config, key, value)

        # Пересоздать компоненты если необходимо
        if "integrate_with_memory" in new_config and new_config["integrate_with_memory"] != self.config.integrate_with_memory:
            if new_config["integrate_with_memory"]:
                self._memory_hierarchy = self._create_memory_hierarchy()
            else:
                self._memory_hierarchy = None

        self.logger.log_event({
            "event_type": "adaptive_processing_config_updated",
            "new_config": new_config,
        })


    def get_legacy_status(self) -> Dict[str, Any]:
        """
        Получить статус в формате старой системы для обратной совместимости.

        Returns:
            Dict со статусом в старом формате
        """
        # Получить текущий статус
        current_status = self.get_system_status()

        # Конвертировать в старый формат
        legacy_status = {
            "clarity_moments": {
                "active": getattr(self.self_state_provider(), 'processing_state', False) if self.self_state_provider else False,
                "duration_remaining": getattr(self.self_state_provider(), 'processing_duration', 0) if self.self_state_provider else 0,
                "total_events": current_status["manager"]["stats"]["processing_events_triggered"],
                "modifier": getattr(self.self_state_provider(), 'processing_modifier', 1.0) if self.self_state_provider else 1.0,
            },
            "consciousness_system": {
                "current_state": getattr(self.self_state_provider(), 'current_adaptive_state', 'standard') if self.self_state_provider else 'standard',
                "consciousness_level": getattr(self.self_state_provider(), 'processing_efficiency', 0.0) if self.self_state_provider else 0.0,
                "total_transitions": current_status["manager"]["stats"]["state_transitions"],
            },
            "unified_system": {
                "clarity_events_total": current_status["manager"]["stats"]["processing_events_triggered"],
                "state_transitions_total": current_status["manager"]["stats"]["state_transitions"],
                "active_clarity_events": len(getattr(self.self_state_provider(), 'processing_history', [])) if self.self_state_provider else 0,
            }
        }

        return legacy_status
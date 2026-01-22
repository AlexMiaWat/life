import copy
import cProfile
import logging
import time
from typing import Dict, Any

from src.action import execute_action
from src.activation.activation import activate_memory
from src.adaptation.adaptation import AdaptationManager
from src.decision.decision import decide_response
from src.environment.internal_generator import InternalEventGenerator

# Экспериментальные компоненты импортируются условно на основе feature flags
# from src.experimental import AdaptiveProcessingManager, AdaptiveProcessingConfig
# from src.experimental.clarity_moments import ClarityMoments
from src.config import feature_flags
from src.feedback import observe_consequences, register_action
from src.intelligence.intelligence import process_information
from src.learning.learning import LearningEngine
from src.meaning.engine import MeaningEngine
from src.memory.memory import MemoryEntry
from src.planning.planning import record_potential_sequences
from src.runtime.life_policy import LifePolicy
from src.runtime.log_manager import FlushPolicy, LogManager
from src.runtime.snapshot_manager import SnapshotManager
from src.runtime.subjective_time import compute_subjective_dt
from src.runtime.data_collection_manager import DataCollectionManager
from src.state.self_state import SelfState, save_snapshot

logger = logging.getLogger(__name__)

# Константы для интервалов вызова компонентов (в тиков)
LEARNING_INTERVAL = 75  # Вызов Learning раз в 75 тиков (между 50-100)
ADAPTATION_INTERVAL = 100  # Вызов Adaptation раз в 100 тиков (реже чем Learning)
ARCHIVE_INTERVAL = 50  # Вызов архивации раз в 50 тиков
DECAY_INTERVAL = 10  # Вызов затухания весов раз в 10 тиков
METRICS_COLLECTION_INTERVAL = 100  # Сбор технических метрик раз в 100 тиков
MEMORY_CONSOLIDATION_INTERVAL = 25  # Консолидация экспериментальной памяти раз в 25 тиков

# Константы для работы с памятью
MEMORY_DECAY_FACTOR = 0.99  # Фактор затухания весов памяти
MEMORY_MIN_WEIGHT = 0.1  # Минимальный вес для архивации
MEMORY_MAX_AGE_SECONDS = 7 * 24 * 3600  # Максимальный возраст записей (7 дней в секундах)
MEMORY_DECAY_MIN_WEIGHT = 0.0  # Минимальный вес при затухании (для полного забывания)

# Константы для обработки ошибок
# Штраф integrity при ошибке в цикле
ERROR_INTEGRITY_PENALTY = 0.05

# Константы для модификации impact
# Коэффициент для уменьшения impact при обработке событий
IMPACT_REDUCTION_COEFFICIENT = 0.5


def _get_default_learning_params() -> dict:
    """
    Получить параметры learning по умолчанию без создания временного объекта SelfState.

    Returns:
        dict: словарь с параметрами learning по умолчанию
    """
    return {
        "event_type_sensitivity": {
            "noise": 0.2,
            "decay": 0.2,
            "recovery": 0.2,
            "shock": 0.2,
            "idle": 0.2,
        },
        "significance_thresholds": {
            "noise": 0.1,
            "decay": 0.1,
            "recovery": 0.1,
            "shock": 0.1,
            "idle": 0.1,
        },
        "response_coefficients": {
            "dampen": 0.5,
            "absorb": 1.0,
            "ignore": 0.0,
        },
    }


def _get_default_adaptation_params() -> dict:
    """
    Получить параметры adaptation по умолчанию без создания временного объекта SelfState.

    Returns:
        dict: словарь с параметрами adaptation по умолчанию
    """
    return {
        "behavior_sensitivity": {
            "noise": 0.2,
            "decay": 0.2,
            "recovery": 0.2,
            "shock": 0.2,
            "idle": 0.2,
        },
        "behavior_thresholds": {
            "noise": 0.1,
            "decay": 0.1,
            "recovery": 0.1,
            "shock": 0.1,
            "idle": 0.1,
        },
        "behavior_coefficients": {
            "dampen": 0.5,
            "absorb": 1.0,
            "ignore": 0.0,
        },
    }


def _validate_learning_params(learning_params: dict) -> bool:
    """
    Валидирует структуру learning_params.

    Returns:
        True если параметры валидны, False иначе
    """
    if not isinstance(learning_params, dict):
        return False

    required_keys = [
        "event_type_sensitivity",
        "significance_thresholds",
        "response_coefficients",
    ]
    for key in required_keys:
        if key not in learning_params:
            return False
        if not isinstance(learning_params[key], dict):
            return False

    return True


def _validate_adaptation_params(adaptation_params: dict) -> bool:
    """
    Валидирует структуру adaptation_params.

    Returns:
        True если параметры валидны, False иначе
    """
    if not isinstance(adaptation_params, dict):
        return False

    # adaptation_params может быть пустым при первой инициализации
    # Проверяем только если есть ключи
    if adaptation_params:
        expected_keys = [
            "behavior_sensitivity",
            "behavior_thresholds",
            "behavior_coefficients",
        ]
        for key in expected_keys:
            if key in adaptation_params and not isinstance(adaptation_params[key], dict):
                return False

    return True


def _safe_copy_dict(d: dict) -> dict:
    """
    Безопасное копирование словаря.
    Использует поверхностное копирование для простых словарей с числами,
    глубокое копирование только при необходимости.
    """
    if not d:
        return {}

    # Проверяем, нужна ли глубокая копия
    # Если все значения - простые типы (числа, строки), используем поверхностное копирование
    needs_deepcopy = False
    for value in d.values():
        if isinstance(value, dict):
            # Рекурсивно проверяем вложенные словари
            for nested_value in value.values():
                if isinstance(nested_value, (dict, list)):
                    needs_deepcopy = True
                    break
            if needs_deepcopy:
                break

    if needs_deepcopy:
        return copy.deepcopy(d)
    else:
        return d.copy()


def _record_adaptation_params_change(self_state, old_params: dict, new_params: dict) -> None:
    """
    Записывает изменения adaptation_params в историю для анализа эволюции.

    Args:
        self_state: Экземпляр SelfState для записи истории
        old_params: Параметры до изменения
        new_params: Параметры после изменения
    """
    # Определяем, какие параметры изменились
    changes = {}
    for key in set(old_params.keys()) | set(new_params.keys()):
        old_value = old_params.get(key)
        new_value = new_params.get(key)
        if old_value != new_value:
            changes[key] = {"old_value": old_value, "new_value": new_value}

    if not changes:
        return  # Нет изменений

    # Создаем запись истории
    history_entry = {
        "timestamp": time.time(),
        "tick": getattr(self_state, "ticks", 0),
        "old_params": old_params.copy(),
        "new_params": new_params.copy(),
        "changes": changes,
        "learning_params_snapshot": getattr(self_state, "learning_params", {}).copy(),
    }

    # Thread-safe добавление в историю
    if not hasattr(self_state, "adaptation_params_history"):
        self_state.adaptation_params_history = []

    self_state.adaptation_params_history.append(history_entry)

    # Ограничиваем размер истории (последние 50 записей)
    if len(self_state.adaptation_params_history) > 50:
        self_state.adaptation_params_history = self_state.adaptation_params_history[-50:]


def run_loop(
    self_state: SelfState,
    monitor,
    tick_interval=1.0,
    snapshot_period=10,
    stop_event=None,
    event_queue=None,
    disable_weakness_penalty=False,
    disable_learning=False,
    disable_adaptation=False,
    disable_adaptive_processing=False,  # Включено по умолчанию для оптимизации обработки
    enable_memory_hierarchy=None,  # Автоматически определяется через feature flags
    enable_silence_detection=True,  # Включение системы осознания тишины
    log_flush_period_ticks=10,
    enable_profiling=False,
    structured_logger=None  # StructuredLogger для активного логирования ключевых этапов
):
    """
    Runtime Loop с интеграцией Environment (этап 07)

    Args:
        self_state: Состояние Life
        monitor: Функция мониторинга
        tick_interval: Интервал между тиками
        snapshot_period: Периодичность snapshot
        stop_event: threading.Event для остановки
        event_queue: Очередь событий из Environment
        disable_weakness_penalty: Отключить штрафы за слабость
        disable_structured_logging: Отключить структурированное логирование
        disable_learning: Отключить модуль Learning
        disable_adaptation: Отключить модуль Adaptation
        # disable_philosophical_analysis: REMOVED - external tool only
        # disable_philosophical_reports: REMOVED - external tool only
        disable_adaptive_processing: Отключить адаптивную систему обработки
        enable_memory_hierarchy: Включить многоуровневую систему памяти (краткосрочная/долгосрочная/архивная)
        enable_silence_detection: Включить систему осознания тишины
        log_flush_period_ticks: Период сброса логов в тиках
        enable_profiling: Включить профилирование runtime loop с cProfile
    """
    # Активный мониторинг: система Life требует активного вмешательства в runtime для observability
    # Это НЕ пассивное наблюдение, а активный мониторинг с интеграцией в каждый тик

    # Проверка корректности feature flags перед инициализацией экспериментальных компонентов
    def _validate_experimental_components_safety():
        """Проверяет, что экспериментальные компоненты корректно изолированы."""
        experimental_flags = [
            'memory_hierarchy_manager',
            'adaptive_processing_manager',
            'clarity_moments',
            'sensory_buffer',
            'parallel_consciousness_engine'
        ]

        enabled_experimental = []
        for flag in experimental_flags:
            if feature_flags.is_enabled(flag):
                enabled_experimental.append(flag)

        if enabled_experimental:
            logger.warning(f"EXPERIMENTAL COMPONENTS ENABLED: {', '.join(enabled_experimental)}")
            logger.warning("Experimental components may impact system stability and performance")
        else:
            logger.info("All experimental components are disabled - system running in stable mode")

        return enabled_experimental

    # Выполняем проверку безопасности экспериментальных компонентов
    enabled_experimental = _validate_experimental_components_safety()

    # Инициализация асинхронной очереди для операций наблюдения
    from src.runtime.async_data_queue import AsyncDataQueue
    async_data_queue = AsyncDataQueue(max_size=10000, flush_interval=1.0)  # Быстрое сброс каждую секунду
    async_data_queue.start()

    # Инициализация PassiveDataSink для пассивного сбора данных
    from src.observability.passive_data_sink import PassiveDataSink
    passive_data_sink = PassiveDataSink(
        data_directory="./data/observations",
        observations_file="passive_observations.jsonl",
        max_entries=50000,  # Увеличенный буфер для пассивного сбора
        enabled=True,
        auto_flush=True
    )

    # Инициализация AsyncDataSink для асинхронной обработки данных
    from src.observability.async_data_sink import AsyncDataSink
    async_data_sink = AsyncDataSink(
        data_directory="./data/observations",
        observations_file="async_observations.jsonl",
        enabled=True,
        buffer_size=5000,
        max_queue_size=10000,
        flush_interval=0.5  # Более частый сброс для асинхронной обработки
    )

    # Инициализация structured logger с AsyncLogWriter для <1% overhead
    # Оптимизация производительности: логируем каждый 10-й тик, отключаем детальное логирование
    from src.observability.structured_logger import StructuredLogger
    if not isinstance(structured_logger, StructuredLogger):
        structured_logger = StructuredLogger(
            log_tick_interval=10,  # Логировать каждый 10-й тик
            enable_detailed_logging=False,  # Отключить детальное логирование для производительности
            buffer_size=10000,  # Буфер на 10000 записей в памяти
            batch_size=50,  # Batch-запись по 50 записей
            flush_interval=0.1,  # Сброс каждые 100ms
            passive_data_sink=passive_data_sink,  # Передача компонентов для интеграции
            async_data_sink=async_data_sink
        )

    # Запуск AsyncDataSink
    import asyncio
    asyncio.run(async_data_sink.start())

    # Инициализация компонентов наблюдения
    from src.observability.runtime_analysis_engine import ActiveRuntimeAnalysisEngine

    # Функция обработки результатов анализа для real-time алертов
    def handle_analysis_results(analysis_type: str, result_data: Dict[str, Any]) -> None:
        """Обработчик результатов анализа для генерации алертов."""
        if analysis_type == "performance":
            avg_duration = result_data.get('avg_tick_duration', 0)
            slow_ticks = result_data.get('slow_ticks_100ms', 0)

            if avg_duration > 0.100:  # > 100ms в среднем
                logger.warning(f"PERFORMANCE ALERT: Average tick duration {avg_duration:.3f}s exceeds 100ms threshold")
                # Можно добавить адаптивные действия здесь

            if slow_ticks > 5:
                logger.warning(f"PERFORMANCE ALERT: {slow_ticks} ticks exceed 100ms")

        elif analysis_type == "errors":
            total_errors = result_data.get('total_errors', 0)
            error_trend = result_data.get('error_trend', 0)

            if total_errors > 10:
                logger.error(f"ERROR ALERT: {total_errors} errors detected in recent logs")

            if error_trend > 1:
                logger.warning(f"ERROR TREND ALERT: Error rate is increasing (trend: {error_trend:.2f})")

    # Инициализация активного движка анализа (без фоновых потоков)
    analysis_engine = ActiveRuntimeAnalysisEngine(
        log_path="data/structured_log.jsonl",
        structured_logger=structured_logger,
        analysis_interval=30.0  # Минимальный интервал между анализами
    )

    # Добавляем callback для алертов
    analysis_engine.add_result_callback(handle_analysis_results)

    engine = MeaningEngine()
    learning_engine = LearningEngine()  # Learning Engine (Этап 14)
    adaptation_manager = AdaptationManager()  # Adaptation Manager (Этап 15)
    # Инициализация адаптивной системы обработки
    # Проверяем feature flag, если adaptive processing не отключен явно
    enable_adaptive_processing = not disable_adaptive_processing and feature_flags.is_adaptive_processing_enabled()
    adaptive_processing_manager = None
    if enable_adaptive_processing:
        try:
            logger.info("Initializing AdaptiveProcessingManager (experimental component)")
            from src.experimental import AdaptiveProcessingManager, AdaptiveProcessingConfig
            adaptive_processing_manager = AdaptiveProcessingManager(
                self_state_provider=lambda: self_state,
                config=AdaptiveProcessingConfig(),
                logger=structured_logger
            )
            logger.info("AdaptiveProcessingManager initialized successfully")
        except ImportError as e:
            logger.warning(f"AdaptiveProcessingManager not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize AdaptiveProcessingManager: {e}")
            adaptive_processing_manager = None  # Гарантируем None при ошибке
    else:
        logger.info("AdaptiveProcessingManager disabled by feature flag")

    # Инициализация Clarity Moments с реальным состоянием системы (если включено)
    clarity_moments = None
    if feature_flags.is_enabled('clarity_moments'):
        try:
            logger.info("Initializing ClarityMoments (experimental component)")
            from src.experimental.clarity_moments import ClarityMoments
            clarity_moments = ClarityMoments(
                logger=structured_logger,
                self_state_provider=lambda: self_state
            )
            logger.info("ClarityMoments initialized successfully")
        except ImportError as e:
            logger.warning(f"ClarityMoments not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize ClarityMoments: {e}")
            clarity_moments = None  # Гарантируем None при ошибке
    else:
        logger.info("ClarityMoments disabled by feature flag")

    internal_generator = InternalEventGenerator()  # Internal Event Generator (Memory Echoes)
    # Настройка доступа к памяти для генерации конкретных эхо-воспоминаний
    if hasattr(self_state, 'memory'):
        internal_generator.set_memory(self_state.memory)
    pending_actions = []  # Список ожидающих Feedback действий

    # Экспериментальные компоненты (опционально)
    memory_hierarchy = None

    # Определяем через feature flags, если не указано явно
    if enable_memory_hierarchy is None:
        enable_memory_hierarchy = feature_flags.is_memory_hierarchy_enabled()

    if enable_memory_hierarchy:
        try:
            logger.info("Initializing MemoryHierarchyManager (experimental component)")
            from src.experimental.memory_hierarchy import MemoryHierarchyManager

            memory_hierarchy = MemoryHierarchyManager(logger=structured_logger)
            # Подключение эпизодической памяти к иерархии
            memory_hierarchy.set_episodic_memory(self_state.memory)
            logger.info("MemoryHierarchyManager initialized successfully")
        except ImportError as e:
            logger.warning(f"MemoryHierarchyManager not available: {e}")
            memory_hierarchy = None
        except Exception as e:
            logger.error(f"Failed to initialize MemoryHierarchyManager: {e}")
            memory_hierarchy = None  # Гарантируем None при ошибке
    else:
        logger.info("MemoryHierarchyManager disabled by feature flag")


    # Менеджеры для управления снапшотами, логами и политикой
    snapshot_manager = SnapshotManager(period_ticks=snapshot_period, saver=save_snapshot)
    flush_policy = FlushPolicy(
        flush_period_ticks=log_flush_period_ticks,
        flush_before_snapshot=True,
        flush_on_exception=True,
        flush_on_shutdown=True,
    )
    log_manager = LogManager(
        flush_policy=flush_policy,
        flush_fn=self_state._flush_log_buffer,
    )
    life_policy = (
        LifePolicy()
    )  # Использует значения по умолчанию (совпадают с предыдущими константами)
    data_collection_manager = DataCollectionManager()  # Менеджер сбора данных
    data_collection_manager.start()  # Запускаем менеджер сбора данных

    # Счетчики ошибок для отслеживания проблем
    learning_errors = 0
    adaptation_errors = 0
    # philosophical_errors = 0  # REMOVED: no longer needed
    max_errors_before_warning = 10  # Порог для предупреждения о частых ошибках

    # Счетчики для внутренних событий
    ticks_since_last_memory_echo = 0
    ticks_since_last_metrics_collection = 0
    last_report_time = time.time()  # Время последнего автоматического отчета
    report_interval = 6 * 3600  # Генерировать отчет каждые 6 часов

    def run_main_loop():
        """Основной цикл runtime loop - выделен для профилирования"""
        nonlocal learning_errors, adaptation_errors, ticks_since_last_memory_echo, ticks_since_last_metrics_collection
        last_time = time.time()  # Инициализация last_time в начале цикла
        while stop_event is None or not stop_event.is_set():
            try:
                tick_start_time = time.time()
                current_time = tick_start_time
                dt = current_time - last_time
                last_time = current_time

                # Log tick start
                queue_size = event_queue.size() if event_queue else 0
                structured_logger.log_tick_start(self_state.ticks, queue_size)

                # Passive data collection: tick start
                passive_data_sink.receive_data(
                    event_type="tick_start",
                    data={"tick": self_state.ticks, "queue_size": queue_size, "timestamp": current_time},
                    source="runtime_loop",
                    metadata={"subjective_time": self_state.subjective_time}
                )

                # Async data collection: tick metrics
                async_data_sink.log_event(
                    data={"tick": self_state.ticks, "queue_size": queue_size, "dt": dt},
                    event_type="tick_metrics",
                    source="runtime_loop",
                    metadata={"performance": True}
                )

                # Обновление состояния
                self_state.apply_delta({"ticks": 1})
                self_state.apply_delta({"age": dt})
                # Subjective time increment (metric only) - enabled
                # Применяем модификатор Clarity Moments (замедление времени в моменты ясности)
                clarity_modifier = getattr(self_state, 'clarity_modifier', 1.0)
                adjusted_dt = dt * clarity_modifier

                subjective_dt = compute_subjective_dt(
                    dt=adjusted_dt,
                    base_rate=self_state.subjective_time_base_rate,
                    intensity=self_state.last_event_intensity,
                    stability=self_state.stability,
                    energy=self_state.energy,
                    intensity_coeff=self_state.subjective_time_intensity_coeff,
                    stability_coeff=abs(self_state.subjective_time_stability_coeff),  # Положительный для ускорения при высокой стабильности
                    energy_coeff=self_state.subjective_time_energy_coeff,
                    rate_min=self_state.subjective_time_rate_min,
                    rate_max=self_state.subjective_time_rate_max,
                    circadian_phase=getattr(self_state, 'circadian_phase', 0.0),
                    recovery_efficiency=getattr(self_state, 'recovery_efficiency', 1.0),
                )
                self_state.apply_delta({"subjective_time": subjective_dt})

                # Обновление внутренних ритмов
                self_state.update_circadian_rhythm(dt)

                # Проверка условий Clarity Moments (если компонент включен)
                if clarity_moments and self_state.stability >= clarity_moments.CLARITY_STABILITY_THRESHOLD and \
                   self_state.energy >= clarity_moments.CLARITY_ENERGY_THRESHOLD * 100:  # energy в процентах
                    # Проверяем условия для активации момента ясности
                    clarity_result = clarity_moments.check_clarity_conditions(self_state)
                    if clarity_result:
                        # Активируем момент ясности
                        clarity_moments.activate_clarity_moment(self_state)
                        # Анализируем момент ясности для создания события
                        moment = clarity_moments.analyze_clarity(self_state)

                        # Интегрируем момент ясности с управлением памятью
                        if memory_hierarchy and moment:
                            # Определяем тип ясности на основе стадии
                            clarity_type = _map_clarity_stage_to_type(moment.stage)
                            memory_hierarchy.handle_clarity_moment(
                                clarity_type, moment.intensity, self_state
                            )
                        if moment:
                            # Создаем событие момента ясности
                            clarity_event = {
                                "type": "clarity_moment",
                                "timestamp": time.time(),
                                "subjective_timestamp": self_state.subjective_time,
                                "data": {
                                    "intensity": moment.intensity,
                                    "stage": moment.stage,
                                    "correlation_id": moment.correlation_id,
                                    "reason": "high_stability_energy"
                                }
                            }
                            # Добавляем в очередь событий
                            event_queue.put_nowait(clarity_event)

                            # Записываем в историю моментов ясности
                            clarity_record = {
                                "timestamp": time.time(),
                                "subjective_timestamp": self_state.subjective_time,
                                "intensity": moment.intensity,
                                "stage": moment.stage,
                                "correlation_id": moment.correlation_id,
                                "consciousness_level": self_state.consciousness_level,
                                "stability": self_state.stability,
                                "energy": self_state.energy
                            }
                            self_state.clarity_history.append(clarity_record)

                            # Ограничиваем историю последними 100 записями
                            if len(self_state.clarity_history) > 100:
                                self_state.clarity_history = self_state.clarity_history[-100:]

                # Обновление состояния Clarity Moments (если компонент включен)
                if clarity_moments:
                    clarity_moments.update_clarity_state(self_state)

                # Технический мониторинг: сбор метрик через регулярные интервалы (асинхронно)
                ticks_since_last_metrics_collection += 1
                if ticks_since_last_metrics_collection >= METRICS_COLLECTION_INTERVAL:
                    try:
                        # Создаем mock decision engine с историей решений из self_state
                        class MockDecisionEngine:
                            def get_recent_decisions(self, limit=100):
                                # Извлекаем недавние решения из памяти или действий
                                decisions = []
                                # Ищем записи о решениях в памяти
                                for entry in reversed(self_state.memory):
                                    if hasattr(entry, "event_type") and entry.event_type in [
                                        "decision",
                                        "action",
                                    ]:
                                        decision_data = {
                                            "timestamp": getattr(entry, "timestamp", time.time()),
                                            "type": getattr(entry, "event_type", "unknown"),
                                            "data": (
                                                getattr(entry, "data", {})
                                                if hasattr(entry, "data")
                                                else {}
                                            ),
                                        }
                                        decisions.append(decision_data)
                                        if len(decisions) >= limit:
                                            break
                                return decisions

                            def get_statistics(self):
                                return {
                                    "total_decisions": len(
                                        [
                                            e
                                            for e in self_state.memory
                                            if hasattr(e, "event_type")
                                            and e.event_type in ["decision", "action"]
                                        ]
                                    ),
                                    "average_time": 0.01,  # Заглушка
                                    "accuracy": 0.8,  # Заглушка
                                }

                        mock_decision_engine = MockDecisionEngine()

                        # Ставим операцию сбора метрик в асинхронную очередь
                        success = data_collection_manager.collect_technical_metrics(
                            self_state=self_state,
                            memory=self_state.memory,
                            learning_engine=learning_engine,
                            adaptation_manager=adaptation_manager,
                            decision_engine=mock_decision_engine,
                            base_dir="metrics",
                            filename_prefix="technical_report"
                        )

                        if success:
                            logger.debug("Technical metrics collection queued for async processing")
                        else:
                            logger.warning("Failed to queue technical metrics collection")

                        # Запускаем анализ логов для получения рекомендаций (активный анализ по запросу)
                        try:
                            analysis_engine.perform_analysis()
                            logger.debug("Active runtime analysis completed")
                        except Exception as e:
                            logger.warning(f"Failed to run active runtime analysis: {e}")

                    except Exception as e:
                        logger.warning(f"Failed to queue technical metrics collection: {e}")
                    finally:
                        ticks_since_last_metrics_collection = 0

                # Async passive observation: данные собираются в фоне без влияния на runtime

                # Адаптивная система обработки
                if adaptive_processing_manager:
                    try:
                        # Запускаем менеджер если он еще не запущен
                        if not getattr(adaptive_processing_manager, '_is_active', False):
                            adaptive_processing_manager.start()

                        # Обновляем состояние адаптивной обработки
                        processing_results = adaptive_processing_manager.update(self_state)

                        # Создаем события для значимых режимов обработки
                        if processing_results.get("processing_events"):
                            from src.environment.event import Event
                            for event_data in processing_results["processing_events"]:
                                if event_data["intensity"] > 0.5:  # Только значимые события
                                    event_obj = Event(
                                        type="processing_mode_activated",
                                        intensity=event_data["intensity"],
                                        timestamp=time.time(),
                                        metadata={
                                            "processing_mode": event_data["mode"],
                                            "duration": event_data["duration"],
                                        }
                                    )
                                    if event_queue:
                                        event_queue.push(event_obj)

                        # Логируем переходы состояний
                        if processing_results.get("state_transitions"):
                            for transition in processing_results["state_transitions"]:
                                logger.info(
                                    f"Adaptive state transition: {transition.get('from_state', 'unknown')} -> {transition.get('to_state', 'unknown')}",
                                    extra={"transition": transition}
                                )

                    except Exception as e:
                        logger.warning(f"Adaptive processing update failed: {e}")
                        # Продолжаем работу даже при ошибке в экспериментальном компоненте

                # Наблюдаем последствия прошлых действий (Feedback)
                feedback_records = observe_consequences(self_state, pending_actions, event_queue)

                # Log feedback records
                for feedback in feedback_records:
                    # Try to find correlation ID from action (if available)
                    correlation_id = getattr(feedback, "correlation_id", None) or "feedback_chain"
                    structured_logger.log_feedback(feedback, correlation_id)

                # Сохраняем Feedback в Memory
                for feedback in feedback_records:
                    feedback_entry = MemoryEntry(
                        event_type="feedback",
                        meaning_significance=0.0,  # Feedback не имеет значимости
                        timestamp=feedback.timestamp,
                        subjective_timestamp=self_state.subjective_time,
                        feedback_data={
                            "action_id": feedback.action_id,
                            "action_pattern": feedback.action_pattern,
                            "state_delta": feedback.state_delta,
                            "delay_ticks": feedback.delay_ticks,
                            "associated_events": feedback.associated_events,
                        },
                    )
                    self_state.memory.append(feedback_entry)

                # === ШАГ 1: Получить события из среды ===
                if event_queue and not event_queue.is_empty():
                    logger.debug(f"[LOOP] Queue not empty, size={event_queue.size()}")
                    events = event_queue.pop_all()
                    logger.debug(f"[LOOP] POPPED {len(events)} events")

                    # Хук: Добавить события в сенсорный буфер (экспериментальная память)
                    if memory_hierarchy and events:
                        for event in events:
                            memory_hierarchy.add_sensory_event(event)

                    # Log events
                    correlation_ids = []
                    for event in events:
                        correlation_id = structured_logger.log_event(event)
                        correlation_ids.append(correlation_id)

                        # Passive data collection: external events
                        passive_data_sink.receive_data(
                            event_type="external_event",
                            data={"event": event.to_dict() if hasattr(event, 'to_dict') else str(event)},
                            source="runtime_loop",
                            metadata={"correlation_id": correlation_id, "tick": self_state.ticks}
                        )

                        # Async data collection: event processing
                        async_data_sink.log_event(
                            data={"event_type": getattr(event, 'event_type', 'unknown'), "correlation_id": correlation_id},
                            event_type="event_processed",
                            source="runtime_loop",
                            metadata={"external": True}
                        )
                    # Update intensity signal for this tick using exponential smoothing
                    try:
                        current_max_intensity = max([float(e.intensity) for e in events] + [0.0])
                        # Exponential smoothing: new_value = alpha * current + (1-alpha) * previous
                        alpha = self_state.subjective_time_intensity_smoothing
                        self_state.last_event_intensity = (
                            alpha * current_max_intensity
                            + (1 - alpha) * self_state.last_event_intensity
                        )
                    except Exception:
                        self_state.last_event_intensity = 0.0

                    # === ШАГ 2: Интерпретировать события ===
                    event_index = 0
                    for event in events:
                        correlation_id = (
                            correlation_ids[event_index]
                            if event_index < len(correlation_ids)
                            else None
                        )
                        logger.debug(
                            f"[LOOP] Interpreting event: type={event.type}, intensity={event.intensity}"
                        )
                        meaning = engine.process(
                            event,
                            self_state.get_safe_status_dict(include_optional=False),
                        )

                        # Log meaning
                        if correlation_id:
                            structured_logger.log_meaning(event, meaning, correlation_id)

                        if meaning.significance > 0:
                            # Активация памяти для события с учетом субъективного времени
                            activated = activate_memory(
                                event.type, self_state.memory, self_state=self_state
                            )
                            self_state.activated_memory = activated
                            logger.debug(
                                f"[LOOP] Activated {len(activated)} memories for type '{event.type}'"
                            )

                            # Decision
                            pattern = decide_response(self_state, meaning)
                            self_state.last_pattern = pattern

                            # Log decision
                            if correlation_id:
                                structured_logger.log_decision(correlation_id)

                            if pattern == "ignore":
                                continue  # skip apply_delta
                            elif pattern == "dampen":
                                meaning.impact = {
                                    k: v * IMPACT_REDUCTION_COEFFICIENT
                                    for k, v in meaning.impact.items()
                                }
                            # else "absorb" — no change

                            # Применяем модификаторы ритмов к recovery событиям
                            if event.type == "recovery" and meaning.impact:
                                # Применяем эффективность восстановления от циркадного ритма
                                recovery_impact = meaning.impact.copy()
                                for key in recovery_impact:
                                    if key in ["energy"]:  # Восстановление влияет на энергию
                                        recovery_impact[key] *= self_state.recovery_efficiency
                                meaning.impact = recovery_impact

                            # КРИТИЧНО: Сохраняем снимок состояния ДО действия
                            state_before = {
                                "energy": self_state.energy,
                                "stability": self_state.stability,
                                "integrity": self_state.integrity,
                            }

                            self_state.apply_delta(meaning.impact)
                            execute_action(pattern, self_state)

                            # Log action
                            if correlation_id:
                                action_id = (
                                    f"action_{self_state.ticks}_{pattern}_{int(time.time()*1000)}"
                                )
                                structured_logger.log_action(action_id, correlation_id)

                            # Регистрируем для Feedback (после выполнения)
                            # Action не знает о Feedback - регистрация происходит в Loop
                            action_id = (
                                f"action_{self_state.ticks}_{pattern}_{int(time.time()*1000)}"
                            )
                            action_timestamp = time.time()
                            register_action(
                                action_id,
                                pattern,
                                state_before,
                                action_timestamp,
                                pending_actions,
                            )
                            self_state.recent_events.append(event.type)
                            self_state.last_significance = meaning.significance
                            self_state.memory.append(
                                MemoryEntry(
                                    event_type=event.type,
                                    meaning_significance=meaning.significance,
                                    timestamp=time.time(),
                                    subjective_timestamp=self_state.subjective_time,
                                )
                            )


                            # Хук: Обновление экспериментальных метрик SelfState
                            if memory_hierarchy:
                                # Обновление размера сенсорного буфера
                                self_state.sensory_buffer_size = (
                                    memory_hierarchy.sensory_buffer.buffer_size
                                )
                                # Обновление количества концепций
                                self_state.semantic_concepts_count = (
                                    len(memory_hierarchy.semantic_store._concepts)
                                    if memory_hierarchy.semantic_store
                                    else 0
                                )
                                # Обновление количества паттернов
                                self_state.procedural_patterns_count = (
                                    len(memory_hierarchy.procedural_store._patterns)
                                    if memory_hierarchy.procedural_store
                                    else 0
                                )

                                # Обновление уровня сознания (базовое значение на основе стабильности и энергии)
                                self_state.consciousness_level = min(1.0, (self_state.stability + self_state.energy / 100.0) / 2.0)


                        logger.debug(
                            f"[LOOP] After interpret: energy={self_state.energy:.2f}, stability={self_state.stability:.4f}"
                        )
                        event_index += 1

                    record_potential_sequences(self_state)
                    process_information(self_state)

                # === ШАГ 1.5: Генерация внутренних событий (Memory Echoes) ===
                # Генерируем спонтанные внутренние события после обработки внешних
                memory_stats = (
                    self_state.memory.get_statistics()
                    if hasattr(self_state.memory, "get_statistics")
                    else None
                )
                memory_pressure = (
                    len(self_state.memory) / 50.0 if len(self_state.memory) > 0 else 0.0
                )

                # Проверяем необходимость генерации memory echo
                if internal_generator.should_generate_echo(
                    ticks_since_last_memory_echo, memory_pressure, self_state
                ):
                    internal_event = internal_generator.generate_memory_echo(self_state, memory_stats)
                    if internal_event:
                        logger.debug(f"[LOOP] Generated internal event: {internal_event.type}")
                        # Добавляем внутреннее событие в очередь для обработки на следующем тике
                        if event_queue:
                            event_queue.push(internal_event)
                            ticks_since_last_memory_echo = 0
                            # Логируем внутреннее событие
                            correlation_id = structured_logger.log_event(internal_event)

                            # Passive data collection: internal events
                            passive_data_sink.receive_data(
                                event_type="internal_event",
                                data={"event": internal_event.to_dict() if hasattr(internal_event, 'to_dict') else str(internal_event)},
                                source="runtime_loop",
                                metadata={"correlation_id": correlation_id, "tick": self_state.ticks}
                            )

                            # Async data collection: internal event generation
                            async_data_sink.log_event(
                                data={"event_type": getattr(internal_event, 'event_type', 'unknown'), "correlation_id": correlation_id},
                                event_type="internal_event_generated",
                                source="runtime_loop",
                                metadata={"internal": True}
                            )
                        else:
                            logger.warning("[LOOP] No event queue available for internal event")
                    else:
                        logger.debug("[LOOP] Internal event generator returned None")
                else:
                    ticks_since_last_memory_echo += 1
                    # No events this tick -> gradually decay intensity signal using smoothing
                    alpha = self_state.subjective_time_intensity_smoothing
                    self_state.last_event_intensity = (1 - alpha) * self_state.last_event_intensity

                # Learning (Этап 14) - медленное изменение внутренних параметров
                # Вызывается раз в LEARNING_INTERVAL тиков, после Feedback, перед Planning/Intelligence
                if (
                    not disable_learning
                    and self_state.ticks > 0
                    and self_state.ticks % LEARNING_INTERVAL == 0
                ):
                    try:
                        # Проверяем инициализацию параметров
                        if (
                            not hasattr(self_state, "learning_params")
                            or not self_state.learning_params
                        ):
                            # Автоматическая инициализация при первом запуске
                            logger.info(
                                "learning_params не инициализирован, инициализируем значениями по умолчанию"
                            )
                            # Используем метод из SelfState для получения значений по умолчанию
                            if hasattr(self_state, "_get_default_learning_params"):
                                self_state.learning_params = (
                                    self_state._get_default_learning_params()
                                )
                            else:
                                # Fallback: используем вспомогательную функцию без создания временного объекта
                                self_state.learning_params = _get_default_learning_params()

                        # Валидируем структуру параметров
                        if not _validate_learning_params(self_state.learning_params):
                            logger.error(
                                "learning_params имеет некорректную структуру, исправляем значениями по умолчанию"
                            )
                            # Исправляем некорректную структуру значениями по умолчанию
                            if hasattr(self_state, "_get_default_learning_params"):
                                self_state.learning_params = (
                                    self_state._get_default_learning_params()
                                )
                            else:
                                # Fallback: используем вспомогательную функцию без создания временного объекта
                                self_state.learning_params = _get_default_learning_params()

                        # Обрабатываем статистику из Memory
                        statistics = learning_engine.process_statistics(self_state.memory)

                        # Получаем текущие параметры
                        current_params = self_state.learning_params

                        # Медленно изменяем параметры (без оптимизации, без целей)
                        new_params = learning_engine.adjust_parameters(statistics, current_params)

                        # Фиксируем изменения в SelfState (пустой словарь означает отсутствие изменений)
                        if new_params:
                            learning_engine.record_changes(current_params, new_params, self_state)
                    except (TypeError, ValueError) as e:
                        learning_errors += 1
                        logger.error(
                            f"Критическая ошибка в Learning (параметры): {e}",
                            exc_info=True,
                        )
                        # При критичных ошибках валидации пропускаем только блок Learning,
                        # но продолжаем выполнение остальных частей итерации
                        if learning_errors >= max_errors_before_warning:
                            logger.warning(
                                f"Обнаружено {learning_errors} ошибок в Learning. "
                                "Возможна деградация функциональности."
                            )
                    except Exception as e:
                        learning_errors += 1
                        logger.error(f"Неожиданная ошибка в Learning: {e}", exc_info=True)
                        # При неожиданных ошибках пропускаем только блок Learning,
                        # но продолжаем выполнение остальных частей итерации
                        if learning_errors >= max_errors_before_warning:
                            logger.warning(
                                f"Обнаружено {learning_errors} ошибок в Learning. "
                                "Возможна деградация функциональности."
                            )

                # Затухание весов памяти (Memory v2.0) - механизм забывания
                # Вызывается раз в DECAY_INTERVAL тиков
                if self_state.ticks > 0 and self_state.ticks % DECAY_INTERVAL == 0:
                    try:
                        self_state.memory.decay_weights(
                            decay_factor=MEMORY_DECAY_FACTOR,
                            min_weight=MEMORY_DECAY_MIN_WEIGHT,
                        )
                    except Exception as e:
                        logger.error(f"Ошибка в decay_weights: {e}", exc_info=True)

                # Архивация старых записей памяти (Memory v2.0)
                # Вызывается раз в ARCHIVE_INTERVAL тиков
                if self_state.ticks > 0 and self_state.ticks % ARCHIVE_INTERVAL == 0:
                    try:
                        # Архивируем записи старше MEMORY_MAX_AGE_SECONDS или с весом < MEMORY_MIN_WEIGHT
                        archived_count = self_state.memory.archive_old_entries(
                            max_age=MEMORY_MAX_AGE_SECONDS, min_weight=MEMORY_MIN_WEIGHT
                        )
                        if archived_count > 0:
                            logger.info(f"[LOOP] Заархивировано {archived_count} записей памяти")
                    except Exception as e:
                        logger.error(f"Ошибка в archive_old_entries: {e}", exc_info=True)

                # Консолидация экспериментальной памяти
                # Вызывается раз в MEMORY_CONSOLIDATION_INTERVAL тиков
                if (
                    memory_hierarchy
                    and self_state.ticks > 0
                    and self_state.ticks % MEMORY_CONSOLIDATION_INTERVAL == 0
                ):
                    try:
                        consolidation_stats = memory_hierarchy.consolidate_memory(self_state)
                        if (
                            consolidation_stats["sensory_to_episodic_transfers"] > 0
                            or consolidation_stats["episodic_to_semantic_transfers"] > 0
                        ):
                            logger.info(
                                f"[LOOP] Консолидация памяти: sensory→episodic={consolidation_stats['sensory_to_episodic_transfers']}, "
                                f"episodic→semantic={consolidation_stats['episodic_to_semantic_transfers']}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Ошибка в консолидации экспериментальной памяти: {e}", exc_info=True
                        )

                # Adaptation (Этап 15) - медленная перестройка поведения на основе статистики Learning
                # Вызывается раз в ADAPTATION_INTERVAL тиков, после Learning, перед Planning/Intelligence
                if (
                    not disable_adaptation
                    and self_state.ticks > 0
                    and self_state.ticks % ADAPTATION_INTERVAL == 0
                ):
                    try:
                        # Проверяем инициализацию параметров
                        if (
                            not hasattr(self_state, "learning_params")
                            or not self_state.learning_params
                        ):
                            # Автоматическая инициализация при первом запуске
                            logger.info(
                                "learning_params не инициализирован, инициализируем значениями по умолчанию"
                            )
                            if hasattr(self_state, "_get_default_learning_params"):
                                self_state.learning_params = (
                                    self_state._get_default_learning_params()
                                )
                            else:
                                # Используем вспомогательную функцию без создания временного объекта
                                self_state.learning_params = _get_default_learning_params()

                        if (
                            not hasattr(self_state, "adaptation_params")
                            or not self_state.adaptation_params
                        ):
                            # Автоматическая инициализация при первом запуске
                            logger.info(
                                "adaptation_params не инициализирован, инициализируем значениями по умолчанию"
                            )
                            if hasattr(self_state, "_get_default_adaptation_params"):
                                self_state.adaptation_params = (
                                    self_state._get_default_adaptation_params()
                                )
                            else:
                                # Fallback: используем вспомогательную функцию без создания временного объекта
                                self_state.adaptation_params = _get_default_adaptation_params()

                        # Валидируем структуру параметров
                        if not _validate_learning_params(self_state.learning_params):
                            logger.error(
                                "learning_params имеет некорректную структуру, исправляем значениями по умолчанию"
                            )
                            if hasattr(self_state, "_get_default_learning_params"):
                                self_state.learning_params = (
                                    self_state._get_default_learning_params()
                                )
                            else:
                                # Используем вспомогательную функцию без создания временного объекта
                                self_state.learning_params = _get_default_learning_params()

                        if not _validate_adaptation_params(self_state.adaptation_params):
                            logger.error(
                                "adaptation_params имеет некорректную структуру, исправляем значениями по умолчанию"
                            )
                            if hasattr(self_state, "_get_default_adaptation_params"):
                                self_state.adaptation_params = (
                                    self_state._get_default_adaptation_params()
                                )
                            else:
                                # Fallback: используем вспомогательную функцию без создания временного объекта
                                self_state.adaptation_params = _get_default_adaptation_params()

                        # Анализируем изменения от Learning
                        analysis = adaptation_manager.analyze_changes(
                            self_state.learning_params,
                            self_state.adaptation_history,
                        )

                        # Получаем текущие параметры поведения (безопасная копия для истории)
                        # Используем оптимизированное копирование вместо глубокого
                        old_behavior_params = _safe_copy_dict(self_state.adaptation_params)

                        # Применяем адаптацию (медленная перестройка поведения)
                        new_behavior_params = adaptation_manager.apply_adaptation(
                            analysis, old_behavior_params, self_state
                        )

                        # Интеграция результатов анализа в адаптацию
                        analysis_recommendations = analysis_engine.get_recommendations()
                        if analysis_recommendations['performance'] or analysis_recommendations['errors']:
                            logger.info(f"Analysis recommendations available: perf={len(analysis_recommendations['performance'])}, errors={len(analysis_recommendations['errors'])}")

                            # На основе анализа производительности корректируем параметры
                            perf_result = analysis_engine.get_current_analysis('performance')
                            if perf_result and perf_result.is_recent():
                                perf_data = perf_result.data
                                if perf_data.get('trend_direction') == 'degrading':
                                    # Если производительность ухудшается, уменьшаем сложность обработки
                                    logger.info("Performance degrading detected, adjusting processing parameters")
                                    if 'adaptive_processing' not in new_behavior_params:
                                        new_behavior_params['adaptive_processing'] = {}
                                    new_behavior_params['adaptive_processing']['complexity_reduction'] = 0.8

                        # Сохраняем историю и обновляем параметры
                        if new_behavior_params:
                            # Оптимизированное объединение параметров в SelfState
                            # Гарантируем, что все существующие параметры сохраняются
                            for key, new_value_dict in new_behavior_params.items():
                                if key not in self_state.adaptation_params:
                                    # Новый параметр - копируем безопасно
                                    self_state.adaptation_params[key] = _safe_copy_dict(
                                        new_value_dict
                                    )
                                else:
                                    # Существующий параметр - объединение
                                    current_value_dict = self_state.adaptation_params[key]
                                    if isinstance(new_value_dict, dict) and isinstance(
                                        current_value_dict, dict
                                    ):
                                        # Обновляем только измененные параметры, сохраняя остальные
                                        for (
                                            param_name,
                                            new_value,
                                        ) in new_value_dict.items():
                                            current_value_dict[param_name] = new_value
                                        # Не перезаписываем весь словарь, чтобы сохранить ключи,
                                        # которые не были в new_value_dict

                            # Сохраняем историю адаптаций с актуальными старыми параметрами
                            adaptation_manager.store_history(
                                old_behavior_params,
                                new_behavior_params,
                                self_state,
                            )

                            # Записываем изменения в adaptation_params_history для анализа эволюции
                            _record_adaptation_params_change(
                                self_state, old_behavior_params, new_behavior_params
                            )
                    except (TypeError, ValueError) as e:
                        logger.error(
                            f"Критическая ошибка в Adaptation (параметры): {e}",
                            exc_info=True,
                        )
                        # При критичных ошибках валидации пропускаем только блок Adaptation,
                        # но продолжаем выполнение остальных частей итерации
                        pass
                    except Exception as e:
                        logger.error(f"Неожиданная ошибка в Adaptation: {e}", exc_info=True)
                        # При неожиданных ошибках пропускаем только блок Adaptation,
                        # но продолжаем выполнение остальных частей итерации
                        pass

                # Philosophical Analysis REMOVED: violates architecture principles
                # Философский анализ теперь является внешним инструментом наблюдения

                # Philosophical Reports REMOVED: external tool only

                # Логика слабости: когда параметры низкие, добавляем штрафы за немощность
                if not disable_weakness_penalty and life_policy.is_weak(self_state):
                    penalty_deltas = life_policy.weakness_penalty(dt)
                    self_state.apply_delta(penalty_deltas)
                    penalty = abs(penalty_deltas["energy"])
                    logger.debug(
                        f"[LOOP] Слабость: штрафы penalty={penalty:.4f}, energy={self_state.energy:.2f}"
                    )

                # Вызов мониторинга
                try:
                    monitor(self_state)
                except Exception as e:
                    logger.error(f"Ошибка в monitor: {e}", exc_info=True)

                # Периодическое обслуживание DataCollectionManager теперь выполняется асинхронно
                # в фоновом потоке AsyncDataQueue


                # Flush логов перед снапшотом (если политика требует)
                log_manager.maybe_flush(self_state, phase="before_snapshot")

                # Snapshot через SnapshotManager
                snapshot_was_made = snapshot_manager.maybe_snapshot(self_state)

                # Flush логов после снапшота (если политика требует)
                if snapshot_was_made:
                    log_manager.maybe_flush(self_state, phase="after_snapshot")

                # Flush логов по периодичности (редко, не на каждом тике)
                # Примечание: flush после снапшота обрабатывается только в фазе "after_snapshot" выше,
                # чтобы избежать двойного flush.
                log_manager.maybe_flush(self_state, phase="tick")


                # Поддержка постоянного интервала тиков
                tick_end = time.time()
                elapsed_tick = tick_end - current_time

                # Passive data collection: tick end metrics
                passive_data_sink.receive_data(
                    event_type="tick_end",
                    data={"tick": self_state.ticks, "elapsed": elapsed_tick, "timestamp": tick_end},
                    source="runtime_loop",
                    metadata={"performance": True}
                )

                # Async data collection: performance metrics
                async_data_sink.log_event(
                    data={"tick": self_state.ticks, "elapsed_seconds": elapsed_tick, "sleep_duration": sleep_duration},
                    event_type="performance_metrics",
                    source="runtime_loop",
                    metadata={"tick_duration": elapsed_tick}
                )

                # Периодическая очистка старых данных в PassiveDataSink (каждые 100 тиков)
                if self_state.ticks % 100 == 0:
                    removed_count = passive_data_sink.clear_old_data(keep_recent=10000)
                    if removed_count > 0:
                        logger.info(f"[DATA_SINK] Cleared {removed_count} old entries from PassiveDataSink")

                sleep_duration = max(0.0, tick_interval - elapsed_tick)
                time.sleep(sleep_duration)

            except Exception as e:
                self_state.apply_delta({"integrity": -ERROR_INTEGRITY_PENALTY})
                logger.error(f"[LOOP] Ошибка в цикле: {e}", exc_info=True)
                # Flush логов при исключении (если политика требует)
                log_manager.maybe_flush(self_state, phase="exception")

            finally:
                # Остановка адаптивной системы обработки
                if adaptive_processing_manager:
                    adaptive_processing_manager.stop()
                    structured_logger.log_event(
                        {"event_type": "adaptive_processing_manager_stopped"}
                    )

                # Остановка менеджера сбора данных
                if data_collection_manager:
                    data_collection_manager.stop()

                # Остановка AsyncDataSink
                try:
                    async_data_sink.stop()
                    logger.info("[DATA_SINK] AsyncDataSink stopped successfully")
                except Exception as e:
                    logger.error(f"[DATA_SINK] Error stopping AsyncDataSink: {e}")

                # Финализация PassiveDataSink
                try:
                    final_stats = passive_data_sink.get_stats()
                    logger.info(f"[DATA_SINK] PassiveDataSink final stats: {final_stats}")
                except Exception as e:
                    logger.error(f"[DATA_SINK] Error getting PassiveDataSink stats: {e}")


                # Flush логов при завершении (обязательно)
                log_manager.maybe_flush(self_state, phase="shutdown")

                # NOTE: Система Life не останавливается при параметрах <= 0
                # Она продолжает работать в degraded состоянии ("бессмертная слабость")
                # Остановка происходит только по внешнему сигналу (stop_event)


    try:
        # Запуск основного цикла с профилированием или без
        if enable_profiling:
            logger.info("[PROFILING] Включено профилирование runtime loop с cProfile")
            profiler = cProfile.Profile()
            try:
                profiler.enable()
                run_main_loop()
            finally:
                profiler.disable()
                # Сохраняем результаты профилирования
                import os
                import pstats
                from io import StringIO

                # Создаем директорию data если не существует
                os.makedirs("data", exist_ok=True)

                stats = pstats.Stats(profiler, stream=StringIO())
                stats.sort_stats("cumulative")
                stats.print_stats(50)  # Top 50 функций

                # Сохраняем в файл для анализа
                profile_filename = f"data/runtime_loop_profile_{int(time.time())}.prof"
                profiler.dump_stats(profile_filename)
                logger.info(f"[PROFILING] Результаты профилирования сохранены в {profile_filename}")

                # Выводим краткую статистику в лог
                s = StringIO()
                stats = pstats.Stats(profiler, stream=s)
                stats.sort_stats("cumulative")
                stats.print_stats(10)
                logger.info(f"[PROFILING] Top 10 функций по cumulative time:\n{s.getvalue()}")
        else:
            run_main_loop()
    finally:
        # Корректное завершение StructuredLogger при окончании работы
        if 'structured_logger' in locals() and structured_logger is not None:
            structured_logger.shutdown()


def _map_clarity_stage_to_type(stage: str) -> str:
    """
    Map clarity moment stage to memory-relevant type.

    Args:
        stage: Clarity moment stage

    Returns:
        Memory-relevant clarity type
    """
    stage_mapping = {
        "initial_awakening": "cognitive",
        "deep_insight": "existential",
        "pattern_recognition": "cognitive",
        "emotional_clarity": "emotional",
        "flow_state": "cognitive",
        "meta_awareness": "existential"
    }
    return stage_mapping.get(stage, "cognitive")



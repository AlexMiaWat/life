"""
Многопоточный движок сознания - Parallel Consciousness Engine.

Реализация многопоточной модели сознания с параллельными процессами для
исследования эмерджентных свойств искусственного сознания.
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
import queue

from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


@dataclass
class ParallelProcessMetrics:
    """
    Метрики параллельного процесса сознания.
    """

    process_name: str
    update_frequency: float  # Hz
    last_update_time: float = 0.0
    update_count: int = 0
    average_update_time: float = 0.0
    is_active: bool = True
    thread_id: Optional[int] = None
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class ConsciousnessSharedState:
    """
    Разделяемое состояние сознания для потоков.
    """

    consciousness_level: float = 0.0
    self_reflection_score: float = 0.0
    meta_cognition_depth: float = 0.0
    current_state: str = "awake"
    neural_activity: float = 0.0
    energy_level: float = 0.5
    stability: float = 0.5
    cognitive_load: float = 0.3

    # Синхронизация
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def update_metric(self, metric_name: str, value: float) -> None:
        """Безопасно обновить метрику."""
        with self._lock:
            if hasattr(self, metric_name):
                setattr(self, metric_name, value)

    def get_metrics_snapshot(self) -> Dict[str, float]:
        """Получить snapshot всех метрик."""
        with self._lock:
            return {
                "consciousness_level": self.consciousness_level,
                "self_reflection_score": self.self_reflection_score,
                "meta_cognition_depth": self.meta_cognition_depth,
                "current_state": self.current_state,
                "neural_activity": self.neural_activity,
                "energy_level": self.energy_level,
                "stability": self.stability,
                "cognitive_load": self.cognitive_load,
            }


class ConsciousnessProcess(threading.Thread):
    """
    Базовый класс для параллельных процессов сознания.
    """

    def __init__(
        self,
        name: str,
        shared_state: ConsciousnessSharedState,
        logger: Optional[StructuredLogger] = None,
    ):
        super().__init__(name=name, daemon=True)
        self.process_name = name
        self.shared_state = shared_state
        self.logger = logger or StructuredLogger(__name__)

        # Конфигурация процесса
        self.update_interval = 1.0  # секунды
        self.is_running = False
        self.stop_event = threading.Event()

        # Метрики процесса
        self.metrics = ParallelProcessMetrics(
            process_name=name, update_frequency=1.0 / self.update_interval
        )

        # Очереди для межпроцессного общения
        self.input_queue = queue.Queue(maxsize=100)
        self.output_queue = queue.Queue(maxsize=100)

    def start_process(self) -> None:
        """Запустить процесс."""
        self.is_running = True
        self.stop_event.clear()
        self.start()

    def stop_process(self) -> None:
        """Остановить процесс."""
        self.is_running = False
        self.stop_event.set()
        self.join(timeout=2.0)

    def run(self) -> None:
        """Основной цикл процесса."""
        self.metrics.thread_id = threading.get_ident()

        self.logger.log_event(
            {
                "event_type": "consciousness_process_started",
                "process_name": self.process_name,
                "thread_id": self.metrics.thread_id,
                "update_interval": self.update_interval,
            }
        )

        while self.is_running and not self.stop_event.is_set():
            try:
                start_time = time.time()

                # Выполнить работу процесса
                self.process_step()

                # Обновить метрики
                end_time = time.time()
                update_time = end_time - start_time
                self._update_process_metrics(update_time)

                # Подождать до следующего обновления
                self.stop_event.wait(self.update_interval)

            except Exception as e:
                self.metrics.error_count += 1
                self.metrics.last_error = str(e)

                self.logger.log_event(
                    {
                        "event_type": "consciousness_process_error",
                        "process_name": self.process_name,
                        "error": str(e),
                        "error_count": self.metrics.error_count,
                    }
                )

                # Небольшая пауза при ошибке
                self.stop_event.wait(1.0)

        self.logger.log_event(
            {
                "event_type": "consciousness_process_stopped",
                "process_name": self.process_name,
                "total_updates": self.metrics.update_count,
            }
        )

    def process_step(self) -> None:
        """
        Шаг обработки процесса. Должен быть переопределен в подклассах.
        """
        raise NotImplementedError("process_step must be implemented by subclass")

    def _update_process_metrics(self, update_time: float) -> None:
        """Обновить метрики процесса."""
        self.metrics.last_update_time = time.time()
        self.metrics.update_count += 1

        # Экспоненциальное сглаживание среднего времени
        alpha = 0.1
        if self.metrics.average_update_time == 0:
            self.metrics.average_update_time = update_time
        else:
            self.metrics.average_update_time = (
                alpha * update_time + (1 - alpha) * self.metrics.average_update_time
            )


class NeuralActivityMonitor(ConsciousnessProcess):
    """
    Монитор нейронной активности.
    Отслеживает частоту обработки событий и тиков.
    """

    def __init__(
        self,
        shared_state: ConsciousnessSharedState,
        self_state_provider: Callable,
        logger: Optional[StructuredLogger] = None,
    ):
        super().__init__("neural_activity_monitor", shared_state, logger)
        self.update_interval = 0.1  # 10 Hz
        self.self_state_provider = self_state_provider

        # История для сглаживания
        self.tick_history = deque(maxlen=100)
        self.event_history = deque(maxlen=100)

    def process_step(self) -> None:
        """Мониторить нейронную активность."""
        try:
            # Получить текущее состояние системы
            self_state = self.self_state_provider()

            # Извлечь метрики активности
            tick_frequency = getattr(self_state, "tick_frequency", 1.0)
            event_processing_rate = getattr(self_state, "event_processing_rate", 10.0)
            decision_complexity = getattr(self_state, "decision_complexity", 0.5)

            # Добавить в историю
            current_time = time.time()
            self.tick_history.append((current_time, tick_frequency))
            self.event_history.append((current_time, event_processing_rate))

            # Рассчитать сглаженные значения
            smoothed_tick_freq = self._calculate_smoothed_value(self.tick_history)
            smoothed_event_rate = self._calculate_smoothed_value(self.event_history)

            # Рассчитать нейронную активность
            neural_activity = self._calculate_neural_activity(
                smoothed_tick_freq, smoothed_event_rate, decision_complexity
            )

            # Обновить разделяемое состояние
            self.shared_state.update_metric("neural_activity", neural_activity)

            # Логировать результаты (не на каждом шаге для производительности)
            if self.metrics.update_count % 10 == 0:  # Каждые 10 обновлений (1 сек)
                self.logger.log_event(
                    {
                        "event_type": "neural_activity_updated",
                        "neural_activity": neural_activity,
                        "tick_frequency": smoothed_tick_freq,
                        "event_processing_rate": smoothed_event_rate,
                        "decision_complexity": decision_complexity,
                    }
                )

        except Exception as e:
            self.logger.log_event({"event_type": "neural_activity_monitor_error", "error": str(e)})

    def _calculate_smoothed_value(self, history: deque) -> float:
        """Рассчитать сглаженное значение из истории."""
        if not history:
            return 0.0

        # Взвешенное среднее (более свежие значения имеют больший вес)
        total_weight = 0.0
        weighted_sum = 0.0

        for i, (timestamp, value) in enumerate(history):
            # Экспоненциально убывающий вес
            weight = 0.9 ** (len(history) - 1 - i)
            weighted_sum += value * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_neural_activity(
        self, tick_freq: float, event_rate: float, complexity: float
    ) -> float:
        """Рассчитать уровень нейронной активности."""
        # Нормализация
        normalized_tick = min(1.0, tick_freq / 10.0)  # Макс 10 тиков/сек
        normalized_event = min(1.0, event_rate / 100.0)  # Макс 100 событий/сек

        # Взвешенная сумма
        activity = normalized_tick * 0.4 + normalized_event * 0.4 + complexity * 0.2

        return max(0.0, min(1.0, activity))


class SelfReflectionProcessor(ConsciousnessProcess):
    """
    Процессор саморефлексии.
    Анализирует паттерны поведения и эффективность решений.
    """

    def __init__(
        self,
        shared_state: ConsciousnessSharedState,
        decision_history_provider: Callable,
        behavior_patterns_provider: Callable,
        logger: Optional[StructuredLogger] = None,
    ):
        super().__init__("self_reflection_processor", shared_state, logger)
        self.update_interval = 5.0  # 0.2 Hz
        self.decision_history_provider = decision_history_provider
        self.behavior_patterns_provider = behavior_patterns_provider

    def process_step(self) -> None:
        """Обработать саморефлексию."""
        try:
            # Получить данные для анализа
            decision_history = self.decision_history_provider()
            behavior_patterns = self.behavior_patterns_provider()

            # Анализировать паттерны поведения
            behavior_quality = self._analyze_behavior_patterns(behavior_patterns)
            decision_quality = self._evaluate_decision_quality(decision_history)
            pattern_recognition = self._assess_pattern_recognition(behavior_patterns)

            # Рассчитать общий уровень саморефлексии
            self_reflection_score = (
                behavior_quality * 0.5 + decision_quality * 0.3 + pattern_recognition * 0.2
            )

            # Ограничить диапазон
            self_reflection_score = max(0.0, min(1.0, self_reflection_score))

            # Обновить разделяемое состояние
            self.shared_state.update_metric("self_reflection_score", self_reflection_score)

            self.logger.log_event(
                {
                    "event_type": "self_reflection_updated",
                    "self_reflection_score": self_reflection_score,
                    "behavior_quality": behavior_quality,
                    "decision_quality": decision_quality,
                    "pattern_recognition": pattern_recognition,
                }
            )

        except Exception as e:
            self.logger.log_event(
                {"event_type": "self_reflection_processor_error", "error": str(e)}
            )

    def _analyze_behavior_patterns(self, behavior_patterns: List[Dict]) -> float:
        """Анализировать качество паттернов поведения."""
        if not behavior_patterns:
            return 0.0
        return sum(p.get("quality", 0.5) for p in behavior_patterns) / len(behavior_patterns)

    def _evaluate_decision_quality(self, decision_history: List[Dict]) -> float:
        """Оценивать качество решений."""
        if not decision_history:
            return 0.0
        success_count = sum(1 for d in decision_history if d.get("success", False))
        return success_count / len(decision_history)

    def _assess_pattern_recognition(self, behavior_patterns: List[Dict]) -> float:
        """Оценивать способность распознавания паттернов."""
        if not behavior_patterns:
            return 0.0
        pattern_count = len(behavior_patterns)
        diversity = len(set(p.get("type", "unknown") for p in behavior_patterns))
        return min(1.0, (pattern_count + diversity) / 20.0)


class MetaCognitionAnalyzer(ConsciousnessProcess):
    """
    Анализатор метакогниции.
    Осознает собственные когнитивные процессы.
    """

    def __init__(
        self,
        shared_state: ConsciousnessSharedState,
        cognitive_processes_provider: Callable,
        optimization_history_provider: Callable,
        logger: Optional[StructuredLogger] = None,
    ):
        super().__init__("meta_cognition_analyzer", shared_state, logger)
        self.update_interval = 30.0  # 0.033 Hz - низкочастотный анализ
        self.cognitive_processes_provider = cognitive_processes_provider
        self.optimization_history_provider = optimization_history_provider

    def process_step(self) -> None:
        """Анализировать метакогницию."""
        try:
            # Получить данные для глубокого анализа
            cognitive_processes = self.cognitive_processes_provider()
            optimization_history = self.optimization_history_provider()

            # Оценить различные аспекты метакогниции
            process_awareness = self._measure_process_awareness(cognitive_processes)
            optimization_capability = self._assess_optimization_capability(optimization_history)
            abstract_reasoning = self._evaluate_abstract_reasoning(cognitive_processes)

            # Рассчитать глубину метакогниции
            meta_cognition_depth = (
                process_awareness * 0.4 + optimization_capability * 0.4 + abstract_reasoning * 0.2
            )

            # Ограничить диапазон
            meta_cognition_depth = max(0.0, min(1.0, meta_cognition_depth))

            # Обновить разделяемое состояние
            self.shared_state.update_metric("meta_cognition_depth", meta_cognition_depth)

            self.logger.log_event(
                {
                    "event_type": "meta_cognition_updated",
                    "meta_cognition_depth": meta_cognition_depth,
                    "process_awareness": process_awareness,
                    "optimization_capability": optimization_capability,
                    "abstract_reasoning": abstract_reasoning,
                }
            )

        except Exception as e:
            self.logger.log_event({"event_type": "meta_cognition_analyzer_error", "error": str(e)})

    def _measure_process_awareness(self, cognitive_processes: List[Dict]) -> float:
        """Измерить осознанность когнитивных процессов."""
        if not cognitive_processes:
            return 0.0
        return min(1.0, len(cognitive_processes) / 10.0)

    def _assess_optimization_capability(self, optimization_history: List[Dict]) -> float:
        """Оценить способность к самооптимизации."""
        if not optimization_history:
            return 0.0
        success_count = sum(1 for opt in optimization_history if opt.get("success", False))
        return success_count / len(optimization_history)

    def _evaluate_abstract_reasoning(self, cognitive_processes: List[Dict]) -> float:
        """Оценить способность к абстрактному мышлению."""
        if not cognitive_processes:
            return 0.0
        abstract_count = sum(
            1
            for proc in cognitive_processes
            if proc.get("type") in ["generalization", "abstraction", "concept_formation"]
        )
        return min(1.0, abstract_count / 5.0)


class StateTransitionManager(ConsciousnessProcess):
    """
    Менеджер переходов состояний.
    Управляет переходами между состояниями сознания.
    """

    def __init__(
        self, shared_state: ConsciousnessSharedState, logger: Optional[StructuredLogger] = None
    ):
        super().__init__("state_transition_manager", shared_state, logger)
        self.update_interval = 1.0  # 1 Hz

        # Определение состояний (упрощенная версия)
        self.states = {
            "unconscious": {"min_level": 0.0, "max_level": 0.1},
            "dreaming": {"min_level": 0.1, "max_level": 0.2},
            "awake": {"min_level": 0.1, "max_level": 0.5},
            "reflective": {"min_level": 0.3, "max_level": 0.7},
            "flow": {"min_level": 0.4, "max_level": 0.9},
            "meta": {"min_level": 0.5, "max_level": 1.0},
        }

        # Предотвращение частых переходов
        self.last_transition_time = 0.0
        self.transition_cooldown = 5.0  # секунды

    def process_step(self) -> None:
        """Управлять переходами состояний."""
        try:
            current_time = time.time()

            # Проверяем cooldown
            if current_time - self.last_transition_time < self.transition_cooldown:
                return

            # Получить текущие метрики
            metrics = self.shared_state.get_metrics_snapshot()
            current_level = metrics["consciousness_level"]
            current_energy = metrics["energy_level"]
            current_stability = metrics["stability"]
            current_state = metrics["current_state"]

            # Определить целевое состояние
            target_state = self._determine_target_state(
                current_level, current_energy, current_stability
            )

            # Проверить необходимость перехода
            if target_state != current_state:
                # Выполнить переход
                self.shared_state.update_metric("current_state", target_state)
                self.last_transition_time = current_time

                self.logger.log_event(
                    {
                        "event_type": "consciousness_state_transition",
                        "from_state": current_state,
                        "to_state": target_state,
                        "consciousness_level": current_level,
                        "energy_level": current_energy,
                        "stability": current_stability,
                        "reason": "automatic_transition",
                    }
                )

        except Exception as e:
            self.logger.log_event({"event_type": "state_transition_manager_error", "error": str(e)})

    def _determine_target_state(self, level: float, energy: float, stability: float) -> str:
        """Определить целевое состояние на основе метрик."""
        # Приоритет состояний (от высшего к низшему)
        state_priority = ["meta", "flow", "reflective", "awake", "dreaming", "unconscious"]

        for state_name in state_priority:
            state_config = self.states[state_name]
            min_level = state_config["min_level"]
            max_level = state_config["max_level"]

            if min_level <= level <= max_level:
                # Дополнительные условия для специальных состояний
                if state_name == "flow" and (energy < 0.7 or stability < 0.8):
                    continue
                if state_name == "meta" and (energy < 0.6 or level < 0.5):
                    continue

                return state_name

        return "awake"  # fallback


class ConsciousnessMetricsAggregator(ConsciousnessProcess):
    """
    Агрегатор метрик сознания.
    Собирает и агрегирует метрики от всех процессов.
    """

    def __init__(
        self, shared_state: ConsciousnessSharedState, logger: Optional[StructuredLogger] = None
    ):
        super().__init__("consciousness_metrics_aggregator", shared_state, logger)
        self.update_interval = 1.0  # 1 Hz

    def process_step(self) -> None:
        """Агрегировать метрики сознания."""
        try:
            # Получить текущие метрики
            metrics = self.shared_state.get_metrics_snapshot()

            # Рассчитать общий уровень сознания
            consciousness_level = self._calculate_consciousness_level(metrics)

            # Обновить финальный уровень
            self.shared_state.update_metric("consciousness_level", consciousness_level)

            # Логировать агрегированные метрики (не на каждом шаге)
            if self.metrics.update_count % 10 == 0:  # Каждые 10 сек
                self.logger.log_event(
                    {
                        "event_type": "consciousness_metrics_aggregated",
                        "consciousness_level": consciousness_level,
                        "self_reflection_score": metrics["self_reflection_score"],
                        "meta_cognition_depth": metrics["meta_cognition_depth"],
                        "current_state": metrics["current_state"],
                        "neural_activity": metrics["neural_activity"],
                    }
                )

        except Exception as e:
            self.logger.log_event(
                {"event_type": "consciousness_metrics_aggregator_error", "error": str(e)}
            )

    def _calculate_consciousness_level(self, metrics: Dict[str, float]) -> float:
        """Рассчитать общий уровень сознания."""
        neural_activity = metrics["neural_activity"]
        self_reflection = metrics["self_reflection_score"]
        meta_cognition = metrics["meta_cognition_depth"]
        energy = metrics["energy_level"]

        # Взвешенная формула
        level = neural_activity * 0.4 + self_reflection * 0.3 + meta_cognition * 0.2 + energy * 0.1

        return max(0.1, min(1.0, level))  # Минимум 0.1 для базовой осознанности


class ParallelConsciousnessEngine:
    """
    Многопоточный движок сознания.
    Координирует работу параллельных процессов сознания.
    """

    def __init__(
        self,
        self_state_provider: Callable,
        decision_history_provider: Callable = None,
        behavior_patterns_provider: Callable = None,
        cognitive_processes_provider: Callable = None,
        optimization_history_provider: Callable = None,
        logger: Optional[StructuredLogger] = None,
    ):
        """
        Инициализация многопоточного движка сознания.

        Args:
            self_state_provider: Функция для получения SelfState
            decision_history_provider: Функция для получения истории решений
            behavior_patterns_provider: Функция для получения паттернов поведения
            cognitive_processes_provider: Функция для получения когнитивных процессов
            optimization_history_provider: Функция для получения истории оптимизаций
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)

        # Провайдеры данных
        self.self_state_provider = self_state_provider
        self.decision_history_provider = decision_history_provider or (lambda: [])
        self.behavior_patterns_provider = behavior_patterns_provider or (lambda: [])
        self.cognitive_processes_provider = cognitive_processes_provider or (lambda: [])
        self.optimization_history_provider = optimization_history_provider or (lambda: [])

        # Разделяемое состояние
        self.shared_state = ConsciousnessSharedState()

        # Параллельные процессы
        self.processes = self._create_processes()

        # Статус
        self.is_running = False

        self.logger.log_event(
            {
                "event_type": "parallel_consciousness_engine_initialized",
                "process_count": len(self.processes),
            }
        )

    def _create_processes(self) -> List[ConsciousnessProcess]:
        """Создать все параллельные процессы."""
        return [
            NeuralActivityMonitor(self.shared_state, self.self_state_provider, self.logger),
            SelfReflectionProcessor(
                self.shared_state,
                self.decision_history_provider,
                self.behavior_patterns_provider,
                self.logger,
            ),
            MetaCognitionAnalyzer(
                self.shared_state,
                self.cognitive_processes_provider,
                self.optimization_history_provider,
                self.logger,
            ),
            StateTransitionManager(self.shared_state, self.logger),
            ConsciousnessMetricsAggregator(self.shared_state, self.logger),
        ]

    def start(self) -> None:
        """Запустить все процессы сознания."""
        if self.is_running:
            return

        self.is_running = True

        # Запустить все процессы
        for process in self.processes:
            process.start_process()

        self.logger.log_event(
            {
                "event_type": "parallel_consciousness_engine_started",
                "active_processes": [p.process_name for p in self.processes if p.is_alive()],
            }
        )

    def stop(self) -> None:
        """Остановить все процессы сознания."""
        if not self.is_running:
            return

        self.is_running = False

        # Остановить все процессы
        for process in self.processes:
            process.stop_process()

        self.logger.log_event({"event_type": "parallel_consciousness_engine_stopped"})

    def get_consciousness_snapshot(self) -> Dict[str, Any]:
        """
        Получить текущий snapshot состояния сознания.

        Returns:
            Полное состояние сознания со всеми метриками
        """
        metrics = self.shared_state.get_metrics_snapshot()

        # Добавить информацию о процессах
        process_status = {}
        for process in self.processes:
            process_status[process.process_name] = {
                "is_alive": process.is_alive(),
                "update_count": process.metrics.update_count,
                "error_count": process.metrics.error_count,
                "last_update": process.metrics.last_update_time,
                "thread_id": process.metrics.thread_id,
            }

        return {
            "metrics": metrics,
            "processes": process_status,
            "timestamp": time.time(),
            "is_running": self.is_running,
        }

    def get_process_metrics(self) -> Dict[str, Any]:
        """
        Получить метрики всех процессов.

        Returns:
            Детальные метрики каждого процесса
        """
        return {
            process.process_name: {
                "update_frequency": process.metrics.update_frequency,
                "last_update_time": process.metrics.last_update_time,
                "update_count": process.metrics.update_count,
                "average_update_time": process.metrics.average_update_time,
                "is_active": process.metrics.is_active,
                "thread_id": process.metrics.thread_id,
                "error_count": process.metrics.error_count,
                "last_error": process.metrics.last_error,
            }
            for process in self.processes
        }

    def update_external_metrics(
        self, energy: float = None, stability: float = None, cognitive_load: float = None
    ) -> None:
        """
        Обновить внешние метрики (энергия, стабильность и т.д.).

        Args:
            energy: Уровень энергии системы
            stability: Уровень стабильности
            cognitive_load: Когнитивная нагрузка
        """
        if energy is not None:
            self.shared_state.update_metric("energy_level", energy)
        if stability is not None:
            self.shared_state.update_metric("stability", stability)
        if cognitive_load is not None:
            self.shared_state.update_metric("cognitive_load", cognitive_load)

    def reset_engine(self) -> None:
        """Сбросить состояние движка."""
        self.stop()

        # Сбросить разделяемое состояние
        self.shared_state = ConsciousnessSharedState()

        # Пересоздать процессы
        self.processes = self._create_processes()

        self.logger.log_event({"event_type": "parallel_consciousness_engine_reset"})

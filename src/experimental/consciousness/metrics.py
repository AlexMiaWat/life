"""
Метрики сознания - Consciousness Metrics.

Компонент для количественной оценки различных аспектов сознания и когнитивных процессов.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from collections import deque

from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


class ConsciousnessMetrics:
    """
    Метрики для количественной оценки различных аспектов сознания.

    Измеряет:
    - Нейронную активность
    - Самоосознание
    - Временную непрерывность
    - Абстрактное мышление
    - Когнитивную нагрузку
    """

    def __init__(self, history_window: int = 100, logger: Optional[StructuredLogger] = None):
        """
        Инициализация метрик сознания.

        Args:
            history_window: Размер окна истории для расчетов
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)
        self.history_window = history_window

        # История измерений для каждого типа метрики
        self._neural_activity_history: deque = deque(maxlen=history_window)
        self._self_awareness_history: deque = deque(maxlen=history_window)
        self._temporal_continuity_history: deque = deque(maxlen=history_window)
        self._abstract_reasoning_history: deque = deque(maxlen=history_window)
        self._cognitive_load_history: deque = deque(maxlen=history_window)

        # Временные метки последних измерений
        self._last_measurement_time = 0.0

        # Статистика измерений
        self._measurement_count = 0
        self._average_measurement_time = 0.0

        self.logger.log_event(
            {"event_type": "consciousness_metrics_initialized", "history_window": history_window}
        )

    def measure_neural_activity(
        self, tick_frequency: float, event_processing_rate: float, decision_complexity: float
    ) -> float:
        """
        Измерить нейронную активность системы.

        Args:
            tick_frequency: Частота тиков в секунду
            event_processing_rate: Скорость обработки событий
            decision_complexity: Сложность принимаемых решений

        Returns:
            Уровень нейронной активности (0.0-1.0)
        """
        start_time = time.time()

        # Нормализация входных параметров
        normalized_tick_freq = min(1.0, tick_frequency / 10.0)  # Макс 10 тиков/сек
        normalized_event_rate = min(1.0, event_processing_rate / 100.0)  # Макс 100 событий/сек
        normalized_complexity = decision_complexity  # Уже в диапазоне 0.0-1.0

        # Взвешенная сумма факторов
        neural_activity = (
            normalized_tick_freq * 0.4 + normalized_event_rate * 0.4 + normalized_complexity * 0.2
        )

        # Ограничиваем диапазон
        neural_activity = max(0.0, min(1.0, neural_activity))

        # Добавляем в историю
        self._neural_activity_history.append(
            {
                "value": neural_activity,
                "timestamp": time.time(),
                "tick_frequency": tick_frequency,
                "event_processing_rate": event_processing_rate,
                "decision_complexity": decision_complexity,
            }
        )

        # Обновляем статистику
        self._update_measurement_stats(time.time() - start_time)

        self.logger.log_event(
            {
                "event_type": "neural_activity_measured",
                "value": neural_activity,
                "tick_frequency": tick_frequency,
                "event_processing_rate": event_processing_rate,
                "decision_complexity": decision_complexity,
            }
        )

        return neural_activity

    def assess_self_awareness(
        self, state_analysis_quality: float, behavior_tracking: float, reflection_frequency: float
    ) -> float:
        """
        Оценить самоосознание системы.

        Args:
            state_analysis_quality: Качество анализа собственного состояния
            behavior_tracking: Эффективность отслеживания поведения
            reflection_frequency: Частота рефлексивных процессов

        Returns:
            Уровень самоосознания (0.0-1.0)
        """
        start_time = time.time()

        # Комбинированная оценка
        self_awareness = (
            state_analysis_quality * 0.4 + behavior_tracking * 0.4 + reflection_frequency * 0.2
        )

        # Ограничиваем диапазон
        self_awareness = max(0.0, min(1.0, self_awareness))

        # Добавляем в историю
        self._self_awareness_history.append(
            {
                "value": self_awareness,
                "timestamp": time.time(),
                "state_analysis_quality": state_analysis_quality,
                "behavior_tracking": behavior_tracking,
                "reflection_frequency": reflection_frequency,
            }
        )

        # Обновляем статистику
        self._update_measurement_stats(time.time() - start_time)

        self.logger.log_event(
            {
                "event_type": "self_awareness_assessed",
                "value": self_awareness,
                "state_analysis_quality": state_analysis_quality,
                "behavior_tracking": behavior_tracking,
                "reflection_frequency": reflection_frequency,
            }
        )

        return self_awareness

    def evaluate_temporal_continuity(
        self,
        subjective_time_consistency: float,
        memory_coherence: float,
        event_sequence_integrity: float,
    ) -> float:
        """
        Оценить временную непрерывность восприятия.

        Args:
            subjective_time_consistency: Согласованность субъективного времени
            memory_coherence: Целостность памяти
            event_sequence_integrity: Целостность последовательности событий

        Returns:
            Уровень временной непрерывности (0.0-1.0)
        """
        start_time = time.time()

        # Комбинированная оценка
        temporal_continuity = (
            subjective_time_consistency * 0.4
            + memory_coherence * 0.3
            + event_sequence_integrity * 0.3
        )

        # Ограничиваем диапазон
        temporal_continuity = max(0.0, min(1.0, temporal_continuity))

        # Добавляем в историю
        self._temporal_continuity_history.append(
            {
                "value": temporal_continuity,
                "timestamp": time.time(),
                "subjective_time_consistency": subjective_time_consistency,
                "memory_coherence": memory_coherence,
                "event_sequence_integrity": event_sequence_integrity,
            }
        )

        # Обновляем статистику
        self._update_measurement_stats(time.time() - start_time)

        self.logger.log_event(
            {
                "event_type": "temporal_continuity_evaluated",
                "value": temporal_continuity,
                "subjective_time_consistency": subjective_time_consistency,
                "memory_coherence": memory_coherence,
                "event_sequence_integrity": event_sequence_integrity,
            }
        )

        return temporal_continuity

    def measure_abstract_reasoning(
        self, concept_formation: float, generalization: float, pattern_abstraction: float
    ) -> float:
        """
        Измерить способность к абстрактному мышлению.

        Args:
            concept_formation: Способность к формированию концепций
            generalization: Способность к обобщению
            pattern_abstraction: Способность к абстракции паттернов

        Returns:
            Уровень абстрактного мышления (0.0-1.0)
        """
        start_time = time.time()

        # Комбинированная оценка
        abstract_reasoning = (
            concept_formation * 0.4 + generalization * 0.3 + pattern_abstraction * 0.3
        )

        # Ограничиваем диапазон
        abstract_reasoning = max(0.0, min(1.0, abstract_reasoning))

        # Добавляем в историю
        self._abstract_reasoning_history.append(
            {
                "value": abstract_reasoning,
                "timestamp": time.time(),
                "concept_formation": concept_formation,
                "generalization": generalization,
                "pattern_abstraction": pattern_abstraction,
            }
        )

        # Обновляем статистику
        self._update_measurement_stats(time.time() - start_time)

        self.logger.log_event(
            {
                "event_type": "abstract_reasoning_measured",
                "value": abstract_reasoning,
                "concept_formation": concept_formation,
                "generalization": generalization,
                "pattern_abstraction": pattern_abstraction,
            }
        )

        return abstract_reasoning

    def measure_cognitive_load(
        self, active_processes: int, memory_usage: float, attention_focus: float
    ) -> float:
        """
        Измерить когнитивную нагрузку.

        Args:
            active_processes: Количество активных когнитивных процессов
            memory_usage: Использование памяти
            attention_focus: Фокус внимания

        Returns:
            Уровень когнитивной нагрузки (0.0-1.0)
        """
        start_time = time.time()

        # Нормализация параметров
        normalized_processes = min(1.0, active_processes / 10.0)  # Макс 10 процессов
        normalized_memory = memory_usage  # Уже в диапазоне 0.0-1.0
        normalized_attention = attention_focus  # Уже в диапазоне 0.0-1.0

        # Когнитивная нагрузка растет с увеличением параметров
        cognitive_load = (
            normalized_processes * 0.4
            + normalized_memory * 0.4
            + (1.0 - normalized_attention) * 0.2  # Инвертированный фокус внимания
        )

        # Ограничиваем диапазон
        cognitive_load = max(0.0, min(1.0, cognitive_load))

        # Добавляем в историю
        self._cognitive_load_history.append(
            {
                "value": cognitive_load,
                "timestamp": time.time(),
                "active_processes": active_processes,
                "memory_usage": memory_usage,
                "attention_focus": attention_focus,
            }
        )

        # Обновляем статистику
        self._update_measurement_stats(time.time() - start_time)

        self.logger.log_event(
            {
                "event_type": "cognitive_load_measured",
                "value": cognitive_load,
                "active_processes": active_processes,
                "memory_usage": memory_usage,
                "attention_focus": attention_focus,
            }
        )

        return cognitive_load

    def get_metric_trends(self, metric_name: str, time_window: float = 300.0) -> Dict[str, Any]:
        """
        Получить тренды изменения метрики за указанный период.

        Args:
            metric_name: Название метрики ('neural_activity', 'self_awareness', etc.)
            time_window: Временное окно в секундах

        Returns:
            Статистика тренда метрики
        """
        # Выбираем нужную историю
        history_map = {
            "neural_activity": self._neural_activity_history,
            "self_awareness": self._self_awareness_history,
            "temporal_continuity": self._temporal_continuity_history,
            "abstract_reasoning": self._abstract_reasoning_history,
            "cognitive_load": self._cognitive_load_history,
        }

        history = history_map.get(metric_name)
        if not history:
            return {"error": f"Unknown metric: {metric_name}"}

        current_time = time.time()
        cutoff_time = current_time - time_window

        # Фильтруем по времени
        recent_measurements = [item for item in history if item["timestamp"] >= cutoff_time]

        if not recent_measurements:
            return {
                "trend": "insufficient_data",
                "average_value": 0.0,
                "change_rate": 0.0,
                "samples": 0,
                "time_window": time_window,
            }

        # Рассчитываем статистику
        values = [item["value"] for item in recent_measurements]
        timestamps = [item["timestamp"] for item in recent_measurements]

        average_value = sum(values) / len(values)

        # Рассчитываем скорость изменения
        if len(values) >= 2:
            time_span = timestamps[-1] - timestamps[0]
            value_change = values[-1] - values[0]
            change_rate = value_change / time_span if time_span > 0 else 0.0
        else:
            change_rate = 0.0

        # Определяем тренд
        if change_rate > 0.001:
            trend = "increasing"
        elif change_rate < -0.001:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "average_value": average_value,
            "change_rate": change_rate,
            "samples": len(recent_measurements),
            "time_window": time_window,
            "current_value": values[-1] if values else 0.0,
        }

    def get_comprehensive_metrics(self, self_state) -> Dict[str, float]:
        """
        Получить комплексную оценку всех метрик сознания.

        Args:
            self_state: Текущее состояние системы

        Returns:
            Словарь со всеми метриками сознания
        """
        # Извлекаем параметры из состояния системы
        tick_frequency = getattr(self_state, "tick_frequency", 1.0)
        event_processing_rate = getattr(self_state, "event_processing_rate", 10.0)
        decision_complexity = getattr(self_state, "decision_complexity", 0.5)

        state_analysis_quality = getattr(self_state, "state_analysis_quality", 0.5)
        behavior_tracking = getattr(self_state, "behavior_tracking", 0.5)
        reflection_frequency = getattr(self_state, "reflection_frequency", 0.3)

        subjective_time_consistency = getattr(self_state, "subjective_time_consistency", 0.8)
        memory_coherence = getattr(self_state, "memory_coherence", 0.7)
        event_sequence_integrity = getattr(self_state, "event_sequence_integrity", 0.9)

        concept_formation = getattr(self_state, "concept_formation", 0.4)
        generalization = getattr(self_state, "generalization", 0.3)
        pattern_abstraction = getattr(self_state, "pattern_abstraction", 0.5)

        active_processes = getattr(self_state, "active_cognitive_processes", 3)
        memory_usage = getattr(self_state, "memory_usage", 0.6)
        attention_focus = getattr(self_state, "attention_focus", 0.7)

        # Рассчитываем все метрики
        metrics = {
            "neural_activity": self.measure_neural_activity(
                tick_frequency, event_processing_rate, decision_complexity
            ),
            "self_awareness": self.assess_self_awareness(
                state_analysis_quality, behavior_tracking, reflection_frequency
            ),
            "temporal_continuity": self.evaluate_temporal_continuity(
                subjective_time_consistency, memory_coherence, event_sequence_integrity
            ),
            "abstract_reasoning": self.measure_abstract_reasoning(
                concept_formation, generalization, pattern_abstraction
            ),
            "cognitive_load": self.measure_cognitive_load(
                active_processes, memory_usage, attention_focus
            ),
        }

        self.logger.log_event({"event_type": "comprehensive_metrics_calculated", **metrics})

        return metrics

    def get_metric_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику по всем метрикам.

        Returns:
            Статистика измерений для каждой метрики
        """
        histories = {
            "neural_activity": self._neural_activity_history,
            "self_awareness": self._self_awareness_history,
            "temporal_continuity": self._temporal_continuity_history,
            "abstract_reasoning": self._abstract_reasoning_history,
            "cognitive_load": self._cognitive_load_history,
        }

        stats = {}
        for metric_name, history in histories.items():
            if history:
                values = [item["value"] for item in history]
                stats[metric_name] = {
                    "count": len(history),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1],
                }
            else:
                stats[metric_name] = {
                    "count": 0,
                    "average": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "latest": 0.0,
                }

        stats["overall"] = {
            "total_measurements": self._measurement_count,
            "average_measurement_time": self._average_measurement_time,
            "last_measurement": self._last_measurement_time,
        }

        return stats

    def _update_measurement_stats(self, measurement_time: float) -> None:
        """Обновить статистику измерений."""
        self._measurement_count += 1
        self._last_measurement_time = time.time()

        # Экспоненциальное сглаживание среднего времени измерения
        alpha = 0.1
        if self._average_measurement_time == 0:
            self._average_measurement_time = measurement_time
        else:
            self._average_measurement_time = (
                alpha * measurement_time + (1 - alpha) * self._average_measurement_time
            )

    def reset_metrics(self) -> None:
        """Сбросить все метрики и историю измерений."""
        self._neural_activity_history.clear()
        self._self_awareness_history.clear()
        self._temporal_continuity_history.clear()
        self._abstract_reasoning_history.clear()
        self._cognitive_load_history.clear()

        self._measurement_count = 0
        self._average_measurement_time = 0.0
        self._last_measurement_time = 0.0

        self.logger.log_event({"event_type": "consciousness_metrics_reset"})

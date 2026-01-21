"""
Движок сознания - Consciousness Engine.

Основной компонент системы сознания, отвечающий за расчет уровней осознанности
и управление когнитивными процессами.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


@dataclass
class ConsciousnessSnapshot:
    """
    Снимок состояния сознания в момент времени.
    """
    timestamp: float
    consciousness_level: float
    self_reflection_score: float
    meta_cognition_depth: float
    current_state: str
    neural_activity: float
    energy_level: float
    stability: float
    recent_events_count: int


class ConsciousnessEngine:
    """
    Движок для расчета и управления уровнем сознания.

    Отвечает за:
    - Расчет общего уровня сознания на основе различных факторов
    - Оценку саморефлексии и метакогниции
    - Управление переходами между состояниями сознания
    - Мониторинг когнитивных процессов
    """

    # Константы для расчетов
    BASELINE_CONSCIOUSNESS = 0.1  # Минимальный уровень сознания
    MAX_CONSCIOUSNESS_HISTORY = 100  # Максимум записей истории

    # Коэффициенты для расчета consciousness_level
    NEURAL_ACTIVITY_WEIGHT = 0.4
    SELF_REFLECTION_WEIGHT = 0.3
    META_COGNITION_WEIGHT = 0.2
    ENERGY_INFLUENCE_WEIGHT = 0.1

    # Пороги для состояний сознания
    AWAKE_THRESHOLD = 0.1
    REFLECTIVE_THRESHOLD = 0.3
    META_THRESHOLD = 0.5
    FLOW_STATE_ENERGY_MIN = 0.7
    FLOW_STATE_STABILITY_MIN = 0.8

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Инициализация движка сознания.

        Args:
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)

        # История состояний сознания
        self._consciousness_history: List[ConsciousnessSnapshot] = []

        # Внутреннее состояние
        self._last_calculation_time = time.time()
        self._state_change_cooldown = 0  # Предотвращает частые смены состояний

        # Кэшированные значения для оптимизации
        self._cached_consciousness_level = self.BASELINE_CONSCIOUSNESS
        self._cached_self_reflection = 0.0
        self._cached_meta_cognition = 0.0

        # Метрики производительности
        self._calculation_count = 0
        self._average_calculation_time = 0.0

        self.logger.log_event({
            "event_type": "consciousness_engine_initialized",
            "baseline_consciousness": self.BASELINE_CONSCIOUSNESS
        })

    def calculate_consciousness_level(self, self_state, event_history: Optional[List] = None) -> float:
        """
        Рассчитать общий уровень сознания на основе состояния системы и истории событий.

        Args:
            self_state: Текущее состояние системы (SelfState)
            event_history: Недавняя история событий

        Returns:
            Уровень сознания (0.0-1.0)
        """
        start_time = time.time()

        # Подготавливаем входные данные
        event_history = event_history or []
        recent_events_count = len(event_history)

        # Расчет нейронной активности
        neural_activity = self._calculate_neural_activity(self_state, recent_events_count)

        # Расчет саморефлексии
        self_reflection = self._calculate_self_reflection(self_state, event_history)

        # Расчет метакогниции
        meta_cognition = self._calculate_meta_cognition(self_state, event_history)

        # Влияние энергии
        energy_factor = getattr(self_state, 'energy', 0.5)

        # Влияние осознания тишины
        silence_factor = self._calculate_silence_consciousness_factor(event_history)

        # Основная формула расчета уровня сознания
        consciousness_level = (
            neural_activity * self.NEURAL_ACTIVITY_WEIGHT +
            self_reflection * self.SELF_REFLECTION_WEIGHT +
            meta_cognition * self.META_COGNITION_WEIGHT +
            energy_factor * self.ENERGY_INFLUENCE_WEIGHT +
            silence_factor * 0.1  # Влияние осознания тишины
        )

        # Ограничиваем диапазон
        consciousness_level = max(self.BASELINE_CONSCIOUSNESS,
                                min(1.0, consciousness_level))

        # Обновляем кэш
        self._cached_consciousness_level = consciousness_level
        self._cached_self_reflection = self_reflection
        self._cached_meta_cognition = meta_cognition

        # Определяем текущее состояние сознания
        current_state = self._determine_consciousness_state(
            consciousness_level, energy_factor, getattr(self_state, 'stability', 0.5)
        )

        # Создаем снимок состояния
        snapshot = ConsciousnessSnapshot(
            timestamp=time.time(),
            consciousness_level=consciousness_level,
            self_reflection_score=self_reflection,
            meta_cognition_depth=meta_cognition,
            current_state=current_state,
            neural_activity=neural_activity,
            energy_level=energy_factor,
            stability=getattr(self_state, 'stability', 0.5),
            recent_events_count=recent_events_count
        )

        # Добавляем в историю
        self._add_to_history(snapshot)

        # Обновляем метрики производительности
        calculation_time = time.time() - start_time
        self._update_performance_metrics(calculation_time)

        # Логируем изменение уровня сознания
        self._log_consciousness_change(snapshot)

        return consciousness_level

    def assess_self_reflection(self, decision_history: List[Dict], behavior_patterns: List[Dict]) -> float:
        """
        Оценить качество саморефлексии на основе истории решений и паттернов поведения.

        Args:
            decision_history: История принятых решений
            behavior_patterns: Выявленные паттерны поведения

        Returns:
            Оценка саморефлексии (0.0-1.0)
        """
        if not decision_history:
            return 0.0

        # Анализируем последовательность решений
        behavior_analysis_quality = self._analyze_behavior_patterns(behavior_patterns)
        decision_evaluation_quality = self._evaluate_decision_quality(decision_history)
        pattern_recognition_quality = self._assess_pattern_recognition(behavior_patterns)

        # Комбинированная оценка
        self_reflection_score = (
            behavior_analysis_quality * 0.5 +
            decision_evaluation_quality * 0.3 +
            pattern_recognition_quality * 0.2
        )

        return min(1.0, self_reflection_score)

    def evaluate_meta_cognition(self, cognitive_processes: List[Dict], optimization_history: List[Dict]) -> float:
        """
        Оценить глубину метакогниции на основе когнитивных процессов и истории оптимизаций.

        Args:
            cognitive_processes: История когнитивных процессов
            optimization_history: История оптимизаций и улучшений

        Returns:
            Оценка метакогниции (0.0-1.0)
        """
        if not cognitive_processes:
            return 0.0

        # Оцениваем различные аспекты метакогниции
        process_awareness = self._measure_process_awareness(cognitive_processes)
        optimization_capability = self._assess_optimization_capability(optimization_history)
        abstract_reasoning = self._evaluate_abstract_reasoning(cognitive_processes)

        # Комбинированная оценка
        meta_cognition_depth = (
            process_awareness * 0.4 +
            optimization_capability * 0.4 +
            abstract_reasoning * 0.2
        )

        return min(1.0, meta_cognition_depth)

    def determine_consciousness_state(self, consciousness_metrics: Dict[str, float]) -> str:
        """
        Определить текущее состояние сознания на основе метрик.

        Args:
            consciousness_metrics: Метрики сознания

        Returns:
            Название состояния сознания
        """
        consciousness_level = consciousness_metrics.get('consciousness_level', 0.0)
        energy = consciousness_metrics.get('energy', 0.5)
        stability = consciousness_metrics.get('stability', 0.5)

        # Предотвращаем слишком частые смены состояний
        current_time = time.time()
        if current_time - self._state_change_cooldown < 5.0:  # 5 секунд cooldown
            # Возвращаем предыдущее состояние
            if self._consciousness_history:
                return self._consciousness_history[-1].current_state
            return "awake"

        # Логика определения состояния
        if consciousness_level >= self.META_THRESHOLD:
            new_state = "meta"
        elif consciousness_level >= self.REFLECTIVE_THRESHOLD:
            new_state = "reflective"
        elif (consciousness_level >= self.AWAKE_THRESHOLD and
              energy >= self.FLOW_STATE_ENERGY_MIN and
              stability >= self.FLOW_STATE_STABILITY_MIN):
            new_state = "flow"
        elif consciousness_level >= self.AWAKE_THRESHOLD:
            new_state = "awake"
        elif energy < 0.3 or stability < 0.3:
            new_state = "unconscious"
        else:
            new_state = "dreaming"

        # Проверяем, изменилось ли состояние
        old_state = "awake"
        if self._consciousness_history:
            old_state = self._consciousness_history[-1].current_state

        if new_state != old_state:
            self._state_change_cooldown = current_time
            self._log_state_transition(old_state, new_state, consciousness_metrics)

        return new_state

    def get_consciousness_trend(self, time_window: float = 300.0) -> Dict[str, Any]:
        """
        Получить тренд изменения уровня сознания за указанный период.

        Args:
            time_window: Временное окно в секундах (по умолчанию 5 минут)

        Returns:
            Статистика тренда сознания
        """
        current_time = time.time()
        cutoff_time = current_time - time_window

        # Фильтруем историю по времени
        recent_snapshots = [
            s for s in self._consciousness_history
            if s.timestamp >= cutoff_time
        ]

        if not recent_snapshots:
            return {
                "trend": "insufficient_data",
                "average_level": self.BASELINE_CONSCIOUSNESS,
                "change_rate": 0.0,
                "samples": 0
            }

        # Рассчитываем статистику
        levels = [s.consciousness_level for s in recent_snapshots]
        timestamps = [s.timestamp for s in recent_snapshots]

        average_level = sum(levels) / len(levels)

        # Рассчитываем скорость изменения (уровень/секунду)
        if len(levels) >= 2:
            time_span = timestamps[-1] - timestamps[0]
            level_change = levels[-1] - levels[0]
            change_rate = level_change / time_span if time_span > 0 else 0.0
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
            "average_level": average_level,
            "change_rate": change_rate,
            "samples": len(recent_snapshots),
            "time_window": time_window
        }

    def _calculate_neural_activity(self, self_state, recent_events_count: int) -> float:
        """
        Рассчитать нейронную активность на основе частоты обработки событий.

        Args:
            self_state: Состояние системы
            recent_events_count: Количество недавних событий

        Returns:
            Уровень нейронной активности (0.0-1.0)
        """
        # Базовый уровень активности
        base_activity = 0.1

        # Влияние частоты тиков (если доступно)
        tick_frequency = getattr(self_state, 'tick_frequency', 1.0)
        tick_factor = min(1.0, tick_frequency / 10.0)  # Нормализация

        # Влияние количества событий
        event_factor = min(1.0, recent_events_count / 50.0)  # Нормализация

        # Влияние сложности решений (если доступно)
        complexity_factor = getattr(self_state, 'decision_complexity', 0.5)

        neural_activity = (
            base_activity * 0.3 +
            tick_factor * 0.3 +
            event_factor * 0.2 +
            complexity_factor * 0.2
        )

        return min(1.0, neural_activity)

    def _calculate_self_reflection(self, self_state, event_history: List) -> float:
        """
        Рассчитать уровень саморефлексии.

        Args:
            self_state: Состояние системы
            event_history: История событий

        Returns:
            Уровень саморефлексии (0.0-1.0)
        """
        # Используем кэшированное значение или рассчитываем новое
        if time.time() - self._last_calculation_time < 10.0:  # Кэш на 10 секунд
            return self._cached_self_reflection

        # Анализируем историю решений (заглушка для демонстрации)
        decision_history = getattr(self_state, 'decision_history', [])
        behavior_patterns = getattr(self_state, 'behavior_patterns', [])

        return self.assess_self_reflection(decision_history, behavior_patterns)

    def _calculate_meta_cognition(self, self_state, event_history: List) -> float:
        """
        Рассчитать глубину метакогниции.

        Args:
            self_state: Состояние системы
            event_history: История событий

        Returns:
            Глубина метакогниции (0.0-1.0)
        """
        # Используем кэшированное значение или рассчитываем новое
        if time.time() - self._last_calculation_time < 10.0:  # Кэш на 10 секунд
            return self._cached_meta_cognition

        # Анализируем когнитивные процессы (заглушка для демонстрации)
        cognitive_processes = getattr(self_state, 'cognitive_processes', [])
        optimization_history = getattr(self_state, 'optimization_history', [])

        return self.evaluate_meta_cognition(cognitive_processes, optimization_history)

    def _determine_consciousness_state(self, consciousness_level: float,
                                     energy: float, stability: float) -> str:
        """
        Определить состояние сознания на основе метрик.

        Args:
            consciousness_level: Уровень сознания
            energy: Уровень энергии
            stability: Уровень стабильности

        Returns:
            Название состояния
        """
        metrics = {
            'consciousness_level': consciousness_level,
            'energy': energy,
            'stability': stability
        }
        return self.determine_consciousness_state(metrics)

    def _analyze_behavior_patterns(self, behavior_patterns: List[Dict]) -> float:
        """Анализировать качество распознавания паттернов поведения."""
        if not behavior_patterns:
            return 0.0
        # Заглушка: возвращаем среднее качество паттернов
        return sum(p.get('quality', 0.5) for p in behavior_patterns) / len(behavior_patterns)

    def _evaluate_decision_quality(self, decision_history: List[Dict]) -> float:
        """Оценивать качество принятых решений."""
        if not decision_history:
            return 0.0
        # Заглушка: возвращаем средний success rate
        return sum(d.get('success', False) for d in decision_history) / len(decision_history)

    def _assess_pattern_recognition(self, behavior_patterns: List[Dict]) -> float:
        """Оценивать способность к распознаванию паттернов."""
        if not behavior_patterns:
            return 0.0
        # Заглушка: оцениваем по количеству и разнообразию паттернов
        pattern_count = len(behavior_patterns)
        diversity = len(set(p.get('type', 'unknown') for p in behavior_patterns))
        return min(1.0, (pattern_count + diversity) / 20.0)

    def _measure_process_awareness(self, cognitive_processes: List[Dict]) -> float:
        """Измерить осознанность когнитивных процессов."""
        if not cognitive_processes:
            return 0.0
        # Заглушка: оцениваем по количеству отслеживаемых процессов
        return min(1.0, len(cognitive_processes) / 10.0)

    def _assess_optimization_capability(self, optimization_history: List[Dict]) -> float:
        """Оценить способность к самооптимизации."""
        if not optimization_history:
            return 0.0
        # Заглушка: оцениваем по количеству успешных оптимизаций
        success_count = sum(1 for opt in optimization_history if opt.get('success', False))
        return success_count / len(optimization_history)

    def _evaluate_abstract_reasoning(self, cognitive_processes: List[Dict]) -> float:
        """Оценить способность к абстрактному мышлению."""
        if not cognitive_processes:
            return 0.0
        # Заглушка: ищем признаки абстрактного мышления
        abstract_indicators = sum(1 for proc in cognitive_processes
                                if proc.get('type') in ['generalization', 'abstraction', 'concept_formation'])
        return min(1.0, abstract_indicators / 5.0)

    def _calculate_silence_consciousness_factor(self, event_history: List) -> float:
        """
        Рассчитать влияние осознания тишины на уровень сознания.

        Тишина способствует повышению осознанности, особенно комфортная тишина.

        Args:
            event_history: История недавних событий

        Returns:
            Фактор влияния тишины на сознание (0.0-1.0)
        """
        if not event_history:
            return 0.0

        # Ищем события silence в недавней истории
        silence_events = [event for event in event_history if event.type == "silence"]

        if not silence_events:
            return 0.0

        # Рассчитываем среднюю интенсивность событий silence
        # Положительная интенсивность (комфортная тишина) повышает сознание
        # Отрицательная интенсивность (тревожная тишина) меньше влияет
        silence_intensities = [event.intensity for event in silence_events]
        avg_silence_intensity = sum(silence_intensities) / len(silence_intensities)

        # Преобразуем интенсивность в фактор сознания
        # Положительная тишина дает бонус, отрицательная - минимальное влияние
        if avg_silence_intensity > 0:
            silence_factor = min(1.0, avg_silence_intensity * 0.8)  # Умеренный бонус
        else:
            silence_factor = max(0.0, -avg_silence_intensity * 0.3)  # Слабое влияние тревожной тишины

        # Учитываем количество событий silence (больше событий = сильнее влияние)
        event_count_factor = min(1.0, len(silence_events) / 5.0)  # Нормализация

        return silence_factor * event_count_factor

    def _add_to_history(self, snapshot: ConsciousnessSnapshot) -> None:
        """Добавить снимок в историю."""
        self._consciousness_history.append(snapshot)

        # Ограничиваем размер истории
        if len(self._consciousness_history) > self.MAX_CONSCIOUSNESS_HISTORY:
            self._consciousness_history = self._consciousness_history[-self.MAX_CONSCIOUSNESS_HISTORY:]

    def _update_performance_metrics(self, calculation_time: float) -> None:
        """Обновить метрики производительности."""
        self._calculation_count += 1

        # Экспоненциальное сглаживание среднего времени
        alpha = 0.1
        if self._average_calculation_time == 0:
            self._average_calculation_time = calculation_time
        else:
            self._average_calculation_time = (
                alpha * calculation_time + (1 - alpha) * self._average_calculation_time
            )

    def _log_consciousness_change(self, snapshot: ConsciousnessSnapshot) -> None:
        """Логировать изменение уровня сознания."""
        self.logger.log_event({
            "event_type": "consciousness_level_updated",
            "consciousness_level": snapshot.consciousness_level,
            "self_reflection_score": snapshot.self_reflection_score,
            "meta_cognition_depth": snapshot.meta_cognition_depth,
            "current_state": snapshot.current_state,
            "neural_activity": snapshot.neural_activity,
            "energy_level": snapshot.energy_level,
            "stability": snapshot.stability,
            "recent_events_count": snapshot.recent_events_count
        })

    def _log_state_transition(self, old_state: str, new_state: str, metrics: Dict[str, float]) -> None:
        """Логировать переход между состояниями сознания."""
        self.logger.log_event({
            "event_type": "consciousness_state_transition",
            "from_state": old_state,
            "to_state": new_state,
            "consciousness_level": metrics.get('consciousness_level', 0.0),
            "energy": metrics.get('energy', 0.5),
            "stability": metrics.get('stability', 0.5),
            "reason": "automatic_transition"
        })

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Получить статистику производительности движка сознания.

        Returns:
            Статистика производительности
        """
        return {
            "calculation_count": self._calculation_count,
            "average_calculation_time": self._average_calculation_time,
            "history_size": len(self._consciousness_history),
            "cache_hit_rate": 0.0  # Заглушка, можно реализовать позже
        }

    def reset_engine(self) -> None:
        """Сбросить состояние движка сознания."""
        self._consciousness_history.clear()
        self._last_calculation_time = time.time()
        self._state_change_cooldown = 0
        self._cached_consciousness_level = self.BASELINE_CONSCIOUSNESS
        self._cached_self_reflection = 0.0
        self._cached_meta_cognition = 0.0
        self._calculation_count = 0
        self._average_calculation_time = 0.0

        self.logger.log_event({
            "event_type": "consciousness_engine_reset"
        })
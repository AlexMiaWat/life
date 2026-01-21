"""
Анализатор качества адаптации системы Life.

Модуль анализирует эффективность и стабильность адаптационных процессов,
способность к предсказанию и общее качество адаптации.
"""

import logging
from typing import TYPE_CHECKING, Dict, List

from .metrics import AdaptationQualityMetrics

if TYPE_CHECKING:
    from src.state.self_state import SelfState
    from src.adaptation.adaptation import AdaptationManager
    from src.learning.learning import LearningEngine

logger = logging.getLogger(__name__)


class AdaptationQualityAnalyzer:
    """
    Анализатор качества адаптации.

    Анализирует:
    - Эффективность адаптации к изменениям
    - Стабильность адаптационных изменений
    - Скорость адаптации
    - Качество предсказания будущих состояний
    """

    def __init__(self):
        """Инициализация анализатора качества адаптации."""
        self.history_window = 50  # Окно анализа для трендов

    def analyze_adaptation_quality(
        self,
        self_state: 'SelfState',
        adaptation_manager: 'AdaptationManager',
        learning_engine: 'LearningEngine'
    ) -> AdaptationQualityMetrics:
        """
        Проанализировать качество адаптации.

        Args:
            self_state: Текущее состояние системы
            adaptation_manager: Менеджер адаптации
            learning_engine: Движок обучения

        Returns:
            AdaptationQualityMetrics: Метрики качества адаптации
        """
        metrics = AdaptationQualityMetrics()

        # Анализ эффективности адаптации
        metrics.adaptation_effectiveness = self._analyze_adaptation_effectiveness(
            self_state, adaptation_manager
        )

        # Анализ стабильности адаптации
        metrics.adaptation_stability = self._analyze_adaptation_stability(
            adaptation_manager
        )

        # Анализ скорости адаптации
        metrics.adaptation_speed = self._analyze_adaptation_speed(
            adaptation_manager
        )

        # Анализ качества предсказания
        metrics.predictive_quality = self._analyze_predictive_quality(
            self_state, learning_engine
        )

        # Вычисление общего качества адаптации
        metrics.overall_adaptation_quality = self._calculate_overall_adaptation_quality(metrics)

        # Добавление в историю параметров
        current_params = self._get_current_adaptation_params(adaptation_manager)
        metrics.parameter_history.append(current_params)

        # Ограничение размера истории
        if len(metrics.parameter_history) > self.history_window:
            metrics.parameter_history = metrics.parameter_history[-self.history_window:]

        return metrics

    def _analyze_adaptation_effectiveness(
        self,
        self_state: 'SelfState',
        adaptation_manager: 'AdaptationManager'
    ) -> float:
        """
        Анализировать эффективность адаптации к изменениям.

        Args:
            self_state: Состояние системы
            adaptation_manager: Менеджер адаптации

        Returns:
            float: Эффективность адаптации (0.0 - 1.0)
        """
        effectiveness_score = 0.0
        factors_count = 0

        # Фактор 1: Способность поддерживать стабильность при изменениях
        try:
            if hasattr(self_state, 'stability_history') and len(self_state.stability_history) > 5:
                recent_stability = self_state.stability_history[-5:]
                stability_variance = sum((x - sum(recent_stability)/len(recent_stability))**2 for x in recent_stability) / len(recent_stability)

                # Низкая дисперсия = высокая стабильность
                if stability_variance < 0.01:
                    effectiveness_score += 0.4
                elif stability_variance < 0.05:
                    effectiveness_score += 0.2
                else:
                    effectiveness_score += 0.1
                factors_count += 1
        except Exception:
            effectiveness_score += 0.05
            factors_count += 1

        # Фактор 2: Адаптация к уровню энергии
        try:
            if hasattr(self_state, 'energy'):
                energy_level = self_state.energy
                # Система должна адаптироваться к низкому уровню энергии
                if energy_level < 30 and hasattr(self_state, 'stability') and self_state.stability > 0.5:
                    effectiveness_score += 0.3  # Способна поддерживать стабильность при низкой энергии
                elif energy_level > 70:
                    effectiveness_score += 0.2  # Хорошо функционирует при высокой энергии
                else:
                    effectiveness_score += 0.1
                factors_count += 1
        except Exception:
            effectiveness_score += 0.05
            factors_count += 1

        # Фактор 3: История адаптаций
        try:
            adaptation_history = getattr(adaptation_manager, 'adaptation_history', [])
            if len(adaptation_history) > 10:
                effectiveness_score += 0.3
            elif len(adaptation_history) > 5:
                effectiveness_score += 0.15
            else:
                effectiveness_score += 0.05
            factors_count += 1
        except Exception:
            effectiveness_score += 0.05
            factors_count += 1

        return effectiveness_score / max(factors_count, 1)

    def _analyze_adaptation_stability(self, adaptation_manager: 'AdaptationManager') -> float:
        """
        Анализировать стабильность адаптационных изменений.

        Args:
            adaptation_manager: Менеджер адаптации

        Returns:
            float: Стабильность адаптации (0.0 - 1.0)
        """
        stability_score = 0.0
        factors_count = 0

        # Фактор 1: Размер изменений параметров
        try:
            # Проверяем, что изменения не слишком резкие
            adaptation_params = getattr(adaptation_manager, 'adaptation_params', {})
            max_change = 0.0

            for param_name, param_value in adaptation_params.items():
                if isinstance(param_value, (int, float)):
                    # Проверяем историю изменений для этого параметра
                    history = getattr(adaptation_manager, 'adaptation_history', [])
                    if len(history) > 1:
                        recent_changes = [h.get(param_name, param_value) for h in history[-3:]]
                        if recent_changes:
                            param_changes = [abs(recent_changes[i] - recent_changes[i-1])
                                           for i in range(1, len(recent_changes))]
                            if param_changes:
                                max_change = max(max_change, max(param_changes))

            # Оцениваем стабильность на основе максимального изменения
            if max_change < 0.01:  # Очень стабильные изменения
                stability_score += 0.4
            elif max_change < 0.05:  # Стабильные изменения
                stability_score += 0.2
            else:  # Резкие изменения
                stability_score += 0.05
            factors_count += 1

        except Exception:
            stability_score += 0.1
            factors_count += 1

        # Фактор 2: Частота адаптаций
        try:
            history = getattr(adaptation_manager, 'adaptation_history', [])
            if len(history) > 20:
                # Слишком частые адаптации могут указывать на нестабильность
                stability_score += 0.3
            elif len(history) > 10:
                stability_score += 0.2
            elif len(history) > 5:
                stability_score += 0.1
            else:
                stability_score += 0.05
            factors_count += 1
        except Exception:
            stability_score += 0.05
            factors_count += 1

        # Фактор 3: Консистентность направления изменений
        try:
            history = getattr(adaptation_manager, 'adaptation_history', [])
            if len(history) > 5:
                # Анализируем направление последних изменений
                consistent_direction = 0
                total_params = 0

                for param_name in ['behavior_sensitivity', 'behavior_thresholds', 'behavior_coefficients']:
                    param_history = [h.get(param_name) for h in history[-5:] if h.get(param_name) is not None]
                    if len(param_history) > 2:
                        total_params += 1
                        # Проверяем консистентность направления (не слишком частые смены)
                        direction_changes = 0
                        for i in range(2, len(param_history)):
                            prev_diff = param_history[i-1] - param_history[i-2]
                            curr_diff = param_history[i] - param_history[i-1]
                            if (prev_diff > 0) != (curr_diff > 0):  # Смена направления
                                direction_changes += 1

                        if direction_changes <= 1:  # Максимум одна смена направления
                            consistent_direction += 1

                if total_params > 0:
                    consistency_ratio = consistent_direction / total_params
                    stability_score += 0.3 * consistency_ratio
                factors_count += 1
        except Exception:
            stability_score += 0.05
            factors_count += 1

        return stability_score / max(factors_count, 1)

    def _analyze_adaptation_speed(self, adaptation_manager: 'AdaptationManager') -> float:
        """
        Анализировать скорость адаптации.

        Args:
            adaptation_manager: Менеджер адаптации

        Returns:
            float: Скорость адаптации (0.0 - 1.0, нормализованная)
        """
        speed_score = 0.0

        try:
            history = getattr(adaptation_manager, 'adaptation_history', [])
            if len(history) < 2:
                return 0.1  # Недостаточно данных

            # Вычисляем среднюю скорость изменений
            total_changes = 0
            total_params = 0

            for param_name in ['behavior_sensitivity', 'behavior_thresholds', 'behavior_coefficients']:
                param_history = [h.get(param_name) for h in history if h.get(param_name) is not None]
                if len(param_history) > 1:
                    total_params += 1
                    changes = sum(abs(param_history[i] - param_history[i-1])
                                for i in range(1, len(param_history)))
                    total_changes += changes / len(param_history)  # Среднее изменение

            if total_params > 0:
                avg_change = total_changes / total_params

                # Нормализуем скорость: оптимальная скорость - умеренная
                if 0.001 <= avg_change <= 0.01:  # Оптимальный диапазон
                    speed_score = 0.8
                elif 0.0001 <= avg_change < 0.001:  # Слишком медленно
                    speed_score = 0.4
                elif 0.01 < avg_change <= 0.05:  # Довольно быстро
                    speed_score = 0.6
                else:  # Слишком быстро или отсутствуют изменения
                    speed_score = 0.2
            else:
                speed_score = 0.1

        except Exception:
            speed_score = 0.1

        return speed_score

    def _analyze_predictive_quality(
        self,
        self_state: 'SelfState',
        learning_engine: 'LearningEngine'
    ) -> float:
        """
        Анализировать качество предсказания будущих состояний.

        Args:
            self_state: Состояние системы
            learning_engine: Движок обучения

        Returns:
            float: Качество предсказания (0.0 - 1.0)
        """
        predictive_score = 0.0
        factors_count = 0

        # Фактор 1: Качество статистики learning
        try:
            learning_stats = getattr(learning_engine, 'learning_statistics', {})
            if learning_stats:
                # Проверяем разнообразие собранной статистики
                stats_keys = learning_stats.keys()
                if len(stats_keys) > 10:
                    predictive_score += 0.3
                elif len(stats_keys) > 5:
                    predictive_score += 0.2
                else:
                    predictive_score += 0.1
                factors_count += 1
        except Exception:
            predictive_score += 0.05
            factors_count += 1

        # Фактор 2: Способность предсказывать изменения состояния
        try:
            if hasattr(self_state, 'energy_history') and len(self_state.energy_history) > 10:
                # Анализируем паттерны в истории энергии
                recent = self_state.energy_history[-10:]
                if len(recent) >= 5:
                    # Вычисляем тренд
                    trend = sum((recent[i] - recent[i-1]) for i in range(1, len(recent))) / (len(recent) - 1)

                    # Если есть предсказуемый тренд (не случайные колебания)
                    if abs(trend) > 1.0:  # Значимый тренд
                        predictive_score += 0.3
                    elif abs(trend) > 0.5:
                        predictive_score += 0.2
                    else:
                        predictive_score += 0.1
                    factors_count += 1
        except Exception:
            predictive_score += 0.05
            factors_count += 1

        # Фактор 3: Использование planning для предсказания
        try:
            if hasattr(self_state, 'planning') and self_state.planning:
                planning_complexity = len(str(self_state.planning))
                if planning_complexity > 100:
                    predictive_score += 0.4
                elif planning_complexity > 50:
                    predictive_score += 0.2
                else:
                    predictive_score += 0.1
                factors_count += 1
        except Exception:
            predictive_score += 0.05
            factors_count += 1

        return predictive_score / max(factors_count, 1)

    def _calculate_overall_adaptation_quality(self, metrics: AdaptationQualityMetrics) -> float:
        """
        Вычислить общее качество адаптации.

        Args:
            metrics: Индивидуальные метрики адаптации

        Returns:
            float: Общее качество адаптации (0.0 - 1.0)
        """
        weights = {
            'effectiveness': 0.35,
            'stability': 0.30,
            'speed': 0.20,
            'predictive_quality': 0.15
        }

        overall_score = (
            metrics.adaptation_effectiveness * weights['effectiveness'] +
            metrics.adaptation_stability * weights['stability'] +
            metrics.adaptation_speed * weights['speed'] +
            metrics.predictive_quality * weights['predictive_quality']
        )

        return min(overall_score, 1.0)

    def _get_current_adaptation_params(self, adaptation_manager: 'AdaptationManager') -> Dict:
        """
        Получить текущие параметры адаптации.

        Args:
            adaptation_manager: Менеджер адаптации

        Returns:
            Dict: Текущие параметры адаптации
        """
        try:
            params = getattr(adaptation_manager, 'adaptation_params', {}).copy()
            params['timestamp'] = getattr(adaptation_manager, '_last_adaptation_time', None)
            return params
        except Exception:
            return {'error': 'unable_to_get_params'}
"""
Оценщик жизненности поведения системы Life.

Модуль оценивает общую "живость" и витальность поведения системы,
включая энергичность, адаптивность, внутреннюю гармонию и потенциал развития.
"""

import logging
from typing import TYPE_CHECKING, Dict, List

from .metrics import LifeVitalityMetrics

if TYPE_CHECKING:
    from src.state.self_state import SelfState
    from src.memory.memory import Memory
    from src.adaptation.adaptation import AdaptationManager
    from src.learning.learning import LearningEngine

logger = logging.getLogger(__name__)


class LifeVitalityEvaluator:
    """
    Оценщик жизненности поведения.

    Оценивает:
    - Энергичность и активность системы
    - Адаптивность к окружающей среде
    - Внутреннюю гармонию и баланс
    - Потенциал развития и роста
    """

    def __init__(self):
        """Инициализация оценщика жизненности."""
        self.vitality_history_window = 25  # Окно анализа трендов жизненности

    def evaluate_life_vitality(
        self,
        self_state: 'SelfState',
        memory: 'Memory',
        adaptation_manager: 'AdaptationManager',
        learning_engine: 'LearningEngine'
    ) -> LifeVitalityMetrics:
        """
        Оценить жизненность поведения системы.

        Args:
            self_state: Текущее состояние системы
            memory: Память системы
            adaptation_manager: Менеджер адаптации
            learning_engine: Движок обучения

        Returns:
            LifeVitalityMetrics: Метрики жизненности
        """
        metrics = LifeVitalityMetrics()

        # Оценка энергичности и активности
        metrics.vitality_level = self._evaluate_vitality_level(self_state, memory)

        # Оценка адаптивности к среде
        metrics.environmental_adaptability = self._evaluate_environmental_adaptability(
            self_state, adaptation_manager
        )

        # Оценка внутренней гармонии
        metrics.internal_harmony = self._evaluate_internal_harmony(self_state)

        # Оценка потенциала развития
        metrics.developmental_potential = self._evaluate_developmental_potential(
            learning_engine, memory
        )

        # Вычисление общей жизненности
        metrics.overall_vitality = self._calculate_overall_vitality(metrics)

        # Добавление в историю трендов
        current_trend = self._get_current_vitality_trend(metrics)
        metrics.vitality_trends.append(current_trend)

        # Ограничение размера истории
        if len(metrics.vitality_trends) > self.vitality_history_window:
            metrics.vitality_trends = metrics.vitality_trends[-self.vitality_history_window:]

        return metrics

    def _evaluate_vitality_level(self, self_state: 'SelfState', memory: 'Memory') -> float:
        """
        Оценить уровень энергичности и активности.

        Args:
            self_state: Состояние системы
            memory: Память системы

        Returns:
            float: Уровень энергичности (0.0 - 1.0)
        """
        vitality_score = 0.0
        factors_count = 0

        # Фактор 1: Уровень энергии
        try:
            if hasattr(self_state, 'energy'):
                energy = self_state.energy
                if energy > 70:
                    vitality_score += 0.3
                elif energy > 40:
                    vitality_score += 0.2
                elif energy > 10:
                    vitality_score += 0.1
                else:
                    vitality_score += 0.05
                factors_count += 1
        except Exception:
            vitality_score += 0.1
            factors_count += 1

        # Фактор 2: Активность (количество действий)
        try:
            # Оцениваем активность по количеству записей в памяти
            memory_stats = memory.get_statistics()
            total_entries = memory_stats.get('total_entries', 0)

            if total_entries > 200:
                vitality_score += 0.3
            elif total_entries > 100:
                vitality_score += 0.2
            elif total_entries > 50:
                vitality_score += 0.15
            elif total_entries > 20:
                vitality_score += 0.1
            else:
                vitality_score += 0.05
            factors_count += 1

        except Exception:
            vitality_score += 0.1
            factors_count += 1

        # Фактор 3: Разнообразие активности
        try:
            # Оцениваем разнообразие по статистике памяти
            memory_stats = memory.get_statistics()
            event_types = memory_stats.get('event_types', {})

            # Вычисляем разнообразие типов событий
            event_diversity = min(len(event_types) / 8, 1.0)  # Ожидаем до 8 типов событий

            if event_diversity > 0.5:
                vitality_score += 0.4
            elif event_diversity > 0.3:
                vitality_score += 0.25
            elif event_diversity > 0.1:
                vitality_score += 0.15
            else:
                vitality_score += 0.05

            factors_count += 1

        except Exception as e:
            logger.debug(f"Не удалось оценить разнообразие активности: {e}")
            vitality_score += 0.05
            factors_count += 1

        return vitality_score / max(factors_count, 1)

    def _evaluate_environmental_adaptability(
        self,
        self_state: 'SelfState',
        adaptation_manager: 'AdaptationManager'
    ) -> float:
        """
        Оценить адаптивность к окружающей среде.

        Args:
            self_state: Состояние системы
            adaptation_manager: Менеджер адаптации

        Returns:
            float: Уровень адаптивности (0.0 - 1.0)
        """
        adaptability_score = 0.0
        factors_count = 0

        # Фактор 1: Способность поддерживать стабильность
        try:
            if hasattr(self_state, 'stability'):
                stability = self_state.stability
                if stability > 0.8:
                    adaptability_score += 0.3
                elif stability > 0.6:
                    adaptability_score += 0.2
                elif stability > 0.4:
                    adaptability_score += 0.15
                else:
                    adaptability_score += 0.05
                factors_count += 1
        except Exception:
            adaptability_score += 0.1
            factors_count += 1

        # Фактор 2: История адаптаций
        try:
            adaptation_history = getattr(adaptation_manager, 'adaptation_history', [])
            if len(adaptation_history) > 10:
                adaptability_score += 0.3
            elif len(adaptation_history) > 5:
                adaptability_score += 0.2
            elif len(adaptation_history) > 2:
                adaptability_score += 0.1
            else:
                adaptability_score += 0.05
            factors_count += 1
        except Exception:
            adaptability_score += 0.1
            factors_count += 1

        # Фактор 3: Гибкость параметров адаптации
        try:
            adaptation_params = getattr(adaptation_manager, 'adaptation_params', {})
            if adaptation_params:
                # Оцениваем разнообразие параметров адаптации
                param_count = len([p for p in adaptation_params.values() if isinstance(p, (int, float))])
                if param_count > 5:
                    adaptability_score += 0.4
                elif param_count > 3:
                    adaptability_score += 0.3
                elif param_count > 1:
                    adaptability_score += 0.2
                else:
                    adaptability_score += 0.1
                factors_count += 1
        except Exception:
            adaptability_score += 0.1
            factors_count += 1

        return adaptability_score / max(factors_count, 1)

    def _evaluate_internal_harmony(self, self_state: 'SelfState') -> float:
        """
        Оценить внутреннюю гармонию и баланс.

        Args:
            self_state: Состояние системы

        Returns:
            float: Уровень внутренней гармонии (0.0 - 1.0)
        """
        harmony_score = 0.0
        factors_count = 0

        # Фактор 1: Баланс между параметрами состояния
        try:
            # Проверяем гармоничное сочетание энергии, целостности и стабильности
            energy = getattr(self_state, 'energy', 50)
            integrity = getattr(self_state, 'integrity', 1.0)
            stability = getattr(self_state, 'stability', 1.0)

            # Вычисляем баланс (все параметры в оптимальных диапазонах)
            balance_score = 0.0

            # Энергия: оптимально 40-80
            if 40 <= energy <= 80:
                balance_score += 1.0
            elif 20 <= energy <= 90:
                balance_score += 0.7
            else:
                balance_score += 0.3

            # Целостность: оптимально > 0.7
            if integrity > 0.7:
                balance_score += 1.0
            elif integrity > 0.5:
                balance_score += 0.7
            else:
                balance_score += 0.3

            # Стабильность: оптимально > 0.7
            if stability > 0.7:
                balance_score += 1.0
            elif stability > 0.5:
                balance_score += 0.7
            else:
                balance_score += 0.3

            harmony_score += 0.4 * (balance_score / 3.0)
            factors_count += 1

        except Exception:
            harmony_score += 0.2
            factors_count += 1

        # Фактор 2: Управление стрессом и усталостью
        try:
            fatigue = getattr(self_state, 'fatigue', 50)  # Значение по умолчанию
            tension = getattr(self_state, 'tension', 50)  # Значение по умолчанию

            # Оцениваем способность справляться со стрессом
            # Нормализуем значения (предполагаем диапазон 0-100)
            normalized_fatigue = min(fatigue / 100.0, 1.0)
            normalized_tension = min(tension / 100.0, 1.0)

            stress_level = (normalized_fatigue + normalized_tension) / 2

            # Гармония выше при низком стрессе
            if stress_level < 0.4:  # Менее 40% от максимума
                harmony_score += 0.3
            elif stress_level < 0.6:
                harmony_score += 0.2
            elif stress_level < 0.8:
                harmony_score += 0.1
            else:
                harmony_score += 0.05
            factors_count += 1

        except Exception:
            harmony_score += 0.1
            factors_count += 1

        # Фактор 3: Консистентность временных соотношений
        try:
            if hasattr(self_state, 'age') and hasattr(self_state, 'subjective_time'):
                age = self_state.age
                subjective_time = self_state.subjective_time

                if age > 0:
                    time_ratio = subjective_time / age
                    # Гармоничное соотношение физического и субъективного времени
                    if 0.5 <= time_ratio <= 2.0:
                        harmony_score += 0.3
                    elif 0.2 <= time_ratio <= 5.0:
                        harmony_score += 0.2
                    else:
                        harmony_score += 0.1
                    factors_count += 1

        except Exception:
            harmony_score += 0.1
            factors_count += 1

        return harmony_score / max(factors_count, 1)

    def _evaluate_developmental_potential(
        self,
        learning_engine: 'LearningEngine',
        memory: 'Memory'
    ) -> float:
        """
        Оценить потенциал развития и роста.

        Args:
            learning_engine: Движок обучения
            memory: Память системы

        Returns:
            float: Потенциал развития (0.0 - 1.0)
        """
        potential_score = 0.0
        factors_count = 0

        # Фактор 1: Активность обучения
        try:
            learning_stats = getattr(learning_engine, 'learning_statistics', {})
            if learning_stats:
                # Оцениваем объем накопленных знаний
                total_experience = sum(learning_stats.values())
                if total_experience > 200:
                    potential_score += 0.3
                elif total_experience > 100:
                    potential_score += 0.2
                elif total_experience > 50:
                    potential_score += 0.15
                elif total_experience > 10:
                    potential_score += 0.1
                else:
                    potential_score += 0.05
                factors_count += 1
        except Exception:
            potential_score += 0.1
            factors_count += 1

        # Фактор 2: Способность к изменениям
        try:
            parameter_history = getattr(learning_engine, 'parameter_history', [])
            if len(parameter_history) > 5:
                # Есть история развития параметров
                potential_score += 0.3
            elif len(parameter_history) > 2:
                potential_score += 0.2
            else:
                potential_score += 0.1
            factors_count += 1
        except Exception:
            potential_score += 0.1
            factors_count += 1

        # Фактор 3: Накопление опыта в памяти
        try:
            memory_stats = memory.get_statistics()
            archived_entries = memory_stats.get('archived_entries', 0)

            # Архивная память указывает на способность к долгосрочному развитию
            if archived_entries > 50:
                potential_score += 0.4
            elif archived_entries > 20:
                potential_score += 0.3
            elif archived_entries > 10:
                potential_score += 0.2
            elif archived_entries > 0:
                potential_score += 0.1
            else:
                potential_score += 0.05
            factors_count += 1

        except Exception:
            potential_score += 0.1
            factors_count += 1

        return potential_score / max(factors_count, 1)

    def _calculate_overall_vitality(self, metrics: LifeVitalityMetrics) -> float:
        """
        Вычислить общую жизненность.

        Args:
            metrics: Индивидуальные метрики жизненности

        Returns:
            float: Общая жизненность (0.0 - 1.0)
        """
        weights = {
            'vitality_level': 0.25,
            'environmental_adaptability': 0.25,
            'internal_harmony': 0.25,
            'developmental_potential': 0.25
        }

        overall_score = (
            metrics.vitality_level * weights['vitality_level'] +
            metrics.environmental_adaptability * weights['environmental_adaptability'] +
            metrics.internal_harmony * weights['internal_harmony'] +
            metrics.developmental_potential * weights['developmental_potential']
        )

        return min(overall_score, 1.0)

    def _get_current_vitality_trend(self, metrics: LifeVitalityMetrics) -> Dict:
        """
        Получить текущий тренд жизненности.

        Args:
            metrics: Метрики жизненности

        Returns:
            Dict: Текущий тренд
        """
        import time
        return {
            'timestamp': time.time(),
            'vitality_level': metrics.vitality_level,
            'environmental_adaptability': metrics.environmental_adaptability,
            'internal_harmony': metrics.internal_harmony,
            'developmental_potential': metrics.developmental_potential,
            'overall_vitality': metrics.overall_vitality
        }
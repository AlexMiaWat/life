"""
Анализатор этического поведения системы Life.

Модуль анализирует поведение системы с точки зрения этических принципов,
включая соблюдение норм, осознание последствий и разрешение этических дилемм.
"""

import logging
from typing import TYPE_CHECKING, Dict, List

from .metrics import EthicalBehaviorMetrics

if TYPE_CHECKING:
    from src.state.self_state import SelfState
    from src.memory.memory import Memory
    from src.decision.decision import DecisionEngine

logger = logging.getLogger(__name__)


class EthicalBehaviorAnalyzer:
    """
    Анализатор этического поведения.

    Анализирует:
    - Соблюдение внутренних норм и правил
    - Осознание последствий действий
    - Этическую последовательность
    - Способность к разрешению этических дилемм
    """

    def __init__(self):
        """Инициализация анализатора этического поведения."""
        self.decision_history_window = 20  # Окно анализа решений

    def analyze_ethical_behavior(
        self,
        self_state: 'SelfState',
        memory: 'Memory',
        decision_engine: 'DecisionEngine'
    ) -> EthicalBehaviorMetrics:
        """
        Проанализировать этическое поведение системы.

        Args:
            self_state: Текущее состояние системы
            memory: Память системы
            decision_engine: Движок принятия решений

        Returns:
            EthicalBehaviorMetrics: Метрики этического поведения
        """
        metrics = EthicalBehaviorMetrics()

        # Анализ соблюдения норм
        metrics.norm_compliance = self._analyze_norm_compliance(self_state, memory)

        # Анализ осознания последствий
        metrics.consequence_awareness = self._analyze_consequence_awareness(memory, decision_engine)

        # Анализ этической последовательности
        metrics.ethical_consistency = self._analyze_ethical_consistency(memory)

        # Анализ разрешения дилемм
        metrics.dilemma_resolution = self._analyze_dilemma_resolution(decision_engine)

        # Вычисление общего этического уровня
        metrics.overall_ethical_score = self._calculate_overall_ethical_score(metrics)

        # Добавление в историю решений
        current_decision = self._get_current_ethical_decision(memory)
        if current_decision:
            metrics.ethical_decisions_history.append(current_decision)

        # Ограничение размера истории
        if len(metrics.ethical_decisions_history) > self.decision_history_window:
            metrics.ethical_decisions_history = metrics.ethical_decisions_history[-self.decision_history_window:]

        return metrics

    def _analyze_norm_compliance(self, self_state: 'SelfState', memory: 'Memory') -> float:
        """
        Анализировать соблюдение внутренних норм.

        Args:
            self_state: Состояние системы
            memory: Память системы

        Returns:
            float: Уровень соблюдения норм (0.0 - 1.0)
        """
        compliance_score = 0.0
        factors_count = 0

        # Фактор 1: Соблюдение жизненно важных параметров
        try:
            # Проверка поддержания энергии в разумных пределах
            if hasattr(self_state, 'energy'):
                energy = self_state.energy
                if 10 <= energy <= 90:  # Соблюдение нормы энергии
                    compliance_score += 0.25
                elif 0 <= energy <= 100:  # Хотя бы в допустимых пределах
                    compliance_score += 0.1
                factors_count += 1

            # Проверка целостности
            if hasattr(self_state, 'integrity'):
                integrity = self_state.integrity
                if integrity > 0.5:  # Поддержание хорошей целостности
                    compliance_score += 0.25
                elif integrity > 0.2:
                    compliance_score += 0.1
                factors_count += 1

            # Проверка стабильности
            if hasattr(self_state, 'stability'):
                stability = self_state.stability
                if stability > 0.5:  # Поддержание стабильности
                    compliance_score += 0.25
                elif stability > 0.2:
                    compliance_score += 0.1
                factors_count += 1

        except Exception:
            compliance_score += 0.05
            factors_count += 1

        # Фактор 2: Избегание экстремальных состояний
        try:
            fatigue = getattr(self_state, 'fatigue', 0)
            tension = getattr(self_state, 'tension', 0)

            # Нормальные уровни усталости и напряжения
            if fatigue < 70 and tension < 70:
                compliance_score += 0.25
            elif fatigue < 85 and tension < 85:
                compliance_score += 0.15
            else:
                compliance_score += 0.05
            factors_count += 1

        except Exception:
            compliance_score += 0.05
            factors_count += 1

        return compliance_score / max(factors_count, 1)

    def _analyze_consequence_awareness(self, memory: 'Memory', decision_engine: 'DecisionEngine') -> float:
        """
        Анализировать осознание последствий действий.

        Args:
            memory: Память системы
            decision_engine: Движок принятия решений

        Returns:
            float: Уровень осознания последствий (0.0 - 1.0)
        """
        awareness_score = 0.0
        factors_count = 0

        # Фактор 1: Анализ паттернов в памяти (причина-следствие)
        try:
            memory_stats = memory.get_statistics()
            total_entries = memory_stats.get('total_entries', 0)

            if total_entries > 100:
                awareness_score += 0.3  # Большой объем памяти позволяет анализировать последствия
            elif total_entries > 50:
                awareness_score += 0.2
            elif total_entries > 20:
                awareness_score += 0.1
            else:
                awareness_score += 0.05
            factors_count += 1

        except Exception:
            awareness_score += 0.05
            factors_count += 1

        # Фактор 2: Способность к планированию (предвидение последствий)
        try:
            # Проверяем сложность планирования как индикатор предвидения
            planning_complexity = 0
            if hasattr(decision_engine, '_planning_engine'):
                planning_engine = getattr(decision_engine, '_planning_engine', None)
                if planning_engine:
                    # Предполагаем, что сложность планирования коррелирует с осознанием
                    planning_complexity = 0.2

            if planning_complexity > 0:
                awareness_score += 0.3
            else:
                awareness_score += 0.1
            factors_count += 1

        except Exception:
            awareness_score += 0.1
            factors_count += 1

        # Фактор 3: Анализ обратной связи от действий
        try:
            # Ищем паттерны положительной/отрицательной обратной связи
            feedback_patterns = 0

            # Анализируем недавние события на наличие обратной связи
            try:
                recent_events = getattr(memory, '_active_memory', [])
                if recent_events:
                    positive_feedback = 0
                    negative_feedback = 0

                    for event in recent_events[-10:]:  # Последние 10 событий
                        significance = getattr(event, 'significance', 0)
                        if significance > 0.5:
                            positive_feedback += 1
                        elif significance < -0.5:
                            negative_feedback += 1

                    if positive_feedback > 0 or negative_feedback > 0:
                        feedback_patterns = min((positive_feedback + negative_feedback) / 5, 1.0)
                        awareness_score += 0.4 * feedback_patterns
                    else:
                        awareness_score += 0.1
                else:
                    awareness_score += 0.05

            except Exception:
                awareness_score += 0.05

            factors_count += 1

        except Exception:
            awareness_score += 0.05
            factors_count += 1

        return awareness_score / max(factors_count, 1)

    def _analyze_ethical_consistency(self, memory: 'Memory') -> float:
        """
        Анализировать этическую последовательность поведения.

        Args:
            memory: Память системы

        Returns:
            float: Уровень этической последовательности (0.0 - 1.0)
        """
        consistency_score = 0.0
        factors_count = 0

        # Фактор 1: Последовательность в реагировании на похожие ситуации
        try:
            # Анализируем паттерны реакций на события
            event_patterns = {}

            try:
                memory_entries = getattr(memory, '_active_memory', [])
                if memory_entries:
                    for entry in memory_entries[-50:]:  # Анализируем последние 50 записей
                        event_type = getattr(entry, 'event', {}).get('type', 'unknown')
                        action = getattr(entry, 'action', 'unknown')

                        if event_type not in event_patterns:
                            event_patterns[event_type] = {}

                        if action not in event_patterns[event_type]:
                            event_patterns[event_type][action] = 0

                        event_patterns[event_type][action] += 1

                    # Вычисляем консистентность: чем больше доминирует одно действие для типа события, тем выше консистентность
                    total_consistency = 0.0
                    pattern_count = 0

                    for event_type, actions in event_patterns.items():
                        if actions:
                            total_actions = sum(actions.values())
                            if total_actions > 1:
                                # Вычисляем энтропию: чем ниже энтропия, тем выше консистентность
                                entropy = 0.0
                                for count in actions.values():
                                    if count > 0:
                                        p = count / total_actions
                                        entropy -= p * (p ** 0.5)  # Упрощенная энтропия

                                # Консистентность = 1 - нормализованная энтропия
                                max_entropy = len(actions) ** 0.5
                                consistency = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 1.0
                                total_consistency += consistency
                                pattern_count += 1

                    if pattern_count > 0:
                        avg_consistency = total_consistency / pattern_count
                        consistency_score += 0.4 * avg_consistency
                    else:
                        consistency_score += 0.05
                else:
                    consistency_score += 0.05

            except Exception:
                consistency_score += 0.05

            factors_count += 1

        except Exception:
            consistency_score += 0.05
            factors_count += 1

        # Фактор 2: Стабильность ценностных ориентаций
        try:
            # Анализируем стабильность значимости событий со временем
            significance_trend = []

            try:
                memory_entries = getattr(memory, '_active_memory', [])
                if len(memory_entries) > 10:
                    # Берем значимости последних 20 событий
                    for entry in memory_entries[-20:]:
                        significance = getattr(entry, 'significance', 0)
                        significance_trend.append(significance)

                    if len(significance_trend) > 5:
                        # Вычисляем стабильность тренда значимости
                        trend_stability = 1.0
                        for i in range(1, len(significance_trend)):
                            diff = abs(significance_trend[i] - significance_trend[i-1])
                            if diff > 0.3:  # Значительное изменение
                                trend_stability *= 0.9

                        consistency_score += 0.3 * trend_stability
                    else:
                        consistency_score += 0.1
                else:
                    consistency_score += 0.05

            except Exception:
                consistency_score += 0.05

            factors_count += 1

        except Exception:
            consistency_score += 0.05
            factors_count += 1

        # Фактор 3: Избегание противоречивых действий
        try:
            # Ищем противоречия в поведении (например, одновременное выполнение взаимоисключающих действий)
            contradictions = 0
            total_actions = 0

            try:
                memory_entries = getattr(memory, '_active_memory', [])
                if memory_entries:
                    recent_actions = []
                    for entry in memory_entries[-10:]:
                        action = getattr(entry, 'action', None)
                        if action:
                            recent_actions.append(action)
                            total_actions += 1

                    # Проверяем на очевидные противоречия
                    # (в реальной системе это можно расширить на основе доменной логики)
                    action_counts = {}
                    for action in recent_actions:
                        action_counts[action] = action_counts.get(action, 0) + 1

                    # Если есть слишком много разных действий за короткий период,
                    # это может указывать на непоследовательность
                    unique_actions = len(action_counts)
                    if unique_actions > total_actions * 0.7:  # Более 70% уникальных действий
                        contradictions += 0.5

                    consistency_score += 0.3 * (1.0 - contradictions)
                else:
                    consistency_score += 0.1

            except Exception:
                consistency_score += 0.1

            factors_count += 1

        except Exception:
            consistency_score += 0.05
            factors_count += 1

        return consistency_score / max(factors_count, 1)

    def _analyze_dilemma_resolution(self, decision_engine: 'DecisionEngine') -> float:
        """
        Анализировать способность к разрешению этических дилемм.

        Args:
            decision_engine: Движок принятия решений

        Returns:
            float: Способность к разрешению дилемм (0.0 - 1.0)
        """
        dilemma_score = 0.0
        factors_count = 0

        # Фактор 1: Способность к балансировке конкурирующих целей
        try:
            # Анализируем сложность принимаемых решений
            decision_complexity = 0

            # Проверяем использование различных факторов в решениях
            if hasattr(decision_engine, '_decision_factors'):
                factors = getattr(decision_engine, '_decision_factors', {})
                decision_complexity = min(len(factors) / 10, 1.0)  # Нормализуем

            dilemma_score += 0.3 * decision_complexity
            factors_count += 1

        except Exception:
            dilemma_score += 0.1
            factors_count += 1

        # Фактор 2: Способность к компромиссам
        try:
            # Анализируем умеренность в решениях (избегание экстремальных выборов)
            moderation_score = 0.5  # Базовый уровень

            # В реальной системе здесь можно анализировать историю решений
            # на предмет баланса между различными аспектами

            dilemma_score += 0.3 * moderation_score
            factors_count += 1

        except Exception:
            dilemma_score += 0.1
            factors_count += 1

        # Фактор 3: Адаптация к этическим ограничениям
        try:
            # Проверяем соблюдение ограничений в сложных ситуациях
            constraint_awareness = 0.5  # Базовый уровень

            # Анализируем, насколько система учитывает ограничения
            # в своих решениях

            dilemma_score += 0.4 * constraint_awareness
            factors_count += 1

        except Exception:
            dilemma_score += 0.1
            factors_count += 1

        return dilemma_score / max(factors_count, 1)

    def _calculate_overall_ethical_score(self, metrics: EthicalBehaviorMetrics) -> float:
        """
        Вычислить общий этический уровень.

        Args:
            metrics: Индивидуальные этические метрики

        Returns:
            float: Общий этический уровень (0.0 - 1.0)
        """
        weights = {
            'norm_compliance': 0.3,
            'consequence_awareness': 0.3,
            'ethical_consistency': 0.25,
            'dilemma_resolution': 0.15
        }

        overall_score = (
            metrics.norm_compliance * weights['norm_compliance'] +
            metrics.consequence_awareness * weights['consequence_awareness'] +
            metrics.ethical_consistency * weights['ethical_consistency'] +
            metrics.dilemma_resolution * weights['dilemma_resolution']
        )

        return min(overall_score, 1.0)

    def _get_current_ethical_decision(self, memory: 'Memory') -> Dict:
        """
        Получить информацию о текущем этическом решении.

        Args:
            memory: Память системы

        Returns:
            Dict: Информация о решении или None
        """
        try:
            recent_entries = getattr(memory, '_active_memory', [])
            if recent_entries:
                latest_entry = recent_entries[-1]
                return {
                    'timestamp': getattr(latest_entry, 'timestamp', None),
                    'event_type': getattr(latest_entry, 'event', {}).get('type', 'unknown'),
                    'action': getattr(latest_entry, 'action', 'unknown'),
                    'significance': getattr(latest_entry, 'significance', 0),
                    'ethical_context': self._assess_ethical_context(latest_entry)
                }
        except Exception:
            pass

        return None

    def _assess_ethical_context(self, memory_entry) -> str:
        """
        Оценить этический контекст решения.

        Args:
            memory_entry: Запись в памяти

        Returns:
            str: Этический контекст
        """
        try:
            significance = getattr(memory_entry, 'significance', 0)
            action = getattr(memory_entry, 'action', 'unknown')

            if significance > 0.7:
                return 'highly_positive'
            elif significance > 0.3:
                return 'positive'
            elif significance > -0.3:
                return 'neutral'
            elif significance > -0.7:
                return 'negative'
            else:
                return 'highly_negative'

        except Exception:
            return 'unknown'
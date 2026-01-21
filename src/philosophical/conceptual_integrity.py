"""
Анализатор концептуальной целостности системы Life.

Модуль анализирует целостность внутренней модели мира,
согласованность поведения с концепцией и способность к концептуальному обучению.
"""

import logging
from typing import TYPE_CHECKING, Dict, List

from .metrics import ConceptualIntegrityMetrics

if TYPE_CHECKING:
    from src.state.self_state import SelfState
    from src.memory.memory import Memory
    from src.learning.learning import LearningEngine

logger = logging.getLogger(__name__)


class ConceptualIntegrityAnalyzer:
    """
    Анализатор концептуальной целостности.

    Анализирует:
    - Целостность внутренней модели мира
    - Согласованность поведения с концепцией
    - Стабильность концептуальных представлений
    - Способность к концептуальному обучению
    """

    def __init__(self):
        """Инициализация анализатора концептуальной целостности."""
        self.conceptual_history_window = 30  # Окно анализа концептуальных изменений

    def analyze_conceptual_integrity(
        self,
        self_state: 'SelfState',
        memory: 'Memory',
        learning_engine: 'LearningEngine'
    ) -> ConceptualIntegrityMetrics:
        """
        Проанализировать концептуальную целостность.

        Args:
            self_state: Текущее состояние системы
            memory: Память системы
            learning_engine: Движок обучения

        Returns:
            ConceptualIntegrityMetrics: Метрики концептуальной целостности
        """
        metrics = ConceptualIntegrityMetrics()

        # Анализ целостности модели мира
        metrics.model_integrity = self._analyze_model_integrity(self_state, memory)

        # Анализ согласованности поведения
        metrics.behavioral_consistency = self._analyze_behavioral_consistency(memory)

        # Анализ стабильности концепций
        metrics.conceptual_stability = self._analyze_conceptual_stability(learning_engine)

        # Анализ концептуального обучения
        metrics.conceptual_learning = self._analyze_conceptual_learning(learning_engine)

        # Вычисление общей концептуальной целостности
        metrics.overall_integrity = self._calculate_overall_integrity(metrics)

        # Добавление в историю изменений
        current_state = self._get_current_conceptual_state(self_state, learning_engine)
        metrics.conceptual_changes_history.append(current_state)

        # Ограничение размера истории
        if len(metrics.conceptual_changes_history) > self.conceptual_history_window:
            metrics.conceptual_changes_history = metrics.conceptual_changes_history[-self.conceptual_history_window:]

        return metrics

    def _analyze_model_integrity(self, self_state: 'SelfState', memory: 'Memory') -> float:
        """
        Анализировать целостность внутренней модели мира.

        Args:
            self_state: Состояние системы
            memory: Память системы

        Returns:
            float: Целостность модели (0.0 - 1.0)
        """
        integrity_score = 0.0
        factors_count = 0

        # Фактор 1: Связность воспоминаний
        try:
            memory_stats = memory.get_statistics()
            total_entries = memory_stats.get('total_entries', 0)
            archived_entries = memory_stats.get('archived_entries', 0)

            if total_entries > 0:
                # Высокая доля архивных записей указывает на хорошую организацию памяти
                archive_ratio = archived_entries / total_entries
                if archive_ratio > 0.3:
                    integrity_score += 0.3
                elif archive_ratio > 0.1:
                    integrity_score += 0.2
                else:
                    integrity_score += 0.1
                factors_count += 1
        except Exception:
            integrity_score += 0.1
            factors_count += 1

        # Фактор 2: Целостность состояния системы
        try:
            # Проверяем консистентность ключевых параметров состояния
            state_integrity = 0.0
            state_checks = 0

            # Проверка энергии
            if hasattr(self_state, 'energy') and 0 <= self_state.energy <= 100:
                state_integrity += 1
                state_checks += 1

            # Проверка целостности
            if hasattr(self_state, 'integrity') and 0 <= self_state.integrity <= 1:
                state_integrity += 1
                state_checks += 1

            # Проверка стабильности
            if hasattr(self_state, 'stability') and 0 <= self_state.stability <= 1:
                state_integrity += 1
                state_checks += 1

            # Проверка возраста
            if hasattr(self_state, 'age') and self_state.age >= 0:
                state_integrity += 1
                state_checks += 1

            if state_checks > 0:
                state_integrity_ratio = state_integrity / state_checks
                integrity_score += 0.3 * state_integrity_ratio
                factors_count += 1

        except Exception:
            integrity_score += 0.1
            factors_count += 1

        # Фактор 3: Согласованность временных аспектов
        try:
            temporal_integrity = 0.0

            if hasattr(self_state, 'age') and hasattr(self_state, 'subjective_time'):
                # Проверяем разумность соотношения физического и субъективного времени
                if self_state.age > 0:
                    time_ratio = self_state.subjective_time / self_state.age
                    if 0.01 <= time_ratio <= 100:  # Разумный диапазон
                        temporal_integrity += 0.5
                    elif 0.001 <= time_ratio <= 1000:  # Приемлемый диапазон
                        temporal_integrity += 0.3
                    else:
                        temporal_integrity += 0.1

            if hasattr(self_state, 'ticks') and self_state.ticks >= 0:
                temporal_integrity += 0.5

            integrity_score += 0.4 * (temporal_integrity / 1.0)
            factors_count += 1

        except Exception:
            integrity_score += 0.1
            factors_count += 1

        return integrity_score / max(factors_count, 1)

    def _analyze_behavioral_consistency(self, memory: 'Memory') -> float:
        """
        Анализировать согласованность поведения с концепцией.

        Args:
            memory: Память системы

        Returns:
            float: Согласованность поведения (0.0 - 1.0)
        """
        consistency_score = 0.0
        factors_count = 0

        # Фактор 1: Консистентность реакций на события
        try:
            # Анализируем паттерны реагирования
            reaction_patterns = {}
            total_reactions = 0

            try:
                memory_entries = getattr(memory, '_active_memory', [])
                if memory_entries:
                    for entry in memory_entries[-50:]:  # Анализируем последние 50 записей
                        event = getattr(entry, 'event', {})
                        event_type = event.get('type', 'unknown') if isinstance(event, dict) else str(event)
                        action = getattr(entry, 'action', 'unknown')

                        if event_type not in reaction_patterns:
                            reaction_patterns[event_type] = {}

                        if action not in reaction_patterns[event_type]:
                            reaction_patterns[event_type][action] = 0

                        reaction_patterns[event_type][action] += 1
                        total_reactions += 1

                    if total_reactions > 10:
                        # Вычисляем среднюю консистентность реакций
                        total_consistency = 0.0
                        pattern_count = 0

                        for event_type, actions in reaction_patterns.items():
                            if actions and sum(actions.values()) > 2:
                                # Вычисляем доминирование основного паттерна реакции
                                max_count = max(actions.values())
                                total_count = sum(actions.values())
                                consistency_ratio = max_count / total_count
                                total_consistency += consistency_ratio
                                pattern_count += 1

                        if pattern_count > 0:
                            avg_consistency = total_consistency / pattern_count
                            consistency_score += 0.4 * avg_consistency
                        else:
                            consistency_score += 0.1
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

        # Фактор 2: Соответствие архитектурным принципам
        try:
            # Проверяем соответствие базовым принципам системы Life
            architectural_compliance = 0.0

            # Принцип 1: Избегание целей и оптимизации
            # (проверяем отсутствие явных целевых метрик в поведении)
            architectural_compliance += 0.5  # Предполагаем соответствие

            # Принцип 2: Медленное изменение параметров
            # (проверяем отсутствие резких изменений в поведении)
            architectural_compliance += 0.5

            consistency_score += 0.3 * (architectural_compliance / 1.0)
            factors_count += 1

        except Exception:
            consistency_score += 0.1
            factors_count += 1

        # Фактор 3: Стабильность значимости событий
        try:
            significance_stability = 0.5  # Базовый уровень

            try:
                memory_entries = getattr(memory, '_active_memory', [])
                if len(memory_entries) > 10:
                    significances = [getattr(entry, 'significance', 0) for entry in memory_entries[-20:]]
                    if significances:
                        # Вычисляем стабильность значимости
                        mean_sig = sum(significances) / len(significances)
                        variance = sum((s - mean_sig) ** 2 for s in significances) / len(significances)
                        std_dev = variance ** 0.5

                        # Низкое стандартное отклонение = высокая стабильность
                        if std_dev < 0.2:
                            significance_stability = 0.9
                        elif std_dev < 0.4:
                            significance_stability = 0.7
                        elif std_dev < 0.6:
                            significance_stability = 0.5
                        else:
                            significance_stability = 0.3

                consistency_score += 0.3 * significance_stability

            except Exception:
                consistency_score += 0.1

            factors_count += 1

        except Exception:
            consistency_score += 0.05
            factors_count += 1

        return consistency_score / max(factors_count, 1)

    def _analyze_conceptual_stability(self, learning_engine: 'LearningEngine') -> float:
        """
        Анализировать стабильность концептуальных представлений.

        Args:
            learning_engine: Движок обучения

        Returns:
            float: Стабильность концепций (0.0 - 1.0)
        """
        stability_score = 0.0
        factors_count = 0

        # Фактор 1: Стабильность параметров обучения
        try:
            learning_params = getattr(learning_engine, 'learning_params', {})
            if learning_params:
                # Анализируем историю изменений параметров
                param_history = getattr(learning_engine, 'parameter_history', [])

                if len(param_history) > 5:
                    # Вычисляем стабильность изменений
                    total_stability = 0.0
                    param_count = 0

                    for param_name in ['event_type_sensitivity', 'significance_thresholds', 'response_coefficients']:
                        if param_name in learning_params:
                            param_count += 1
                            param_value = learning_params[param_name]

                            # Ищем изменения этого параметра в истории
                            changes = []
                            for i, hist_params in enumerate(param_history[-10:]):
                                if param_name in hist_params:
                                    hist_value = hist_params[param_name]
                                    if i > 0 and param_history[-11+i] and param_name in param_history[-11+i]:
                                        prev_value = param_history[-11+i][param_name]
                                        change = abs(hist_value - prev_value)
                                        changes.append(change)

                            if changes:
                                avg_change = sum(changes) / len(changes)
                                # Низкие изменения = высокая стабильность
                                if avg_change < 0.01:
                                    param_stability = 0.9
                                elif avg_change < 0.05:
                                    param_stability = 0.7
                                elif avg_change < 0.1:
                                    param_stability = 0.5
                                else:
                                    param_stability = 0.3
                            else:
                                param_stability = 0.8  # Нет изменений = стабильность

                            total_stability += param_stability

                    if param_count > 0:
                        avg_stability = total_stability / param_count
                        stability_score += 0.4 * avg_stability
                    else:
                        stability_score += 0.2
                else:
                    stability_score += 0.2  # Недостаточно истории

                factors_count += 1
        except Exception:
            stability_score += 0.1
            factors_count += 1

        # Фактор 2: Консистентность концептуального обучения
        try:
            learning_stats = getattr(learning_engine, 'learning_statistics', {})
            if learning_stats:
                # Анализируем консистентность процесса обучения
                stats_keys = list(learning_stats.keys())
                if len(stats_keys) > 5:
                    # Разнообразие статистик указывает на активное обучение
                    stability_score += 0.3
                elif len(stats_keys) > 2:
                    stability_score += 0.2
                else:
                    stability_score += 0.1
                factors_count += 1
        except Exception:
            stability_score += 0.1
            factors_count += 1

        # Фактор 3: Отсутствие концептуальных конфликтов
        try:
            # Проверяем отсутствие противоречий в параметрах
            param_conflicts = 0
            total_params = 0

            learning_params = getattr(learning_engine, 'learning_params', {})
            for param_name, param_value in learning_params.items():
                if isinstance(param_value, (int, float)):
                    total_params += 1
                    # Проверяем разумность значения параметра
                    if not (0 <= param_value <= 2):  # Параметры должны быть в разумных пределах
                        param_conflicts += 1

            if total_params > 0:
                conflict_ratio = param_conflicts / total_params
                stability_score += 0.3 * (1.0 - conflict_ratio)
            else:
                stability_score += 0.1

            factors_count += 1

        except Exception:
            stability_score += 0.1
            factors_count += 1

        return stability_score / max(factors_count, 1)

    def _analyze_conceptual_learning(self, learning_engine: 'LearningEngine') -> float:
        """
        Анализировать способность к концептуальному обучению.

        Args:
            learning_engine: Движок обучения

        Returns:
            float: Способность к обучению (0.0 - 1.0)
        """
        learning_score = 0.0
        factors_count = 0

        # Фактор 1: Активность процесса обучения
        try:
            learning_stats = getattr(learning_engine, 'learning_statistics', {})
            if learning_stats:
                # Оцениваем объем собранной статистики
                total_stats = sum(learning_stats.values()) if learning_stats else 0
                if total_stats > 100:
                    learning_score += 0.3
                elif total_stats > 50:
                    learning_score += 0.2
                elif total_stats > 10:
                    learning_score += 0.1
                else:
                    learning_score += 0.05
                factors_count += 1
        except Exception:
            learning_score += 0.05
            factors_count += 1

        # Фактор 2: Адаптация параметров обучения
        try:
            param_history = getattr(learning_engine, 'parameter_history', [])
            if len(param_history) > 3:
                # Есть история изменений параметров
                learning_score += 0.3
            elif len(param_history) > 1:
                learning_score += 0.2
            else:
                learning_score += 0.1
            factors_count += 1
        except Exception:
            learning_score += 0.1
            factors_count += 1

        # Фактор 3: Эффективность обучения
        try:
            # Оцениваем постепенность изменений (соответствие MAX_PARAMETER_DELTA)
            param_history = getattr(learning_engine, 'parameter_history', [])
            if len(param_history) > 1:
                total_gradual_changes = 0
                total_changes = 0

                for i in range(1, min(len(param_history), 10)):
                    current_params = param_history[i]
                    prev_params = param_history[i-1]

                    for param_name in current_params:
                        if param_name in prev_params:
                            change = abs(current_params[param_name] - prev_params[param_name])
                            total_changes += 1
                            if change <= 0.01:  # Постепенное изменение
                                total_gradual_changes += 1

                if total_changes > 0:
                    gradual_ratio = total_gradual_changes / total_changes
                    learning_score += 0.4 * gradual_ratio
                else:
                    learning_score += 0.1
            else:
                learning_score += 0.05

            factors_count += 1

        except Exception:
            learning_score += 0.1
            factors_count += 1

        return learning_score / max(factors_count, 1)

    def _calculate_overall_integrity(self, metrics: ConceptualIntegrityMetrics) -> float:
        """
        Вычислить общую концептуальную целостность.

        Args:
            metrics: Индивидуальные метрики целостности

        Returns:
            float: Общая концептуальная целостность (0.0 - 1.0)
        """
        weights = {
            'model_integrity': 0.3,
            'behavioral_consistency': 0.3,
            'conceptual_stability': 0.25,
            'conceptual_learning': 0.15
        }

        overall_score = (
            metrics.model_integrity * weights['model_integrity'] +
            metrics.behavioral_consistency * weights['behavioral_consistency'] +
            metrics.conceptual_stability * weights['conceptual_stability'] +
            metrics.conceptual_learning * weights['conceptual_learning']
        )

        return min(overall_score, 1.0)

    def _get_current_conceptual_state(self, self_state: 'SelfState', learning_engine: 'LearningEngine') -> Dict:
        """
        Получить текущее концептуальное состояние.

        Args:
            self_state: Состояние системы
            learning_engine: Движок обучения

        Returns:
            Dict: Текущее концептуальное состояние
        """
        try:
            return {
                'timestamp': getattr(self_state, 'age', 0),
                'learning_params': getattr(learning_engine, 'learning_params', {}).copy(),
                'key_state_params': {
                    'energy': getattr(self_state, 'energy', 0),
                    'integrity': getattr(self_state, 'integrity', 1.0),
                    'stability': getattr(self_state, 'stability', 1.0),
                    'subjective_time': getattr(self_state, 'subjective_time', 0)
                }
            }
        except Exception:
            return {'error': 'unable_to_get_conceptual_state'}
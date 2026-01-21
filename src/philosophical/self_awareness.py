"""
Анализатор наблюдаемых характеристик поведения системы Life.

Модуль анализирует наблюдаемые характеристики поведения системы,
которые могут быть интерпретированы как признаки определенных качеств.

ВАЖНО: Это внешнее наблюдение, а не внутреннее самоосознание системы.
"""

import logging
from typing import TYPE_CHECKING, Dict, List

from .metrics import SelfAwarenessMetrics

if TYPE_CHECKING:
    from src.state.self_state import SelfState
    from src.memory.memory import Memory

logger = logging.getLogger(__name__)


class SelfAwarenessAnalyzer:
    """
    Анализатор наблюдаемых характеристик поведения.

    Анализирует наблюдаемые характеристики:
    - Стабильность и предсказуемость поведения
    - Адаптивность к изменениям
    - Регулярность паттернов поведения
    - Способность к поддержанию состояния
    """

    def __init__(self):
        """Инициализация анализатора самоосознания."""
        self.history_window = 100  # Окно анализа для трендов

    def analyze_self_awareness(self, self_state: 'SelfState', memory: 'Memory') -> SelfAwarenessMetrics:
        """
        Проанализировать уровень самоосознания на основе состояния и памяти.

        Args:
            self_state: Текущее состояние системы
            memory: Память системы

        Returns:
            SelfAwarenessMetrics: Метрики самоосознания
        """
        metrics = SelfAwarenessMetrics()

        # Анализ осознания собственного состояния
        metrics.state_awareness = self._analyze_state_awareness(self_state)

        # Анализ рефлексии поведения
        metrics.behavioral_reflection = self._analyze_behavioral_reflection(self_state, memory)

        # Анализ осознания временного контекста
        metrics.temporal_awareness = self._analyze_temporal_awareness(self_state)

        # Анализ самоконтроля и регуляции
        metrics.self_regulation = self._analyze_self_regulation(self_state)

        # Вычисление общего уровня самоосознания
        metrics.overall_self_awareness = self._calculate_overall_self_awareness(metrics)

        # Добавление в историю
        metrics.history.append(metrics.to_dict() if hasattr(metrics, 'to_dict') else vars(metrics))

        # Ограничение размера истории
        if len(metrics.history) > self.history_window:
            metrics.history = metrics.history[-self.history_window:]

        return metrics

    def _analyze_state_awareness(self, self_state: 'SelfState') -> float:
        """
        Анализировать осознание собственного состояния.

        Args:
            self_state: Состояние системы

        Returns:
            float: Уровень осознания состояния (0.0 - 1.0)
        """
        # Факторы осознания состояния:
        # 1. Мониторинг жизненно важных параметров
        # 2. Способность к самодиагностике
        # 3. Осознание изменений в состоянии

        state_awareness_score = 0.0
        factors_count = 0

        # Фактор 1: Мониторинг жизненно важных параметров
        # Проверяем наличие основных параметров состояния
        core_params = ['energy', 'stability', 'integrity', 'fatigue']
        available_params = sum(1 for param in core_params if hasattr(self_state, param))

        if available_params >= 3:  # Большинство параметров доступны
            state_awareness_score += 0.4
        elif available_params >= 2:
            state_awareness_score += 0.2
        else:
            state_awareness_score += 0.1
        factors_count += 1

        # Фактор 2: Способность к самодиагностике
        # Проверяем наличие диагностических параметров
        diagnostic_params = ['last_event_intensity', 'last_significance']
        diagnostic_available = sum(1 for param in diagnostic_params if hasattr(self_state, param))

        if diagnostic_available >= 2:
            state_awareness_score += 0.3
        elif diagnostic_available >= 1:
            state_awareness_score += 0.15
        else:
            state_awareness_score += 0.05
        factors_count += 1

        # Фактор 3: Осознание временного контекста
        temporal_awareness = 0.0
        if hasattr(self_state, 'age') and self_state.age > 0:
            temporal_awareness += 0.2
        if hasattr(self_state, 'subjective_time') and self_state.subjective_time > 0:
            temporal_awareness += 0.2
        if hasattr(self_state, 'ticks') and self_state.ticks > 0:
            temporal_awareness += 0.2
            # Бонус за длительную работу
            if self_state.ticks > 1000:
                temporal_awareness += 0.2
            elif self_state.ticks > 100:
                temporal_awareness += 0.1

        state_awareness_score += temporal_awareness
        factors_count += 1

        return state_awareness_score / max(factors_count, 1)

    def _analyze_behavioral_reflection(self, self_state: 'SelfState', memory: 'Memory') -> float:
        """
        Анализировать способность к рефлексии поведения.

        Args:
            self_state: Состояние системы
            memory: Память системы

        Returns:
            float: Уровень рефлексии поведения (0.0 - 1.0)
        """
        reflection_score = 0.0
        factors_count = 0

        # Фактор 1: Наличие недавних событий для анализа
        # Используем память системы для анализа паттернов поведения
        try:
            memory_stats = memory.get_statistics()
            total_entries = memory_stats.get('total_entries', 0)
            recent_entries = memory_stats.get('recent_entries_count', 0)

            # Оцениваем количество недавних событий
            if recent_entries > 50:
                reflection_score += 0.4
            elif recent_entries > 20:
                reflection_score += 0.25
            elif recent_entries > 5:
                reflection_score += 0.15
            elif total_entries > 0:
                reflection_score += 0.05

            # Бонус за разнообразие типов событий в памяти
            event_types = memory_stats.get('event_types', {})
            if len(event_types) > 3:
                reflection_score += 0.1

            factors_count += 1
        except Exception as e:
            logger.debug(f"Не удалось получить статистику памяти: {e}")
            reflection_score += 0.05
            factors_count += 1

        # Фактор 2: Способность к анализу паттернов в памяти
        try:
            memory_stats = memory.get_statistics()
            total_entries = memory_stats.get('total_entries', 0)

            # Оцениваем не только количество, но и организацию памяти
            if total_entries > 100:
                reflection_score += 0.4
            elif total_entries > 50:
                reflection_score += 0.25
            elif total_entries > 20:
                reflection_score += 0.15
            else:
                reflection_score += 0.05

            # Бонус за структурированную память
            if memory_stats.get('archived_entries', 0) > 0:
                reflection_score += 0.1

            factors_count += 1
        except Exception as e:
            logger.debug(f"Не удалось получить статистику памяти: {e}")
            reflection_score += 0.05  # Минимальный уровень при ошибке доступа
            factors_count += 1

        # Фактор 3: Наличие механизма обратной связи
        feedback_score = 0.0
        if hasattr(self_state, 'last_significance') and self_state.last_significance is not None:
            feedback_score += 0.2
        if hasattr(self_state, 'last_event_intensity') and self_state.last_event_intensity is not None:
            feedback_score += 0.2
        # Проверяем наличие истории обратной связи
        if hasattr(self_state, 'memory') and self_state.memory is not None:
            try:
                # Пытаемся получить размер памяти
                memory_size = len(self_state.memory) if hasattr(self_state.memory, '__len__') else 0
                if memory_size > 0:
                    # Ищем feedback записи в памяти (если доступно)
                    try:
                        if hasattr(self_state.memory, '__iter__'):
                            feedback_entries = [entry for entry in self_state.memory
                                              if hasattr(entry, 'event_type') and getattr(entry, 'event_type', None) == 'feedback']
                            if len(feedback_entries) > 0:
                                feedback_score += 0.2
                        else:
                            feedback_score += 0.1  # Память существует, но не итерируема
                    except (TypeError, AttributeError):
                        feedback_score += 0.1  # Не можем итерировать, но память существует
                else:
                    feedback_score += 0.05  # Память пуста
            except (TypeError, AttributeError):
                feedback_score += 0.05  # Не можем получить размер памяти

        reflection_score += feedback_score
        factors_count += 1

        return reflection_score / max(factors_count, 1)

    def _analyze_temporal_awareness(self, self_state: 'SelfState') -> float:
        """
        Анализировать осознание временного контекста.

        Args:
            self_state: Состояние системы

        Returns:
            float: Уровень осознания времени (0.0 - 1.0)
        """
        temporal_score = 0.0
        factors_count = 0

        # Фактор 1: Отслеживание возраста системы
        if hasattr(self_state, 'age') and self_state.age > 0:
            temporal_score += 0.3
            factors_count += 1

        # Фактор 2: Осознание субъективного времени
        if hasattr(self_state, 'subjective_time') and self_state.subjective_time > 0:
            temporal_score += 0.3
            factors_count += 1

        # Фактор 3: Количество тиков (единиц дискретного времени)
        if hasattr(self_state, 'ticks') and self_state.ticks > 0:
            if self_state.ticks > 1000:
                temporal_score += 0.4
            elif self_state.ticks > 100:
                temporal_score += 0.2
            else:
                temporal_score += 0.1
            factors_count += 1

        return temporal_score / max(factors_count, 1)

    def _analyze_self_regulation(self, self_state: 'SelfState') -> float:
        """
        Анализировать способность к самоконтролю и регуляции.

        Args:
            self_state: Состояние системы

        Returns:
            float: Уровень саморегуляции (0.0 - 1.0)
        """
        regulation_score = 0.0
        factors_count = 0

        # Фактор 1: Контроль уровня энергии
        if hasattr(self_state, 'energy'):
            energy = self_state.energy
            # Оцениваем, насколько энергия находится в жизнеспособном диапазоне
            if energy > 10:  # Минимальный уровень для функционирования
                if energy > 50:  # Хороший уровень энергии
                    regulation_score += 0.25
                elif energy > 25:
                    regulation_score += 0.15
                else:
                    regulation_score += 0.05
            factors_count += 1

        # Фактор 2: Поддержание целостности
        if hasattr(self_state, 'integrity'):
            integrity = self_state.integrity
            # Оцениваем уровень целостности
            if integrity > 0.3:  # Минимальный уровень для функционирования
                if integrity > 0.8:  # Высокая целостность
                    regulation_score += 0.25
                elif integrity > 0.6:
                    regulation_score += 0.15
                else:
                    regulation_score += 0.05
            factors_count += 1

        # Фактор 3: Контроль стабильности
        if hasattr(self_state, 'stability'):
            stability = self_state.stability
            # Оцениваем уровень стабильности
            if stability > 0.2:  # Минимальный уровень для функционирования
                if stability > 0.7:  # Высокая стабильность
                    regulation_score += 0.25
                elif stability > 0.5:
                    regulation_score += 0.15
                else:
                    regulation_score += 0.05
            factors_count += 1

        # Фактор 4: Управление усталостью
        if hasattr(self_state, 'fatigue'):
            fatigue = self_state.fatigue
            # Оцениваем способность справляться с усталостью
            if fatigue < 80:  # Не критический уровень усталости
                if fatigue < 40:  # Низкий уровень усталости
                    regulation_score += 0.25
                elif fatigue < 60:
                    regulation_score += 0.15
                else:
                    regulation_score += 0.05
            factors_count += 1

        return regulation_score / max(factors_count, 1)

    def _calculate_overall_self_awareness(self, metrics: SelfAwarenessMetrics) -> float:
        """
        Вычислить общий уровень самоосознания.

        Args:
            metrics: Индивидуальные метрики самоосознания

        Returns:
            float: Общий уровень самоосознания (0.0 - 1.0)
        """
        weights = {
            'state_awareness': 0.3,
            'behavioral_reflection': 0.25,
            'temporal_awareness': 0.25,
            'self_regulation': 0.2
        }

        overall_score = (
            metrics.state_awareness * weights['state_awareness'] +
            metrics.behavioral_reflection * weights['behavioral_reflection'] +
            metrics.temporal_awareness * weights['temporal_awareness'] +
            metrics.self_regulation * weights['self_regulation']
        )

        return min(overall_score, 1.0)  # Ограничение максимумом
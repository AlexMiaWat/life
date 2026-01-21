"""
Процедурная память - Procedural Memory Store.

Хранит навыки, автоматизмы и паттерны поведения, извлеченные из успешного опыта.
Реализует автоматическое выполнение часто повторяющихся последовательностей действий.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Sequence
from dataclasses import dataclass, field
from collections import defaultdict

from src.observability.structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


@dataclass
class ProceduralPattern:
    """
    Процедурный паттерн - автоматизированная последовательность действий.

    Представляет навык или автоматизм, извлеченный из повторяющегося успешного опыта.
    """
    pattern_id: str  # Уникальный идентификатор паттерна
    name: str  # Читаемое имя паттерна
    description: str  # Описание паттерна

    # Последовательность действий: (action_type, parameters)
    action_sequence: List[Tuple[str, Dict[str, Any]]] = field(default_factory=list)

    # Условия активации паттерна
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)

    # Статистика использования
    success_count: int = 0  # Количество успешных выполнений
    failure_count: int = 0  # Количество неудач
    total_executions: int = 0  # Общее количество выполнений

    # Метрики эффективности
    average_execution_time: float = 0.0  # Среднее время выполнения
    success_rate: float = 0.0  # Доля успешных выполнений

    # Автоматизация
    automation_level: float = 0.0  # Уровень автоматизации (0.0-1.0)
    min_automation_threshold: float = 0.8  # Минимальный порог для автоматического выполнения

    # Временные метки
    created_at: float = field(default_factory=time.time)
    last_execution: float = 0.0
    last_success: float = 0.0

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить паттерн в заданном контексте.

        Args:
            context: Контекст выполнения

        Returns:
            Результат выполнения
        """
        start_time = time.time()
        self.total_executions += 1
        self.last_execution = start_time

        try:
            # Имитация выполнения последовательности действий
            result = self._execute_sequence(context)
            execution_time = time.time() - start_time

            # Обновляем статистику успеха
            self.success_count += 1
            self.last_success = time.time()
            self._update_execution_metrics(execution_time, True)

            return {
                "success": True,
                "pattern_id": self.pattern_id,
                "execution_time": execution_time,
                "actions_executed": len(self.action_sequence),
                "result": result
            }

        except Exception as e:
            execution_time = time.time() - start_time
            self.failure_count += 1
            self._update_execution_metrics(execution_time, False)

            return {
                "success": False,
                "pattern_id": self.pattern_id,
                "execution_time": execution_time,
                "error": str(e)
            }

    def _execute_sequence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить последовательность действий.

        Args:
            context: Контекст выполнения

        Returns:
            Результат выполнения последовательности
        """
        # Заглушка для демонстрации - в реальной реализации
        # здесь будет выполнение конкретных действий
        results = []

        for action_type, parameters in self.action_sequence:
            # Имитация выполнения действия
            action_result = {
                "action_type": action_type,
                "parameters": parameters,
                "timestamp": time.time(),
                "simulated_result": f"Executed {action_type} with {parameters}"
            }
            results.append(action_result)

        return {
            "sequence_length": len(self.action_sequence),
            "actions": results
        }

    def _update_execution_metrics(self, execution_time: float, success: bool) -> None:
        """Обновить метрики выполнения."""
        # Обновляем среднее время выполнения
        if self.average_execution_time == 0:
            self.average_execution_time = execution_time
        else:
            # Экспоненциальное сглаживание
            alpha = 0.1
            self.average_execution_time = (
                alpha * execution_time + (1 - alpha) * self.average_execution_time
            )

        # Обновляем success rate
        total_attempts = self.success_count + self.failure_count
        if total_attempts > 0:
            self.success_rate = self.success_count / total_attempts

        # Обновляем уровень автоматизации на основе success rate
        if self.success_rate > 0.9 and self.total_executions > 5:
            self.automation_level = min(1.0, self.automation_level + 0.1)
        elif self.success_rate < 0.5:
            self.automation_level = max(0.0, self.automation_level - 0.1)

    def can_automate(self, context: Dict[str, Any]) -> bool:
        """
        Проверить, можно ли автоматически выполнить паттерн в данном контексте.

        Args:
            context: Контекст для проверки

        Returns:
            True если паттерн можно автоматизировать
        """
        # Проверяем уровень автоматизации
        if self.automation_level < self.min_automation_threshold:
            return False

        # Проверяем условия активации
        for condition_key, condition_value in self.trigger_conditions.items():
            context_value = context.get(condition_key)
            if context_value != condition_value:
                return False

        return True

    def get_effectiveness_score(self) -> float:
        """
        Получить оценку эффективности паттерна.

        Returns:
            Оценка эффективности (0.0-1.0)
        """
        if self.total_executions == 0:
            return 0.0

        # Комбинированная метрика: success_rate + automation_level + experience_factor
        experience_factor = min(1.0, self.total_executions / 10.0)  # Нормализация опыта

        return (
            self.success_rate * 0.5 +
            self.automation_level * 0.3 +
            experience_factor * 0.2
        )


@dataclass
class DecisionPattern:
    """
    Паттерн принятия решений - ассоциация между условиями и успешными решениями.
    """
    pattern_id: str
    conditions: Dict[str, Any]  # Условия ситуации
    decision: str  # Принятое решение
    outcome: str  # Результат решения
    confidence: float  # Уверенность в паттерне
    usage_count: int = 0  # Количество использований

    def matches(self, current_conditions: Dict[str, Any]) -> float:
        """
        Проверить соответствие текущим условиям.

        Args:
            current_conditions: Текущие условия

        Returns:
            Степень соответствия (0.0-1.0)
        """
        if not self.conditions:
            return 0.0

        matches = 0
        total_conditions = len(self.conditions)

        for key, expected_value in self.conditions.items():
            current_value = current_conditions.get(key)
            if current_value == expected_value:
                matches += 1

        return matches / total_conditions if total_conditions > 0 else 0.0


class ProceduralMemoryStore:
    """
    Хранилище процедурной памяти.

    Управляет навыками и автоматизмами поведения, обеспечивая:
    - Хранение и извлечение поведенческих паттернов
    - Автоматическое выполнение рутинных задач
    - Обучение на успешном опыте
    - Оптимизацию поведения через автоматизацию
    """

    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Инициализация процедурного хранилища.

        Args:
            logger: Логгер для структурированного логирования
        """
        self.logger = logger or StructuredLogger(__name__)

        # Хранилище паттернов: pattern_id -> ProceduralPattern
        self._patterns: Dict[str, ProceduralPattern] = {}

        # Хранилище паттернов решений: condition_hash -> DecisionPattern
        self._decision_patterns: Dict[str, DecisionPattern] = {}

        # Индексы для быстрого поиска
        self._action_sequences: Dict[Tuple[str, ...], List[str]] = defaultdict(list)  # action_types -> pattern_ids
        self._trigger_conditions_index: Dict[str, List[str]] = defaultdict(list)  # condition_key -> pattern_ids

        # Статистика
        self._stats = {
            "total_patterns": 0,
            "total_decision_patterns": 0,
            "automated_executions": 0,
            "manual_executions": 0,
            "last_optimization": time.time()
        }

        self.logger.log_event({
            "event_type": "procedural_store_initialized"
        })

    def add_pattern(self, pattern: ProceduralPattern) -> None:
        """
        Добавить новый процедурный паттерн.

        Args:
            pattern: Паттерн для добавления
        """
        if pattern.pattern_id in self._patterns:
            # Обновляем существующий паттерн
            existing = self._patterns[pattern.pattern_id]
            existing.success_count += pattern.success_count
            existing.failure_count += pattern.failure_count
            existing.total_executions += pattern.total_executions
            existing._update_execution_metrics(0, True)  # Пересчитываем метрики
        else:
            # Добавляем новый паттерн
            self._patterns[pattern.pattern_id] = pattern
            self._stats["total_patterns"] += 1

            # Обновляем индексы
            self._update_pattern_indexes(pattern)

        self.logger.log_event({
            "event_type": "procedural_pattern_added",
            "pattern_id": pattern.pattern_id,
            "pattern_name": pattern.name,
            "automation_level": pattern.automation_level
        })

    def get_pattern(self, pattern_id: str) -> Optional[ProceduralPattern]:
        """
        Получить паттерн по ID.

        Args:
            pattern_id: Идентификатор паттерна

        Returns:
            Паттерн или None если не найден
        """
        return self._patterns.get(pattern_id)

    def find_applicable_patterns(self, context: Dict[str, Any]) -> List[Tuple[ProceduralPattern, float]]:
        """
        Найти паттерны, применимые в текущем контексте.

        Args:
            context: Текущий контекст

        Returns:
            Список (паттерн, релевантность) отсортированный по релевантности
        """
        applicable = []

        for pattern in self._patterns.values():
            relevance = self._calculate_pattern_relevance(pattern, context)
            if relevance > 0:
                applicable.append((pattern, relevance))

        # Сортируем по релевантности
        applicable.sort(key=lambda x: x[1], reverse=True)
        return applicable

    def execute_best_pattern(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Выполнить наиболее подходящий паттерн в текущем контексте.

        Args:
            context: Контекст выполнения

        Returns:
            Результат выполнения или None если подходящих паттернов нет
        """
        applicable_patterns = self.find_applicable_patterns(context)

        if not applicable_patterns:
            return None

        # Выбираем лучший паттерн (с максимальной релевантностью)
        best_pattern, relevance = applicable_patterns[0]

        # Проверяем, можно ли автоматизировать
        if best_pattern.can_automate(context):
            self._stats["automated_executions"] += 1
            result = best_pattern.execute(context)

            self.logger.log_event({
                "event_type": "procedural_pattern_automated_execution",
                "pattern_id": best_pattern.pattern_id,
                "relevance": relevance,
                "success": result.get("success", False)
            })

            return result
        else:
            self._stats["manual_executions"] += 1
            return None

    def learn_from_experience(self, context: Dict[str, Any], actions: List[Tuple[str, Dict[str, Any]]],
                            outcome: str, success: bool) -> None:
        """
        Извлечь урок из опыта выполнения действий.

        Args:
            context: Контекст выполнения
            actions: Выполненные действия
            outcome: Результат выполнения
            success: Успешность выполнения
        """
        # Создаем паттерн из последовательности действий
        pattern_id = f"pattern_{len(self._patterns)}_{int(time.time())}"

        pattern = ProceduralPattern(
            pattern_id=pattern_id,
            name=f"Learned pattern from {'successful' if success else 'failed'} experience",
            description=f"Pattern learned from experience with outcome: {outcome}",
            action_sequence=actions,
            trigger_conditions=context.copy()
        )

        # Если опыт успешный, сразу повышаем уровень автоматизации
        if success:
            pattern.success_count = 1
            pattern.total_executions = 1
            pattern.automation_level = 0.3  # Начальный уровень для успешных паттернов
        else:
            pattern.failure_count = 1
            pattern.total_executions = 1
            pattern.automation_level = 0.1  # Низкий уровень для неудачных паттернов

        self.add_pattern(pattern)

        # Также сохраняем паттерн решений
        self._learn_decision_pattern(context, actions[0][0] if actions else "unknown", outcome, success)

        self.logger.log_event({
            "event_type": "procedural_learning_from_experience",
            "pattern_id": pattern_id,
            "success": success,
            "outcome": outcome,
            "actions_count": len(actions)
        })

    def _learn_decision_pattern(self, conditions: Dict[str, Any], decision: str,
                               outcome: str, success: bool) -> None:
        """Извлечь паттерн принятия решений."""
        # Создаем хэш условий для индексации
        condition_hash = hash(frozenset(conditions.items()))

        pattern = DecisionPattern(
            pattern_id=f"decision_{condition_hash}_{int(time.time())}",
            conditions=conditions,
            decision=decision,
            outcome=outcome,
            confidence=0.8 if success else 0.3
        )

        self._decision_patterns[str(condition_hash)] = pattern
        self._stats["total_decision_patterns"] += 1

    def get_decision_recommendation(self, current_conditions: Dict[str, Any]) -> Optional[str]:
        """
        Получить рекомендацию по принятию решения на основе прошлого опыта.

        Args:
            current_conditions: Текущие условия

        Returns:
            Рекомендуемое решение или None
        """
        best_match = None
        best_score = 0.0

        for pattern in self._decision_patterns.values():
            match_score = pattern.matches(current_conditions)
            if match_score > best_score and match_score > 0.7:  # Минимальный порог соответствия
                best_score = match_score
                best_match = pattern

        if best_match:
            self.logger.log_event({
                "event_type": "decision_recommendation_given",
                "pattern_id": best_match.pattern_id,
                "recommended_decision": best_match.decision,
                "confidence": best_match.confidence,
                "match_score": best_score
            })

            return best_match.decision

        return None

    def _calculate_pattern_relevance(self, pattern: ProceduralPattern, context: Dict[str, Any]) -> float:
        """
        Рассчитать релевантность паттерна для текущего контекста.

        Args:
            pattern: Паттерн для оценки
            context: Текущий контекст

        Returns:
            Оценка релевантности (0.0-1.0)
        """
        # Проверяем условия активации
        condition_match = 0.0
        if pattern.trigger_conditions:
            matches = 0
            for key, expected_value in pattern.trigger_conditions.items():
                if context.get(key) == expected_value:
                    matches += 1
            condition_match = matches / len(pattern.trigger_conditions)

        # Учитываем эффективность паттерна
        effectiveness = pattern.get_effectiveness_score()

        # Учитываем недавность использования
        recency_factor = 1.0
        if pattern.last_execution > 0:
            time_since_last = time.time() - pattern.last_execution
            # Экспоненциальное затухание: каждый час -10%
            recency_factor = 0.9 ** (time_since_last / 3600)

        # Комбинированная релевантность
        relevance = (
            condition_match * 0.4 +
            effectiveness * 0.4 +
            recency_factor * 0.2
        )

        return relevance

    def _update_pattern_indexes(self, pattern: ProceduralPattern) -> None:
        """Обновить индексы для паттерна."""
        # Индекс по последовательностям действий
        action_types = tuple(action[0] for action in pattern.action_sequence)
        self._action_sequences[action_types].append(pattern.pattern_id)

        # Индекс по условиям активации
        for condition_key in pattern.trigger_conditions.keys():
            self._trigger_conditions_index[condition_key].append(pattern.pattern_id)

    def optimize_patterns(self) -> int:
        """
        Оптимизировать паттерны - удалить неэффективные и консолидировать похожие.

        Returns:
            Количество оптимизированных паттернов
        """
        optimizations = 0
        patterns_to_remove = []

        for pattern_id, pattern in self._patterns.items():
            effectiveness = pattern.get_effectiveness_score()

            # Удаляем паттерны с низкой эффективностью и редким использованием
            if effectiveness < 0.2 and pattern.total_executions < 3:
                patterns_to_remove.append(pattern_id)
                optimizations += 1

            # Понижаем уровень автоматизации для паттернов с низким success rate
            elif pattern.success_rate < 0.3 and pattern.automation_level > 0.2:
                pattern.automation_level = max(0.0, pattern.automation_level - 0.1)
                optimizations += 1

        # Удаляем неэффективные паттерны
        for pattern_id in patterns_to_remove:
            self._remove_pattern(pattern_id)

        self._stats["last_optimization"] = time.time()

        if optimizations > 0:
            self.logger.log_event({
                "event_type": "procedural_patterns_optimized",
                "optimizations": optimizations
            })

        return optimizations

    def _remove_pattern(self, pattern_id: str) -> None:
        """Удалить паттерн и обновить индексы."""
        if pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]

            # Удаляем из индексов
            action_types = tuple(action[0] for action in pattern.action_sequence)
            if pattern_id in self._action_sequences[action_types]:
                self._action_sequences[action_types].remove(pattern_id)

            for condition_key in pattern.trigger_conditions.keys():
                if pattern_id in self._trigger_conditions_index[condition_key]:
                    self._trigger_conditions_index[condition_key].remove(pattern_id)

            # Удаляем паттерн
            del self._patterns[pattern_id]
            self._stats["total_patterns"] -= 1

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику процедурного хранилища.

        Returns:
            Статистика использования
        """
        total_executions = self._stats["automated_executions"] + self._stats["manual_executions"]
        automation_rate = (
            self._stats["automated_executions"] / total_executions
            if total_executions > 0 else 0
        )

        # Средняя эффективность паттернов
        avg_effectiveness = 0.0
        if self._patterns:
            avg_effectiveness = sum(
                p.get_effectiveness_score() for p in self._patterns.values()
            ) / len(self._patterns)

        return {
            "total_patterns": self._stats["total_patterns"],
            "total_decision_patterns": self._stats["total_decision_patterns"],
            "automated_executions": self._stats["automated_executions"],
            "manual_executions": self._stats["manual_executions"],
            "automation_rate": automation_rate,
            "average_pattern_effectiveness": avg_effectiveness,
            "last_optimization": self._stats["last_optimization"]
        }

    def clear_store(self) -> None:
        """Очистить все данные хранилища."""
        self._patterns.clear()
        self._decision_patterns.clear()
        self._action_sequences.clear()
        self._trigger_conditions_index.clear()
        self._stats = {
            "total_patterns": 0,
            "total_decision_patterns": 0,
            "automated_executions": 0,
            "manual_executions": 0,
            "last_optimization": time.time()
        }

        self.logger.log_event({
            "event_type": "procedural_store_cleared"
        })
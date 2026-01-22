"""
Decision Recorder - запись истории решений

Отвечает только за хранение и анализ истории принятых решений.
"""
import time
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DecisionRecord:
    """Запись о принятом решении."""
    timestamp: float
    decision_type: str
    context: Dict[str, Any]
    outcome: Optional[str] = None
    success: Optional[bool] = None
    execution_time: Optional[float] = None
    pattern: Optional[str] = None


class DecisionRecorder:
    """
    Записывает и анализирует историю решений.

    Отвечает за:
    - Хранение истории решений
    - Расчет статистики
    - Анализ паттернов принятия решений
    """

    def __init__(self, max_history_size: int = 1000, enable_logging: bool = False):
        """
        Инициализация рекордера решений.

        Args:
            max_history_size: Максимальный размер истории
            enable_logging: Включить детальное логирование (feature flag)
        """
        self.max_history_size = max_history_size
        self.enable_logging = enable_logging
        self.decision_history: List[DecisionRecord] = []
        self.decision_stats = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "average_time": 0.0,
            "accuracy": 0.8,
            "pattern_distribution": {},
        }
        self._lock = threading.RLock()  # Reentrant lock для thread safety

    def record_decision(
        self,
        decision_type: str,
        context: Dict[str, Any],
        pattern: str,
        outcome: Optional[str] = None,
        success: Optional[bool] = None,
        execution_time: Optional[float] = None
    ) -> None:
        """
        Записать решение в историю.

        Args:
            decision_type: Тип решения
            context: Контекст принятия решения
            pattern: Выбранный паттерн реакции
            outcome: Результат решения
            success: Успешность решения
            execution_time: Время выполнения решения
        """
        if not self.enable_logging:
            return

        record = DecisionRecord(
            timestamp=time.time(),
            decision_type=decision_type,
            context=context.copy() if context else {},
            outcome=outcome,
            success=success,
            execution_time=execution_time,
            pattern=pattern,
        )

        with self._lock:
            self.decision_history.append(record)

            # Обновляем статистику
            self.decision_stats["total_decisions"] += 1
            if success is not None and success:
                self.decision_stats["successful_decisions"] += 1

            # Распределение паттернов
            self.decision_stats["pattern_distribution"][pattern] = (
                self.decision_stats["pattern_distribution"].get(pattern, 0) + 1
            )

            if execution_time is not None:
                # Экспоненциальное сглаживание среднего времени
                alpha = 0.1
                if self.decision_stats["average_time"] == 0:
                    self.decision_stats["average_time"] = execution_time
                else:
                    self.decision_stats["average_time"] = (
                        alpha * execution_time + (1 - alpha) * self.decision_stats["average_time"]
                    )

            # Ограничиваем историю
            if len(self.decision_history) > self.max_history_size:
                self.decision_history = self.decision_history[-self.max_history_size:]

    def get_recent_decisions(self, limit: int = 100) -> List[DecisionRecord]:
        """
        Получить недавние решения.

        Args:
            limit: Максимальное количество решений для возврата

        Returns:
            Список недавних решений
        """
        with self._lock:
            return list(reversed(self.decision_history[-limit:]))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику принятия решений.

        Returns:
            Dict со статистикой
        """
        with self._lock:
            stats = self.decision_stats.copy()

            # Вычисляем точность на основе успешных решений
            total = stats["total_decisions"]
            if total > 0:
                stats["accuracy"] = stats["successful_decisions"] / total
            else:
                stats["accuracy"] = 0.0

            return stats

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Анализ паттернов принятия решений.

        Returns:
            Анализ паттернов
        """
        with self._lock:
            if not self.decision_history:
                return {"pattern_trends": {}, "success_rates": {}, "avg_times": {}}

            # Анализ последних 50 решений
            recent = self.decision_history[-50:]

            pattern_trends = {}
            success_rates = {}
            avg_times = {}

            for record in recent:
                pattern = record.pattern
                if pattern:
                    # Тренды паттернов
                    pattern_trends[pattern] = pattern_trends.get(pattern, 0) + 1

                    # Успешность по паттернам
                    if record.success is not None:
                        if pattern not in success_rates:
                            success_rates[pattern] = {"total": 0, "success": 0}
                        success_rates[pattern]["total"] += 1
                        if record.success:
                            success_rates[pattern]["success"] += 1

                    # Среднее время по паттернам
                    if record.execution_time is not None:
                        if pattern not in avg_times:
                            avg_times[pattern] = []
                        avg_times[pattern].append(record.execution_time)

            # Вычисляем средние значения
            for pattern, times in avg_times.items():
                avg_times[pattern] = sum(times) / len(times) if times else 0.0

            for pattern, rates in success_rates.items():
                total = rates["total"]
                success_rates[pattern] = rates["success"] / total if total > 0 else 0.0

            return {
                "pattern_trends": pattern_trends,
                "success_rates": success_rates,
                "avg_times": avg_times,
            }
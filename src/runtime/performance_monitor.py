"""
Performance Monitor для измерения влияния компонентов на производительность системы.

Отслеживает время выполнения ключевых операций и их влияние на общую производительность.
"""

import time
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class PerformanceMetrics:
    """Метрики производительности для компонента."""
    total_calls: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    recent_calls: list = field(default_factory=list)  # Последние 10 вызовов

    def add_measurement(self, execution_time: float):
        """Добавить измерение времени выполнения."""
        self.total_calls += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.total_calls
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)

        # Храним последние 10 измерений
        self.recent_calls.append(execution_time)
        if len(self.recent_calls) > 10:
            self.recent_calls = self.recent_calls[-10:]

    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку метрик."""
        return {
            "total_calls": self.total_calls,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time if self.min_time != float('inf') else 0.0,
            "max_time": self.max_time,
            "recent_avg": sum(self.recent_calls) / len(self.recent_calls) if self.recent_calls else 0.0,
        }


class PerformanceMonitor:
    """
    Монитор производительности компонентов системы.

    Отслеживает время выполнения операций и их влияние на общую производительность.
    """

    def __init__(self):
        """Инициализация монитора."""
        self.metrics: Dict[str, PerformanceMetrics] = defaultdict(PerformanceMetrics)
        self.enabled = True

    def enable(self):
        """Включить мониторинг производительности."""
        self.enabled = True

    def disable(self):
        """Отключить мониторинг производительности."""
        self.enabled = False

    @contextmanager
    def measure(self, component_name: str, operation_name: str = "default"):
        """
        Контекстный менеджер для измерения времени выполнения операции.

        Args:
            component_name: Имя компонента
            operation_name: Имя операции
        """
        if not self.enabled:
            yield
            return

        key = f"{component_name}.{operation_name}"
        start_time = time.time()

        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.metrics[key].add_measurement(execution_time)

    def measure_function(self, component_name: str, operation_name: str = "default"):
        """
        Декоратор для измерения времени выполнения функции.

        Args:
            component_name: Имя компонента
            operation_name: Имя операции
        """
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                with self.measure(component_name, operation_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def get_metrics(self, component_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить метрики производительности.

        Args:
            component_name: Имя компонента (если None, возвращает все метрики)

        Returns:
            Dict с метриками
        """
        if component_name:
            # Метрики конкретного компонента
            component_metrics = {
                key: metrics.get_summary()
                for key, metrics in self.metrics.items()
                if key.startswith(f"{component_name}.")
            }
            return component_metrics
        else:
            # Все метрики
            return {
                key: metrics.get_summary()
                for key, metrics in self.metrics.items()
            }

    def get_overall_impact(self) -> Dict[str, Any]:
        """
        Получить общую оценку влияния на производительность.

        Returns:
            Анализ общего влияния компонентов
        """
        all_metrics = self.get_metrics()

        if not all_metrics:
            return {"status": "no_data", "message": "Нет данных для анализа"}

        # Анализ самых медленных операций
        slowest_operations = sorted(
            all_metrics.items(),
            key=lambda x: x[1]["avg_time"],
            reverse=True
        )[:5]

        # Общая статистика
        total_operations = sum(m["total_calls"] for m in all_metrics.values())
        total_time = sum(m["total_time"] for m in all_metrics.values())

        return {
            "total_operations": total_operations,
            "total_time_spent": total_time,
            "avg_time_per_operation": total_time / total_operations if total_operations > 0 else 0,
            "slowest_operations": [
                {
                    "operation": op,
                    "avg_time": metrics["avg_time"],
                    "total_calls": metrics["total_calls"],
                    "total_time": metrics["total_time"]
                }
                for op, metrics in slowest_operations
            ],
            "performance_impact": "high" if total_time > 1.0 else "medium" if total_time > 0.1 else "low"
        }

    def reset(self):
        """Сбросить все метрики."""
        self.metrics.clear()


# Глобальный экземпляр монитора производительности
performance_monitor = PerformanceMonitor()
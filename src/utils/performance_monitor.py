"""
Мониторинг производительности для компонентов системы Life.

Предоставляет инструменты для измерения времени выполнения операций,
отслеживания использования ресурсов и выявления узких мест производительности.
"""

import time
import statistics
from collections import defaultdict, deque
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PerformanceMetrics:
    """
    Метрики производительности для операции или компонента.

    Хранит статистику о времени выполнения, частоте вызовов и трендах.
    """

    operation_name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    avg_time: float = 0.0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    start_time: Optional[float] = None

    def record_call(self, duration: float) -> None:
        """Записывает вызов операции с заданным временем выполнения."""
        self.call_count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.recent_times.append(duration)

        # Обновляем среднее время
        if self.call_count > 0:
            self.avg_time = self.total_time / self.call_count

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику производительности."""
        recent_times_list = list(self.recent_times)
        return {
            "operation_name": self.operation_name,
            "call_count": self.call_count,
            "total_time": round(self.total_time, 4),
            "min_time": round(self.min_time, 4) if self.min_time != float('inf') else 0.0,
            "max_time": round(self.max_time, 4),
            "avg_time": round(self.avg_time, 4),
            "recent_calls": len(recent_times_list),
            "recent_avg": round(statistics.mean(recent_times_list), 4) if recent_times_list else 0.0,
            "recent_stdev": round(statistics.stdev(recent_times_list), 4) if len(recent_times_list) > 1 else 0.0,
        }

    def reset(self) -> None:
        """Сбрасывает все метрики."""
        self.call_count = 0
        self.total_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0
        self.avg_time = 0.0
        self.recent_times.clear()
        self.start_time = None


class PerformanceMonitor:
    """
    Монитор производительности для компонентов системы Life.

    Предоставляет декораторы и контекстные менеджеры для измерения
    производительности операций.
    """

    def __init__(self, max_metrics_history: int = 1000):
        """
        Инициализация монитора производительности.

        Args:
            max_metrics_history: Максимальное количество хранимых метрик
        """
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.max_metrics_history = max_metrics_history
        self._enabled = True

    def enable(self) -> None:
        """Включает сбор метрик производительности."""
        self._enabled = True

    def disable(self) -> None:
        """Отключает сбор метрик производительности."""
        self._enabled = False

    @contextmanager
    def measure(self, operation_name: str):
        """
        Контекстный менеджер для измерения времени выполнения операции.

        Usage:
            with monitor.measure("intensity_adaptation"):
                result = adapter.adapt_intensity(...)
        """
        if not self._enabled:
            yield
            return

        start_time = time.perf_counter()

        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self._record_operation(operation_name, duration)

    def measure_func(self, operation_name: Optional[str] = None):
        """
        Декоратор для измерения времени выполнения функции.

        Usage:
            @monitor.measure_func("generate_event")
            def generate(self, context_state):
                ...
        """
        def decorator(func):
            name = operation_name or f"{func.__module__}.{func.__qualname__}"

            def wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)

                with self.measure(name):
                    return func(*args, **kwargs)

            return wrapper
        return decorator

    def _record_operation(self, operation_name: str, duration: float) -> None:
        """Записывает выполнение операции."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = PerformanceMetrics(operation_name)

        self.metrics[operation_name].record_call(duration)

        # Ограничиваем количество метрик
        if len(self.metrics) > self.max_metrics_history:
            # Удаляем самую старую метрику (простая стратегия)
            oldest_key = min(self.metrics.keys(), key=lambda k: self.metrics[k].call_count)
            del self.metrics[oldest_key]

    def get_metrics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Возвращает метрики производительности.

        Args:
            operation_name: Имя операции (если None, возвращает все метрики)

        Returns:
            Метрики производительности
        """
        if operation_name:
            if operation_name in self.metrics:
                return {operation_name: self.metrics[operation_name].get_stats()}
            else:
                return {}

        return {name: metric.get_stats() for name, metric in self.metrics.items()}

    def get_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку производительности по всем операциям.

        Returns:
            Сводная статистика производительности
        """
        all_stats = self.get_metrics()

        if not all_stats:
            return {"total_operations": 0, "total_calls": 0, "total_time": 0.0}

        total_calls = sum(stats["call_count"] for stats in all_stats.values())
        total_time = sum(stats["total_time"] for stats in all_stats.values())

        # Находим самые медленные операции
        slowest_ops = sorted(
            all_stats.items(),
            key=lambda x: x[1]["avg_time"],
            reverse=True
        )[:5]

        return {
            "total_operations": len(all_stats),
            "total_calls": total_calls,
            "total_time": round(total_time, 4),
            "avg_time_per_call": round(total_time / total_calls, 4) if total_calls > 0 else 0.0,
            "slowest_operations": slowest_ops,
            "enabled": self._enabled
        }

    def reset(self, operation_name: Optional[str] = None) -> None:
        """
        Сбрасывает метрики.

        Args:
            operation_name: Имя операции (если None, сбрасывает все)
        """
        if operation_name:
            if operation_name in self.metrics:
                self.metrics[operation_name].reset()
        else:
            self.metrics.clear()

    def get_performance_alerts(self) -> List[str]:
        """
        Возвращает список предупреждений о проблемах производительности.

        Returns:
            Список строк с предупреждениями
        """
        alerts = []
        all_stats = self.get_metrics()

        for name, stats in all_stats.items():
            # Предупреждение о медленных операциях
            if stats["avg_time"] > 0.01:  # Более 10мс в среднем
                alerts.append(f"Операция '{name}' слишком медленная: {stats['avg_time']:.4f}s среднее время")

            # Предупреждение о высоком разбросе времени
            if stats["recent_stdev"] > stats["recent_avg"] * 0.5 and stats["recent_calls"] > 10:
                alerts.append(f"Операция '{name}' имеет нестабильное время выполнения")

            # Предупреждение о большом количестве вызовов
            if stats["call_count"] > 10000:
                alerts.append(f"Операция '{name}' вызывается слишком часто: {stats['call_count']} вызовов")

        return alerts


# Глобальный экземпляр монитора для удобства использования
performance_monitor = PerformanceMonitor()
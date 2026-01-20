"""
Модуль для измерения производительности критических операций.
"""

import logging
import time
from contextlib import contextmanager
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Класс для сбора метрик производительности."""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.current_measurements: Dict[str, float] = {}

    def start_measurement(self, operation: str):
        """Начинает измерение времени выполнения операции."""
        self.current_measurements[operation] = time.perf_counter()

    def end_measurement(self, operation: str) -> float:
        """Завершает измерение и возвращает время выполнения."""
        if operation not in self.current_measurements:
            return 0.0

        start_time = self.current_measurements.pop(operation)
        duration = time.perf_counter() - start_time

        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)

        return duration

    def get_average_time(self, operation: str) -> Optional[float]:
        """Возвращает среднее время выполнения операции."""
        if operation not in self.metrics or not self.metrics[operation]:
            return None
        return sum(self.metrics[operation]) / len(self.metrics[operation])

    def get_last_time(self, operation: str) -> Optional[float]:
        """Возвращает время последнего выполнения операции."""
        if operation not in self.metrics or not self.metrics[operation]:
            return None
        return self.metrics[operation][-1]

    def log_summary(self):
        """Логирует сводку по метрикам производительности."""
        for operation, times in self.metrics.items():
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                logger.info(
                    f"Performance: {operation} - avg: {avg_time:.4f}s, "
                    f"min: {min_time:.4f}s, max: {max_time:.4f}s, count: {len(times)}"
                )


# Глобальный экземпляр для метрик
performance_metrics = PerformanceMetrics()


@contextmanager
def measure_time(operation: str):
    """
    Контекстный менеджер для измерения времени выполнения операции.

    Usage:
        with measure_time("save_snapshot"):
            save_snapshot(state)
    """
    performance_metrics.start_measurement(operation)
    try:
        yield
    finally:
        duration = performance_metrics.end_measurement(operation)
        logger.debug(f"Operation {operation} took {duration:.4f}s")

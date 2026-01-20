"""
Базовые значения и пороги для performance бенчмарков.

Этот модуль содержит baseline значения производительности и пороги для обнаружения регрессий.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceBaseline:
    """
    Управление baseline значениями производительности и порогами регрессий.
    """

    def __init__(self, baseline_file: str = "data/performance_baseline.json"):
        self.baseline_file = Path(baseline_file)
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        self.baselines = self._load_baselines()

    def _load_baselines(self) -> Dict[str, Any]:
        """Загружает baseline значения из файла."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(
                    f"Не удалось загрузить baseline файл {self.baseline_file}: {e}"
                )
                return {}
        return {}

    def _save_baselines(self):
        """Сохраняет baseline значения в файл."""
        try:
            with open(self.baseline_file, "w", encoding="utf-8") as f:
                json.dump(self.baselines, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(
                f"Не удалось сохранить baseline файл {self.baseline_file}: {e}"
            )

    def get_baseline(self, test_name: str, metric: str) -> Optional[float]:
        """Получить baseline значение для теста и метрики."""
        return self.baselines.get(test_name, {}).get(metric)

    def set_baseline(self, test_name: str, metric: str, value: float):
        """Установить baseline значение."""
        if test_name not in self.baselines:
            self.baselines[test_name] = {}
        self.baselines[test_name][metric] = value
        self._save_baselines()

    def check_regression(
        self,
        test_name: str,
        metric: str,
        current_value: float,
        threshold_percent: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Проверить на регрессию производительности.

        Args:
            test_name: Имя теста
            metric: Название метрики (например, 'elapsed', 'ticks_per_second')
            current_value: Текущее измеренное значение
            threshold_percent: Порог регрессии в процентах

        Returns:
            Словарь с результатами проверки:
            {
                'is_regression': bool,
                'baseline_value': float or None,
                'current_value': float,
                'deviation_percent': float or None,
                'threshold_percent': float,
                'message': str
            }
        """
        baseline_value = self.get_baseline(test_name, metric)

        if baseline_value is None:
            return {
                "is_regression": False,
                "baseline_value": None,
                "current_value": current_value,
                "deviation_percent": None,
                "threshold_percent": threshold_percent,
                "message": f"Нет baseline значения для {test_name}.{metric}",
            }

        # Для разных метрик разные правила сравнения
        if metric in [
            "elapsed",
            "push_elapsed",
            "pop_elapsed",
            "process_elapsed",
            "adjust_elapsed",
            "analyze_time_per_call",
            "apply_time_per_call",
        ]:
            # Для времени: регрессия если текущее время > baseline * (1 + threshold/100)
            regression_threshold = baseline_value * (1 + threshold_percent / 100)
            is_regression = current_value > regression_threshold
            deviation_percent = (
                (current_value - baseline_value) / baseline_value
            ) * 100
        elif metric in ["ticks_per_second"]:
            # Для производительности: регрессия если текущее значение < baseline * (1 - threshold/100)
            regression_threshold = baseline_value * (1 - threshold_percent / 100)
            is_regression = current_value < regression_threshold
            deviation_percent = (
                (baseline_value - current_value) / baseline_value
            ) * 100
        else:
            # По умолчанию: регрессия если отклонение > threshold_percent
            deviation_percent = (
                abs((current_value - baseline_value) / baseline_value) * 100
            )
            is_regression = deviation_percent > threshold_percent

        if is_regression:
            message = f"🚨 РЕГРЕССИЯ: {test_name}.{metric} " ".2f" ".1f"
        else:
            message = f"✅ OK: {test_name}.{metric} " ".2f" ".1f"

        return {
            "is_regression": is_regression,
            "baseline_value": baseline_value,
            "current_value": current_value,
            "deviation_percent": deviation_percent,
            "threshold_percent": threshold_percent,
            "message": message,
        }


# Глобальный экземпляр
performance_baseline = PerformanceBaseline()


# Функция для pytest fixtures
def update_baseline_if_needed(
    test_name: str, metrics: Dict[str, float], force_update: bool = False
):
    """
    Обновить baseline значения если нужно.

    Args:
        test_name: Имя теста
        metrics: Словарь метрик и их значений
        force_update: Принудительно обновить baseline
    """
    # Проверяем переменную окружения для принудительного обновления
    force_update = force_update or os.getenv("PERFORMANCE_UPDATE_BASELINE") == "1"

    for metric, value in metrics.items():
        current_baseline = performance_baseline.get_baseline(test_name, metric)

        if current_baseline is None or force_update:
            performance_baseline.set_baseline(test_name, metric, value)
            logger.info(f"Установлен baseline для {test_name}.{metric}: {value}")
        else:
            # Проверяем на значительное улучшение (>20% лучше)
            if metric in [
                "elapsed",
                "push_elapsed",
                "pop_elapsed",
                "process_elapsed",
                "adjust_elapsed",
                "analyze_time_per_call",
                "apply_time_per_call",
            ]:
                if value < current_baseline * 0.8:  # 20% улучшение
                    performance_baseline.set_baseline(test_name, metric, value)
                    logger.info(
                        f"Обновлен baseline для {test_name}.{metric}: {current_baseline:.4f} -> {value:.4f} (улучшение)"
                    )
            elif metric in ["ticks_per_second"]:
                if value > current_baseline * 1.2:  # 20% улучшение
                    performance_baseline.set_baseline(test_name, metric, value)
                    logger.info(
                        f"Обновлен baseline для {test_name}.{metric}: {current_baseline:.1f} -> {value:.1f} (улучшение)"
                    )


# Дефолтные пороги для разных типов метрик
DEFAULT_THRESHOLDS = {
    "time_based": 15.0,  # 15% для временных метрик
    "performance_based": 10.0,  # 10% для метрик производительности
    "count_based": 5.0,  # 5% для счетчиков
}

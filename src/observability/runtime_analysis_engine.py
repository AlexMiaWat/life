"""
Runtime Analysis Engine - Движок анализа в реальном времени.

Интегрирует инструменты анализа в runtime loop для обеспечения
реального времени обратной связи и адаптивного поведения.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from collections import deque

from .log_analysis import analyze_logs, get_performance_metrics, get_error_summary
from .structured_logger import StructuredLogger

logger = logging.getLogger(__name__)


class AnalysisResult:
    """
    Результат анализа для использования в runtime loop.
    """

    def __init__(self, analysis_type: str, data: Dict[str, Any], timestamp: float):
        self.analysis_type = analysis_type
        self.data = data
        self.timestamp = timestamp
        self.is_stale = False

    def mark_stale(self):
        """Пометить результат как устаревший."""
        self.is_stale = True

    def is_recent(self, max_age_seconds: float = 60.0) -> bool:
        """Проверить, является ли результат достаточно свежим."""
        return (time.time() - self.timestamp) < max_age_seconds and not self.is_stale


class ActiveRuntimeAnalysisEngine:
    """
    Активный движок анализа для интеграции в runtime loop.

    Предоставляет:
    - Анализ логов производительности по запросу
    - Мониторинг ошибок по требованию
    - Анализ трендов и аномалий
    - Интеграцию результатов анализа в принятие решений

    Note: Переименован из RuntimeAnalysisEngine для отражения активной природы
    анализа без фоновых потоков.
    """

    def __init__(
        self,
        log_path: str = "data/structured_log.jsonl",
        structured_logger: Optional[StructuredLogger] = None,
        analysis_interval: float = 30.0,  # Анализ каждые 30 секунд
        max_history_size: int = 100
    ):
        """
        Инициализация движка анализа.

        Args:
            log_path: Путь к файлу структурированных логов
            structured_logger: Экземпляр StructuredLogger для логирования анализа
            analysis_interval: Интервал между анализами (секунды)
            max_history_size: Максимальный размер истории результатов
        """
        self.log_path = log_path
        self.structured_logger = structured_logger
        self.analysis_interval = analysis_interval
        self.max_history_size = max_history_size

        # История результатов анализа
        self._analysis_history: Dict[str, deque] = {
            'performance': deque(maxlen=max_history_size),
            'errors': deque(maxlen=max_history_size),
            'trends': deque(maxlen=max_history_size),
        }

        # Текущие результаты
        self._current_results: Dict[str, AnalysisResult] = {}

        # Синхронизация
        self._lock = threading.RLock()

        # Время последнего анализа (для предотвращения слишком частого анализа)
        self._last_analysis_time = 0.0

        # Callbacks для обработки результатов
        self._result_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []

        logger.info(f"RuntimeAnalysisEngine initialized: interval={analysis_interval}s, log_path={log_path}")

    def perform_analysis(self) -> None:
        """
        Выполнить анализ по запросу.

        Анализирует логи производительности, ошибки и тренды,
        обновляет историю и вызывает callbacks.
        """
        current_time = time.time()

        # Предотвращаем слишком частый анализ
        if current_time - self._last_analysis_time < self.analysis_interval:
            return

        try:
            # Выполняем анализ всех типов
            self.trigger_immediate_analysis()
            self._last_analysis_time = current_time

        except Exception as e:
            logger.error(f"Error in ActiveRuntimeAnalysisEngine analysis: {e}")

    def add_result_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Добавить callback для обработки результатов анализа.

        Args:
            callback: Функция, принимающая (analysis_type, result_data)
        """
        with self._lock:
            self._result_callbacks.append(callback)

    def get_current_analysis(self, analysis_type: str) -> Optional[AnalysisResult]:
        """
        Получить текущий результат анализа.

        Args:
            analysis_type: Тип анализа ('performance', 'errors', 'trends')

        Returns:
            Текущий результат анализа или None
        """
        with self._lock:
            return self._current_results.get(analysis_type)

    def get_analysis_history(self, analysis_type: str, limit: Optional[int] = None) -> List[AnalysisResult]:
        """
        Получить историю результатов анализа.

        Args:
            analysis_type: Тип анализа
            limit: Максимальное количество записей

        Returns:
            Список результатов анализа
        """
        with self._lock:
            history = list(self._analysis_history.get(analysis_type, []))
            if limit:
                history = history[-limit:]
            return history

    def trigger_immediate_analysis(self, analysis_type: str = "all") -> Dict[str, Any]:
        """
        Запустить немедленный анализ.

        Args:
            analysis_type: Тип анализа ('performance', 'errors', 'trends', 'all')

        Returns:
            Результаты анализа
        """
        results = {}

        if analysis_type in ("performance", "all"):
            results["performance"] = self._analyze_performance()

        if analysis_type in ("errors", "all"):
            results["errors"] = self._analyze_errors()

        if analysis_type in ("trends", "all"):
            results["trends"] = self._analyze_trends()

        # Обновить текущие результаты
        with self._lock:
            for result_type, result_data in results.items():
                result = AnalysisResult(result_type, result_data, time.time())
                self._current_results[result_type] = result
                self._analysis_history[result_type].append(result)

                # Вызвать callbacks
                for callback in self._result_callbacks:
                    try:
                        callback(result_type, result_data)
                    except Exception as e:
                        logger.error(f"Error in analysis callback: {e}")

        # Логировать анализ
        if self.structured_logger:
            for result_type, result_data in results.items():
                self.structured_logger.log_event({
                    "event_type": f"analysis_{result_type}",
                    "analysis_result": result_data
                })

        return results


    def _analyze_performance(self) -> Dict[str, Any]:
        """Анализ производительности."""
        try:
            metrics = get_performance_metrics(self.log_path)

            # Дополнительные расчеты трендов
            history = self.get_analysis_history('performance', limit=10)
            if len(history) >= 2:
                recent_avg = sum(r.data.get('avg_tick_duration', 0) for r in history[-3:]) / 3
                older_avg = sum(r.data.get('avg_tick_duration', 0) for r in history[:-3]) / max(1, len(history) - 3)

                if older_avg > 0:
                    trend = (recent_avg - older_avg) / older_avg
                    metrics['performance_trend'] = trend
                    metrics['trend_direction'] = 'improving' if trend < -0.1 else 'degrading' if trend > 0.1 else 'stable'
                else:
                    metrics['performance_trend'] = 0.0
                    metrics['trend_direction'] = 'unknown'
            else:
                metrics['performance_trend'] = 0.0
                metrics['trend_direction'] = 'insufficient_data'

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {
                'error': str(e),
                'total_ticks': 0,
                'avg_tick_duration': 0,
                'performance_trend': 0.0,
                'trend_direction': 'error'
            }

    def _analyze_errors(self) -> Dict[str, Any]:
        """Анализ ошибок."""
        try:
            error_summary = get_error_summary(self.log_path)

            # Дополнительные расчеты трендов ошибок
            history = self.get_analysis_history('errors', limit=10)
            if len(history) >= 2:
                recent_errors = sum(r.data.get('total_errors', 0) for r in history[-3:])
                older_errors = sum(r.data.get('total_errors', 0) for r in history[:-3])

                if len(history) > 3:
                    older_count = len(history) - 3
                    error_trend = (recent_errors / 3) - (older_errors / older_count) if older_count > 0 else 0
                    error_summary['error_trend'] = error_trend
                    error_summary['error_trend_direction'] = 'improving' if error_trend < -1 else 'worsening' if error_trend > 1 else 'stable'
                else:
                    error_summary['error_trend'] = 0.0
                    error_summary['error_trend_direction'] = 'insufficient_data'
            else:
                error_summary['error_trend'] = 0.0
                error_summary['error_trend_direction'] = 'insufficient_data'

            return error_summary

        except Exception as e:
            logger.error(f"Error analyzing errors: {e}")
            return {
                'error': str(e),
                'total_errors': 0,
                'error_types': {},
                'recent_errors': [],
                'error_trend': 0.0,
                'error_trend_direction': 'error'
            }

    def _analyze_trends(self) -> Dict[str, Any]:
        """Анализ трендов."""
        try:
            # Анализ основных логов
            log_analysis = analyze_logs(self.log_path)

            # Вычисление трендов
            trends = {
                'total_entries': log_analysis.get('total_entries', 0),
                'error_rate': log_analysis.get('error_count', 0) / max(1, log_analysis.get('total_entries', 1)),
                'correlation_completeness': log_analysis.get('total_correlations', 0),
                'event_diversity': len(log_analysis.get('event_types', {})),
                'decision_consistency': len(log_analysis.get('decision_patterns', {})),
            }

            # Анализ трендов по истории
            perf_history = self.get_analysis_history('performance', limit=5)
            if perf_history:
                avg_durations = [r.data.get('avg_tick_duration', 0) for r in perf_history if r.data.get('avg_tick_duration', 0) > 0]
                if avg_durations:
                    trends['avg_performance_trend'] = sum(avg_durations) / len(avg_durations)
                else:
                    trends['avg_performance_trend'] = 0.0

            return trends

        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {
                'error': str(e),
                'total_entries': 0,
                'error_rate': 0.0,
                'correlation_completeness': 0,
                'event_diversity': 0,
                'decision_consistency': 0,
                'avg_performance_trend': 0.0
            }

    def get_recommendations(self) -> Dict[str, Any]:
        """
        Получить рекомендации на основе анализа.

        Returns:
            Словарь с рекомендациями
        """
        recommendations = {
            'performance': [],
            'errors': [],
            'general': []
        }

        # Анализ производительности
        perf_result = self.get_current_analysis('performance')
        if perf_result and perf_result.is_recent():
            perf_data = perf_result.data
            avg_duration = perf_data.get('avg_tick_duration', 0)
            slow_ticks = perf_data.get('slow_ticks_100ms', 0)

            if avg_duration > 0.050:  # > 50ms в среднем
                recommendations['performance'].append({
                    'severity': 'high',
                    'message': f'Среднее время тика {avg_duration:.3f}s превышает порог 50ms',
                    'action': 'Оптимизировать компоненты runtime loop'
                })

            if slow_ticks > 10:
                recommendations['performance'].append({
                    'severity': 'medium',
                    'message': f'{slow_ticks} тиков выполняются дольше 100ms',
                    'action': 'Проанализировать причины задержек'
                })

        # Анализ ошибок
        error_result = self.get_current_analysis('errors')
        if error_result and error_result.is_recent():
            error_data = error_result.data
            total_errors = error_data.get('total_errors', 0)
            trend = error_data.get('error_trend', 0)

            if total_errors > 50:
                recommendations['errors'].append({
                    'severity': 'high',
                    'message': f'Обнаружено {total_errors} ошибок в логах',
                    'action': 'Проанализировать причины ошибок'
                })

            if trend > 2:
                recommendations['errors'].append({
                    'severity': 'medium',
                    'message': 'Количество ошибок увеличивается',
                    'action': 'Мониторить систему на предмет проблем'
                })

        return recommendations
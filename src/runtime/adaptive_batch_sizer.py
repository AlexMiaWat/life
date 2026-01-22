"""
AdaptiveBatchSizer - класс для динамического определения оптимального размера батча событий.

Основная цель: оптимизировать обработку событий через адаптивное определение размера батча
на основе текущей нагрузки системы, паттернов событий и производительности.
"""

import logging
import time
import psutil
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class AdaptiveBatchSizer:
    """
    Класс для динамического определения оптимального размера батча событий.

    Основные возможности:
    - Мониторинг системных ресурсов (CPU, память)
    - Анализ паттернов событий (типы, частота, значимость)
    - Динамический расчет размера батча
    - Адаптация к изменяющимся условиям нагрузки
    """

    def __init__(self,
                 min_batch_size: int = 5,
                 max_batch_size: int = 100,
                 default_batch_size: int = 25,
                 adaptation_interval: int = 50,  # тиков между адаптациями
                 history_window: int = 20):  # размер окна истории для анализа

        # Основные параметры
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.default_batch_size = default_batch_size
        self.adaptation_interval = adaptation_interval

        # История для анализа паттернов
        self.batch_performance_history = deque(maxlen=history_window)
        self.system_load_history = deque(maxlen=history_window)
        self.event_pattern_history = deque(maxlen=history_window)

        # Текущие метрики
        self.current_batch_size = default_batch_size
        self.last_adaptation_tick = 0
        self.ticks_since_adaptation = 0

        # Коэффициенты адаптации
        self.cpu_weight = 0.3
        self.memory_weight = 0.3
        self.event_complexity_weight = 0.2
        self.performance_trend_weight = 0.2

        # Пороги нагрузки
        self.high_cpu_threshold = 80.0  # %
        self.high_memory_threshold = 85.0  # %
        self.low_performance_threshold = 0.010  # 10ms - низкая производительность

        logger.info(f"AdaptiveBatchSizer initialized: batch_size={default_batch_size}, "
                   f"range=[{min_batch_size}, {max_batch_size}]")

    def get_optimal_batch_size(self,
                              current_tick: int,
                              system_metrics: Optional[Dict[str, Any]] = None,
                              event_batch: Optional[List] = None) -> int:
        """
        Возвращает оптимальный размер батча для текущих условий.

        Args:
            current_tick: Текущий тик системы
            system_metrics: Метрики системы (CPU, память, etc.)
            event_batch: Текущий батч событий для анализа паттернов

        Returns:
            int: Оптимальный размер батча
        """
        self.ticks_since_adaptation += 1

        # Собираем метрики системы если не переданы
        if system_metrics is None:
            system_metrics = self._collect_system_metrics()

        # Анализируем паттерны событий если батч передан
        event_complexity = self._analyze_event_complexity(event_batch) if event_batch else 1.0

        # Проверяем необходимость адаптации
        should_adapt = (self.ticks_since_adaptation >= self.adaptation_interval)

        if should_adapt:
            self._adapt_batch_size(system_metrics, event_complexity, current_tick)
            self.ticks_since_adaptation = 0

        return self.current_batch_size

    def record_batch_performance(self,
                                batch_size: int,
                                processing_time: float,
                                events_processed: int,
                                significant_events: int):
        """
        Записывает результаты обработки батча для анализа производительности.

        Args:
            batch_size: Размер обработанного батча
            processing_time: Время обработки батча в секундах
            events_processed: Количество обработанных событий
            significant_events: Количество значимых событий
        """
        performance_record = {
            'batch_size': batch_size,
            'processing_time': processing_time,
            'events_processed': events_processed,
            'significant_events': significant_events,
            'time_per_event': processing_time / max(events_processed, 1),
            'significance_ratio': significant_events / max(events_processed, 1),
            'timestamp': time.time()
        }

        self.batch_performance_history.append(performance_record)

        logger.debug(f"Recorded batch performance: size={batch_size}, "
                    f"time={processing_time:.4f}s, events={events_processed}")

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """
        Собирает метрики текущей нагрузки системы.

        Returns:
            Dict с метриками системы
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # System load (if available)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()
            except (AttributeError, OSError):
                # getloadavg not available on Windows
                load_avg = (cpu_percent / 100.0, cpu_percent / 100.0, cpu_percent / 100.0)

            metrics = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'load_avg': load_avg,
                'timestamp': time.time()
            }

            self.system_load_history.append(metrics)

            return metrics

        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            # Возвращаем безопасные значения по умолчанию
            return {
                'cpu_percent': 50.0,
                'memory_percent': 50.0,
                'load_avg': (0.5, 0.5, 0.5),
                'timestamp': time.time()
            }

    def _analyze_event_complexity(self, event_batch: List) -> float:
        """
        Анализирует сложность батча событий.

        Args:
            event_batch: Список событий для анализа

        Returns:
            float: Коэффициент сложности (1.0 = средняя сложность)
        """
        if not event_batch:
            return 1.0

        try:
            # Анализируем типы событий
            event_types = {}
            total_intensity = 0.0
            significant_events = 0

            for event in event_batch:
                # Определяем тип события
                event_type = getattr(event, 'type', getattr(event, 'event_type', 'unknown'))
                event_types[event_type] = event_types.get(event_type, 0) + 1

                # Суммируем интенсивность
                intensity = getattr(event, 'intensity', 0.5)
                total_intensity += intensity

                # Считаем значимые события
                if intensity > 0.7:  # порог значимости
                    significant_events += 1

            # Вычисляем метрики сложности
            avg_intensity = total_intensity / len(event_batch)
            significance_ratio = significant_events / len(event_batch)

            # Разнообразие типов (энтропия)
            type_diversity = len(event_types) / max(len(event_batch), 1)

            # Комплексный коэффициент сложности
            complexity = (
                0.4 * avg_intensity +           # средняя интенсивность
                0.3 * significance_ratio +      # доля значимых событий
                0.3 * type_diversity            # разнообразие типов
            )

            # Нормализуем в разумные пределы
            complexity = max(0.1, min(3.0, complexity))

            logger.debug(f"Event complexity analysis: avg_intensity={avg_intensity:.2f}, "
                        f"significance_ratio={significance_ratio:.2f}, "
                        f"type_diversity={type_diversity:.2f}, complexity={complexity:.2f}")

            return complexity

        except Exception as e:
            logger.warning(f"Failed to analyze event complexity: {e}")
            return 1.0

    def _adapt_batch_size(self,
                         system_metrics: Dict[str, Any],
                         event_complexity: float,
                         current_tick: int):
        """
        Адаптирует размер батча на основе текущих метрик.

        Args:
            system_metrics: Метрики системы
            event_complexity: Коэффициент сложности событий
            current_tick: Текущий тик
        """
        try:
            # Анализируем тренд производительности
            performance_trend = self._calculate_performance_trend()

            # Вычисляем факторы влияния
            cpu_factor = self._calculate_cpu_factor(system_metrics['cpu_percent'])
            memory_factor = self._calculate_memory_factor(system_metrics['memory_percent'])
            complexity_factor = self._calculate_complexity_factor(event_complexity)
            performance_factor = self._calculate_performance_factor(performance_trend)

            # Комплексный фактор адаптации
            adaptation_factor = (
                self.cpu_weight * cpu_factor +
                self.memory_weight * memory_factor +
                self.event_complexity_weight * complexity_factor +
                self.performance_trend_weight * performance_factor
            )

            # Вычисляем новый размер батча
            new_batch_size = int(self.current_batch_size * adaptation_factor)

            # Ограничиваем пределами
            new_batch_size = max(self.min_batch_size, min(self.max_batch_size, new_batch_size))

            # Плавная адаптация - не более 20% изменения за раз
            max_change = max(1, int(self.current_batch_size * 0.2))
            if abs(new_batch_size - self.current_batch_size) > max_change:
                if new_batch_size > self.current_batch_size:
                    new_batch_size = self.current_batch_size + max_change
                else:
                    new_batch_size = self.current_batch_size - max_change

            # Финальная проверка границ
            new_batch_size = max(self.min_batch_size, min(self.max_batch_size, new_batch_size))

            if new_batch_size != self.current_batch_size:
                logger.info(f"Adapting batch size: {self.current_batch_size} -> {new_batch_size} "
                           f"(cpu_factor={cpu_factor:.2f}, memory_factor={memory_factor:.2f}, "
                           f"complexity_factor={complexity_factor:.2f}, performance_factor={performance_factor:.2f})")

                self.current_batch_size = new_batch_size
                self.last_adaptation_tick = current_tick

        except Exception as e:
            logger.error(f"Failed to adapt batch size: {e}")
            # В случае ошибки возвращаемся к размеру по умолчанию
            self.current_batch_size = self.default_batch_size

    def _calculate_performance_trend(self) -> float:
        """
        Рассчитывает тренд производительности на основе истории.

        Returns:
            float: Коэффициент тренда (1.0 = стабильная производительность)
        """
        if len(self.batch_performance_history) < 5:
            return 1.0

        try:
            # Берем последние записи
            recent_records = list(self.batch_performance_history)[-10:]

            # Вычисляем среднее время на событие
            times_per_event = [r['time_per_event'] for r in recent_records]
            avg_time_per_event = statistics.mean(times_per_event)

            # Сравниваем с целевым временем (10ms per event = 0.01s)
            target_time_per_event = 0.01

            if avg_time_per_event > target_time_per_event:
                # Производительность низкая - уменьшаем батч
                return 0.8
            elif avg_time_per_event < target_time_per_event * 0.5:
                # Производительность высокая - можно увеличить батч
                return 1.2
            else:
                # Производительность приемлемая
                return 1.0

        except Exception as e:
            logger.warning(f"Failed to calculate performance trend: {e}")
            return 1.0

    def _calculate_cpu_factor(self, cpu_percent: float) -> float:
        """
        Рассчитывает фактор влияния CPU.

        Args:
            cpu_percent: Процент использования CPU

        Returns:
            float: Фактор (0.5-1.5)
        """
        if cpu_percent > self.high_cpu_threshold:
            # Высокая нагрузка CPU - уменьшаем батч
            return 0.7
        elif cpu_percent < 30.0:
            # Низкая нагрузка CPU - можно увеличить батч
            return 1.3
        else:
            return 1.0

    def _calculate_memory_factor(self, memory_percent: float) -> float:
        """
        Рассчитывает фактор влияния памяти.

        Args:
            memory_percent: Процент использования памяти

        Returns:
            float: Фактор (0.5-1.5)
        """
        if memory_percent > self.high_memory_threshold:
            # Высокая нагрузка памяти - уменьшаем батч
            return 0.6
        elif memory_percent < 40.0:
            # Низкая нагрузка памяти - можно увеличить батч
            return 1.4
        else:
            return 1.0

    def _calculate_complexity_factor(self, complexity: float) -> float:
        """
        Рассчитывает фактор влияния сложности событий.

        Args:
            complexity: Коэффициент сложности

        Returns:
            float: Фактор (0.5-1.5)
        """
        if complexity > 2.0:
            # Высокая сложность - уменьшаем батч
            return 0.8
        elif complexity < 0.5:
            # Низкая сложность - можно увеличить батч
            return 1.2
        else:
            return 1.0

    def _calculate_performance_factor(self, performance_trend: float) -> float:
        """
        Рассчитывает фактор на основе тренда производительности.

        Args:
            performance_trend: Коэффициент тренда производительности

        Returns:
            float: Фактор (0.5-1.5)
        """
        # Тренд уже содержит нужный коэффициент
        return max(0.5, min(1.5, performance_trend))

    def get_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы адаптивного сайзера.

        Returns:
            Dict со статистикой
        """
        return {
            'current_batch_size': self.current_batch_size,
            'adaptation_interval': self.adaptation_interval,
            'ticks_since_adaptation': self.ticks_since_adaptation,
            'performance_history_size': len(self.batch_performance_history),
            'system_load_history_size': len(self.system_load_history),
            'min_batch_size': self.min_batch_size,
            'max_batch_size': self.max_batch_size
        }
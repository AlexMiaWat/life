"""
Контракты для конкретных компонентов системы Life.

Каждый контракт определяет интерфейс, гарантии и правила взаимодействия
для соответствующего компонента.
"""

from typing import Dict, Any, Optional, List
from .base_contracts import BaseContract


class EventGeneratorContract(BaseContract):
    """Контракт для EventGenerator компонента."""

    def _get_description(self) -> str:
        return "Контракт генератора событий: определяет интерфейс генерации событий с гарантиями качества и производительности"

    def get_input_ranges(self) -> Dict[str, tuple]:
        return {
            'context_state': (None, None),  # Optional[SelfState]
            'event_types_count': (20, 50),  # Количество поддерживаемых типов событий
        }

    def get_output_guarantees(self) -> Dict[str, Any]:
        return {
            'event_intensity': (0.0, 3.0),      # Диапазон интенсивности событий
            'event_types': list,                # Всегда возвращает Event объект
            'generation_time': (0.0, 0.1),      # Максимум 100ms на генерацию
            'deterministic': True,              # Детерминированная генерация при одинаковых входах
        }

    def get_error_handling(self) -> Dict[str, str]:
        return {
            'invalid_context': 'use_default_state',
            'config_error': 'fallback_to_defaults',
            'generation_failure': 'return_safe_event'
        }


class IntensityCalculatorContract(BaseContract):
    """Контракт для IntensityCalculator компонента."""

    def _get_description(self) -> str:
        return "Контракт калькулятора интенсивностей: гарантирует точный расчет модификаторов интенсивности"

    def get_input_ranges(self) -> Dict[str, tuple]:
        return {
            'event_type': (str, str),           # Не пустая строка
            'base_intensity': (0.0, 1.0),       # Нормализованная интенсивность
            'energy': (0.0, 100.0),             # Процент энергии
            'stability': (0.0, 2.0),            # Коэффициент стабильности
            'integrity': (0.0, 1.0),            # Коэффициент целостности
        }

    def get_output_guarantees(self) -> Dict[str, Any]:
        return {
            'intensity': (0.1, 3.0),            # Гарантированный диапазон
            'precision': 0.001,                 # Точность расчетов
            'deterministic': True,              # Повторяемые результаты
            'thread_safe': True,                # Безопасность в многопоточной среде
        }

    def get_error_handling(self) -> Dict[str, str]:
        return {
            'invalid_input': 'clamp_to_range',
            'calculation_error': 'fallback_to_base_intensity',
            'context_missing': 'use_default_modifiers'
        }


class PatternAnalyzerContract(BaseContract):
    """Контракт для PatternAnalyzer компонента."""

    def _get_description(self) -> str:
        return "Контракт анализатора паттернов: обеспечивает надежный анализ последовательностей событий"

    def get_input_ranges(self) -> Dict[str, tuple]:
        return {
            'event_type': (str, str),           # Не пустая строка
            'recent_events': (0, 100),          # Максимум 100 последних событий
            'analysis_window': (3, 50),         # Окно анализа паттернов
        }

    def get_output_guarantees(self) -> Dict[str, Any]:
        return {
            'pattern_modifier': (0.5, 2.0),     # Диапазон модификатора
            'confidence': (0.0, 1.0),           # Уровень уверенности
            'deterministic': True,              # Повторяемые результаты
            'computation_time': (0.0, 0.01),    # Максимум 10ms
        }

    def get_error_handling(self) -> Dict[str, str]:
        return {
            'empty_events': 'return_default_modifier',
            'invalid_event_type': 'log_warning_continue',
            'analysis_failure': 'return_safe_modifier'
        }


class SmoothingEngineContract(BaseContract):
    """Контракт для SmoothingEngine компонента."""

    def _get_description(self) -> str:
        return "Контракт движка сглаживания: гарантирует стабильность и плавность изменения значений"

    def get_input_ranges(self) -> Dict[str, tuple]:
        return {
            'modifier': (0.0, 10.0),            # Диапазон модификаторов
            'intensity': (0.0, 5.0),            # Диапазон интенсивностей
            'history_size': (10, 200),          # Размер истории
        }

    def get_output_guarantees(self) -> Dict[str, Any]:
        return {
            'smoothed_value': 'input_range',    # В пределах входного диапазона
            'stability': 0.95,                  # Минимум 95% стабильности
            'memory_efficient': True,           # Ограниченное потребление памяти
            'thread_safe': True,                # Безопасность в многопоточной среде
        }

    def get_error_handling(self) -> Dict[str, str]:
        return {
            'invalid_input': 'clamp_to_range',
            'memory_limit': 'reduce_history_size',
            'calculation_error': 'return_previous_value'
        }


class SelfStateContract(BaseContract):
    """Контракт для SelfState компонента."""

    def _get_description(self) -> str:
        return "Контракт состояния системы: определяет структуру и гарантии состояния Life"

    def get_input_ranges(self) -> Dict[str, tuple]:
        return {
            'energy': (0.0, 100.0),             # Процент энергии
            'stability': (0.0, 2.0),            # Коэффициент стабильности
            'integrity': (0.0, 1.0),            # Коэффициент целостности
            'subjective_time': (0.0, float('inf')),  # Неотрицательное время
            'memory_size': (0, 10000),          # Максимум 10k записей
        }

    def get_output_guarantees(self) -> Dict[str, Any]:
        return {
            'serializable': True,               # Всегда сериализуемо
            'consistent': True,                 # Внутренняя согласованность
            'thread_safe': False,               # Не thread-safe (нуждается во внешней синхронизации)
            'delta_application': 'atomic',      # Атомарное применение изменений
        }

    def get_error_handling(self) -> Dict[str, str]:
        return {
            'invalid_delta': 'clamp_to_range',
            'serialization_error': 'log_error_continue',
            'consistency_violation': 'attempt_repair'
        }


class RuntimeLoopContract(BaseContract):
    """Контракт для RuntimeLoop компонента."""

    def _get_description(self) -> str:
        return "Контракт основного цикла: определяет гарантии работы и производительности runtime"

    def get_input_ranges(self) -> Dict[str, tuple]:
        return {
            'tick_interval': (0.1, 10.0),       # Интервал между тиками в секундах
            'snapshot_period': (1, 1000),       # Период снимков в тиках
            'max_memory_mb': (10, 1000),        # Максимум потребления памяти
            'max_cpu_percent': (1, 100),        # Максимум CPU usage
        }

    def get_output_guarantees(self) -> Dict[str, Any]:
        return {
            'tick_duration': (0.0, 1.0),        # Максимум 1 секунда на тик
            'memory_leaks': False,              # Гарантия отсутствия утечек
            'system_stability': 0.99,           # 99% времени система стабильна
            'graceful_shutdown': True,          # Корректное завершение работы
        }

    def get_error_handling(self) -> Dict[str, str]:
        return {
            'component_failure': 'isolate_and_continue',
            'memory_exceeded': 'reduce_memory_usage',
            'performance_degraded': 'adaptive_throttling',
            'external_interrupt': 'graceful_shutdown'
        }


class FeatureFlagsContract(BaseContract):
    """Контракт для FeatureFlags компонента."""

    def _get_description(self) -> str:
        return "Контракт системы флагов: гарантирует безопасное включение/отключение экспериментальных компонентов"

    def get_input_ranges(self) -> Dict[str, tuple]:
        return {
            'component_name': (str, str),       # Не пустое имя компонента
            'cache_ttl': (1, 300),              # TTL кэша в секундах
        }

    def get_output_guarantees(self) -> Dict[str, Any]:
        return {
            'deterministic': True,              # Повторяемые результаты
            'fail_safe': True,                  # Безопасное поведение при ошибках
            'performance': 'cached',           # Кэширование для производительности
            'thread_safe': True,                # Безопасность в многопоточной среде
        }

    def get_error_handling(self) -> Dict[str, str]:
        return {
            'config_unavailable': 'default_disabled',
            'cache_failure': 'direct_lookup',
            'invalid_component': 'return_false'
        }
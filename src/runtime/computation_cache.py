"""
LRU кэш для вычислений runtime loop.
Кэширует дорогостоящие вычисления для оптимизации производительности.
"""

import hashlib
import logging
from collections import OrderedDict
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from src.runtime.subjective_time import compute_subjective_dt
from src.activation.activation import activate_memory as _activate_memory

logger = logging.getLogger(__name__)


class ComputationCache:
    """
    LRU кэш для кэширования вычислений runtime loop.

    Кэширует:
    - compute_subjective_dt с одинаковыми параметрами
    - Валидацию состояний
    - Результаты поиска в памяти
    """

    def __init__(self, max_size: int = 1000):
        """
        Инициализация кэша вычислений.

        Args:
            max_size: Максимальный размер кэша
        """
        self.max_size = max_size

        # Кэш для compute_subjective_dt
        self.subjective_dt_cache: OrderedDict[str, float] = OrderedDict()
        self.subjective_dt_hits = 0
        self.subjective_dt_misses = 0

        # Кэш для валидации состояний
        self.validation_cache: OrderedDict[str, bool] = OrderedDict()
        self.validation_hits = 0
        self.validation_misses = 0

        # Кэш для поиска в памяти
        self.memory_search_cache: OrderedDict[str, Any] = OrderedDict()
        self.memory_search_hits = 0
        self.memory_search_misses = 0

        # Кэш для Meaning Engine appraisal
        self.meaning_appraisal_cache: OrderedDict[str, Any] = OrderedDict()
        self.meaning_appraisal_hits = 0
        self.meaning_appraisal_misses = 0

        # Кэш для Decision Engine
        self.decision_cache: OrderedDict[str, Any] = OrderedDict()
        self.decision_hits = 0
        self.decision_misses = 0

    def _make_cache_key(self, *args, **kwargs) -> str:
        """
        Создает ключ кэша из аргументов.

        Args:
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            str: Хэшированный ключ кэша
        """
        # Сортируем kwargs для детерминированного хэширования
        sorted_kwargs = sorted(kwargs.items())
        cache_str = str(args) + str(sorted_kwargs)
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _evict_if_needed(self, cache_dict: OrderedDict):
        """Удаляет старые записи если кэш переполнен."""
        if len(cache_dict) > self.max_size:
            # Удаляем самый старый элемент (LRU)
            cache_dict.popitem(last=False)

    def get_cached_subjective_dt(self, dt: float, base_rate: float, intensity: float,
                                stability: float, energy: float, intensity_coeff: float,
                                stability_coeff: float, energy_coeff: float, rate_min: float,
                                rate_max: float, circadian_phase: float = 0.0,
                                recovery_efficiency: float = 1.0) -> Optional[float]:
        """
        Получает кэшированное значение subjective_dt или None если нет в кэше.

        Args:
            dt: Временной интервал
            base_rate: Базовая скорость
            intensity: Интенсивность
            stability: Стабильность
            energy: Энергия
            intensity_coeff: Коэффициент интенсивности
            stability_coeff: Коэффициент стабильности
            energy_coeff: Коэффициент энергии
            rate_min: Минимальная скорость
            rate_max: Максимальная скорость
            circadian_phase: Фаза циркадного ритма
            recovery_efficiency: Эффективность восстановления

        Returns:
            Optional[float]: Кэшированное значение или None
        """
        # Округляем float значения для лучшего кэширования
        rounded_args = (
            round(dt, 6),
            round(base_rate, 6),
            round(intensity, 6),
            round(stability, 6),
            round(energy, 6),
            round(intensity_coeff, 6),
            round(stability_coeff, 6),
            round(energy_coeff, 6),
            round(rate_min, 6),
            round(rate_max, 6),
            round(circadian_phase, 6),
            round(recovery_efficiency, 6)
        )

        cache_key = self._make_cache_key(*rounded_args)
        if cache_key in self.subjective_dt_cache:
            self.subjective_dt_hits += 1
            # Перемещаем в конец (MRU)
            value = self.subjective_dt_cache.pop(cache_key)
            self.subjective_dt_cache[cache_key] = value
            return value
        else:
            self.subjective_dt_misses += 1
            return None

    def cache_subjective_dt(self, dt: float, base_rate: float, intensity: float,
                           stability: float, energy: float, intensity_coeff: float,
                           stability_coeff: float, energy_coeff: float, rate_min: float,
                           rate_max: float, circadian_phase: float = 0.0,
                           recovery_efficiency: float = 1.0, value: float = 0.0) -> None:
        """
        Кэширует значение subjective_dt.

        Args:
            dt: Временной интервал
            base_rate: Базовая скорость
            intensity: Интенсивность
            stability: Стабильность
            energy: Энергия
            intensity_coeff: Коэффициент интенсивности
            stability_coeff: Коэффициент стабильности
            energy_coeff: Коэффициент энергии
            rate_min: Минимальная скорость
            rate_max: Максимальная скорость
            circadian_phase: Фаза циркадного ритма
            recovery_efficiency: Эффективность восстановления
            value: Значение для кэширования
        """
        rounded_args = (
            round(dt, 6),
            round(base_rate, 6),
            round(intensity, 6),
            round(stability, 6),
            round(energy, 6),
            round(intensity_coeff, 6),
            round(stability_coeff, 6),
            round(energy_coeff, 6),
            round(rate_min, 6),
            round(rate_max, 6),
            round(circadian_phase, 6),
            round(recovery_efficiency, 6)
        )

        cache_key = self._make_cache_key(*rounded_args)
        self.subjective_dt_cache[cache_key] = value
        self._evict_if_needed(self.subjective_dt_cache)

    def get_cached_validation(self, validation_type: str, data: Any) -> Optional[bool]:
        """
        Получает кэшированный результат валидации.

        Args:
            validation_type: Тип валидации
            data: Данные для валидации

        Returns:
            Optional[bool]: Кэшированный результат или None
        """
        cache_key = self._make_cache_key(validation_type, data)
        if cache_key in self.validation_cache:
            self.validation_hits += 1
            # Перемещаем в конец (MRU)
            value = self.validation_cache.pop(cache_key)
            self.validation_cache[cache_key] = value
            return value
        else:
            self.validation_misses += 1
            return None

    def cache_validation(self, validation_type: str, data: Any, result: bool) -> None:
        """
        Кэширует результат валидации.

        Args:
            validation_type: Тип валидации
            data: Данные для валидации
            result: Результат валидации
        """
        cache_key = self._make_cache_key(validation_type, data)
        self.validation_cache[cache_key] = result
        self._evict_if_needed(self.validation_cache)

    def get_cached_memory_search(self, search_type: str, query_params: Dict[str, Any]) -> Optional[Any]:
        """
        Получает кэшированный результат поиска в памяти.

        Args:
            search_type: Тип поиска
            query_params: Параметры запроса

        Returns:
            Optional[Any]: Кэшированный результат или None
        """
        cache_key = self._make_cache_key(search_type, query_params)
        if cache_key in self.memory_search_cache:
            self.memory_search_hits += 1
            # Перемещаем в конец (MRU)
            value = self.memory_search_cache.pop(cache_key)
            self.memory_search_cache[cache_key] = value
            return value
        else:
            self.memory_search_misses += 1
            return None

    def cache_memory_search(self, search_type: str, query_params: Dict[str, Any], result: Any) -> None:
        """
        Кэширует результат поиска в памяти.

        Args:
            search_type: Тип поиска
            query_params: Параметры запроса
            result: Результат поиска
        """
        cache_key = self._make_cache_key(search_type, query_params)
        self.memory_search_cache[cache_key] = result
        self._evict_if_needed(self.memory_search_cache)

    def get_cached_activate_memory(self, event_type: str, memory_size: int,
                                  subjective_time: float, age: float,
                                  limit: Optional[int] = None) -> Optional[Any]:
        """
        Получает кэшированный результат activate_memory.

        Args:
            event_type: Тип события
            memory_size: Размер памяти (для инвалидации кэша при изменениях)
            subjective_time: Субъективное время
            age: Возраст
            limit: Лимит активации

        Returns:
            Optional[Any]: Кэшированный результат или None
        """
        # Округляем значения для лучшего кэширования
        rounded_args = (
            event_type,
            memory_size,
            round(subjective_time, 3),
            round(age, 3),
            limit
        )

        cache_key = self._make_cache_key("activate_memory", rounded_args)
        if cache_key in self.memory_search_cache:
            self.memory_search_hits += 1
            # Перемещаем в конец (MRU)
            value = self.memory_search_cache.pop(cache_key)
            self.memory_search_cache[cache_key] = value
            return value
        else:
            self.memory_search_misses += 1
            return None

    def cache_activate_memory(self, event_type: str, memory_size: int,
                             subjective_time: float, age: float,
                             limit: Optional[int], result: Any) -> None:
        """
        Кэширует результат activate_memory.

        Args:
            event_type: Тип события
            memory_size: Размер памяти
            subjective_time: Субъективное время
            age: Возраст
            limit: Лимит активации
            result: Результат для кэширования
        """
        rounded_args = (
            event_type,
            memory_size,
            round(subjective_time, 3),
            round(age, 3),
            limit
        )

        cache_key = self._make_cache_key("activate_memory", rounded_args)
        self.memory_search_cache[cache_key] = result
        self._evict_if_needed(self.memory_search_cache)

    def get_cached_meaning_appraisal(self, event_type: str, intensity: float,
                                    state_energy: float, state_stability: float,
                                    state_integrity: float) -> Optional[Any]:
        """
        Получает кэшированный результат appraisal из Meaning Engine.

        Args:
            event_type: Тип события
            intensity: Интенсивность события
            state_energy: Энергия состояния
            state_stability: Стабильность состояния
            state_integrity: Целостность состояния

        Returns:
            Optional[Any]: Кэшированный результат или None
        """
        # Округляем значения для лучшего кэширования
        rounded_args = (
            event_type,
            round(intensity, 3),
            round(state_energy, 3),
            round(state_stability, 3),
            round(state_integrity, 3)
        )

        cache_key = self._make_cache_key("meaning_appraisal", rounded_args)
        if cache_key in self.meaning_appraisal_cache:
            self.meaning_appraisal_hits += 1
            # Перемещаем в конец (MRU)
            value = self.meaning_appraisal_cache.pop(cache_key)
            self.meaning_appraisal_cache[cache_key] = value
            return value
        else:
            self.meaning_appraisal_misses += 1
            return None

    def cache_meaning_appraisal(self, event_type: str, intensity: float,
                               state_energy: float, state_stability: float,
                               state_integrity: float, result: Any) -> None:
        """
        Кэширует результат appraisal из Meaning Engine.

        Args:
            event_type: Тип события
            intensity: Интенсивность события
            state_energy: Энергия состояния
            state_stability: Стабильность состояния
            state_integrity: Целостность состояния
            result: Результат для кэширования
        """
        rounded_args = (
            event_type,
            round(intensity, 3),
            round(state_energy, 3),
            round(state_stability, 3),
            round(state_integrity, 3)
        )

        cache_key = self._make_cache_key("meaning_appraisal", rounded_args)
        self.meaning_appraisal_cache[cache_key] = result
        self._evict_if_needed(self.meaning_appraisal_cache)

    def get_cached_decision(self, activated_memory_count: int, top_significance: float,
                           event_type: str, current_energy: float, current_stability: float) -> Optional[Any]:
        """
        Получает кэшированное решение.

        Args:
            activated_memory_count: Количество активированной памяти
            top_significance: Максимальная значимость в активированной памяти
            event_type: Тип события
            current_energy: Текущая энергия
            current_stability: Текущая стабильность

        Returns:
            Optional[Any]: Кэшированное решение или None
        """
        rounded_args = (
            activated_memory_count,
            round(top_significance, 3),
            event_type,
            round(current_energy, 3),
            round(current_stability, 3)
        )

        cache_key = self._make_cache_key("decision", rounded_args)
        if cache_key in self.decision_cache:
            self.decision_hits += 1
            # Перемещаем в конец (MRU)
            value = self.decision_cache.pop(cache_key)
            self.decision_cache[cache_key] = value
            return value
        else:
            self.decision_misses += 1
            return None

    def cache_decision(self, activated_memory_count: int, top_significance: float,
                      event_type: str, current_energy: float, current_stability: float,
                      result: Any) -> None:
        """
        Кэширует решение.

        Args:
            activated_memory_count: Количество активированной памяти
            top_significance: Максимальная значимость
            event_type: Тип события
            current_energy: Текущая энергия
            current_stability: Текущая стабильность
            result: Результат для кэширования
        """
        rounded_args = (
            activated_memory_count,
            round(top_significance, 3),
            event_type,
            round(current_energy, 3),
            round(current_stability, 3)
        )

        cache_key = self._make_cache_key("decision", rounded_args)
        self.decision_cache[cache_key] = result
        self._evict_if_needed(self.decision_cache)

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Получает статистику использования кэша.

        Returns:
            Dict[str, Dict[str, int]]: Статистика по типам кэша
        """
        return {
            "subjective_dt": {
                "hits": self.subjective_dt_hits,
                "misses": self.subjective_dt_misses,
                "hit_rate": (self.subjective_dt_hits / max(1, self.subjective_dt_hits + self.subjective_dt_misses)) * 100,
                "size": len(self.subjective_dt_cache)
            },
            "validation": {
                "hits": self.validation_hits,
                "misses": self.validation_misses,
                "hit_rate": (self.validation_hits / max(1, self.validation_hits + self.validation_misses)) * 100,
                "size": len(self.validation_cache)
            },
            "memory_search": {
                "hits": self.memory_search_hits,
                "misses": self.memory_search_misses,
                "hit_rate": (self.memory_search_hits / max(1, self.memory_search_hits + self.memory_search_misses)) * 100,
                "size": len(self.memory_search_cache)
            },
            "meaning_appraisal": {
                "hits": self.meaning_appraisal_hits,
                "misses": self.meaning_appraisal_misses,
                "hit_rate": (self.meaning_appraisal_hits / max(1, self.meaning_appraisal_hits + self.meaning_appraisal_misses)) * 100,
                "size": len(self.meaning_appraisal_cache)
            },
            "decision": {
                "hits": self.decision_hits,
                "misses": self.decision_misses,
                "hit_rate": (self.decision_hits / max(1, self.decision_hits + self.decision_misses)) * 100,
                "size": len(self.decision_cache)
            }
        }

    def clear(self):
        """Очищает все кэши."""
        self.subjective_dt_cache.clear()
        self.validation_cache.clear()
        self.memory_search_cache.clear()
        self.subjective_dt_hits = 0
        self.subjective_dt_misses = 0
        self.validation_hits = 0
        self.validation_misses = 0
        self.memory_search_hits = 0
        self.memory_search_misses = 0
        self.meaning_appraisal_hits = 0
        self.meaning_appraisal_misses = 0
        self.decision_hits = 0
        self.decision_misses = 0


# Глобальный экземпляр кэша
_computation_cache = None


def get_computation_cache() -> ComputationCache:
    """Получает глобальный экземпляр кэша вычислений."""
    global _computation_cache
    if _computation_cache is None:
        _computation_cache = ComputationCache()
    return _computation_cache


def cached_compute_subjective_dt(*, dt: float, base_rate: float, intensity: float,
                                stability: float, energy: float, intensity_coeff: float,
                                stability_coeff: float, energy_coeff: float, rate_min: float,
                                rate_max: float, circadian_phase: float = 0.0,
                                recovery_efficiency: float = 1.0) -> float:
    """
    Кэшированная версия compute_subjective_dt.

    Returns:
        float: Вычисленное значение subjective time increment
    """
    cache = get_computation_cache()

    # Проверяем кэш
    cached_value = cache.get_cached_subjective_dt(
        dt, base_rate, intensity, stability, energy, intensity_coeff,
        stability_coeff, energy_coeff, rate_min, rate_max, circadian_phase, recovery_efficiency
    )

    if cached_value is not None:
        return cached_value

    # Вычисляем и кэшируем
    value = compute_subjective_dt(
        dt=dt, base_rate=base_rate, intensity=intensity, stability=stability, energy=energy,
        intensity_coeff=intensity_coeff, stability_coeff=stability_coeff, energy_coeff=energy_coeff,
        rate_min=rate_min, rate_max=rate_max, circadian_phase=circadian_phase,
        recovery_efficiency=recovery_efficiency
    )

    cache.cache_subjective_dt(
        dt, base_rate, intensity, stability, energy, intensity_coeff,
        stability_coeff, energy_coeff, rate_min, rate_max, circadian_phase, recovery_efficiency, value
    )

    return value


def cached_activate_memory(current_event_type: str, memory: Any, limit: Optional[int] = None,
                          self_state: Optional[Any] = None) -> Any:
    """
    Кэшированная версия activate_memory для оптимизации поиска в памяти.

    Args:
        current_event_type: Тип текущего события
        memory: Список записей памяти
        limit: Лимит активации
        self_state: Состояние SelfState

    Returns:
        List[MemoryEntry]: Активированные записи памяти
    """
    cache = get_computation_cache()

    # Подготавливаем параметры для кэширования
    memory_size = len(memory) if hasattr(memory, '__len__') else 0
    subjective_time = getattr(self_state, 'subjective_time', 0.0) if self_state else 0.0
    age = getattr(self_state, 'age', 0.0) if self_state else 0.0

    # Проверяем кэш
    cached_result = cache.get_cached_activate_memory(
        current_event_type, memory_size, subjective_time, age, limit
    )

    if cached_result is not None:
        return cached_result

    # Вычисляем и кэшируем
    result = _activate_memory(current_event_type, memory, limit, self_state)

    cache.cache_activate_memory(
        current_event_type, memory_size, subjective_time, age, limit, result
    )

    return result
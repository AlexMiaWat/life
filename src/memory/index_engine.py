#!/usr/bin/env python3
"""
Модуль индексации памяти для быстрого поиска.
Реализует multi-level индексацию MemoryEntry с LRU кэшированием.
"""

import hashlib
import logging
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union

from .types import MemoryEntry

try:
    from ..runtime.performance_metrics import measure_time
except ImportError:
    # Fallback для случаев когда модуль не доступен
    from contextlib import contextmanager
    @contextmanager
    def measure_time(operation: str):
        yield

# Настройка логирования
logger = logging.getLogger(__name__)

# Константы
DEFAULT_MAX_CACHE_SIZE = 1000
DEFAULT_INDEX_UPDATE_BATCH_SIZE = 100


@dataclass
class MemoryQuery:
    """Класс для представления поискового запроса к памяти."""
    event_type: Optional[str] = None
    min_significance: Optional[float] = None
    max_significance: Optional[float] = None
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None
    limit: int = 100
    sort_by: str = "timestamp"  # timestamp, significance, weight
    sort_order: str = "desc"  # asc, desc

    def __post_init__(self):
        """Валидация параметров после инициализации."""
        if self.min_significance is not None and not (0.0 <= self.min_significance <= 1.0):
            raise ValueError("min_significance должен быть в диапазоне [0.0, 1.0]")
        if self.max_significance is not None and not (0.0 <= self.max_significance <= 1.0):
            raise ValueError("max_significance должен быть в диапазоне [0.0, 1.0]")
        if self.min_weight is not None and not (0.0 <= self.min_weight <= 1.0):
            raise ValueError("min_weight должен быть в диапазоне [0.0, 1.0]")
        if self.max_weight is not None and not (0.0 <= self.max_weight <= 1.0):
            raise ValueError("max_weight должен быть в диапазоне [0.0, 1.0]")
        if self.sort_by not in {"timestamp", "significance", "weight"}:
            raise ValueError("sort_by должен быть одним из: timestamp, significance, weight")
        if self.sort_order not in {"asc", "desc"}:
            raise ValueError("sort_order должен быть asc или desc")

    def get_hash(self) -> str:
        """Возвращает хэш запроса для кэширования."""
        query_str = f"{self.event_type}|{self.min_significance}|{self.max_significance}|{self.start_timestamp}|{self.end_timestamp}|{self.min_weight}|{self.max_weight}|{self.limit}|{self.sort_by}|{self.sort_order}"
        return hashlib.md5(query_str.encode()).hexdigest()


class MemoryIndexEngine:
    """
    Multi-level индексный движок для быстрого поиска в памяти.

    Архитектура индексов:
    - Уровень 1: Primary indexes (прямой доступ)
    - Уровень 2: Composite indexes (составные индексы)
    - Уровень 3: Query cache (LRU кэш результатов)
    """

    def __init__(
        self,
        max_cache_size: int = DEFAULT_MAX_CACHE_SIZE,
        enable_composite_indexes: bool = True,
        enable_query_cache: bool = True
    ):
        """
        Инициализация индексного движка.

        Args:
            max_cache_size: Максимальный размер кэша результатов запросов
            enable_composite_indexes: Включить составные индексы
            enable_query_cache: Включить кэш результатов запросов
        """
        # Primary indexes (Уровень 1)
        self.event_type_index: Dict[str, Set[int]] = defaultdict(set)  # event_type -> set of entry ids
        self.entries_by_id: Dict[int, MemoryEntry] = {}  # entry_id -> entry
        self.timestamp_entries: List[Tuple[float, MemoryEntry]] = []  # sorted by timestamp
        self.significance_entries: List[Tuple[float, MemoryEntry]] = []  # sorted by significance
        self.weight_entries: List[Tuple[float, MemoryEntry]] = []  # sorted by weight

        # Composite indexes (Уровень 2) - для сложных запросов
        self.composite_indexes_enabled = enable_composite_indexes
        if enable_composite_indexes:
            # event_type + time_range: dict[event_type, sorted_timestamps]
            self.event_type_timestamp_index: Dict[str, List[Tuple[float, MemoryEntry]]] = defaultdict(list)
            # event_type + significance: dict[event_type, sorted_significance]
            self.event_type_significance_index: Dict[str, List[Tuple[float, MemoryEntry]]] = defaultdict(list)

        # Query cache (Уровень 3) - LRU кэш результатов
        self.query_cache_enabled = enable_query_cache
        self.query_cache: OrderedDict[str, List[MemoryEntry]] = OrderedDict()
        self.max_cache_size = max_cache_size

        # Статистика для мониторинга
        self.stats = {
            "total_entries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "index_updates": 0,
            "query_count": 0
        }

    def add_entry(self, entry: MemoryEntry):
        """
        Добавляет запись в индексы.

        Args:
            entry: Запись памяти для индексации
        """
        with measure_time("memory_index_add_entry"):
            entry_id = id(entry)

            # Сохраняем ссылку на запись
            self.entries_by_id[entry_id] = entry

            # Уровень 1: Primary indexes
            self.event_type_index[entry.event_type].add(entry_id)

        # Добавляем в сортированные списки (используем insertion sort для поддержания порядка)
        self._insert_sorted(self.timestamp_entries, (entry.timestamp, entry), key=lambda x: x[0])
        self._insert_sorted(self.significance_entries, (entry.meaning_significance, entry), key=lambda x: x[0])
        self._insert_sorted(self.weight_entries, (entry.weight, entry), key=lambda x: x[0])

        # Уровень 2: Composite indexes
        if self.composite_indexes_enabled:
            self._insert_sorted(
                self.event_type_timestamp_index[entry.event_type],
                (entry.timestamp, entry),
                key=lambda x: x[0]
            )
            self._insert_sorted(
                self.event_type_significance_index[entry.event_type],
                (entry.meaning_significance, entry),
                key=lambda x: x[0]
            )

        self.stats["total_entries"] += 1
        self.stats["index_updates"] += 1

        # Инвалидируем кэш запросов (слишком грубо, но безопасно)
        if self.query_cache_enabled:
            self.query_cache.clear()

    def remove_entry(self, entry: MemoryEntry):
        """
        Удаляет запись из индексов.

        Args:
            entry: Запись памяти для удаления из индексов
        """
        entry_id = id(entry)

        # Уровень 1: Primary indexes
        if entry.event_type in self.event_type_index:
            self.event_type_index[entry.event_type].discard(entry_id)
            if not self.event_type_index[entry.event_type]:
                del self.event_type_index[entry.event_type]

        # Удаляем из сортированных списков
        self.timestamp_entries = [(ts, e) for ts, e in self.timestamp_entries if e is not entry]
        self.significance_entries = [(sig, e) for sig, e in self.significance_entries if e is not entry]
        self.weight_entries = [(w, e) for w, e in self.weight_entries if e is not entry]

        # Уровень 2: Composite indexes
        if self.composite_indexes_enabled:
            if entry.event_type in self.event_type_timestamp_index:
                self.event_type_timestamp_index[entry.event_type] = [
                    (ts, e) for ts, e in self.event_type_timestamp_index[entry.event_type] if e is not entry
                ]
                if not self.event_type_timestamp_index[entry.event_type]:
                    del self.event_type_timestamp_index[entry.event_type]

            if entry.event_type in self.event_type_significance_index:
                self.event_type_significance_index[entry.event_type] = [
                    (sig, e) for sig, e in self.event_type_significance_index[entry.event_type] if e is not entry
                ]
                if not self.event_type_significance_index[entry.event_type]:
                    del self.event_type_significance_index[entry.event_type]

        # Удаляем из словаря записей
        if entry_id in self.entries_by_id:
            del self.entries_by_id[entry_id]

        self.stats["total_entries"] -= 1
        self.stats["index_updates"] += 1

        # Инвалидируем кэш запросов
        if self.query_cache_enabled:
            self.query_cache.clear()

    def search(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Выполняет поиск с использованием multi-level индексов.

        Args:
            query: Поисковый запрос

        Returns:
            Список найденных записей, отсортированный по указанному критерию
        """
        with measure_time("memory_index_search"):
            self.stats["query_count"] += 1

            # Уровень 3: Проверяем кэш запросов
            if self.query_cache_enabled:
                cache_key = query.get_hash()
                if cache_key in self.query_cache:
                    self.stats["cache_hits"] += 1
                    # Перемещаем в конец для LRU
                    result = self.query_cache.pop(cache_key)
                    self.query_cache[cache_key] = result
                    return result.copy()
                self.stats["cache_misses"] += 1

            # Уровень 1-2: Выполняем поиск через индексы
            candidates = self._find_candidates(query)

            # Применяем все фильтры (для точности)
            results = []
            for entry in candidates:
                if self._matches_query(entry, query):
                    results.append(entry)

            # Сортировка результатов
            results = self._sort_results(results, query)

            # Ограничение количества
            if len(results) > query.limit:
                results = results[:query.limit]

            # Кэшируем результат
            if self.query_cache_enabled:
                self._cache_result(query.get_hash(), results.copy())

            return results

    def _find_candidates(self, query: MemoryQuery) -> List[MemoryEntry]:
        """
        Находит кандидатов для поиска через индексы (быстрый этап).

        Returns:
            Список потенциально подходящих записей
        """
        candidates = []

        # Если указан event_type, используем индекс
        if query.event_type:
            if query.event_type in self.event_type_index:
                # Получаем записи по их id
                entry_ids = self.event_type_index[query.event_type].copy()
                candidates = [self.entries_by_id[eid] for eid in entry_ids if eid in self.entries_by_id]

                # Оптимизация: используем composite индексы для event_type + другие критерии
                if self.composite_indexes_enabled:
                    if query.start_timestamp is not None or query.end_timestamp is not None:
                        # Используем event_type_timestamp_index для быстрого фильтра по времени
                        time_candidates = self._filter_by_timestamp_range(
                            self.event_type_timestamp_index[query.event_type],
                            query.start_timestamp,
                            query.end_timestamp
                        )
                        time_entries = [entry for _, entry in time_candidates]
                        # Пересечение списков
                        candidates = [c for c in candidates if c in time_entries]

                    if query.min_significance is not None or query.max_significance is not None:
                        # Используем event_type_significance_index
                        sig_candidates = self._filter_by_significance_range(
                            self.event_type_significance_index[query.event_type],
                            query.min_significance,
                            query.max_significance
                        )
                        sig_entries = [entry for _, entry in sig_candidates]
                        # Пересечение списков
                        candidates = [c for c in candidates if c in sig_entries]
            else:
                # Нет записей с таким event_type
                return []
        else:
            # Нет фильтра по event_type - берем все записи
            candidates = list(self.entries_by_id.values())

        return candidates

    def _matches_query(self, entry: MemoryEntry, query: MemoryQuery) -> bool:
        """
        Проверяет, соответствует ли запись всем критериям запроса.

        Args:
            entry: Запись для проверки
            query: Запрос

        Returns:
            True если запись соответствует всем критериям
        """
        # Проверяем event_type
        if query.event_type and entry.event_type != query.event_type:
            return False

        # Проверяем significance
        if query.min_significance is not None and entry.meaning_significance < query.min_significance:
            return False
        if query.max_significance is not None and entry.meaning_significance > query.max_significance:
            return False

        # Проверяем timestamp
        if query.start_timestamp is not None and entry.timestamp < query.start_timestamp:
            return False
        if query.end_timestamp is not None and entry.timestamp > query.end_timestamp:
            return False

        # Проверяем weight
        if query.min_weight is not None and entry.weight < query.min_weight:
            return False
        if query.max_weight is not None and entry.weight > query.max_weight:
            return False

        return True

    def _sort_results(self, results: List[MemoryEntry], query: MemoryQuery) -> List[MemoryEntry]:
        """
        Сортирует результаты по указанному критерию.

        Args:
            results: Список записей для сортировки
            query: Запрос с параметрами сортировки

        Returns:
            Отсортированный список
        """
        if not results:
            return results

        reverse = query.sort_order == "desc"

        if query.sort_by == "timestamp":
            return sorted(results, key=lambda x: x.timestamp, reverse=reverse)
        elif query.sort_by == "significance":
            return sorted(results, key=lambda x: x.meaning_significance, reverse=reverse)
        elif query.sort_by == "weight":
            return sorted(results, key=lambda x: x.weight, reverse=reverse)

        return results

    def _filter_by_timestamp_range(
        self,
        sorted_entries: List[Tuple[float, MemoryEntry]],
        start_ts: Optional[float],
        end_ts: Optional[float]
    ) -> List[Tuple[float, MemoryEntry]]:
        """
        Фильтрует сортированный список записей по диапазону timestamp.
        Использует бинарный поиск для эффективности.

        Args:
            sorted_entries: Список (timestamp, entry), отсортированный по timestamp
            start_ts: Минимальный timestamp
            end_ts: Максимальный timestamp

        Returns:
            Отфильтрованный список
        """
        if not sorted_entries:
            return []

        # Находим границы с помощью бинарного поиска
        start_idx = 0
        end_idx = len(sorted_entries)

        if start_ts is not None:
            # Ищем первый элемент >= start_ts
            start_idx = self._binary_search_left(sorted_entries, start_ts, key=lambda x: x[0])

        if end_ts is not None:
            # Ищем первый элемент > end_ts
            end_idx = self._binary_search_right(sorted_entries, end_ts, key=lambda x: x[0])

        return sorted_entries[start_idx:end_idx]

    def _filter_by_significance_range(
        self,
        sorted_entries: List[Tuple[float, MemoryEntry]],
        min_sig: Optional[float],
        max_sig: Optional[float]
    ) -> List[Tuple[float, MemoryEntry]]:
        """
        Фильтрует сортированный список записей по диапазону significance.

        Args:
            sorted_entries: Список (significance, entry), отсортированный по significance
            min_sig: Минимальная significance
            max_sig: Максимальная significance

        Returns:
            Отфильтрованный список
        """
        if not sorted_entries:
            return []

        start_idx = 0
        end_idx = len(sorted_entries)

        if min_sig is not None:
            start_idx = self._binary_search_left(sorted_entries, min_sig, key=lambda x: x[0])

        if max_sig is not None:
            end_idx = self._binary_search_right(sorted_entries, max_sig, key=lambda x: x[0])

        return sorted_entries[start_idx:end_idx]

    def _insert_sorted(self, sorted_list: list, item, key=lambda x: x):
        """
        Вставляет элемент в сортированный список, сохраняя порядок.

        Args:
            sorted_list: Сортированный список
            item: Элемент для вставки
            key: Функция для получения ключа сортировки
        """
        # Используем бинарный поиск для нахождения позиции вставки
        left, right = 0, len(sorted_list)
        item_key = key(item)

        while left < right:
            mid = (left + right) // 2
            if key(sorted_list[mid]) < item_key:
                left = mid + 1
            else:
                right = mid

        sorted_list.insert(left, item)

    def _binary_search_left(self, sorted_list: list, target, key=lambda x: x) -> int:
        """
        Бинарный поиск левой границы (первый элемент >= target).

        Args:
            sorted_list: Отсортированный список
            target: Целевое значение
            key: Функция для получения ключа

        Returns:
            Индекс первого элемента >= target
        """
        left, right = 0, len(sorted_list)
        while left < right:
            mid = (left + right) // 2
            if key(sorted_list[mid]) < target:
                left = mid + 1
            else:
                right = mid
        return left

    def _binary_search_right(self, sorted_list: list, target, key=lambda x: x) -> int:
        """
        Бинарный поиск правой границы (первый элемент > target).

        Args:
            sorted_list: Отсортированный список
            target: Целевое значение
            key: Функция для получения ключа

        Returns:
            Индекс первого элемента > target
        """
        left, right = 0, len(sorted_list)
        while left < right:
            mid = (left + right) // 2
            if key(sorted_list[mid]) <= target:
                left = mid + 1
            else:
                right = mid
        return left

    def _cache_result(self, cache_key: str, result: List[MemoryEntry]):
        """
        Кэширует результат запроса с LRU eviction.

        Args:
            cache_key: Ключ кэша
            result: Результат для кэширования
        """
        # Проверяем лимит кэша
        if len(self.query_cache) >= self.max_cache_size:
            # Удаляем самый старый элемент (FIFO)
            self.query_cache.popitem(last=False)

        self.query_cache[cache_key] = result

    def clear_cache(self):
        """Очищает кэш запросов."""
        self.query_cache.clear()
        self.stats["cache_hits"] = 0
        self.stats["cache_misses"] = 0

    def get_stats(self) -> Dict:
        """
        Возвращает статистику использования индексного движка.

        Returns:
            Словарь со статистикой
        """
        cache_hit_rate = 0.0
        total_cache_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_cache_requests > 0:
            cache_hit_rate = self.stats["cache_hits"] / total_cache_requests

        return {
            "total_entries": self.stats["total_entries"],
            "cache_size": len(self.query_cache),
            "max_cache_size": self.max_cache_size,
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "index_updates": self.stats["index_updates"],
            "query_count": self.stats["query_count"],
            "composite_indexes_enabled": self.composite_indexes_enabled,
            "query_cache_enabled": self.query_cache_enabled,
            "event_types_count": len(self.event_type_index),
        }

    def rebuild_indexes(self, entries: List[MemoryEntry]):
        """
        Полностью перестраивает индексы из списка записей.
        Используется при загрузке данных или восстановлении.

        Args:
            entries: Список всех записей для индексации
        """
        with measure_time("memory_index_rebuild"):
            # Очищаем текущие индексы
            self.event_type_index.clear()
            self.entries_by_id.clear()
            self.timestamp_entries.clear()
            self.significance_entries.clear()
            self.weight_entries.clear()

            if self.composite_indexes_enabled:
                self.event_type_timestamp_index.clear()
                self.event_type_significance_index.clear()

            self.query_cache.clear()

            # Перестраиваем индексы
            for entry in entries:
                self.add_entry(entry)

            logger.info(f"Перестроены индексы для {len(entries)} записей")
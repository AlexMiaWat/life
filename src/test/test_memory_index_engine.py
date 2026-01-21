"""
Тесты для MemoryIndexEngine - multi-level индексации памяти
"""

import time
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.memory.index_engine import MemoryIndexEngine, MemoryQuery
from src.memory.types import MemoryEntry


@pytest.mark.unit
class TestMemoryIndexEngine:
    """Тесты для MemoryIndexEngine"""

    def test_index_engine_creation(self):
        """Тест создания индексного движка"""
        engine = MemoryIndexEngine()
        assert engine is not None
        assert len(engine.event_type_index) == 0
        assert len(engine.timestamp_entries) == 0
        assert len(engine.query_cache) == 0

    def test_add_and_remove_entry(self):
        """Тест добавления и удаления записей"""
        engine = MemoryIndexEngine()
        entry = MemoryEntry(
            event_type="test_event",
            meaning_significance=0.8,
            timestamp=time.time()
        )

        # Добавляем запись
        engine.add_entry(entry)
        assert id(entry) in engine.event_type_index["test_event"]
        assert entry in engine.entries_by_id.values()
        assert len(engine.timestamp_entries) == 1
        assert len(engine.significance_entries) == 1
        assert engine.stats["total_entries"] == 1

        # Удаляем запись
        engine.remove_entry(entry)
        assert id(entry) not in engine.event_type_index.get("test_event", set())
        assert entry not in engine.entries_by_id.values()
        assert len(engine.timestamp_entries) == 0
        assert len(engine.significance_entries) == 0
        assert engine.stats["total_entries"] == 0

    def test_search_by_event_type(self):
        """Тест поиска по типу события"""
        engine = MemoryIndexEngine()

        # Создаем тестовые записи
        entries = [
            MemoryEntry("event_a", 0.5, 1000.0),
            MemoryEntry("event_b", 0.7, 1001.0),
            MemoryEntry("event_a", 0.9, 1002.0),
        ]

        for entry in entries:
            engine.add_entry(entry)

        # Ищем по event_a
        query = MemoryQuery(event_type="event_a")
        results = engine.search(query)

        assert len(results) == 2
        assert all(e.event_type == "event_a" for e in results)

    def test_search_by_timestamp_range(self):
        """Тест поиска по диапазону timestamp"""
        engine = MemoryIndexEngine()

        entries = [
            MemoryEntry("event", 0.5, 1000.0),
            MemoryEntry("event", 0.7, 1001.0),
            MemoryEntry("event", 0.9, 1002.0),
            MemoryEntry("event", 0.6, 1003.0),
        ]

        for entry in entries:
            engine.add_entry(entry)

        # Ищем в диапазоне 1001-1002
        query = MemoryQuery(start_timestamp=1001.0, end_timestamp=1002.0)
        results = engine.search(query)

        assert len(results) == 2
        assert all(1001.0 <= e.timestamp <= 1002.0 for e in results)

    def test_search_by_significance_range(self):
        """Тест поиска по диапазону significance"""
        engine = MemoryIndexEngine()

        entries = [
            MemoryEntry("event", 0.3, 1000.0),
            MemoryEntry("event", 0.5, 1001.0),
            MemoryEntry("event", 0.7, 1002.0),
            MemoryEntry("event", 0.9, 1003.0),
        ]

        for entry in entries:
            engine.add_entry(entry)

        # Ищем с significance > 0.6
        query = MemoryQuery(min_significance=0.6)
        results = engine.search(query)

        assert len(results) == 2
        assert all(e.meaning_significance >= 0.6 for e in results)

    def test_complex_query(self):
        """Тест сложного запроса с несколькими критериями"""
        engine = MemoryIndexEngine()

        entries = [
            MemoryEntry("decay", 0.8, 1000.0),
            MemoryEntry("recovery", 0.6, 1001.0),
            MemoryEntry("decay", 0.9, 1002.0),
            MemoryEntry("decay", 0.3, 1003.0),  # низкая significance
        ]

        for entry in entries:
            engine.add_entry(entry)

        # Ищем decay события с significance > 0.5
        query = MemoryQuery(
            event_type="decay",
            min_significance=0.5
        )
        results = engine.search(query)

        assert len(results) == 2
        assert all(e.event_type == "decay" and e.meaning_significance >= 0.5 for e in results)

    def test_query_caching(self):
        """Тест кэширования запросов"""
        engine = MemoryIndexEngine(max_cache_size=10)

        entry = MemoryEntry("event", 0.8, 1000.0)
        engine.add_entry(entry)

        query = MemoryQuery(event_type="event")

        # Первый поиск - кэш miss
        results1 = engine.search(query)
        assert len(results1) == 1
        assert engine.stats["cache_misses"] == 1
        assert engine.stats["cache_hits"] == 0

        # Второй поиск - кэш hit
        results2 = engine.search(query)
        assert len(results2) == 1
        assert engine.stats["cache_misses"] == 1
        assert engine.stats["cache_hits"] == 1

        # Результаты должны быть одинаковыми
        assert results1[0] is results2[0]

    def test_sorting(self):
        """Тест сортировки результатов"""
        engine = MemoryIndexEngine()

        entries = [
            MemoryEntry("event", 0.3, 1000.0),
            MemoryEntry("event", 0.9, 1002.0),
            MemoryEntry("event", 0.6, 1001.0),
        ]

        for entry in entries:
            engine.add_entry(entry)

        # Сортировка по significance desc (по умолчанию)
        query = MemoryQuery(sort_by="significance", sort_order="desc")
        results = engine.search(query)

        assert len(results) == 3
        assert results[0].meaning_significance == 0.9
        assert results[1].meaning_significance == 0.6
        assert results[2].meaning_significance == 0.3

        # Сортировка по significance asc
        query = MemoryQuery(sort_by="significance", sort_order="asc")
        results = engine.search(query)

        assert results[0].meaning_significance == 0.3
        assert results[1].meaning_significance == 0.6
        assert results[2].meaning_significance == 0.9

    def test_limit_results(self):
        """Тест ограничения количества результатов"""
        engine = MemoryIndexEngine()

        # Создаем много записей
        entries = [
            MemoryEntry("event", 0.9 - i * 0.1, 1000.0 + i)
            for i in range(10)
        ]

        for entry in entries:
            engine.add_entry(entry)

        # Ограничиваем до 3 результатов
        query = MemoryQuery(limit=3, sort_by="significance", sort_order="desc")
        results = engine.search(query)

        assert len(results) == 3
        # Проверяем, что вернулись самые значимые
        assert results[0].meaning_significance == 0.9
        assert results[1].meaning_significance == 0.8
        assert results[2].meaning_significance == 0.7

    def test_get_stats(self):
        """Тест получения статистики"""
        engine = MemoryIndexEngine()

        entry = MemoryEntry("event", 0.8, 1000.0)
        engine.add_entry(entry)

        query = MemoryQuery(event_type="event")
        engine.search(query)

        stats = engine.get_stats()

        assert stats["total_entries"] == 1
        assert stats["event_types_count"] == 1
        assert stats["query_count"] == 1
        assert stats["cache_hits"] == 0  # Первый запрос - miss
        assert stats["cache_misses"] == 1
        assert "cache_hit_rate" in stats

    def test_rebuild_indexes(self):
        """Тест перестройки индексов"""
        engine = MemoryIndexEngine()

        entries = [
            MemoryEntry("event_a", 0.5, 1000.0),
            MemoryEntry("event_b", 0.7, 1001.0),
            MemoryEntry("event_a", 0.9, 1002.0),
        ]

        # Перестраиваем индексы
        engine.rebuild_indexes(entries)

        assert engine.stats["total_entries"] == 3
        assert len(engine.event_type_index["event_a"]) == 2
        assert len(engine.event_type_index["event_b"]) == 1
        assert len(engine.entries_by_id) == 3
        assert len(engine.timestamp_entries) == 3
        assert len(engine.significance_entries) == 3

    def test_binary_search_timestamp(self):
        """Тест бинарного поиска по timestamp"""
        engine = MemoryIndexEngine()

        # Создаем записи с разными timestamp
        timestamps = [1000.0, 1001.0, 1002.0, 1003.0, 1004.0]
        entries = [MemoryEntry("event", 0.5, ts) for ts in timestamps]

        for entry in entries:
            engine.add_entry(entry)

        # Тестируем фильтр по диапазону
        filtered = engine._filter_by_timestamp_range(
            engine.timestamp_entries, 1001.5, 1003.5
        )

        assert len(filtered) == 2  # timestamp 1002.0 и 1003.0
        assert filtered[0][0] == 1002.0
        assert filtered[1][0] == 1003.0


@pytest.mark.unit
class TestMemoryQuery:
    """Тесты для класса MemoryQuery"""

    def test_query_creation(self):
        """Тест создания запроса"""
        query = MemoryQuery(
            event_type="decay",
            min_significance=0.5,
            start_timestamp=1000.0,
            limit=10
        )

        assert query.event_type == "decay"
        assert query.min_significance == 0.5
        assert query.start_timestamp == 1000.0
        assert query.limit == 10

    def test_query_validation(self):
        """Тест валидации параметров запроса"""
        # Некорректная significance
        with pytest.raises(ValueError):
            MemoryQuery(min_significance=-0.1)

        with pytest.raises(ValueError):
            MemoryQuery(max_significance=1.1)

        # Некорректный sort_by
        with pytest.raises(ValueError):
            MemoryQuery(sort_by="invalid")

        # Некорректный sort_order
        with pytest.raises(ValueError):
            MemoryQuery(sort_order="invalid")

    def test_query_hash(self):
        """Тест генерации хэша запроса"""
        query1 = MemoryQuery(event_type="decay", min_significance=0.5)
        query2 = MemoryQuery(event_type="decay", min_significance=0.5)
        query3 = MemoryQuery(event_type="recovery", min_significance=0.5)

        # Одинаковые запросы должны иметь одинаковый хэш
        assert query1.get_hash() == query2.get_hash()

        # Разные запросы должны иметь разные хэши
        assert query1.get_hash() != query3.get_hash()
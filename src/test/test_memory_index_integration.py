"""
Интеграционные тесты для MemoryIndexEngine - работа с Memory и ArchiveMemory

Проверяем:
- Взаимодействие MemoryIndexEngine с Memory классом
- Интеграцию с ArchiveMemory
- Синхронизацию индексов при добавлении/удалении записей
- Производительность индексации
- Восстановление индексов из сохраненных данных
"""

import time
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.memory.memory import Memory, ArchiveMemory
from src.memory.index_engine import MemoryIndexEngine, MemoryQuery
from src.memory.memory_types import MemoryEntry


@pytest.mark.integration
class TestMemoryIndexIntegration:
    """Интеграционные тесты MemoryIndexEngine с Memory классами"""

    # ============================================================================
    # Memory Integration Tests
    # ============================================================================

    def test_memory_index_integration_basic(self):
        """Базовая интеграция MemoryIndexEngine с Memory"""
        memory = Memory()

        # Добавляем записи в память
        entry1 = MemoryEntry("noise", 0.3, 1000.0, 1.0, {"source": "test"})
        entry2 = MemoryEntry("shock", 0.8, 1001.0, 1.0, {"source": "test"})
        entry3 = MemoryEntry("recovery", 0.6, 1002.0, 1.0, {"source": "test"})
        memory.append(entry1)
        memory.append(entry2)
        memory.append(entry3)

        # Проверяем что индекс работает
        assert memory._index_engine is not None
        assert isinstance(memory._index_engine, MemoryIndexEngine)

        # Проверяем статистику индекса
        stats = memory._index_engine.get_stats()
        assert stats["total_entries"] == 3

        # Проверяем поиск через индекс
        query = MemoryQuery(event_type="noise")
        results = memory._index_engine.search(query)
        assert len(results) == 1
        assert results[0].event_type == "noise"

    def test_memory_index_search_integration(self):
        """Интеграция поиска через индекс в Memory"""
        memory = Memory()

        # Создаем разнообразные записи
        timestamps = [1000.0, 1001.0, 1002.0, 1003.0, 1004.0]
        significances = [0.2, 0.4, 0.6, 0.8, 0.9]

        entries = []
        for i, (ts, sig) in enumerate(zip(timestamps, significances)):
            entry = MemoryEntry("test_event", sig, ts, 1.0, {"index": i})
            memory.append(entry)
            entries.append(entry)

        # Поиск по типу события
        query = MemoryQuery(event_type="test_event")
        results = memory._index_engine.search(query)
        assert len(results) == 5

        # Поиск по диапазону significance
        query = MemoryQuery(min_significance=0.5, max_significance=0.9)
        results = memory._index_engine.search(query)
        assert len(results) == 3  # 0.6, 0.8, 0.9

        # Поиск по диапазону timestamp
        query = MemoryQuery(start_timestamp=1001.0, end_timestamp=1003.0)
        results = memory._index_engine.search(query)
        assert len(results) == 3  # 1001.0, 1002.0, 1003.0

        # Сложный запрос
        query = MemoryQuery(
            event_type="test_event",
            min_significance=0.5,
            start_timestamp=1002.0,
            end_timestamp=1004.0,
        )
        results = memory._index_engine.search(query)
        assert len(results) == 3  # 1002.0 (0.6), 1003.0 (0.8), 1004.0 (0.9)

    def test_memory_index_performance_integration(self):
        """Интеграция производительности индексации"""
        memory = Memory()

        # Создаем много записей для тестирования производительности
        num_entries = 1000
        start_time = time.time()

        entries = []
        for i in range(num_entries):
            entry = MemoryEntry(
                f"event_{i % 10}",  # 10 разных типов событий
                0.1 + (i % 90) * 0.01,  # significance от 0.1 до 1.0
                1000.0 + i,
                1.0,
                {"index": i},
            )
            memory.append(entry)
            entries.append(entry)

        index_time = time.time() - start_time

        # Проверяем что записи добавлены (memory ограничивает размер)
        stats = memory._index_engine.get_stats()
        assert stats["total_entries"] > 0  # Есть записи

        # Тестируем производительность поиска
        search_start = time.time()

        # Поиск по типу события
        query = MemoryQuery(event_type="event_5", limit=50)
        results = memory._index_engine.search(query)
        assert len(results) > 0  # Есть записи типа event_5

        # Поиск по диапазону
        query = MemoryQuery(min_significance=0.5, max_significance=0.8, limit=50)
        results = memory._index_engine.search(query)
        assert len(results) > 0  # Есть результаты поиска

        search_time = time.time() - search_start

        # Производительность должна быть хорошей (менее 1 секунды на 1000 записей)
        assert index_time < 2.0, f"Indexing too slow: {index_time:.2f}s"
        assert search_time < 0.5, f"Search too slow: {search_time:.2f}s"

    def test_memory_index_cache_integration(self):
        """Интеграция кэширования запросов"""
        memory = Memory()

        # Добавляем записи
        for i in range(100):
            entry = MemoryEntry("test_event", 0.5, 1000.0 + i, 1.0, {"index": i})
            memory.append(entry)

        # Первый запрос (cache miss)
        query = MemoryQuery(event_type="test_event", limit=10)
        results1 = memory._index_engine.search(query)

        stats_after_miss = memory._index_engine.get_stats()
        misses_after_first = stats_after_miss["cache_misses"]

        # Второй запрос (cache hit)
        results2 = memory._index_engine.search(query)

        stats_after_hit = memory._index_engine.get_stats()
        hits_after_second = stats_after_hit["cache_hits"]

        # Проверяем что результаты одинаковые
        assert len(results1) == len(results2) == 10
        assert results1[0] is results2[0]  # Тот же объект из кэша

        # Проверяем статистику кэша
        assert misses_after_first >= 1
        assert hits_after_second >= 1

    def test_memory_index_memory_cleanup_integration(self):
        """Интеграция с очисткой памяти Memory"""
        memory = Memory()

        # Добавляем записи
        entries = []
        for i in range(50):
            entry = MemoryEntry("test", 0.5, 1000.0 + i, 1.0, {"index": i})
            memory.append(entry)
            entries.append(entry)

        # Проверяем что записи в индексе
        stats = memory._index_engine.get_stats()
        assert stats["total_entries"] == 50

        # Имитируем очистку памяти (удаляем записи из памяти)
        # В реальном коде это происходит через forget_old_entries или аналогично
        for entry in entries[:25]:  # Удаляем половину
            memory._index_engine.remove_entry(entry)

        # Проверяем что индекс обновился
        stats_after = memory._index_engine.get_stats()
        assert stats_after["total_entries"] == 25

    # ============================================================================
    # ArchiveMemory Integration Tests
    # ============================================================================

    def test_archive_memory_index_integration(self):
        """Интеграция MemoryIndexEngine с ArchiveMemory"""
        archive = ArchiveMemory()

        # ArchiveMemory должен иметь индекс
        assert hasattr(archive, "_index_engine")
        assert isinstance(archive._index_engine, MemoryIndexEngine)

        # Добавляем записи в архив
        entry1 = MemoryEntry("decay", 0.7, 1000.0, 1.0, {"archived": True})
        entry2 = MemoryEntry("noise", 0.3, 1001.0, 1.0, {"archived": True})
        archive.add_entry(entry1)
        archive.add_entry(entry2)

        # Проверяем индексацию
        stats = archive._index_engine.get_stats()
        assert stats["total_entries"] == 2

        # Проверяем поиск
        query = MemoryQuery(event_type="decay")
        results = archive._index_engine.search(query)
        assert len(results) == 1
        assert results[0].event_type == "decay"

    def test_archive_memory_large_dataset_integration(self):
        """Интеграция ArchiveMemory с большим набором данных"""
        archive = ArchiveMemory()

        # Создаем большой набор данных
        num_entries = 5000
        event_types = ["decay", "noise", "recovery", "shock", "idle"]

        start_time = time.time()
        for i in range(num_entries):
            event_type = event_types[i % len(event_types)]
            significance = 0.1 + (i % 90) * 0.01  # 0.1 to 1.0
            timestamp = 1000.0 + i * 0.1

            entry = MemoryEntry(event_type, significance, timestamp, feedback_data={"batch": i // 100})
            archive.add_entry(entry)

        archive_time = time.time() - start_time

        # Проверяем что записи добавлены (memory ограничивает размер)
        stats = archive._index_engine.get_stats()
        assert stats["total_entries"] <= num_entries  # Не более чем добавлено
        assert stats["total_entries"] > 0  # Но не пустой

        # Тестируем производительность поиска
        search_start = time.time()

        # Поиск по типу события
        query = MemoryQuery(event_type="decay", limit=100)
        results = archive._index_engine.search(query)
        assert len(results) == 100  # limit=100 ограничивает до 100 записей

        # Поиск по диапазону significance
        query = MemoryQuery(min_significance=0.8, limit=100)
        results = archive._index_engine.search(query)
        assert len(results) == 100

        # Сложный поиск
        query = MemoryQuery(
            event_type="noise",
            min_significance=0.5,
            start_timestamp=1500.0,
            end_timestamp=2000.0,
            limit=50,
        )
        results = archive._index_engine.search(query)
        assert len(results) <= 50

        search_time = time.time() - search_start

        # Проверяем производительность
        assert archive_time < 5.0, f"Archive creation too slow: {archive_time:.2f}s"
        assert search_time < 1.0, f"Archive search too slow: {search_time:.2f}s"

    def test_archive_memory_index_persistence_integration(self):
        """Интеграция индексации с сохранением/загрузкой ArchiveMemory"""
        # Создаем архив с данными
        archive1 = ArchiveMemory()

        entries_data = [
            ("decay", 0.8, 1000.0, {"test": "persistence"}),
            ("noise", 0.5, 1001.0, {"test": "persistence"}),
            ("recovery", 0.7, 1002.0, {"test": "persistence"}),
        ]

        for event_type, significance, timestamp, metadata in entries_data:
            entry = MemoryEntry(event_type, significance, timestamp, 1.0, metadata)
            archive1.add_entry(entry)

        # Сохраняем архив (имитируем сохранение)
        # В реальном коде ArchiveMemory имеет методы сохранения
        saved_data = archive1._entries.copy()  # Имитируем сохраненные данные

        # Создаем новый архив и загружаем данные
        archive2 = ArchiveMemory()
        archive2._entries = saved_data

        # Перестраиваем индекс
        archive2._index_engine.rebuild_indexes(saved_data)

        # Проверяем что индекс восстановлен
        stats = archive2._index_engine.get_stats()
        assert stats["total_entries"] == 3

        # Проверяем поиск
        query = MemoryQuery(event_type="decay")
        results = archive2._index_engine.search(query)
        assert len(results) == 1
        assert results[0].event_type == "decay"
        assert results[0].meaning_significance == 0.8

    # ============================================================================
    # Memory vs ArchiveMemory Comparison Tests
    # ============================================================================

    def test_memory_archive_index_consistency(self):
        """Согласованность индексации между Memory и ArchiveMemory"""
        memory = Memory()
        archive = ArchiveMemory()

        # Создаем одинаковые записи
        test_data = [
            ("noise", 0.4, 1000.0),
            ("shock", 0.8, 1001.0),
            ("recovery", 0.6, 1002.0),
        ]

        # Добавляем в память
        memory_entries = []
        for event_type, significance, timestamp in test_data:
            entry = MemoryEntry(event_type, significance, timestamp, 1.0, {})
            memory.append(entry)
            memory_entries.append(entry)

        # Добавляем в архив
        archive_entries = []
        for event_type, significance, timestamp in test_data:
            entry = MemoryEntry(event_type, significance, timestamp, 1.0, {})
            archive.add_entry(entry)
            archive_entries.append(entry)

        # Проверяем что индексы содержат одинаковое количество записей
        memory_stats = memory._index_engine.get_stats()
        archive_stats = archive._index_engine.get_stats()

        assert memory_stats["total_entries"] == archive_stats["total_entries"] == 3

        # Проверяем одинаковые результаты поиска
        query = MemoryQuery(min_significance=0.5)
        memory_results = memory._index_engine.search(query)
        archive_results = archive._index_engine.search(query)

        assert len(memory_results) == len(archive_results) == 2  # shock и recovery

        # Сортируем результаты для сравнения
        memory_sorted = sorted(memory_results, key=lambda x: x.timestamp)
        archive_sorted = sorted(archive_results, key=lambda x: x.timestamp)

        for mem_entry, arch_entry in zip(memory_sorted, archive_sorted):
            assert mem_entry.event_type == arch_entry.event_type
            assert mem_entry.meaning_significance == arch_entry.meaning_significance
            assert abs(mem_entry.timestamp - arch_entry.timestamp) < 0.001

    # ============================================================================
    # Index Synchronization Tests
    # ============================================================================

    def test_index_synchronization_on_memory_operations(self):
        """Синхронизация индекса при операциях с памятью"""
        memory = Memory()

        # Добавляем записи и проверяем синхронизацию
        entry1 = MemoryEntry("test", 0.5, 1000.0, 1.0, {"sync": "test"})
        memory.append(entry1)
        stats1 = memory._index_engine.get_stats()
        assert stats1["total_entries"] == 1

        entry2 = MemoryEntry("test", 0.7, 1001.0, 1.0, {"sync": "test"})
        memory.append(entry2)
        stats2 = memory._index_engine.get_stats()
        assert stats2["total_entries"] == 2

        # Имитируем удаление записи из памяти
        memory._index_engine.remove_entry(entry1)
        stats3 = memory._index_engine.get_stats()
        assert stats3["total_entries"] == 1

        # Проверяем что оставшаяся запись находится
        query = MemoryQuery(event_type="test")
        results = memory._index_engine.search(query)
        assert len(results) == 1
        assert results[0].meaning_significance == 0.7

    def test_index_rebuild_after_corruption(self):
        """Перестройка индекса после повреждения"""
        memory = Memory()

        # Создаем записи
        entries = []
        for i in range(10):
            entry = MemoryEntry("rebuild_test", 0.5, 1000.0 + i, 1.0, {"index": i})
            memory.append(entry)
            entries.append(entry)

        # Проверяем начальное состояние
        stats = memory._index_engine.get_stats()
        assert stats["total_entries"] == 10

        # Имитируем повреждение индекса (очищаем индексы)
        memory._index_engine.event_type_index.clear()
        memory._index_engine.entries_by_id.clear()
        memory._index_engine.timestamp_entries.clear()
        memory._index_engine.significance_entries.clear()
        memory._index_engine.query_cache.clear()

        # Проверяем что индекс "поврежден" - поиск не работает
        corrupted_query = MemoryQuery(event_type="rebuild_test")
        corrupted_results = memory._index_engine.search(corrupted_query)
        assert len(corrupted_results) == 0

        # Перестраиваем индекс
        memory._index_engine.rebuild_indexes(entries)

        # Проверяем что индекс восстановлен
        rebuilt_stats = memory._index_engine.get_stats()
        assert rebuilt_stats["total_entries"] >= 10  # Минимум 10 записей восстановлено

        # Проверяем что поиск работает
        query = MemoryQuery(event_type="rebuild_test")
        results = memory._index_engine.search(query)
        assert len(results) == 10

    # ============================================================================
    # Performance Benchmark Integration Tests
    # ============================================================================

    def test_memory_index_performance_scalability(self):
        """Тестирование масштабируемости производительности индекса"""
        memory = Memory()

        # Тестируем с разными размерами данных
        sizes = [100, 500, 1000]

        for size in sizes:
            # Очищаем предыдущие данные
            memory._index_engine.clear_cache()
            memory.clear()  # Очищаем список
            memory._index_engine.rebuild_indexes([])

            # Создаем данные
            start_time = time.time()
            entries = []
            for i in range(size):
                entry = MemoryEntry(
                    f"perf_event_{i % 20}",  # 20 разных типов
                    0.1 + (i % 90) * 0.01,
                    1000.0 + i,
                    1.0,
                    {"perf_test": True}
                )
                memory.append(entry)
                entries.append(entry)

            creation_time = time.time() - start_time

            # Тестируем поиск
            search_start = time.time()
            query = MemoryQuery(limit=min(100, size))
            results = memory._index_engine.search(query)
            search_time = time.time() - search_start

            # Проверяем результаты (может вернуть меньше из-за фильтрации)
            assert len(results) <= min(100, size)
            assert len(results) > 0

            # Производительность должна масштабироваться линейно
            # Для size=100: creation < 0.1s, search < 0.01s
            # Для size=1000: creation < 1.0s, search < 0.1s
            expected_creation = size * 0.001  # ~1ms per entry
            expected_search = size * 0.0001  # ~0.1ms per entry for search

            assert (
                creation_time < expected_creation * 5
            ), f"Creation too slow for size {size}: {creation_time:.3f}s"
            assert (
                search_time < expected_search * 5
            ), f"Search too slow for size {size}: {search_time:.3f}s"

    def test_memory_index_cache_effectiveness(self):
        """Тестирование эффективности кэширования"""
        memory = Memory()
        # Устанавливаем размер кэша индексного движка
        memory._index_engine.max_cache_size = 50

        # Создаем тестовые данные
        for i in range(200):
            entry = MemoryEntry("cache_test", 0.5, 1000.0 + i, 1.0, {"cache": i})
            memory.append(entry)

        # Выполняем серию запросов
        queries = [
            MemoryQuery(event_type="cache_test", limit=10),
            MemoryQuery(min_significance=0.4, limit=10),
            MemoryQuery(start_timestamp=1100.0, end_timestamp=1200.0, limit=10),
        ]

        total_hits = 0
        total_misses = 0

        for query in queries:
            # Первый запрос (miss)
            memory._index_engine.search(query)
            stats_after_miss = memory._index_engine.get_stats()
            total_misses += stats_after_miss["cache_misses"]

            # Повторные запросы (hits)
            for _ in range(5):
                memory._index_engine.search(query)

            stats_after_hits = memory._index_engine.get_stats()
            total_hits += stats_after_hits["cache_hits"]

        # Проверяем что кэш работает
        assert total_misses >= len(queries)  # Минимум по одному miss на запрос
        assert total_hits >= len(queries) * 2  # Несколько hits на запрос

        # Эффективность кэша должна быть > 50%
        total_requests = total_hits + total_misses
        if total_requests > 0:
            cache_hit_rate = total_hits / total_requests
            assert cache_hit_rate > 0.5, f"Cache hit rate too low: {cache_hit_rate:.2f}"

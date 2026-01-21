"""
Тесты для MemoryIndexEngine - multi-level индексации памяти
"""

import inspect
import time
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.memory.index_engine import MemoryIndexEngine, MemoryQuery
from src.memory.memory_types import MemoryEntry


@pytest.mark.static
class TestMemoryIndexEngineStatic:
    """Статические тесты для MemoryIndexEngine"""

    # ============================================================================
    # MemoryIndexEngine Static Tests
    # ============================================================================

    def test_memory_index_engine_structure(self):
        """Проверка структуры MemoryIndexEngine"""
        assert hasattr(MemoryIndexEngine, "__init__")
        assert hasattr(MemoryIndexEngine, "add_entry")
        assert hasattr(MemoryIndexEngine, "remove_entry")
        assert hasattr(MemoryIndexEngine, "search")
        assert hasattr(MemoryIndexEngine, "rebuild_indexes")
        assert hasattr(MemoryIndexEngine, "get_stats")
        assert hasattr(MemoryIndexEngine, "clear_cache")

        # Проверяем константы модуля
        import src.memory.index_engine as index_module

        assert hasattr(index_module, "DEFAULT_MAX_CACHE_SIZE")
        assert hasattr(index_module, "DEFAULT_INDEX_UPDATE_BATCH_SIZE")

    def test_memory_index_engine_constants(self):
        """Проверка констант MemoryIndexEngine"""
        # Импортируем константы
        from src.memory.index_engine import DEFAULT_MAX_CACHE_SIZE, DEFAULT_INDEX_UPDATE_BATCH_SIZE

        assert DEFAULT_MAX_CACHE_SIZE == 1000
        assert DEFAULT_INDEX_UPDATE_BATCH_SIZE == 100

        # Проверяем что константы положительные
        assert DEFAULT_MAX_CACHE_SIZE > 0
        assert DEFAULT_INDEX_UPDATE_BATCH_SIZE > 0

    def test_memory_index_engine_method_signatures(self):
        """Проверка сигнатур методов MemoryIndexEngine"""
        engine = MemoryIndexEngine()

        # __init__
        sig = inspect.signature(MemoryIndexEngine.__init__)
        assert len(sig.parameters) == 4  # self + 3 параметра
        assert "max_cache_size" in sig.parameters
        assert "enable_composite_indexes" in sig.parameters
        assert "enable_query_cache" in sig.parameters

        # add_entry
        sig = inspect.signature(engine.add_entry)
        assert "entry" in sig.parameters

        # remove_entry
        sig = inspect.signature(engine.remove_entry)
        assert "entry" in sig.parameters

        # search
        sig = inspect.signature(engine.search)
        assert "query" in sig.parameters

        # rebuild_indexes
        sig = inspect.signature(engine.rebuild_indexes)
        assert "entries" in sig.parameters

        # get_stats
        sig = inspect.signature(engine.get_stats)
        # только self, но len(sig.parameters) не включает self

        # clear_cache
        sig = inspect.signature(engine.clear_cache)
        # clear_cache не имеет параметров кроме self

    def test_memory_index_engine_return_types(self):
        """Проверка типов возвращаемых значений MemoryIndexEngine"""
        engine = MemoryIndexEngine()
        entry = MemoryEntry("test", 0.5, 1000.0)
        query = MemoryQuery(event_type="test")

        # add_entry возвращает None
        result = engine.add_entry(entry)
        assert result is None

        # remove_entry возвращает None
        result = engine.remove_entry(entry)
        assert result is None

        # search возвращает list
        result = engine.search(query)
        assert isinstance(result, list)

        # rebuild_indexes возвращает None
        result = engine.rebuild_indexes([])
        assert result is None

        # get_stats возвращает dict
        result = engine.get_stats()
        assert isinstance(result, dict)

        # clear_cache возвращает None
        result = engine.clear_cache()
        assert result is None

    def test_memory_index_engine_private_methods(self):
        """Проверка приватных методов MemoryIndexEngine"""
        engine = MemoryIndexEngine()

        # Проверяем наличие приватных методов
        assert hasattr(engine, "_filter_by_timestamp_range")
        assert hasattr(engine, "_filter_by_significance_range")
        assert hasattr(engine, "_sort_results")
        assert hasattr(engine, "_insert_sorted")
        assert hasattr(engine, "_binary_search_left")

        # Проверяем что они приватные (начинаются с _)
        assert "_filter_by_timestamp_range" in dir(engine)
        assert "_filter_by_significance_range" in dir(engine)
        assert "_sort_results" in dir(engine)
        assert "_insert_sorted" in dir(engine)
        assert "_binary_search_left" in dir(engine)

    def test_memory_index_engine_attributes_initialization(self):
        """Проверка инициализации атрибутов MemoryIndexEngine"""
        engine = MemoryIndexEngine()

        # Primary indexes
        assert hasattr(engine, "event_type_index")
        assert hasattr(engine, "entries_by_id")
        assert hasattr(engine, "timestamp_entries")
        assert hasattr(engine, "significance_entries")
        assert hasattr(engine, "weight_entries")

        # Composite indexes (если включены)
        assert hasattr(engine, "composite_indexes_enabled")
        if engine.composite_indexes_enabled:
            assert hasattr(engine, "event_type_timestamp_index")
            assert hasattr(engine, "event_type_significance_index")

        # Query cache
        assert hasattr(engine, "query_cache")
        assert hasattr(engine, "query_cache_enabled")
        assert hasattr(engine, "max_cache_size")

        # Statistics
        assert hasattr(engine, "stats")

        # Проверяем типы
        assert isinstance(engine.event_type_index, dict)
        assert isinstance(engine.entries_by_id, dict)
        assert isinstance(engine.timestamp_entries, list)
        assert isinstance(engine.significance_entries, list)
        assert isinstance(engine.weight_entries, list)
        assert isinstance(engine.query_cache, dict)
        assert isinstance(engine.stats, dict)

    def test_memory_index_engine_no_forbidden_patterns(self):
        """Проверка отсутствия запрещенных паттернов в MemoryIndexEngine"""
        source_code = inspect.getsource(MemoryIndexEngine)

        forbidden_patterns = [
            "print(",  # Не используем print
            "import os",  # Не используем os напрямую
            "import sys",  # Не используем sys напрямую
            "eval(",  # Не используем eval
            "exec(",  # Не используем exec
        ]

        for pattern in forbidden_patterns:
            assert (
                pattern not in source_code
            ), f"Forbidden pattern '{pattern}' found in MemoryIndexEngine"

    def test_memory_index_engine_docstrings(self):
        """Проверка наличия docstrings в MemoryIndexEngine"""
        assert MemoryIndexEngine.__doc__ is not None
        assert len(MemoryIndexEngine.__doc__.strip()) > 50  # Достаточно подробный

        engine = MemoryIndexEngine()
        assert engine.add_entry.__doc__ is not None
        assert engine.remove_entry.__doc__ is not None
        assert engine.search.__doc__ is not None
        assert engine.rebuild_indexes.__doc__ is not None
        assert engine.get_stats.__doc__ is not None

    # ============================================================================
    # MemoryQuery Static Tests
    # ============================================================================

    def test_memory_query_structure(self):
        """Проверка структуры MemoryQuery"""
        assert hasattr(MemoryQuery, "__init__")
        assert hasattr(MemoryQuery, "__post_init__")
        assert hasattr(MemoryQuery, "get_hash")

        # Проверяем поля dataclass
        query = MemoryQuery()
        assert hasattr(query, "event_type")
        assert hasattr(query, "min_significance")
        assert hasattr(query, "max_significance")
        assert hasattr(query, "start_timestamp")
        assert hasattr(query, "end_timestamp")
        assert hasattr(query, "min_weight")
        assert hasattr(query, "max_weight")
        assert hasattr(query, "limit")
        assert hasattr(query, "sort_by")
        assert hasattr(query, "sort_order")

    def test_memory_query_constants_and_defaults(self):
        """Проверка констант и значений по умолчанию MemoryQuery"""
        query = MemoryQuery()

        # Проверяем значения по умолчанию
        assert query.event_type is None
        assert query.min_significance is None
        assert query.max_significance is None
        assert query.start_timestamp is None
        assert query.end_timestamp is None
        assert query.min_weight is None
        assert query.max_weight is None
        assert query.limit == 100
        assert query.sort_by == "timestamp"
        assert query.sort_order == "desc"

    def test_memory_query_method_signatures(self):
        """Проверка сигнатур методов MemoryQuery"""
        # __init__ - проверяем через создание экземпляра
        query = MemoryQuery()

        # get_hash
        sig = inspect.signature(query.get_hash)
        # self не учитывается в len(sig.parameters)

        # __post_init__ - проверяем через inspect
        sig = inspect.signature(MemoryQuery.__post_init__)
        assert len(sig.parameters) == 1  # только self

    def test_memory_query_return_types(self):
        """Проверка типов возвращаемых значений MemoryQuery"""
        query = MemoryQuery()

        # get_hash возвращает str
        result = query.get_hash()
        assert isinstance(result, str)
        assert len(result) == 32  # MD5 хэш

    def test_memory_query_validation_rules(self):
        """Проверка правил валидации MemoryQuery"""
        # Проверяем допустимые значения
        valid_query = MemoryQuery(
            min_significance=0.0,
            max_significance=1.0,
            min_weight=0.0,
            max_weight=1.0,
            sort_by="timestamp",
            sort_order="desc",
        )
        assert valid_query is not None

    def test_memory_query_hash_consistency(self):
        """Проверка консистентности хэширования MemoryQuery"""
        query1 = MemoryQuery(event_type="test", min_significance=0.5)
        query2 = MemoryQuery(event_type="test", min_significance=0.5)
        query3 = MemoryQuery(event_type="different", min_significance=0.5)

        # Одинаковые запросы дают одинаковый хэш
        assert query1.get_hash() == query2.get_hash()

        # Разные запросы дают разные хэши
        assert query1.get_hash() != query3.get_hash()

    def test_memory_query_docstrings(self):
        """Проверка наличия docstrings в MemoryQuery"""
        assert MemoryQuery.__doc__ is not None
        assert len(MemoryQuery.__doc__.strip()) > 20

        query = MemoryQuery()
        assert query.get_hash.__doc__ is not None

    def test_memory_query_inheritance(self):
        """Проверка наследования MemoryQuery"""
        # MemoryQuery должен наследоваться только от object (через dataclass)
        assert MemoryQuery.__bases__ == (object,)

    # ============================================================================
    # Cross-Module Integration Static Tests
    # ============================================================================

    def test_memory_index_engine_imports_structure(self):
        """Проверка структуры импортов модуля index_engine"""
        import src.memory.index_engine as index_module

        # Проверяем что модуль экспортирует основные классы
        assert hasattr(index_module, "MemoryIndexEngine")
        assert hasattr(index_module, "MemoryQuery")

        # Проверяем соответствие
        assert index_module.MemoryIndexEngine == MemoryIndexEngine
        assert index_module.MemoryQuery == MemoryQuery

    def test_memory_index_engine_module_constants(self):
        """Проверка констант модуля index_engine"""
        import src.memory.index_engine as index_module

        assert hasattr(index_module, "DEFAULT_MAX_CACHE_SIZE")
        assert hasattr(index_module, "DEFAULT_INDEX_UPDATE_BATCH_SIZE")

        assert index_module.DEFAULT_MAX_CACHE_SIZE == 1000
        assert index_module.DEFAULT_INDEX_UPDATE_BATCH_SIZE == 100

    def test_memory_index_engine_no_optimization_methods(self):
        """Проверка отсутствия методов оптимизации в MemoryIndexEngine"""
        source_code = inspect.getsource(MemoryIndexEngine)

        forbidden_methods = [
            "optimize",
            "optimization",
            "optimizer",
            "improve",
            "improvement",
            "maximize",
            "minimize",
            "evaluate",
            "evaluation",
            "score",
            "scoring",
            "scorer",
            "judge",
            "judgment",
            "train",
            "training",
            "trainer",
            "fit",
            "fitting",
            "gradient",
            "backprop",
            "loss",
            "cost",
            "error",
        ]

        for method in forbidden_methods:
            assert (
                method.lower() not in source_code.lower()
            ), f"MemoryIndexEngine не должен иметь метод {method}"

    def test_memory_index_engine_no_goals_or_rewards(self):
        """Проверка отсутствия целей и reward в MemoryIndexEngine"""
        source_code = inspect.getsource(MemoryIndexEngine)

        forbidden_terms = [
            "goal",
            "objective",
            "reward",
            "punishment",
            "utility",
            "scoring",
            "rate",  # кроме случаев в названиях переменных
        ]

        lines = [
            line
            for line in source_code.split("\n")
            if not line.strip().startswith("#")
            and not line.strip().startswith('"""')
            and not line.strip().startswith("'''")
        ]
        source_clean = "\n".join(lines)

        for term in forbidden_terms:
            # Разрешаем некоторые термины в допустимых контекстах
            if term == "rate":
                # Проверяем что "rate" не используется как отдельный термин в коде
                # (разрешаем только в названиях переменных)
                lines_with_term = [
                    line for line in source_clean.split("\n") if "rate" in line.lower()
                ]
                for line in lines_with_term:
                    # Разрешаем в контексте названий переменных
                    if any(var_name in line.lower() for var_name in ["cache_hit_rate", "rate ="]):
                        continue
                    # Проверяем что это не запрещенное использование
                    if not any(
                        allowed in line.lower()
                        for allowed in ["cache_hit_rate", "hit_rate", "rate_min", "rate_max"]
                    ):
                        # Это может быть в комментариях или документации - проверяем контекст
                        if not any(comment in line.lower() for comment in ["#", '"""', "'''"]):
                            assert False, f"Термин 'rate' найден в недопустимом контексте: {line}"
            else:
                assert (
                    term.lower() not in source_clean.lower()
                ), f"Термин {term} не должен использоваться в коде MemoryIndexEngine"


@pytest.mark.smoke
class TestMemoryIndexEngineSmoke:
    """Дымовые тесты для MemoryIndexEngine"""

    # ============================================================================
    # MemoryIndexEngine Smoke Tests
    # ============================================================================

    def test_memory_index_engine_instantiation(self):
        """Тест создания экземпляра MemoryIndexEngine"""
        # Без параметров
        engine = MemoryIndexEngine()
        assert engine is not None
        assert isinstance(engine, MemoryIndexEngine)

        # С параметрами
        engine_custom = MemoryIndexEngine(
            max_cache_size=500, enable_composite_indexes=False, enable_query_cache=False
        )
        assert engine_custom is not None
        assert isinstance(engine_custom, MemoryIndexEngine)

    def test_memory_index_engine_empty_operations(self):
        """Дымовой тест операций с пустым индексом"""
        engine = MemoryIndexEngine()

        # Поиск в пустом индексе
        query = MemoryQuery()
        results = engine.search(query)
        assert isinstance(results, list)
        assert len(results) == 0

        # Получение статистики пустого индекса
        stats = engine.get_stats()
        assert isinstance(stats, dict)
        assert stats["total_entries"] == 0

        # Очистка пустого кэша
        engine.clear_cache()  # Не должно вызывать исключений

        # Перестройка индексов с пустым списком
        engine.rebuild_indexes([])  # Не должно вызывать исключений

    def test_memory_index_engine_single_entry_operations(self):
        """Дымовой тест операций с одной записью"""
        engine = MemoryIndexEngine()
        entry = MemoryEntry("test_event", 0.5, 1000.0)

        # Добавление записи
        engine.add_entry(entry)  # Не должно вызывать исключений

        # Поиск добавленной записи
        query = MemoryQuery(event_type="test_event")
        results = engine.search(query)
        assert isinstance(results, list)
        assert len(results) == 1

        # Удаление записи
        engine.remove_entry(entry)  # Не должно вызывать исключений

        # Проверка что запись удалена
        results_after = engine.search(query)
        assert len(results_after) == 0

    def test_memory_index_engine_minimal_data_operations(self):
        """Дымовой тест с минимальными данными"""
        engine = MemoryIndexEngine()

        # Минимальная запись
        entry = MemoryEntry("", 0.0, 0.0)  # Минимально допустимые значения
        engine.add_entry(entry)

        # Поиск с минимальными критериями
        query = MemoryQuery(limit=1)
        results = engine.search(query)
        assert isinstance(results, list)

        # Очистка
        engine.remove_entry(entry)

    def test_memory_index_engine_boundary_values(self):
        """Дымовой тест с граничными значениями"""
        engine = MemoryIndexEngine()

        # Граничные значения significance
        entry_min = MemoryEntry("event", 0.0, 1000.0)
        entry_max = MemoryEntry("event", 1.0, 1000.0)

        engine.add_entry(entry_min)
        engine.add_entry(entry_max)

        # Поиск с граничными значениями
        query_min = MemoryQuery(min_significance=0.0)
        query_max = MemoryQuery(max_significance=1.0)

        results_min = engine.search(query_min)
        results_max = engine.search(query_max)

        assert isinstance(results_min, list)
        assert isinstance(results_max, list)

        # Очистка
        engine.remove_entry(entry_min)
        engine.remove_entry(entry_max)

    def test_memory_index_engine_large_limit(self):
        """Дымовой тест с большим значением limit"""
        engine = MemoryIndexEngine()
        entry = MemoryEntry("event", 0.5, 1000.0)
        engine.add_entry(entry)

        # Большой limit
        query = MemoryQuery(limit=10000)
        results = engine.search(query)
        assert isinstance(results, list)
        assert len(results) == 1  # Должна вернуться одна запись

        engine.remove_entry(entry)

    def test_memory_index_engine_zero_limit(self):
        """Дымовой тест с нулевым limit"""
        engine = MemoryIndexEngine()
        entry = MemoryEntry("event", 0.5, 1000.0)
        engine.add_entry(entry)

        # Нулевой limit
        query = MemoryQuery(limit=0)
        results = engine.search(query)
        assert isinstance(results, list)
        assert len(results) == 0  # Ничего не возвращается

        engine.remove_entry(entry)

    def test_memory_index_engine_timestamp_boundaries(self):
        """Дымовой тест с граничными timestamp"""
        engine = MemoryIndexEngine()

        # Разные timestamp
        entries = [
            MemoryEntry("event", 0.5, 0.0),  # Минимальный timestamp
            MemoryEntry("event", 0.5, 1000.0),  # Обычный timestamp
            MemoryEntry("event", 0.5, 999999.0),  # Большой timestamp
        ]

        for entry in entries:
            engine.add_entry(entry)

        # Поиск по диапазонам
        query_full = MemoryQuery(start_timestamp=0.0, end_timestamp=999999.0)
        results = engine.search(query_full)
        assert isinstance(results, list)
        assert len(results) == 3

        # Очистка
        for entry in entries:
            engine.remove_entry(entry)

    def test_memory_index_engine_disabled_features(self):
        """Дымовой тест с отключенными функциями"""
        # Отключаем composite indexes и query cache
        engine = MemoryIndexEngine(enable_composite_indexes=False, enable_query_cache=False)

        entry = MemoryEntry("event", 0.5, 1000.0)
        engine.add_entry(entry)

        # Операции должны работать даже с отключенными функциями
        query = MemoryQuery(event_type="event")
        results = engine.search(query)
        assert isinstance(results, list)
        assert len(results) == 1

        stats = engine.get_stats()
        assert isinstance(stats, dict)

        engine.remove_entry(entry)

    def test_memory_index_engine_multiple_operations(self):
        """Дымовой тест последовательных операций"""
        engine = MemoryIndexEngine()

        # Последовательные операции
        entries = [
            MemoryEntry("event1", 0.3, 1000.0),
            MemoryEntry("event2", 0.7, 1001.0),
            MemoryEntry("event1", 0.9, 1002.0),
        ]

        # Добавляем все записи
        for entry in entries:
            engine.add_entry(entry)

        # Выполняем поиск
        query = MemoryQuery()
        results1 = engine.search(query)
        assert len(results1) == 3

        # Получаем статистику
        stats1 = engine.get_stats()
        assert stats1["total_entries"] == 3

        # Удаляем одну запись
        engine.remove_entry(entries[0])

        # Проверяем после удаления
        results2 = engine.search(query)
        assert len(results2) == 2

        stats2 = engine.get_stats()
        assert stats2["total_entries"] == 2

        # Очищаем кэш
        engine.clear_cache()

        # Финальная проверка
        results3 = engine.search(query)
        assert len(results3) == 2

        # Очистка
        for entry in entries[1:]:
            engine.remove_entry(entry)

    def test_memory_index_engine_error_conditions(self):
        """Дымовой тест обработки ошибочных условий"""
        engine = MemoryIndexEngine()

        # Попытка удалить несуществующую запись
        fake_entry = MemoryEntry("fake", 0.5, 1000.0)
        engine.remove_entry(fake_entry)  # Не должно вызывать исключений

        # Поиск с несуществующими критериями
        query = MemoryQuery(event_type="nonexistent")
        results = engine.search(query)
        assert isinstance(results, list)
        assert len(results) == 0

        # Статистика пустого индекса
        stats = engine.get_stats()
        assert isinstance(stats, dict)

    def test_memory_index_engine_cache_operations(self):
        """Дымовой тест операций с кэшем"""
        engine = MemoryIndexEngine(max_cache_size=10)

        # Добавляем запись
        entry = MemoryEntry("event", 0.5, 1000.0)
        engine.add_entry(entry)

        # Выполняем несколько одинаковых запросов для тестирования кэша
        query = MemoryQuery(event_type="event")

        for i in range(5):
            results = engine.search(query)
            assert isinstance(results, list)
            assert len(results) == 1

        # Очищаем кэш
        engine.clear_cache()

        # Запрос после очистки кэша
        results_after = engine.search(query)
        assert isinstance(results_after, list)
        assert len(results_after) == 1

        # Очистка
        engine.remove_entry(entry)

    # ============================================================================
    # MemoryQuery Smoke Tests
    # ============================================================================

    def test_memory_query_instantiation(self):
        """Тест создания экземпляра MemoryQuery"""
        # Без параметров
        query = MemoryQuery()
        assert query is not None
        assert isinstance(query, MemoryQuery)

        # С параметрами
        query_custom = MemoryQuery(
            event_type="test",
            min_significance=0.5,
            limit=50,
            sort_by="significance",
            sort_order="asc",
        )
        assert query_custom is not None
        assert isinstance(query_custom, MemoryQuery)

    def test_memory_query_empty_query_operations(self):
        """Дымовой тест операций с пустым запросом"""
        query = MemoryQuery()

        # Получение хэша
        hash_value = query.get_hash()
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0

    def test_memory_query_boundary_values(self):
        """Дымовой тест с граничными значениями MemoryQuery"""
        # Граничные значения significance
        query_min = MemoryQuery(min_significance=0.0, max_significance=0.0)
        query_max = MemoryQuery(min_significance=1.0, max_significance=1.0)

        # Граничные значения weight
        query_weight_min = MemoryQuery(min_weight=0.0, max_weight=0.0)
        query_weight_max = MemoryQuery(min_weight=1.0, max_weight=1.0)

        # Граничные значения limit
        query_limit_min = MemoryQuery(limit=0)
        query_limit_max = MemoryQuery(limit=10000)

        # Все запросы должны создаваться без исключений
        assert query_min is not None
        assert query_max is not None
        assert query_weight_min is not None
        assert query_weight_max is not None
        assert query_limit_min is not None
        assert query_limit_max is not None

        # Все должны возвращать хэши
        assert isinstance(query_min.get_hash(), str)
        assert isinstance(query_max.get_hash(), str)

    def test_memory_query_all_sort_options(self):
        """Дымовой тест всех опций сортировки"""
        sort_options = ["timestamp", "significance", "weight"]
        sort_orders = ["asc", "desc"]

        for sort_by in sort_options:
            for sort_order in sort_orders:
                query = MemoryQuery(sort_by=sort_by, sort_order=sort_order)
                assert query is not None
                assert isinstance(query.get_hash(), str)

    def test_memory_query_large_values(self):
        """Дымовой тест с большими значениями"""
        # Большие timestamp
        query = MemoryQuery(start_timestamp=999999999.0, end_timestamp=9999999999.0)
        assert query is not None
        assert isinstance(query.get_hash(), str)

    def test_memory_query_none_values(self):
        """Дымовой тест с None значениями"""
        query = MemoryQuery(
            event_type=None,
            min_significance=None,
            max_significance=None,
            start_timestamp=None,
            end_timestamp=None,
            min_weight=None,
            max_weight=None,
        )
        assert query is not None
        assert isinstance(query.get_hash(), str)

    def test_memory_query_hash_stability(self):
        """Дымовой тест стабильности хэширования"""
        query = MemoryQuery(event_type="test", min_significance=0.5)

        # Многократное получение хэша должно давать одинаковый результат
        hashes = [query.get_hash() for _ in range(10)]
        assert all(h == hashes[0] for h in hashes)

    def test_memory_query_different_instances_same_hash(self):
        """Дымовой тест одинакового хэша для одинаковых экземпляров"""
        query1 = MemoryQuery(event_type="test", min_significance=0.5, limit=10)
        query2 = MemoryQuery(event_type="test", min_significance=0.5, limit=10)

        assert query1.get_hash() == query2.get_hash()


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
            event_type="test_event", meaning_significance=0.8, timestamp=time.time()
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
        query = MemoryQuery(event_type="decay", min_significance=0.5)
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
        entries = [MemoryEntry("event", 0.9 - i * 0.1, 1000.0 + i) for i in range(10)]

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
        filtered = engine._filter_by_timestamp_range(engine.timestamp_entries, 1001.5, 1003.5)

        assert len(filtered) == 2  # timestamp 1002.0 и 1003.0
        assert filtered[0][0] == 1002.0
        assert filtered[1][0] == 1003.0


@pytest.mark.unit
class TestMemoryQuery:
    """Тесты для класса MemoryQuery"""

    def test_query_creation(self):
        """Тест создания запроса"""
        query = MemoryQuery(
            event_type="decay", min_significance=0.5, start_timestamp=1000.0, limit=10
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

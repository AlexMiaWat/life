"""
Unit-тесты для fallback стратегии в mcp_index_engine
"""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_index_engine import IndexEngine


@pytest.fixture
def temp_dirs():
    """Создает временные директории для тестирования"""
    docs_dir = tempfile.mkdtemp()
    todo_dir = tempfile.mkdtemp()
    src_dir = tempfile.mkdtemp()

    yield {
        "docs": Path(docs_dir),
        "todo": Path(todo_dir),
        "src": Path(src_dir),
    }

    # Очистка
    shutil.rmtree(docs_dir, ignore_errors=True)
    shutil.rmtree(todo_dir, ignore_errors=True)
    shutil.rmtree(src_dir, ignore_errors=True)


@pytest.fixture
def index_engine(temp_dirs):
    """Создает экземпляр IndexEngine для тестирования"""
    return IndexEngine(
        docs_dir=temp_dirs["docs"],
        todo_dir=temp_dirs["todo"],
        src_dir=temp_dirs["src"],
    )


@pytest.fixture
def search_functions():
    """Создает функции поиска для тестирования"""
    from mcp_index import (
        _search_and,
        _search_or,
        _search_phrase,
        _find_context_lines,
        _tokenize_query,
    )

    return {
        "search_and": _search_and,
        "search_or": _search_or,
        "search_phrase": _search_phrase,
        "find_context": _find_context_lines,
        "tokenize": _tokenize_query,
    }


@pytest.mark.unit
class TestFallbackIndexAvailability:
    """Тесты проверки доступности индекса"""

    def test_is_index_available_false_when_not_initialized(self, index_engine):
        """Тест что индекс недоступен до инициализации"""
        assert index_engine._is_index_available() is False

    def test_is_index_available_false_when_empty_index(self, index_engine, temp_dirs):
        """Тест что индекс недоступен при пустом индексе"""
        index_engine._initialized = True
        assert index_engine._is_index_available() is False

    def test_is_index_available_false_when_empty_cache(self, index_engine, temp_dirs):
        """Тест что индекс недоступен при пустом кэше"""
        index_engine._initialized = True
        index_engine.inverted_index["test"] = {"file.md"}
        assert index_engine._is_index_available() is False

    def test_is_index_available_true_when_ready(self, index_engine, temp_dirs):
        """Тест что индекс доступен когда все готово"""
        index_engine._initialized = True
        index_engine.inverted_index["test"] = {"file.md"}
        index_engine.content_cache["file.md"] = "test content"
        assert index_engine._is_index_available() is True


@pytest.mark.unit
class TestFallbackLinearSearch:
    """Тесты линейного поиска по кэшу (уровень 2)"""

    def test_linear_search_empty_cache(self, index_engine, temp_dirs, search_functions):
        """Тест линейного поиска при пустом кэше"""
        mode, tokens = search_functions["tokenize"]("test", "AND", False)
        results = index_engine._linear_search_in_cache(
            temp_dirs["docs"],
            "test",
            mode,
            tokens,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) == 0

    def test_linear_search_with_cache(self, index_engine, temp_dirs, search_functions):
        """Тест линейного поиска с кэшем"""
        # Добавляем файл в кэш
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")
        index_engine.content_cache["test.md"] = "Hello world test"

        mode, tokens = search_functions["tokenize"]("test", "AND", False)
        results = index_engine._linear_search_in_cache(
            temp_dirs["docs"],
            "test",
            mode,
            tokens,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) > 0
        assert any("test.md" in r["path"] for r in results)

    def test_linear_search_and_mode(self, index_engine, temp_dirs, search_functions):
        """Тест линейного поиска в режиме AND"""
        index_engine.content_cache["test.md"] = "Hello world test"
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        mode, tokens = search_functions["tokenize"]("hello world", "AND", False)
        results = index_engine._linear_search_in_cache(
            temp_dirs["docs"],
            "hello world",
            mode,
            tokens,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) > 0

    def test_linear_search_or_mode(self, index_engine, temp_dirs, search_functions):
        """Тест линейного поиска в режиме OR"""
        index_engine.content_cache["test.md"] = "Hello world"
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world", encoding="utf-8")

        mode, tokens = search_functions["tokenize"]("hello test", "OR", True)
        results = index_engine._linear_search_in_cache(
            temp_dirs["docs"],
            "hello test",
            mode,
            tokens,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) > 0

    def test_linear_search_phrase_mode(self, index_engine, temp_dirs, search_functions):
        """Тест линейного поиска в режиме PHRASE"""
        index_engine.content_cache["test.md"] = "Hello world test"
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        mode, phrase = search_functions["tokenize"]('"hello world"', "PHRASE", False)
        results = index_engine._linear_search_in_cache(
            temp_dirs["docs"],
            '"hello world"',
            mode,
            phrase,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) > 0

    def test_linear_search_limit(self, index_engine, temp_dirs, search_functions):
        """Тест ограничения количества результатов"""
        # Добавляем несколько файлов в кэш
        for i in range(20):
            filename = f"test{i}.md"
            index_engine.content_cache[filename] = "test content"
            test_file = temp_dirs["docs"] / filename
            test_file.write_text("test content", encoding="utf-8")

        mode, tokens = search_functions["tokenize"]("test", "AND", False)
        results = index_engine._linear_search_in_cache(
            temp_dirs["docs"],
            "test",
            mode,
            tokens,
            5,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) <= 5


@pytest.mark.unit
class TestFallbackGrepSearch:
    """Тесты grep-поиска по файлам (уровень 3)"""

    def test_grep_search_no_files(self, index_engine, temp_dirs, search_functions):
        """Тест grep-поиска при отсутствии файлов"""
        mode, tokens = search_functions["tokenize"]("test", "AND", False)
        results = index_engine._grep_search_in_files(
            temp_dirs["docs"],
            "test",
            mode,
            tokens,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) == 0

    def test_grep_search_with_files(self, index_engine, temp_dirs, search_functions):
        """Тест grep-поиска с файлами"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        mode, tokens = search_functions["tokenize"]("test", "AND", False)
        results = index_engine._grep_search_in_files(
            temp_dirs["docs"],
            "test",
            mode,
            tokens,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) > 0
        assert any("test.md" in r["path"] for r in results)

    def test_grep_search_updates_cache(self, index_engine, temp_dirs, search_functions):
        """Тест что grep-поиск обновляет кэш"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        assert "test.md" not in index_engine.content_cache

        mode, tokens = search_functions["tokenize"]("test", "AND", False)
        results = index_engine._grep_search_in_files(
            temp_dirs["docs"],
            "test",
            mode,
            tokens,
            10,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )

        # После grep-поиска файл должен быть в кэше
        assert "test.md" in index_engine.content_cache

    def test_grep_search_limit(self, index_engine, temp_dirs, search_functions):
        """Тест ограничения количества результатов в grep-поиске"""
        # Создаем несколько файлов
        for i in range(20):
            test_file = temp_dirs["docs"] / f"test{i}.md"
            test_file.write_text("test content", encoding="utf-8")

        mode, tokens = search_functions["tokenize"]("test", "AND", False)
        results = index_engine._grep_search_in_files(
            temp_dirs["docs"],
            "test",
            mode,
            tokens,
            5,
            search_functions["search_and"],
            search_functions["search_or"],
            search_functions["search_phrase"],
            search_functions["find_context"],
        )
        assert len(results) <= 5


@pytest.mark.integration
class TestFallbackSequence:
    """Тесты последовательности fallback уровней"""

    def test_fallback_level_1_index_available(self, index_engine, temp_dirs):
        """Тест что используется уровень 1 когда индекс доступен"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        index_engine.initialize()

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "test",
            mode="AND",
            limit=10,
        )

        # Должен использоваться индекс (уровень 1)
        assert len(results) > 0
        assert index_engine._is_index_available() is True

    def test_fallback_level_2_no_index(self, index_engine, temp_dirs):
        """Тест переключения на уровень 2 при недоступности индекса"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        # Добавляем файл в кэш, но не инициализируем индекс
        index_engine.content_cache["test.md"] = "Hello world test"

        # Очищаем индекс, чтобы симулировать его недоступность
        index_engine.inverted_index.clear()
        index_engine._initialized = False

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "test",
            mode="AND",
            limit=10,
        )

        # Должен использоваться линейный поиск (уровень 2)
        assert len(results) > 0
        assert index_engine._is_index_available() is False

    def test_fallback_level_3_no_cache(self, index_engine, temp_dirs):
        """Тест переключения на уровень 3 при недоступности кэша"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        # Очищаем индекс и кэш
        index_engine.inverted_index.clear()
        index_engine.content_cache.clear()
        index_engine._initialized = False

        cache_size_before = len(index_engine.content_cache)
        assert cache_size_before == 0  # Кэш пуст до поиска

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "test",
            mode="AND",
            limit=10,
        )

        # Должен использоваться grep-поиск (уровень 3)
        assert len(results) > 0
        # После grep-поиска файл должен быть добавлен в кэш
        assert len(index_engine.content_cache) > cache_size_before

    def test_fallback_sequence_index_error(self, index_engine, temp_dirs):
        """Тест переключения на уровень 2 при ошибке индекса"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        # Добавляем файл в кэш, но не инициализируем индекс
        index_engine.content_cache["test.md"] = "Hello world test"

        # Очищаем индекс, чтобы симулировать его недоступность
        index_engine.inverted_index.clear()
        index_engine._initialized = False

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "test",
            mode="AND",
            limit=10,
        )

        # Должен использоваться уровень 2 (линейный поиск)
        assert len(results) > 0

    def test_fallback_all_levels_fail(self, index_engine, temp_dirs):
        """Тест что возвращается пустой список если все уровни не дали результатов"""
        # Создаем пустую директорию
        # (не добавляем файлы и не инициализируем индекс)

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "nonexistent query",
            mode="AND",
            limit=10,
        )

        # Должен вернуться пустой список
        assert len(results) == 0

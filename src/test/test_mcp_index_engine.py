"""
Unit-тесты для модуля mcp_index_engine
"""

import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_index_engine import MAX_FILE_SIZE, IndexEngine


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


@pytest.mark.unit
class TestIndexEngineInitialization:
    """Тесты инициализации IndexEngine"""

    def test_init_with_paths(self, temp_dirs):
        """Тест создания IndexEngine с путями"""
        engine = IndexEngine(
            temp_dirs["docs"],
            temp_dirs["todo"],
            temp_dirs["src"],
        )
        assert engine.docs_dir == temp_dirs["docs"].resolve()
        assert engine.todo_dir == temp_dirs["todo"].resolve()
        assert engine.src_dir == temp_dirs["src"].resolve()
        assert len(engine.content_cache) == 0
        assert len(engine.inverted_index) == 0
        assert not engine._initialized

    def test_init_with_string_paths(self, temp_dirs):
        """Тест создания IndexEngine со строковыми путями"""
        engine = IndexEngine(
            str(temp_dirs["docs"]),
            str(temp_dirs["todo"]),
            str(temp_dirs["src"]),
        )
        assert isinstance(engine.docs_dir, Path)
        assert isinstance(engine.todo_dir, Path)
        assert isinstance(engine.src_dir, Path)

    def test_init_with_custom_limits(self, temp_dirs):
        """Тест создания IndexEngine с кастомными лимитами"""
        engine = IndexEngine(
            temp_dirs["docs"],
            temp_dirs["todo"],
            temp_dirs["src"],
            cache_size_limit=1000,
            max_file_size=5 * 1024 * 1024,
        )
        assert engine.cache_size_limit == 1000
        assert engine.max_file_size == 5 * 1024 * 1024


@pytest.mark.unit
class TestIndexEngineTokenization:
    """Тесты токенизации контента"""

    def test_tokenize_content(self, index_engine):
        """Тест токенизации простого текста"""
        content = "Hello world test"
        tokens = index_engine._tokenize_content(content)
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert len(tokens) == 3

    def test_tokenize_content_lowercase(self, index_engine):
        """Тест что токены приводятся к нижнему регистру"""
        content = "Hello WORLD Test"
        tokens = index_engine._tokenize_content(content)
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_tokenize_content_empty(self, index_engine):
        """Тест токенизации пустого текста"""
        tokens = index_engine._tokenize_content("")
        assert len(tokens) == 0

    def test_tokenize_content_special_chars(self, index_engine):
        """Тест токенизации текста со специальными символами"""
        content = "Hello, world! Test-123."
        tokens = index_engine._tokenize_content(content)
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert "123" in tokens


@pytest.mark.unit
class TestIndexEngineFileOperations:
    """Тесты операций с файлами"""

    def test_load_content(self, index_engine, temp_dirs):
        """Тест загрузки содержимого файла"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Test content", encoding="utf-8")

        content = index_engine._load_content(test_file)
        assert content == "Test content"

    def test_load_content_large_file(self, index_engine, temp_dirs):
        """Тест загрузки большого файла (должен быть пропущен)"""
        test_file = temp_dirs["docs"] / "large.md"
        # Создаем файл больше лимита
        large_content = "x" * (MAX_FILE_SIZE + 1)
        test_file.write_bytes(large_content.encode("utf-8"))

        with pytest.raises(ValueError, match="слишком большой"):
            index_engine._load_content(test_file)

    def test_get_base_dir(self, index_engine, temp_dirs):
        """Тест определения базовой директории"""
        test_file = temp_dirs["docs"] / "subdir" / "test.md"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("test")

        base_dir = index_engine._get_base_dir(test_file)
        assert base_dir == temp_dirs["docs"].resolve()

    def test_get_base_dir_todo(self, index_engine, temp_dirs):
        """Тест определения базовой директории для TODO"""
        test_file = temp_dirs["todo"] / "test.md"
        test_file.write_text("test")

        base_dir = index_engine._get_base_dir(test_file)
        assert base_dir == temp_dirs["todo"].resolve()

    def test_get_base_dir_none(self, index_engine, temp_dirs):
        """Тест определения базовой директории для файла вне базовых"""
        other_dir = tempfile.mkdtemp()
        test_file = Path(other_dir) / "test.md"
        test_file.write_text("test")

        base_dir = index_engine._get_base_dir(test_file)
        assert base_dir is None

        shutil.rmtree(other_dir, ignore_errors=True)

    def test_get_relative_path(self, index_engine, temp_dirs):
        """Тест получения относительного пути"""
        test_file = temp_dirs["docs"] / "subdir" / "test.md"
        rel_path = index_engine._get_relative_path(test_file, temp_dirs["docs"])
        assert rel_path == "subdir/test.md"

    def test_validate_path(self, index_engine, temp_dirs):
        """Тест валидации пути"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("test")

        assert index_engine._validate_path(test_file, temp_dirs["docs"]) is True

    def test_validate_path_traversal(self, index_engine, temp_dirs):
        """Тест защиты от path traversal"""
        # Попытка доступа к файлу вне базовой директории
        other_dir = tempfile.mkdtemp()
        test_file = Path(other_dir) / "test.md"
        test_file.write_text("test")

        assert index_engine._validate_path(test_file, temp_dirs["docs"]) is False

        shutil.rmtree(other_dir, ignore_errors=True)


@pytest.mark.unit
class TestIndexEngineIndexing:
    """Тесты индексации"""

    def test_index_directory_empty(self, index_engine, temp_dirs):
        """Тест индексации пустой директории"""
        index_engine.index_directory(temp_dirs["docs"])
        assert len(index_engine.content_cache) == 0

    def test_index_directory_single_file(self, index_engine, temp_dirs):
        """Тест индексации директории с одним файлом"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"])
        assert len(index_engine.content_cache) == 1
        assert "test.md" in index_engine.content_cache

    def test_index_directory_multiple_files(self, index_engine, temp_dirs):
        """Тест индексации директории с несколькими файлами"""
        (temp_dirs["docs"] / "test1.md").write_text("Hello", encoding="utf-8")
        (temp_dirs["docs"] / "test2.md").write_text("World", encoding="utf-8")
        (temp_dirs["docs"] / "subdir").mkdir(exist_ok=True)
        (temp_dirs["docs"] / "subdir" / "test3.md").write_text("Test", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"])
        assert len(index_engine.content_cache) == 3

    def test_index_directory_pattern(self, index_engine, temp_dirs):
        """Тест индексации с паттерном файлов"""
        (temp_dirs["docs"] / "test.md").write_text("Hello", encoding="utf-8")
        (temp_dirs["docs"] / "test.txt").write_text("World", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"], "*.md")
        assert len(index_engine.content_cache) == 1
        assert "test.md" in index_engine.content_cache
        assert "test.txt" not in index_engine.content_cache

    def test_initialize(self, index_engine, temp_dirs):
        """Тест инициализации индекса"""
        (temp_dirs["docs"] / "test.md").write_text("Hello", encoding="utf-8")
        (temp_dirs["todo"] / "todo.md").write_text("World", encoding="utf-8")

        index_engine.initialize()
        assert index_engine._initialized is True
        assert len(index_engine.content_cache) == 2

    def test_reindex(self, index_engine, temp_dirs):
        """Тест переиндексации"""
        (temp_dirs["docs"] / "test1.md").write_text("Hello", encoding="utf-8")
        index_engine.initialize()

        assert len(index_engine.content_cache) == 1

        # Добавляем новый файл
        (temp_dirs["docs"] / "test2.md").write_text("World", encoding="utf-8")
        index_engine.reindex()

        assert len(index_engine.content_cache) == 2

    def test_update_index_for_file(self, index_engine, temp_dirs):
        """Тест обновления индекса для файла"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"])

        # Проверяем что токены добавлены
        assert "hello" in index_engine.inverted_index
        assert "world" in index_engine.inverted_index
        assert "test.md" in index_engine.inverted_index["hello"]

        # Обновляем файл
        test_file.write_text("New content", encoding="utf-8")
        index_engine._update_index_for_file("test.md", "New content")

        # Старые токены должны быть удалены
        assert (
            "hello" not in index_engine.inverted_index
            or "test.md" not in index_engine.inverted_index["hello"]
        )
        # Новые токены должны быть добавлены
        assert "new" in index_engine.inverted_index
        assert "content" in index_engine.inverted_index


@pytest.mark.unit
class TestIndexEngineCache:
    """Тесты кэширования"""

    def test_get_content_caches(self, index_engine, temp_dirs):
        """Тест что содержимое кэшируется"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello", encoding="utf-8")

        content1 = index_engine._get_content(test_file, temp_dirs["docs"])
        content2 = index_engine._get_content(test_file, temp_dirs["docs"])

        assert content1 == "Hello"
        assert content2 == "Hello"
        assert len(index_engine.content_cache) == 1

    def test_get_content_updates_on_change(self, index_engine, temp_dirs):
        """Тест обновления кэша при изменении файла"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello", encoding="utf-8")

        index_engine._get_content(test_file, temp_dirs["docs"])
        assert index_engine.content_cache["test.md"] == "Hello"

        # Изменяем файл
        time.sleep(0.1)  # Небольшая задержка для изменения mtime
        test_file.write_text("World", encoding="utf-8")

        content = index_engine._get_content(test_file, temp_dirs["docs"])
        assert content == "World"
        assert index_engine.content_cache["test.md"] == "World"

    def test_cache_eviction(self, index_engine, temp_dirs):
        """Тест удаления старых записей из кэша при превышении лимита"""
        # Создаем движок с маленьким лимитом кэша
        engine = IndexEngine(
            temp_dirs["docs"],
            temp_dirs["todo"],
            temp_dirs["src"],
            cache_size_limit=3,
        )

        # Добавляем файлы до превышения лимита
        for i in range(5):
            test_file = temp_dirs["docs"] / f"test{i}.md"
            test_file.write_text(f"Content {i}", encoding="utf-8")
            engine._get_content(test_file, temp_dirs["docs"])

        # Кэш не должен превышать лимит
        assert len(engine.content_cache) <= 3

    def test_get_file_content(self, index_engine, temp_dirs):
        """Тест получения содержимого файла из кэша"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello", encoding="utf-8")

        # Сначала индексируем
        index_engine._get_content(test_file, temp_dirs["docs"])

        # Затем получаем из кэша
        content = index_engine.get_file_content(test_file, temp_dirs["docs"])
        assert content == "Hello"

    def test_get_file_content_not_cached(self, index_engine, temp_dirs):
        """Тест получения содержимого файла не из кэша"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello", encoding="utf-8")

        content = index_engine.get_file_content(test_file, temp_dirs["docs"])
        assert content is None  # Файл не в кэше


@pytest.mark.unit
class TestIndexEngineSearch:
    """Тесты поиска"""

    def test_search_empty_directory(self, index_engine, temp_dirs):
        """Тест поиска в пустой директории"""
        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "test",
            limit=10,
        )
        assert len(results) == 0

    def test_search_single_file(self, index_engine, temp_dirs):
        """Тест поиска в директории с одним файлом"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello world test", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"])

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "test",
            mode="AND",
            limit=10,
        )
        assert len(results) > 0
        assert any("test.md" in r["path"] for r in results)

    def test_search_multiple_files(self, index_engine, temp_dirs):
        """Тест поиска в директории с несколькими файлами"""
        (temp_dirs["docs"] / "test1.md").write_text("Hello world", encoding="utf-8")
        (temp_dirs["docs"] / "test2.md").write_text("Hello test", encoding="utf-8")
        (temp_dirs["docs"] / "test3.md").write_text("Other content", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"])

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "hello",
            mode="OR",
            limit=10,
        )
        assert len(results) >= 2

    def test_search_limit(self, index_engine, temp_dirs):
        """Тест ограничения количества результатов"""
        for i in range(20):
            test_file = temp_dirs["docs"] / f"test{i}.md"
            test_file.write_text("Hello world", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"])

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "hello",
            limit=5,
        )
        assert len(results) <= 5

    def test_search_invalid_directory(self, index_engine):
        """Тест поиска в несуществующей директории"""
        non_existent = Path("/non/existent/path")
        results = index_engine.search_in_directory(
            non_existent,
            "test",
        )
        assert len(results) == 0

    def test_search_empty_query(self, index_engine, temp_dirs):
        """Тест поиска с пустым запросом"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"])

        results = index_engine.search_in_directory(
            temp_dirs["docs"],
            "",
        )
        assert len(results) == 0


@pytest.mark.unit
class TestIndexEngineUpdateFile:
    """Тесты обновления файлов"""

    def test_update_file(self, index_engine, temp_dirs):
        """Тест обновления индекса для одного файла"""
        test_file = temp_dirs["docs"] / "test.md"
        test_file.write_text("Hello", encoding="utf-8")

        index_engine.update_file(test_file)

        assert "test.md" in index_engine.content_cache
        assert index_engine.content_cache["test.md"] == "Hello"

    def test_update_file_not_exists(self, index_engine, temp_dirs):
        """Тест обновления несуществующего файла"""
        test_file = temp_dirs["docs"] / "nonexistent.md"

        # Не должно быть ошибки
        index_engine.update_file(test_file)

        assert "nonexistent.md" not in index_engine.content_cache


@pytest.mark.unit
class TestIndexEngineEdgeCases:
    """Тесты граничных случаев"""

    def test_index_nonexistent_directory(self, index_engine):
        """Тест индексации несуществующей директории"""
        non_existent = Path("/non/existent/path")
        index_engine.index_directory(non_existent)
        # Не должно быть ошибки

    def test_index_file_not_matching_pattern(self, index_engine, temp_dirs):
        """Тест что файлы не соответствующие паттерну не индексируются"""
        (temp_dirs["docs"] / "test.txt").write_text("Hello", encoding="utf-8")

        index_engine.index_directory(temp_dirs["docs"], "*.md")
        assert len(index_engine.content_cache) == 0

    def test_get_content_nonexistent_file(self, index_engine, temp_dirs):
        """Тест получения содержимого несуществующего файла"""
        test_file = temp_dirs["docs"] / "nonexistent.md"
        content = index_engine._get_content(test_file, temp_dirs["docs"])
        assert content == ""

    def test_initialize_multiple_times(self, index_engine, temp_dirs):
        """Тест множественной инициализации"""
        (temp_dirs["docs"] / "test.md").write_text("Hello", encoding="utf-8")

        index_engine.initialize()
        cache_size_1 = len(index_engine.content_cache)

        index_engine.initialize()
        cache_size_2 = len(index_engine.content_cache)

        # Вторая инициализация не должна дублировать файлы
        assert cache_size_1 == cache_size_2

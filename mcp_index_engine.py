#!/usr/bin/env python3
"""
Модуль индексации для MCP сервера.
Предоставляет кэширование содержимого файлов и инвертированный индекс для быстрого поиска.
"""

import logging
import re
from collections import OrderedDict
from pathlib import Path
from typing import Optional

# Настройка логирования
logger = logging.getLogger(__name__)

# Константы
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_CACHE_SIZE_LIMIT = 10000  # Максимальное количество файлов в кэше
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB - максимальный размер файла для индексации


class IndexEngine:
    """
    Движок индексации для быстрого поиска по файлам.

    Предоставляет:
    - Кэш содержимого файлов (content_cache)
    - Инвертированный индекс (inverted_index) для быстрого поиска по токенам
    - Автоматическое отслеживание изменений файлов
    """

    def __init__(
        self,
        docs_dir: Path,
        todo_dir: Path,
        src_dir: Path,
        cache_size_limit: int = DEFAULT_CACHE_SIZE_LIMIT,
        max_file_size: int = MAX_FILE_SIZE,
    ):
        """
        Инициализация IndexEngine.

        Args:
            docs_dir: Директория с документацией
            todo_dir: Директория с TODO файлами
            src_dir: Директория с исходным кодом
            cache_size_limit: Максимальное количество файлов в кэше (по умолчанию 10000)
            max_file_size: Максимальный размер файла для индексации в байтах (по умолчанию 10MB)
        """
        # Валидация входных данных
        if not isinstance(docs_dir, Path):
            docs_dir = Path(docs_dir)
        if not isinstance(todo_dir, Path):
            todo_dir = Path(todo_dir)
        if not isinstance(src_dir, Path):
            src_dir = Path(src_dir)

        self.docs_dir = docs_dir.resolve()
        self.todo_dir = todo_dir.resolve()
        self.src_dir = src_dir.resolve()
        self.cache_size_limit = cache_size_limit
        self.max_file_size = max_file_size

        # Кэш содержимого файлов: относительный путь -> содержимое
        # Используем OrderedDict для реализации LRU eviction
        self.content_cache: OrderedDict[str, str] = OrderedDict()

        # Инвертированный индекс: токен -> множество относительных путей к файлам
        self.inverted_index: dict[str, set[str]] = {}

        # Время модификации файлов: относительный путь -> mtime
        self.file_mtimes: dict[str, float] = {}

        # Индекс для быстрого поиска файлов по токенам (для оптимизации обновления)
        # Файл -> множество токенов
        self.file_tokens: dict[str, set[str]] = {}

        # Флаг инициализации
        self._initialized = False

    def initialize(self):
        """Инициализация индекса (ленивая загрузка)."""
        if not self._initialized:
            self.index_directory(self.docs_dir, "*.md")
            self.index_directory(self.todo_dir, "*.md")
            self._initialized = True

    def _tokenize_content(self, content: str) -> set[str]:
        """
        Извлекает токены из содержимого файла.

        Args:
            content: Содержимое файла

        Returns:
            Множество токенов (слов) в нижнем регистре
        """
        tokens = re.findall(r"\b\w+\b", content.lower())
        return set(tokens)

    def _load_content(self, file_path: Path) -> str:
        """
        Загружает содержимое файла с проверкой размера.

        Args:
            file_path: Путь к файлу

        Returns:
            Содержимое файла

        Raises:
            ValueError: Если файл слишком большой
            IOError: Если файл не удалось прочитать
        """
        # Проверка размера файла
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise ValueError(
                f"Файл {file_path} слишком большой ({file_size} байт). "
                f"Максимальный размер: {self.max_file_size} байт"
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            raise

    def _validate_path(self, file_path: Path, base_dir: Path) -> bool:
        """
        Валидирует путь файла для защиты от path traversal.

        Args:
            file_path: Путь к файлу
            base_dir: Базовая директория

        Returns:
            True если путь валиден, False иначе
        """
        try:
            resolved_path = file_path.resolve()
            resolved_base = base_dir.resolve()
            # Проверяем, что файл находится внутри базовой директории
            return (
                resolved_base in resolved_path.parents
                or resolved_path.parent == resolved_base
            )
        except Exception:
            return False

    def _get_base_dir(self, file_path: Path) -> Optional[Path]:
        """
        Определяет базовую директорию для файла.

        Args:
            file_path: Путь к файлу

        Returns:
            Базовая директория или None
        """
        try:
            resolved_path = file_path.resolve()
            if (
                self.docs_dir in resolved_path.parents
                or resolved_path.parent == self.docs_dir
            ):
                return self.docs_dir
            elif (
                self.todo_dir in resolved_path.parents
                or resolved_path.parent == self.todo_dir
            ):
                return self.todo_dir
            elif (
                self.src_dir in resolved_path.parents
                or resolved_path.parent == self.src_dir
            ):
                return self.src_dir
        except Exception as e:
            logger.debug(f"Ошибка определения базовой директории для {file_path}: {e}")
        return None

    def _get_relative_path(self, file_path: Path, base_dir: Path) -> str:
        """
        Получает относительный путь файла от базовой директории.

        Args:
            file_path: Полный путь к файлу
            base_dir: Базовая директория

        Returns:
            Относительный путь
        """
        try:
            return str(file_path.relative_to(base_dir))
        except ValueError:
            # Если файл не находится в базовой директории, используем полный путь
            return str(file_path)

    def _update_index_for_file(self, rel_path: str, content: str):
        """
        Обновляет инвертированный индекс для файла (оптимизированная версия).

        Args:
            rel_path: Относительный путь к файлу
            content: Содержимое файла
        """
        # Получаем новые токены
        new_tokens = self._tokenize_content(content)

        # Получаем старые токены из индекса файлов
        old_tokens = self.file_tokens.get(rel_path, set())

        # Находим токены для удаления и добавления
        tokens_to_remove = old_tokens - new_tokens
        tokens_to_add = new_tokens - old_tokens

        # Удаляем старые токены из инвертированного индекса
        for token in tokens_to_remove:
            if token in self.inverted_index:
                self.inverted_index[token].discard(rel_path)
                if not self.inverted_index[token]:
                    del self.inverted_index[token]

        # Добавляем новые токены в инвертированный индекс
        for token in tokens_to_add:
            if token not in self.inverted_index:
                self.inverted_index[token] = set()
            self.inverted_index[token].add(rel_path)

        # Обновляем индекс файлов
        self.file_tokens[rel_path] = new_tokens

    def _evict_cache_if_needed(self):
        """Удаляет старые записи из кэша, если превышен лимит (LRU eviction)."""
        while len(self.content_cache) >= self.cache_size_limit:
            # Удаляем самую старую запись (FIFO из OrderedDict)
            oldest_key = next(iter(self.content_cache))
            self._remove_file_from_cache(oldest_key)

    def _remove_file_from_cache(self, rel_path: str):
        """
        Удаляет файл из кэша и индексов.

        Args:
            rel_path: Относительный путь к файлу
        """
        # Удаляем из кэша
        if rel_path in self.content_cache:
            del self.content_cache[rel_path]

        # Удаляем из индекса времени модификации
        if rel_path in self.file_mtimes:
            del self.file_mtimes[rel_path]

        # Удаляем токены файла из инвертированного индекса
        if rel_path in self.file_tokens:
            tokens = self.file_tokens[rel_path]
            for token in tokens:
                if token in self.inverted_index:
                    self.inverted_index[token].discard(rel_path)
                    if not self.inverted_index[token]:
                        del self.inverted_index[token]
            del self.file_tokens[rel_path]

    def _get_content(self, file_path: Path, base_dir: Path) -> str:
        """
        Получает содержимое из кэша или загружает и кэширует.

        Args:
            file_path: Полный путь к файлу
            base_dir: Базовая директория

        Returns:
            Содержимое файла
        """
        # Валидация пути
        if not self._validate_path(file_path, base_dir):
            logger.warning(
                f"Попытка доступа к файлу вне базовой директории: {file_path}"
            )
            return ""

        rel_path = self._get_relative_path(file_path, base_dir)

        # Проверка изменений файла
        if file_path.exists():
            try:
                current_mtime = file_path.stat().st_mtime
                if rel_path in self.file_mtimes:
                    if current_mtime > self.file_mtimes[rel_path]:
                        # Файл изменился, обновляем кэш
                        try:
                            content = self._load_content(file_path)
                            # Перемещаем в конец для LRU (обновляем порядок доступа)
                            if rel_path in self.content_cache:
                                del self.content_cache[rel_path]
                            self.content_cache[rel_path] = content
                            self.file_mtimes[rel_path] = current_mtime
                            self._update_index_for_file(rel_path, content)
                            return content
                        except ValueError as e:
                            logger.warning(f"Пропущен файл {file_path}: {e}")
                            return ""
                        except Exception as e:
                            logger.error(f"Ошибка обновления файла {file_path}: {e}")
                            return ""

                # Файл не в кэше или не изменился
                if rel_path not in self.content_cache:
                    try:
                        content = self._load_content(file_path)
                        # Проверяем лимит кэша перед добавлением
                        self._evict_cache_if_needed()
                        self.content_cache[rel_path] = content
                        self.file_mtimes[rel_path] = current_mtime
                        self._update_index_for_file(rel_path, content)
                    except ValueError as e:
                        logger.warning(f"Пропущен файл {file_path}: {e}")
                        return ""
                    except Exception as e:
                        logger.error(f"Ошибка загрузки файла {file_path}: {e}")
                        return ""

                # Перемещаем в конец для LRU (обновляем порядок доступа)
                content = self.content_cache.pop(rel_path)
                self.content_cache[rel_path] = content
                return content
            except Exception as e:
                logger.error(f"Ошибка доступа к файлу {file_path}: {e}")
                return ""
        else:
            # Файл не существует, удаляем из кэша
            if rel_path in self.content_cache:
                self._remove_file_from_cache(rel_path)
            return ""

    def index_directory(self, directory: Path, file_pattern: str = "*.md"):
        """
        Индексирует все файлы в директории.

        Args:
            directory: Директория для индексации
            file_pattern: Паттерн файлов для индексации (по умолчанию "*.md")
        """
        # Валидация входных данных
        if not isinstance(directory, Path):
            directory = Path(directory)

        if not directory.exists():
            logger.warning(f"Директория не существует: {directory}")
            return

        if not directory.is_dir():
            logger.warning(f"Путь не является директорией: {directory}")
            return

        indexed_count = 0
        skipped_count = 0

        for file_path in directory.rglob(file_pattern):
            if file_path.is_file():
                try:
                    self._get_content(file_path, directory)
                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"Пропущен файл {file_path} при индексации: {e}")
                    skipped_count += 1
                    continue

        logger.info(
            f"Индексация директории {directory} завершена: "
            f"проиндексировано {indexed_count}, пропущено {skipped_count}"
        )

    def reindex(self):
        """Выполняет полную переиндексацию всех директорий."""
        logger.info("Начало полной переиндексации")
        self.content_cache.clear()
        self.inverted_index.clear()
        self.file_mtimes.clear()
        self.file_tokens.clear()
        self._initialized = False
        self.initialize()
        logger.info("Переиндексация завершена")

    def update_file(self, file_path: Path):
        """
        Обновляет индекс для одного файла.

        Args:
            file_path: Путь к файлу для обновления
        """
        # Валидация входных данных
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        base_dir = self._get_base_dir(file_path)
        if base_dir and file_path.exists():
            try:
                self._get_content(file_path, base_dir)
            except Exception as e:
                logger.error(f"Ошибка обновления файла {file_path}: {e}")

    def get_file_content(self, file_path: Path, base_dir: Path) -> Optional[str]:
        """
        Получает содержимое файла из кэша.

        Args:
            file_path: Полный путь к файлу
            base_dir: Базовая директория

        Returns:
            Содержимое файла или None, если файл не в кэше
        """
        rel_path = self._get_relative_path(file_path, base_dir)
        return self.content_cache.get(rel_path)

    def search_in_directory(
        self,
        directory: Path,
        query: str,
        mode: str = "AND",
        limit: int = DEFAULT_SEARCH_LIMIT,
        tokenize_query_func=None,
        search_and_func=None,
        search_or_func=None,
        search_phrase_func=None,
        find_context_func=None,
    ) -> list[dict]:
        """
        Поиск в указанной директории с использованием индекса.

        Args:
            directory: Директория для поиска
            query: Поисковый запрос
            mode: Режим поиска ("AND", "OR", "PHRASE")
            limit: Максимальное количество результатов
            tokenize_query_func: Функция токенизации запроса
            search_and_func: Функция поиска в режиме AND
            search_or_func: Функция поиска в режиме OR
            search_phrase_func: Функция поиска в режиме PHRASE
            find_context_func: Функция поиска контекста

        Returns:
            Список результатов поиска с путями и контекстом
        """
        # Валидация входных данных
        if not isinstance(directory, Path):
            directory = Path(directory)

        if not directory.exists():
            logger.warning(f"Директория для поиска не существует: {directory}")
            return []

        if not isinstance(query, str) or not query.strip():
            logger.warning("Пустой поисковый запрос")
            return []

        if limit <= 0:
            limit = DEFAULT_SEARCH_LIMIT

        # Используем переданные функции или импортируем из mcp_index
        if tokenize_query_func is None:
            from mcp_index import _tokenize_query

            tokenize_query_func = _tokenize_query

        if search_and_func is None:
            from mcp_index import _search_and

            search_and_func = _search_and

        if search_or_func is None:
            from mcp_index import _search_or

            search_or_func = _search_or

        if search_phrase_func is None:
            from mcp_index import _search_phrase

            search_phrase_func = _search_phrase

        if find_context_func is None:
            from mcp_index import _find_context_lines

            find_context_func = _find_context_lines

        # Токенизация запроса
        explicit_mode = mode != "AND"
        search_mode, tokens_or_phrase = tokenize_query_func(query, mode, explicit_mode)

        # Определяем кандидатов из индекса
        candidate_files = set()

        if search_mode == "PHRASE":
            # Для PHRASE mode используем полный поиск по кэшу
            phrase = str(tokens_or_phrase)
            for rel_path, content in self.content_cache.items():
                full_path = directory / rel_path
                if full_path.exists() and search_phrase_func(content, phrase):
                    candidate_files.add(rel_path)
        elif search_mode == "AND" and isinstance(tokens_or_phrase, list):
            # Пересечение множеств файлов для каждого токена
            if tokens_or_phrase:
                candidate_files = set(
                    self.inverted_index.get(tokens_or_phrase[0].lower(), set())
                )
                for token in tokens_or_phrase[1:]:
                    candidate_files &= self.inverted_index.get(token.lower(), set())
        elif search_mode == "OR" and isinstance(tokens_or_phrase, list):
            # Объединение множеств файлов
            for token in tokens_or_phrase:
                candidate_files |= self.inverted_index.get(token.lower(), set())

        # Фильтруем результаты и добавляем контекст
        results = []
        for rel_path in candidate_files:
            if len(results) >= limit:
                break

            full_path = directory / rel_path
            if not full_path.exists():
                continue

            try:
                content = self._get_content(full_path, directory)

                # Применяем режим поиска для точной проверки
                match = False
                if search_mode == "PHRASE":
                    match = search_phrase_func(content, str(tokens_or_phrase))
                elif search_mode == "AND" and isinstance(tokens_or_phrase, list):
                    match = search_and_func(content, tokens_or_phrase)
                elif search_mode == "OR" and isinstance(tokens_or_phrase, list):
                    match = search_or_func(content, tokens_or_phrase)

                if match:
                    # Находим контекст
                    context_lines = find_context_func(
                        content, query, search_mode, tokens_or_phrase
                    )
                    context = "\n".join(context_lines)

                    results.append(
                        {
                            "path": rel_path,
                            "title": full_path.name,
                            "context": context,
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"Ошибка при обработке результата поиска {rel_path}: {e}"
                )
                continue

        return results

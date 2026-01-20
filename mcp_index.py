#!/usr/bin/env python3
"""
MCP Server для документации проекта Life.
Предоставляет доступ к документации через инструменты и ресурсы MCP.
Использует FastMCP для упрощения.
"""

import logging
import os
import threading
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Настройка логирования
logger = logging.getLogger(__name__)

# Блокировка для защиты от одновременного доступа к переиндексации
_reindex_lock = threading.Lock()

# Путь к директории документации
DOCS_DIR = Path(__file__).parent / "docs"

# Путь к директории TODO
TODO_DIR = Path(__file__).parent / "todo"

# Путь к директории исходного кода
SRC_DIR = Path(__file__).parent / "src"

# Путь к директории планов (master индексы)
PLANS_DIR = Path(__file__).parent / "plans"

# Путь к директории данных (snapshots)
DATA_DIR = Path(__file__).parent / "data"

# Создание FastMCP сервера
app = FastMCP("life-docs-server")

# Глобальный экземпляр IndexEngine (ленивая инициализация)
_index_engine = None

# Глобальный менеджер поиска (ленивая инициализация)
_search_manager = None


def _get_index_engine():
    """Получает или создает экземпляр IndexEngine."""
    global _index_engine
    if _index_engine is None:
        from mcp_index_engine import IndexEngine

        _index_engine = IndexEngine(DOCS_DIR, TODO_DIR, SRC_DIR)
        _index_engine.initialize()
    return _index_engine


def _get_search_manager():
    """Получает или создает SearchManager для multi-provider архитектуры."""
    global _search_manager
    if _search_manager is None:
        from mcp_search_provider import SearchManager, IndexSearchProvider

        engine = _get_index_engine()
        _search_manager = SearchManager()
        _search_manager.add_provider(IndexSearchProvider(engine))
        # Опционально: добавить LLM провайдер в будущем
        # if llm_client:
        #     from mcp_search_provider import LLMSearchProvider
        #     _search_manager.add_provider(LLMSearchProvider(llm_client))
    return _search_manager


def _tokenize_query(
    query: str, default_mode: str = "AND", explicit_mode: bool = False
) -> tuple[str, list[str] | str]:
    """
    Токенизирует запрос и определяет режим поиска.

    Args:
        query: Поисковый запрос
        default_mode: Режим по умолчанию (AND/OR/PHRASE).
        explicit_mode: True, если режим был указан явно пользователем (не default).

    Returns:
        Tuple (mode, tokens_or_phrase):
        - mode: "AND", "OR", или "PHRASE"
        - tokens_or_phrase: список токенов для AND/OR или строка для PHRASE
    """
    import re

    query = query.strip()

    # Валидация и нормализация режима
    mode = (default_mode or "AND").strip().upper()
    if mode not in {"AND", "OR", "PHRASE"}:
        mode = "AND"

    # Проверка на кавычки: если запрос в кавычках, автоматически используем PHRASE
    # (согласно контракту API: "PHRASE определяется автоматически по кавычкам")
    # Явный режим имеет приоритет только если он был указан явно как AND или OR
    is_quoted = query.startswith('"') and query.endswith('"') and len(query) > 2
    if is_quoted:
        inner = query[1:-1].strip()
        # Если режим явно указан как PHRASE, используем его
        if mode == "PHRASE":
            return ("PHRASE", inner)
        # Если режим был указан явно как AND/OR, приоритет у явного режима
        # (токенизируем содержимое кавычек для AND/OR)
        # Иначе (режим не указан явно или default_mode="AND") - кавычки автоматически включают PHRASE
        if explicit_mode and mode in {"AND", "OR"}:
            # Явный AND/OR режим имеет приоритет над кавычками
            query = inner
        else:
            # Режим не указан явно или это default - кавычки автоматически включают PHRASE
            return ("PHRASE", inner)

    # Явный PHRASE mode без кавычек: ищем точную фразу как есть
    if mode == "PHRASE":
        return ("PHRASE", query)

    # Токенизация для AND/OR: разбиваем на слова, удаляем пунктуацию
    tokens = re.findall(r"\b\w+\b", query.lower())

    # Валидация: пустой список токенов означает пустой/невалидный запрос
    if not tokens:
        # Возвращаем пустой список, вызывающий код должен обработать это
        return (mode, tokens)

    return (mode, tokens)


def _search_and(content: str, tokens: list[str]) -> bool:
    """Проверяет, что все токены присутствуют в контенте."""
    # Пустой список токенов не должен матчить всё
    if not tokens:
        return False
    content_lower = content.lower()
    return all(token in content_lower for token in tokens)


def _search_or(content: str, tokens: list[str]) -> bool:
    """Проверяет, что хотя бы один токен присутствует в контенте."""
    # Пустой список токенов не должен матчить всё
    if not tokens:
        return False
    content_lower = content.lower()
    return any(token in content_lower for token in tokens)


def _search_phrase(content: str, phrase: str) -> bool:
    """Ищет точную фразу в контенте (case-insensitive)."""
    # Пустая фраза не должна матчить всё
    if not phrase or not phrase.strip():
        return False
    return phrase.lower() in content.lower()


def _find_context_lines(
    content: str, query: str, mode: str, tokens_or_phrase: list[str] | str
) -> list[str]:
    """
    Находит контекст вокруг найденного текста.

    Args:
        content: Содержимое файла
        query: Исходный запрос
        mode: Режим поиска
        tokens_or_phrase: Токены или фраза для поиска

    Returns:
        Список строк контекста
    """
    lines = content.split("\n")
    context_lines = []
    content_lower = content.lower()

    # Определяем, что искать для контекста
    # Выбираем первый реально найденный токен/фразу
    if mode == "PHRASE":
        search_term = str(tokens_or_phrase).lower()
        # Проверяем, что фраза действительно найдена
        if search_term not in content_lower:
            return []
    elif mode == "AND" and isinstance(tokens_or_phrase, list):
        # Для AND ищем первый токен, который реально присутствует в контенте
        search_term = None
        for token in tokens_or_phrase:
            if token.lower() in content_lower:
                search_term = token.lower()
                break
        if not search_term:
            # Если ни один токен не найден (не должно быть, но на всякий случай)
            search_term = query.lower()
    elif mode == "OR" and isinstance(tokens_or_phrase, list):
        # Для OR ищем первый токен, который реально присутствует в контенте
        search_term = None
        for token in tokens_or_phrase:
            if token.lower() in content_lower:
                search_term = token.lower()
                break
        if not search_term:
            # Если ни один токен не найден (не должно быть, но на всякий случай)
            search_term = query.lower()
    else:
        search_term = query.lower()

    # Находим первую строку с совпадением
    for i, line in enumerate(lines):
        if search_term in line.lower():
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context_lines.extend(lines[start:end])
            break

    return context_lines[:5]  # Ограничить контекст


@app.tool()
async def search_docs(query: str, search_mode: str = "AND", limit: int = 10) -> str:
    """Поиск по ключевым словам в документации проекта Life.

    Args:
        query: Ключевые слова для поиска. Если запрос в кавычках и search_mode не указан явно,
               автоматически используется режим PHRASE.
        search_mode: Режим поиска ("AND", "OR", "PHRASE"). По умолчанию "AND".
                     Если запрос в кавычках, PHRASE определяется автоматически (если режим не указан явно).
        limit: Максимальное количество результатов (по умолчанию 10)
    """
    # Валидация пустого запроса
    if not query or not query.strip():
        return "Ошибка: пустой запрос. Укажите хотя бы одно ключевое слово."

    # Определяем, был ли режим указан явно (проверяем, был ли передан не-default параметр)
    # В FastMCP мы не можем различить это напрямую, поэтому используем эвристику:
    # если search_mode != "AND", считаем что он указан явно
    explicit_mode = search_mode != "AND"

    # Определяем режим и токенизируем запрос
    mode, tokens_or_phrase = _tokenize_query(query, search_mode, explicit_mode)

    # Валидация результата токенизации
    if (
        mode in {"AND", "OR"}
        and isinstance(tokens_or_phrase, list)
        and not tokens_or_phrase
    ):
        return f"Ошибка: запрос '{query}' не содержит валидных слов для поиска."
    if mode == "PHRASE" and (not tokens_or_phrase or not str(tokens_or_phrase).strip()):
        return f"Ошибка: пустая фраза в запросе '{query}'."

    # Используем SearchManager для поиска (multi-provider архитектура)
    manager = _get_search_manager()
    results = manager.search(
        DOCS_DIR,
        query,
        search_mode,
        limit,
        tokenize_query_func=_tokenize_query,
        search_and_func=_search_and,
        search_or_func=_search_or,
        search_phrase_func=_search_phrase,
        find_context_func=_find_context_lines,
    )

    if not results:
        return f"По запросу '{query}' ничего не найдено."

    text = (
        f"Найдено {len(results)} результатов по запросу '{query}' (режим: {mode}):\n\n"
    )
    for result in results:
        text += f"**{result['path']}**\n{result['context']}\n\n---\n\n"

    return text


@app.tool()
async def search_todo(query: str, search_mode: str = "AND", limit: int = 10) -> str:
    """Поиск по ключевым словам в документации TODO проекта Life.

    Args:
        query: Ключевые слова для поиска. Если запрос в кавычках и search_mode не указан явно,
               автоматически используется режим PHRASE.
        search_mode: Режим поиска ("AND", "OR", "PHRASE"). По умолчанию "AND".
                     Если запрос в кавычках, PHRASE определяется автоматически (если режим не указан явно).
        limit: Максимальное количество результатов (по умолчанию 10)
    """
    # Валидация пустого запроса
    if not query or not query.strip():
        return "Ошибка: пустой запрос. Укажите хотя бы одно ключевое слово."

    # Определяем, был ли режим указан явно (проверяем, был ли передан не-default параметр)
    # В FastMCP мы не можем различить это напрямую, поэтому используем эвристику:
    # если search_mode != "AND", считаем что он указан явно
    explicit_mode = search_mode != "AND"

    # Определяем режим и токенизируем запрос
    mode, tokens_or_phrase = _tokenize_query(query, search_mode, explicit_mode)

    # Валидация результата токенизации
    if (
        mode in {"AND", "OR"}
        and isinstance(tokens_or_phrase, list)
        and not tokens_or_phrase
    ):
        return f"Ошибка: запрос '{query}' не содержит валидных слов для поиска."
    if mode == "PHRASE" and (not tokens_or_phrase or not str(tokens_or_phrase).strip()):
        return f"Ошибка: пустая фраза в запросе '{query}'."

    # Используем IndexEngine для поиска
    engine = _get_index_engine()
    results = engine.search_in_directory(
        TODO_DIR,
        query,
        search_mode,
        limit,
        tokenize_query_func=_tokenize_query,
        search_and_func=_search_and,
        search_or_func=_search_or,
        search_phrase_func=_search_phrase,
        find_context_func=_find_context_lines,
    )

    if not results:
        return f"По запросу '{query}' ничего не найдено."

    text = (
        f"Найдено {len(results)} результатов по запросу '{query}' (режим: {mode}):\n\n"
    )
    for result in results:
        text += f"**{result['path']}**\n{result['context']}\n\n---\n\n"

    return text


@app.tool()
async def get_doc_content(path: str) -> str:
    """Получить полное содержимое документа по пути.

    Args:
        path: Относительный путь к документу в docs/
    """
    file_path = DOCS_DIR / path

    if not file_path.exists() or not file_path.is_file():
        return f"Файл не найден: {path}"

    try:
        # Используем IndexEngine для получения содержимого из кэша
        engine = _get_index_engine()
        content = engine.get_file_content(file_path, DOCS_DIR)

        # Если файл не в кэше, загружаем его
        if content is None:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Обновляем кэш
            engine.update_file(file_path)

        return f"# {path}\n\n{content}"
    except Exception as e:
        return f"Ошибка чтения файла {path}: {str(e)}"


@app.tool()
async def get_todo_content(path: str) -> str:
    """Получить полное содержимое документа TODO по пути.

    Args:
        path: Относительный путь к документу в todo/
    """
    file_path = TODO_DIR / path

    if not file_path.exists() or not file_path.is_file():
        return f"Файл не найден: {path}"

    try:
        # Используем IndexEngine для получения содержимого из кэша
        engine = _get_index_engine()
        content = engine.get_file_content(file_path, TODO_DIR)

        # Если файл не в кэше, загружаем его
        if content is None:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Обновляем кэш
            engine.update_file(file_path)

        return f"# {path}\n\n{content}"
    except Exception as e:
        return f"Ошибка чтения файла {path}: {str(e)}"


@app.tool()
async def list_docs(recursive: bool = True) -> str:
    """Получить список всех документов в директории docs/.

    Args:
        recursive: Включать подпапки (по умолчанию true)
    """
    docs = []
    if recursive:
        for root, dirs, files in os.walk(DOCS_DIR):
            for file in files:
                if file.endswith(".md"):
                    rel_path = Path(root) / file
                    rel_path = rel_path.relative_to(DOCS_DIR)
                    docs.append(str(rel_path))
    else:
        for file in DOCS_DIR.glob("*.md"):
            docs.append(file.name)

    if not docs:
        return "Документы не найдены."

    text = f"Найдено {len(docs)} документов:\n\n"
    for doc in sorted(docs):
        text += f"- {doc}\n"

    return text


@app.tool()
async def list_todo(recursive: bool = True) -> str:
    """Получить список всех документов в директории todo/.

    Args:
        recursive: Включать подпапки (по умолчанию true)
    """
    docs = []
    if recursive:
        for root, dirs, files in os.walk(TODO_DIR):
            for file in files:
                if file.endswith(".md"):
                    rel_path = Path(root) / file
                    rel_path = rel_path.relative_to(TODO_DIR)
                    docs.append(str(rel_path))
    else:
        for file in TODO_DIR.glob("*.md"):
            docs.append(file.name)

    if not docs:
        return "Документы не найдены."

    text = f"Найдено {len(docs)} документов:\n\n"
    for doc in sorted(docs):
        text += f"- {doc}\n"

    return text


@app.tool()
async def get_code_index() -> str:
    """Получить индекс всего кода проекта из plans/master_code_index.md.

    Returns:
        Содержимое master_code_index.md или сообщение об ошибке
    """
    index_file = PLANS_DIR / "master_code_index.md"

    if not index_file.exists():
        return "Индекс кода не найден. Запустите Index_code.py для генерации."

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()
        return (
            content[:5000]
            + "\n\n[... файл обрезан для показа, используйте get_code_index_full для полной версии ...]"
        )
    except Exception as e:
        return f"Ошибка чтения индекса кода: {str(e)}"


@app.tool()
async def search_code(query: str, limit: int = 10) -> str:
    """Семантический поиск по коду проекта (ищет в .py файлах).

    Args:
        query: Ключевые слова для поиска
        limit: Максимальное количество результатов (по умолчанию 10)

    Returns:
        Строка с результатами поиска
    """
    query_lower = query.lower()
    results = []

    for root, dirs, files in os.walk(SRC_DIR):
        # Пропускаем тесты и __pycache__
        if "test" in root or "__pycache__" in root:
            continue

        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(SRC_DIR)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if query_lower in content.lower():
                        # Найти контекст вокруг найденного текста
                        lines = content.split("\n")
                        context_lines = []
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                start = max(0, i - 3)
                                end = min(len(lines), i + 4)
                                context_lines.extend(lines[start:end])
                                break

                        context = "\n".join(context_lines[:7])

                        results.append({"path": str(rel_path), "context": context})

                        if len(results) >= limit:
                            break
                except Exception:
                    continue

        if len(results) >= limit:
            break

    if not results:
        return f"По запросу '{query}' ничего не найдено в коде."

    text = f"Найдено {len(results)} результатов по запросу '{query}' в коде:\n\n"
    for result in results:
        text += (
            f"**src/{result['path']}**\n```python\n{result['context']}\n```\n\n---\n\n"
        )

    return text


@app.tool()
async def get_code_file(path: str) -> str:
    """Получить содержимое файла исходного кода.

    Args:
        path: Относительный путь к файлу от src/ (например, "runtime/loop.py")

    Returns:
        Содержимое файла или сообщение об ошибке
    """
    file_path = SRC_DIR / path

    if not file_path.exists() or not file_path.is_file():
        return f"Файл не найден: src/{path}"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"# src/{path}\n\n```python\n{content}\n```"
    except Exception as e:
        return f"Ошибка чтения файла src/{path}: {str(e)}"


@app.tool()
async def get_test_coverage() -> str:
    """Получить информацию о покрытии тестами из htmlcov/status.json.

    Returns:
        Информация о покрытии или сообщение о том, что нужно запустить pytest с --cov
    """
    status_file = Path(__file__).parent / "htmlcov" / "status.json"

    if not status_file.exists():
        return "Файл status.json не найден. Запустите 'pytest --cov=src --cov-report=html' для генерации отчета о покрытии."

    try:
        import json

        with open(status_file, "r", encoding="utf-8") as f:
            status = json.load(f)

        status.get("format-version", "N/A")
        summary = status.get("totals", {})
        percent_covered = summary.get("percent_covered", "N/A")
        num_statements = summary.get("num_statements", "N/A")
        missing = summary.get("missing_lines", "N/A")

        return f"""Информация о покрытии тестами:

- **Процент покрытия:** {percent_covered}%
- **Всего строк:** {num_statements}
- **Непокрытых строк:** {missing}

Для детальной информации откройте htmlcov/index.html в браузере.
"""
    except Exception as e:
        return f"Ошибка чтения файла покрытия: {str(e)}"


@app.tool()
async def list_snapshots() -> str:
    """Получить список доступных snapshots из data/snapshots/.

    Returns:
        Список snapshots или сообщение, если их нет
    """
    snapshots_dir = DATA_DIR / "snapshots"

    if not snapshots_dir.exists():
        return "Директория data/snapshots не найдена."

    snapshots = []
    for file in sorted(snapshots_dir.glob("*.json")):
        snapshots.append(file.name)

    if not snapshots:
        return "Snapshots не найдены. Система еще не сохраняла состояния."

    return (
        f"Найдено {len(snapshots)} snapshots:\n\n"
        + "\n".join(f"- {s}" for s in snapshots[-20:])
        + (
            f"\n\n... и еще {len(snapshots) - 20} snapshots"
            if len(snapshots) > 20
            else ""
        )
    )


@app.tool()
async def get_snapshot(filename: str) -> str:
    """Получить содержимое конкретного snapshot.

    Args:
        filename: Имя файла snapshot (например, "snapshot_000123.json")

    Returns:
        Содержимое snapshot или сообщение об ошибке
    """
    snapshot_file = DATA_DIR / "snapshots" / filename

    if not snapshot_file.exists():
        return f"Snapshot не найден: {filename}"

    try:
        import json

        with open(snapshot_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Форматируем JSON для читаемости
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        return f"# Snapshot: {filename}\n\n```json\n{formatted}\n```"
    except Exception as e:
        return f"Ошибка чтения snapshot {filename}: {str(e)}"


@app.tool()
async def refresh_index() -> str:
    """Обновить индекс документации и TODO файлов.

    Выполняет полную переиндексацию всех директорий (docs/, todo/).
    Полезно использовать после массового изменения файлов или если индекс устарел.

    **Потокобезопасность:** Операция защищена блокировкой для предотвращения одновременного
    доступа. Если переиндексация уже выполняется, последующие вызовы будут ждать завершения.

    Returns:
        Сообщение о статусе обновления индекса с информацией о времени выполнения и статистике.

    Examples:
        >>> import asyncio
        >>> from mcp_index import refresh_index
        >>> result = asyncio.run(refresh_index())
        >>> print(result)
        Индекс успешно обновлен.
        
        - Проиндексировано файлов: 150
        - Уникальных токенов в индексе: 5234
        - Время выполнения: 2.34 сек.

    Raises:
        RuntimeError: При критических ошибках инициализации движка индексации
        ValueError: При ошибках валидации данных
        OSError: При ошибках доступа к файловой системе
    """
    start_time = time.time()
    
    # Используем блокировку для защиты от одновременного доступа
    # Это предотвращает race conditions при параллельных вызовах
    if not _reindex_lock.acquire(blocking=False):
        # Если блокировка уже занята, значит переиндексация уже выполняется
        logger.warning("Попытка запустить переиндексацию, когда она уже выполняется")
        return (
            "Переиндексация уже выполняется. Пожалуйста, подождите завершения "
            "текущей операции перед повторным вызовом."
        )
    
    try:
        logger.info("Начало переиндексации")
        
        # Инициализация движка
        try:
            engine = _get_index_engine()
        except Exception as e:
            logger.error(f"Ошибка инициализации IndexEngine: {type(e).__name__}: {e}", exc_info=True)
            raise RuntimeError(f"Не удалось инициализировать движок индексации: {str(e)}") from e
        
        # Выполнение переиндексации
        try:
            engine.reindex()
            logger.info("Переиндексация завершена успешно")
        except Exception as e:
            logger.error(f"Ошибка при выполнении переиндексации: {type(e).__name__}: {e}", exc_info=True)
            raise RuntimeError(f"Ошибка при переиндексации: {str(e)}") from e

        # Подсчитываем статистику
        try:
            cache_size = len(engine.content_cache)
            index_size = len(engine.inverted_index)
        except Exception as e:
            logger.error(f"Ошибка при подсчете статистики: {type(e).__name__}: {e}", exc_info=True)
            raise ValueError(f"Ошибка при подсчете статистики: {str(e)}") from e

        # Валидация статистики
        warnings = []
        
        if cache_size == 0:
            warnings.append("⚠️ Предупреждение: не проиндексировано ни одного файла. Возможно, директории docs/ и todo/ пусты.")
            logger.warning("Статистика: cache_size == 0")
        
        if index_size == 0:
            warnings.append("⚠️ Предупреждение: индекс не содержит токенов. Возможно, файлы пусты или не содержат текста.")
            logger.warning("Статистика: index_size == 0")
        
        # Проверка на подозрительно большие значения
        if cache_size > 100000:
            warnings.append(f"⚠️ Предупреждение: очень большое количество проиндексированных файлов ({cache_size}). Возможна ошибка.")
            logger.warning(f"Статистика: подозрительно большое cache_size: {cache_size}")
        
        # Вычисляем время выполнения
        elapsed_time = time.time() - start_time
        
        # Формируем результат
        result = (
            f"Индекс успешно обновлен.\n\n"
            f"- Проиндексировано файлов: {cache_size}\n"
            f"- Уникальных токенов в индексе: {index_size}\n"
            f"- Время выполнения: {elapsed_time:.2f} сек."
        )
        
        if warnings:
            result += "\n\n" + "\n".join(warnings)
        
        logger.info(f"Переиндексация завершена: {cache_size} файлов, {index_size} токенов, {elapsed_time:.2f} сек.")
        
        return result
        
    except (RuntimeError, ValueError) as e:
        # Специфичные ошибки - логируем и возвращаем понятное сообщение
        elapsed_time = time.time() - start_time
        error_msg = f"Ошибка при обновлении индекса: {str(e)}\nВремя до ошибки: {elapsed_time:.2f} сек."
        logger.error(error_msg)
        return error_msg
        
    except OSError as e:
        # Ошибки файловой системы
        elapsed_time = time.time() - start_time
        error_msg = f"Ошибка доступа к файловой системе при обновлении индекса: {str(e)}\nВремя до ошибки: {elapsed_time:.2f} сек."
        logger.error(error_msg, exc_info=True)
        return error_msg
        
    except Exception as e:
        # Неожиданные ошибки - логируем с полной информацией
        elapsed_time = time.time() - start_time
        error_msg = f"Неожиданная ошибка при обновлении индекса: {type(e).__name__}: {str(e)}\nВремя до ошибки: {elapsed_time:.2f} сек."
        logger.error(error_msg, exc_info=True)
        return error_msg
        
    finally:
        # Всегда освобождаем блокировку
        _reindex_lock.release()
        logger.debug("Блокировка переиндексации освобождена")


if __name__ == "__main__":
    # FastMCP сервер запускается через stdio для MCP протокола
    # Не запускайте его напрямую - он должен запускаться через Cursor MCP конфигурацию
    # Для тестирования используйте Cursor UI или MCP клиент
    try:
        app.run()
    except Exception as e:
        print(
            "Примечание: MCP сервер предназначен для запуска через Cursor MCP конфигурацию."
        )
        print("Для тестирования настройте MCP сервер в Cursor Settings.")
        print(f"Ошибка (ожидаема при прямом запуске): {e}")

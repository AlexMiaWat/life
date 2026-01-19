#!/usr/bin/env python3
"""
MCP Server для документации проекта Life.
Предоставляет доступ к документации через инструменты и ресурсы MCP.
Использует FastMCP для упрощения.
"""

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

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


@app.tool()
async def search_docs(query: str, limit: int = 10) -> str:
    """Поиск по ключевым словам в документации проекта Life.

    Args:
        query: Ключевые слова для поиска
        limit: Максимальное количество результатов (по умолчанию 10)
    """
    query_lower = query.lower()
    results = []

    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(DOCS_DIR)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if query_lower in content.lower():
                        # Найти контекст вокруг найденного текста
                        lines = content.split("\n")
                        context_lines = []
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context_lines.extend(lines[start:end])
                                break

                        context = "\n".join(context_lines[:5])  # Ограничить контекст

                        results.append(
                            {"path": str(rel_path), "title": file, "context": context}
                        )

                        if len(results) >= limit:
                            break
                except Exception:
                    continue

        if len(results) >= limit:
            break

    if not results:
        return f"По запросу '{query}' ничего не найдено."

    text = f"Найдено {len(results)} результатов по запросу '{query}':\n\n"
    for result in results:
        text += f"**{result['path']}**\n{result['context']}\n\n---\n\n"

    return text


@app.tool()
async def search_todo(query: str, limit: int = 10) -> str:
    """Поиск по ключевым словам в документации TODO проекта Life.

    Args:
        query: Ключевые слова для поиска
        limit: Максимальное количество результатов (по умолчанию 10)
    """
    query_lower = query.lower()
    results = []

    for root, dirs, files in os.walk(TODO_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(TODO_DIR)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if query_lower in content.lower():
                        # Найти контекст вокруг найденного текста
                        lines = content.split("\n")
                        context_lines = []
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context_lines.extend(lines[start:end])
                                break

                        context = "\n".join(context_lines[:5])  # Ограничить контекст

                        results.append(
                            {"path": str(rel_path), "title": file, "context": context}
                        )

                        if len(results) >= limit:
                            break
                except Exception:
                    continue

        if len(results) >= limit:
            break

    if not results:
        return f"По запросу '{query}' ничего не найдено."

    text = f"Найдено {len(results)} результатов по запросу '{query}':\n\n"
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
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

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
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

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

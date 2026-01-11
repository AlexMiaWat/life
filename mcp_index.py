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
            if file.endswith('.md'):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(DOCS_DIR)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if query_lower in content.lower():
                        # Найти контекст вокруг найденного текста
                        lines = content.split('\n')
                        context_lines = []
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context_lines.extend(lines[start:end])
                                break

                        context = '\n'.join(context_lines[:5])  # Ограничить контекст

                        results.append({
                            'path': str(rel_path),
                            'title': file,
                            'context': context
                        })

                        if len(results) >= limit:
                            break
                except Exception as e:
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
            if file.endswith('.md'):
                file_path = Path(root) / file
                rel_path = file_path.relative_to(TODO_DIR)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if query_lower in content.lower():
                        # Найти контекст вокруг найденного текста
                        lines = content.split('\n')
                        context_lines = []
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context_lines.extend(lines[start:end])
                                break

                        context = '\n'.join(context_lines[:5])  # Ограничить контекст

                        results.append({
                            'path': str(rel_path),
                            'title': file,
                            'context': context
                        })

                        if len(results) >= limit:
                            break
                except Exception as e:
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
        with open(file_path, 'r', encoding='utf-8') as f:
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
        with open(file_path, 'r', encoding='utf-8') as f:
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
                if file.endswith('.md'):
                    rel_path = Path(root) / file
                    rel_path = rel_path.relative_to(DOCS_DIR)
                    docs.append(str(rel_path))
    else:
        for file in DOCS_DIR.glob('*.md'):
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
                if file.endswith('.md'):
                    rel_path = Path(root) / file
                    rel_path = rel_path.relative_to(TODO_DIR)
                    docs.append(str(rel_path))
    else:
        for file in TODO_DIR.glob('*.md'):
            docs.append(file.name)

    if not docs:
        return "Документы не найдены."

    text = f"Найдено {len(docs)} документов:\n\n"
    for doc in sorted(docs):
        text += f"- {doc}\n"

    return text

if __name__ == "__main__":
    app.run()
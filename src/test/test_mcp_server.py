#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы MCP сервера life-docs
"""

import asyncio
import sys
from pathlib import Path

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent))

# Импортируем функции из mcp_index
from mcp_index import search_docs, search_todo, get_doc_content, get_todo_content, list_docs, list_todo

async def test_search_docs():
    """Тест поиска в документации"""
    print("\n=== Тест: search_docs ===")
    result = await search_docs("api", limit=3)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert "api" in result.lower() or "API" in result or "Найдено" in result
    print("[OK] search_docs работает корректно")

async def test_list_docs():
    """Тест списка документов"""
    print("\n=== Тест: list_docs ===")
    result = await list_docs(recursive=True)
    print(f"Результат (первые 300 символов):\n{result[:300]}...")
    assert "Найдено" in result or "документов" in result.lower()
    print("[OK] list_docs работает корректно")

async def test_get_doc_content():
    """Тест получения содержимого документа"""
    print("\n=== Тест: get_doc_content ===")
    # Попробуем получить существующий документ
    result = await get_doc_content("README.md")
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert "README.md" in result or "Файл не найден" not in result
    print("[OK] get_doc_content работает корректно")

async def test_search_todo():
    """Тест поиска в TODO"""
    print("\n=== Тест: search_todo ===")
    result = await search_todo("TODO", limit=2)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert "TODO" in result.upper() or "Найдено" in result or "ничего не найдено" in result.lower()
    print("[OK] search_todo работает корректно")

async def test_list_todo():
    """Тест списка TODO документов"""
    print("\n=== Тест: list_todo ===")
    result = await list_todo(recursive=True)
    print(f"Результат:\n{result}")
    assert "Найдено" in result or "документов" in result.lower()
    print("[OK] list_todo работает корректно")

async def test_get_todo_content():
    """Тест получения содержимого TODO документа"""
    print("\n=== Тест: get_todo_content ===")
    result = await get_todo_content("CURRENT.md")
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert "CURRENT.md" in result or "Файл не найден" not in result
    print("[OK] get_todo_content работает корректно")

async def test_mcp_server_init():
    """Тест инициализации MCP сервера"""
    print("\n=== Тест: Инициализация MCP сервера ===")
    from mcp_index import app, DOCS_DIR, TODO_DIR
    
    print(f"DOCS_DIR: {DOCS_DIR}")
    print(f"TODO_DIR: {TODO_DIR}")
    print(f"DOCS_DIR exists: {DOCS_DIR.exists()}")
    print(f"TODO_DIR exists: {TODO_DIR.exists()}")
    print(f"App name: {app}")
    
    assert DOCS_DIR.exists()
    assert TODO_DIR.exists()
    print("[OK] MCP сервер инициализирован корректно")

async def main():
    """Запуск всех тестов"""
    print("=" * 60)
    print("Тестирование MCP сервера life-docs")
    print("=" * 60)
    
    try:
        await test_mcp_server_init()
        await test_list_docs()
        await test_search_docs()
        await test_get_doc_content()
        await test_list_todo()
        await test_search_todo()
        await test_get_todo_content()
        
        print("\n" + "=" * 60)
        print("[OK] Все тесты пройдены успешно!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n[ERROR] Ошибка при тестировании: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

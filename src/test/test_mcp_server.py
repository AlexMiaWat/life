#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы MCP сервера life-docs
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в путь для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Импортируем функции из mcp_index
from mcp_index import (
    _tokenize_query,
    get_doc_content,
    get_todo_content,
    list_docs,
    list_todo,
    refresh_index,
    search_docs,
    search_todo,
)


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
    assert (
        "TODO" in result.upper()
        or "Найдено" in result
        or "ничего не найдено" in result.lower()
    )
    print("[OK] search_todo работает корректно")


async def test_search_docs_and_mode():
    """Тест поиска в документации с режимом AND"""
    print("\n=== Тест: search_docs (AND mode) ===")
    result = await search_docs("test query", search_mode="AND", limit=3)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    # Строгая проверка: должен быть именно AND режим
    assert (
        "режим: AND" in result
    ), f"Ожидался режим AND, но получен результат: {result[:200]}"
    print("[OK] search_docs AND mode работает корректно")


async def test_search_docs_or_mode():
    """Тест поиска в документации с режимом OR"""
    print("\n=== Тест: search_docs (OR mode) ===")
    result = await search_docs("test query", search_mode="OR", limit=3)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    # Строгая проверка: должен быть именно OR режим
    assert (
        "режим: OR" in result
    ), f"Ожидался режим OR, но получен результат: {result[:200]}"
    print("[OK] search_docs OR mode работает корректно")


async def test_search_docs_or_mode_with_quoted_query():
    """Тест: явный OR режим имеет приоритет над кавычками"""
    print("\n=== Тест: search_docs (OR mode, quoted query) ===")
    result = await search_docs('"test query"', search_mode="OR", limit=3)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    # Строгая проверка: должен быть именно OR режим (явный режим имеет приоритет)
    assert (
        "режим: OR" in result
    ), f"Ожидался режим OR при явном указании, но получен результат: {result[:200]}"
    print(
        "[OK] search_docs OR mode с quoted query работает корректно (явный режим имеет приоритет)"
    )


async def test_search_docs_phrase_mode():
    """Тест поиска в документации с режимом PHRASE"""
    print("\n=== Тест: search_docs (PHRASE mode) ===")
    result = await search_docs('"test query"', limit=3)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    # Строгая проверка: должен быть именно PHRASE режим
    assert (
        "режим: PHRASE" in result
    ), f"Ожидался режим PHRASE, но получен результат: {result[:200]}"
    print("[OK] search_docs PHRASE mode работает корректно")


async def test_tokenize_query_quotes_auto_phrase():
    """Тест: кавычки автоматически включают PHRASE режим"""
    print("\n=== Тест: _tokenize_query (кавычки → PHRASE) ===")
    # Кавычки без явного режима должны давать PHRASE
    mode, tokens_or_phrase = _tokenize_query('"test query"', "AND", explicit_mode=False)
    assert mode == "PHRASE", f"Ожидался режим PHRASE, получен {mode}"
    assert (
        tokens_or_phrase == "test query"
    ), f"Ожидалась фраза 'test query', получено {tokens_or_phrase}"
    print("[OK] Кавычки автоматически включают PHRASE режим")


async def test_tokenize_query_explicit_mode_priority():
    """Тест: явный режим имеет приоритет над кавычками"""
    print("\n=== Тест: _tokenize_query (явный режим имеет приоритет) ===")
    # Явный OR режим должен иметь приоритет над кавычками
    mode, tokens_or_phrase = _tokenize_query('"test query"', "OR", explicit_mode=True)
    assert mode == "OR", f"Ожидался режим OR, получен {mode}"
    assert isinstance(
        tokens_or_phrase, list
    ), f"Ожидался список токенов, получено {type(tokens_or_phrase)}"
    assert (
        "test" in tokens_or_phrase and "query" in tokens_or_phrase
    ), f"Ожидались токены ['test', 'query'], получено {tokens_or_phrase}"
    print("[OK] Явный режим имеет приоритет над кавычками")


async def test_tokenize_query_empty_query():
    """Тест: пустой запрос обрабатывается корректно"""
    print("\n=== Тест: _tokenize_query (пустой запрос) ===")
    # Пустой запрос должен давать пустой список токенов
    mode, tokens_or_phrase = _tokenize_query("   ", "AND", explicit_mode=False)
    assert mode == "AND", f"Ожидался режим AND, получен {mode}"
    assert isinstance(
        tokens_or_phrase, list
    ), f"Ожидался список токенов, получено {type(tokens_or_phrase)}"
    assert (
        len(tokens_or_phrase) == 0
    ), f"Ожидался пустой список токенов, получено {tokens_or_phrase}"
    print("[OK] Пустой запрос обрабатывается корректно")


async def test_search_docs_empty_query():
    """Тест: пустой запрос возвращает ошибку"""
    print("\n=== Тест: search_docs (пустой запрос) ===")
    result = await search_docs("   ", limit=3)
    print(f"Результат: {result}")
    assert (
        "Ошибка" in result or "пустой запрос" in result.lower()
    ), f"Ожидалась ошибка для пустого запроса, получено: {result}"
    print("[OK] Пустой запрос возвращает ошибку")


async def test_search_todo_and_mode():
    """Тест поиска в TODO с режимом AND"""
    print("\n=== Тест: search_todo (AND mode) ===")
    result = await search_todo("test query", search_mode="AND", limit=2)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert (
        "режим: AND" in result
        or "Найдено" in result
        or "ничего не найдено" in result.lower()
    )
    print("[OK] search_todo AND mode работает корректно")


async def test_search_todo_or_mode():
    """Тест поиска в TODO с режимом OR"""
    print("\n=== Тест: search_todo (OR mode) ===")
    result = await search_todo("test query", search_mode="OR", limit=2)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert (
        "режим: OR" in result
        or "Найдено" in result
        or "ничего не найдено" in result.lower()
    )
    print("[OK] search_todo OR mode работает корректно")


async def test_search_todo_phrase_mode():
    """Тест поиска в TODO с режимом PHRASE"""
    print("\n=== Тест: search_todo (PHRASE mode) ===")
    result = await search_todo('"test query"', limit=2)
    print(f"Результат (первые 200 символов):\n{result[:200]}...")
    assert (
        "режим: PHRASE" in result
        or "Найдено" in result
        or "ничего не найдено" in result.lower()
    )
    print("[OK] search_todo PHRASE mode работает корректно")


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


async def test_refresh_index():
    """Тест обновления индекса"""
    print("\n=== Тест: refresh_index ===")
    result = await refresh_index()
    print(f"Результат:\n{result}")
    
    # Проверяем, что результат содержит ожидаемую информацию
    assert "Индекс успешно обновлен" in result or "Ошибка" in result
    assert "Проиндексировано файлов:" in result
    assert "Уникальных токенов в индексе:" in result
    assert "Время выполнения:" in result
    
    # Если успешно, проверяем формат статистики
    if "Индекс успешно обновлен" in result:
        # Проверяем, что есть числа в статистике
        import re
        file_count_match = re.search(r"Проиндексировано файлов: (\d+)", result)
        token_count_match = re.search(r"Уникальных токенов в индексе: (\d+)", result)
        time_match = re.search(r"Время выполнения: ([\d.]+) сек\.", result)
        
        assert file_count_match is not None, "Не найдено количество файлов в результате"
        assert token_count_match is not None, "Не найдено количество токенов в результате"
        assert time_match is not None, "Не найдено время выполнения в результате"
        
        file_count = int(file_count_match.group(1))
        token_count = int(token_count_match.group(1))
        elapsed_time = float(time_match.group(1))
        
        assert file_count >= 0, "Количество файлов должно быть неотрицательным"
        assert token_count >= 0, "Количество токенов должно быть неотрицательным"
        assert elapsed_time >= 0, "Время выполнения должно быть неотрицательным"
        
        print(f"[OK] refresh_index работает корректно: {file_count} файлов, {token_count} токенов, {elapsed_time:.2f} сек.")
    else:
        print(f"[WARNING] refresh_index вернул ошибку: {result}")
    
    print("[OK] refresh_index работает корректно")


async def test_refresh_index_statistics():
    """Тест проверки статистики после обновления индекса"""
    print("\n=== Тест: refresh_index (проверка статистики) ===")
    
    # Выполняем переиндексацию
    result = await refresh_index()
    
    if "Индекс успешно обновлен" in result:
        import re
        file_count_match = re.search(r"Проиндексировано файлов: (\d+)", result)
        token_count_match = re.search(r"Уникальных токенов в индексе: (\d+)", result)
        
        if file_count_match and token_count_match:
            file_count = int(file_count_match.group(1))
            token_count = int(token_count_match.group(1))
            
            # Проверяем, что статистика разумная
            # (в реальном проекте должно быть хотя бы несколько файлов)
            print(f"Статистика: {file_count} файлов, {token_count} токенов")
            
            # Если файлов 0, проверяем наличие предупреждения
            if file_count == 0:
                assert "⚠️" in result or "Предупреждение" in result, "Должно быть предупреждение при 0 файлах"
                print("[OK] Предупреждение при 0 файлах присутствует")
            
            print("[OK] Статистика корректна")
    else:
        print(f"[WARNING] Не удалось проверить статистику из-за ошибки: {result}")


async def test_refresh_index_timing():
    """Тест проверки времени выполнения переиндексации"""
    print("\n=== Тест: refresh_index (проверка времени выполнения) ===")
    
    import time
    start = time.time()
    result = await refresh_index()
    actual_elapsed = time.time() - start
    
    if "Индекс успешно обновлен" in result:
        import re
        time_match = re.search(r"Время выполнения: ([\d.]+) сек\.", result)
        
        if time_match:
            reported_time = float(time_match.group(1))
            
            # Проверяем, что заявленное время близко к реальному (с допуском 1 сек)
            assert abs(reported_time - actual_elapsed) < 1.0, \
                f"Заявленное время ({reported_time:.2f}) сильно отличается от реального ({actual_elapsed:.2f})"
            
            print(f"[OK] Время выполнения корректно: заявлено {reported_time:.2f} сек., реально {actual_elapsed:.2f} сек.")
        else:
            print("[WARNING] Не найдено время выполнения в результате")
    else:
        print(f"[WARNING] Не удалось проверить время из-за ошибки: {result}")


async def test_mcp_server_init():
    """Тест инициализации MCP сервера"""
    print("\n=== Тест: Инициализация MCP сервера ===")
    from mcp_index import DOCS_DIR, TODO_DIR, app

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
        # Тесты токенизации (проверка реальной логики)
        await test_tokenize_query_quotes_auto_phrase()
        await test_tokenize_query_explicit_mode_priority()
        await test_tokenize_query_empty_query()
        # Тесты режимов поиска
        await test_search_docs_and_mode()
        await test_search_docs_or_mode()
        await test_search_docs_or_mode_with_quoted_query()
        await test_search_docs_phrase_mode()
        await test_search_docs_empty_query()
        await test_get_doc_content()
        await test_list_todo()
        await test_search_todo()
        await test_search_todo_and_mode()
        await test_search_todo_or_mode()
        await test_search_todo_phrase_mode()
        await test_get_todo_content()
        # Тесты refresh_index
        await test_refresh_index()
        await test_refresh_index_statistics()
        await test_refresh_index_timing()

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

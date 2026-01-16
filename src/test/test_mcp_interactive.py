#!/usr/bin/env python3
"""Интерактивная проверка MCP сервера"""

import asyncio

from mcp_index import (
    get_code_index,
    get_test_coverage,
    list_docs,
    list_snapshots,
    search_code,
    search_docs,
    search_todo,
)


async def test_mcp_functions():
    """Тестирование функций MCP сервера"""
    print("=" * 60)
    print("Тестирование MCP сервера проекта Life")
    print("=" * 60)

    # Тест 1: Поиск в документации
    print("\n[1] Тест search_docs('test'):")
    try:
        result = await search_docs("test", 3)
        print(f"   [OK] Найдено {len(result)} символов")
        print(f"   Первые 100 символов: {result[:100]}...")
    except Exception as e:
        print(f"   [ERROR] Ошибка: {e}")

    # Тест 2: Список документов
    print("\n[2] Тест list_docs(False):")
    try:
        result = await list_docs(False)
        print(f"   [OK] {result[:100]}...")
    except Exception as e:
        print(f"   [ERROR] Ошибка: {e}")

    # Тест 3: Поиск в TODO
    print("\n[3] Тест search_todo('CURRENT'):")
    try:
        result = await search_todo("CURRENT", 2)
        print(f"   [OK] Найдено {len(result)} символов")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 4: Получение индекса кода
    print("\n[4] Тест get_code_index():")
    try:
        result = await get_code_index()
        if "Индекс кода" in result or "не найден" in result:
            print(f"   [OK] {result[:150]}...")
        else:
            print(f"   [OK] Индекс загружен ({len(result)} символов)")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 5: Поиск в коде
    print("\n[5] Тест search_code('def test'):")
    try:
        result = await search_code("def test", 2)
        print(f"   [OK] Найдено {len(result)} символов")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 6: Покрытие тестами
    print("\n[6] Тест get_test_coverage():")
    try:
        result = await get_test_coverage()
        print(f"   [OK] {result[:150]}...")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Тест 7: Список snapshots
    print("\n[7] Тест list_snapshots():")
    try:
        result = await list_snapshots()
        print(f"   [OK] {result[:150]}...")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    print("\n" + "=" * 60)
    print("Тестирование завершено!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_functions())

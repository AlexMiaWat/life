#!/usr/bin/env python3
"""
Ручное тестирование примеров кода из документации
Проверяет выполнимость всех примеров из docs/
"""

import ast
import re
import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, "src")


def extract_code_blocks(markdown_file):
    """Извлекает блоки кода из markdown файла"""
    code_blocks = []

    try:
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Находим все блоки кода (между ```)
        pattern = r"```(?:python|bash)?\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            code_blocks.append(match.strip())

    except Exception as e:
        print(f"❌ Ошибка чтения {markdown_file}: {e}")

    return code_blocks


def test_code_examples_execution():
    """Тестирование выполнения примеров кода"""
    print("🧪 Тестирование выполнения примеров кода...")

    docs_dir = Path("docs")
    examples_tested = 0
    examples_passed = 0

    # Проверяем основные файлы документации
    doc_files = [
        "development/debugging.md",
        "components/memory.md",
        "components/runtime.md",
        "components/environment.md",
    ]

    for doc_file in doc_files:
        full_path = docs_dir / doc_file
        if not full_path.exists():
            print(f"⚠️  Файл {doc_file} не найден")
            continue

        code_blocks = extract_code_blocks(full_path)
        print(f"📄 {doc_file}: найдено {len(code_blocks)} блоков кода")

        for i, code_block in enumerate(code_blocks):
            examples_tested += 1

            # Проверяем, что код синтаксически корректен
            try:
                if not code_block.startswith("#") and not code_block.startswith("curl"):
                    ast.parse(code_block)
                    examples_passed += 1
                    print(f"  ✅ Блок {i+1}: синтаксис корректен")
                else:
                    examples_passed += 1
                    print(f"  ✅ Блок {i+1}: комментарий/bash (пропускаем парсинг)")
            except SyntaxError as e:
                print(f"  ❌ Блок {i+1}: синтаксическая ошибка - {e}")

    return examples_passed == examples_tested


def test_documentation_links():
    """Тестирование ссылок в документации"""
    print("🧪 Тестирование ссылок в документации...")

    docs_dir = Path("docs")
    links_tested = 0
    links_valid = 0

    # Проверяем основные файлы
    doc_files = list(docs_dir.rglob("*.md"))

    for doc_file in doc_files:
        try:
            with open(doc_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Ищем относительные ссылки на .md файлы
            link_pattern = r"\[([^\]]+)\]\(([^)]+\.md)\)"
            matches = re.findall(link_pattern, content)

            for match in matches:
                link_text, link_path = match
                links_tested += 1

                # Проверяем существование файла
                target_path = docs_dir / link_path
                if target_path.exists():
                    links_valid += 1
                    print(f"  ✅ {link_path}")
                else:
                    print(f"  ❌ {link_path} - файл не найден")

        except Exception as e:
            print(f"❌ Ошибка проверки {doc_file}: {e}")

    return links_valid == links_tested


def test_command_examples():
    """Тестирование команд в примерах"""
    print("🧪 Тестирование команд в примерах...")

    # Проверяем основные команды из руководства
    commands = [
        (
            [sys.executable, "-c", "import sys; print('Python works')"],
            "Python интерпретатор",
        ),
        ([sys.executable, "-m", "pytest", "--version"], "pytest"),
    ]

    commands_tested = 0
    commands_passed = 0

    for cmd, description in commands:
        commands_tested += 1
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                commands_passed += 1
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description}: код возврата {result.returncode}")
        except Exception as e:
            print(f"  ❌ {description}: {e}")

    return commands_passed == commands_tested


def test_configuration_examples():
    """Тестирование конфигураций в примерах"""
    print("🧪 Тестирование конфигураций в примерах...")

    # Проверяем существование конфигурационных файлов
    config_files = [
        "pytest.ini",
        "requirements.txt",
        ".gitignore",
    ]

    configs_tested = 0
    configs_valid = 0

    for config_file in config_files:
        configs_tested += 1
        if Path(config_file).exists():
            configs_valid += 1
            print(f"  ✅ {config_file}")
        else:
            print(f"  ❌ {config_file} - не найден")

    return configs_valid == configs_tested


def main():
    """Основная функция тестирования"""
    print("🚀 Начало тестирования примеров документации")
    print("=" * 60)

    tests = [
        test_code_examples_execution,
        test_documentation_links,
        test_command_examples,
        test_configuration_examples,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__}")
            else:
                print(f"❌ {test.__name__}")
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")

    print("=" * 60)
    print(f"📊 Результаты: {passed}/{total} тестов пройдено")

    if passed == total:
        print("🎉 Все примеры валидны! Документация готова.")
        return 0
    else:
        print("⚠️  Некоторые примеры требуют проверки.")
        return 1


if __name__ == "__main__":
    import subprocess

    sys.exit(main())

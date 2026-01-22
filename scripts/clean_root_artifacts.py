#!/usr/bin/env python3
"""
Скрипт для очистки корневого каталога проекта от артефактов и временных файлов.

Удаляет:
- export_*.json/csv/jsonl файлы
- benchmark_*.json файлы
- performance_*.json файлы
- test_*.py/md/txt/xml файлы (кроме основных конфигурационных)
- error_report_*.txt файлы
- check_feedback_*.txt файлы
- src.* файлы (структурированные логи)
- __main__ файл

Использование:
    python scripts/clean_root_artifacts.py
"""

import os
import glob
from pathlib import Path


def clean_root_artifacts():
    """Очистить корневой каталог от артефактов."""
    root_dir = Path.cwd()

    # Файлы для удаления
    patterns_to_remove = [
        "export_*.json",
        "export_*.csv",
        "export_*.jsonl",
        "benchmark_*.json",
        "performance_*.json",
        "test_*.py",
        "test_*.md",
        "test_*.txt",
        "test_*.xml",
        "test_results*.xml",
        "test_output*.txt",
        "test_error_report*.md",
        "test_errors*.txt",
        "test_execution*.txt",
        "test_full*.xml",
        "error_report_*.txt",
        "check_feedback_*.txt",
        "src.*",  # Структурированные логи с __name__
        "__main__",
        "codeAgentProjectStatus.md",
    ]

    # Исключения - файлы, которые НЕ нужно удалять
    exclude_files = {
        "conftest.py",  # pytest конфигурация
        "pytest.ini",  # pytest конфигурация
        "test_system_validation.py",  # может быть нужен для ручных проверок
        "sample_snapshot.json",  # пример данных для демонстрации
    }

    removed_files = []

    for pattern in patterns_to_remove:
        for filepath in glob.glob(str(root_dir / pattern)):
            file_path = Path(filepath)
            if file_path.name not in exclude_files:
                try:
                    file_path.unlink()
                    removed_files.append(str(file_path))
                    print(f"Удален: {file_path.name}")
                except Exception as e:
                    print(f"Ошибка удаления {file_path.name}: {e}")

    if removed_files:
        print(f"\nУдалено {len(removed_files)} файлов")
    else:
        print("\nКорневой каталог чистый - ничего не удалено")

    return removed_files


if __name__ == "__main__":
    print("Очистка корневого каталога от артефактов...")
    clean_root_artifacts()
    print("Готово!")
#!/usr/bin/env python3
"""
Скрипт для диагностики проблемы с ArchiveMemory
"""

import sys
from pathlib import Path

# Добавляем src в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.memory.memory import ArchiveMemory


def test_archive_issue():
    """Тестируем создание ArchiveMemory"""
    print("=== Диагностика ArchiveMemory ===")

    # Проверим дефолтный файл
    default_file = Path("data/archive/memory_archive.json")
    print(f"Дефолтный файл существует: {default_file.exists()}")
    if default_file.exists():
        # Создаем ArchiveMemory с load_existing=True для дефолтного файла
        archive_default = ArchiveMemory(load_existing=True)
        print(f"Размер ArchiveMemory с дефолтным файлом: {archive_default.size()}")
        print(f"Файл: {archive_default.archive_file}")

        # Покажем первые записи
        entries = archive_default.get_all_entries()
        if entries:
            print(f"Первая запись: {entries[0]}")
    else:
        print("Дефолтный файл не существует")

    # Создаем ArchiveMemory без параметров (load_existing=False по умолчанию)
    archive_new = ArchiveMemory()
    print(f"Размер нового ArchiveMemory: {archive_new.size()}")
    print(f"Файл: {archive_new.archive_file}")

    # Создаем с явными параметрами
    archive_explicit = ArchiveMemory(load_existing=False, ignore_existing_file=True)
    print(f"Размер ArchiveMemory с явными параметрами: {archive_explicit.size()}")
    print(f"Файл: {archive_explicit.archive_file}")


if __name__ == "__main__":
    test_archive_issue()

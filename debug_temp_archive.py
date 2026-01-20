#!/usr/bin/env python3
"""
Тест для проверки temp_archive fixture
"""

import sys
import tempfile
from pathlib import Path

# Добавляем src в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.memory.memory import ArchiveMemory


def test_temp_archive_like_fixture():
    """Тестируем создание ArchiveMemory как в temp_archive fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Имитируем temp_archive fixture
        archive_file = tmp_path / f"test_archive_{hash(tmp_path)}.json"
        print(f"Archive file: {archive_file}")
        print(f"File exists before creation: {archive_file.exists()}")

        # Убедимся, что файл не существует
        if archive_file.exists():
            archive_file.unlink()

        archive = ArchiveMemory(
            archive_file=archive_file, load_existing=False, ignore_existing_file=True
        )

        print(f"Archive size after creation: {archive.size()}")
        print(f"Archive file path: {archive.archive_file}")
        print(f"File exists after creation: {archive_file.exists()}")

        # Проверим дефолтный файл
        default_file = Path("data/archive/memory_archive.json")
        print(f"Default file exists: {default_file.exists()}")
        if default_file.exists():
            print(f"Default file size: {default_file.stat().st_size}")

        # Создадим ArchiveMemory с дефолтным файлом
        default_archive = ArchiveMemory()
        print(f"Default archive size: {default_archive.size()}")
        print(f"Default archive file: {default_archive.archive_file}")


if __name__ == "__main__":
    test_temp_archive_like_fixture()

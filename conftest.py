"""
Конфигурация pytest для проекта Life
"""

from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_global_archive():
    """Очищает глобальный архивный файл перед всеми тестами"""
    archive_file = Path("data/archive/memory_archive.json")
    if archive_file.exists():
        archive_file.unlink()
    yield
    # После всех тестов тоже можно очистить, но оставим для анализа
    # if archive_file.exists():
    #     archive_file.unlink()

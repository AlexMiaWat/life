"""
Конфигурация pytest для проекта Life
"""

from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_global_state():
    """Очищает глобальные файлы состояния перед всеми тестами"""
    # Очистка архивных файлов
    archive_file = Path("data/archive/memory_archive.json")
    if archive_file.exists():
        archive_file.unlink()

    # Очистка директории snapshots
    snapshots_dir = Path("data/snapshots")
    if snapshots_dir.exists():
        for snapshot_file in snapshots_dir.glob("snapshot_*.json"):
            snapshot_file.unlink()

    # Очистка лог файлов
    log_files = [
        Path("data/tick_log.jsonl"),
        Path("data/state_changes.log"),
        Path("data/structured_log.jsonl"),
    ]
    for log_file in log_files:
        if log_file.exists():
            log_file.unlink()

    # Очистка директории профилей, если есть
    profile_dir = Path("data/profiles")
    if profile_dir.exists():
        for profile_file in profile_dir.glob("*.prof"):
            profile_file.unlink()

    yield
    # После всех тестов оставляем файлы для анализа

"""
Конфигурация pytest для проекта Life
"""

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_global_state():
    """Очищает глобальные файлы состояния перед всеми тестами"""
    # Оптимизированная очистка: очищаем только если переменная окружения установлена
    if os.environ.get("TEST_CLEANUP", "true").lower() == "true":
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


@pytest.fixture(scope="function")
def temp_state():
    """Создает временное состояние для тестов с автоматической очисткой"""
    from src.state.self_state import SelfState

    state = SelfState()
    state.disable_logging()  # Отключаем логирование для тестов

    yield state

    # Очистка после теста
    state.reset_to_defaults()


@pytest.fixture(scope="function")
def mock_event_generator():
    """Создает mock EventGenerator для изоляции тестов"""
    from unittest.mock import MagicMock

    mock_gen = MagicMock()
    mock_gen.generate.return_value = MagicMock(type="test_event", intensity=0.5)

    yield mock_gen

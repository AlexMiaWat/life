"""
Тесты для SnapshotReader
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.runtime.snapshot_reader import SnapshotReader, read_life_status, get_snapshot_reader


class TestSnapshotReader:
    """Тесты SnapshotReader"""

    def test_init(self):
        """Тест инициализации SnapshotReader"""
        reader = SnapshotReader()
        assert reader.cache_ttl_seconds == 1.0
        assert reader._cache is None
        assert reader._cache_timestamp == 0.0
        assert reader._last_snapshot_path is None

    def test_init_custom_ttl(self):
        """Тест инициализации с кастомным TTL"""
        reader = SnapshotReader(cache_ttl_seconds=2.0)
        assert reader.cache_ttl_seconds == 2.0

    def test_invalidate_cache(self):
        """Тест инвалидации кэша"""
        reader = SnapshotReader()
        reader._cache = {"test": "data"}
        reader._cache_timestamp = 123.0
        reader._last_snapshot_path = Path("test.json")

        reader.invalidate_cache()

        assert reader._cache is None
        assert reader._cache_timestamp == 0.0
        assert reader._last_snapshot_path is None

    def test_read_latest_snapshot_no_files(self):
        """Тест чтения при отсутствии snapshot файлов"""
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.read_latest_snapshot()
                assert result is None

    def test_read_latest_snapshot_with_file(self):
        """Тест чтения snapshot из файла"""
        test_data = {
            "ticks": 100,
            "energy": 85.0,
            "integrity": 0.95,
            "stability": 0.9,
            "active": True
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            # Создаем snapshot файл
            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open('w') as f:
                json.dump(test_data, f)

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.read_latest_snapshot()

                assert result is not None
                assert result == test_data
                assert reader._cache == test_data
                assert reader._last_snapshot_path == snapshot_file

    def test_read_latest_snapshot_multiple_files(self):
        """Тест чтения последнего snapshot из нескольких файлов"""
        test_data_1 = {"ticks": 50, "energy": 90.0}
        test_data_2 = {"ticks": 100, "energy": 85.0}

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            # Создаем два snapshot файла
            snapshot_file_1 = snapshot_dir / "snapshot_000050.json"
            snapshot_file_2 = snapshot_dir / "snapshot_000100.json"

            with snapshot_file_1.open('w') as f:
                json.dump(test_data_1, f)
            with snapshot_file_2.open('w') as f:
                json.dump(test_data_2, f)

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.read_latest_snapshot()

                assert result is not None
                assert result == test_data_2  # Должен вернуть последний
                assert reader._last_snapshot_path == snapshot_file_2

    def test_read_latest_snapshot_corrupted_file(self):
        """Тест чтения при поврежденном файле"""
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            # Создаем поврежденный snapshot файл
            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open('w') as f:
                f.write("invalid json content")

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.read_latest_snapshot()
                assert result is None

    def test_get_safe_status_dict_no_snapshot(self):
        """Тест get_safe_status_dict при отсутствии snapshot"""
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.get_safe_status_dict()
                assert result is None

    def test_get_safe_status_dict_basic(self):
        """Тест get_safe_status_dict с базовыми полями"""
        test_data = {
            "ticks": 100,
            "energy": 85.0,
            "integrity": 0.95,
            "stability": 0.9,
            "active": True,
            "age": 150.5,
            "subjective_time": 140.0,
            "life_id": "test-uuid",
            "birth_timestamp": 1234567890.0,
            "_internal_field": "should_be_removed",
            "activated_memory": ["should_be_removed"],
            "last_pattern": "ignore"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open('w') as f:
                json.dump(test_data, f)

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.get_safe_status_dict(include_optional=True)

                assert result is not None
                # Проверяем наличие основных полей
                assert "ticks" in result
                assert "energy" in result
                assert "integrity" in result
                assert "stability" in result
                assert "active" in result

                # Проверяем отсутствие внутренних полей
                assert "_internal_field" not in result
                assert "activated_memory" not in result
                assert "last_pattern" not in result

    def test_get_safe_status_dict_minimal(self):
        """Тест get_safe_status_dict с минимальным набором полей"""
        test_data = {
            "ticks": 100,
            "energy": 85.0,
            "integrity": 0.95,
            "stability": 0.9,
            "active": True,
            "age": 150.5,
            "subjective_time": 140.0,
            "life_id": "test-uuid",  # Опциональное поле
            "learning_params": {"test": "data"}  # Опциональное поле
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open('w') as f:
                json.dump(test_data, f)

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.get_safe_status_dict(include_optional=False)

                assert result is not None
                # Основные поля должны присутствовать
                assert "ticks" in result
                assert "energy" in result

                # Опциональные поля должны отсутствовать
                assert "life_id" not in result
                assert "learning_params" not in result

    def test_get_safe_status_dict_with_limits(self):
        """Тест get_safe_status_dict с лимитами для больших полей"""
        test_data = {
            "ticks": 100,
            "energy": 85.0,
            "integrity": 0.95,
            "stability": 0.9,
            "active": True,
            "memory": [{"id": 1}, {"id": 2}, {"id": 3}],
            "recent_events": ["event1", "event2", "event3"],
            "energy_history": [80.0, 82.0, 85.0, 87.0]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open('w') as f:
                json.dump(test_data, f)

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader()
                result = reader.get_safe_status_dict(
                    include_optional=True,
                    limits={
                        "memory_limit": 2,
                        "events_limit": 2,
                        "energy_history_limit": 3
                    }
                )

                assert result is not None
                # Проверяем ограничения
                assert len(result["memory"]) == 2  # Ограничено 2
                assert len(result["recent_events"]) == 2  # Ограничено 2
                assert len(result["energy_history"]) == 3  # Ограничено 3

    def test_cache_functionality(self):
        """Тест работы кэширования"""
        test_data = {"ticks": 100, "energy": 85.0}

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open('w') as f:
                json.dump(test_data, f)

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader(cache_ttl_seconds=10.0)  # Длинный TTL

                # Первое чтение
                result1 = reader.read_latest_snapshot()
                assert result1 == test_data
                cache_timestamp = reader._cache_timestamp

                # Второе чтение (должно быть из кэша)
                result2 = reader.read_latest_snapshot()
                assert result2 == test_data
                assert reader._cache_timestamp == cache_timestamp  # Время не изменилось

    def test_cache_expiration(self):
        """Тест истечения кэша"""
        test_data = {"ticks": 100, "energy": 85.0}

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open('w') as f:
                json.dump(test_data, f)

            with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
                reader = SnapshotReader(cache_ttl_seconds=0.1)  # Короткий TTL

                # Первое чтение
                result1 = reader.read_latest_snapshot()
                assert result1 == test_data

                # Ждем истечения кэша
                import time
                time.sleep(0.2)

                # Второе чтение (должно перечитать файл)
                result2 = reader.read_latest_snapshot()
                assert result2 == test_data


def test_get_snapshot_reader():
    """Тест получения глобального экземпляра SnapshotReader"""
    reader = get_snapshot_reader()
    assert isinstance(reader, SnapshotReader)
    # Должен возвращать один и тот же экземпляр
    reader2 = get_snapshot_reader()
    assert reader is reader2


def test_read_life_status_no_snapshot():
    """Тест read_life_status при отсутствии snapshot"""
    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_dir = Path(temp_dir) / "snapshots"
        snapshot_dir.mkdir()

        with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
            result = read_life_status()
            assert result is None


def test_read_life_status_with_snapshot():
    """Тест read_life_status с snapshot"""
    test_data = {
        "ticks": 100,
        "energy": 85.0,
        "integrity": 0.95,
        "stability": 0.9,
        "active": True
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_dir = Path(temp_dir) / "snapshots"
        snapshot_dir.mkdir()

        snapshot_file = snapshot_dir / "snapshot_000100.json"
        with snapshot_file.open('w') as f:
            json.dump(test_data, f)

        with patch('src.runtime.snapshot_reader.SNAPSHOT_DIR', snapshot_dir):
            result = read_life_status()
            assert result is not None
            assert "ticks" in result
            assert "energy" in result
            assert result["ticks"] == 100
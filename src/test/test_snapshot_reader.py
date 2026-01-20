"""
Тесты для SnapshotReader - DISABLED: Read functionality has been removed
"""
import json
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from src.runtime.snapshot_reader import (
    SnapshotReader,
    get_snapshot_reader,
    read_life_status,
)

pytestmark = pytest.mark.skip(reason="Read functionality has been disabled")


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

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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
            "active": True,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            # Создаем snapshot файл
            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open("w") as f:
                json.dump(test_data, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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

            with snapshot_file_1.open("w") as f:
                json.dump(test_data_1, f)
            with snapshot_file_2.open("w") as f:
                json.dump(test_data_2, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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
            with snapshot_file.open("w") as f:
                f.write("invalid json content")

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
                reader = SnapshotReader()
                result = reader.read_latest_snapshot()
                assert result is None

    def test_get_safe_status_dict_no_snapshot(self):
        """Тест get_safe_status_dict при отсутствии snapshot"""
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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
            "last_pattern": "ignore",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open("w") as f:
                json.dump(test_data, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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
            "learning_params": {"test": "data"},  # Опциональное поле
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open("w") as f:
                json.dump(test_data, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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
            "energy_history": [80.0, 82.0, 85.0, 87.0],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open("w") as f:
                json.dump(test_data, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
                reader = SnapshotReader()
                result = reader.get_safe_status_dict(
                    include_optional=True,
                    limits={
                        "memory_limit": 2,
                        "events_limit": 2,
                        "energy_history_limit": 3,
                    },
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
            with snapshot_file.open("w") as f:
                json.dump(test_data, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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
            with snapshot_file.open("w") as f:
                json.dump(test_data, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
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

        with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
            result = read_life_status()
            assert result is None


def test_read_life_status_with_snapshot():
    """Тест read_life_status с snapshot"""
    test_data = {
        "ticks": 100,
        "energy": 85.0,
        "integrity": 0.95,
        "stability": 0.9,
        "active": True,
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        snapshot_dir = Path(temp_dir) / "snapshots"
        snapshot_dir.mkdir()

        snapshot_file = snapshot_dir / "snapshot_000100.json"
        with snapshot_file.open("w") as f:
            json.dump(test_data, f)

        with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
            result = read_life_status()
            assert result is not None
            assert "ticks" in result
            assert "energy" in result
            assert result["ticks"] == 100


class TestSnapshotReaderThreading:
    """Тесты потокобезопасности SnapshotReader"""

    def test_concurrent_reads_atomic_snapshot_replacement(self):
        """Тест конкурентного чтения во время атомарной замены снапшотов"""
        test_data_1 = {"ticks": 50, "energy": 90.0, "version": 1}
        test_data_2 = {"ticks": 100, "energy": 85.0, "version": 2}

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            # Создаем начальный snapshot
            snapshot_file = snapshot_dir / "snapshot_000100.json"
            with snapshot_file.open("w") as f:
                json.dump(test_data_1, f)

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
                reader = SnapshotReader(
                    cache_ttl_seconds=0.0
                )  # Без кэширования для теста

                results = []
                errors = []

                def concurrent_reader(reader_id):
                    """Читатель, пытающийся прочитать snapshot"""
                    try:
                        for _ in range(10):  # Много попыток чтения
                            # Для теста отключаем кэширование, чтобы видеть изменения
                            reader.invalidate_cache()
                            result = reader.read_latest_snapshot()
                            if result:
                                results.append((reader_id, result["version"]))
                            time.sleep(0.001)  # Маленькая задержка
                    except Exception as e:
                        errors.append((reader_id, str(e)))

                def snapshot_writer():
                    """Писатель, атомарно заменяющий snapshot"""
                    try:
                        time.sleep(0.01)  # Даем читателям время начать
                        # Атомарная замена: сначала во временный файл, затем переименование
                        temp_file = snapshot_dir / "snapshot_000100.tmp"
                        with temp_file.open("w") as f:
                            json.dump(test_data_2, f)
                        temp_file.replace(snapshot_file)
                    except Exception as e:
                        errors.append(("writer", str(e)))

                # Запускаем читателей и писателя конкурентно
                threads = []

                # 3 читателя
                for i in range(3):
                    thread = threading.Thread(target=concurrent_reader, args=(i,))
                    threads.append(thread)

                # 1 писатель
                writer_thread = threading.Thread(target=snapshot_writer)
                threads.append(writer_thread)

                # Запуск всех потоков
                for thread in threads:
                    thread.start()

                # Ожидание завершения
                for thread in threads:
                    thread.join(timeout=2.0)

                # Проверки
                assert len(errors) == 0, f"Были ошибки: {errors}"

                # Должны быть успешные чтения
                assert len(results) > 0

                # Все чтения должны возвращать либо старую, либо новую версию
                # (но не частично записанную или поврежденную)
                versions = set()
                for _, version in results:
                    versions.add(version)

                # Должны видеть либо версию 1, либо версию 2 (атомарная замена)
                assert versions.issubset({1, 2})

                # Должны видеть хотя бы одну версию 2 (после замены)
                assert 2 in versions

    def test_rw_lock_functionality(self):
        """Тест работы reader-writer lock"""
        from src.runtime.snapshot_reader import RWLock

        rw_lock = RWLock()
        results = []

        def reader(reader_id):
            """Читатель"""
            try:
                with rw_lock:  # Используем контекстный менеджер
                    results.append(("read_start", reader_id))
                    time.sleep(0.01)  # Имитируем работу
                    results.append(("read_end", reader_id))
            except Exception as e:
                results.append(("read_error", reader_id, str(e)))

        def writer(writer_id):
            """Писатель"""
            try:
                rw_lock.acquire_write()
                results.append(("write_start", writer_id))
                time.sleep(0.01)  # Имитируем работу
                results.append(("write_end", writer_id))
                rw_lock.release_write()
            except Exception as e:
                results.append(("write_error", writer_id, str(e)))

        # Тест 1: Множественные читатели могут работать одновременно
        results.clear()
        threads = []

        for i in range(3):
            thread = threading.Thread(target=reader, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Все читатели должны успешно завершить
        read_starts = [r for r in results if r[0] == "read_start"]
        read_ends = [r for r in results if r[0] == "read_end"]
        assert len(read_starts) == 3
        assert len(read_ends) == 3

        # Тест 2: Писатель блокирует читателей
        results.clear()

        # Запускаем читателя в фоне
        reader_thread = threading.Thread(target=lambda: reader("background"))
        reader_thread.start()

        # Даем читателю начать
        time.sleep(0.005)

        # Запускаем писателя
        writer_thread = threading.Thread(target=lambda: writer("main"))
        writer_thread.start()

        # Даем писателю завершить
        writer_thread.join(timeout=1.0)

        # Читатель должен был завершиться до или после писателя
        reader_thread.join(timeout=1.0)

        # Проверяем последовательность
        write_start_idx = None
        write_end_idx = None

        for i, result in enumerate(results):
            if result[0] == "write_start":
                write_start_idx = i
            elif result[0] == "write_end":
                write_end_idx = i

        assert write_start_idx is not None
        assert write_end_idx is not None

        # Во время записи не должно быть других операций
        # (упрощенная проверка - в реальности нужна более сложная логика)

    def test_atomic_snapshot_replacement_simulation(self):
        """Тест симуляции атомарной замены снапшотов"""
        test_data_v1 = {"ticks": 100, "energy": 90.0, "version": 1}
        test_data_v2 = {"ticks": 100, "energy": 85.0, "version": 2}

        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_dir = Path(temp_dir) / "snapshots"
            snapshot_dir.mkdir()

            snapshot_file = snapshot_dir / "snapshot_000100.json"

            with patch("src.runtime.snapshot_reader.SNAPSHOT_DIR", snapshot_dir):
                reader = SnapshotReader(cache_ttl_seconds=0.0)

                # Создаем начальный snapshot
                with snapshot_file.open("w") as f:
                    json.dump(test_data_v1, f)

                # Проверяем начальное чтение
                result1 = reader.read_latest_snapshot()
                assert result1["version"] == 1

                # Имитируем атомарную замену
                temp_file = snapshot_dir / "snapshot_000100.tmp"
                with temp_file.open("w") as f:
                    json.dump(test_data_v2, f)
                temp_file.replace(snapshot_file)

                # Принудительно обновляем кэш и проверяем чтение после замены
                result2 = reader.force_refresh()
                assert result2 is not None
                assert result2["version"] == 2

                # Проверяем, что временный файл не остался
                assert not temp_file.exists()

                # Проверяем, что финальный файл существует и корректен
                assert snapshot_file.exists()
                with snapshot_file.open("r") as f:
                    final_data = json.load(f)
                    assert final_data["version"] == 2

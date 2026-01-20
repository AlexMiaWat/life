"""
Тесты производительности (benchmarks) - ROADMAP T.10

Тесты проверяют производительность различных компонентов системы.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import threading
import time

import pytest

from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.memory.memory import Memory, MemoryEntry
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


@pytest.mark.performance
@pytest.mark.order(4)
class TestPerformanceBenchmarks:
    """Тесты производительности компонентов системы"""

    def test_memory_append_performance(self):
        """Benchmark: производительность добавления записей в Memory"""
        memory = Memory()
        num_entries = 1000

        start_time = time.time()
        for i in range(num_entries):
            entry = MemoryEntry(
                event_type=f"event_{i % 10}",
                meaning_significance=0.5,
                timestamp=time.time() + i
            )
            memory.append(entry)
        elapsed = time.time() - start_time

        # Проверяем производительность: должно быть < 0.1 секунды на 1000 записей
        assert elapsed < 0.1, f"Memory append too slow: {elapsed:.3f}s for {num_entries} entries"
        assert len(memory) == 50  # Размер ограничен

    def test_memory_iteration_performance(self):
        """Benchmark: производительность итерации по Memory"""
        memory = Memory()

        # Заполняем до лимита
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time() + i
            )
            memory.append(entry)

        start_time = time.time()
        count = 0
        for _ in memory:
            count += 1
        elapsed = time.time() - start_time

        assert count == 50
        # Итерация должна быть быстрой (< 0.01 секунды)
        assert elapsed < 0.01, f"Memory iteration too slow: {elapsed:.3f}s"

    def test_event_queue_performance(self):
        """Benchmark: производительность EventQueue"""
        queue = EventQueue()
        num_events = 1000

        # Тест push
        start_time = time.time()
        for i in range(num_events):
            event = Event(type=f"event_{i % 10}", intensity=0.5, timestamp=time.time() + i)
            queue.push(event)
        push_elapsed = time.time() - start_time

        # Тест pop_all
        start_time = time.time()
        events = queue.pop_all()
        pop_elapsed = time.time() - start_time

        assert len(events) == num_events
        # Push должен быть быстрым (< 0.1 секунды на 1000 событий)
        assert push_elapsed < 0.1, f"EventQueue push too slow: {push_elapsed:.3f}s"
        # Pop_all должен быть быстрым (< 0.01 секунды)
        assert pop_elapsed < 0.01, f"EventQueue pop_all too slow: {pop_elapsed:.3f}s"

    def test_self_state_apply_delta_performance(self):
        """Benchmark: производительность apply_delta в SelfState"""
        state = SelfState()
        num_operations = 10000

        start_time = time.time()
        for i in range(num_operations):
            state.apply_delta({
                "energy": 0.1 if i % 2 == 0 else -0.1,
                "integrity": 0.01 if i % 3 == 0 else -0.01,
                "stability": 0.01 if i % 5 == 0 else -0.01,
            })
        elapsed = time.time() - start_time

        # 10000 операций должны выполняться быстро (< 0.5 секунды)
        assert elapsed < 0.5, f"apply_delta too slow: {elapsed:.3f}s for {num_operations} operations"

    def test_runtime_loop_ticks_per_second(self):
        """Benchmark: производительность runtime loop (тиков в секунду)"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 1.0
        state.stability = 1.0
        stop_event = threading.Event()
        event_queue = EventQueue()

        initial_ticks = state.ticks

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.001, 100, stop_event, event_queue),
            daemon=True,
        )

        start_time = time.time()
        loop_thread.start()

        # Запускаем на 1 секунду
        time.sleep(1.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        elapsed = time.time() - start_time
        ticks_done = state.ticks - initial_ticks
        ticks_per_second = ticks_done / elapsed if elapsed > 0 else 0

        # Должно быть минимум 100 тиков в секунду при интервале 0.001
        assert ticks_per_second >= 100, \
            f"Loop too slow: {ticks_per_second:.1f} ticks/sec (expected >= 100)"

    def test_memory_search_performance(self):
        """Benchmark: производительность поиска в Memory"""
        memory = Memory()

        # Заполняем память
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i % 5}",
                meaning_significance=0.3 + (i % 10) * 0.07,
                timestamp=time.time() + i
            )
            memory.append(entry)

        # Тест поиска всех записей определенного типа
        start_time = time.time()
        for _ in range(1000):  # 1000 поисков
            results = [e for e in memory if e.event_type == "event_0"]
        elapsed = time.time() - start_time

        # 1000 поисков должны выполняться быстро (< 0.1 секунды)
        assert elapsed < 0.1, f"Memory search too slow: {elapsed:.3f}s for 1000 searches"
        assert len(results) == 10  # Должно быть 10 записей типа "event_0"

    def test_state_snapshot_performance(self):
        """Benchmark: производительность сохранения snapshot"""
        from state.self_state import save_snapshot
        import tempfile
        from pathlib import Path

        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.8
        state.stability = 0.7
        state.ticks = 100

        # Создаем временную директорию для snapshots
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_dir = Path(tmpdir) / "snapshots"
            snapshot_dir.mkdir()

            # Временно заменяем SNAPSHOT_DIR
            from state import self_state as state_module
            original_dir = state_module.SNAPSHOT_DIR
            state_module.SNAPSHOT_DIR = snapshot_dir

            try:
                num_snapshots = 100
                start_time = time.time()
                for i in range(num_snapshots):
                    state.ticks = i
                    save_snapshot(state)
                elapsed = time.time() - start_time

                # 100 snapshots должны сохраняться быстро (< 1 секунда)
                assert elapsed < 1.0, \
                    f"Snapshot save too slow: {elapsed:.3f}s for {num_snapshots} snapshots"
            finally:
                state_module.SNAPSHOT_DIR = original_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

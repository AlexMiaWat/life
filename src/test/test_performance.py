"""
Тесты производительности (benchmarks) - ROADMAP T.10

Тесты проверяют производительность различных компонентов системы.
Включают проверку на регрессии с использованием baseline значений.
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
from src.test.performance_baseline import (
    performance_baseline,
    update_baseline_if_needed,
)


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
                timestamp=time.time() + i,
            )
            memory.append(entry)
        elapsed = time.time() - start_time

        # Обновляем baseline если нужно
        update_baseline_if_needed("test_memory_append_performance", {"elapsed": elapsed})

        # Проверяем на регрессию
        regression_check = performance_baseline.check_regression(
            "test_memory_append_performance", "elapsed", elapsed, threshold_percent=15.0
        )

        # Логируем результат
        print(regression_check["message"])

        # Проверяем производительность: должно быть < 0.1 секунды на 1000 записей
        assert elapsed < 0.1, f"Memory append too slow: {elapsed:.3f}s for {num_entries} entries"

        # Проверяем на регрессию
        assert not regression_check["is_regression"], regression_check["message"]

        assert len(memory) == 50  # Размер ограничен

    def test_memory_iteration_performance(self):
        """Benchmark: производительность итерации по Memory"""
        memory = Memory()

        # Заполняем до лимита
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i}",
                meaning_significance=0.5,
                timestamp=time.time() + i,
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
        # Увеличиваем размер очереди для performance теста
        import queue as queue_module

        queue._queue = queue_module.Queue(maxsize=2000)
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

        # Обновляем baseline
        update_baseline_if_needed(
            "test_event_queue_performance",
            {"push_elapsed": push_elapsed, "pop_elapsed": pop_elapsed},
        )

        # Проверяем на регрессии
        push_regression = performance_baseline.check_regression(
            "test_event_queue_performance",
            "push_elapsed",
            push_elapsed,
            threshold_percent=25.0,
        )
        pop_regression = performance_baseline.check_regression(
            "test_event_queue_performance",
            "pop_elapsed",
            pop_elapsed,
            threshold_percent=15.0,
        )

        # Логируем результаты
        print(push_regression["message"])
        print(pop_regression["message"])

        assert len(events) == num_events
        # Push должен быть быстрым (< 0.1 секунды на 1000 событий)
        assert push_elapsed < 0.1, f"EventQueue push too slow: {push_elapsed:.3f}s"
        # Pop_all должен быть быстрым (< 0.01 секунды)
        assert pop_elapsed < 0.01, f"EventQueue pop_all too slow: {pop_elapsed:.3f}s"

        # Проверяем на регрессии
        assert not push_regression["is_regression"], push_regression["message"]
        assert not pop_regression["is_regression"], pop_regression["message"]

    def test_self_state_apply_delta_performance(self):
        """Benchmark: производительность apply_delta в SelfState"""
        state = SelfState()
        # Отключаем логирование для performance теста
        state.disable_logging()
        num_operations = 10000

        start_time = time.time()
        for i in range(num_operations):
            state.apply_delta(
                {
                    "energy": 0.1 if i % 2 == 0 else -0.1,
                    "integrity": 0.01 if i % 3 == 0 else -0.01,
                    "stability": 0.01 if i % 5 == 0 else -0.01,
                }
            )
        elapsed = time.time() - start_time

        # 10000 операций должны выполняться быстро (< 0.5 секунды)
        assert (
            elapsed < 0.5
        ), f"apply_delta too slow: {elapsed:.3f}s for {num_operations} operations"

    def test_runtime_loop_ticks_per_second(self):
        """Benchmark: производительность runtime loop (тиков в секунду)"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 1.0
        state.stability = 1.0
        # Отключаем логирование для производительности
        state.disable_logging()
        stop_event = threading.Event()
        event_queue = EventQueue()

        initial_ticks = state.ticks

        loop_thread = threading.Thread(
            target=run_loop,
            args=(
                state,
                dummy_monitor,
                0.009,
                100,
                stop_event,
                event_queue,
                False,
                True,
                True,
                True,
                100,
            ),
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

        # Обновляем baseline
        update_baseline_if_needed(
            "test_runtime_loop_ticks_per_second", {"ticks_per_second": ticks_per_second}
        )

        # Проверяем на регрессию
        regression_check = performance_baseline.check_regression(
            "test_runtime_loop_ticks_per_second",
            "ticks_per_second",
            ticks_per_second,
            threshold_percent=10.0,
        )

        # Логируем результат
        print(regression_check["message"])

        # Должно быть минимум 100 тиков в секунду при интервале 0.01
        assert (
            ticks_per_second >= 100
        ), f"Loop too slow: {ticks_per_second:.1f} ticks/sec (expected >= 100)"

        # Проверяем на регрессию
        assert not regression_check["is_regression"], regression_check["message"]

    def test_memory_search_performance(self):
        """Benchmark: производительность поиска в Memory"""
        memory = Memory()

        # Заполняем память
        for i in range(50):
            entry = MemoryEntry(
                event_type=f"event_{i % 5}",
                meaning_significance=0.3 + (i % 10) * 0.07,
                timestamp=time.time() + i,
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
        import tempfile
        from pathlib import Path

        from state.self_state import save_snapshot

        state = SelfState()
        # Отключаем логирование для performance теста
        state.disable_logging()
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
                assert (
                    elapsed < 1.0
                ), f"Snapshot save too slow: {elapsed:.3f}s for {num_snapshots} snapshots"
            finally:
                state_module.SNAPSHOT_DIR = original_dir

    def test_learning_engine_performance_with_large_memory(self):
        """Benchmark: производительность Learning Engine с большой памятью (1000+ записей)"""
        from src.learning.learning import LearningEngine

        learning_engine = LearningEngine()
        memory = Memory()

        # Создаем 1000 записей памяти с различными типами событий
        num_entries = 1000
        for i in range(num_entries):
            # Для feedback записей добавляем feedback_data
            feedback_data = None
            if i % 3 == 0:  # Каждая третья запись - feedback
                feedback_data = {
                    "action_pattern": f"pattern_{(i % 5)}",
                    "state_delta": {
                        "energy": (i % 3 - 1) * 2.0,
                        "stability": (i % 4 - 2) * 0.1,
                    },
                }

            entry = MemoryEntry(
                event_type=f"event_{i % 10}",  # 10 разных типов событий
                meaning_significance=0.1 + (i % 9) * 0.1,  # Различная значимость
                timestamp=time.time() + i,
                feedback_data=feedback_data,
            )
            memory.append(entry)

        # Тест производительности process_statistics
        start_time = time.time()
        statistics = learning_engine.process_statistics(list(memory))
        process_elapsed = time.time() - start_time

        # Тест производительности adjust_parameters
        current_params = {
            "event_type_sensitivity": {"event_0": 0.5, "event_1": 0.3},
            "significance_thresholds": {"event_0": 0.2, "event_1": 0.1},
            "response_coefficients": {"dampen": 0.5, "absorb": 1.0},
        }

        start_time = time.time()
        new_params = learning_engine.adjust_parameters(statistics, current_params)
        adjust_elapsed = time.time() - start_time

        # Проверки производительности
        assert (
            process_elapsed < 0.5
        ), f"Learning process_statistics too slow: {process_elapsed:.3f}s for {num_entries} entries"
        assert adjust_elapsed < 0.1, f"Learning adjust_parameters too slow: {adjust_elapsed:.3f}s"
        assert new_params is not None
        assert statistics["total_entries"] == min(num_entries, 50)  # Memory ограничена 50 записями

    def test_adaptation_manager_performance_with_frequent_calls(self):
        """Benchmark: производительность Adaptation Manager при частых вызовах"""
        from src.adaptation.adaptation import AdaptationManager

        adaptation_manager = AdaptationManager()

        # Создаем тестовые данные
        learning_params = {
            "event_type_sensitivity": {"event_0": 0.5, "event_1": 0.3},
            "significance_thresholds": {"event_0": 0.2, "event_1": 0.1},
            "response_coefficients": {"dampen": 0.5, "absorb": 1.0},
        }

        adaptation_history = [
            {
                "learning_params_snapshot": learning_params,
                "timestamp": time.time() - i,
            }
            for i in range(10)
        ]

        current_behavior_params = {
            "behavior_sensitivity": {"event_0": 0.4, "event_1": 0.2},
            "behavior_thresholds": {"event_0": 0.15, "event_1": 0.05},
            "behavior_coefficients": {"dampen": 0.4, "absorb": 0.9},
        }

        # Тест производительности analyze_changes
        num_iterations = 1000
        start_time = time.time()
        for _ in range(num_iterations):
            analysis = adaptation_manager.analyze_changes(learning_params, adaptation_history)
        analyze_elapsed = time.time() - start_time

        # Тест производительности apply_adaptation
        start_time = time.time()
        for _ in range(num_iterations):
            _ = adaptation_manager.apply_adaptation(analysis, current_behavior_params, None)
        apply_elapsed = time.time() - start_time

        # Проверки производительности
        analyze_time_per_call = analyze_elapsed / num_iterations
        apply_time_per_call = apply_elapsed / num_iterations

        assert (
            analyze_time_per_call < 0.001
        ), f"Adaptation analyze_changes too slow: {analyze_time_per_call:.6f}s per call"
        assert (
            apply_time_per_call < 0.001
        ), f"Adaptation apply_adaptation too slow: {apply_time_per_call:.6f}s per call"

    def test_meaning_engine_performance_with_many_events(self):
        """Benchmark: производительность Meaning Engine при обработке множества событий"""
        from src.meaning.engine import MeaningEngine

        meaning_engine = MeaningEngine()
        state = SelfState()

        # Создаем тестовые события разных типов
        events = []
        event_types = ["noise", "decay", "recovery", "shock", "idle"]
        num_events = 1000

        for i in range(num_events):
            event = Event(
                type=event_types[i % len(event_types)],
                intensity=0.1 + (i % 10) * 0.09,  # intensity от 0.1 до 1.0
                timestamp=time.time() + i,
            )
            events.append(event)

        # Тест производительности обработки событий
        start_time = time.time()
        meanings = []
        for event in events:
            meaning = meaning_engine.process(
                event,
                {
                    "energy": state.energy,
                    "integrity": state.integrity,
                    "stability": state.stability,
                    "learning_params": state.learning_params,
                    "adaptation_params": state.adaptation_params,
                },
            )
            meanings.append(meaning)
        elapsed = time.time() - start_time

        # Проверки производительности и корректности
        assert elapsed < 2.0, f"Meaning Engine too slow: {elapsed:.3f}s for {num_events} events"
        assert len(meanings) == num_events
        assert all(
            meaning.significance >= 0.0 and meaning.significance <= 1.0 for meaning in meanings
        )
        assert all(isinstance(meaning.impact, dict) for meaning in meanings)

    def test_runtime_loop_performance_with_learning_adaptation(self):
        """Benchmark: производительность runtime loop с активными Learning/Adaptation"""
        state = SelfState()
        state.energy = 80.0
        state.integrity = 0.9
        state.stability = 0.8

        # Заполняем память событиями для Learning
        for i in range(30):  # Близко к лимиту памяти
            feedback_data = None
            if i % 2 == 0:  # Каждая вторая запись - feedback
                feedback_data = {
                    "action_pattern": f"pattern_{i % 3}",
                    "state_delta": {
                        "energy": (i % 5 - 2) * 5.0,
                        "stability": (i % 3 - 1) * 0.1,
                    },
                }

            entry = MemoryEntry(
                event_type=f"event_{i % 5}",
                meaning_significance=0.3 + (i % 7) * 0.1,
                timestamp=time.time() + i,
                feedback_data=feedback_data,
            )
            state.memory.append(entry)

        stop_event = threading.Event()
        event_queue = EventQueue()

        # Добавляем события в очередь
        for i in range(50):
            event = Event(
                type="noise" if i % 3 == 0 else "shock",
                intensity=0.3 + (i % 5) * 0.14,
                timestamp=time.time() + i,
            )
            event_queue.push(event)

        initial_ticks = state.ticks
        loop_thread = threading.Thread(
            target=run_loop,
            args=(
                state,
                dummy_monitor,
                0.01,
                100,
                stop_event,
                event_queue,
            ),  # 100 тиков
            daemon=True,
        )

        start_time = time.time()
        loop_thread.start()

        # Ждем завершения (run_loop остановится после 100 тиков или по stop_event)
        loop_thread.join(timeout=5.0)
        stop_event.set()

        elapsed = time.time() - start_time
        ticks_done = state.ticks - initial_ticks

        # Проверки производительности (более мягкие лимиты для интеграционного теста)
        assert ticks_done >= 30, f"Loop didn't complete enough ticks: {ticks_done} (expected >= 30)"
        assert elapsed < 8.0, f"Loop too slow: {elapsed:.3f}s for {ticks_done} ticks"

        # Проверяем, что Learning и Adaptation вызывались
        # (проверяем косвенно через наличие параметров)
        assert hasattr(state, "learning_params")
        assert hasattr(state, "adaptation_params")
        assert isinstance(state.learning_params, dict)
        assert isinstance(state.adaptation_params, dict)

    def test_event_queue_overflow_performance(self):
        """Benchmark: производительность EventQueue при переполнении"""
        queue = EventQueue()
        # Маленькая очередь для тестирования переполнения
        import queue as queue_module

        queue._queue = queue_module.Queue(maxsize=10)
        num_events = 50  # Больше максимального размера

        start_time = time.time()
        for i in range(num_events):
            event = Event(type=f"event_{i % 5}", intensity=0.5, timestamp=time.time() + i)
            queue.push(event)  # Должен логировать переполнение для некоторых событий
        overflow_elapsed = time.time() - start_time

        # Обновляем baseline
        update_baseline_if_needed(
            "test_event_queue_overflow_performance",
            {"overflow_elapsed": overflow_elapsed},
        )

        # Проверяем на регрессии
        overflow_regression = performance_baseline.check_regression(
            "test_event_queue_overflow_performance",
            "overflow_elapsed",
            overflow_elapsed,
            threshold_percent=25.0,
        )

        # Логируем результаты
        print(overflow_regression["message"])

        # Проверяем на регрессии
        assert not overflow_regression["is_regression"], overflow_regression["message"]

        # Проверяем, что некоторые события были потеряны
        assert queue._dropped_events_count > 0, "Expected some events to be dropped due to overflow"

    def test_subjective_time_performance(self):
        """Benchmark: влияние субъективного времени на производительность"""
        state = SelfState()
        num_operations = 5000

        # Тест с нормальным субъективным временем
        start_time = time.time()
        for i in range(num_operations):
            # Имитируем работу MeaningEngine с субъективным временем
            time_ratio = state.subjective_time / state.age if state.age > 0 else 1.0
            significance = 0.5
            if time_ratio > 1.1:
                significance *= 1.3
            elif time_ratio < 0.9:
                significance *= 0.8
            # Обновляем состояние
            state.apply_delta({"subjective_time": 0.001})
        normal_elapsed = time.time() - start_time

        # Обновляем baseline
        update_baseline_if_needed(
            "test_subjective_time_performance", {"normal_elapsed": normal_elapsed}
        )

        # Проверяем на регрессии
        normal_regression = performance_baseline.check_regression(
            "test_subjective_time_performance",
            "normal_elapsed",
            normal_elapsed,
            threshold_percent=20.0,
        )

        # Логируем результаты
        print(normal_regression["message"])

        # Проверяем на регрессии
        assert not normal_regression["is_regression"], normal_regression["message"]

    def test_memory_subjective_timestamp_performance(self):
        """Benchmark: производительность Memory с субъективными timestamp"""
        memory = Memory()
        num_entries = 1000

        start_time = time.time()
        for i in range(num_entries):
            entry = MemoryEntry(
                event_type=f"event_{i % 10}",
                meaning_significance=0.5,
                timestamp=time.time() + i,
                subjective_timestamp=float(i),  # Субъективное время
            )
            memory.append(entry)
        memory_elapsed = time.time() - start_time

        # Тест поиска по субъективному времени (пока не реализован, но измеряем базовую производительность)
        search_start = time.time()
        # Имитируем поиск (пока просто итерация)
        count = sum(
            1 for entry in memory if entry.subjective_timestamp and entry.subjective_timestamp > 500
        )
        search_elapsed = time.time() - search_start

        # Обновляем baseline
        update_baseline_if_needed(
            "test_memory_subjective_timestamp_performance",
            {"memory_elapsed": memory_elapsed, "search_elapsed": search_elapsed},
        )

        # Проверяем на регрессии
        memory_regression = performance_baseline.check_regression(
            "test_memory_subjective_timestamp_performance",
            "memory_elapsed",
            memory_elapsed,
            threshold_percent=20.0,
        )
        search_regression = performance_baseline.check_regression(
            "test_memory_subjective_timestamp_performance",
            "search_elapsed",
            search_elapsed,
            threshold_percent=20.0,
        )

        # Логируем результаты
        print(memory_regression["message"])
        print(search_regression["message"])

        # Проверяем на регрессии
        assert not memory_regression["is_regression"], memory_regression["message"]
        assert not search_regression["is_regression"], search_regression["message"]

        # Проверяем результаты
        assert count > 0, "Expected to find some entries with subjective_timestamp > 500"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

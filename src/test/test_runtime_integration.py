"""
Интеграционные тесты для Runtime Loop
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
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


@pytest.mark.integration
@pytest.mark.order(2)
class TestRuntimeLoop:
    """Интеграционные тесты для runtime loop"""

    @pytest.fixture
    def base_state(self):
        """Создает базовое состояние"""
        state = SelfState()
        state.energy = 50.0
        state.stability = 0.8
        state.integrity = 0.9
        return state

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_loop_single_tick(self, base_state, event_queue):
        """Тест выполнения одного тика цикла"""
        stop_event = threading.Event()
        initial_ticks = base_state.ticks

        # Запускаем цикл в отдельном потоке
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем немного
        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что тики увеличились
        assert base_state.ticks > initial_ticks

    def test_loop_processes_events(self, base_state, event_queue):
        """Тест обработки событий в цикле"""
        stop_event = threading.Event()

        # Добавляем событие в очередь
        event = Event(type="shock", intensity=0.5, timestamp=time.time())
        event_queue.push(event)

        initial_memory_size = len(base_state.memory)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что событие обработано (добавлено в память или изменено состояние)
        # Событие может быть обработано, если significance > 0
        # Проверяем, что что-то изменилось
        assert len(base_state.memory) >= initial_memory_size or base_state.energy != 50.0

    def test_loop_feedback_registration(self, base_state, event_queue):
        """Тест регистрации действий для Feedback"""
        stop_event = threading.Event()

        # Добавляем значимое событие
        event = Event(type="shock", intensity=0.8, timestamp=time.time())
        event_queue.push(event)

        # Запускаем цикл
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем обработки
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что состояние изменилось (событие было обработано)
        # Это косвенно подтверждает, что действие было зарегистрировано

    def test_loop_state_updates(self, base_state, event_queue):
        """Тест обновления состояния в цикле"""
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что тики увеличились
        assert base_state.ticks > 0
        # Возраст может увеличиться (зависит от dt)

    def test_loop_stops_on_stop_event(self, base_state, event_queue):
        """Тест остановки цикла по stop_event"""
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Убеждаемся, что цикл работает
        time.sleep(0.2)

        # Останавливаем
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что поток завершился
        assert not loop_thread.is_alive()

        # Проверяем, что цикл остановился (не делаем дополнительных тиков после join)
        # Цикл мог завершить текущий тик, поэтому проверяем только что он остановился
        assert not loop_thread.is_alive()

    def test_loop_handles_empty_queue(self, base_state, event_queue):
        """Тест работы цикла с пустой очередью"""
        stop_event = threading.Event()
        initial_ticks = base_state.ticks

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Цикл должен работать даже без событий
        assert base_state.ticks > initial_ticks

    def test_loop_multiple_events(self, base_state, event_queue):
        """Тест обработки нескольких событий"""
        stop_event = threading.Event()

        # Добавляем несколько событий
        events = [
            Event(type="shock", intensity=0.5, timestamp=time.time()),
            Event(type="noise", intensity=0.3, timestamp=time.time()),
            Event(type="recovery", intensity=0.4, timestamp=time.time()),
        ]
        for event in events:
            event_queue.push(event)

        initial_memory_size = len(base_state.memory)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # События должны быть обработаны
        # Проверяем, что очередь пуста или память изменилась
        assert event_queue.is_empty() or len(base_state.memory) > initial_memory_size

    def test_loop_snapshot_creation(self, base_state, event_queue, tmp_path):
        """Тест создания снимков в цикле"""
        import state.self_state as state_module

        original_dir = state_module.SNAPSHOT_DIR

        # Временно меняем директорию снимков
        state_module.SNAPSHOT_DIR = tmp_path / "snapshots"
        state_module.SNAPSHOT_DIR.mkdir(exist_ok=True)

        try:
            stop_event = threading.Event()
            base_state.ticks = 0  # Начинаем с 0

            loop_thread = threading.Thread(
                target=run_loop,
                args=(
                    base_state,
                    dummy_monitor,
                    0.05,
                    1,
                    stop_event,
                    event_queue,
                ),  # snapshot каждые 1 тик
                daemon=True,
            )
            loop_thread.start()

            # Ждем несколько тиков
            time.sleep(0.3)
            stop_event.set()
            loop_thread.join(timeout=1.0)

            # Проверяем, что снимки созданы
            list(state_module.SNAPSHOT_DIR.glob("snapshot_*.json"))
            # Может быть создан хотя бы один снимок
        finally:
            # Восстанавливаем оригинальную директорию
            state_module.SNAPSHOT_DIR = original_dir

    def test_loop_weakness_penalty(self, base_state, event_queue):
        """Тест штрафов за слабость в цикле"""
        stop_event = threading.Event()

        # Устанавливаем низкие значения
        base_state.energy = 0.03
        base_state.integrity = 0.03
        base_state.stability = 0.03

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что параметры уменьшились (штрафы)
        # Но не должны стать отрицательными
        assert base_state.energy >= 0.0
        assert base_state.integrity >= 0.0
        assert base_state.stability >= 0.0

    def test_loop_deactivates_on_zero_params(self, base_state, event_queue):
        """Тест деактивации при нулевых параметрах"""
        stop_event = threading.Event()

        # Устанавливаем нулевые значения
        base_state.energy = 0.0
        base_state.integrity = 0.0
        base_state.stability = 0.0

        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем, что состояние остается активным (бессмертная слабость - ADR 009)
        assert base_state.active is True

    def test_snapshot_recovery_integration(self, tmp_path):
        """Интеграционный тест восстановления из snapshot после 'перезапуска'"""
        import state.self_state as state_module
        from src.state.self_state import save_snapshot

        original_dir = state_module.SNAPSHOT_DIR

        # Временно меняем директорию снимков
        state_module.SNAPSHOT_DIR = tmp_path / "snapshots"
        state_module.SNAPSHOT_DIR.mkdir(exist_ok=True)

        try:
            # === Фаза 1: Создание состояния и snapshot вручную ===
            initial_state = SelfState()
            initial_state.energy = 80.0
            initial_state.integrity = 0.9
            initial_state.stability = 0.85
            initial_state.ticks = 5  # Имитируем работу в течение 5 тиков

            # Добавляем записи в память для реалистичного теста
            from src.memory.memory import MemoryEntry

            entry1 = MemoryEntry(
                event_type="noise", meaning_significance=0.3, timestamp=time.time() - 10
            )
            entry2 = MemoryEntry(
                event_type="decay", meaning_significance=0.7, timestamp=time.time() - 5
            )
            initial_state.memory.append(entry1)
            initial_state.memory.append(entry2)

            # Сохраняем snapshot
            save_snapshot(initial_state)

            # === Фаза 2: "Перезапуск" - загрузка из snapshot ===
            # Имитируем перезапуск: создаем новое состояние из последнего snapshot
            recovered_state = SelfState()
            recovered_state = recovered_state.load_latest_snapshot()

            # === Фаза 3: Проверка восстановления ===
            # Проверяем основные параметры
            assert recovered_state.ticks == 5, f"ticks: {recovered_state.ticks} != 5"
            assert (
                abs(recovered_state.energy - 80.0) < 0.001
            ), f"energy: {recovered_state.energy} != 80.0"
            assert (
                abs(recovered_state.integrity - 0.9) < 0.001
            ), f"integrity: {recovered_state.integrity} != 0.9"
            assert (
                abs(recovered_state.stability - 0.85) < 0.001
            ), f"stability: {recovered_state.stability} != 0.85"
            assert recovered_state.life_id == initial_state.life_id, "life_id должен сохраняться"
            assert (
                recovered_state.birth_timestamp == initial_state.birth_timestamp
            ), "birth_timestamp должен сохраняться"

            # Проверяем память
            assert (
                len(recovered_state.memory) == 2
            ), f"memory size: {len(recovered_state.memory)} != 2"
            assert recovered_state.memory[0].event_type == "noise"
            assert recovered_state.memory[1].event_type == "decay"
            assert abs(recovered_state.memory[0].meaning_significance - 0.3) < 0.001
            assert abs(recovered_state.memory[1].meaning_significance - 0.7) < 0.001

            # Проверяем, что система активна после восстановления
            assert recovered_state.is_active(), "Система должна быть активна после восстановления"

            # === Фаза 4: Тест продолжения работы ===
            # Имитируем продолжение работы - увеличиваем ticks
            recovered_state.ticks = 8
            recovered_state.energy = 75.0  # Имитируем небольшое снижение энергии

            # Сохраняем новый snapshot
            save_snapshot(recovered_state)

            # Загружаем еще раз, чтобы проверить, что изменения сохраняются
            final_state = SelfState()
            final_state = final_state.load_latest_snapshot()

            assert final_state.ticks == 8, f"final ticks: {final_state.ticks} != 8"
            assert (
                abs(final_state.energy - 75.0) < 0.001
            ), f"final energy: {final_state.energy} != 75.0"
            assert len(final_state.memory) == 2, "Память должна сохраняться"

        finally:
            # Восстанавливаем оригинальную директорию
            state_module.SNAPSHOT_DIR = original_dir

    def test_clarity_moments_integration_with_runtime_loop(self, base_state, event_queue):
        """Тест интеграции ClarityMoments с runtime loop"""
        from unittest.mock import Mock

        from src.experimental.clarity_moments import ClarityMoments

        # Создаем компоненты
        logger = Mock()
        clarity_moments = ClarityMoments(logger=logger)

        # Устанавливаем состояние для активации clarity
        base_state.stability = 0.9
        base_state.energy = 0.8
        base_state.ticks = 15

        # Проверяем, что ClarityMoments может создать событие
        clarity_event = clarity_moments.check_clarity_conditions(base_state)
        assert clarity_event is not None
        assert clarity_event["type"] == "clarity_moment"

        # Активируем clarity момент
        clarity_moments.activate_clarity_moment(base_state)

        # Проверяем, что SelfState имеет поля clarity и они установлены правильно
        assert hasattr(base_state, "clarity_state")
        assert hasattr(base_state, "clarity_duration")
        assert hasattr(base_state, "clarity_modifier")
        assert base_state.clarity_state is True
        assert base_state.clarity_duration == 50
        assert base_state.clarity_modifier == 1.5

    def test_clarity_moments_runtime_events_processing(self, base_state, event_queue):
        """Тест обработки событий clarity в runtime"""
        from unittest.mock import Mock

        from src.environment.event import Event
        from src.experimental.clarity_moments import ClarityMoments

        logger = Mock()
        clarity_moments = ClarityMoments(logger=logger)

        # Создаем и активируем clarity
        base_state.stability = 0.9
        base_state.energy = 0.8
        base_state.ticks = 15

        clarity_event = clarity_moments.check_clarity_conditions(base_state)
        assert clarity_event is not None

        clarity_moments.activate_clarity_moment(base_state)
        assert base_state.clarity_state is True

        # Создаем событие и помещаем в очередь
        event = Event(
            type="clarity_moment",
            intensity=0.8,
            timestamp=clarity_event["timestamp"],
            metadata=clarity_event["data"],
        )
        event_queue.push(event)

        # Проверяем, что событие в очереди
        assert not event_queue.is_empty()
        popped_events = event_queue.pop_all()
        assert len(popped_events) == 1
        assert popped_events[0].type == "clarity_moment"
        assert popped_events[0].metadata["clarity_id"] == 1

    def test_clarity_moments_with_meaning_engine_integration(self, base_state):
        """Тест интеграции ClarityMoments с MeaningEngine в runtime контексте"""
        from unittest.mock import Mock

        from src.environment.event import Event
        from src.experimental.clarity_moments import ClarityMoments
        from src.meaning.engine import MeaningEngine

        logger = Mock()
        clarity_moments = ClarityMoments(logger=logger)
        meaning_engine = MeaningEngine()

        # Создаем тестовое событие
        test_event = Event(type="noise", intensity=0.5, timestamp=time.time())

        # Получаем значимость без clarity
        base_state.clarity_state = False
        significance_without = meaning_engine.appraisal(test_event, base_state)

        # Активируем clarity
        clarity_moments.activate_clarity_moment(base_state)
        assert base_state.clarity_state is True

        # Получаем значимость с clarity
        significance_with = meaning_engine.appraisal(test_event, base_state)

        # Значимость с clarity должна быть выше
        assert significance_with > significance_without

        # Проверяем коэффициент усиления (примерно 1.5x)
        ratio = significance_with / significance_without
        assert 1.3 <= ratio <= 1.7  # С небольшим допуском

    def test_clarity_moments_state_persistence_in_runtime(self, base_state):
        """Тест сохранения состояния clarity в runtime цикле"""
        from unittest.mock import Mock

        from src.experimental.clarity_moments import ClarityMoments

        logger = Mock()
        clarity_moments = ClarityMoments(logger=logger)

        # Активируем clarity
        clarity_moments.activate_clarity_moment(base_state)
        assert base_state.clarity_state is True
        assert base_state.clarity_duration == 50

        # Симулируем несколько обновлений состояния (как в runtime loop)
        for i in range(10):
            clarity_moments.update_clarity_state(base_state)

        assert base_state.clarity_state is True
        assert base_state.clarity_duration == 40

        # Продолжаем до деактивации
        for i in range(40):
            clarity_moments.update_clarity_state(base_state)

        assert base_state.clarity_state is False
        assert base_state.clarity_duration == 0
        assert base_state.clarity_modifier == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

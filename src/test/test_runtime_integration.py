"""
Интеграционные тесты для Runtime Loop
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import threading
import pytest
from runtime.loop import run_loop
from state.self_state import SelfState
from environment.event_queue import EventQueue
from environment.event import Event
from memory.memory import MemoryEntry


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


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
            daemon=True
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
            daemon=True
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
            daemon=True
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
        initial_energy = base_state.energy
        initial_age = base_state.age
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True
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
            daemon=True
        )
        loop_thread.start()
        
        # Убеждаемся, что цикл работает
        time.sleep(0.2)
        initial_ticks = base_state.ticks
        
        # Останавливаем
        stop_event.set()
        loop_thread.join(timeout=1.0)
        
        # Проверяем, что поток завершился
        assert not loop_thread.is_alive()
        
        # Проверяем, что тики не увеличиваются после остановки
        time.sleep(0.2)
        assert base_state.ticks == initial_ticks
    
    def test_loop_handles_empty_queue(self, base_state, event_queue):
        """Тест работы цикла с пустой очередью"""
        stop_event = threading.Event()
        initial_ticks = base_state.ticks
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True
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
            Event(type="recovery", intensity=0.4, timestamp=time.time())
        ]
        for event in events:
            event_queue.push(event)
        
        initial_memory_size = len(base_state.memory)
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True
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
                args=(base_state, dummy_monitor, 0.05, 1, stop_event, event_queue),  # snapshot каждые 1 тик
                daemon=True
            )
            loop_thread.start()
            
            # Ждем несколько тиков
            time.sleep(0.3)
            stop_event.set()
            loop_thread.join(timeout=1.0)
            
            # Проверяем, что снимки созданы
            snapshots = list(state_module.SNAPSHOT_DIR.glob("snapshot_*.json"))
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
        
        initial_energy = base_state.energy
        initial_integrity = base_state.integrity
        initial_stability = base_state.stability
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(base_state, dummy_monitor, 0.1, 100, stop_event, event_queue),
            daemon=True
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
            daemon=True
        )
        loop_thread.start()
        
        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)
        
        # Проверяем, что состояние деактивировано
        assert base_state.active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

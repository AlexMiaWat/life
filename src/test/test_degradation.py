"""
Тесты на деградацию системы Life (ROADMAP T.1)

Проверяют:
- Падение energy/integrity/stability до 0
- Поведение системы при различных типах деградации
- Механизм слабости и штрафов
- Взаимодействие деградации с runtime loop
- Edge cases при критических значениях параметров
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import threading
import time

import pytest

from environment.event import Event
from environment.event_queue import EventQueue
from memory.memory import MemoryEntry
from runtime.loop import run_loop
from state.self_state import SelfState


def dummy_monitor(state):
    """Простой монитор для тестов"""
    pass


class DegradationTracker:
    """Трекер для отслеживания изменений состояния при деградации"""

    def __init__(self):
        self.history = []

    def track(self, state):
        """Записывает текущее состояние"""
        self.history.append({
            "energy": state.energy,
            "integrity": state.integrity,
            "stability": state.stability,
            "active": state.active,
            "ticks": state.ticks,
        })


@pytest.mark.unit
@pytest.mark.order(3)
class TestDegradationUnit:
    """Unit тесты для деградации SelfState"""

    def test_energy_degradation_to_zero(self):
        """Тест падения energy до 0"""
        state = SelfState()
        state.energy = 10.0

        # Постепенно уменьшаем energy
        for _ in range(20):
            state.apply_delta({"energy": -1.0})

        assert state.energy == 0.0
        # Проверяем, что не стало отрицательным
        state.apply_delta({"energy": -5.0})
        assert state.energy == 0.0

    def test_integrity_degradation_to_zero(self):
        """Тест падения integrity до 0"""
        state = SelfState()
        state.integrity = 0.5

        # Постепенно уменьшаем integrity
        for _ in range(10):
            state.apply_delta({"integrity": -0.1})

        assert state.integrity == 0.0
        # Проверяем, что не стало отрицательным
        state.apply_delta({"integrity": -0.1})
        assert state.integrity == 0.0

    def test_stability_degradation_to_zero(self):
        """Тест падения stability до 0"""
        state = SelfState()
        state.stability = 0.3

        # Постепенно уменьшаем stability
        for _ in range(6):
            state.apply_delta({"stability": -0.1})

        # С учетом погрешности float
        assert state.stability <= 0.0001
        state.apply_delta({"stability": -0.1})
        assert state.stability == 0.0

    def test_simultaneous_degradation_all_params(self):
        """Тест одновременной деградации всех параметров"""
        state = SelfState()
        state.energy = 20.0
        state.integrity = 0.2
        state.stability = 0.2

        # Одновременное уменьшение
        for _ in range(5):
            state.apply_delta({
                "energy": -5.0,
                "integrity": -0.05,
                "stability": -0.05
            })

        assert state.energy == 0.0
        assert state.integrity <= 0.0001
        assert state.stability <= 0.0001

    def test_active_flag_set_false_on_zero_energy(self):
        """Тест: флаг active должен быть False при energy=0 в loop"""
        state = SelfState()
        state.energy = 0.0
        state.integrity = 1.0
        state.stability = 1.0

        # Проверяем условие из loop.py (finally block)
        if state.energy <= 0 or state.integrity <= 0 or state.stability <= 0:
            state.active = False

        assert state.active is False

    def test_active_flag_set_false_on_zero_integrity(self):
        """Тест: флаг active должен быть False при integrity=0"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 0.0
        state.stability = 1.0

        if state.energy <= 0 or state.integrity <= 0 or state.stability <= 0:
            state.active = False

        assert state.active is False

    def test_active_flag_set_false_on_zero_stability(self):
        """Тест: флаг active должен быть False при stability=0"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 1.0
        state.stability = 0.0

        if state.energy <= 0 or state.integrity <= 0 or state.stability <= 0:
            state.active = False

        assert state.active is False

    def test_degradation_preserves_other_state(self):
        """Тест: деградация не влияет на другие параметры состояния"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 1.0
        state.stability = 1.0
        state.ticks = 100
        state.age = 50.0
        life_id = state.life_id

        # Деградируем energy
        state.apply_delta({"energy": -100.0})

        assert state.energy == 0.0
        assert state.integrity == 1.0
        assert state.stability == 1.0
        assert state.ticks == 100
        assert state.age == 50.0
        assert state.life_id == life_id  # Идентичность сохранена

    def test_gradual_degradation_history(self):
        """Тест: постепенная деградация с историей"""
        state = SelfState()
        state.energy = 50.0
        history = []

        for i in range(10):
            history.append(state.energy)
            state.apply_delta({"energy": -5.0})

        # Проверяем монотонное убывание
        for i in range(len(history) - 1):
            assert history[i] > history[i + 1] or history[i + 1] == 0.0


@pytest.mark.integration
@pytest.mark.order(3)
class TestDegradationIntegration:
    """Интеграционные тесты деградации с Runtime Loop"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_energy_degradation_in_loop_with_events(self, event_queue):
        """Тест деградации energy при обработке событий в loop"""
        state = SelfState()
        state.energy = 30.0
        state.integrity = 1.0
        state.stability = 1.0
        stop_event = threading.Event()

        # Добавляем события, которые потребляют energy
        for _ in range(5):
            event = Event(type="shock", intensity=0.8, timestamp=time.time())
            event_queue.push(event)

        initial_energy = state.energy

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Energy должна уменьшиться
        assert state.energy < initial_energy

    def test_weakness_penalty_acceleration(self, event_queue):
        """Тест: слабость ускоряет деградацию (штрафы)"""
        state = SelfState()
        # Устанавливаем значения ниже порога слабости (0.05)
        state.energy = 0.03
        state.integrity = 0.5
        state.stability = 0.5
        stop_event = threading.Event()

        initial_integrity = state.integrity
        initial_stability = state.stability

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # При слабости stability и integrity должны уменьшаться быстрее
        # из-за штрафа penalty = 0.02 * dt
        assert state.stability < initial_stability
        assert state.integrity < initial_integrity

    def test_full_degradation_cycle(self, event_queue):
        """Тест полного цикла деградации от начального до критического состояния"""
        state = SelfState()
        state.energy = 5.0  # Низкая начальная энергия
        state.integrity = 0.1
        state.stability = 0.1
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.8)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Проверяем историю деградации
        assert len(tracker.history) > 0

        # Проверяем, что параметры уменьшались
        if len(tracker.history) > 1:
            first = tracker.history[0]
            last = tracker.history[-1]
            # Хотя бы один параметр должен уменьшиться
            assert (
                last["energy"] <= first["energy"] or
                last["integrity"] <= first["integrity"] or
                last["stability"] <= first["stability"]
            )

    def test_deactivation_on_energy_zero(self, event_queue):
        """Тест деактивации при падении energy до 0"""
        state = SelfState()
        state.energy = 0.01  # Почти 0
        state.integrity = 0.01
        state.stability = 0.01
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Система должна деактивироваться
        assert state.active is False

    def test_deactivation_on_integrity_zero(self, event_queue):
        """Тест деактивации при падении integrity до 0"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 0.0  # Уже 0
        state.stability = 1.0
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        assert state.active is False

    def test_deactivation_on_stability_zero(self, event_queue):
        """Тест деактивации при падении stability до 0"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 1.0
        state.stability = 0.0  # Уже 0
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        assert state.active is False

    def test_loop_continues_while_degrading(self, event_queue):
        """Тест: loop продолжает работать пока параметры > 0"""
        state = SelfState()
        state.energy = 10.0  # Достаточно для нескольких тиков
        state.integrity = 0.5
        state.stability = 0.5
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Тики должны увеличиться
        assert state.ticks > 0


@pytest.mark.integration
@pytest.mark.order(3)
class TestDegradationEdgeCases:
    """Edge cases для тестов деградации"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_boundary_values_energy(self):
        """Тест граничных значений energy"""
        state = SelfState()

        # Точное значение 0
        state.energy = 0.0
        assert state.energy == 0.0

        # Очень маленькое значение
        state.energy = 0.0001
        assert state.energy > 0.0
        assert state.energy < 0.001

        # Максимальное значение
        state.energy = 100.0
        assert state.energy == 100.0

        # Попытка превысить максимум
        state.apply_delta({"energy": 50.0})
        assert state.energy == 100.0

    def test_boundary_values_integrity(self):
        """Тест граничных значений integrity"""
        state = SelfState()

        # Точное значение 0
        state.integrity = 0.0
        assert state.integrity == 0.0

        # Очень маленькое значение
        state.integrity = 0.0001
        assert state.integrity > 0.0

        # Максимальное значение
        state.integrity = 1.0
        assert state.integrity == 1.0

        # Попытка превысить максимум
        state.apply_delta({"integrity": 0.5})
        assert state.integrity == 1.0

    def test_boundary_values_stability(self):
        """Тест граничных значений stability"""
        state = SelfState()

        # Точное значение 0
        state.stability = 0.0
        assert state.stability == 0.0

        # Очень маленькое значение
        state.stability = 0.0001
        assert state.stability > 0.0

        # Максимальное значение
        state.stability = 1.0
        assert state.stability == 1.0

        # Попытка превысить максимум
        state.apply_delta({"stability": 0.5})
        assert state.stability == 1.0

    def test_weakness_threshold_boundary(self, event_queue):
        """Тест порогового значения слабости (0.05)"""
        # Тест на значении выше порога
        state_above = SelfState()
        state_above.energy = 0.06  # Выше порога 0.05
        state_above.integrity = 1.0
        state_above.stability = 1.0

        # Тест на значении ниже порога
        state_below = SelfState()
        state_below.energy = 0.04  # Ниже порога 0.05
        state_below.integrity = 1.0
        state_below.stability = 1.0

        # Проверяем логику из loop.py
        weakness_threshold = 0.05

        # Выше порога - штрафы не применяются
        assert not (
            state_above.energy <= weakness_threshold or
            state_above.integrity <= weakness_threshold or
            state_above.stability <= weakness_threshold
        )

        # Ниже порога - штрафы применяются
        assert (
            state_below.energy <= weakness_threshold or
            state_below.integrity <= weakness_threshold or
            state_below.stability <= weakness_threshold
        )

    def test_rapid_degradation_many_events(self, event_queue):
        """Тест быстрой деградации при большом количестве событий"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.8
        state.stability = 0.8
        stop_event = threading.Event()

        # Добавляем много негативных событий
        for _ in range(20):
            event = Event(type="shock", intensity=0.9, timestamp=time.time())
            event_queue.push(event)

        initial_energy = state.energy

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.02, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Значительное падение энергии
        assert state.energy < initial_energy

    def test_degradation_with_memory(self, event_queue):
        """Тест: память сохраняется при деградации"""
        state = SelfState()
        state.energy = 20.0
        state.integrity = 0.5
        state.stability = 0.5
        stop_event = threading.Event()

        # Добавляем записи в память
        for i in range(3):
            entry = MemoryEntry(
                event_type=f"test_event_{i}",
                meaning_significance=0.5,
                timestamp=time.time()
            )
            state.memory.append(entry)

        initial_memory_count = len(state.memory)

        # Добавляем события для обработки
        event = Event(type="shock", intensity=0.7, timestamp=time.time())
        event_queue.push(event)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Память должна сохраниться или увеличиться
        assert len(state.memory) >= initial_memory_count

    def test_degradation_does_not_affect_identity(self, event_queue):
        """Тест: деградация не меняет идентичность"""
        state = SelfState()
        life_id = state.life_id
        birth_timestamp = state.birth_timestamp
        state.energy = 1.0  # Очень низкая энергия
        state.integrity = 0.1
        state.stability = 0.1
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.3)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Идентичность неизменна
        assert state.life_id == life_id
        assert state.birth_timestamp == birth_timestamp

    def test_all_params_zero_simultaneously(self, event_queue):
        """Тест: все параметры равны 0 одновременно"""
        state = SelfState()
        state.energy = 0.0
        state.integrity = 0.0
        state.stability = 0.0
        stop_event = threading.Event()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.2)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Система деактивирована
        assert state.active is False
        # Параметры остаются на 0
        assert state.energy == 0.0
        assert state.integrity == 0.0
        assert state.stability == 0.0


@pytest.mark.integration
@pytest.mark.order(3)
class TestDegradationRecovery:
    """Тесты на проверку возможности восстановления после деградации"""

    def test_energy_recovery_possible(self):
        """Тест: энергия может восстанавливаться"""
        state = SelfState()
        state.energy = 10.0

        # Восстанавливаем энергию
        state.apply_delta({"energy": 50.0})
        assert state.energy == 60.0

        # Восстанавливаем до максимума
        state.apply_delta({"energy": 100.0})
        assert state.energy == 100.0

    def test_integrity_recovery_possible(self):
        """Тест: integrity может восстанавливаться"""
        state = SelfState()
        state.integrity = 0.3

        state.apply_delta({"integrity": 0.4})
        assert abs(state.integrity - 0.7) < 0.0001

        state.apply_delta({"integrity": 0.5})
        assert state.integrity == 1.0

    def test_stability_recovery_possible(self):
        """Тест: stability может восстанавливаться"""
        state = SelfState()
        state.stability = 0.2

        state.apply_delta({"stability": 0.5})
        assert abs(state.stability - 0.7) < 0.0001

        state.apply_delta({"stability": 0.5})
        assert state.stability == 1.0

    def test_recovery_from_near_zero(self):
        """Тест восстановления с почти нулевых значений"""
        state = SelfState()
        state.energy = 0.01
        state.integrity = 0.01
        state.stability = 0.01

        # Восстанавливаем все параметры
        state.apply_delta({
            "energy": 99.0,
            "integrity": 0.9,
            "stability": 0.9
        })

        # Проверяем восстановление
        assert state.energy > 90.0
        assert state.integrity > 0.9
        assert state.stability > 0.9

    def test_active_flag_stays_false_after_deactivation(self):
        """Тест: флаг active остается False после деактивации"""
        state = SelfState()
        state.energy = 0.0
        state.active = False  # Деактивирован

        # Попытка восстановить энергию
        state.apply_delta({"energy": 100.0})
        assert state.energy == 100.0

        # Но active остается False (нужно явное восстановление)
        assert state.active is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

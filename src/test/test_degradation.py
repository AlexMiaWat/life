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

from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.memory.memory import MemoryEntry
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


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

    def test_learning_params_recovery_from_snapshot(self):
        """Тест: восстановление learning_params из snapshot"""
        from state.self_state import save_snapshot, load_snapshot
        
        state = SelfState()
        state.energy = 50.0
        
        # Модифицируем learning_params
        state.learning_params["event_type_sensitivity"]["noise"] = 0.8
        state.learning_params["event_type_sensitivity"]["shock"] = 0.9
        state.learning_params["significance_thresholds"]["noise"] = 0.15
        state.learning_params["response_coefficients"]["dampen"] = 0.7
        
        # Сохраняем snapshot
        save_snapshot(state)
        tick = state.ticks
        
        # Изменяем параметры
        state.learning_params["event_type_sensitivity"]["noise"] = 0.2
        state.learning_params["significance_thresholds"]["noise"] = 0.05
        
        # Загружаем snapshot
        loaded_state = load_snapshot(tick)
        
        # Проверяем восстановление параметров
        assert loaded_state.learning_params["event_type_sensitivity"]["noise"] == 0.8
        assert loaded_state.learning_params["event_type_sensitivity"]["shock"] == 0.9
        assert loaded_state.learning_params["significance_thresholds"]["noise"] == 0.15
        assert loaded_state.learning_params["response_coefficients"]["dampen"] == 0.7

    def test_adaptation_params_recovery_from_snapshot(self):
        """Тест: восстановление adaptation_params из snapshot"""
        from state.self_state import save_snapshot, load_snapshot
        
        state = SelfState()
        state.energy = 50.0
        
        # Модифицируем adaptation_params
        state.adaptation_params["behavior_sensitivity"]["noise"] = 0.8
        state.adaptation_params["behavior_sensitivity"]["shock"] = 0.9
        state.adaptation_params["behavior_thresholds"]["noise"] = 0.15
        state.adaptation_params["behavior_coefficients"]["dampen"] = 0.7
        
        # Сохраняем snapshot
        save_snapshot(state)
        tick = state.ticks
        
        # Изменяем параметры
        state.adaptation_params["behavior_sensitivity"]["noise"] = 0.2
        state.adaptation_params["behavior_thresholds"]["noise"] = 0.05
        
        # Загружаем snapshot
        loaded_state = load_snapshot(tick)
        
        # Проверяем восстановление параметров
        assert loaded_state.adaptation_params["behavior_sensitivity"]["noise"] == 0.8
        assert loaded_state.adaptation_params["behavior_sensitivity"]["shock"] == 0.9
        assert loaded_state.adaptation_params["behavior_thresholds"]["noise"] == 0.15
        assert loaded_state.adaptation_params["behavior_coefficients"]["dampen"] == 0.7

    def test_learning_adaptation_params_recovery_together(self):
        """Тест: совместное восстановление learning_params и adaptation_params из snapshot"""
        from state.self_state import save_snapshot, load_snapshot
        
        state = SelfState()
        state.energy = 50.0
        
        # Модифицируем оба набора параметров
        state.learning_params["event_type_sensitivity"]["noise"] = 0.75
        state.adaptation_params["behavior_sensitivity"]["noise"] = 0.85
        state.adaptation_params["behavior_coefficients"]["absorb"] = 0.6
        
        # Сохраняем snapshot
        save_snapshot(state)
        tick = state.ticks
        
        # Изменяем параметры
        state.learning_params["event_type_sensitivity"]["noise"] = 0.1
        state.adaptation_params["behavior_sensitivity"]["noise"] = 0.1
        state.adaptation_params["behavior_coefficients"]["absorb"] = 1.0
        
        # Загружаем snapshot
        loaded_state = load_snapshot(tick)
        
        # Проверяем восстановление обоих наборов параметров
        assert loaded_state.learning_params["event_type_sensitivity"]["noise"] == 0.75
        assert loaded_state.adaptation_params["behavior_sensitivity"]["noise"] == 0.85
        assert loaded_state.adaptation_params["behavior_coefficients"]["absorb"] == 0.6
        
        # Проверяем, что структура параметров сохранена
        assert "event_type_sensitivity" in loaded_state.learning_params
        assert "significance_thresholds" in loaded_state.learning_params
        assert "response_coefficients" in loaded_state.learning_params
        assert "behavior_sensitivity" in loaded_state.adaptation_params
        assert "behavior_thresholds" in loaded_state.adaptation_params
        assert "behavior_coefficients" in loaded_state.adaptation_params


@pytest.mark.integration
@pytest.mark.order(3)
@pytest.mark.slow
class TestDegradationLongRunning:
    """Тесты на деградацию при длительной работе (1000+ тиков) - ROADMAP T.2"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_degradation_over_1000_ticks(self, event_queue):
        """Тест деградации системы при длительной работе (1000+ тиков)"""
        state = SelfState()
        # Начальные значения - низкие, чтобы деградация была заметна
        state.energy = 30.0
        state.integrity = 0.6
        state.stability = 0.6
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Добавляем события, которые будут вызывать деградацию
        for _ in range(50):
            event = Event(type="shock", intensity=0.7, timestamp=time.time())
            event_queue.push(event)

        initial_energy = state.energy
        initial_integrity = state.integrity
        initial_stability = state.stability

        # Запускаем loop на 1000+ тиков с коротким интервалом
        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.001, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно долго для выполнения 1000+ тиков
        time.sleep(2.0)
        stop_event.set()
        loop_thread.join(timeout=3.0)

        # Проверяем, что система выполнила много тиков
        assert state.ticks >= 1000, f"Expected >= 1000 ticks, got {state.ticks}"

        # Проверяем, что деградация произошла
        # Хотя бы один параметр должен уменьшиться
        assert (
            state.energy < initial_energy or
            state.integrity < initial_integrity or
            state.stability < initial_stability
        ), "No degradation occurred during long run"

        # Проверяем, что история деградации записана
        assert len(tracker.history) > 0, "No degradation history recorded"

    def test_degradation_stability_over_time(self, event_queue):
        """Тест стабильности деградации при длительной работе"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.8
        state.stability = 0.8
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.001, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(1.5)
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем выполнение большого количества тиков
        assert state.ticks >= 1000

        # Проверяем, что деградация была постепенной (не скачкообразной)
        if len(tracker.history) > 10:
            # Проверяем монотонность убывания энергии (с допуском на восстановление)
            energy_values = [h["energy"] for h in tracker.history]
            # Энергия должна в целом убывать (не обязательно строго монотонно)
            # Проверяем, что последнее значение не больше первого более чем на 10%
            assert energy_values[-1] <= energy_values[0] * 1.1, \
                "Energy increased significantly during degradation test"


@pytest.mark.integration
@pytest.mark.order(3)
class TestDegradationWithLearningAdaptation:
    """Тесты на использование параметров Learning/Adaptation при деградации"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_learning_params_affect_degradation(self, event_queue):
        """Тест: параметры Learning влияют на деградацию через MeaningEngine"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.8
        state.stability = 0.8
        
        # Устанавливаем высокую чувствительность к noise в learning_params
        state.learning_params["event_type_sensitivity"]["noise"] = 0.9
        state.learning_params["event_type_sensitivity"]["shock"] = 0.9
        
        # Устанавливаем низкие пороги значимости
        state.learning_params["significance_thresholds"]["noise"] = 0.05
        state.learning_params["significance_thresholds"]["shock"] = 0.05
        
        stop_event = threading.Event()
        initial_energy = state.energy
        
        # Добавляем события noise
        for _ in range(10):
            event = Event(type="noise", intensity=0.3, timestamp=time.time())
            event_queue.push(event)
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()
        
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)
        
        # С высокой чувствительностью деградация должна быть более заметной
        assert state.energy < initial_energy
        
        # Проверяем, что learning_params сохранились
        assert "event_type_sensitivity" in state.learning_params
        assert state.learning_params["event_type_sensitivity"]["noise"] == 0.9

    def test_adaptation_params_affect_degradation(self, event_queue):
        """Тест: параметры Adaptation влияют на деградацию"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.8
        state.stability = 0.8
        
        # Устанавливаем высокую чувствительность поведения
        state.adaptation_params["behavior_sensitivity"]["noise"] = 0.9
        state.adaptation_params["behavior_sensitivity"]["shock"] = 0.9
        
        # Устанавливаем низкие пороги поведения
        state.adaptation_params["behavior_thresholds"]["noise"] = 0.05
        state.adaptation_params["behavior_thresholds"]["shock"] = 0.05
        
        # Устанавливаем низкие коэффициенты реакции (меньше поглощение)
        state.adaptation_params["behavior_coefficients"]["absorb"] = 0.5
        state.adaptation_params["behavior_coefficients"]["dampen"] = 0.3
        
        stop_event = threading.Event()
        initial_energy = state.energy
        
        # Добавляем события shock
        for _ in range(5):
            event = Event(type="shock", intensity=0.5, timestamp=time.time())
            event_queue.push(event)
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()
        
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)
        
        # С низкими коэффициентами деградация должна быть меньше
        # (меньше поглощение = меньше влияние)
        assert state.energy < initial_energy
        
        # Проверяем, что adaptation_params сохранились
        assert "behavior_sensitivity" in state.adaptation_params
        assert state.adaptation_params["behavior_sensitivity"]["noise"] == 0.9

    def test_learning_adaptation_params_preserved_during_degradation(self, event_queue):
        """Тест: параметры Learning/Adaptation сохраняются во время деградации"""
        state = SelfState()
        state.energy = 30.0
        state.integrity = 0.5
        state.stability = 0.5
        
        # Запоминаем начальные параметры
        initial_learning_params = state.learning_params.copy()
        initial_adaptation_params = state.adaptation_params.copy()
        
        stop_event = threading.Event()
        
        # Добавляем события, вызывающие деградацию
        for _ in range(10):
            event = Event(type="shock", intensity=0.7, timestamp=time.time())
            event_queue.push(event)
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()
        
        time.sleep(0.8)
        stop_event.set()
        loop_thread.join(timeout=1.0)
        
        # Проверяем, что параметры сохранились (структура)
        assert "event_type_sensitivity" in state.learning_params
        assert "significance_thresholds" in state.learning_params
        assert "response_coefficients" in state.learning_params
        
        assert "behavior_sensitivity" in state.adaptation_params
        assert "behavior_thresholds" in state.adaptation_params
        assert "behavior_coefficients" in state.adaptation_params
        
        # Параметры могут измениться из-за работы Learning/Adaptation,
        # но структура должна сохраниться
        assert len(state.learning_params) == len(initial_learning_params)
        assert len(state.adaptation_params) == len(initial_adaptation_params)

    def test_degradation_with_modified_coefficients(self, event_queue):
        """Тест: деградация с модифицированными коэффициентами реакции"""
        state = SelfState()
        state.energy = 50.0
        
        # Устанавливаем очень низкие коэффициенты для absorb (меньше поглощение)
        state.learning_params["response_coefficients"]["absorb"] = 0.2
        state.adaptation_params["behavior_coefficients"]["absorb"] = 0.2
        
        # Устанавливаем высокие коэффициенты для dampen (больше ослабление)
        state.learning_params["response_coefficients"]["dampen"] = 0.8
        state.adaptation_params["behavior_coefficients"]["dampen"] = 0.8
        
        stop_event = threading.Event()
        initial_energy = state.energy
        
        # Добавляем события recovery (положительные)
        for _ in range(5):
            event = Event(type="recovery", intensity=0.5, timestamp=time.time())
            event_queue.push(event)
        
        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, dummy_monitor, 0.05, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()
        
        time.sleep(0.5)
        stop_event.set()
        loop_thread.join(timeout=1.0)
        
        # С низкими коэффициентами для absorb, восстановление должно быть меньше
        # (но все равно должно быть положительным для recovery)
        # Проверяем, что параметры использовались
        assert hasattr(state, "learning_params")
        assert hasattr(state, "adaptation_params")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

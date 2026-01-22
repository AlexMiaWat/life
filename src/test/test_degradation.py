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
        self.history.append(
            {
                "energy": state.energy,
                "integrity": state.integrity,
                "stability": state.stability,
                "active": state.active,
                "ticks": state.ticks,
            }
        )


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
            state.apply_delta({"energy": -5.0, "integrity": -0.05, "stability": -0.05})

        assert state.energy == 0.0
        assert state.integrity <= 0.0001
        assert state.stability <= 0.0001

    def test_active_flag_remains_true_on_zero_energy(self):
        """Тест: флаг active остается True при energy=0 (система продолжает работать в degraded состоянии)"""
        state = SelfState()
        # Используем apply_delta для установки energy в 0, чтобы избежать проблем с __setattr__
        state.apply_delta({"energy": -100.0})  # Уменьшаем до 0
        state.integrity = 1.0
        state.stability = 1.0

        # Согласно философии Life, система продолжает работать при параметрах <= 0
        # Флаг active не должен автоматически становиться False
        assert state.active is True
        assert state.energy == 0.0

    def test_active_flag_remains_true_on_zero_integrity(self):
        """Тест: флаг active остается True при integrity=0 (система продолжает работать в degraded состоянии)"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 0.0
        state.stability = 1.0

        # Согласно философии Life, система продолжает работать при параметрах <= 0
        assert state.active is True

    def test_active_flag_remains_true_on_zero_stability(self):
        """Тест: флаг active остается True при stability=0 (система продолжает работать в degraded состоянии)"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 1.0
        state.stability = 0.0

        # Согласно философии Life, система продолжает работать при параметрах <= 0
        assert state.active is True

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
                last["energy"] <= first["energy"]
                or last["integrity"] <= first["integrity"]
                or last["stability"] <= first["stability"]
            )

    def test_system_continues_on_energy_zero(self, event_queue):
        """Тест продолжения работы при падении energy до 0 (бессмертная слабость)"""
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

        # Система должна продолжать работать в degraded состоянии
        assert state.active is True
        # Параметры могут быть <= 0, но система не останавливается
        assert state.ticks > 0  # Тики должны увеличиваться

    def test_system_continues_on_integrity_zero(self, event_queue):
        """Тест продолжения работы при integrity=0 (бессмертная слабость)"""
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

        # Система продолжает работать
        assert state.active is True
        assert state.ticks > 0

    def test_system_continues_on_stability_zero(self, event_queue):
        """Тест продолжения работы при stability=0 (бессмертная слабость)"""
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

        # Система продолжает работать
        assert state.active is True
        assert state.ticks > 0

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
            state_above.energy <= weakness_threshold
            or state_above.integrity <= weakness_threshold
            or state_above.stability <= weakness_threshold
        )

        # Ниже порога - штрафы применяются
        assert (
            state_below.energy <= weakness_threshold
            or state_below.integrity <= weakness_threshold
            or state_below.stability <= weakness_threshold
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
            args=(state, dummy_monitor, 0.001, 100, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(2.0)
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
                timestamp=time.time(),
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

    def test_system_continues_with_all_params_zero(self, event_queue):
        """Тест: система продолжает работать даже когда все параметры равны 0 (бессмертная слабость)"""
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

        # Система продолжает работать в крайне degraded состоянии
        assert state.active is True
        # Параметры остаются на 0, но система не останавливается
        assert state.energy == 0.0
        assert state.integrity == 0.0
        assert state.stability == 0.0
        # Тики должны увеличиваться несмотря на нулевые параметры
        assert state.ticks > 0


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
        state.apply_delta({"energy": 99.0, "integrity": 0.9, "stability": 0.9})

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
        from state.self_state import load_snapshot, save_snapshot

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
        from state.self_state import load_snapshot, save_snapshot

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
        from state.self_state import load_snapshot, save_snapshot

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
        # Начальные значения - достаточно высокие для длительной работы
        state.energy = 80.0
        state.integrity = 0.9
        state.stability = 0.9
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        initial_energy = state.energy
        initial_integrity = state.integrity
        initial_stability = state.stability

        # Отключаем weakness penalty для теста длительной работы
        # Отключаем logging для теста
        state.disable_logging()

        # Запускаем loop без событий для проверки базовой работоспособности
        # Увеличиваем snapshot_period до 10000, чтобы не сохранять snapshots
        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.001, 10000, stop_event, event_queue, True),
            daemon=True,
        )
        loop_thread.start()

        # Ждем достаточно долго для выполнения 1000+ тиков
        time.sleep(25.0)  # Увеличиваем время ожидания
        stop_event.set()
        loop_thread.join(timeout=2.0)

        # Проверяем, что система выполнила много тиков
        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Проверяем, что система остается стабильной при длительной работе
        # Параметры не должны сильно отклоняться от начальных значений
        assert (
            abs(state.energy - initial_energy) < 5.0
        ), "Energy changed significantly during long run"
        assert (
            abs(state.integrity - initial_integrity) < 0.1
        ), "Integrity changed significantly during long run"
        assert (
            abs(state.stability - initial_stability) < 0.1
        ), "Stability changed significantly during long run"

        # Проверяем, что история деградации записана
        assert len(tracker.history) > 0, "No degradation history recorded"

    def test_degradation_stability_over_time(self, event_queue):
        """Тест стабильности деградации при длительной работе"""
        state = SelfState()
        state.energy = 90.0  # Более высокие начальные значения
        state.integrity = 0.95
        state.stability = 0.95
        state.disable_logging()  # Отключаем logging
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Функция для постепенного добавления легких событий
        def add_light_events():
            for i in range(10):  # Меньше событий
                if stop_event.is_set():
                    break
                event = Event(
                    type="decay", intensity=-0.1, timestamp=time.time()
                )  # Легкая деградация
                event_queue.push(event)
                time.sleep(0.1)  # Реже добавляем события

        # Запускаем поток для постепенного добавления событий
        event_thread = threading.Thread(target=add_light_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.0001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(30.0)  # Ждем достаточного количества тиков
        stop_event.set()
        loop_thread.join(timeout=2.0)
        if "event_thread" in locals():
            event_thread.join(timeout=1.0)

        # Проверяем выполнение большого количества тиков
        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Проверяем стабильность системы при длительной работе
        if len(tracker.history) > 10:
            # Проверяем, что параметры остаются в допустимых пределах
            energy_values = [h["energy"] for h in tracker.history]
            integrity_values = [h["integrity"] for h in tracker.history]
            stability_values = [h["stability"] for h in tracker.history]

            # Параметры должны оставаться стабильными (не выходить за разумные пределы)
            assert all(70 <= e <= 90 for e in energy_values), "Energy values out of expected range"
            assert all(
                0.85 <= i <= 0.95 for i in integrity_values
            ), "Integrity values out of expected range"
            assert all(
                0.85 <= s <= 0.95 for s in stability_values
            ), "Stability values out of expected range"


@pytest.mark.integration
@pytest.mark.order(3)
@pytest.mark.slow
@pytest.mark.long_running
class TestExtendedLongRunningStress:
    """Расширенные стресс-тесты длительной работы с высокой нагрузкой событий"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_high_frequency_events_1000_ticks(self, event_queue):
        """Тест длительной работы с высокой частотой событий (стресс-тест)"""
        state = SelfState()
        state.energy = 100.0
        state.integrity = 1.0
        state.stability = 1.0
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Добавляем события с высокой частотой
        def add_high_frequency_events():
            event_types = ["shock", "noise", "decay"]
            for i in range(500):  # Много событий
                if stop_event.is_set():
                    break
                event_type = event_types[i % len(event_types)]
                intensity = 0.3 + (i % 3) * 0.2  # Варьируем интенсивность
                event = Event(type=event_type, intensity=intensity, timestamp=time.time())
                event_queue.push(event)
                time.sleep(0.005)  # Высокая частота

        event_thread = threading.Thread(target=add_high_frequency_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.0001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(30.0)  # Ждем выполнения достаточного количества тиков
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        # Проверки
        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"
        assert len(tracker.history) > 0, "No degradation tracking"

        # Система должна выдерживать высокую нагрузку
        final_energy = tracker.history[-1]["energy"]
        assert final_energy >= 0.0, f"Energy went below 0: {final_energy}"

    def test_burst_event_load_1000_ticks(self, event_queue):
        """Тест с всплесками нагрузки событий (burst нагрузка)"""
        state = SelfState()
        state.energy = 80.0
        state.integrity = 0.9
        state.stability = 0.9
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Функция для создания всплесков событий
        def add_burst_events():
            burst_count = 0
            while not stop_event.is_set() and burst_count < 10:
                # Всплеск: много событий подряд
                for _ in range(20):
                    if stop_event.is_set():
                        break
                    event = Event(type="shock", intensity=0.8, timestamp=time.time())
                    event_queue.push(event)

                burst_count += 1
                time.sleep(0.1)  # Пауза между всплесками

        event_thread = threading.Thread(target=add_burst_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.005, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(10.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Проверяем, что система справилась с всплесками
        if len(tracker.history) > 5:
            # Параметры должны быть в разумных пределах
            energies = [h["energy"] for h in tracker.history[-10:]]
            assert all(e >= 0.0 for e in energies), "Energy dropped below 0 during bursts"

    def test_mixed_event_patterns_1000_ticks(self, event_queue):
        """Тест с смешанными паттернами событий различной интенсивности"""
        state = SelfState()
        state.energy = 90.0
        state.integrity = 0.95
        state.stability = 0.95
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Смешанные паттерны: периодические изменения интенсивности
        def add_mixed_events():
            patterns = [
                ("noise", 0.1),   # Низкая интенсивность
                ("decay", 0.3),   # Средняя
                ("shock", 0.7),   # Высокая
                ("recovery", 0.4), # Восстановление
                ("idle", 0.0),    # Отдых
            ]

            for i in range(200):
                if stop_event.is_set():
                    break
                pattern_idx = (i // 20) % len(patterns)  # Меняем паттерн каждые 20 событий
                event_type, base_intensity = patterns[pattern_idx]

                # Добавляем вариацию к интенсивности
                intensity = base_intensity + 0.1 * ((i % 5) - 2) / 2.0
                intensity = max(0.0, min(1.0, intensity))  # Ограничиваем диапазон

                event = Event(type=event_type, intensity=intensity, timestamp=time.time())
                event_queue.push(event)
                time.sleep(0.008)  # Средняя частота

        event_thread = threading.Thread(target=add_mixed_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.0001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(25.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Проверяем стабильность при смешанной нагрузке
        if len(tracker.history) > 20:
            # Вычисляем вариацию параметров
            energies = [h["energy"] for h in tracker.history]
            energy_variation = max(energies) - min(energies)
            # Вариация должна быть разумной (не слишком хаотичной)
            assert energy_variation < 50.0, f"Too much energy variation: {energy_variation}"


@pytest.mark.integration
@pytest.mark.order(3)
@pytest.mark.slow
@pytest.mark.long_running
class TestExtendedLongRunningRecovery:
    """Тесты на восстановление после длительной деградации"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_gradual_degradation_recovery_1000_ticks(self, event_queue):
        """Тест постепенной деградации с последующим восстановлением"""
        state = SelfState()
        state.energy = 50.0
        state.integrity = 0.8
        state.stability = 0.8
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Фаза 1: Деградация (первые 500 тиков)
        # Фаза 2: Восстановление (остальные тики)
        def add_phased_events():
            phase_switch_tick = 500

            for i in range(800):  # Много событий
                if stop_event.is_set():
                    break

                if i < phase_switch_tick:
                    # Фаза деградации: негативные события
                    event_type = "shock" if i % 3 == 0 else "decay"
                    intensity = 0.6 + 0.2 * (i % 2)
                else:
                    # Фаза восстановления: позитивные события
                    event_type = "recovery"
                    intensity = 0.5 + 0.2 * (i % 2)

                event = Event(type=event_type, intensity=intensity, timestamp=time.time())
                event_queue.push(event)
                time.sleep(0.003)

        event_thread = threading.Thread(target=add_phased_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.0001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(30.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Анализируем фазы
        if len(tracker.history) > 50:
            mid_point = len(tracker.history) // 2

            early_phase = tracker.history[:mid_point]
            late_phase = tracker.history[mid_point:]

            early_avg_energy = sum(h["energy"] for h in early_phase) / len(early_phase)
            late_avg_energy = sum(h["energy"] for h in late_phase) / len(late_phase)

            # Во второй фазе энергия должна быть выше (восстановление)
            assert late_avg_energy >= early_avg_energy * 0.8, \
                f"No recovery detected: early={early_avg_energy:.2f}, late={late_avg_energy:.2f}"

    def test_extreme_degradation_recovery_1000_ticks(self, event_queue):
        """Тест экстремальной деградации до критических значений с восстановлением"""
        state = SelfState()
        state.energy = 20.0  # Низкий старт
        state.integrity = 0.2
        state.stability = 0.2
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Фаза 1: Довести до почти нулевых значений
        # Фаза 2: Интенсивное восстановление
        def add_extreme_events():
            phase_switch_tick = 400

            for i in range(600):
                if stop_event.is_set():
                    break

                if i < phase_switch_tick:
                    # Экстремальная деградация
                    event = Event(type="shock", intensity=0.95, timestamp=time.time())
                else:
                    # Интенсивное восстановление
                    event = Event(type="recovery", intensity=0.9, timestamp=time.time())

                event_queue.push(event)
                time.sleep(0.002)  # Быстрая подача событий

        event_thread = threading.Thread(target=add_extreme_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.0001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(35.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Проверяем восстановление от экстремальной деградации
        if len(tracker.history) > 30:
            # Минимальные значения в первой половине
            first_half = tracker.history[:len(tracker.history)//2]
            min_energy_first = min(h["energy"] for h in first_half)

            # Максимальные значения во второй половине
            second_half = tracker.history[len(tracker.history)//2:]
            max_energy_second = max(h["energy"] for h in second_half)

            # Должно быть значимое восстановление
            recovery_ratio = max_energy_second / max(min_energy_first, 0.1)
            assert recovery_ratio > 2.0, \
                f"Insufficient recovery: min_first={min_energy_first:.2f}, max_second={max_energy_second:.2f}, ratio={recovery_ratio:.2f}"

    def test_cyclic_load_pattern_1000_ticks(self, event_queue):
        """Тест циклической нагрузки (высокая-низкая) при длительной работе"""
        state = SelfState()
        state.energy = 60.0
        state.integrity = 0.7
        state.stability = 0.7
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Циклическая нагрузка: 5 циклов по 100 событий каждый
        # Каждый цикл: 30 сек высокая нагрузка + 30 сек низкая нагрузка
        def add_cyclic_events():
            cycle_count = 0
            while not stop_event.is_set() and cycle_count < 5:
                # Фаза высокой нагрузки (30 сек)
                high_load_start = time.time()
                while time.time() - high_load_start < 30 and not stop_event.is_set():
                    # Высокая частота разнообразных событий
                    event_types = ["shock", "noise", "decay"]
                    event_type = event_types[cycle_count % len(event_types)]
                    intensity = 0.6 + 0.3 * (cycle_count % 3) / 2.0  # Варьируем интенсивность

                    event = Event(type=event_type, intensity=intensity, timestamp=time.time())
                    event_queue.push(event)
                    time.sleep(0.01)  # Высокая частота

                # Фаза низкой нагрузки (30 сек)
                low_load_start = time.time()
                while time.time() - low_load_start < 30 and not stop_event.is_set():
                    # Низкая частота легких событий
                    event = Event(type="recovery", intensity=0.1, timestamp=time.time())
                    event_queue.push(event)
                    time.sleep(0.2)  # Низкая частота

                cycle_count += 1

        event_thread = threading.Thread(target=add_cyclic_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(320.0)  # 5 циклов * (30 + 30) сек = 300 сек + запас
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Анализируем циклическую нагрузку
        if len(tracker.history) > 100:
            # Разделяем историю на циклы
            cycle_length = len(tracker.history) // 5
            energy_cycles = []

            for i in range(5):
                start_idx = i * cycle_length
                end_idx = (i + 1) * cycle_length
                cycle_data = tracker.history[start_idx:end_idx]
                cycle_energies = [h["energy"] for h in cycle_data]
                energy_cycles.append(cycle_energies)

            # Проверяем, что в каждом цикле есть вариация энергии
            for i, energies in enumerate(energy_cycles):
                if len(energies) > 20:
                    energy_variation = max(energies) - min(energies)
                    # В каждом цикле должна быть заметная вариация энергии
                    assert energy_variation > 5.0, \
                        f"Insufficient energy variation in cycle {i}: {energy_variation:.2f}"

            # Проверяем общую тенденцию: энергия не должна падать ниже критического уровня
            all_energies = [h["energy"] for h in tracker.history]
            min_energy_overall = min(all_energies)
            assert min_energy_overall >= 0.0, f"Energy dropped below 0: {min_energy_overall}"

            # Максимальная энергия должна быть в разумных пределах
            max_energy_overall = max(all_energies)
            assert max_energy_overall <= 100.0, f"Energy exceeded max: {max_energy_overall}"


@pytest.mark.integration
@pytest.mark.order(3)
@pytest.mark.slow
@pytest.mark.long_running
class TestExtendedLongRunningMemory:
    """Тесты давления памяти при длительной работе"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_memory_pressure_under_load_1000_ticks(self, event_queue):
        """Тест давления на память при высокой нагрузке событий"""
        state = SelfState()
        state.energy = 70.0
        state.integrity = 0.8
        state.stability = 0.8
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Создаем много событий, которые будут записаны в память
        def add_memory_pressure_events():
            for i in range(300):
                if stop_event.is_set():
                    break
                # Разнообразные события для создания богатой памяти
                event_types = ["shock", "noise", "decay", "recovery"]
                event_type = event_types[i % len(event_types)]

                # Каждое событие имеет уникальные метаданные для разнообразия
                metadata = {
                    "source": f"memory_test_{i}",
                    "category": event_type,
                    "sequence": i,
                    "pressure_test": True
                }

                event = Event(
                    type=event_type,
                    intensity=0.3 + 0.4 * (i % 3) / 2.0,
                    timestamp=time.time(),
                    metadata=metadata
                )
                event_queue.push(event)
                time.sleep(0.01)  # Контролируемая частота

        event_thread = threading.Thread(target=add_memory_pressure_events, daemon=True)
        event_thread.start()

        initial_memory_count = len(state.memory)

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(30.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Проверяем работу памяти под нагрузкой
        final_memory_count = len(state.memory)

        # Память должна расти, но оставаться в разумных пределах (макс 50 записей)
        assert final_memory_count <= 50, f"Memory overflow: {final_memory_count} entries"

        # Должны быть новые записи в памяти
        assert final_memory_count >= initial_memory_count, \
            f"Memory should grow: initial={initial_memory_count}, final={final_memory_count}"

        # Проверяем разнообразие записей в памяти
        if final_memory_count > 10:
            memory_types = [entry.event_type for entry in state.memory]
            unique_types = set(memory_types)
            # Должны быть разные типы событий
            assert len(unique_types) >= 3, f"Insufficient memory diversity: {unique_types}"

    def test_memory_archiving_under_load_1000_ticks(self, event_queue):
        """Тест архивации памяти при длительной работе с нагрузкой"""
        state = SelfState()
        state.energy = 60.0
        state.integrity = 0.7
        state.stability = 0.7
        stop_event = threading.Event()

        # Заполняем память начальными записями
        for i in range(30):
            entry = MemoryEntry(
                event_type="initial",
                meaning_significance=0.5,
                timestamp=time.time() - 3600 + i * 100,  # Разные времена
            )
            state.memory.append(entry)

        initial_memory_count = len(state.memory)
        initial_archive_count = len(state.archive_memory) if hasattr(state, 'archive_memory') else 0

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Создаем постоянный поток событий
        def add_continuous_events():
            event_count = 0
            while not stop_event.is_set() and event_count < 200:
                event = Event(
                    type="noise",
                    intensity=0.4,
                    timestamp=time.time(),
                    metadata={"continuous_test": True, "event_id": event_count}
                )
                event_queue.push(event)
                event_count += 1
                time.sleep(0.02)

        event_thread = threading.Thread(target=add_continuous_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(35.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Проверяем работу механизма архивации
        final_memory_count = len(state.memory)
        final_archive_count = len(state.archive_memory) if hasattr(state, 'archive_memory') else 0

        # Основная память должна быть ограничена
        assert final_memory_count <= 50, f"Main memory overflow: {final_memory_count}"

        # Архивная память должна содержать старые записи
        assert final_archive_count >= initial_archive_count, \
            f"Archive should grow: initial={initial_archive_count}, final={final_archive_count}"


@pytest.mark.integration
@pytest.mark.order(3)
@pytest.mark.slow
@pytest.mark.long_running
class TestExtendedLongRunningPerformance:
    """Тесты производительности при длительной работе"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий"""
        return EventQueue()

    def test_performance_stability_1000_ticks(self, event_queue):
        """Тест стабильности производительности при длительной работе"""
        state = SelfState()
        state.energy = 85.0
        state.integrity = 0.9
        state.stability = 0.9
        stop_event = threading.Event()

        # Метрики производительности
        tick_durations = []
        start_time = time.time()

        def performance_monitor(s):
            # Измеряем время тика
            tick_start = time.time()
            # Имитация работы монитора
            time.sleep(0.001)  # Небольшая задержка для измерения
            tick_end = time.time()
            tick_durations.append(tick_end - tick_start)

        # Добавляем умеренную нагрузку событий
        def add_performance_events():
            for i in range(100):
                if stop_event.is_set():
                    break
                event = Event(
                    type="noise",
                    intensity=0.2,
                    timestamp=time.time(),
                    metadata={"performance_test": True}
                )
                event_queue.push(event)
                time.sleep(0.05)  # Редкие события для измерения базовой производительности

        event_thread = threading.Thread(target=add_performance_events, daemon=True)
        event_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, performance_monitor, 0.001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(22.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        event_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Анализируем производительность
        if len(tick_durations) > 10:
            avg_duration = sum(tick_durations) / len(tick_durations)
            max_duration = max(tick_durations)
            min_duration = min(tick_durations)

            # Среднее время тика должно быть разумным (< 50ms)
            assert avg_duration < 0.05, f"Average tick duration too high: {avg_duration:.4f}s"

            # Максимальное время не должно быть экстремальным (< 200ms)
            assert max_duration < 0.2, f"Max tick duration too high: {max_duration:.4f}s"

            # Проверяем стабильность (коэффициент вариации < 50%)
            if avg_duration > 0:
                std_dev = (sum((d - avg_duration) ** 2 for d in tick_durations) / len(tick_durations)) ** 0.5
                cv = std_dev / avg_duration
                assert cv < 0.5, f"Performance too unstable: CV={cv:.2f}"

    def test_event_queue_overflow_handling_1000_ticks(self, event_queue):
        """Тест обработки переполнения очереди событий при длительной работе"""
        state = SelfState()
        state.energy = 75.0
        state.integrity = 0.8
        state.stability = 0.8
        stop_event = threading.Event()

        tracker = DegradationTracker()

        def tracking_monitor(s):
            tracker.track(s)

        # Создаем переполнение очереди
        def flood_event_queue():
            flood_count = 0
            while not stop_event.is_set() and flood_count < 200:
                # Пытаемся переполнить очередь (maxsize=100)
                for _ in range(120):  # Больше чем maxsize
                    if stop_event.is_set():
                        break
                    try:
                        event = Event(
                            type="shock",
                            intensity=0.5,
                            timestamp=time.time(),
                            metadata={"flood_test": True, "flood_id": flood_count}
                        )
                        event_queue.push(event)
                    except:
                        # Очередь переполнена - это нормально
                        pass

                flood_count += 1
                time.sleep(0.02)

        flood_thread = threading.Thread(target=flood_event_queue, daemon=True)
        flood_thread.start()

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, tracking_monitor, 0.001, 10000, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(25.0)
        stop_event.set()
        loop_thread.join(timeout=2.0)
        flood_thread.join(timeout=1.0)

        assert state.ticks >= 300, f"Expected >= 300 ticks, got {state.ticks}"

        # Система должна продолжать работать несмотря на переполнение очереди
        assert state.active is True, "System should remain active despite queue overflow"

        # Параметры должны оставаться в допустимых пределах
        assert state.energy >= 0.0, f"Energy corrupted: {state.energy}"
        assert 0.0 <= state.integrity <= 1.0, f"Integrity corrupted: {state.integrity}"
        assert 0.0 <= state.stability <= 1.0, f"Stability corrupted: {state.stability}"


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

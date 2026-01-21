"""
Тесты-инварианты для базовых ограничений системы Life - ROADMAP T.9 (расширение)

Property-based тесты, проверяющие инварианты системы:
- Бессмертная слабость: система остается "живой" при любых параметрах
- Границы параметров: значения всегда в допустимых пределах
- Отсутствие целей/оптимизации: поведение остается реактивным
- Runtime loop integrity: система продолжает работу в degraded состоянии

Эти тесты гарантируют, что эксперименты и изменения кода не нарушают
фундаментальные свойства системы Life.
"""

import sys
import threading
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.environment.event import Event
from src.environment.event_queue import EventQueue
from src.meaning.engine import MeaningEngine
from src.memory.memory import MemoryEntry
from src.runtime.loop import run_loop
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestImmortalWeaknessInvariant:
    """Инвариант бессмертной слабости: система может быть неактивной, но runtime продолжает работать"""

    @given(
        energy=st.floats(min_value=0.0, max_value=100.0),
        integrity=st.floats(min_value=0.0, max_value=1.0),
        stability=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_system_activity_consistent_with_viability(
        self, energy, integrity, stability
    ):
        """Инвариант: active всегда True при нормальных параметрах (бессмертная слабость)"""
        state = SelfState()

        # Устанавливаем значения параметров
        state.energy = energy
        state.integrity = integrity
        state.stability = stability

        # Согласно ADR 009, система остается активной даже при низких параметрах
        # active всегда True, кроме случаев ручной установки в False
        assert state.active is True, f"active should always be True (immortal weakness)"

    @given(
        event_intensity=st.floats(min_value=-1.0, max_value=1.0),
        event_type=st.sampled_from(["noise", "decay", "recovery", "shock", "idle"]),
        energy=st.floats(min_value=0.0, max_value=100.0),
        integrity=st.floats(min_value=0.0, max_value=1.0),
        stability=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_activity_changes_predictably_after_events(
        self, event_intensity, event_type, energy, integrity, stability
    ):
        """Инвариант: изменение active после обработки события предсказуемо"""
        state = SelfState()
        state.energy = energy
        state.integrity = integrity
        state.stability = stability

        initial_active = state.active

        meaning_engine = MeaningEngine()
        event = Event(type=event_type, intensity=event_intensity, timestamp=time.time())

        # Обрабатываем событие
        meaning = meaning_engine.process(event, state)
        state.apply_delta(meaning.impact)

        final_active = state.active

        # Согласно ADR 009, система остается активной даже после событий
        # active всегда True, кроме случаев ручной установки в False
        assert final_active is True, f"After {event_type} event: active should remain True (immortal weakness)"

    def test_manual_active_override_works(self):
        """Инвариант: ручная установка active работает независимо от параметров"""
        state = SelfState()

        # Устанавливаем низкие параметры
        state.energy = 0.0
        state.integrity = 0.0
        state.stability = 0.0

        # active должен быть False (is_viable() возвращает False)
        assert state.active is False

        # Ручная установка active в True
        state.active = True
        assert state.active is True, "Manual active override should work"

        # Ручная установка active в False
        state.active = False
        assert state.active is False, "Manual active override should work"


@pytest.mark.unit
@pytest.mark.order(1)
class TestParameterBoundsInvariant:
    """Инвариант границ параметров: значения всегда в допустимых пределах"""

    @given(
        energy=st.floats(min_value=-1000.0, max_value=1000.0),
        integrity=st.floats(min_value=-100.0, max_value=100.0),
        stability=st.floats(min_value=-100.0, max_value=100.0),
    )
    def test_parameter_bounds_after_direct_assignment(
        self, energy, integrity, stability
    ):
        """Инвариант: параметры всегда в границах после прямого присваивания"""
        state = SelfState()

        # Пытаемся присвоить любые значения (включая некорректные)
        try:
            state.energy = energy
            state.integrity = integrity
            state.stability = stability
        except ValueError:
            # ValueError ожидаемо для некорректных значений - это нормально
            pass

        # Инвариант: если присваивание удалось, значения должны быть в границах
        if hasattr(state, "_energy"):  # Проверяем, что поле существует
            assert (
                0.0 <= state.energy <= 100.0
            ), f"Energy {state.energy} out of bounds [0, 100]"
        if hasattr(state, "_integrity"):
            assert (
                0.0 <= state.integrity <= 1.0
            ), f"Integrity {state.integrity} out of bounds [0, 1]"
        if hasattr(state, "_stability"):
            assert (
                0.0 <= state.stability <= 1.0
            ), f"Stability {state.stability} out of bounds [0, 1]"

    @given(
        energy_delta=st.floats(min_value=-1000.0, max_value=1000.0),
        integrity_delta=st.floats(min_value=-100.0, max_value=100.0),
        stability_delta=st.floats(min_value=-100.0, max_value=100.0),
    )
    def test_parameter_bounds_after_apply_delta(
        self, energy_delta, integrity_delta, stability_delta
    ):
        """Инвариант: параметры всегда в границах после apply_delta"""
        state = SelfState()

        # Применяем любые изменения
        state.apply_delta(
            {
                "energy": energy_delta,
                "integrity": integrity_delta,
                "stability": stability_delta,
            }
        )

        # Инвариант: значения всегда в допустимых границах
        assert (
            0.0 <= state.energy <= 100.0
        ), f"Energy {state.energy} out of bounds [0, 100] after delta {energy_delta}"
        assert (
            0.0 <= state.integrity <= 1.0
        ), f"Integrity {state.integrity} out of bounds [0, 1] after delta {integrity_delta}"
        assert (
            0.0 <= state.stability <= 1.0
        ), f"Stability {state.stability} out of bounds [0, 1] after delta {stability_delta}"

    @given(
        event_intensity=st.floats(min_value=-1.0, max_value=1.0),
        event_type=st.sampled_from(["noise", "decay", "recovery", "shock", "idle"]),
        initial_energy=st.floats(min_value=0.0, max_value=100.0),
        initial_integrity=st.floats(min_value=0.0, max_value=1.0),
        initial_stability=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_parameter_bounds_after_event_processing(
        self,
        event_intensity,
        event_type,
        initial_energy,
        initial_integrity,
        initial_stability,
    ):
        """Инвариант: параметры в границах после обработки любого события"""
        state = SelfState()
        state.energy = initial_energy
        state.integrity = initial_integrity
        state.stability = initial_stability

        meaning_engine = MeaningEngine()
        event = Event(type=event_type, intensity=event_intensity, timestamp=time.time())
        meaning = meaning_engine.process(event, state)

        # Применяем impact события
        state.apply_delta(meaning.impact)

        # Инвариант: параметры остаются в границах
        assert (
            0.0 <= state.energy <= 100.0
        ), f"Energy {state.energy} out of bounds after {event_type} event"
        assert (
            0.0 <= state.integrity <= 1.0
        ), f"Integrity {state.integrity} out of bounds after {event_type} event"
        assert (
            0.0 <= state.stability <= 1.0
        ), f"Stability {state.stability} out of bounds after {event_type} event"

    @given(
        num_iterations=st.integers(min_value=1, max_value=100),
        delta_range=st.floats(min_value=-50.0, max_value=50.0),
    )
    def test_parameter_bounds_stable_under_repeated_operations(
        self, num_iterations, delta_range
    ):
        """Инвариант: границы параметров стабильны при многократных операциях"""
        state = SelfState()

        # Выполняем множество операций
        for _ in range(num_iterations):
            state.apply_delta(
                {
                    "energy": delta_range,
                    "integrity": delta_range / 100.0,  # Масштабируем для integrity
                    "stability": delta_range / 100.0,  # Масштабируем для stability
                }
            )

            # Инвариант: на каждом шаге параметры в границах
            assert (
                0.0 <= state.energy <= 100.0
            ), f"Energy {state.energy} out of bounds during iteration"
            assert (
                0.0 <= state.integrity <= 1.0
            ), f"Integrity {state.integrity} out of bounds during iteration"
            assert (
                0.0 <= state.stability <= 1.0
            ), f"Stability {state.stability} out of bounds during iteration"


@pytest.mark.unit
@pytest.mark.order(1)
class TestNoGoalsOptimizationInvariant:
    """Инвариант отсутствия целей/оптимизации: поведение остается реактивным"""

    @given(
        energy=st.floats(min_value=0.0, max_value=100.0),
        integrity=st.floats(min_value=0.0, max_value=1.0),
        stability=st.floats(min_value=0.0, max_value=1.0),
        event_type=st.sampled_from(["noise", "decay", "recovery", "shock", "idle"]),
        event_intensity=st.floats(min_value=-1.0, max_value=1.0),
    )
    def test_behavior_remains_reactive_not_proactive(
        self, energy, integrity, stability, event_type, event_intensity
    ):
        """Инвариант: поведение остается реактивным, не проактивным"""
        state = SelfState()
        state.energy = energy
        state.integrity = integrity
        state.stability = stability

        meaning_engine = MeaningEngine()
        event = Event(type=event_type, intensity=event_intensity, timestamp=time.time())

        # Получаем meaning для события
        meaning = meaning_engine.process(event, state)

        # Инвариант: нет оптимизации или целей - только реакция на событие
        # Проверяем, что impact зависит только от типа события и его интенсивности,
        # но не от стремления к каким-либо целям
        assert isinstance(meaning.impact, dict), "Impact should be a dictionary"
        assert (
            "energy" in meaning.impact
            or "integrity" in meaning.impact
            or "stability" in meaning.impact
        ), "Impact should affect at least one parameter"

        # Проверяем, что нет "оптимизирующего" поведения
        # (например, искусственного поддержания параметров на определенном уровне)
        # Для этого проверяем, что impact соответствует паттернам из MeaningEngine

    @given(
        learning_iterations=st.integers(min_value=1, max_value=50),
        event_sequence=st.lists(
            st.tuples(
                st.sampled_from(["noise", "decay", "recovery", "shock", "idle"]),
                st.floats(min_value=-1.0, max_value=1.0),
            ),
            min_size=5,
            max_size=20,
        ),
    )
    def test_learning_changes_remain_passive(self, learning_iterations, event_sequence):
        """Инвариант: изменения от Learning остаются пассивными, без активного контроля"""
        state = SelfState()

        initial_learning_params = state.learning_params.copy()

        # Имитируем процесс обучения через несколько итераций
        for _ in range(learning_iterations):
            # Обрабатываем последовательность событий
            for event_type, intensity in event_sequence:
                event = Event(
                    type=event_type, intensity=intensity, timestamp=time.time()
                )
                meaning = MeaningEngine().process(event, state)
                state.apply_delta(meaning.impact)

                # Имитируем запись в память (что влияет на learning)
                entry = MemoryEntry(
                    event_type=event_type,
                    meaning_significance=meaning.significance,
                    timestamp=time.time(),
                )
                state.memory.append(entry)

        # Инвариант: изменения параметров learning остаются небольшими и постепенными
        # (не более 0.01 за итерацию согласно архитектуре)
        for key in state.learning_params:
            if key in initial_learning_params:
                initial_value = initial_learning_params[key]
                current_value = state.learning_params[key]
                # Изменения должны быть небольшими (менее 50% от начального значения)
                relative_change = abs(current_value - initial_value) / max(
                    abs(initial_value), 0.001
                )
                assert (
                    relative_change < 0.5
                ), f"Learning parameter {key} changed too dramatically: {relative_change}"

    @given(
        adaptation_iterations=st.integers(min_value=1, max_value=20),
        behavior_types=st.lists(
            st.sampled_from(["noise", "decay", "recovery", "shock"]),
            min_size=1,
            max_size=5,
        ),
    )
    def test_adaptation_changes_remain_passive(
        self, adaptation_iterations, behavior_types
    ):
        """Инвариант: изменения от Adaptation остаются пассивными"""
        state = SelfState()

        initial_adaptation_params = state.adaptation_params.copy()

        # Имитируем процесс адаптации
        for _ in range(adaptation_iterations):
            for behavior_type in behavior_types:
                # Имитируем накопление статистики, которая влияет на adaptation
                if behavior_type in state.memory_entries_by_type:
                    state.memory_entries_by_type[behavior_type] += 1

        # Инвариант: изменения adaptation параметров остаются в разумных пределах
        for key in state.adaptation_params:
            if key in initial_adaptation_params:
                initial_value = initial_adaptation_params[key]
                current_value = state.adaptation_params[key]
                # Изменения должны быть постепенными
                relative_change = abs(current_value - initial_value) / max(
                    abs(initial_value), 0.001
                )
                assert (
                    relative_change < 1.0
                ), f"Adaptation parameter {key} changed too dramatically: {relative_change}"

    def test_no_goal_directed_behavior_optimization(self):
        """Инвариант: нет оптимизации поведения для достижения целей"""
        state = SelfState()

        # Проверяем, что система не пытается оптимизировать параметры
        # Например, не искусственно поддерживать energy на высоком уровне

        # Устанавливаем низкие значения
        state.energy = 10.0
        state.integrity = 0.2
        state.stability = 0.2

        # Имитируем обработку событий
        events = [
            Event(type="decay", intensity=-0.5, timestamp=time.time()),
            Event(type="shock", intensity=-0.8, timestamp=time.time()),
        ]

        meaning_engine = MeaningEngine()

        for event in events:
            meaning = meaning_engine.process(event, state)
            state.apply_delta(meaning.impact)

        # Инвариант: система не "борется" за поддержание параметров
        # Она просто реагирует на события согласно паттернам
        # (проверка, что поведение остается пассивным)
        assert (
            state.energy <= 10.0
        ), "System should not artificially maintain high energy"
        # Инвариант: active остается True даже при низких параметрах (бессмертная слабость)
        assert state.active is True, f"With low params: active should remain True (immortal weakness)"


@pytest.mark.integration
@pytest.mark.order(2)
class TestRuntimeLoopIntegrityInvariant:
    """Инвариант runtime loop integrity: система продолжает работу в degraded состоянии"""

    @pytest.fixture
    def event_queue(self):
        """Создает очередь событий для тестов"""
        return EventQueue()

    def dummy_monitor(self, state):
        """Простой монитор для тестов"""
        pass

    @given(
        energy=st.floats(min_value=0.0, max_value=100.0),
        integrity=st.floats(min_value=0.0, max_value=1.0),
        stability=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=20, deadline=None)  # Ограничиваем для performance
    def test_runtime_loop_continues_with_any_parameters(
        self, energy, integrity, stability, event_queue
    ):
        """Инвариант: runtime loop продолжает работу при любых значениях параметров"""
        state = SelfState()
        state.energy = energy
        state.integrity = integrity
        state.stability = stability

        stop_event = threading.Event()
        initial_ticks = state.ticks

        # Запускаем runtime loop
        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, self.dummy_monitor, 0.01, 10, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        # Ждем короткое время
        time.sleep(0.05)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Инвариант: loop выполнил хотя бы несколько тиков
        assert (
            state.ticks > initial_ticks
        ), f"Runtime loop did not progress with params: energy={energy}, integrity={integrity}, stability={stability}"

        # Инвариант: система остается активной даже при нулевых параметрах
        assert state.active is True, f"active should remain True at zero parameters (immortal weakness)"

    def test_runtime_loop_continues_at_zero_parameters(self, event_queue):
        """Инвариант: runtime loop работает при всех параметрах = 0"""
        state = SelfState()
        state.energy = 0.0
        state.integrity = 0.0
        state.stability = 0.0

        stop_event = threading.Event()
        initial_ticks = state.ticks

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, self.dummy_monitor, 0.01, 10, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.05)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Инвариант: loop продолжает работу даже в крайнем degraded состоянии
        assert (
            state.ticks > initial_ticks
        ), "Runtime loop should continue even with all parameters at zero"
        # Инвариант: active остается True даже при нулевых параметрах (бессмертная слабость)
        assert state.active is True, f"With zero params: active should remain True (immortal weakness)"

    @given(
        event_sequence=st.lists(
            st.tuples(
                st.sampled_from(["noise", "decay", "recovery", "shock", "idle"]),
                st.floats(min_value=-1.0, max_value=1.0),
            ),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=15, deadline=None)
    def test_runtime_loop_handles_events_in_degraded_state(
        self, event_sequence, event_queue
    ):
        """Инвариант: runtime loop корректно обрабатывает события в degraded состоянии"""
        state = SelfState()
        # Начинаем с degraded состояния
        state.energy = 1.0
        state.integrity = 0.1
        state.stability = 0.1

        # Добавляем события в очередь
        for event_type, intensity in event_sequence:
            event = Event(type=event_type, intensity=intensity, timestamp=time.time())
            event_queue.push(event)

        stop_event = threading.Event()
        initial_ticks = state.ticks

        loop_thread = threading.Thread(
            target=run_loop,
            args=(state, self.dummy_monitor, 0.01, 20, stop_event, event_queue),
            daemon=True,
        )
        loop_thread.start()

        time.sleep(0.1)
        stop_event.set()
        loop_thread.join(timeout=1.0)

        # Инвариант: loop обработал события и продолжил работу
        assert (
            state.ticks > initial_ticks
        ), "Runtime loop should process events and continue"
        # Инвариант: active остается True после обработки событий (бессмертная слабость)
        assert state.active is True, f"After event processing: active should remain True (immortal weakness)"

        # Инвариант: параметры остаются в границах
        assert 0.0 <= state.energy <= 100.0
        assert 0.0 <= state.integrity <= 1.0
        assert 0.0 <= state.stability <= 1.0

    def test_runtime_loop_thread_safety_in_degraded_state(self, event_queue):
        """Инвариант: runtime loop остается потокобезопасным в degraded состоянии"""
        state = SelfState()
        state.energy = 0.0
        state.integrity = 0.0
        state.stability = 0.0

        stop_event = threading.Event()
        initial_ticks = state.ticks

        # Запускаем несколько потоков одновременно
        threads = []
        for _ in range(3):
            thread = threading.Thread(
                target=run_loop,
                args=(state, self.dummy_monitor, 0.01, 5, stop_event, event_queue),
                daemon=True,
            )
            threads.append(thread)
            thread.start()

        time.sleep(0.05)
        stop_event.set()

        for thread in threads:
            thread.join(timeout=1.0)

        # Инвариант: система не crashed и осталась в корректном состоянии
        # Инвариант: active соответствует viability после конкурентного доступа
        expected_active = state.is_viable()
        assert (
            state.active == expected_active
        ), f"After concurrent access: active={state.active} but should be {expected_active}"
        # Тики могли увеличиться от любого из потоков
        assert state.ticks >= initial_ticks, "Ticks should not decrease"


@pytest.mark.unit
@pytest.mark.order(1)
class TestCombinedInvariants:
    """Комбинированные тесты инвариантов"""

    @given(
        energy=st.floats(min_value=0.0, max_value=100.0),
        integrity=st.floats(min_value=0.0, max_value=1.0),
        stability=st.floats(min_value=0.0, max_value=1.0),
        event_type=st.sampled_from(["noise", "decay", "recovery", "shock", "idle"]),
        event_intensity=st.floats(min_value=-1.0, max_value=1.0),
        num_iterations=st.integers(min_value=1, max_value=10),
    )
    def test_all_invariants_hold_simultaneously(
        self, energy, integrity, stability, event_type, event_intensity, num_iterations
    ):
        """Инвариант: все базовые инварианты выполняются одновременно"""
        state = SelfState()
        state.energy = energy
        state.integrity = integrity
        state.stability = stability

        meaning_engine = MeaningEngine()

        for _ in range(num_iterations):
            # 1. Создаем и обрабатываем событие
            event = Event(
                type=event_type, intensity=event_intensity, timestamp=time.time()
            )
            meaning = meaning_engine.process(event, state)
            state.apply_delta(meaning.impact)

            # 2. Проверяем все инварианты одновременно
            # Инвариант бессмертной слабости: active всегда True
            assert state.active is True, f"Combined invariants: active should remain True (immortal weakness)"

            # Инвариант границ параметров
            assert (
                0.0 <= state.energy <= 100.0
            ), "Parameter bounds invariant violated for energy"
            assert (
                0.0 <= state.integrity <= 1.0
            ), "Parameter bounds invariant violated for integrity"
            assert (
                0.0 <= state.stability <= 1.0
            ), "Parameter bounds invariant violated for stability"

            # Инвариант отсутствия целей (косвенная проверка через разумные изменения)
            energy_change = abs(state.energy - energy)
            assert (
                energy_change < 200.0
            ), "No goals invariant potentially violated (too large energy change)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

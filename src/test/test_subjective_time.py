import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.runtime.subjective_time import (
    compute_subjective_dt,
    compute_subjective_time_rate,
)
from src.state.self_state import SelfState


@pytest.mark.unit
@pytest.mark.order(1)
class TestSubjectiveTimeModel:
    def test_rate_is_clamped_to_range(self):
        state = SelfState()

        # extremes should still clamp
        rate_hi = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=10.0,
            stability_coeff=0.0,
            energy_coeff=1.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert (
            state.subjective_time_rate_min <= rate_hi <= state.subjective_time_rate_max
        )

        rate_lo = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.0,
            stability=0.0,
            energy=0.0,
            intensity_coeff=0.0,
            stability_coeff=10.0,  # strong negative via (stability-1)
            energy_coeff=1.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert (
            state.subjective_time_rate_min <= rate_lo <= state.subjective_time_rate_max
        )

    def test_subjective_time_is_monotonic_for_positive_dt(self):
        state = SelfState()

        cumulative = 0.0
        # A sequence of dt and varying signals; monotonicity must hold.
        steps = [
            (0.01, 0.0, 1.0),
            (0.02, 0.3, 0.9),
            (0.01, 1.0, 0.2),
            (0.05, 0.0, 1.0),
        ]
        for dt, intensity, stability in steps:
            inc = compute_subjective_dt(
                dt=dt,
                base_rate=state.subjective_time_base_rate,
                intensity=intensity,
                stability=stability,
                energy=50.0,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                energy_coeff=state.subjective_time_energy_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )
            assert inc >= 0.0
            prev = cumulative
            cumulative += inc
            assert cumulative >= prev

    def test_intensity_and_stability_influence_rate_direction(self):
        state = SelfState()

        # intensity up -> rate up
        rate_low_int = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.1,
            stability=1.0,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        rate_high_int = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.9,
            stability=1.0,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_high_int > rate_low_int

        # stability down -> rate down (by design)
        rate_stable = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=1.0,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        rate_unstable = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.2,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_unstable < rate_stable

    def test_negative_dt_returns_zero_increment(self):
        """Тест на отрицательные значения dt - должны возвращать 0"""
        state = SelfState()

        # Отрицательные dt должны возвращать 0
        inc = compute_subjective_dt(
            dt=-0.1,
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.5,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert inc == 0.0

        # Нулевой dt должен возвращать 0
        inc_zero = compute_subjective_dt(
            dt=0.0,
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.5,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert inc_zero == 0.0

    def test_extreme_intensity_and_stability_values(self):
        """Тест на экстремальные значения intensity и stability"""
        state = SelfState()

        # Максимальные значения
        rate_max = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=10.0,  # Большой коэффициент
            stability_coeff=0.0,
            energy_coeff=1.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_max == state.subjective_time_rate_max

        # Минимальные значения
        rate_min = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.0,
            stability=0.0,
            energy=0.0,
            intensity_coeff=0.0,
            stability_coeff=10.0,  # Большой коэффициент для негативного эффекта
            energy_coeff=1.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_min == state.subjective_time_rate_min

        # Значения за пределами [0,1] должны быть clamped
        rate_clamped_high = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=2.0,  # > 1.0
            stability=1.0,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert (
            state.subjective_time_rate_min
            <= rate_clamped_high
            <= state.subjective_time_rate_max
        )

        rate_clamped_low = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=-1.0,  # < 0.0
            stability=1.0,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert (
            state.subjective_time_rate_min
            <= rate_clamped_low
            <= state.subjective_time_rate_max
        )

    def test_boundary_rate_min_max_values(self):
        """Тест на граничные значения rate_min и rate_max"""
        # rate_min = 0 (экстремальный случай)
        rate_zero_min = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.0,
            stability=0.0,
            energy=0.0,
            intensity_coeff=1.0,
            stability_coeff=1.0,
            energy_coeff=1.0,
            rate_min=0.0,  # Минимально возможное
            rate_max=3.0,
        )
        assert rate_zero_min >= 0.0

        # rate_max очень большой
        rate_big_max = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=1.0,
            stability_coeff=0.0,
            energy_coeff=1.0,
            rate_min=0.1,
            rate_max=100.0,  # Очень большой максимум
        )
        assert rate_big_max <= 100.0

        # rate_min > rate_max (некорректная конфигурация)
        rate_invalid_range = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.5,
            stability=0.5,
            energy=50.0,
            intensity_coeff=1.0,
            stability_coeff=1.0,
            energy_coeff=1.0,
            rate_min=2.0,  # min > max
            rate_max=1.0,
        )
        # Функция должна обработать некорректный диапазон (вернуть base_rate или clamped значение)
        assert isinstance(rate_invalid_range, float)

    def test_invalid_input_types(self):
        """Тест на некорректные типы входных данных"""
        state = SelfState()

        # Некорректные типы для intensity/stability - должны быть обработаны clamp/float
        # но некорвертируемые строки должны вызывать исключения
        with pytest.raises((ValueError, TypeError)):
            compute_subjective_time_rate(
                base_rate=state.subjective_time_base_rate,
                intensity="abc",  # некорректная строка
                stability=0.5,
                energy=50.0,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                energy_coeff=state.subjective_time_energy_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

        with pytest.raises((ValueError, TypeError)):
            compute_subjective_time_rate(
                base_rate=state.subjective_time_base_rate,
                intensity=0.5,
                stability="invalid",  # некорректная строка
                energy=50.0,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                energy_coeff=state.subjective_time_energy_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

        # None должен вызывать TypeError
        with pytest.raises((TypeError, AttributeError)):
            compute_subjective_time_rate(
                base_rate=state.subjective_time_base_rate,
                intensity=None,  # None вместо числа
                stability=0.5,
                energy=50.0,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                energy_coeff=state.subjective_time_energy_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

        # Некорректные типы для dt
        with pytest.raises((ValueError, TypeError)):
            compute_subjective_dt(
                dt="invalid",  # некорректная строка
                base_rate=state.subjective_time_base_rate,
                intensity=0.5,
                stability=0.5,
                energy=50.0,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                energy_coeff=state.subjective_time_energy_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

        # Но валидные строки должны конвертироваться
        rate_from_string = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity="0.5",  # валидная строка
            stability=0.3,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert isinstance(rate_from_string, float)
        assert (
            state.subjective_time_rate_min
            <= rate_from_string
            <= state.subjective_time_rate_max
        )

    def test_extreme_coefficient_values(self):
        """Тест на экстремальные значения коэффициентов"""
        state = SelfState()

        # Нулевые коэффициенты
        rate_zero_coeffs = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=1.0,
            stability=0.0,
            energy=50.0,
            intensity_coeff=0.0,
            stability_coeff=0.0,
            energy_coeff=0.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert (
            rate_zero_coeffs == state.subjective_time_base_rate
        )  # Должен вернуться base_rate

        # Очень большие коэффициенты
        rate_big_coeffs = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.1,
            stability=0.9,
            energy=50.0,
            intensity_coeff=100.0,  # Очень большой коэффициент
            stability_coeff=-50.0,  # Отрицательный коэффициент
            energy_coeff=1.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        # Должен быть clamped к границам
        assert (
            state.subjective_time_rate_min
            <= rate_big_coeffs
            <= state.subjective_time_rate_max
        )

    def test_zero_and_negative_base_rate(self):
        """Тест на нулевой и отрицательный base_rate"""
        # state = SelfState()

        # Нулевой base_rate
        rate_zero_base = compute_subjective_time_rate(
            base_rate=0.0,
            intensity=0.5,
            stability=0.5,
            energy=50.0,
            intensity_coeff=1.0,
            stability_coeff=1.0,
            energy_coeff=1.0,
            rate_min=0.0,
            rate_max=3.0,
        )
        assert rate_zero_base >= 0.0  # Не должен быть отрицательным

        # Отрицательный base_rate
        rate_negative_base = compute_subjective_time_rate(
            base_rate=-1.0,
            intensity=0.5,
            stability=0.5,
            energy=50.0,
            intensity_coeff=1.0,
            stability_coeff=1.0,
            energy_coeff=1.0,
            rate_min=0.0,
            rate_max=3.0,
        )
        assert rate_negative_base >= 0.0  # Должен быть clamped к min


@pytest.mark.integration
class TestSubjectiveTimeIntegration:
    """Интеграционные тесты субъективного времени"""

    def test_subjective_time_memory_integration(self):
        """Тест интеграции субъективного времени с Memory"""
        from src.memory.memory import MemoryEntry

        state = SelfState()
        state.subjective_time = 10.0

        # Создаем записи памяти с субъективным временем
        entries = []
        for i in range(3):
            entry = MemoryEntry(
                event_type="noise",
                meaning_significance=0.3 + i * 0.1,
                timestamp=1000.0 + i,
                subjective_timestamp=state.subjective_time + i * 0.5,
            )
            entries.append(entry)

        # Проверяем, что субъективное время записано корректно
        for i, entry in enumerate(entries):
            expected_subjective = 10.0 + i * 0.5
            assert entry.subjective_timestamp == expected_subjective

        # Проверяем монотонность
        subjective_times = [entry.subjective_timestamp for entry in entries]
        assert subjective_times == sorted(subjective_times)

    def test_subjective_time_with_runtime_loop_simulation(self):
        """Тест субъективного времени в симуляции runtime loop"""
        from src.runtime.subjective_time import compute_subjective_dt

        state = SelfState()
        initial_subjective = 0.0
        state.subjective_time = initial_subjective

        # Симулируем несколько тиков
        total_physical_time = 0.0
        total_subjective_time = 0.0

        for tick in range(10):
            dt = 0.1  # 0.1 секунды на тик

            # Имитируем разные уровни интенсивности
            intensity = min(0.1 * tick, 1.0)  # Растущая интенсивность
            stability = max(0.1, 0.9 - 0.05 * tick)  # Падающая стабильность

            subjective_dt = compute_subjective_dt(
                dt=dt,
                base_rate=state.subjective_time_base_rate,
                intensity=intensity,
                stability=stability,
                energy=state.energy,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                energy_coeff=state.subjective_time_energy_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

            total_physical_time += dt
            total_subjective_time += subjective_dt
            state.subjective_time += subjective_dt

        # Общее субъективное время должно быть положительным
        assert total_subjective_time > 0
        assert state.subjective_time > initial_subjective

        # Субъективное время должно быть не больше физического
        # (из-за ограничений rate_max)
        assert (
            total_subjective_time
            <= total_physical_time * state.subjective_time_rate_max
        )

    def test_subjective_time_feedback_integration(self):
        """Тест интеграции субъективного времени с Feedback"""
        from src.feedback import register_action

        state = SelfState()
        state.subjective_time = 5.0

        # Регистрируем действие
        action_id = "test_action"
        register_action(
            action_id=action_id,
            action_pattern="dampen",
            state_before={"energy": 100.0, "stability": 1.0},
            timestamp=1000.0,
            pending_actions=[],
        )

        # Проверяем, что система готова к работе с субъективным временем
        assert hasattr(state, "subjective_time")
        assert state.subjective_time == 5.0

        # Имитируем обработку Feedback в runtime loop
        # (в реальном коде это происходит в loop.py)
        if hasattr(state, "memory"):
            # Ищем Feedback записи
            feedback_entries = [
                entry for entry in state.memory if entry.event_type == "feedback"
            ]

            # Если есть Feedback, проверяем что subjective_timestamp может быть установлен
            for entry in feedback_entries:
                if hasattr(entry, "subjective_timestamp"):
                    # В реальном коде subjective_timestamp устанавливается при создании
                    assert entry.subjective_timestamp is not None

    def test_subjective_time_rate_adaptation(self):
        """Тест адаптации скорости субъективного времени"""
        from src.runtime.subjective_time import compute_subjective_time_rate

        state = SelfState()

        # Тестируем разные состояния системы
        test_cases = [
            # (intensity, stability, energy, description)
            (0.0, 1.0, 100.0, "Спокойное состояние"),
            (0.5, 0.8, 80.0, "Умеренная активность"),
            (1.0, 0.2, 30.0, "Кризисное состояние"),
            (0.8, 0.9, 60.0, "Высокая интенсивность при хорошей стабильности"),
        ]

        rates = []
        for intensity, stability, energy, desc in test_cases:
            rate = compute_subjective_time_rate(
                base_rate=state.subjective_time_base_rate,
                intensity=intensity,
                stability=stability,
                energy=energy,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                energy_coeff=state.subjective_time_energy_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )
            rates.append((rate, desc))

            # Проверяем границы
            assert (
                state.subjective_time_rate_min <= rate <= state.subjective_time_rate_max
            )

        # Все скорости должны быть в разумных пределах
        for rate, desc in rates:
            assert (
                0.1 <= rate <= 3.0
            ), f"Скорость {rate} для '{desc}' вне разумных пределов"

    def test_subjective_time_persistence_in_snapshots(self):
        """Тест сохранения субъективного времени в снапшотах"""
        from src.state.self_state import load_snapshot, save_snapshot

        state = SelfState()
        state.subjective_time = 42.5
        state.ticks = 100

        # Сохраняем состояние
        save_snapshot(state)

        # Загружаем состояние
        loaded_state = load_snapshot(100)

        # Проверяем, что субъективное время сохранилось
        assert hasattr(loaded_state, "subjective_time")
        assert loaded_state.subjective_time == 42.5

    def test_subjective_time_edge_cases(self):
        """Тест граничных случаев субъективного времени"""
        from src.runtime.subjective_time import (
            compute_subjective_dt,
            compute_subjective_time_rate,
        )

        state = SelfState()

        # Тест с экстремально низкой энергией
        rate_low_energy = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.5,
            energy=0.001,  # Почти нулевая энергия
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )

        # Должен быть clamped к минимальному значению
        assert rate_low_energy >= state.subjective_time_rate_min

        # Тест с очень большим dt
        big_dt = compute_subjective_dt(
            dt=100.0,  # Очень большой временной интервал
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.5,
            energy=50.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            energy_coeff=state.subjective_time_energy_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )

        # Результат должен быть разумным (не бесконечность)
        assert 0 <= big_dt <= 100.0 * state.subjective_time_rate_max

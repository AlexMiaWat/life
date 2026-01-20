import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from src.runtime.subjective_time import compute_subjective_dt, compute_subjective_time_rate
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
            intensity_coeff=10.0,
            stability_coeff=0.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert state.subjective_time_rate_min <= rate_hi <= state.subjective_time_rate_max

        rate_lo = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.0,
            stability=0.0,
            intensity_coeff=0.0,
            stability_coeff=10.0,  # strong negative via (stability-1)
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert state.subjective_time_rate_min <= rate_lo <= state.subjective_time_rate_max

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
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
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
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        rate_high_int = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.9,
            stability=1.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_high_int > rate_low_int

        # stability down -> rate down (by design)
        rate_stable = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=1.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        rate_unstable = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.5,
            stability=0.2,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
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
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
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
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
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
            intensity_coeff=10.0,  # Большой коэффициент
            stability_coeff=0.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_max == state.subjective_time_rate_max

        # Минимальные значения
        rate_min = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.0,
            stability=0.0,
            intensity_coeff=0.0,
            stability_coeff=10.0,  # Большой коэффициент для негативного эффекта
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_min == state.subjective_time_rate_min

        # Значения за пределами [0,1] должны быть clamped
        rate_clamped_high = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=2.0,  # > 1.0
            stability=1.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert state.subjective_time_rate_min <= rate_clamped_high <= state.subjective_time_rate_max

        rate_clamped_low = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=-1.0,  # < 0.0
            stability=1.0,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert state.subjective_time_rate_min <= rate_clamped_low <= state.subjective_time_rate_max

    def test_boundary_rate_min_max_values(self):
        """Тест на граничные значения rate_min и rate_max"""
        # rate_min = 0 (экстремальный случай)
        rate_zero_min = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.0,
            stability=0.0,
            intensity_coeff=1.0,
            stability_coeff=1.0,
            rate_min=0.0,  # Минимально возможное
            rate_max=3.0,
        )
        assert rate_zero_min >= 0.0

        # rate_max очень большой
        rate_big_max = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=1.0,
            stability=1.0,
            intensity_coeff=1.0,
            stability_coeff=0.0,
            rate_min=0.1,
            rate_max=100.0,  # Очень большой максимум
        )
        assert rate_big_max <= 100.0

        # rate_min > rate_max (некорректная конфигурация)
        rate_invalid_range = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.5,
            stability=0.5,
            intensity_coeff=1.0,
            stability_coeff=1.0,
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
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

        with pytest.raises((ValueError, TypeError)):
            compute_subjective_time_rate(
                base_rate=state.subjective_time_base_rate,
                intensity=0.5,
                stability="invalid",  # некорректная строка
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

        # None должен вызывать TypeError
        with pytest.raises((TypeError, AttributeError)):
            compute_subjective_time_rate(
                base_rate=state.subjective_time_base_rate,
                intensity=None,  # None вместо числа
                stability=0.5,
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
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
                intensity_coeff=state.subjective_time_intensity_coeff,
                stability_coeff=state.subjective_time_stability_coeff,
                rate_min=state.subjective_time_rate_min,
                rate_max=state.subjective_time_rate_max,
            )

        # Но валидные строки должны конвертироваться
        rate_from_string = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity="0.5",  # валидная строка
            stability=0.3,
            intensity_coeff=state.subjective_time_intensity_coeff,
            stability_coeff=state.subjective_time_stability_coeff,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert isinstance(rate_from_string, float)
        assert state.subjective_time_rate_min <= rate_from_string <= state.subjective_time_rate_max

    def test_extreme_coefficient_values(self):
        """Тест на экстремальные значения коэффициентов"""
        state = SelfState()

        # Нулевые коэффициенты
        rate_zero_coeffs = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=1.0,
            stability=0.0,
            intensity_coeff=0.0,
            stability_coeff=0.0,
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        assert rate_zero_coeffs == state.subjective_time_base_rate  # Должен вернуться base_rate

        # Очень большие коэффициенты
        rate_big_coeffs = compute_subjective_time_rate(
            base_rate=state.subjective_time_base_rate,
            intensity=0.1,
            stability=0.9,
            intensity_coeff=100.0,  # Очень большой коэффициент
            stability_coeff=-50.0,  # Отрицательный коэффициент
            rate_min=state.subjective_time_rate_min,
            rate_max=state.subjective_time_rate_max,
        )
        # Должен быть clamped к границам
        assert state.subjective_time_rate_min <= rate_big_coeffs <= state.subjective_time_rate_max

    def test_zero_and_negative_base_rate(self):
        """Тест на нулевой и отрицательный base_rate"""
        state = SelfState()

        # Нулевой base_rate
        rate_zero_base = compute_subjective_time_rate(
            base_rate=0.0,
            intensity=0.5,
            stability=0.5,
            intensity_coeff=1.0,
            stability_coeff=1.0,
            rate_min=0.0,
            rate_max=3.0,
        )
        assert rate_zero_base >= 0.0  # Не должен быть отрицательным

        # Отрицательный base_rate
        rate_negative_base = compute_subjective_time_rate(
            base_rate=-1.0,
            intensity=0.5,
            stability=0.5,
            intensity_coeff=1.0,
            stability_coeff=1.0,
            rate_min=0.0,
            rate_max=3.0,
        )
        assert rate_negative_base >= 0.0  # Должен быть clamped к min


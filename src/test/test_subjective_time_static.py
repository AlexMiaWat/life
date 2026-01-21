"""
Статические тесты для модуля субъективного времени.

Тестируют математические функции и логику без зависимостей от внешних компонентов.
"""

import pytest
from src.runtime.subjective_time import (
    clamp,
    compute_subjective_time_rate,
    compute_subjective_dt,
)


class TestClamp:
    """Тесты для функции clamp."""

    def test_clamp_within_bounds(self):
        """Тест clamp для значений внутри границ."""
        assert clamp(5.0, 0.0, 10.0) == 5.0
        assert clamp(0.5, 0.0, 1.0) == 0.5
        assert clamp(50, 0, 100) == 50

    def test_clamp_below_minimum(self):
        """Тест clamp для значений ниже минимума."""
        assert clamp(-1.0, 0.0, 10.0) == 0.0
        assert clamp(-5, 0, 100) == 0
        assert clamp(-0.1, 0.0, 1.0) == 0.0

    def test_clamp_above_maximum(self):
        """Тест clamp для значений выше максимума."""
        assert clamp(15.0, 0.0, 10.0) == 10.0
        assert clamp(150, 0, 100) == 100
        assert clamp(1.1, 0.0, 1.0) == 1.0

    def test_clamp_edge_cases(self):
        """Тест clamp для граничных случаев."""
        assert clamp(0.0, 0.0, 10.0) == 0.0
        assert clamp(10.0, 0.0, 10.0) == 10.0
        assert clamp(0, 0, 0) == 0


class TestComputeSubjectiveTimeRate:
    """Тесты для функции compute_subjective_time_rate."""

    def test_base_rate_only(self):
        """Тест с только базовой скоростью."""
        rate = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # При intensity=0, stability=1, energy=1.0: rate = 1.0 + 0 + 0.2*(1-1) + 0.05*1.0 = 1.05
        assert abs(rate - 1.05) < 0.001

    def test_high_intensity_acceleration(self):
        """Тест ускорения при высокой интенсивности."""
        rate = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # При intensity=1, stability=1, energy=1.0: rate = 1.0 + 0.1*1.0 + 0.2*(1-1) + 0.05*1.0 = 1.15
        assert abs(rate - 1.15) < 0.001

    def test_low_stability_deceleration(self):
        """Тест замедления при низкой стабильности."""
        rate = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.0,
            stability=0.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # При intensity=0, stability=0, energy=1.0: rate = 1.0 + 0 + 0.2*(0-1) + 0.05*1.0 = 0.85
        assert abs(rate - 0.85) < 0.001

    def test_high_energy_acceleration(self):
        """Тест ускорения при высокой энергии."""
        rate = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # При intensity=0, stability=1, energy=1.0: rate = 1.0 + 0 + 0 + 0.05*1.0 = 1.05
        assert abs(rate - 1.05) < 0.001

    def test_rate_clamping_minimum(self):
        """Тест ограничения скорости снизу."""
        rate = compute_subjective_time_rate(
            base_rate=0.05,
            intensity=0.0,
            stability=0.0,
            energy=0.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # rate = 0.05 + 0 + 0.2*(0-1) + 0.05*0 = -0.15, но clamp к 0.1
        assert rate == 0.1

    def test_rate_clamping_maximum(self):
        """Тест ограничения скорости сверху."""
        rate = compute_subjective_time_rate(
            base_rate=2.5,
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # rate = 2.5 + 0.1 + 0 + 0.05 = 2.65, но clamp к 2.0
        assert rate == 2.0

    def test_intensity_clamping(self):
        """Тест автоматического ограничения интенсивности."""
        rate = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=2.0,  # Будет ограничено до 1.0
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # intensity ограничена до 1.0: rate = 1.0 + 0.1*1.0 + 0 + 0.05*1.0 = 1.15
        assert abs(rate - 1.15) < 0.001

    def test_energy_normalization(self):
        """Тест нормализации энергии."""
        rate = compute_subjective_time_rate(
            base_rate=1.0,
            intensity=0.0,
            stability=1.0,
            energy=50.0,  # Будет нормализовано к 0.5
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # energy нормализована: 50/100 = 0.5: rate = 1.0 + 0 + 0 + 0.05*0.5 = 1.025
        assert abs(rate - 1.025) < 0.001


class TestComputeSubjectiveDt:
    """Тесты для функции compute_subjective_dt."""

    def test_zero_dt(self):
        """Тест с нулевым dt."""
        dt = compute_subjective_dt(
            dt=0.0,
            base_rate=1.0,
            intensity=0.5,
            stability=0.8,
            energy=80.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        assert dt == 0.0

    def test_negative_dt(self):
        """Тест с отрицательным dt (должен быть ограничен к 0)."""
        dt = compute_subjective_dt(
            dt=-1.0,
            base_rate=1.0,
            intensity=0.5,
            stability=0.8,
            energy=80.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        assert dt == 0.0

    def test_normal_dt_calculation(self):
        """Тест нормального расчета dt."""
        dt = compute_subjective_dt(
            dt=1.0,
            base_rate=1.0,
            intensity=0.5,
            stability=0.8,
            energy=80.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # rate = 1.0 + 0.1*0.5 + 0.2*(0.8-1) + 0.05*(80/100) = 1.0 + 0.05 - 0.04 + 0.04 = 1.05
        # dt = 1.0 * 1.05 = 1.05
        assert abs(dt - 1.05) < 0.001

    def test_dt_with_different_rates(self):
        """Тест с разными скоростями."""
        # Быстрая скорость
        dt_fast = compute_subjective_dt(
            dt=2.0,
            base_rate=1.5,
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )

        # Медленная скорость
        dt_slow = compute_subjective_dt(
            dt=2.0,
            base_rate=0.5,
            intensity=0.0,
            stability=0.0,
            energy=0.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )

        # Быстрая скорость должна дать больший результат
        assert dt_fast > dt_slow
        assert dt_fast > 2.0  # Увеличение
        assert dt_slow < 2.0  # Уменьшение

    def test_dt_with_clamped_rate(self):
        """Тест с ограниченной скоростью."""
        dt = compute_subjective_dt(
            dt=1.0,
            base_rate=3.0,  # Выше максимума
            intensity=1.0,
            stability=1.0,
            energy=100.0,
            intensity_coeff=0.1,
            stability_coeff=0.2,
            energy_coeff=0.05,
            rate_min=0.1,
            rate_max=2.0,
        )
        # rate будет ограничена до 2.0
        assert abs(dt - 2.0) < 0.001  # 1.0 * 2.0 = 2.0


class TestSubjectiveTimeIntegration:
    """Интеграционные тесты для функций субъективного времени."""

    def test_rate_and_dt_consistency(self):
        """Тест согласованности между rate и dt функциями."""
        params = {
            "base_rate": 1.2,
            "intensity": 0.7,
            "stability": 0.6,
            "energy": 70.0,
            "intensity_coeff": 0.15,
            "stability_coeff": 0.25,
            "energy_coeff": 0.08,
            "rate_min": 0.2,
            "rate_max": 3.0,
        }

        rate = compute_subjective_time_rate(**params)
        dt = compute_subjective_dt(dt=1.5, **params)

        # dt должно быть равно dt * rate
        expected_dt = 1.5 * rate
        assert abs(dt - expected_dt) < 0.001

    def test_realistic_scenarios(self):
        """Тест реалистичных сценариев."""
        scenarios = [
            # Высокая интенсивность - ускорение
            {
                "name": "high_intensity",
                "params": {
                    "dt": 1.0,
                    "base_rate": 1.0,
                    "intensity": 0.9,
                    "stability": 0.8,
                    "energy": 85.0,
                    "intensity_coeff": 0.1,
                    "stability_coeff": 0.2,
                    "energy_coeff": 0.05,
                    "rate_min": 0.1,
                    "rate_max": 2.0,
                },
                "expected_range": (1.08, 1.3),
            },
            # Низкая стабильность - замедление
            {
                "name": "low_stability",
                "params": {
                    "dt": 1.0,
                    "base_rate": 1.0,
                    "intensity": 0.2,
                    "stability": 0.3,
                    "energy": 60.0,
                    "intensity_coeff": 0.1,
                    "stability_coeff": 0.2,
                    "energy_coeff": 0.05,
                    "rate_min": 0.1,
                    "rate_max": 2.0,
                },
                "expected_range": (0.8, 1.0),
            },
            # Высокая энергия - ускорение
            {
                "name": "high_energy",
                "params": {
                    "dt": 1.0,
                    "base_rate": 1.0,
                    "intensity": 0.4,
                    "stability": 0.9,
                    "energy": 95.0,
                    "intensity_coeff": 0.1,
                    "stability_coeff": 0.2,
                    "energy_coeff": 0.05,
                    "rate_min": 0.1,
                    "rate_max": 2.0,
                },
                "expected_range": (1.0, 1.2),
            },
        ]

        for scenario in scenarios:
            dt = compute_subjective_dt(**scenario["params"])
            min_val, max_val = scenario["expected_range"]
            assert min_val <= dt <= max_val, f"Scenario {scenario['name']} failed: dt={dt}"

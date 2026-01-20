"""
Subjective time model.

Goal: provide a deterministic, monotonic mapping from (dt, state, signals) to
subjective time increment. Subjective time is a *metric* (not a control loop).
"""

from __future__ import annotations


def clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def compute_subjective_time_rate(
    *,
    base_rate: float,
    intensity: float,
    stability: float,
    energy: float,
    intensity_coeff: float,
    stability_coeff: float,
    energy_coeff: float,
    rate_min: float,
    rate_max: float,
) -> float:
    """
    Compute subjective time rate multiplier.

    Design:
    - higher intensity -> faster subjective time (positive effect)
    - lower stability -> slower subjective time (negative effect)
    - higher energy -> faster subjective time (positive effect)
    - rate is clamped to [rate_min, rate_max]
    """
    intensity = clamp(float(intensity), 0.0, 1.0)
    stability = clamp(float(stability), 0.0, 1.0)
    energy_normalized = clamp(float(energy) / 100.0, 0.0, 1.0)  # normalize energy to [0,1]

    # stability term: stability=1 => 0; stability<1 => negative contribution
    stability_term = stability_coeff * (stability - 1.0)
    # energy term: higher energy -> faster subjective time (positive contribution)
    energy_term = energy_coeff * energy_normalized

    rate = base_rate + intensity_coeff * intensity + stability_term + energy_term
    return clamp(rate, float(rate_min), float(rate_max))


def compute_subjective_dt(
    *,
    dt: float,
    base_rate: float,
    intensity: float,
    stability: float,
    energy: float,
    intensity_coeff: float,
    stability_coeff: float,
    energy_coeff: float,
    rate_min: float,
    rate_max: float,
) -> float:
    """Compute subjective time increment (seconds) for a physical dt (seconds)."""
    dt = max(0.0, float(dt))
    rate = compute_subjective_time_rate(
        base_rate=base_rate,
        intensity=intensity,
        stability=stability,
        energy=energy,
        intensity_coeff=intensity_coeff,
        stability_coeff=stability_coeff,
        energy_coeff=energy_coeff,
        rate_min=rate_min,
        rate_max=rate_max,
    )
    return dt * rate


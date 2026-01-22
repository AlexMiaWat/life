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
    circadian_phase: float = 0.0,
    recovery_efficiency: float = 1.0,
) -> float:
    """
    Compute subjective time rate multiplier with circadian rhythm influence.

    Design:
    - higher intensity -> faster subjective time (positive effect)
    - lower stability -> slower subjective time (negative effect)
    - higher energy -> faster subjective time (positive effect)
    - circadian rhythm strongly affects time perception:
      * Day (circadian_phase ~π): faster subjective time (активность)
      * Night (circadian_phase ~0 or 2π): slower subjective time (отдых)
    - rate is clamped to [rate_min, rate_max]
    """
    import math

    intensity = clamp(float(intensity), 0.0, 1.0)
    stability = clamp(float(stability), 0.0, 1.0)
    energy_normalized = clamp(float(energy) / 100.0, 0.0, 1.0)  # normalize energy to [0,1]
    circadian_phase = float(circadian_phase)
    recovery_efficiency = clamp(float(recovery_efficiency), 0.4, 1.6)

    # stability term: higher stability -> faster time (positive effect)
    stability_term = stability_coeff * (stability - 0.5)  # 0.5 = neutral stability
    # energy term: higher energy -> faster subjective time (positive contribution)
    energy_term = energy_coeff * energy_normalized

    # circadian term: strong influence on subjective time perception
    # Day phase (around π): faster time perception (активность, бодрость)
    # Night phase (around 0/2π): slower time perception (отдых, восстановление)
    circadian_sin = math.sin(circadian_phase)  # -1 (ночь) to +1 (день)
    circadian_term = 0.3 * circadian_sin * recovery_efficiency  # stronger effect with recovery efficiency

    rate = base_rate + intensity_coeff * intensity + stability_term + energy_term + circadian_term
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
    circadian_phase: float = 0.0,
    recovery_efficiency: float = 1.0,
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
        circadian_phase=circadian_phase,
        recovery_efficiency=recovery_efficiency,
    )
    return dt * rate

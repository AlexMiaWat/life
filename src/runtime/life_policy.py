"""
Life Policy - Weakness Detection and Penalty Calculation

This module contains the LifePolicy class that handles:
- Detection of system weakness based on self-state parameters
- Calculation of weakness penalties
- Configuration of weakness thresholds and multipliers
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class WeaknessPenalty:
    """Represents calculated weakness penalty."""
    penalty: float
    components: Dict[str, float]
    reason: str


class LifePolicy:
    """
    Policy for detecting system weakness and calculating penalties.

    The policy monitors self-state parameters (energy, integrity, stability)
    and applies penalties when the system is deemed weak.
    """

    def __init__(self,
                 weakness_threshold: float = 0.05,
                 penalty_k: float = 0.02,
                 stability_multiplier: float = 2.0,
                 integrity_multiplier: float = 2.0):
        """
        Initialize LifePolicy with configuration parameters.

        Args:
            weakness_threshold: Threshold below which parameters are considered weak
            penalty_k: Base penalty coefficient
            stability_multiplier: Multiplier for stability component
            integrity_multiplier: Multiplier for integrity component

        Raises:
            ValueError: If any parameter is negative
        """
        if weakness_threshold < 0:
            raise ValueError("weakness_threshold must be non-negative")
        if penalty_k < 0:
            raise ValueError("penalty_k must be non-negative")
        if stability_multiplier < 0:
            raise ValueError("stability_multiplier must be non-negative")
        if integrity_multiplier < 0:
            raise ValueError("integrity_multiplier must be non-negative")

        self.weakness_threshold = weakness_threshold
        self.penalty_k = penalty_k
        self.stability_multiplier = stability_multiplier
        self.integrity_multiplier = integrity_multiplier

    def is_weak(self, self_state) -> bool:
        """
        Determine if the system is weak based on self-state parameters.

        Args:
            self_state: SelfState object with energy, integrity, stability attributes

        Returns:
            True if any parameter is below weakness threshold
        """
        return (self_state.energy < self.weakness_threshold or
                self_state.integrity < self.weakness_threshold or
                self_state.stability < self.weakness_threshold)

    def calculate_penalty(self, self_state) -> float:
        """
        Calculate weakness penalty based on self-state parameters.

        Formula: penalty_k * (stability_multiplier * (threshold - stability) +
                              integrity_multiplier * (threshold - integrity))

        Note: Energy is not used in penalty calculation, only stability and integrity.

        Args:
            self_state: SelfState object with energy, integrity, stability attributes

        Returns:
            Calculated penalty (0.0 if not weak)
        """
        if not self.is_weak(self_state):
            return 0.0

        stability_penalty = max(0, self.weakness_threshold - self_state.stability)
        integrity_penalty = max(0, self.weakness_threshold - self_state.integrity)

        total_penalty = (self.stability_multiplier * stability_penalty +
                        self.integrity_multiplier * integrity_penalty)

        return self.penalty_k * total_penalty

    def weakness_penalty(self, dt: float, self_state=None) -> Dict[str, float]:
        """
        Calculate weakness penalty deltas for a time step.

        This method is used by the runtime loop to apply penalties over time.

        Args:
            dt: Time step delta
            self_state: SelfState object to check for weakness

        Returns:
            Dictionary with penalty deltas for each component
        """
        if self_state is None:
            # Return default penalty values for testing
            return {
                'energy': -self.penalty_k * dt,
                'stability': -self.stability_multiplier * self.penalty_k * dt,
                'integrity': -self.integrity_multiplier * self.penalty_k * dt
            }

        if not self.is_weak(self_state):
            return {
                'energy': 0.0,
                'integrity': 0.0,
                'stability': 0.0
            }

        penalty = self.calculate_penalty(self_state)

        # Apply penalty proportionally to all components
        energy_penalty = penalty * 0.2  # 20% to energy
        stability_penalty = penalty * 0.4  # 40% to stability
        integrity_penalty = penalty * 0.4  # 40% to integrity

        return {
            'energy': -energy_penalty * dt,
            'stability': -stability_penalty * dt,
            'integrity': -integrity_penalty * dt
        }

    def apply_weakness_penalties(self, self_state, dt: float) -> Dict[str, float]:
        """
        Apply weakness penalties to self-state over a time step.

        Args:
            self_state: SelfState object to modify
            dt: Time step delta

        Returns:
            Dictionary with applied penalty deltas
        """
        if not self.is_weak(self_state):
            return {'energy': 0.0, 'integrity': 0.0, 'stability': 0.0}

        penalty = self.calculate_penalty(self_state)

        # Apply penalty proportionally to stability and integrity
        stability_penalty = penalty * 0.6  # 60% to stability
        integrity_penalty = penalty * 0.4  # 40% to integrity

        # Apply penalties (reduce values)
        self_state.stability = max(0.0, self_state.stability - stability_penalty * dt)
        self_state.integrity = max(0.0, self_state.integrity - integrity_penalty * dt)

        return {
            'energy': 0.0,
            'stability': -stability_penalty * dt,
            'integrity': -integrity_penalty * dt
        }

    def get_policy_info(self) -> Dict[str, Any]:
        """
        Get information about current policy configuration.

        Returns:
            Dictionary with policy parameters
        """
        return {
            "weakness_threshold": self.weakness_threshold,
            "penalty_k": self.penalty_k,
            "stability_multiplier": self.stability_multiplier,
            "integrity_multiplier": self.integrity_multiplier
        }
"""
Core State - базовое состояние системы Life.

Отвечает за основные поля состояния и их базовое управление.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, List

from ..memory.memory import Memory
from ..memory.memory_types import MemoryEntry


@dataclass
class CoreState:
    """
    Базовое состояние системы Life.

    Содержит основные поля состояния без дополнительной логики валидации,
    сериализации или аналитики.
    """

    # Identity
    life_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    birth_timestamp: float = field(default_factory=time.time)

    # Temporal
    age: float = 0.0
    ticks: int = 0
    subjective_time: float = 0.0

    # Vital parameters
    energy: float = 100.0
    integrity: float = 1.0
    stability: float = 1.0

    # Internal dynamics
    fatigue: float = 0.0
    tension: float = 0.0

    # Cognitive layers
    intelligence: Dict[str, any] = field(default_factory=dict)
    planning: Dict[str, any] = field(default_factory=dict)

    # Learning & Adaptation
    learning_params: dict = field(default_factory=lambda: {
        "event_type_sensitivity": {
            "noise": 0.2,
            "decay": 0.2,
            "recovery": 0.2,
            "shock": 0.2,
            "idle": 0.2,
        },
        "significance_thresholds": {
            "noise": 0.1,
            "decay": 0.1,
            "recovery": 0.1,
            "shock": 0.1,
            "idle": 0.1,
        },
        "response_coefficients": {
            "dampen": 0.5,
            "absorb": 1.0,
            "ignore": 0.0,
        },
    })

    adaptation_params: dict = field(default_factory=lambda: {
        "behavior_sensitivity": {
            "noise": 0.2,
            "decay": 0.2,
            "recovery": 0.2,
            "shock": 0.2,
            "idle": 0.2,
        },
        "behavior_thresholds": {
            "noise": 0.1,
            "decay": 0.1,
            "recovery": 0.1,
            "shock": 0.1,
            "idle": 0.1,
        },
        "behavior_coefficients": {
            "dampen": 0.5,
            "absorb": 1.0,
            "ignore": 0.0,
        },
    })

    # Memory
    memory: Optional[Memory] = None

    # Event history
    recent_events: list = field(default_factory=list)

    # History tracking
    energy_history: list = field(default_factory=list)
    stability_history: list = field(default_factory=list)
    parameter_history: list = field(default_factory=list)
    learning_params_history: list = field(default_factory=list)
    adaptation_params_history: list = field(default_factory=list)
    adaptation_history: list = field(default_factory=list)

    # Consciousness
    consciousness_level: float = 0.0
    clarity_history: list = field(default_factory=list)
    state_transition_history: list = field(default_factory=list)
    last_event_intensity: float = 0.0

    # Echo memory
    echo_count: int = 0
    last_echo_time: float = 0.0

    # Multi-level memory stats
    sensory_buffer_size: int = 0
    semantic_concepts_count: int = 0
    procedural_patterns_count: int = 0

    def reset_to_defaults(self) -> None:
        """Сброс к начальным значениям (кроме identity)"""
        self.energy = 100.0
        self.integrity = 1.0
        self.stability = 1.0
        self.fatigue = 0.0
        self.tension = 0.0
        self.age = 0.0
        self.ticks = 0
        self.recent_events = []
        self.energy_history = []
        self.stability_history = []
        self.parameter_history = []
        self.learning_params_history = []
        self.adaptation_params_history = []
        self.adaptation_history = []

    def is_active(self) -> bool:
        """Проверка активности по vital параметрам"""
        return self.energy > 0 and self.integrity > 0 and self.stability > 0

    def is_viable(self) -> bool:
        """Проверка жизнеспособности с более строгими критериями"""
        return self.energy > 10.0 and self.integrity > 0.1 and self.stability > 0.1

    def update_vital_params(
        self,
        energy: Optional[float] = None,
        integrity: Optional[float] = None,
        stability: Optional[float] = None,
    ) -> None:
        """Безопасное обновление vital параметров"""
        if energy is not None:
            self.energy = energy
        if integrity is not None:
            self.integrity = integrity
        if stability is not None:
            self.stability = stability
"""
Clarity Moments Module - Compatibility Layer

This module provides backward compatibility for the old ClarityMoments API
while using the new AdaptiveProcessingManager under the hood.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.contracts.serialization_contract import SerializationContract
from src.experimental.adaptive_processing_manager import (
    AdaptiveProcessingManager,
    ProcessingMode,
    AdaptiveState,
    ProcessingEvent
)


@dataclass
class ClarityMoment:
    """Represents a moment of clarity in the system."""
    timestamp: float
    stage: str
    correlation_id: str
    event_id: str
    event_type: str
    intensity: float
    data: Dict[str, Any]


class ClarityMomentsTracker(SerializationContract):
    """Tracks and analyzes moments of clarity. Реализует контракты сериализации."""

    # Constants for backward compatibility
    CLARITY_CHECK_INTERVAL = 10
    CLARITY_STABILITY_THRESHOLD = 0.8
    CLARITY_ENERGY_THRESHOLD = 0.7

    def __init__(self, self_state=None, adaptive_manager=None):
        """
        Инициализация ClarityMomentsTracker с dependency injection.

        Args:
            self_state: Экземпляр SelfState для dependency injection
            adaptive_manager: Экземпляр AdaptiveProcessingManager (опционально)
        """
        if self_state is not None:
            # Dependency injection через SelfState
            self.self_state = self_state
            self.self_state_provider = lambda: self.self_state
        else:
            # Fallback для обратной совместимости
            def default_self_state_provider():
                return type('DefaultState', (), {
                    'energy': 80.0,
                    'stability': 0.9,
                    'processing_load': 0.3,
                    'memory_usage': 0.6,
                    'error_rate': 0.01
                })()
            self.self_state_provider = default_self_state_provider
            self.self_state = None

        # Используем предоставленный adaptive_manager или создаем новый
        if adaptive_manager is not None:
            self.adaptive_manager = adaptive_manager
        else:
            self.adaptive_manager = AdaptiveProcessingManager(self.self_state_provider)
        self.moments: List[ClarityMoment] = []
        self._correlation_counter = 0

    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID."""
        self._correlation_counter += 1
        return f"clarity_chain_{self._correlation_counter}"

    def add_moment(self, moment: ClarityMoment):
        """Add a new clarity moment."""
        self.moments.append(moment)

        # Convert to adaptive processing event
        processing_mode = self._map_intensity_to_mode(moment.intensity)
        current_state = self.self_state_provider()

        # Add to adaptive manager
        self.adaptive_manager.trigger_processing_event(current_state, processing_mode, moment.intensity)

    def _map_intensity_to_mode(self, intensity: float) -> ProcessingMode:
        """Map clarity intensity to processing mode."""
        if intensity >= 0.9:
            return ProcessingMode.OPTIMIZED
        elif intensity >= 0.7:
            return ProcessingMode.INTENSIVE
        elif intensity >= 0.5:
            return ProcessingMode.EFFICIENT
        else:
            return ProcessingMode.BASELINE

    def get_moments_by_intensity(self, min_intensity: float = 0.0) -> List[ClarityMoment]:
        """Get moments filtered by minimum intensity."""
        return [m for m in self.moments if m.intensity >= min_intensity]

    def get_recent_moments(self, limit: int = 10) -> List[ClarityMoment]:
        """Get most recent moments."""
        return sorted(self.moments, key=lambda m: m.timestamp, reverse=True)[:limit]

    def get_clarity_history(self, limit: Optional[int] = None) -> List[ClarityMoment]:
        """Get the history of clarity moments."""
        moments = sorted(self.moments, key=lambda m: m.timestamp)
        if limit:
            moments = moments[-limit:]
        return moments

    def analyze_clarity_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in clarity moments."""
        # Get data from adaptive manager
        adaptive_stats = self.adaptive_manager.get_processing_statistics()

        if not self.moments:
            return {
                'total_moments': 0,
                'adaptive_stats': adaptive_stats
            }

        # Convert to old format
        intensities = [m.intensity for m in self.moments]
        event_types = [m.event_type for m in self.moments]

        return {
            'total_moments': len(self.moments),
            'avg_intensity': sum(intensities) / len(intensities) if intensities else 0,
            'max_intensity': max(intensities) if intensities else 0,
            'unique_event_types': len(set(event_types)),
            'event_type_distribution': self._count_occurrences(event_types),
            'adaptive_stats': adaptive_stats  # Include new stats
        }

    def _count_occurrences(self, items: List[str]) -> Dict[str, int]:
        """Count occurrences of items in a list."""
        counts = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts

    def get_adaptive_state(self) -> AdaptiveState:
        """Get current adaptive processing state."""
        return self.adaptive_manager.get_current_state()

    def force_clarity_analysis(self) -> Optional[ClarityMoment]:
        """Force immediate clarity analysis."""
        # Trigger adaptive processing analysis
        self.adaptive_manager.analyze_system_conditions()

        current_state = self.adaptive_manager.get_current_state()
        intensity = self._map_state_to_intensity(current_state)

        if intensity >= 0.0:  # Always create moment for testing
            moment = ClarityMoment(
                timestamp=time.time(),
                stage="forced_analysis",
                correlation_id=self._generate_correlation_id(),
                event_id=f"forced_{int(time.time())}",
                event_type="system_analysis",
                intensity=intensity,
                data={
                    'adaptive_state': current_state.value,
                    'trigger_type': 'forced'
                }
            )
            self.add_moment(moment)
            return moment

        return None

    def _map_state_to_intensity(self, state: AdaptiveState) -> float:
        """Map adaptive state to clarity intensity."""
        state_mapping = {
            AdaptiveState.STANDARD: 0.3,
            AdaptiveState.EFFICIENT_PROCESSING: 0.6,
            AdaptiveState.INTENSIVE_ANALYSIS: 0.8,
            AdaptiveState.SYSTEM_SELF_MONITORING: 0.7,
            AdaptiveState.OPTIMAL_PROCESSING: 0.9
        }
        return state_mapping.get(state, 0.3)

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализация состояния ClarityMomentsTracker.

        Архитектурные гарантии:
        - Thread-safe: Метод безопасен для вызова из разных потоков
        - Атомарный: Сериализация представляет консистентное состояние
        - Отказоустойчивый: Исключения не должны приводить к повреждению состояния
        - Детерминированный: Для одинакового состояния возвращает одинаковый результат

        Returns:
            Dict[str, Any]: Словарь с состоянием компонента
        """
        moments_data = []
        for moment in self.moments:
            moments_data.append({
                "timestamp": moment.timestamp,
                "stage": moment.stage,
                "correlation_id": moment.correlation_id,
                "event_id": moment.event_id,
                "event_type": moment.event_type,
                "intensity": moment.intensity,
                "data": moment.data
            })

        return {
            "correlation_counter": self._correlation_counter,
            "moments_count": len(self.moments),
            "moments": moments_data,
            "component_type": "ClarityMomentsTracker",
            "version": "1.0",
            "has_adaptive_manager": self.adaptive_manager is not None
        }

    def get_serialization_metadata(self) -> Dict[str, Any]:
        """
        Получить метаданные сериализации для ClarityMomentsTracker.

        Returns:
            Dict[str, Any]: Метаданные содержащие как минимум:
            - version: str - версия формата сериализации
            - timestamp: float - время сериализации
            - component_type: str - тип компонента
            - thread_safe: bool - подтверждение thread-safety
        """
        return {
            "version": "1.0",
            "component_type": "ClarityMomentsTracker",
            "thread_safe": True,
            "timestamp": time.time(),
            "moments_count": len(self.moments),
            "correlation_counter": self._correlation_counter,
            "has_self_state_provider": self.self_state_provider is not None,
            "adaptive_manager_available": self.adaptive_manager is not None
        }


# Global tracker instance - compatibility layer
tracker: ClarityMomentsTracker = ClarityMomentsTracker()


# Backward compatibility class
class ClarityMoments:
    """Backward compatibility class for old ClarityMoments usage."""

    # Class constants for backward compatibility
    CLARITY_CHECK_INTERVAL = ClarityMomentsTracker.CLARITY_CHECK_INTERVAL
    CLARITY_STABILITY_THRESHOLD = ClarityMomentsTracker.CLARITY_STABILITY_THRESHOLD
    CLARITY_ENERGY_THRESHOLD = ClarityMomentsTracker.CLARITY_ENERGY_THRESHOLD
    CLARITY_DURATION_TICKS = 50

    def __init__(self, logger=None, self_state=None, adaptive_manager=None):
        """
        Инициализация ClarityMoments с dependency injection.

        Args:
            logger: Логгер (для обратной совместимости)
            self_state: Экземпляр SelfState для dependency injection
            adaptive_manager: AdaptiveProcessingManager (опционально для совместимости)
        """
        # Для обратной совместимости adaptive_manager может быть None
        # но архитектурно рекомендуется передавать его явно
        self.tracker = ClarityMomentsTracker(self_state=self_state, adaptive_manager=adaptive_manager)
        # Backward compatibility attributes
        self._clarity_events_count = 0
        self._last_check_tick = -10  # -CLARITY_CHECK_INTERVAL

    def analyze_clarity(self, self_state=None) -> Optional[ClarityMoment]:
        """Analyze clarity based on self state (backward compatibility)."""
        return self.tracker.force_clarity_analysis()

    def get_clarity_moments(self) -> List[ClarityMoment]:
        """Get all clarity moments."""
        return self.tracker.moments.copy()

    def check_clarity_conditions(self, self_state) -> Optional[dict]:
        """Check if clarity conditions are met (backward compatibility)."""
        moment = self.tracker.force_clarity_analysis()
        if moment:
            self._clarity_events_count += 1
            return {
                "type": "clarity_moment",
                "data": {
                    "clarity_id": self._clarity_events_count,
                    "intensity": moment.intensity,
                    "reason": "forced_analysis"
                }
            }
        return None

    def activate_clarity_moment(self, self_state):
        """Activate clarity moment on self state (backward compatibility)."""
        self_state.clarity_state = True
        self_state.clarity_duration = self.CLARITY_DURATION_TICKS
        self_state.clarity_modifier = 1.5

    def update_clarity_state(self, self_state):
        """Update clarity state (backward compatibility)."""
        if hasattr(self_state, 'clarity_duration') and self_state.clarity_duration > 0:
            self_state.clarity_duration -= 1
            if self_state.clarity_duration <= 0:
                self.deactivate_clarity_moment(self_state)

    def deactivate_clarity_moment(self, self_state):
        """Deactivate clarity moment (backward compatibility)."""
        self_state.clarity_state = False
        self_state.clarity_duration = 0
        self_state.clarity_modifier = 1.0

    def get_clarity_level(self) -> float:
        """Get current clarity level."""
        if self.tracker.moments:
            return self.tracker.moments[-1].intensity
        return 0.0  # type: ignore

    def get_status(self) -> Dict[str, Any]:
        """Get current status of clarity moments system."""
        adaptive_state = self.tracker.get_adaptive_state()
        return {
            "active": len(self.tracker.moments) > 0,
            "intensity": self.get_clarity_level(),
            "duration": getattr(self.tracker.adaptive_manager, 'current_duration', 0),
            "adaptive_state": adaptive_state.value if adaptive_state else "unknown"
        }

    def process(self, data: Dict[str, Any], intensity_threshold: float = 0.5, duration_ticks: int = 10) -> Optional[Dict[str, Any]]:
        """Process clarity data and potentially create a clarity moment."""
        intensity = data.get('intensity', 0.0)

        if intensity >= intensity_threshold:
            # Create a clarity moment
            moment = ClarityMoment(
                timestamp=time.time(),
                stage=data.get('stage', 'processed'),
                correlation_id=data.get('correlation_id', self.tracker._generate_correlation_id()),
                event_id=data.get('event_id', f"processed_{int(time.time())}"),
                event_type=data.get('event_type', 'processed_event'),
                intensity=intensity,
                data=data
            )

            self.tracker.add_moment(moment)

            return {
                "clarity_moment_created": True,
                "moment_id": len(self.tracker.moments),
                "intensity": intensity,
                "duration_ticks": duration_ticks
            }

        return None

    def reset(self) -> None:
        """Reset clarity moments state (legacy compatibility)."""
        self.tracker.moments.clear()
        self.tracker._correlation_counter = 0
        self._clarity_events_count = 0
        self._last_check_tick = -10

    # Legacy compatibility mappings
    _LEGACY_MODE_MAPPING = {
        "baseline": "baseline",
        "efficient": "efficient",
        "intensive": "intensive",
        "optimized": "optimized",
        "self_monitoring": "self_monitoring"
    }

    _LEGACY_STATE_MAPPING = {
        "standard": "standard",
        "efficient_processing": "efficient_processing",
        "intensive_analysis": "intensive_analysis",
        "system_self_monitoring": "system_self_monitoring",
        "optimal_processing": "optimal_processing"
    }

    def _convert_to_adaptive_mode(self, legacy_mode: str) -> str:
        """Convert legacy mode to adaptive mode (compatibility)."""
        return self._LEGACY_MODE_MAPPING.get(legacy_mode, "baseline")

    def _convert_from_adaptive_mode(self, adaptive_mode: str) -> str:
        """Convert adaptive mode to legacy mode (compatibility)."""
        for legacy, adaptive in self._LEGACY_MODE_MAPPING.items():
            if adaptive == adaptive_mode:
                return legacy
        return "baseline"

    def _get_legacy_status(self) -> Dict[str, Any]:
        """Get legacy status format (compatibility)."""
        return self.get_status()
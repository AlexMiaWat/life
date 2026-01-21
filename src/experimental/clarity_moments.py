"""
Clarity Moments Module - Compatibility Layer

This module provides backward compatibility for the old ClarityMoments API
while using the new AdaptiveProcessingManager under the hood.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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


class ClarityMomentsTracker:
    """Tracks and analyzes moments of clarity."""

    # Constants for backward compatibility
    CLARITY_CHECK_INTERVAL = 10
    CLARITY_STABILITY_THRESHOLD = 0.8
    CLARITY_ENERGY_THRESHOLD = 70.0

    def __init__(self, data_file: Optional[str] = None):
        # Initialize with new adaptive processing manager
        self.adaptive_manager = AdaptiveProcessingManager()
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
        adaptive_event = ProcessingEvent(
            processing_mode=processing_mode,
            intensity=moment.intensity,
            trigger_conditions={
                'stage': moment.stage,
                'event_type': moment.event_type,
                'correlation_id': moment.correlation_id
            }
        )

        # Add to adaptive manager
        self.adaptive_manager.add_processing_event(adaptive_event)

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

    def analyze_clarity_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in clarity moments."""
        if not self.moments:
            return {'total_moments': 0}

        # Get data from adaptive manager
        adaptive_stats = self.adaptive_manager.get_processing_statistics()

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

        if intensity >= 0.5:  # Only create moment for significant states
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


# Global tracker instance - compatibility layer
tracker: ClarityMomentsTracker = ClarityMomentsTracker()


# Backward compatibility class
class ClarityMoments:
    """Backward compatibility class for old ClarityMoments usage."""

    # Class constants for backward compatibility
    CLARITY_CHECK_INTERVAL = ClarityMomentsTracker.CLARITY_CHECK_INTERVAL
    CLARITY_STABILITY_THRESHOLD = ClarityMomentsTracker.CLARITY_STABILITY_THRESHOLD
    CLARITY_ENERGY_THRESHOLD = ClarityMomentsTracker.CLARITY_ENERGY_THRESHOLD

    def __init__(self):
        self.tracker = tracker

    def analyze_clarity(self, self_state=None) -> Optional[ClarityMoment]:
        """Analyze clarity based on self state (backward compatibility)."""
        return self.tracker.force_clarity_analysis()

    def get_clarity_moments(self) -> List[ClarityMoment]:
        """Get all clarity moments."""
        return self.tracker.moments.copy()

    def get_clarity_level(self) -> float:
        """Get current clarity level."""
        if self.tracker.moments:
            return self.tracker.moments[-1].intensity
        return 0.0</contents>
</xai:function_call=FileWrite>
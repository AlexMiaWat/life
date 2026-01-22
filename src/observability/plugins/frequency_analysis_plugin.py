"""
Example analysis plugin for SemanticAnalysisEngine.

This plugin demonstrates the plugin architecture by analyzing event frequency patterns.
"""

import logging
from typing import Dict, List, Any
from collections import Counter

from src.observability.semantic_analysis_engine import AnalysisPlugin

logger = logging.getLogger(__name__)


class FrequencyAnalysisPlugin(AnalysisPlugin):
    """
    Plugin for analyzing event frequency patterns in correlation chains.

    This plugin detects anomalies based on unusual event type frequencies
    and transitions between event types.
    """

    def __init__(self):
        super().__init__(
            name="frequency_analysis",
            description="Analyzes event frequency patterns and detects unusual distributions"
        )

        # Plugin-specific data
        self.event_frequencies: Counter = Counter()
        self.transition_matrix: Dict[str, Dict[str, int]] = {}
        self.analysis_count = 0

    def analyze(self, correlation_chain: List[Dict]) -> Dict[str, Any]:
        """
        Analyze event frequencies in the correlation chain.

        Args:
            correlation_chain: List of log entries in the chain

        Returns:
            Dict with frequency analysis results
        """
        if not correlation_chain:
            return {'error': 'Empty correlation chain'}

        # Extract event types from chain
        event_types = []
        for entry in correlation_chain:
            if entry.get('stage') == 'event':
                event_type = entry.get('event_type', 'unknown')
                event_types.append(event_type)

        if not event_types:
            return {'error': 'No events found in chain'}

        # Calculate frequencies
        frequencies = Counter(event_types)
        total_events = len(event_types)

        # Calculate transition frequencies
        transitions = {}
        for i in range(len(event_types) - 1):
            current = event_types[i]
            next_event = event_types[i + 1]
            transition_key = f"{current}->{next_event}"
            transitions[transition_key] = transitions.get(transition_key, 0) + 1

        # Update global statistics
        self.event_frequencies.update(event_types)
        for transition, count in transitions.items():
            if transition not in self.transition_matrix:
                self.transition_matrix[transition] = {}
            self.transition_matrix[transition]['count'] = \
                self.transition_matrix[transition].get('count', 0) + count

        self.analysis_count += 1

        return {
            'event_types': list(frequencies.keys()),
            'frequencies': dict(frequencies),
            'total_events': total_events,
            'transitions': transitions,
            'unique_event_types': len(frequencies),
            'entropy': self._calculate_entropy(frequencies, total_events),
            'analysis_count': self.analysis_count
        }

    def get_anomaly_score(self, analysis_result: Dict[str, Any]) -> float:
        """
        Calculate anomaly score based on frequency analysis.

        Args:
            analysis_result: Results from analyze() method

        Returns:
            Anomaly score between 0.0 and 1.0
        """
        if 'error' in analysis_result:
            return 0.0

        score = 0.0
        factors = 0

        # Factor 1: Unusual event distribution (high entropy)
        entropy = analysis_result.get('entropy', 0.0)
        if entropy > 1.5:  # High entropy indicates unpredictable behavior
            score += min(0.4, (entropy - 1.5) / 1.0)
            factors += 1

        # Factor 2: Rare event types
        frequencies = analysis_result.get('frequencies', {})
        total_events = analysis_result.get('total_events', 1)

        for event_type, count in frequencies.items():
            frequency_ratio = count / total_events
            global_freq = self.event_frequencies.get(event_type, 0)
            global_total = sum(self.event_frequencies.values())

            if global_total > 0:
                expected_ratio = global_freq / global_total
                if expected_ratio > 0:
                    deviation = abs(frequency_ratio - expected_ratio) / expected_ratio
                    if deviation > 2.0:  # Significant deviation from expected
                        score += min(0.3, deviation * 0.1)
                        factors += 1

        # Factor 3: Unusual transitions
        transitions = analysis_result.get('transitions', {})
        for transition, count in transitions.items():
            if count == 1 and self.analysis_count > 5:  # Very rare transition
                score += 0.2
                factors += 1

        return min(1.0, score / max(1, factors))

    def _calculate_entropy(self, frequencies: Counter, total: int) -> float:
        """Calculate Shannon entropy of event distribution."""
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in frequencies.values():
            if count > 0:
                probability = count / total
                entropy -= probability * (probability.log() / 2.302585)  # log10

        return entropy

    def get_plugin_info(self) -> Dict[str, Any]:
        """Get extended information about this plugin."""
        base_info = super().get_plugin_info()
        base_info.update({
            'total_events_analyzed': sum(self.event_frequencies.values()),
            'unique_event_types_learned': len(self.event_frequencies),
            'transitions_learned': len(self.transition_matrix),
            'analysis_count': self.analysis_count
        })
        return base_info
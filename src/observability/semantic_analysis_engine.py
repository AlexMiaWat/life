"""
Semantic Analysis Engine for Life system observability.

Provides deep semantic understanding of system behavior through analysis of:
- Event-meaning-decision-action-feedback chains
- Semantic patterns and relationships
- Behavioral anomalies and trends
- Contextual state analysis
"""

import json
import logging
import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import time

logger = logging.getLogger(__name__)


@dataclass
class SemanticPattern:
    """Semantic pattern identified in event chains."""
    pattern_id: str
    event_types: List[str]
    decision_patterns: List[str]
    impact_profile: Dict[str, float]  # Average impact on state parameters
    frequency: int
    confidence: float  # How confident we are in this pattern
    last_seen: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehavioralAnomaly:
    """Detected behavioral anomaly."""
    anomaly_id: str
    anomaly_type: str  # 'pattern_deviation', 'state_aberration', 'chain_breakage'
    severity: float  # 0.0 to 1.0
    description: str
    timestamp: float
    correlation_ids: List[str]
    evidence: Dict[str, Any]


@dataclass
class SystemHealthProfile:
    """Semantic health profile of the system."""
    energy_stability: float
    cognitive_coherence: float
    adaptation_efficiency: float
    memory_integrity: float
    overall_health: float
    risk_factors: List[str]
    recommendations: List[str]


class SemanticAnalysisEngine:
    """
    Engine for semantic analysis of Life system behavior.

    Analyzes the deep meaning behind event chains and system behavior patterns.
    """

    # Event type categories for semantic grouping
    EVENT_CATEGORIES = {
        'physiological': ['decay', 'recovery', 'fatigue'],
        'cognitive': ['cognitive_doubt', 'cognitive_clarity', 'cognitive_confusion',
                     'insight', 'confusion', 'curiosity', 'meaning_found'],
        'emotional': ['joy', 'sadness', 'fear', 'calm', 'discomfort', 'comfort',
                     'anticipation', 'boredom', 'inspiration'],
        'existential': ['existential_void', 'existential_purpose', 'existential_finitude',
                       'void', 'acceptance', 'clarity_moment'],
        'social': ['social_presence', 'social_conflict', 'social_harmony',
                  'connection', 'isolation'],
        'environmental': ['noise', 'shock', 'idle', 'memory_echo']
    }

    # State parameter relationships
    STATE_RELATIONSHIPS = {
        'energy': ['fatigue', 'recovery', 'stability'],
        'integrity': ['shock', 'cognitive_confusion', 'cognitive_clarity'],
        'stability': ['noise', 'shock', 'cognitive_doubt', 'calm'],
        'subjective_time': ['cognitive_clarity', 'existential_purpose', 'boredom']
    }

    def __init__(self, max_patterns: int = 100, anomaly_threshold: float = 0.7):
        """
        Initialize the semantic analysis engine.

        Args:
            max_patterns: Maximum number of semantic patterns to track
            anomaly_threshold: Threshold for anomaly detection (0.0-1.0)
        """
        self.max_patterns = max_patterns
        self.anomaly_threshold = anomaly_threshold

        # Core analysis data structures
        self.semantic_patterns: Dict[str, SemanticPattern] = {}
        self.behavioral_anomalies: List[BehavioralAnomaly] = []
        self.correlation_chains: Dict[str, List[Dict]] = {}
        self.state_evolution: List[Dict] = []

        # Statistical accumulators
        self.event_type_frequencies: Counter = Counter()
        self.decision_pattern_frequencies: Counter = Counter()
        self.impact_accumulators: Dict[str, List[float]] = defaultdict(list)

        # Pattern learning
        self.pattern_learning_window = 1000  # Number of recent chains to analyze
        self.min_pattern_confidence = 0.6

        logger.info("SemanticAnalysisEngine initialized")

    def analyze_correlation_chain(self, correlation_id: str, chain_entries: List[Dict]) -> Dict[str, Any]:
        """
        Analyze a complete correlation chain semantically.

        Args:
            correlation_id: Correlation ID for the chain
            chain_entries: List of log entries in the chain

        Returns:
            Semantic analysis results for this chain
        """
        if not chain_entries:
            return {}

        # Extract chain components
        events = [e for e in chain_entries if e.get('stage') == 'event']
        meanings = [e for e in chain_entries if e.get('stage') == 'meaning']
        decisions = [e for e in chain_entries if e.get('stage') == 'decision']
        actions = [e for e in chain_entries if e.get('stage') == 'action']
        feedbacks = [e for e in chain_entries if e.get('stage') == 'feedback']

        # Semantic analysis
        chain_semantics = {
            'correlation_id': correlation_id,
            'chain_length': len(chain_entries),
            'event_types': [e.get('event_type', 'unknown') for e in events],
            'decision_patterns': [d.get('data', {}).get('pattern', 'unknown') for d in decisions],
            'impact_profile': self._extract_impact_profile(meanings),
            'semantic_category': self._categorize_chain(events),
            'behavioral_context': self._analyze_behavioral_context(chain_entries),
            'anomaly_score': self._calculate_anomaly_score(chain_entries),
            'timestamp': time.time()
        }

        # Update learning data
        self._update_pattern_learning(chain_semantics)
        self.correlation_chains[correlation_id] = chain_entries

        return chain_semantics

    def _extract_impact_profile(self, meanings: List[Dict]) -> Dict[str, float]:
        """Extract average impact profile from meaning entries."""
        impacts = []
        for meaning in meanings:
            data = meaning.get('data', {})
            if 'impact' in data:
                impacts.append(data['impact'])

        if not impacts:
            return {}

        # Calculate average impact across all meanings
        avg_impact = {}
        param_counts = defaultdict(int)

        for impact in impacts:
            for param, value in impact.items():
                if param not in avg_impact:
                    avg_impact[param] = 0.0
                avg_impact[param] += value
                param_counts[param] += 1

        for param in avg_impact:
            avg_impact[param] /= param_counts[param]

        return dict(avg_impact)

    def _categorize_chain(self, events: List[Dict]) -> str:
        """Categorize the semantic nature of an event chain."""
        if not events:
            return 'empty'

        event_types = [e.get('event_type', 'unknown') for e in events]

        # Count categories
        category_scores = defaultdict(int)
        for event_type in event_types:
            for category, types in self.EVENT_CATEGORIES.items():
                if event_type in types:
                    category_scores[category] += 1

        if not category_scores:
            return 'uncategorized'

        # Return dominant category
        return max(category_scores.items(), key=lambda x: x[1])[0]

    def _analyze_behavioral_context(self, chain_entries: List[Dict]) -> Dict[str, Any]:
        """Analyze the behavioral context of a chain."""
        context = {
            'has_meaning_processing': any(e.get('stage') == 'meaning' for e in chain_entries),
            'has_decision_making': any(e.get('stage') == 'decision' for e in chain_entries),
            'has_action_execution': any(e.get('stage') == 'action' for e in chain_entries),
            'has_feedback_loop': any(e.get('stage') == 'feedback' for e in chain_entries),
            'processing_completeness': 0.0,
            'response_efficiency': 0.0
        }

        # Calculate processing completeness (0.0 to 1.0)
        expected_stages = {'event', 'meaning', 'decision', 'action', 'feedback'}
        present_stages = {e.get('stage') for e in chain_entries if e.get('stage') in expected_stages}
        context['processing_completeness'] = len(present_stages) / len(expected_stages)

        # Calculate response efficiency based on timing
        timestamps = [e.get('timestamp', 0) for e in chain_entries if 'timestamp' in e]
        if len(timestamps) >= 2:
            time_span = max(timestamps) - min(timestamps)
            context['response_efficiency'] = min(1.0, 1.0 / (1.0 + time_span))  # Efficiency decreases with time

        return context

    def _calculate_anomaly_score(self, chain_entries: List[Dict]) -> float:
        """Calculate anomaly score for a chain (0.0 = normal, 1.0 = highly anomalous)."""
        score = 0.0
        factors = 0

        # Factor 1: Chain completeness
        completeness = self._analyze_behavioral_context(chain_entries)['processing_completeness']
        if completeness < 0.6:  # Incomplete processing
            score += (1.0 - completeness) * 0.4
            factors += 1

        # Factor 2: Unusual event patterns
        events = [e for e in chain_entries if e.get('stage') == 'event']
        if events:
            event_types = [e.get('event_type', 'unknown') for e in events]
            # Check for rare event combinations
            rare_combinations = self._detect_rare_patterns(event_types)
            score += rare_combinations * 0.3
            factors += 1

        # Factor 3: Impact magnitude
        meanings = [e for e in chain_entries if e.get('stage') == 'meaning']
        if meanings:
            total_impact = 0.0
            impact_count = 0
            for meaning in meanings:
                impact_data = meaning.get('data', {}).get('impact', {})
                for param, value in impact_data.items():
                    total_impact += abs(value)
                    impact_count += 1

            if impact_count > 0:
                avg_impact = total_impact / impact_count
                if avg_impact > 0.5:  # High impact events
                    score += min(0.3, avg_impact / 2.0)
                    factors += 1

        return score / max(factors, 1)

    def _detect_rare_patterns(self, event_types: List[str]) -> float:
        """Detect rare or unusual event type combinations."""
        if len(event_types) < 2:
            return 0.0

        # Simple rarity scoring based on frequency
        rarity_score = 0.0
        for event_type in event_types:
            freq = self.event_type_frequencies.get(event_type, 0)
            if freq < 10:  # Rare event
                rarity_score += 0.2
            elif freq > 1000:  # Very common event
                rarity_score += 0.05

        # Combination rarity
        combination = tuple(sorted(set(event_types)))
        if len(combination) > 1:
            # Check if this combination is unusual
            combination_str = '|'.join(combination)
            # This is a simplified check - in practice, you'd maintain combination frequencies
            if len(set(event_types)) == len(event_types):  # All different types
                rarity_score += 0.1

        return min(1.0, rarity_score)

    def _update_pattern_learning(self, chain_semantics: Dict[str, Any]):
        """Update pattern learning with new chain data."""
        # Update frequency counters
        for event_type in chain_semantics.get('event_types', []):
            self.event_type_frequencies[event_type] += 1

        for decision_pattern in chain_semantics.get('decision_patterns', []):
            self.decision_pattern_frequencies[decision_pattern] += 1

        # Update impact accumulators
        for param, value in chain_semantics.get('impact_profile', {}).items():
            self.impact_accumulators[param].append(value)

        # Learn semantic patterns
        self._learn_semantic_patterns(chain_semantics)

    def _learn_semantic_patterns(self, chain_semantics: Dict[str, Any]):
        """Learn semantic patterns from chain analysis."""
        event_types = tuple(sorted(set(chain_semantics.get('event_types', []))))
        decision_patterns = tuple(sorted(set(chain_semantics.get('decision_patterns', []))))
        category = chain_semantics.get('semantic_category', 'unknown')

        if not event_types:
            return

        # Create pattern key
        pattern_key = f"{category}:{event_types}:{decision_patterns}"

        if pattern_key in self.semantic_patterns:
            # Update existing pattern
            pattern = self.semantic_patterns[pattern_key]
            pattern.frequency += 1
            pattern.last_seen = time.time()

            # Update impact profile (moving average)
            current_impact = chain_semantics.get('impact_profile', {})
            for param in set(pattern.impact_profile.keys()) | set(current_impact.keys()):
                old_value = pattern.impact_profile.get(param, 0.0)
                new_value = current_impact.get(param, 0.0)
                pattern.impact_profile[param] = (old_value * (pattern.frequency - 1) + new_value) / pattern.frequency

            # Update confidence based on frequency and consistency
            pattern.confidence = min(1.0, pattern.frequency / 10.0)

        else:
            # Create new pattern
            if len(self.semantic_patterns) < self.max_patterns:
                impact_profile = chain_semantics.get('impact_profile', {})
                self.semantic_patterns[pattern_key] = SemanticPattern(
                    pattern_id=pattern_key,
                    event_types=list(event_types),
                    decision_patterns=list(decision_patterns),
                    impact_profile=impact_profile.copy(),
                    frequency=1,
                    confidence=0.1,  # Start low, build up
                    last_seen=time.time(),
                    metadata={'category': category}
                )

    def analyze_system_health(self, recent_chains: List[Dict] = None) -> SystemHealthProfile:
        """
        Analyze overall system health based on semantic patterns.

        Args:
            recent_chains: Recent correlation chains to analyze

        Returns:
            System health profile
        """
        if recent_chains is None:
            recent_chains = list(self.correlation_chains.values())[-100:]  # Last 100 chains

        # Analyze energy stability
        energy_impacts = []
        stability_impacts = []
        cognitive_events = []
        adaptation_patterns = []

        for chain in recent_chains:
            for entry in chain:
                if entry.get('stage') == 'meaning':
                    impact = entry.get('data', {}).get('impact', {})
                    if 'energy' in impact:
                        energy_impacts.append(impact['energy'])
                    if 'stability' in impact:
                        stability_impacts.append(impact['stability'])

                elif entry.get('stage') == 'event':
                    event_type = entry.get('event_type', '')
                    if any(cat in ['cognitive', 'existential'] for cat, types in self.EVENT_CATEGORIES.items() if event_type in types):
                        cognitive_events.append(event_type)

                elif entry.get('stage') == 'decision':
                    pattern = entry.get('data', {}).get('pattern', '')
                    adaptation_patterns.append(pattern)

        # Calculate health metrics
        energy_stability = self._calculate_energy_stability(energy_impacts)
        cognitive_coherence = self._calculate_cognitive_coherence(cognitive_events)
        adaptation_efficiency = self._calculate_adaptation_efficiency(adaptation_patterns)
        memory_integrity = self._calculate_memory_integrity(recent_chains)

        # Overall health is weighted average
        overall_health = (
            energy_stability * 0.3 +
            cognitive_coherence * 0.3 +
            adaptation_efficiency * 0.2 +
            memory_integrity * 0.2
        )

        # Identify risk factors
        risk_factors = []
        recommendations = []

        if energy_stability < 0.5:
            risk_factors.append("Low energy stability")
            recommendations.append("Consider energy management optimization")

        if cognitive_coherence < 0.6:
            risk_factors.append("Poor cognitive coherence")
            recommendations.append("Review cognitive event processing")

        if adaptation_efficiency < 0.5:
            risk_factors.append("Inefficient adaptation patterns")
            recommendations.append("Optimize decision-making algorithms")

        if memory_integrity < 0.7:
            risk_factors.append("Memory integrity issues")
            recommendations.append("Check memory consolidation processes")

        return SystemHealthProfile(
            energy_stability=energy_stability,
            cognitive_coherence=cognitive_coherence,
            adaptation_efficiency=adaptation_efficiency,
            memory_integrity=memory_integrity,
            overall_health=overall_health,
            risk_factors=risk_factors,
            recommendations=recommendations
        )

    def _calculate_energy_stability(self, energy_impacts: List[float]) -> float:
        """Calculate energy stability score."""
        if not energy_impacts:
            return 0.5  # Neutral score

        # Energy stability is inverse of impact volatility
        if len(energy_impacts) < 3:
            return 0.5

        try:
            volatility = statistics.stdev(energy_impacts)
            # Lower volatility = higher stability
            stability = max(0.0, 1.0 - volatility * 2.0)
            return stability
        except statistics.StatisticsError:
            return 0.5

    def _calculate_cognitive_coherence(self, cognitive_events: List[str]) -> float:
        """Calculate cognitive coherence based on event patterns."""
        if not cognitive_events:
            return 0.5

        # Coherence based on event type diversity and consistency
        unique_events = len(set(cognitive_events))
        total_events = len(cognitive_events)

        # Balance between diversity and focus
        diversity_ratio = unique_events / max(1, total_events)

        # Ideal diversity is around 0.3-0.7
        if 0.3 <= diversity_ratio <= 0.7:
            coherence = 1.0
        elif diversity_ratio < 0.3:
            coherence = diversity_ratio / 0.3  # Too focused
        else:
            coherence = (1.0 - diversity_ratio) / 0.3  # Too scattered

        return max(0.0, min(1.0, coherence))

    def _calculate_adaptation_efficiency(self, adaptation_patterns: List[str]) -> float:
        """Calculate adaptation efficiency from decision patterns."""
        if not adaptation_patterns:
            return 0.5

        # Efficiency based on pattern diversity and common successful patterns
        pattern_counts = Counter(adaptation_patterns)
        total_patterns = len(adaptation_patterns)
        unique_patterns = len(pattern_counts)

        # Prefer moderate pattern diversity (not too rigid, not too chaotic)
        diversity_score = 1.0 - abs(unique_patterns / total_patterns - 0.4) / 0.4

        # Bonus for using known effective patterns
        effective_patterns = {'absorb', 'dampen', 'amplify'}  # Assume these are effective
        effective_usage = sum(count for pattern, count in pattern_counts.items()
                            if pattern in effective_patterns) / total_patterns

        efficiency = (diversity_score * 0.6 + effective_usage * 0.4)
        return max(0.0, min(1.0, efficiency))

    def _calculate_memory_integrity(self, recent_chains: List[List[Dict]]) -> float:
        """Calculate memory integrity based on chain consistency."""
        if not recent_chains:
            return 0.5

        # Check for chain completeness and consistency
        complete_chains = 0
        total_chains = len(recent_chains)

        for chain in recent_chains:
            stages = {entry.get('stage') for entry in chain}
            required_stages = {'event', 'meaning', 'decision', 'action'}
            if required_stages.issubset(stages):
                complete_chains += 1

        integrity = complete_chains / total_chains
        return max(0.0, min(1.0, integrity))

    def detect_anomalies(self, analysis_results: Dict[str, Any]) -> List[BehavioralAnomaly]:
        """
        Detect behavioral anomalies from analysis results.

        Args:
            analysis_results: Results from chain analysis

        Returns:
            List of detected anomalies
        """
        anomalies = []
        anomaly_score = analysis_results.get('anomaly_score', 0.0)

        if anomaly_score > self.anomaly_threshold:
            anomaly = BehavioralAnomaly(
                anomaly_id=f"anomaly_{int(time.time()*1000)}",
                anomaly_type='pattern_deviation',
                severity=anomaly_score,
                description=f"Unusual behavioral pattern detected (score: {anomaly_score:.2f})",
                timestamp=time.time(),
                correlation_ids=[analysis_results.get('correlation_id', 'unknown')],
                evidence={
                    'anomaly_score': anomaly_score,
                    'semantic_category': analysis_results.get('semantic_category', 'unknown'),
                    'behavioral_context': analysis_results.get('behavioral_context', {})
                }
            )
            anomalies.append(anomaly)
            self.behavioral_anomalies.append(anomaly)

        return anomalies

    def get_semantic_insights(self) -> Dict[str, Any]:
        """
        Get comprehensive semantic insights from analysis.

        Returns:
            Dictionary with semantic insights
        """
        insights = {
            'semantic_patterns': {
                pattern_id: {
                    'frequency': pattern.frequency,
                    'confidence': pattern.confidence,
                    'impact_profile': pattern.impact_profile,
                    'category': pattern.metadata.get('category', 'unknown')
                }
                for pattern_id, pattern in self.semantic_patterns.items()
            },
            'behavioral_anomalies': [
                {
                    'type': anomaly.anomaly_type,
                    'severity': anomaly.severity,
                    'description': anomaly.description,
                    'timestamp': anomaly.timestamp
                }
                for anomaly in self.behavioral_anomalies[-10:]  # Last 10 anomalies
            ],
            'system_health': self.analyze_system_health(),
            'event_type_distribution': dict(self.event_type_frequencies.most_common(10)),
            'decision_pattern_distribution': dict(self.decision_pattern_frequencies.most_common(5)),
            'analysis_timestamp': time.time()
        }

        return insights

    def analyze_behavioral_trends(self, time_window_seconds: float = 3600.0) -> Dict[str, Any]:
        """
        Анализ поведенческих трендов в заданном временном окне.

        Args:
            time_window_seconds: Временное окно для анализа (секунды)

        Returns:
            Анализ поведенческих трендов
        """
        current_time = time.time()
        window_start = current_time - time_window_seconds

        # Filter recent chains
        recent_chains = {}
        for correlation_id, chain in self.correlation_chains.items():
            if chain and chain[0].get('timestamp', 0) >= window_start:
                recent_chains[correlation_id] = chain

        if not recent_chains:
            return {
                'trend_analysis': 'insufficient_data',
                'time_window': time_window_seconds,
                'chains_analyzed': 0
            }

        # Analyze trends
        trends = {
            'event_type_trends': self._analyze_event_type_trends(recent_chains),
            'decision_pattern_trends': self._analyze_decision_trends(recent_chains),
            'impact_trends': self._analyze_impact_trends(recent_chains),
            'processing_efficiency_trends': self._analyze_processing_efficiency_trends(recent_chains),
            'anomaly_trends': self._analyze_anomaly_trends(recent_chains, window_start),
            'overall_trend': 'stable',  # Will be updated based on analysis
            'time_window': time_window_seconds,
            'chains_analyzed': len(recent_chains),
            'analysis_timestamp': current_time
        }

        # Determine overall trend
        trends['overall_trend'] = self._determine_overall_trend(trends)

        return trends

    def _analyze_event_type_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов типов событий."""
        event_timeline = defaultdict(lambda: defaultdict(int))

        for chain in chains.values():
            for entry in chain:
                if entry.get('stage') == 'event':
                    timestamp = entry.get('timestamp', 0)
                    event_type = entry.get('event_type', 'unknown')

                    # Group by 5-minute intervals
                    interval = int(timestamp // 300) * 300
                    event_timeline[interval][event_type] += 1

        # Calculate trends for each event type
        trends = {}
        intervals = sorted(event_timeline.keys())

        if len(intervals) >= 3:
            for event_type in set():
                for interval_data in event_timeline.values():
                    if event_type in interval_data:
                        break
                else:
                    continue  # Skip event types not seen

                counts = [event_timeline[interval].get(event_type, 0) for interval in intervals]

                # Simple linear trend (slope)
                if len(counts) >= 2:
                    trend_slope = self._calculate_trend_slope(counts)
                    trends[event_type] = {
                        'slope': trend_slope,
                        'direction': 'increasing' if trend_slope > 0.1 else 'decreasing' if trend_slope < -0.1 else 'stable',
                        'volatility': self._calculate_volatility(counts),
                        'recent_average': sum(counts[-3:]) / min(3, len(counts)) if counts else 0
                    }

        return trends

    def _analyze_decision_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов паттернов решений."""
        decision_timeline = defaultdict(lambda: defaultdict(int))

        for chain in chains.values():
            for entry in chain:
                if entry.get('stage') == 'decision':
                    timestamp = entry.get('timestamp', 0)
                    pattern = entry.get('data', {}).get('pattern', 'unknown')

                    interval = int(timestamp // 300) * 300
                    decision_timeline[interval][pattern] += 1

        # Analyze decision pattern effectiveness
        effectiveness = {}
        for pattern in set():
            for interval_data in decision_timeline.values():
                if pattern in interval_data:
                    break
            else:
                continue

            # Calculate effectiveness based on subsequent feedback
            pattern_effectiveness = self._calculate_decision_effectiveness(pattern, chains)
            effectiveness[pattern] = pattern_effectiveness

        return {
            'pattern_distribution': dict(sum((Counter(interval) for interval in decision_timeline.values()), Counter())),
            'effectiveness_scores': effectiveness
        }

    def _analyze_impact_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов воздействий на состояние."""
        impact_timeline = defaultdict(lambda: defaultdict(list))

        for chain in chains.values():
            for entry in chain:
                if entry.get('stage') == 'meaning':
                    timestamp = entry.get('timestamp', 0)
                    impact = entry.get('data', {}).get('impact', {})

                    interval = int(timestamp // 300) * 300
                    for param, value in impact.items():
                        impact_timeline[interval][param].append(value)

        # Calculate impact trends
        trends = {}
        intervals = sorted(impact_timeline.keys())

        for param in ['energy', 'integrity', 'stability']:
            param_impacts = []
            for interval in intervals:
                interval_impacts = impact_timeline[interval].get(param, [])
                if interval_impacts:
                    param_impacts.append(sum(interval_impacts) / len(interval_impacts))

            if len(param_impacts) >= 3:
                trends[param] = {
                    'slope': self._calculate_trend_slope(param_impacts),
                    'volatility': self._calculate_volatility(param_impacts),
                    'recent_average': sum(param_impacts[-3:]) / 3,
                    'extremes': {
                        'min': min(param_impacts),
                        'max': max(param_impacts)
                    }
                }

        return trends

    def _analyze_processing_efficiency_trends(self, chains: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Анализ трендов эффективности обработки."""
        efficiency_metrics = []

        for chain in chains.values():
            if not chain:
                continue

            # Calculate processing time for complete chains
            stages = {entry.get('stage') for entry in chain}
            if {'event', 'meaning', 'decision', 'action'}.issubset(stages):
                timestamps = [entry.get('timestamp', 0) for entry in chain if entry.get('timestamp')]
                if len(timestamps) >= 2:
                    processing_time = max(timestamps) - min(timestamps)
                    completeness = len(stages) / 5.0  # 5 stages total
                    efficiency = completeness / max(processing_time, 0.001)  # Avoid division by zero
                    efficiency_metrics.append({
                        'processing_time': processing_time,
                        'efficiency': efficiency,
                        'stages_completed': len(stages),
                        'timestamp': min(timestamps)
                    })

        if not efficiency_metrics:
            return {'trend': 'no_complete_chains'}

        # Analyze efficiency trends
        efficiencies = [m['efficiency'] for m in efficiency_metrics]
        processing_times = [m['processing_time'] for m in efficiency_metrics]

        return {
            'efficiency_trend': {
                'slope': self._calculate_trend_slope(efficiencies),
                'average': sum(efficiencies) / len(efficiencies),
                'volatility': self._calculate_volatility(efficiencies)
            },
            'processing_time_trend': {
                'slope': self._calculate_trend_slope(processing_times),
                'average': sum(processing_times) / len(processing_times),
                'p95': sorted(processing_times)[int(len(processing_times) * 0.95)] if processing_times else 0
            },
            'complete_chains': len(efficiency_metrics)
        }

    def _analyze_anomaly_trends(self, chains: Dict[str, List[Dict]], window_start: float) -> Dict[str, Any]:
        """Анализ трендов аномалий."""
        recent_anomalies = [a for a in self.behavioral_anomalies if a.timestamp >= window_start]

        if not recent_anomalies:
            return {'anomaly_rate': 0.0, 'trend': 'normal'}

        anomaly_rate = len(recent_anomalies) / len(chains)

        # Group anomalies by time intervals
        anomaly_timeline = defaultdict(int)
        for anomaly in recent_anomalies:
            interval = int(anomaly.timestamp // 300) * 300
            anomaly_timeline[interval] += 1

        intervals = sorted(anomaly_timeline.keys())
        counts = [anomaly_timeline[interval] for interval in intervals]

        return {
            'anomaly_rate': anomaly_rate,
            'trend_slope': self._calculate_trend_slope(counts) if len(counts) >= 2 else 0.0,
            'severity_distribution': {
                'low': len([a for a in recent_anomalies if a.severity < 0.5]),
                'medium': len([a for a in recent_anomalies if 0.5 <= a.severity < 0.8]),
                'high': len([a for a in recent_anomalies if a.severity >= 0.8])
            },
            'total_anomalies': len(recent_anomalies)
        }

    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate simple linear trend slope."""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))

        # Calculate means
        mean_x = sum(x) / n
        mean_y = sum(values) / n

        # Calculate slope
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, values))
        denominator = sum((xi - mean_x) ** 2 for xi in x)

        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (standard deviation normalized by mean)."""
        if len(values) < 2:
            return 0.0

        try:
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                return 0.0

            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5

            return std_dev / abs(mean_val)
        except:
            return 0.0

    def _calculate_decision_effectiveness(self, pattern: str, chains: Dict[str, List[Dict]]) -> float:
        """Calculate effectiveness score for a decision pattern."""
        pattern_chains = []
        for chain in chains.values():
            for entry in chain:
                if (entry.get('stage') == 'decision' and
                    entry.get('data', {}).get('pattern') == pattern):
                    pattern_chains.append(chain)
                    break

        if not pattern_chains:
            return 0.5  # Neutral score

        # Simple effectiveness based on chain completeness and feedback
        effectiveness_scores = []
        for chain in pattern_chains:
            stages = {entry.get('stage') for entry in chain}

            # Completeness score
            required_stages = {'event', 'meaning', 'decision', 'action'}
            completeness = len(stages.intersection(required_stages)) / len(required_stages)

            # Feedback score (simplified)
            has_feedback = 'feedback' in stages
            feedback_bonus = 0.2 if has_feedback else 0.0

            score = completeness + feedback_bonus
            effectiveness_scores.append(min(1.0, score))

        return sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0.5

    def _determine_overall_trend(self, trends: Dict[str, Any]) -> str:
        """Determine overall behavioral trend."""
        anomaly_trend = trends.get('anomaly_trends', {})
        efficiency_trend = trends.get('processing_efficiency_trends', {})
        impact_trends = trends.get('impact_trends', {})

        # Check for concerning signals
        concerning_signals = 0

        # High anomaly rate increasing
        if anomaly_trend.get('anomaly_rate', 0) > 0.1 and anomaly_trend.get('trend_slope', 0) > 0:
            concerning_signals += 1

        # Declining processing efficiency
        if efficiency_trend.get('efficiency_trend', {}).get('slope', 0) < -0.1:
            concerning_signals += 1

        # Volatile state impacts
        for param_trend in impact_trends.values():
            if param_trend.get('volatility', 0) > 0.5:
                concerning_signals += 1
                break

        if concerning_signals >= 2:
            return 'concerning'
        elif concerning_signals == 1:
            return 'unstable'
        else:
            return 'stable'

    def predict_behavioral_risks(self, prediction_horizon: int = 5) -> Dict[str, Any]:
        """
        Predict potential behavioral risks based on current trends.

        Args:
            prediction_horizon: Number of future intervals to predict

        Returns:
            Risk predictions and recommendations
        """
        # Get recent trends
        recent_trends = self.analyze_behavioral_trends(time_window_seconds=1800)  # Last 30 minutes

        predictions = {
            'risk_assessment': {},
            'predicted_anomalies': [],
            'recommendations': [],
            'confidence': 0.0,
            'prediction_horizon': prediction_horizon
        }

        # Predict based on anomaly trends
        anomaly_trend = recent_trends.get('anomaly_trends', {})
        if anomaly_trend.get('trend_slope', 0) > 0.5:
            predictions['predicted_anomalies'].append({
                'type': 'anomaly_rate_increase',
                'severity': 'high',
                'description': 'Увеличение частоты аномалий может указывать на проблемы',
                'timeframe': f'следующие {prediction_horizon} интервалов'
            })
            predictions['risk_assessment']['anomaly_risk'] = 'high'
            predictions['recommendations'].append('Рекомендуется проверить конфигурацию системы')

        # Predict based on efficiency trends
        efficiency_trend = recent_trends.get('processing_efficiency_trends', {})
        efficiency_slope = efficiency_trend.get('efficiency_trend', {}).get('slope', 0)

        if efficiency_slope < -0.2:
            predictions['predicted_anomalies'].append({
                'type': 'efficiency_decline',
                'severity': 'medium',
                'description': 'Снижение эффективности обработки может привести к задержкам',
                'timeframe': f'следующие {prediction_horizon} интервалов'
            })
            predictions['risk_assessment']['efficiency_risk'] = 'medium'
            predictions['recommendations'].append('Оптимизировать алгоритмы обработки')

        # Predict based on state impact volatility
        impact_trends = recent_trends.get('impact_trends', {})
        high_volatility_params = [
            param for param, trend in impact_trends.items()
            if trend.get('volatility', 0) > 0.7
        ]

        if high_volatility_params:
            predictions['predicted_anomalies'].append({
                'type': 'state_instability',
                'severity': 'medium',
                'description': f'Высокая волатильность параметров: {", ".join(high_volatility_params)}',
                'timeframe': f'следующие {prediction_horizon} интервалов'
            })
            predictions['risk_assessment']['stability_risk'] = 'medium'
            predictions['recommendations'].append('Стабилизировать параметры состояния')

        # Overall risk assessment
        risk_levels = predictions['risk_assessment'].values()
        if 'high' in risk_levels:
            predictions['overall_risk'] = 'high'
            predictions['confidence'] = 0.8
        elif 'medium' in risk_levels:
            predictions['overall_risk'] = 'medium'
            predictions['confidence'] = 0.6
        else:
            predictions['overall_risk'] = 'low'
            predictions['confidence'] = 0.4

        return predictions

    def analyze_state_context(self, state_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze contextual relationships between state parameters.

        Args:
            state_data: Current state data (energy, stability, integrity, etc.)

        Returns:
            Contextual state analysis
        """
        if state_data is None:
            # Use accumulated impact data as proxy for state analysis
            state_data = {}
            for param in ['energy', 'integrity', 'stability']:
                impacts = self.impact_accumulators.get(param, [])
                if impacts:
                    # Use recent average impact as proxy for current state
                    recent_impacts = impacts[-10:] if len(impacts) > 10 else impacts
                    state_data[param] = sum(recent_impacts) / len(recent_impacts)

        if not state_data:
            return {'analysis': 'insufficient_state_data'}

        context_analysis = {
            'state_profile': self._create_state_profile(state_data),
            'interactions': self._analyze_state_interactions(state_data),
            'resilience_indicators': self._calculate_resilience_indicators(state_data),
            'adaptation_capacity': self._assess_adaptation_capacity(state_data),
            'risk_factors': self._identify_state_risks(state_data),
            'recommendations': self._generate_state_recommendations(state_data),
            'temporal_patterns': self._analyze_state_temporal_patterns(),
            'timestamp': time.time()
        }

        return context_analysis

    def _create_state_profile(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive profile of the current system state."""
        profile = {}

        # Energy profile
        energy = state_data.get('energy', 50.0)
        profile['energy_profile'] = {
            'level': energy,
            'status': 'high' if energy > 70 else 'medium' if energy > 30 else 'low',
            'stability_risk': 'high' if energy < 20 else 'medium' if energy < 40 else 'low'
        }

        # Integrity profile
        integrity = state_data.get('integrity', 0.8)
        profile['integrity_profile'] = {
            'level': integrity,
            'status': 'robust' if integrity > 0.8 else 'compromised' if integrity > 0.5 else 'critical',
            'coherence': 'high' if integrity > 0.9 else 'medium' if integrity > 0.7 else 'low'
        }

        # Stability profile
        stability = state_data.get('stability', 0.8)
        profile['stability_profile'] = {
            'level': stability,
            'status': 'stable' if stability > 0.8 else 'unstable' if stability > 0.5 else 'chaotic',
            'predictability': 'high' if stability > 0.9 else 'medium' if stability > 0.7 else 'low'
        }

        # Subjective time profile
        subj_time = state_data.get('subjective_time', 0.0)
        profile['temporal_profile'] = {
            'subjective_time': subj_time,
            'time_dilation': 'normal',  # Would need more context to determine
            'experience_intensity': 'moderate'  # Would need event correlation
        }

        # Overall system profile
        profile['system_profile'] = {
            'overall_health': self._calculate_overall_health_score(state_data),
            'dominant_state': self._determine_dominant_state(state_data),
            'system_phase': self._determine_system_phase(state_data)
        }

        return profile

    def _analyze_state_interactions(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze interactions between different state parameters."""
        interactions = {}

        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Energy-Integrity interaction
        energy_integrity_corr = self._calculate_correlation(
            self.impact_accumulators.get('energy', []),
            self.impact_accumulators.get('integrity', [])
        )
        interactions['energy_integrity'] = {
            'correlation': energy_integrity_corr,
            'relationship': 'reinforcing' if energy_integrity_corr > 0.3 else 'neutral' if energy_integrity_corr > -0.3 else 'conflicting',
            'description': 'Energy and integrity tend to change together' if abs(energy_integrity_corr) > 0.3 else 'Energy and integrity changes are independent'
        }

        # Stability-Energy interaction
        stability_energy_corr = self._calculate_correlation(
            self.impact_accumulators.get('stability', []),
            self.impact_accumulators.get('energy', [])
        )
        interactions['stability_energy'] = {
            'correlation': stability_energy_corr,
            'relationship': 'supportive' if stability_energy_corr > 0.2 else 'challenging',
            'description': 'Stability supports energy maintenance' if stability_energy_corr > 0.2 else 'Stability may drain energy resources'
        }

        # Integrity-Stability interaction
        integrity_stability_corr = self._calculate_correlation(
            self.impact_accumulators.get('integrity', []),
            self.impact_accumulators.get('stability', [])
        )
        interactions['integrity_stability'] = {
            'correlation': integrity_stability_corr,
            'relationship': 'complementary' if integrity_stability_corr > 0.4 else 'independent',
            'description': 'Integrity and stability reinforce each other' if integrity_stability_corr > 0.4 else 'Integrity and stability operate somewhat independently'
        }

        # Three-way interaction analysis
        interactions['system_dynamics'] = self._analyze_three_way_dynamics(energy, integrity, stability)

        return interactions

    def _calculate_resilience_indicators(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resilience indicators based on state parameters."""
        indicators = {}

        # Recovery capacity (based on energy and integrity interaction)
        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)

        recovery_capacity = (energy / 100.0) * integrity
        indicators['recovery_capacity'] = {
            'score': recovery_capacity,
            'level': 'high' if recovery_capacity > 0.7 else 'medium' if recovery_capacity > 0.4 else 'low',
            'description': 'Ability to recover from adverse events'
        }

        # Adaptation flexibility (based on stability range and integrity)
        stability = state_data.get('stability', 0.8)
        stability_range = self._calculate_stability_range()

        adaptation_flexibility = stability * integrity * (1 + stability_range)
        indicators['adaptation_flexibility'] = {
            'score': min(1.0, adaptation_flexibility),
            'level': 'high' if adaptation_flexibility > 0.8 else 'medium' if adaptation_flexibility > 0.5 else 'low',
            'description': 'Ability to adapt to changing conditions'
        }

        # Stress tolerance (inverse of volatility)
        state_volatility = self._calculate_overall_state_volatility()
        stress_tolerance = 1.0 - min(1.0, state_volatility)
        indicators['stress_tolerance'] = {
            'score': stress_tolerance,
            'level': 'high' if stress_tolerance > 0.7 else 'medium' if stress_tolerance > 0.4 else 'low',
            'description': 'Tolerance for environmental stress'
        }

        # Overall resilience
        overall_resilience = (recovery_capacity + adaptation_flexibility + stress_tolerance) / 3.0
        indicators['overall_resilience'] = {
            'score': overall_resilience,
            'level': 'resilient' if overall_resilience > 0.7 else 'vulnerable' if overall_resilience > 0.4 else 'fragile'
        }

        return indicators

    def _assess_adaptation_capacity(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the system's capacity for adaptation."""
        capacity = {}

        # Learning capacity (based on integrity and recent experience)
        integrity = state_data.get('integrity', 0.8)
        recent_experience = len([c for c in self.correlation_chains.values()
                               if any(e.get('timestamp', 0) > time.time() - 3600 for e in c)])

        learning_capacity = integrity * min(1.0, recent_experience / 50.0)
        capacity['learning_capacity'] = {
            'score': learning_capacity,
            'level': 'strong' if learning_capacity > 0.7 else 'moderate' if learning_capacity > 0.4 else 'limited',
            'factors': ['system_integrity', 'experience_accumulation']
        }

        # Response flexibility (based on decision pattern diversity)
        decision_patterns = list(self.decision_pattern_frequencies.keys())
        pattern_diversity = len(decision_patterns) / max(1, len(self.decision_pattern_frequencies))

        response_flexibility = pattern_diversity * 0.8  # Scale down slightly
        capacity['response_flexibility'] = {
            'score': response_flexibility,
            'level': 'flexible' if response_flexibility > 0.6 else 'moderate' if response_flexibility > 0.3 else 'rigid',
            'factors': ['decision_pattern_diversity', 'behavioral_repertoire']
        }

        # Recovery speed (based on energy recovery patterns)
        energy_impacts = self.impact_accumulators.get('energy', [])
        if len(energy_impacts) >= 5:
            # Look for recovery patterns (positive impacts after negative)
            recovery_instances = 0
            for i in range(1, len(energy_impacts)):
                if energy_impacts[i-1] < -0.1 and energy_impacts[i] > 0.05:
                    recovery_instances += 1

            recovery_rate = recovery_instances / max(1, len(energy_impacts) - 1)
            recovery_speed = recovery_rate * 2.0  # Scale up for visibility
        else:
            recovery_speed = 0.5  # Neutral assumption

        capacity['recovery_speed'] = {
            'score': min(1.0, recovery_speed),
            'level': 'fast' if recovery_speed > 0.7 else 'moderate' if recovery_speed > 0.4 else 'slow',
            'factors': ['energy_recovery_patterns', 'adaptation_effectiveness']
        }

        return capacity

    def _identify_state_risks(self, state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential risks based on state analysis."""
        risks = []

        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Critical energy risk
        if energy < 20:
            risks.append({
                'risk_type': 'energy_critical',
                'severity': 'high',
                'description': 'Energy levels critically low, system may become unresponsive',
                'indicators': [f'energy={energy:.1f}'],
                'mitigation': 'Prioritize energy recovery, reduce activity'
            })

        # Integrity degradation risk
        if integrity < 0.4:
            risks.append({
                'risk_type': 'integrity_compromised',
                'severity': 'high',
                'description': 'System integrity severely compromised',
                'indicators': [f'integrity={integrity:.2f}'],
                'mitigation': 'Focus on integrity restoration, avoid complex operations'
            })

        # Instability risk
        stability_volatility = self._calculate_stability_range()
        if stability < 0.5 or stability_volatility > 0.8:
            risks.append({
                'risk_type': 'behavioral_instability',
                'severity': 'medium',
                'description': 'System behavior is unstable or unpredictable',
                'indicators': [f'stability={stability:.2f}', f'volatility={stability_volatility:.2f}'],
                'mitigation': 'Stabilize operations, reduce environmental complexity'
            })

        # Cascade risk (multiple parameters degraded)
        degraded_count = sum(1 for val in [energy < 30, integrity < 0.6, stability < 0.6] if val)
        if degraded_count >= 2:
            risks.append({
                'risk_type': 'cascade_failure',
                'severity': 'high',
                'description': 'Multiple state parameters degraded, risk of cascade failure',
                'indicators': [f'{degraded_count}_parameters_degraded'],
                'mitigation': 'Comprehensive system stabilization required'
            })

        return risks

    def _generate_state_recommendations(self, state_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on state analysis."""
        recommendations = []

        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Energy recommendations
        if energy < 40:
            recommendations.append("Увеличить фокус на восстановлении энергии")
        elif energy > 80:
            recommendations.append("Энергия на высоком уровне - можно увеличить активность")

        # Integrity recommendations
        if integrity < 0.7:
            recommendations.append("Приоритет - восстановление целостности системы")
        else:
            recommendations.append("Целостность в хорошем состоянии - поддерживать стабильность")

        # Stability recommendations
        stability_volatility = self._calculate_stability_range()
        if stability_volatility > 0.6:
            recommendations.append("Снизить волатильность - стабилизировать поведенческие паттерны")

        # Interaction-based recommendations
        interactions = self._analyze_state_interactions(state_data)
        energy_integrity = interactions.get('energy_integrity', {})

        if energy_integrity.get('correlation', 0) < -0.5:
            recommendations.append("Разрешить конфликт между энергией и целостностью - сбалансировать приоритеты")

        # Overall system recommendations
        health_score = self._calculate_overall_health_score(state_data)
        if health_score < 0.5:
            recommendations.append("Общее состояние системы требует внимания - начать восстановление")
        elif health_score > 0.8:
            recommendations.append("Система в отличном состоянии - можно экспериментировать с новыми паттернами")

        return recommendations

    def _analyze_state_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns in state evolution."""
        patterns = {}

        # Analyze energy patterns over time
        energy_impacts = list(self.impact_accumulators.get('energy', []))
        if len(energy_impacts) >= 10:
            patterns['energy_patterns'] = self._detect_temporal_patterns(energy_impacts, 'energy')

        # Analyze integrity patterns
        integrity_impacts = list(self.impact_accumulators.get('integrity', []))
        if len(integrity_impacts) >= 10:
            patterns['integrity_patterns'] = self._detect_temporal_patterns(integrity_impacts, 'integrity')

        # Analyze stability patterns
        stability_impacts = list(self.impact_accumulators.get('stability', []))
        if len(stability_impacts) >= 10:
            patterns['stability_patterns'] = self._detect_temporal_patterns(stability_impacts, 'stability')

        # Cross-parameter temporal correlations
        if all(len(self.impact_accumulators.get(param, [])) >= 10 for param in ['energy', 'integrity', 'stability']):
            patterns['cross_parameter_patterns'] = self._analyze_cross_parameter_temporal_patterns()

        return patterns

    def _detect_temporal_patterns(self, values: List[float], param_name: str) -> Dict[str, Any]:
        """Detect temporal patterns in a parameter's values."""
        if len(values) < 5:
            return {'pattern': 'insufficient_data'}

        # Simple pattern detection
        patterns = {
            'trend': 'stable',
            'volatility': self._calculate_volatility(values),
            'cyclical': False,
            'recovery_instances': 0
        }

        # Trend analysis
        if len(values) >= 3:
            slope = self._calculate_trend_slope(values)
            if slope > 0.01:
                patterns['trend'] = 'improving'
            elif slope < -0.01:
                patterns['trend'] = 'degrading'
            else:
                patterns['trend'] = 'stable'

        # Recovery pattern detection
        for i in range(1, len(values)):
            if values[i-1] < -0.05 and values[i] > 0.05:
                patterns['recovery_instances'] += 1

        # Simple cyclical detection (very basic)
        if len(values) >= 10:
            # Look for repeating patterns in chunks
            chunk_size = 5
            chunks = [values[i:i+chunk_size] for i in range(0, len(values)-chunk_size+1, chunk_size)]
            if len(chunks) >= 3:
                # Very simple similarity check
                similarities = []
                for i in range(len(chunks)-1):
                    similarity = self._calculate_sequence_similarity(chunks[i], chunks[i+1])
                    similarities.append(similarity)

                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                patterns['cyclical'] = avg_similarity > 0.7

        return patterns

    def _analyze_cross_parameter_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal relationships between different parameters."""
        patterns = {}

        # Get aligned time series (simplified - assume same length)
        energy = list(self.impact_accumulators.get('energy', []))
        integrity = list(self.impact_accumulators.get('integrity', []))
        stability = list(self.impact_accumulators.get('stability', []))

        min_length = min(len(energy), len(integrity), len(stability))
        if min_length < 5:
            return {'analysis': 'insufficient_data'}

        energy = energy[-min_length:]
        integrity = integrity[-min_length:]
        stability = stability[-min_length:]

        # Analyze leading/lagging relationships
        correlations = {
            'energy_integrity': self._calculate_correlation(energy, integrity),
            'energy_stability': self._calculate_correlation(energy, stability),
            'integrity_stability': self._calculate_correlation(integrity, stability)
        }

        patterns['correlations'] = correlations

        # Detect cascade patterns (one parameter change leading to others)
        cascades = []
        for i in range(1, min_length):
            changes = {
                'energy': energy[i] - energy[i-1],
                'integrity': integrity[i] - integrity[i-1],
                'stability': stability[i] - stability[i-1]
            }

            # Look for significant changes followed by others
            significant_changes = [param for param, change in changes.items() if abs(change) > 0.1]

            if len(significant_changes) >= 2:
                cascades.append({
                    'initiator': significant_changes[0],
                    'followers': significant_changes[1:],
                    'index': i
                })

        patterns['cascades'] = cascades
        patterns['cascade_frequency'] = len(cascades) / max(1, min_length)

        return patterns

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        min_len = min(len(x), len(y))
        if min_len < 2:
            return 0.0

        x = x[-min_len:]
        y = y[-min_len:]

        mean_x = sum(x) / min_len
        mean_y = sum(y) / min_len

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = (sum((xi - mean_x)**2 for xi in x) * sum((yi - mean_y)**2 for yi in y)) ** 0.5

        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_stability_range(self) -> float:
        """Calculate the range of stability variations."""
        stability_impacts = self.impact_accumulators.get('stability', [])
        if len(stability_impacts) < 3:
            return 0.0

        return max(stability_impacts) - min(stability_impacts)

    def _calculate_overall_state_volatility(self) -> float:
        """Calculate overall volatility across all state parameters."""
        volatilities = []
        for param in ['energy', 'integrity', 'stability']:
            impacts = self.impact_accumulators.get(param, [])
            if len(impacts) >= 3:
                volatility = self._calculate_volatility(impacts)
                volatilities.append(volatility)

        return sum(volatilities) / len(volatilities) if volatilities else 0.0

    def _calculate_overall_health_score(self, state_data: Dict[str, Any]) -> float:
        """Calculate overall health score from state parameters."""
        energy = state_data.get('energy', 50.0) / 100.0  # Normalize to 0-1
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        # Weighted average
        health_score = (
            energy * 0.4 +      # Energy is important but can be managed
            integrity * 0.4 +   # Integrity is critical
            stability * 0.2     # Stability affects predictability
        )

        return health_score

    def _determine_dominant_state(self, state_data: Dict[str, Any]) -> str:
        """Determine the dominant state characteristic."""
        energy = state_data.get('energy', 50.0)
        integrity = state_data.get('integrity', 0.8)
        stability = state_data.get('stability', 0.8)

        if energy < 30:
            return 'energy_depleted'
        elif integrity < 0.5:
            return 'integrity_compromised'
        elif stability < 0.6:
            return 'behaviorally_unstable'
        elif energy > 80 and integrity > 0.9 and stability > 0.9:
            return 'peak_performance'
        else:
            return 'balanced_operation'

    def _determine_system_phase(self, state_data: Dict[str, Any]) -> str:
        """Determine the current system operational phase."""
        health_score = self._calculate_overall_health_score(state_data)

        if health_score > 0.8:
            return 'optimal_operation'
        elif health_score > 0.6:
            return 'normal_operation'
        elif health_score > 0.4:
            return 'degraded_operation'
        elif health_score > 0.2:
            return 'critical_operation'
        else:
            return 'emergency_operation'

    def _analyze_three_way_dynamics(self, energy: float, integrity: float, stability: float) -> Dict[str, Any]:
        """Analyze the three-way dynamics between energy, integrity, and stability."""
        # Normalize values for comparison
        energy_norm = energy / 100.0
        integrity_norm = integrity
        stability_norm = stability

        # Calculate balance score (how close the parameters are to each other)
        values = [energy_norm, integrity_norm, stability_norm]
        balance_score = 1.0 - (max(values) - min(values))  # Higher when values are closer

        # Determine dynamic state
        if balance_score > 0.8:
            dynamic_state = 'harmonious'
            description = 'Параметры хорошо сбалансированы, система работает гармонично'
        elif balance_score > 0.6:
            dynamic_state = 'balanced'
            description = 'Параметры reasonably сбалансированы'
        elif balance_score > 0.4:
            dynamic_state = 'unbalanced'
            description = 'Параметры несбалансированы, возможны конфликты'
        else:
            dynamic_state = 'conflicting'
            description = 'Параметры сильно несбалансированы, система в напряжении'

        # Identify potential issues
        issues = []
        if energy_norm < 0.3:
            issues.append('low_energy_draining_others')
        if integrity_norm < 0.6:
            issues.append('integrity_compromising_stability')
        if stability_norm < 0.6:
            issues.append('instability_affecting_coherence')

        return {
            'dynamic_state': dynamic_state,
            'balance_score': balance_score,
            'description': description,
            'potential_issues': issues
        }

    def _calculate_sequence_similarity(self, seq1: List[float], seq2: List[float]) -> float:
        """Calculate similarity between two sequences (simple Euclidean distance)."""
        if len(seq1) != len(seq2):
            return 0.0

        distance = sum((a - b) ** 2 for a, b in zip(seq1, seq2)) ** 0.5
        max_possible_distance = (len(seq1) * 2.0) ** 0.5  # Rough maximum

        return 1.0 - min(1.0, distance / max_possible_distance)

    def reset_analysis(self):
        """Reset analysis state for fresh analysis."""
        self.semantic_patterns.clear()
        self.behavioral_anomalies.clear()
        self.correlation_chains.clear()
        self.state_evolution.clear()
        self.event_type_frequencies.clear()
        self.decision_pattern_frequencies.clear()
        self.impact_accumulators.clear()
        logger.info("Semantic analysis state reset")
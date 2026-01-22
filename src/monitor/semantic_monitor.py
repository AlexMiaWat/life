"""
Semantic Monitor for Life system anomaly detection.

Provides continuous monitoring of behavioral patterns and semantic analysis
to detect anomalies in system behavior using deep event chain analysis.

ARCHITECTURE:
- Passive monitoring integrated into runtime loop (no active threads)
- Real-time semantic analysis with neural network processing
- Performance metrics and efficiency tracking
- Integration with observability pipeline
"""

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None
import os

from src.observability.semantic_analysis_engine import (
    SemanticAnalysisEngine,
    BehavioralAnomaly,
    SystemHealthProfile
)
from src.config.observability_config import get_observability_config, SemanticMonitorConfig

logger = logging.getLogger(__name__)


@dataclass
class MonitorConfig:
    """Configuration for Semantic Monitor."""
    enabled: bool = True
    anomaly_threshold: float = 0.7
    analysis_interval_ticks: int = 50  # Analysis every N ticks instead of time
    max_cached_analyses: int = 1000
    anomaly_log_file: str = "logs/semantic_anomalies.jsonl"
    health_check_interval_ticks: int = 300  # Health check every N ticks
    cache_ttl_seconds: float = 300.0  # 5 minutes
    log_anomalies: bool = True
    enable_performance_metrics: bool = True
    performance_log_file: str = "logs/semantic_performance.jsonl"
    alert_callbacks: List[Callable] = field(default_factory=list)

    @classmethod
    def from_semantic_config(cls, config: SemanticMonitorConfig) -> 'MonitorConfig':
        """Create MonitorConfig from SemanticMonitorConfig."""
        return cls(
            enabled=config.enabled,
            anomaly_threshold=config.anomaly_threshold,
            analysis_interval_ticks=config.analysis_interval_ticks,
            max_cached_analyses=config.max_cached_analyses,
            anomaly_log_file=config.anomaly_log_file,
            health_check_interval_ticks=config.health_check_interval_ticks,
            cache_ttl_seconds=config.cache_ttl_seconds,
            log_anomalies=config.log_anomalies,
            enable_performance_metrics=config.enable_performance_metrics,
            performance_log_file=config.performance_log_file
        )


@dataclass
class CachedAnalysis:
    """Cached analysis result."""
    correlation_id: str
    analysis_result: Dict[str, Any]
    timestamp: float
    anomalies: List[BehavioralAnomaly]

    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > ttl_seconds


class SemanticMonitor:
    """
    Semantic Monitor for detecting behavioral anomalies in Life system.

    Integrated into runtime loop for passive monitoring without active threads.
    Provides real-time semantic analysis with performance metrics and efficiency tracking.
    """

    def __init__(self, config: MonitorConfig = None):
        """
        Initialize the Semantic Monitor.

        Args:
            config: Monitor configuration. If None, loads from observability config.
        """
        if config is None:
            # Load configuration from observability config
            obs_config = get_observability_config()
            self.config = MonitorConfig.from_semantic_config(obs_config.semantic_monitor)
        else:
            self.config = config

        # Core components
        self.analysis_engine = SemanticAnalysisEngine(
            max_patterns=500,
            anomaly_threshold=self.config.anomaly_threshold
        )

        # Analysis cache
        self.analysis_cache: Dict[str, CachedAnalysis] = {}
        self.cache_access_order = deque(maxlen=self.config.max_cached_analyses)

        # Cache performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_hit_rate_history = deque(maxlen=100)  # Track hit rate over time

        # Monitoring state (tick-based instead of time-based)
        self.is_enabled = self.config.enabled
        self.ticks_since_last_analysis = 0
        self.ticks_since_last_health_check = 0
        self.analysis_count = 0
        self.anomaly_count = 0
        self.last_health_check_time = 0.0

        # Performance metrics
        self.performance_metrics = {
            'analysis_times': deque(maxlen=1000),  # Last 1000 analysis times
            'memory_usage': deque(maxlen=100),     # Memory usage over time
            'cache_hit_rates': deque(maxlen=100),  # Cache performance
            'anomaly_detection_rates': deque(maxlen=100),  # Detection accuracy
            'false_positive_rate': 0.0,
            'analysis_throughput': 0.0,  # analyses per second
            'memory_efficiency': 0.0,     # memory used vs cache size
        }

        # Initialize logging
        self._setup_logging()

        logger.info("SemanticMonitor initialized (passive monitoring mode)")

    def _setup_logging(self):
        """Setup anomaly logging."""
        if self.config.log_anomalies:
            anomaly_log_path = Path(self.config.anomaly_log_file)
            anomaly_log_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Anomaly logging enabled: {anomaly_log_path}")

    def tick_update(self, current_tick: int, event_queue_size: int = 0) -> Dict[str, Any]:
        """
        Update monitor state for current tick. Called from runtime loop.

        Args:
            current_tick: Current runtime tick
            event_queue_size: Size of event queue for performance monitoring

        Returns:
            Dict with analysis results if analysis was performed, empty dict otherwise
        """
        if not self.is_enabled:
            return {}

        results = {}

        # Update tick counters
        self.ticks_since_last_analysis += 1
        self.ticks_since_last_health_check += 1

        # Periodic analysis
        if self.ticks_since_last_analysis >= self.config.analysis_interval_ticks:
            try:
                analysis_start = time.time()

                # Perform semantic analysis on recent chains
                analysis_results = self._perform_periodic_analysis()

                analysis_time = time.time() - analysis_start
                self.performance_metrics['analysis_times'].append(analysis_time)

                # Update performance metrics
                self._update_performance_metrics(analysis_time, event_queue_size)

                results = analysis_results
                self.ticks_since_last_analysis = 0

            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")

        # Periodic health check
        if self.ticks_since_last_health_check >= self.config.health_check_interval_ticks:
            try:
                health_results = self._perform_health_check()
                results.update(health_results)
                self.ticks_since_last_health_check = 0
                self.last_health_check_time = time.time()
            except Exception as e:
                logger.error(f"Error in health check: {e}")

        # Clean expired cache periodically
        if current_tick % 100 == 0:  # Every 100 ticks
            self._clean_expired_cache()

        # Log performance metrics periodically
        if current_tick % 500 == 0:  # Every 500 ticks
            self._log_performance_metrics()

        return results

    def enable_monitoring(self):
        """Enable semantic monitoring."""
        self.is_enabled = True
        logger.info("Semantic monitoring enabled")

    def disable_monitoring(self):
        """Disable semantic monitoring."""
        self.is_enabled = False
        logger.info("Semantic monitoring disabled")

    def analyze_correlation_chain(self, correlation_id: str, chain_entries: List[Dict]) -> Dict[str, Any]:
        """
        Analyze a correlation chain for anomalies.

        Args:
            correlation_id: Correlation ID for the chain
            chain_entries: List of log entries in the chain

        Returns:
            Analysis results with anomaly detection
        """
        # Check cache first
        if correlation_id in self.analysis_cache:
            cached = self.analysis_cache[correlation_id]
            if not cached.is_expired(self.config.cache_ttl_seconds):
                self.cache_access_order.append(correlation_id)
                self.cache_hits += 1  # Track cache hit
                return {
                    'correlation_id': correlation_id,
                    'analysis_result': cached.analysis_result,
                    'anomalies': [self._anomaly_to_dict(a) for a in cached.anomalies],
                    'cached': True,
                    'timestamp': cached.timestamp
                }

        # Track cache miss
        self.cache_misses += 1

        # Perform fresh analysis
        try:
            # Semantic analysis
            analysis_result = self.analysis_engine.analyze_correlation_chain(
                correlation_id, chain_entries
            )

            # Anomaly detection
            anomalies = self.analysis_engine.detect_anomalies(analysis_result)

            # Update counters
            self.analysis_count += 1
            self.anomaly_count += len(anomalies)

            # Log anomalies
            self._log_anomalies(anomalies, analysis_result)

            # Trigger alerts
            self._trigger_alerts(anomalies, analysis_result)

            # Cache result
            self._cache_analysis(correlation_id, analysis_result, anomalies)

            return {
                'correlation_id': correlation_id,
                'analysis_result': analysis_result,
                'anomalies': [self._anomaly_to_dict(a) for a in anomalies],
                'cached': False,
                'timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Error analyzing correlation chain {correlation_id}: {e}")
            return {
                'correlation_id': correlation_id,
                'error': str(e),
                'anomalies': [],
                'cached': False,
                'timestamp': time.time()
            }

    def get_system_health(self) -> SystemHealthProfile:
        """
        Get current system health assessment.

        Returns:
            System health profile
        """
        try:
            # Use recent correlation chains for health assessment
            recent_chains = list(self.analysis_engine.correlation_chains.values())[-50:]
            return self.analysis_engine.analyze_system_health(recent_chains)
        except Exception as e:
            logger.error(f"Error assessing system health: {e}")
            # Return minimal health profile on error
            return SystemHealthProfile(
                energy_stability=0.5,
                cognitive_coherence=0.5,
                adaptation_efficiency=0.5,
                memory_integrity=0.5,
                overall_health=0.5,
                risk_factors=["Health assessment failed"],
                recommendations=["Check monitor logs"]
            )

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring statistics including performance metrics.

        Returns:
            Dictionary with monitoring statistics
        """
        cache_size = len(self.analysis_cache)
        cache_hit_rate = self._calculate_cache_hit_rate()

        # Calculate performance metrics averages
        perf_stats = {
            'avg_analysis_time': 0.0,
            'avg_memory_usage': 0.0,
            'avg_cache_hit_rate': 0.0,
            'analysis_throughput': self.performance_metrics['analysis_throughput'],
            'memory_efficiency': self.performance_metrics['memory_efficiency'],
            'false_positive_rate': self.performance_metrics['false_positive_rate']
        }

        # Average analysis time
        if self.performance_metrics['analysis_times']:
            perf_stats['avg_analysis_time'] = sum(self.performance_metrics['analysis_times']) / len(self.performance_metrics['analysis_times'])

        # Average memory usage
        if HAS_PSUTIL and self.performance_metrics['memory_usage']:
            perf_stats['avg_memory_usage'] = sum(self.performance_metrics['memory_usage']) / len(self.performance_metrics['memory_usage'])

        # Average cache hit rate
        if self.performance_metrics['cache_hit_rates']:
            perf_stats['avg_cache_hit_rate'] = sum(self.performance_metrics['cache_hit_rates']) / len(self.performance_metrics['cache_hit_rates'])

        # Detailed cache statistics
        cache_stats = {
            'size': cache_size,
            'max_size': self.config.max_cached_analyses,
            'utilization': cache_size / self.config.max_cached_analyses if self.config.max_cached_analyses > 0 else 0.0,
            'hit_rate': cache_hit_rate,
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total_accesses': self.cache_hits + self.cache_misses,
            'ttl_seconds': self.config.cache_ttl_seconds,
            'hit_rate_trend': list(self.cache_hit_rate_history)[-5:] if self.cache_hit_rate_history else []  # Last 5 measurements
        }

        # Get detailed performance metrics from analysis engine
        detailed_metrics = self.analysis_engine.get_detailed_performance_metrics()

        return {
            'is_enabled': self.is_enabled,
            'analysis_count': self.analysis_count,
            'anomaly_count': self.anomaly_count,
            'cache_stats': cache_stats,
            'analysis_engine_stats': self._get_engine_stats(),
            'performance_metrics': perf_stats,
            'detailed_accuracy_metrics': detailed_metrics,
            'ticks_since_last_analysis': self.ticks_since_last_analysis,
            'ticks_since_last_health_check': self.ticks_since_last_health_check,
            'last_health_check_time': self.last_health_check_time,
            'timestamp': time.time()
        }

    def update_config(self, new_config: MonitorConfig):
        """
        Update monitor configuration.

        Args:
            new_config: New configuration to apply
        """
        old_enabled = self.config.enabled
        self.config = new_config

        # Update analysis engine threshold
        self.analysis_engine.anomaly_threshold = new_config.anomaly_threshold

        # Handle enable/disable changes
        if old_enabled != new_config.enabled:
            if new_config.enabled:
                self.enable_monitoring()
            else:
                self.disable_monitoring()

        # Reset tick counters if intervals changed
        if hasattr(new_config, 'analysis_interval_ticks'):
            self.ticks_since_last_analysis = 0
        if hasattr(new_config, 'health_check_interval_ticks'):
            self.ticks_since_last_health_check = 0

        logger.info("Monitor configuration updated")

    def add_alert_callback(self, callback: Callable):
        """
        Add a callback for anomaly alerts.

        Args:
            callback: Function to call when anomalies are detected
        """
        self.config.alert_callbacks.append(callback)

    def clear_cache(self):
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        self.cache_access_order.clear()
        # Reset cache performance counters
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_hit_rate_history.clear()
        logger.info("Analysis cache cleared")

    def _perform_periodic_analysis(self) -> Dict[str, Any]:
        """
        Perform periodic semantic analysis of recent correlation chains.

        Returns:
            Dict with analysis results
        """
        # Get recent chains for analysis (last 50 chains)
        recent_chains = list(self.analysis_engine.correlation_chains.values())[-50:]
        if not recent_chains:
            return {'analysis_type': 'periodic', 'status': 'no_recent_chains'}

        results = {
            'analysis_type': 'periodic',
            'chains_analyzed': len(recent_chains),
            'timestamp': time.time()
        }

        # Analyze system health trends
        health_profile = self.analysis_engine.analyze_system_health(recent_chains)
        results['health_profile'] = {
            'overall_health': health_profile.overall_health,
            'energy_stability': health_profile.energy_stability,
            'cognitive_coherence': health_profile.cognitive_coherence,
            'adaptation_efficiency': health_profile.adaptation_efficiency,
            'memory_integrity': health_profile.memory_integrity,
            'risk_factors': health_profile.risk_factors[:3],  # Top 3 risks
            'recommendations': health_profile.recommendations[:3]  # Top 3 recommendations
        }

        # Analyze behavioral trends
        behavioral_trends = self.analysis_engine.analyze_behavioral_trends(time_window_seconds=300)  # Last 5 minutes
        results['behavioral_trends'] = behavioral_trends

        # Check for emerging anomalies
        anomalies = []
        for chain_id, chain in list(self.analysis_engine.correlation_chains.items())[-10:]:  # Last 10 chains
            analysis_result = self.analysis_engine.analyze_correlation_chain(chain_id, chain)
            chain_anomalies = self.analysis_engine.detect_anomalies(analysis_result)
            anomalies.extend(chain_anomalies)

        if anomalies:
            results['anomalies_detected'] = len(anomalies)
            results['anomaly_details'] = [
                {
                    'anomaly_id': a.anomaly_id,
                    'type': a.anomaly_type,
                    'severity': a.severity,
                    'description': a.description
                } for a in anomalies[:5]  # Top 5 anomalies
            ]
            self.anomaly_count += len(anomalies)
            self._trigger_alerts(anomalies, {'analysis_type': 'periodic_trend_analysis'})

        self.analysis_count += 1

        return results

    def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of the semantic monitoring system.

        Returns:
            Dict with health check results
        """
        health_results = {
            'health_check_type': 'comprehensive',
            'timestamp': time.time(),
            'monitor_enabled': self.is_enabled
        }

        # System health assessment
        system_health = self.get_system_health()
        health_results['system_health'] = {
            'overall_health': system_health.overall_health,
            'energy_stability': system_health.energy_stability,
            'cognitive_coherence': system_health.cognitive_coherence,
            'adaptation_efficiency': system_health.adaptation_efficiency,
            'memory_integrity': system_health.memory_integrity,
            'risk_factors_count': len(system_health.risk_factors),
            'recommendations_count': len(system_health.recommendations)
        }

        # Monitor performance metrics
        monitor_stats = self.get_monitoring_stats()
        health_results['monitor_stats'] = {
            'analysis_count': monitor_stats['analysis_count'],
            'anomaly_count': monitor_stats['anomaly_count'],
            'cache_size': monitor_stats['cache_size'],
            'cache_hit_rate': monitor_stats.get('cache_hit_rate', 0.0),
            'is_running': True  # Always running in passive mode
        }

        # Performance health indicators
        performance_health = self._assess_performance_health()
        health_results['performance_health'] = performance_health

        # Log health summary
        logger.info(
            f"Health check: system_health={system_health.overall_health:.2f}, "
            f"analyses={monitor_stats['analysis_count']}, "
            f"anomalies={monitor_stats['anomaly_count']}, "
            f"perf_health={performance_health['overall_score']:.2f}"
        )

        return health_results

    def _update_performance_metrics(self, analysis_time: float, event_queue_size: int):
        """
        Update internal performance metrics.

        Args:
            analysis_time: Time taken for last analysis
            event_queue_size: Current event queue size
        """
        # Memory usage (if psutil available)
        if HAS_PSUTIL:
            try:
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.performance_metrics['memory_usage'].append(memory_mb)
            except Exception as e:
                logger.debug(f"Could not get memory usage: {e}")
        else:
            # Fallback: estimate based on cache size
            estimated_memory = len(self.analysis_cache) * 0.01  # Rough estimate
            self.performance_metrics['memory_usage'].append(estimated_memory)

        # Cache performance metrics (updated less frequently to avoid overhead)
        if self.analysis_count % 10 == 0:  # Update every 10 analyses
            cache_hit_rate = self._calculate_cache_hit_rate()
            self.performance_metrics['cache_hit_rates'].append(cache_hit_rate)

        # Anomaly detection rate (simplified metric)
        if self.analysis_count > 0:
            detection_rate = min(1.0, self.anomaly_count / self.analysis_count)
            self.performance_metrics['anomaly_detection_rates'].append(detection_rate)

        # Analysis throughput (analyses per minute, approximated)
        if len(self.performance_metrics['analysis_times']) >= 10:
            recent_times = list(self.performance_metrics['analysis_times'])[-10:]
            avg_time = sum(recent_times) / len(recent_times)
            throughput = 60.0 / avg_time if avg_time > 0 else 0.0  # analyses per minute
            self.performance_metrics['analysis_throughput'] = throughput

        # Memory efficiency
        cache_size = len(self.analysis_cache)
        max_cache = self.config.max_cached_analyses
        memory_efficiency = cache_size / max_cache if max_cache > 0 else 0.0
        self.performance_metrics['memory_efficiency'] = memory_efficiency

    def _assess_performance_health(self) -> Dict[str, Any]:
        """
        Assess the health of performance metrics.

        Returns:
            Dict with performance health assessment
        """
        health = {
            'overall_score': 1.0,
            'indicators': {},
            'issues': []
        }

        # Memory usage health
        if self.performance_metrics['memory_usage']:
            avg_memory = sum(self.performance_metrics['memory_usage']) / len(self.performance_metrics['memory_usage'])
            memory_limit = 500.0  # MB limit
            memory_score = max(0.0, 1.0 - (avg_memory / memory_limit))
            health['indicators']['memory_usage'] = {
                'score': memory_score,
                'avg_mb': avg_memory,
                'status': 'healthy' if memory_score > 0.8 else 'warning' if memory_score > 0.5 else 'critical'
            }
            if memory_score < 0.7:
                health['issues'].append(f"High memory usage: {avg_memory:.1f} MB")

        # Analysis time health
        if self.performance_metrics['analysis_times']:
            avg_time = sum(self.performance_metrics['analysis_times']) / len(self.performance_metrics['analysis_times'])
            time_limit = 0.1  # 100ms limit
            time_score = max(0.0, 1.0 - (avg_time / time_limit))
            health['indicators']['analysis_time'] = {
                'score': time_score,
                'avg_seconds': avg_time,
                'status': 'healthy' if time_score > 0.8 else 'warning' if time_score > 0.5 else 'critical'
            }
            if time_score < 0.7:
                health['issues'].append(f"Slow analysis: {avg_time:.3f}s average")

        # Cache efficiency health
        if self.performance_metrics['cache_hit_rates']:
            avg_hit_rate = sum(self.performance_metrics['cache_hit_rates']) / len(self.performance_metrics['cache_hit_rates'])
            health['indicators']['cache_efficiency'] = {
                'score': avg_hit_rate,
                'avg_hit_rate': avg_hit_rate,
                'status': 'excellent' if avg_hit_rate > 0.8 else 'good' if avg_hit_rate > 0.6 else 'poor'
            }
            if avg_hit_rate < 0.5:
                health['issues'].append(f"Poor cache efficiency: {avg_hit_rate:.2f} hit rate")

        # Overall health score (weighted average)
        scores = [indicator['score'] for indicator in health['indicators'].values()]
        if scores:
            health['overall_score'] = sum(scores) / len(scores)

        return health

    def _log_performance_metrics(self):
        """Log current performance metrics to file."""
        if not self.config.enable_performance_metrics:
            return

        try:
            perf_log_path = Path(self.config.performance_log_file)
            perf_log_path.parent.mkdir(parents=True, exist_ok=True)

            stats = self.get_monitoring_stats()
            perf_entry = {
                'timestamp': time.time(),
                'analysis_count': stats['analysis_count'],
                'performance_metrics': stats['performance_metrics'],
                'cache_stats': stats['cache_stats'],  # Use full cache stats
                'anomaly_stats': {
                    'count': stats['anomaly_count'],
                    'rate': stats['anomaly_count'] / max(1, stats['analysis_count'])
                }
            }

            with perf_log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(perf_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.error(f"Error logging performance metrics: {e}")

    def _cache_analysis(self, correlation_id: str, analysis_result: Dict[str, Any],
                       anomalies: List[BehavioralAnomaly]):
        """Cache analysis result."""
        if len(self.analysis_cache) >= self.config.max_cached_analyses:
            # Remove oldest entry
            oldest_id = self.cache_access_order.popleft()
            if oldest_id in self.analysis_cache:
                del self.analysis_cache[oldest_id]

        # Add new entry
        self.analysis_cache[correlation_id] = CachedAnalysis(
            correlation_id=correlation_id,
            analysis_result=analysis_result,
            timestamp=time.time(),
            anomalies=anomalies
        )
        self.cache_access_order.append(correlation_id)

    def _clean_expired_cache(self):
        """Clean expired cache entries."""
        current_time = time.time()
        expired_ids = []

        for correlation_id, cached in self.analysis_cache.items():
            if cached.is_expired(self.config.cache_ttl_seconds):
                expired_ids.append(correlation_id)

        for correlation_id in expired_ids:
            del self.analysis_cache[correlation_id]
            try:
                self.cache_access_order.remove(correlation_id)
            except ValueError:
                pass  # Already removed

        if expired_ids:
            logger.debug(f"Cleaned {len(expired_ids)} expired cache entries")

    def _calculate_cache_hit_rate(self) -> float:
        """
        Calculate real cache hit rate based on tracked hits and misses.

        Returns hit rate as a float between 0.0 and 1.0.
        """
        total_accesses = self.cache_hits + self.cache_misses
        if total_accesses == 0:
            return 0.0

        hit_rate = self.cache_hits / total_accesses

        # Update hit rate history for performance tracking
        self.cache_hit_rate_history.append(hit_rate)

        return hit_rate

    def _log_anomalies(self, anomalies: List[BehavioralAnomaly],
                       analysis_result: Dict[str, Any]):
        """Log detected anomalies."""
        if not self.config.log_anomalies or not anomalies:
            return

        try:
            anomaly_log_path = Path(self.config.anomaly_log_file)
            anomaly_log_path.parent.mkdir(parents=True, exist_ok=True)

            with anomaly_log_path.open("a", encoding="utf-8") as f:
                for anomaly in anomalies:
                    log_entry = {
                        'timestamp': anomaly.timestamp,
                        'anomaly_id': anomaly.anomaly_id,
                        'type': anomaly.anomaly_type,
                        'severity': anomaly.severity,
                        'description': anomaly.description,
                        'correlation_ids': anomaly.correlation_ids,
                        'evidence': anomaly.evidence,
                        'analysis_context': {
                            'correlation_id': analysis_result.get('correlation_id'),
                            'semantic_category': analysis_result.get('semantic_category'),
                            'anomaly_score': analysis_result.get('anomaly_score')
                        }
                    }
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.error(f"Error logging anomalies: {e}")

    def _trigger_alerts(self, anomalies: List[BehavioralAnomaly],
                       analysis_result: Dict[str, Any]):
        """Trigger alert callbacks for anomalies."""
        if not anomalies or not self.config.alert_callbacks:
            return

        alert_data = {
            'anomalies': [self._anomaly_to_dict(a) for a in anomalies],
            'analysis_result': analysis_result,
            'timestamp': time.time()
        }

        for callback in self.config.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def _anomaly_to_dict(self, anomaly: BehavioralAnomaly) -> Dict[str, Any]:
        """Convert anomaly to dictionary."""
        return {
            'anomaly_id': anomaly.anomaly_id,
            'anomaly_type': anomaly.anomaly_type,
            'severity': anomaly.severity,
            'description': anomaly.description,
            'timestamp': anomaly.timestamp,
            'correlation_ids': anomaly.correlation_ids,
            'evidence': anomaly.evidence
        }

    def _get_engine_stats(self) -> Dict[str, Any]:
        """Get analysis engine statistics."""
        return {
            'patterns_count': len(self.analysis_engine.semantic_patterns),
            'chains_count': len(self.analysis_engine.correlation_chains),
            'anomalies_count': len(self.analysis_engine.behavioral_anomalies),
            'event_types_count': len(self.analysis_engine.event_type_frequencies),
            'decision_patterns_count': len(self.analysis_engine.decision_pattern_frequencies)
        }
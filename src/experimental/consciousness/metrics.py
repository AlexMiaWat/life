"""
Consciousness Metrics - Compatibility Layer

Backward compatibility for consciousness metrics API.
"""

import time
import statistics
from typing import Dict, List, Any, Optional
from collections import deque
from dataclasses import dataclass

from src.experimental.adaptive_processing_manager import AdaptiveProcessingManager


@dataclass
class MetricValue:
    """Represents a single metric measurement."""
    name: str
    value: float
    timestamp: float
    tags: Optional[Dict[str, str]] = None


class ConsciousnessMetrics:
    """Collects and analyzes consciousness-related metrics."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque[MetricValue]] = {}
        self.adaptive_manager = AdaptiveProcessingManager()

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.max_history)

        metric_value = MetricValue(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )

        self.metrics[name].append(metric_value)

        # Also record in adaptive manager for integration
        if name.startswith('consciousness_'):
            self.adaptive_manager.record_metric(f"legacy_{name}", value)

    def get_metric_values(self, name: str, limit: Optional[int] = None) -> List[MetricValue]:
        """Get metric values for a given name."""
        if name not in self.metrics:
            return []

        values = list(self.metrics[name])
        if limit:
            values = values[-limit:]
        return values

    def get_metric_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return {}

        values = [mv.value for mv in self.metrics[name]]

        try:
            return {
                'count': len(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values),
                'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                'latest': values[-1],
                'earliest': values[0]
            }
        except statistics.StatisticsError:
            return {'count': len(values), 'latest': values[-1]}

    def get_all_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all metrics."""
        summary = {}
        for name in self.metrics.keys():
            summary[name] = self.get_metric_stats(name)
        return summary

    def get_consciousness_health_score(self) -> float:
        """Calculate overall consciousness health score based on metrics."""
        relevant_metrics = ['processing_efficiency', 'error_rate', 'response_time', 'clarity_level']

        scores = []
        for metric in relevant_metrics:
            if metric in self.metrics and self.metrics[metric]:
                stats = self.get_metric_stats(metric)
                if metric == 'error_rate':
                    # Lower error rate is better
                    score = max(0, 1.0 - stats.get('mean', 0))
                elif metric == 'response_time':
                    # Lower response time is better (normalized)
                    mean_time = stats.get('mean', 1.0)
                    score = max(0, 1.0 - (mean_time / 10.0))  # Assume 10s is bad
                else:
                    # Higher values are better for other metrics
                    score = min(1.0, stats.get('mean', 0))
                scores.append(score)

        # Also include adaptive processing health
        adaptive_health = self.adaptive_manager.get_system_health_score()
        scores.append(adaptive_health)

        return statistics.mean(scores) if scores else 0.5

    def get_performance_trends(self, name: str, window: int = 10) -> Dict[str, Any]:
        """Analyze performance trends for a metric."""
        values = self.get_metric_values(name, limit=window*2)
        if len(values) < window:
            return {'trend': 'insufficient_data'}

        # Split into two windows for comparison
        mid = len(values) // 2
        first_half = [v.value for v in values[:mid]]
        second_half = [v.value for v in values[mid:]]

        try:
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)

            if second_avg > first_avg * 1.05:
                trend = 'improving'
            elif second_avg < first_avg * 0.95:
                trend = 'degrading'
            else:
                trend = 'stable'

            return {
                'trend': trend,
                'change_percent': ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0,
                'first_window_avg': first_avg,
                'second_window_avg': second_avg
            }
        except statistics.StatisticsError:
            return {'trend': 'calculation_error'}

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format."""
        if format == 'json':
            import json
            return json.dumps({
                'metrics': {name: [mv.__dict__ for mv in values]
                           for name, values in self.metrics.items()},
                'adaptive_stats': self.adaptive_manager.get_processing_statistics()
            }, indent=2, default=str)
        else:
            # Simple text format
            lines = []
            for name, values in self.metrics.items():
                lines.append(f"Metric: {name}")
                lines.append(f"  Count: {len(values)}")
                if values:
                    lines.append(f"  Latest: {values[-1].value}")
                lines.append("")
            lines.append("Adaptive Processing Stats:")
            adaptive_stats = self.adaptive_manager.get_processing_statistics()
            for key, value in adaptive_stats.items():
                lines.append(f"  {key}: {value}")
            return "\n".join(lines)


# Global metrics instance
metrics = ConsciousnessMetrics()</contents>
</xai:function_call=FileWrite>
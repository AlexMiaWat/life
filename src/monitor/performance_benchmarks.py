"""
Performance benchmarks and metrics for Semantic Monitor.

Provides comprehensive benchmarking tools to measure:
- Analysis latency and throughput
- Memory usage patterns
- Detection accuracy and precision
- Neural network performance
- Cache efficiency metrics
"""

import time
import statistics
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path
import psutil
import os

from src.monitor.semantic_monitor import SemanticMonitor, MonitorConfig
from src.observability.semantic_analysis_engine import SemanticAnalysisEngine


class SemanticMonitorBenchmark:
    """Comprehensive benchmarking suite for Semantic Monitor."""

    def __init__(self, monitor: SemanticMonitor = None):
        self.monitor = monitor or SemanticMonitor()
        self.results = {}
        self.test_data = self._generate_test_data()

    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate comprehensive test data for benchmarking."""
        return {
            'normal_chains': self._generate_normal_chains(100),
            'anomalous_chains': self._generate_anomalous_chains(50),
            'stress_test_chains': self._generate_stress_test_chains(1000),
            'edge_cases': self._generate_edge_cases()
        }

    def _generate_normal_chains(self, count: int) -> List[List[Dict]]:
        """Generate normal correlation chains for testing."""
        chains = []
        base_time = time.time()

        for i in range(count):
            chain = []
            current_time = base_time + i * 0.1

            # Event -> Meaning -> Decision -> Action -> Feedback pattern
            stages = [
                ('event', {'event_type': 'noise', 'intensity': 0.3}),
                ('meaning', {'data': {'impact': {'energy': -0.1, 'stability': 0.05}}}),
                ('decision', {'data': {'pattern': 'dampen'}}),
                ('action', {'data': {}}),
                ('feedback', {'data': {'state_delta': {'energy': -0.05}}})
            ]

            for stage_name, stage_data in stages:
                entry = {
                    'stage': stage_name,
                    'timestamp': current_time,
                    **stage_data
                }
                chain.append(entry)
                current_time += 0.01  # 10ms between stages

            chains.append(chain)

        return chains

    def _generate_anomalous_chains(self, count: int) -> List[List[Dict]]:
        """Generate anomalous correlation chains."""
        chains = []

        for i in range(count):
            # Create chains with various anomalies
            anomaly_types = [
                'missing_feedback',
                'inconsistent_timing',
                'abnormal_impact',
                'wrong_sequence',
                'extreme_values'
            ]

            anomaly_type = anomaly_types[i % len(anomaly_types)]
            chain = self._create_anomalous_chain(anomaly_type, i)
            chains.append(chain)

        return chains

    def _create_anomalous_chain(self, anomaly_type: str, index: int) -> List[Dict]:
        """Create a specific type of anomalous chain."""
        base_chain = self._generate_normal_chains(1)[0]

        if anomaly_type == 'missing_feedback':
            # Remove feedback stage
            return base_chain[:-1]
        elif anomaly_type == 'inconsistent_timing':
            # Mess up timing
            for i, entry in enumerate(base_chain):
                entry['timestamp'] += (i % 2) * 10.0  # Alternate large delays
            return base_chain
        elif anomaly_type == 'abnormal_impact':
            # Extreme impact values
            for entry in base_chain:
                if entry.get('stage') == 'meaning':
                    entry['data']['impact'] = {'energy': 5.0, 'stability': -3.0}
            return base_chain
        elif anomaly_type == 'wrong_sequence':
            # Wrong order of stages
            return base_chain[::-1]  # Reverse order
        elif anomaly_type == 'extreme_values':
            # Extreme intensity/event values
            for entry in base_chain:
                if entry.get('stage') == 'event':
                    entry['intensity'] = 2.0  # Impossible intensity
            return base_chain

        return base_chain

    def _generate_stress_test_chains(self, count: int) -> List[List[Dict]]:
        """Generate chains for stress testing."""
        chains = []

        for i in range(count):
            # Create very long chains
            chain = []
            base_time = time.time() + i * 0.001

            for j in range(20):  # 20 stages per chain
                stage_type = ['event', 'meaning', 'decision', 'action', 'feedback'][j % 5]
                entry = {
                    'stage': stage_type,
                    'timestamp': base_time + j * 0.005,
                    'data': {'complex_data': {'nested': {'value': j * 0.1}}}
                }
                chain.append(entry)

            chains.append(chain)

        return chains

    def _generate_edge_cases(self) -> Dict[str, List[Dict]]:
        """Generate edge cases for testing."""
        return {
            'empty_chain': [],
            'single_event': [{'stage': 'event', 'timestamp': time.time(), 'event_type': 'noise'}],
            'corrupted_data': [{'stage': 'event', 'timestamp': 'invalid', 'event_type': None}],
            'extreme_timestamps': [
                {'stage': 'event', 'timestamp': 0, 'event_type': 'noise'},
                {'stage': 'meaning', 'timestamp': 2147483647, 'data': {'impact': {'energy': 1.0}}}
            ],
            'circular_reference': [{'stage': 'event', 'timestamp': time.time(), 'self': None}]
        }

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite."""
        print("Running Semantic Monitor comprehensive benchmark...")

        results = {
            'latency_benchmark': self._benchmark_latency(),
            'throughput_benchmark': self._benchmark_throughput(),
            'memory_benchmark': self._benchmark_memory_usage(),
            'accuracy_benchmark': self._benchmark_detection_accuracy(),
            'cache_benchmark': self._benchmark_cache_efficiency(),
            'neural_benchmark': self._benchmark_neural_performance(),
            'stress_test': self._benchmark_stress_test(),
            'timestamp': time.time()
        }

        self.results = results
        return results

    def _benchmark_latency(self) -> Dict[str, Any]:
        """Benchmark analysis latency."""
        latencies = []

        # Test normal chains
        for chain in self.test_data['normal_chains'][:10]:
            start_time = time.time()
            correlation_id = f"latency_test_{len(latencies)}"
            self.monitor.analyze_correlation_chain(correlation_id, chain)
            latency = time.time() - start_time
            latencies.append(latency)

        return {
            'mean_latency': statistics.mean(latencies),
            'median_latency': statistics.median(latencies),
            'p95_latency': sorted(latencies)[int(len(latencies) * 0.95)],
            'p99_latency': sorted(latencies)[int(len(latencies) * 0.99)],
            'min_latency': min(latencies),
            'max_latency': max(latencies),
            'std_dev': statistics.stdev(latencies) if len(latencies) > 1 else 0.0
        }

    def _benchmark_throughput(self) -> Dict[str, Any]:
        """Benchmark analysis throughput."""
        test_duration = 10.0  # 10 seconds
        start_time = time.time()
        operations = 0

        while time.time() - start_time < test_duration:
            chain = self.test_data['normal_chains'][operations % len(self.test_data['normal_chains'])]
            correlation_id = f"throughput_test_{operations}"
            self.monitor.analyze_correlation_chain(correlation_id, chain)
            operations += 1

        actual_duration = time.time() - start_time

        return {
            'operations_per_second': operations / actual_duration,
            'total_operations': operations,
            'test_duration': actual_duration,
            'avg_latency': actual_duration / operations
        }

    def _benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns."""
        if not hasattr(psutil, 'Process'):
            return {'error': 'psutil not available for memory benchmarking'}

        process = psutil.Process(os.getpid())
        memory_samples = []

        # Baseline memory
        memory_samples.append(process.memory_info().rss / 1024 / 1024)  # MB

        # Memory during normal operations
        for i in range(50):
            chain = self.test_data['normal_chains'][i % len(self.test_data['normal_chains'])]
            correlation_id = f"memory_test_{i}"
            self.monitor.analyze_correlation_chain(correlation_id, chain)

            if i % 10 == 0:  # Sample every 10 operations
                memory_samples.append(process.memory_info().rss / 1024 / 1024)

        # Memory after cache operations
        self.monitor.clear_cache()
        memory_samples.append(process.memory_info().rss / 1024 / 1024)

        return {
            'baseline_memory_mb': memory_samples[0],
            'peak_memory_mb': max(memory_samples),
            'average_memory_mb': statistics.mean(memory_samples),
            'memory_std_dev_mb': statistics.stdev(memory_samples) if len(memory_samples) > 1 else 0.0,
            'final_memory_mb': memory_samples[-1],
            'memory_efficiency': memory_samples[-1] / memory_samples[0] if memory_samples[0] > 0 else 1.0
        }

    def _benchmark_detection_accuracy(self) -> Dict[str, Any]:
        """Benchmark anomaly detection accuracy."""
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        # Test normal chains (should not be anomalous)
        for chain in self.test_data['normal_chains'][:20]:
            correlation_id = f"accuracy_normal_{len([c for c in self.test_data['normal_chains'][:20] if c == chain])}"
            result = self.monitor.analyze_correlation_chain(correlation_id, chain)
            anomaly_score = result.get('anomaly_score', 0.0)

            if anomaly_score > self.monitor.config.anomaly_threshold:
                false_positives += 1
            else:
                true_negatives += 1

        # Test anomalous chains (should be anomalous)
        for chain in self.test_data['anomalous_chains'][:20]:
            correlation_id = f"accuracy_anomalous_{len([c for c in self.test_data['anomalous_chains'][:20] if c == chain])}"
            result = self.monitor.analyze_correlation_chain(correlation_id, chain)
            anomaly_score = result.get('anomaly_score', 0.0)

            if anomaly_score > self.monitor.config.anomaly_threshold:
                true_positives += 1
            else:
                false_negatives += 1

        # Calculate metrics
        total_predictions = true_positives + false_positives + true_negatives + false_negatives
        accuracy = (true_positives + true_negatives) / total_predictions if total_predictions > 0 else 0.0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'true_negatives': true_negatives,
            'false_negatives': false_negatives,
            'false_positive_rate': false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0.0
        }

    def _benchmark_cache_efficiency(self) -> Dict[str, Any]:
        """Benchmark cache performance."""
        # Fill cache
        for i in range(self.monitor.config.max_cached_analyses // 2):
            chain = self.test_data['normal_chains'][i % len(self.test_data['normal_chains'])]
            correlation_id = f"cache_test_{i}"
            self.monitor.analyze_correlation_chain(correlation_id, chain)

        # Test cache hits
        hits = 0
        misses = 0
        total_accesses = 50

        for i in range(total_accesses):
            # Alternate between cached and new analyses
            if i % 2 == 0:
                # Should hit cache
                correlation_id = f"cache_test_{i % (self.monitor.config.max_cached_analyses // 2)}"
                result = self.monitor.analyze_correlation_chain(correlation_id,
                    self.test_data['normal_chains'][i % len(self.test_data['normal_chains'])])
                if result.get('cached', False):
                    hits += 1
                else:
                    misses += 1
            else:
                # Should miss cache
                correlation_id = f"cache_miss_{i}"
                result = self.monitor.analyze_correlation_chain(correlation_id,
                    self.test_data['normal_chains'][i % len(self.test_data['normal_chains'])])
                if result.get('cached', False):
                    hits += 1
                else:
                    misses += 1

        hit_rate = hits / total_accesses if total_accesses > 0 else 0.0

        return {
            'cache_hit_rate': hit_rate,
            'cache_hits': hits,
            'cache_misses': misses,
            'cache_size': len(self.monitor.analysis_cache),
            'max_cache_size': self.monitor.config.max_cached_analyses,
            'cache_utilization': len(self.monitor.analysis_cache) / self.monitor.config.max_cached_analyses
        }

    def _benchmark_neural_performance(self) -> Dict[str, Any]:
        """Benchmark neural network performance."""
        if not self.monitor.analysis_engine.enable_neural_network:
            return {'neural_network': 'disabled'}

        neural_latencies = []
        neural_outputs = []

        for chain in self.test_data['normal_chains'][:20]:
            start_time = time.time()
            correlation_id = f"neural_test_{len(neural_latencies)}"
            result = self.monitor.analyze_correlation_chain(correlation_id, chain)
            neural_latency = time.time() - start_time

            neural_latencies.append(neural_latency)

            if 'neural_features' in result:
                neural_outputs.append(result['neural_features'])

        return {
            'neural_mean_latency': statistics.mean(neural_latencies) if neural_latencies else 0.0,
            'neural_network_calls': len(neural_latencies),
            'neural_output_variance': self._calculate_output_variance(neural_outputs),
            'neural_consistency': self._calculate_output_consistency(neural_outputs)
        }

    def _benchmark_stress_test(self) -> Dict[str, Any]:
        """Run stress test with high load."""
        stress_latencies = []
        start_time = time.time()

        # Process many chains quickly
        for i, chain in enumerate(self.test_data['stress_test_chains'][:100]):
            chain_start = time.time()
            correlation_id = f"stress_test_{i}"
            self.monitor.analyze_correlation_chain(correlation_id, chain)
            stress_latencies.append(time.time() - chain_start)

        total_time = time.time() - start_time

        return {
            'stress_test_duration': total_time,
            'chains_processed': len(stress_latencies),
            'throughput_stress': len(stress_latencies) / total_time,
            'avg_latency_stress': statistics.mean(stress_latencies),
            'p95_latency_stress': sorted(stress_latencies)[int(len(stress_latencies) * 0.95)],
            'memory_after_stress': self._get_current_memory_mb()
        }

    def _calculate_output_variance(self, outputs: List[List[float]]) -> float:
        """Calculate variance in neural network outputs."""
        if not outputs or not outputs[0]:
            return 0.0

        variances = []
        for i in range(len(outputs[0])):  # For each output dimension
            values = [output[i] for output in outputs if len(output) > i]
            if len(values) > 1:
                variances.append(statistics.variance(values))

        return statistics.mean(variances) if variances else 0.0

    def _calculate_output_consistency(self, outputs: List[List[float]]) -> float:
        """Calculate consistency of neural network outputs."""
        if not outputs or len(outputs) < 2:
            return 0.0

        consistencies = []
        for i in range(1, len(outputs)):
            prev_output = outputs[i-1]
            curr_output = outputs[i]
            if len(prev_output) == len(curr_output):
                # Cosine similarity between consecutive outputs
                dot_product = sum(a * b for a, b in zip(prev_output, curr_output))
                norm_a = math.sqrt(sum(a * a for a in prev_output))
                norm_b = math.sqrt(sum(b * b for b in curr_output))
                if norm_a > 0 and norm_b > 0:
                    consistency = dot_product / (norm_a * norm_b)
                    consistencies.append(consistency)

        return statistics.mean(consistencies) if consistencies else 0.0

    def _get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        if hasattr(psutil, 'Process'):
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        return 0.0

    def save_results(self, filepath: str = "benchmark_results.json"):
        """Save benchmark results to file."""
        results_path = Path(filepath)
        results_path.parent.mkdir(parents=True, exist_ok=True)

        with results_path.open('w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"Benchmark results saved to {filepath}")

    def print_summary(self):
        """Print benchmark summary."""
        if not self.results:
            print("No benchmark results available. Run run_comprehensive_benchmark() first.")
            return

        print("\n=== Semantic Monitor Benchmark Results ===\n")

        # Latency
        lat = self.results.get('latency_benchmark', {})
        print("Latency:")
        print(".4f")
        print(".4f")
        print(".4f")
        print()

        # Throughput
        tp = self.results.get('throughput_benchmark', {})
        print("Throughput:")
        print(".1f")
        print()

        # Memory
        mem = self.results.get('memory_benchmark', {})
        if 'baseline_memory_mb' in mem:
            print("Memory Usage:")
            print(".1f")
            print(".1f")
            print(".1f")
            print(".2f")
            print()

        # Accuracy
        acc = self.results.get('accuracy_benchmark', {})
        print("Detection Accuracy:")
        print(".3f")
        print(".3f")
        print(".3f")
        print(".3f")
        print(".3f")
        print()

        # Cache
        cache = self.results.get('cache_benchmark', {})
        print("Cache Efficiency:")
        print(".3f")
        print(".1f")
        print()


def run_semantic_monitor_benchmarks():
    """Run comprehensive benchmarks for Semantic Monitor."""
    print("Initializing Semantic Monitor benchmarks...")

    # Create monitor with performance monitoring enabled
    config = MonitorConfig(
        enable_performance_metrics=True,
        performance_log_file="logs/benchmark_performance.jsonl"
    )
    monitor = SemanticMonitor(config)

    # Run benchmarks
    benchmark = SemanticMonitorBenchmark(monitor)
    results = benchmark.run_comprehensive_benchmark()

    # Save and display results
    benchmark.save_results("docs/results/semantic_monitor_benchmarks.json")
    benchmark.print_summary()

    return results


if __name__ == "__main__":
    run_semantic_monitor_benchmarks()
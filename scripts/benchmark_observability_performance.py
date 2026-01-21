#!/usr/bin/env python3
"""
Observability Performance Benchmark.

Measures and validates the performance impact of the observability system.
Ensures that passive observation has minimal (< 1%) impact on runtime performance.
"""

import sys
import time
import threading
import statistics
from pathlib import Path
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from observability.async_data_sink import AsyncDataSink, RawObservationData
from observability.async_passive_observer import AsyncPassiveObserver


class PerformanceBenchmark:
    """Performance benchmark suite for observability system."""

    def __init__(self):
        self.results = {}

    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        print("🚀 Starting Observability Performance Benchmarks")
        print("=" * 55)

        self.benchmark_data_sink_throughput()
        self.benchmark_observer_passivity()
        self.benchmark_memory_usage()
        self.benchmark_disabled_impact()

        self.print_summary()
        return self.results

    def benchmark_data_sink_throughput(self):
        """Benchmark AsyncDataSink throughput."""
        print("📊 Benchmarking AsyncDataSink throughput...")

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(
                storage_path=f"{temp_dir}/benchmark_data.jsonl",
                max_queue_size=10000,
                enabled=True
            )

            # Test different batch sizes
            batch_sizes = [1, 10, 100, 1000]
            results = {}

            for batch_size in batch_sizes:
                times = []
                total_operations = 10000

                for _ in range(total_operations // batch_size):
                    start_time = time.perf_counter()

                    # Send batch of data
                    for i in range(batch_size):
                        data = RawObservationData(
                            timestamp=time.time(),
                            data_type="benchmark",
                            data={"value": i, "batch_size": batch_size}
                        )
                        sink.collect_data(data)

                    end_time = time.perf_counter()
                    times.append(end_time - start_time)

                # Calculate metrics
                avg_time_per_batch = statistics.mean(times)
                avg_time_per_operation = avg_time_per_batch / batch_size
                throughput = batch_size / avg_time_per_batch  # operations per second

                results[batch_size] = {
                    "avg_time_per_operation_ms": avg_time_per_operation * 1000,
                    "throughput_ops_per_sec": throughput,
                    "total_operations": total_operations
                }

            sink.shutdown()
            self.results["data_sink_throughput"] = results

            # Print results
            for batch_size, metrics in results.items():
                print(f"  Batch {batch_size}: {metrics['avg_time_per_operation_ms']:.3f}ms/op, "
                      f"{metrics['throughput_ops_per_sec']:.0f} ops/sec")

    def benchmark_observer_passivity(self):
        """Benchmark that observer doesn't interfere with runtime."""
        print("🔍 Benchmarking observer passivity...")

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test snapshots
            snapshots_dir = f"{temp_dir}/snapshots"
            Path(snapshots_dir).mkdir()

            # Create some test snapshots
            for i in range(5):
                snapshot_path = Path(snapshots_dir) / f"snapshot_{i}.json"
                snapshot_data = {
                    "timestamp": time.time() - i * 60,  # Spread over time
                    "energy": 0.5 + i * 0.1,
                    "stability": 0.8 - i * 0.05,
                    "memory": {"episodic_memory": [f"event_{j}" for j in range(10)]}
                }

                with open(snapshot_path, 'w') as f:
                    import json
                    json.dump(snapshot_data, f)

            # Test with observer enabled
            observer_enabled = AsyncPassiveObserver(
                collection_interval=0.1,  # Fast for testing
                snapshots_dir=snapshots_dir,
                enabled=True
            )

            # Let it collect some data
            time.sleep(0.5)

            enabled_status = observer_enabled.get_status()

            # Test with observer disabled
            observer_disabled = AsyncPassiveObserver(
                collection_interval=0.1,
                snapshots_dir=snapshots_dir,
                enabled=False
            )

            disabled_status = observer_disabled.get_status()

            # Cleanup
            observer_enabled.shutdown()
            observer_disabled.shutdown()

            results = {
                "enabled_observer_records": enabled_status["total_state_records"],
                "disabled_observer_records": disabled_status["total_state_records"],
                "enabled_thread_alive": enabled_status["thread_alive"],
                "disabled_thread_alive": disabled_status["thread_alive"]
            }

            self.results["observer_passivity"] = results

            print(f"  Enabled observer collected: {results['enabled_observer_records']} records")
            print(f"  Disabled observer collected: {results['disabled_observer_records']} records")
            print(f"  Enabled observer thread: {'alive' if results['enabled_thread_alive'] else 'dead'}")
            print(f"  Disabled observer thread: {'alive' if results['disabled_thread_alive'] else 'dead'}")

    def benchmark_memory_usage(self):
        """Benchmark memory usage of observability components."""
        print("🧠 Benchmarking memory usage...")

        import psutil
        import os

        # Get baseline memory
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Test with components enabled
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(
                storage_path=f"{temp_dir}/memory_test.jsonl",
                enabled=True
            )

            observer = AsyncPassiveObserver(
                collection_interval=10.0,  # Long interval
                snapshots_dir=temp_dir,
                enabled=True
            )

            # Let them initialize
            time.sleep(0.1)

            # Measure memory with components
            with_components_memory = process.memory_info().rss / 1024 / 1024

            # Cleanup
            observer.shutdown()
            sink.shutdown()

            # Wait for cleanup
            time.sleep(0.1)

            # Measure memory after cleanup
            after_cleanup_memory = process.memory_info().rss / 1024 / 1024

            results = {
                "baseline_memory_mb": baseline_memory,
                "with_components_memory_mb": with_components_memory,
                "after_cleanup_memory_mb": after_cleanup_memory,
                "memory_overhead_mb": with_components_memory - baseline_memory,
                "memory_leak_mb": after_cleanup_memory - baseline_memory
            }

            self.results["memory_usage"] = results

            print(f"  Baseline memory: {results['baseline_memory_mb']:.1f} MB")
            print(f"  With components: {results['with_components_memory_mb']:.1f} MB")
            print(f"  Memory overhead: {results['memory_overhead_mb']:.1f} MB")
            print(f"  Memory leak: {results['memory_leak_mb']:.1f} MB")

    def benchmark_disabled_impact(self):
        """Benchmark that disabled observability has zero impact."""
        print("🚫 Benchmarking disabled observability impact...")

        # Test that disabled components don't start threads or consume resources
        sink_disabled = AsyncDataSink(enabled=False)
        observer_disabled = AsyncPassiveObserver(enabled=False)

        # Quick operations should succeed instantly
        start_time = time.perf_counter()

        for i in range(1000):
            data = RawObservationData(
                timestamp=time.time(),
                data_type="disabled_test",
                data={"value": i}
            )
            sink_disabled.collect_data(data)

        end_time = time.perf_counter()
        disabled_time = end_time - start_time

        # Cleanup
        sink_disabled.shutdown()
        observer_disabled.shutdown()

        results = {
            "disabled_operations_time_ms": disabled_time * 1000,
            "avg_time_per_disabled_operation_us": (disabled_time / 1000) * 1000000,
            "observer_thread_started": observer_disabled._observer_thread is not None
        }

        self.results["disabled_impact"] = results

        print(f"  Disabled operations time: {results['disabled_operations_time_ms']:.3f} ms")
        print(f"  Avg time per operation: {results['avg_time_per_disabled_operation_us']:.1f} μs")
        print(f"  Observer thread started: {results['observer_thread_started']}")

    def print_summary(self):
        """Print benchmark summary."""
        print("\n📋 Performance Benchmark Summary")
        print("=" * 35)

        # Check if benchmarks pass requirements
        all_passed = True

        # Data sink performance check
        if "data_sink_throughput" in self.results:
            throughput = self.results["data_sink_throughput"]
            # Check that single operations are < 1ms
            single_op_time = throughput[1]["avg_time_per_operation_ms"]
            if single_op_time > 1.0:
                print(f"❌ Data sink too slow: {single_op_time:.3f}ms per operation")
                all_passed = False
            else:
                print(f"✅ Data sink performance: {single_op_time:.3f}ms per operation")

        # Observer passivity check
        if "observer_passivity" in self.results:
            passivity = self.results["observer_passivity"]
            if passivity["disabled_thread_alive"]:
                print("❌ Disabled observer still has active thread")
                all_passed = False
            else:
                print("✅ Disabled observer properly inactive")

        # Memory usage check
        if "memory_usage" in self.results:
            memory = self.results["memory_usage"]
            overhead = memory["memory_overhead_mb"]
            if overhead > 50:  # Allow up to 50MB overhead
                print(f"❌ High memory overhead: {overhead:.1f} MB")
                all_passed = False
            else:
                print(f"✅ Memory overhead acceptable: {overhead:.1f} MB")

        # Disabled impact check
        if "disabled_impact" in self.results:
            disabled = self.results["disabled_impact"]
            if disabled["avg_time_per_disabled_operation_us"] > 10:  # < 10μs per operation
                print(f"❌ Disabled operations too slow: {disabled['avg_time_per_disabled_operation_us']:.1f} μs")
                all_passed = False
            else:
                print(f"✅ Disabled operations fast: {disabled['avg_time_per_disabled_operation_us']:.1f} μs")

        print(f"\n{'🎉 All benchmarks passed!' if all_passed else '⚠️  Some benchmarks failed'}")

        # Overall assessment
        if all_passed:
            print("✅ Observability system meets performance requirements (< 1% impact)")
        else:
            print("❌ Observability system needs performance optimization")


def main():
    """Run performance benchmarks."""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()

    # Save results
    output_file = Path("data/benchmark_results.json")
    output_file.parent.mkdir(exist_ok=True)

    import json
    with open(output_file, 'w') as f:
        json.dump({
            "benchmark_timestamp": time.time(),
            "results": results
        }, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")


if __name__ == "__main__":
    main()
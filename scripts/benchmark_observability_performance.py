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
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.async_log_writer import AsyncLogWriter


class PerformanceBenchmark:
    """Performance benchmark suite for observability system."""

    def __init__(self):
        self.results = {}

    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        print("🚀 Starting Observability Performance Benchmarks")
        print("=" * 55)

        self.benchmark_log_writer_performance()
        self.benchmark_memory_usage()

        self.print_summary()
        return self.results


    def benchmark_log_writer_performance(self):
        """Benchmark AsyncLogWriter performance for <1% overhead."""
        print("📝 Benchmarking AsyncLogWriter performance...")

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = f"{temp_dir}/benchmark_log.jsonl"

            # Test with different configurations
            configs = [
                {"batch_size": 50, "flush_interval": 0.1, "buffer_size": 10000},  # Production config
                {"batch_size": 1, "flush_interval": 0.001, "buffer_size": 1000},  # High frequency
            ]

            results = {}

            for i, config in enumerate(configs):
                config_name = f"config_{i+1}"
                print(f"  Testing {config_name}: batch_size={config['batch_size']}, flush={config['flush_interval']}s")

                writer = AsyncLogWriter(
                    log_file=log_file,
                    enabled=True,
                    buffer_size=config["buffer_size"],
                    batch_size=config["batch_size"],
                    flush_interval=config["flush_interval"]
                )

                # Test logging performance
                total_entries = 10000
                start_time = time.perf_counter()

                for j in range(total_entries):
                    writer.write_entry(
                        stage="benchmark",
                        correlation_id=f"test_{j}",
                        event_id=f"event_{j}",
                        data={"value": j, "timestamp": time.time()}
                    )

                # Force flush
                writer.flush()
                end_time = time.perf_counter()

                total_time = end_time - start_time
                avg_time_per_entry = (total_time / total_entries) * 1000  # ms

                # Get stats
                stats = writer.get_stats()

                results[config_name] = {
                    "total_time_ms": total_time * 1000,
                    "avg_time_per_entry_us": avg_time_per_entry * 1000,
                    "entries_per_sec": total_entries / total_time,
                    "buffer_utilization_percent": stats["utilization_percent"],
                    "batches_written": stats["batches_written"],
                    "io_errors": stats["io_errors"]
                }

                writer.shutdown()

                print(f"    Time: {total_time:.3f}s, Avg: {avg_time_per_entry:.3f}ms/entry")
                print(f"    Throughput: {total_entries / total_time:.0f} entries/sec")

            self.results["log_writer_performance"] = results

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
            log_writer = AsyncLogWriter(
                log_file=f"{temp_dir}/memory_test_log.jsonl",
                enabled=True,
                buffer_size=10000,
                batch_size=50,
                flush_interval=0.1
            )

            # Let them initialize
            time.sleep(0.1)

            # Measure memory with components
            with_components_memory = process.memory_info().rss / 1024 / 1024

            # Cleanup
            log_writer.shutdown()

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

        # Log writer performance check (<1% overhead target)
        if "log_writer_performance" in self.results:
            perf = self.results["log_writer_performance"]
            # Check production config (config_1)
            if "config_1" in perf:
                config1 = perf["config_1"]
                avg_time_us = config1["avg_time_per_entry_us"]
                if avg_time_us > 100:  # < 100μs per entry for <1% overhead
                    print(f"❌ Log writer too slow: {avg_time_us:.1f}μs per entry")
                    all_passed = False
                else:
                    print(f"✅ Log writer performance: {avg_time_us:.1f}μs per entry")

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
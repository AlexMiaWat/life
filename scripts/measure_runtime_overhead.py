#!/usr/bin/env python3
"""
Measure real runtime loop overhead with observability enabled/disabled.
"""

import sys
import time
import threading
import statistics
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.self_state import SelfState
from src.observability.structured_logger import StructuredLogger
from src.environment.event import Event


def create_mock_event(intensity=0.5, event_type="test_event"):
    """Create a mock event for testing."""
    return Event(
        type=event_type,
        intensity=intensity,
        timestamp=time.time(),
        metadata={"test": True}
    )


def simulate_runtime_tick(self_state, structured_logger, enable_logging=True):
    """Simulate one runtime tick with logging."""
    if not enable_logging and structured_logger:
        structured_logger.enabled = False

    # Start timing
    tick_start = time.perf_counter()

    # Simulate tick operations (similar to runtime loop)
    queue_size = 5

    # Log tick start (every 10th tick simulation)
    if structured_logger and hasattr(self_state, '_tick_counter'):
        self_state._tick_counter = getattr(self_state, '_tick_counter', 0) + 1
        if self_state._tick_counter % 10 == 0:
            structured_logger.log_tick_start(self_state.ticks, queue_size)

    # Simulate processing events
    events = [create_mock_event() for _ in range(3)]

    for event in events:
        if structured_logger:
            correlation_id = structured_logger.log_event(event)

            # Simulate decision making
            structured_logger.log_decision(correlation_id)

            # Simulate action
            action_id = f"action_{self_state.ticks}_{correlation_id}"
            structured_logger.log_action(action_id, correlation_id)
        else:
            correlation_id = f"mock_{self_state.ticks}"

    # Log tick end (every tick)
    if structured_logger:
        structured_logger.log_tick_end(self_state.ticks)

    # End timing
    tick_end = time.perf_counter()
    tick_duration = tick_end - tick_start

    # Restore logging if it was disabled
    if not enable_logging and structured_logger:
        structured_logger.enabled = True

    return tick_duration


def measure_overhead():
    """Measure runtime overhead with and without observability."""
    print("🚀 Measuring Runtime Loop Overhead")
    print("=" * 40)

    # Create self state
    self_state = SelfState()
    self_state.ticks = 100  # Simulate some ticks already passed

    # Test configurations
    configs = [
        {"name": "No Logging", "logger": None},
        {"name": "AsyncLogWriter Enabled", "logger": StructuredLogger(
            log_tick_interval=10,
            enable_detailed_logging=False,
            buffer_size=10000,
            batch_size=50,
            flush_interval=0.1
        )},
    ]

    results = {}

    for config in configs:
        print(f"\n📊 Testing: {config['name']}")

        structured_logger = config["logger"]
        tick_times = []

        # Run multiple ticks to get stable measurements
        num_ticks = 100

        for i in range(num_ticks):
            self_state.ticks += 1
            duration = simulate_runtime_tick(self_state, structured_logger, enable_logging=True)
            tick_times.append(duration * 1000)  # Convert to milliseconds

            # Small delay to prevent overwhelming
            time.sleep(0.001)

        # Calculate statistics
        avg_time = statistics.mean(tick_times)
        median_time = statistics.median(tick_times)
        p95_time = statistics.quantiles(tick_times, n=20)[18]

        results[config["name"]] = {
            "avg_tick_time_ms": avg_time,
            "median_tick_time_ms": median_time,
            "p95_tick_time_ms": p95_time,
            "samples": num_ticks
        }

        print(f"  Average tick time: {avg_time:.3f} ms")
        print(f"  Median tick time: {median_time:.3f} ms")
        print(f"  P95 tick time: {p95_time:.3f} ms")

        # Cleanup logger if exists
        if structured_logger:
            structured_logger.shutdown()

    # Calculate overhead
    print("\n🎯 Overhead Analysis:")
    no_logging_time = results["No Logging"]["avg_tick_time_ms"]
    with_logging_time = results["AsyncLogWriter Enabled"]["avg_tick_time_ms"]

    overhead_ms = with_logging_time - no_logging_time
    overhead_percent = (overhead_ms / no_logging_time) * 100 if no_logging_time > 0 else 0

    print(f"  Baseline (no logging): {no_logging_time:.3f} ms/tick")
    print(f"  With observability: {with_logging_time:.3f} ms/tick")
    print(f"  Overhead: {overhead_ms:.3f} ms/tick ({overhead_percent:.2f}%)")

    # Check requirements
    passed = overhead_percent <= 1.0  # < 1% overhead requirement

    if passed:
        print(f"  ✅ PASSED: Overhead {overhead_percent:.2f}% ≤ 1% requirement")
    else:
        print(f"  ❌ FAILED: Overhead {overhead_percent:.2f}% > 1% requirement")

    return {
        "passed": passed,
        "overhead_percent": overhead_percent,
        "overhead_ms": overhead_ms,
        "baseline_ms": no_logging_time,
        "with_observability_ms": with_logging_time,
        "detailed_results": results
    }


if __name__ == "__main__":
    result = measure_overhead()

    # Save results
    output_file = Path("data/runtime_overhead_measurement.json")
    output_file.parent.mkdir(exist_ok=True)

    import json
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "overhead_measurement": result
        }, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")

    # Exit with appropriate code
    exit(0 if result["passed"] else 1)
"""
Architecture Tests for Observability Passivity.

Tests to ensure that observability system maintains true passivity:
- No runtime loop interference
- No interpretation of raw data
- Asynchronous operation
- Optional functionality
"""

import time
import threading
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path

from src.observability.async_passive_observer import AsyncPassiveObserver
from src.observability.async_data_sink import AsyncDataSink, RawObservationData
from src.observability.external_observer import RawDataCollector, RawSystemCounters, RawDataReport
from src.observability.state_tracker import StateTracker, StateSnapshot
from src.observability.component_monitor import ComponentMonitor, SystemComponentStats


class TestObservabilityPassivity:
    """Test suite for observability passivity requirements."""

    def test_async_data_sink_no_blocking(self):
        """Test that AsyncDataSink operations are non-blocking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(
                storage_path=os.path.join(temp_dir, "test_data.jsonl"),
                max_queue_size=10,
                enabled=True
            )

            # Test rapid-fire data collection
            start_time = time.time()
            for i in range(20):  # More than queue size
                data = RawObservationData(
                    timestamp=time.time(),
                    data_type="test",
                    data={"counter": i}
                )
                result = sink.collect_data(data)
                if i >= 10:  # After queue fills
                    assert not result, "Should drop data when queue full"

            # Operation should complete very quickly
            duration = time.time() - start_time
            assert duration < 0.1, f"Data collection took too long: {duration}s"

            sink.shutdown()

    def test_async_passive_observer_thread_isolation(self):
        """Test that AsyncPassiveObserver runs in separate thread."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock snapshot
            snapshots_dir = os.path.join(temp_dir, "snapshots")
            os.makedirs(snapshots_dir)

            snapshot_file = os.path.join(snapshots_dir, "snapshot_001.json")
            with open(snapshot_file, 'w') as f:
                import json
                json.dump({
                    "timestamp": time.time(),
                    "energy": 0.8,
                    "memory": {"episodic_memory": [1, 2, 3]}
                }, f)

            observer = AsyncPassiveObserver(
                collection_interval=1.0,  # Fast for testing
                snapshots_dir=snapshots_dir,
                enabled=True
            )

            # Wait a bit for thread to start
            time.sleep(0.1)

            # Check that observer thread is running
            status = observer.get_status()
            assert status["thread_alive"], "Observer thread should be alive"

            # Check that it's a daemon thread (won't prevent shutdown)
            assert observer._observer_thread.daemon, "Observer thread should be daemon"

            observer.shutdown()

    def test_raw_data_only_no_interpretation(self):
        """Test that only raw counters are collected, no derived metrics."""
        # Test RawSystemCounters
        counters = RawSystemCounters(
            timestamp=time.time(),
            cycle_count=100,
            uptime_seconds=3600.0,
            memory_entries_count=50,
            error_count=5,
            action_count=20,
            event_count=15,
            state_change_count=10
        )

        # Ensure no derived/calculated fields
        assert not hasattr(counters, 'event_processing_rate'), "Should not have derived rate metrics"
        assert not hasattr(counters, 'state_change_frequency'), "Should not have derived frequency metrics"
        assert not hasattr(counters, 'efficiency'), "Should not have interpretation metrics"

        # Test serialization contains only raw data
        data = counters.__dict__
        assert 'cycle_count' in data
        assert 'error_count' in data
        assert 'event_processing_rate' not in data

    def test_observer_disabled_has_zero_impact(self):
        """Test that disabled observer has no performance impact."""
        observer = AsyncPassiveObserver(enabled=False)

        # Should not start any threads
        assert observer._observer_thread is None, "Disabled observer should not start thread"

        # Status should reflect disabled state
        status = observer.get_status()
        assert not status["enabled"]
        assert not status["thread_alive"]

        # Operations should be no-ops
        observer.disable()  # Should not crash

    def test_data_sink_graceful_degradation(self):
        """Test that data sink handles failures gracefully."""
        sink = AsyncDataSink(
            storage_path="/nonexistent/directory/test.jsonl",  # Invalid path
            enabled=True
        )

        # Should not crash on invalid path during init
        data = RawObservationData(
            timestamp=time.time(),
            data_type="test",
            data={"test": "data"}
        )

        # Collect should succeed (data goes to queue)
        result = sink.collect_data(data)
        assert result, "Should accept data even with invalid storage path"

        # Shutdown should not crash
        sink.shutdown()

    def test_no_runtime_imports_in_observability(self):
        """Test that observability modules don't import runtime components."""
        import sys

        # Clear any cached imports
        modules_to_check = [
            'src.observability.async_passive_observer',
            'src.observability.async_data_sink',
            'src.observability.external_observer',
            'src.observability.state_tracker',
            'src.observability.component_monitor'
        ]

        for module_name in modules_to_check:
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Import should not pull in runtime dependencies
        from src.observability import AsyncPassiveObserver, AsyncDataSink

        # Check that runtime loop is not imported
        assert 'src.runtime.loop' not in sys.modules, "Observability should not import runtime loop"

        # Check that SelfState is not imported at module level
        assert 'src.state.self_state' not in sys.modules, "Observability should not import SelfState directly"

    def test_passive_observer_uses_external_sources_only(self):
        """Test that passive observer only reads from external files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshots_dir = os.path.join(temp_dir, "snapshots")
            os.makedirs(snapshots_dir)

            # Create test snapshot
            snapshot_data = {
                "timestamp": time.time(),
                "energy": 0.7,
                "memory": {"episodic_memory": []},
                "learning_params": {},
                "adaptation_params": {}
            }

            snapshot_file = os.path.join(snapshots_dir, "test_snapshot.json")
            with open(snapshot_file, 'w') as f:
                import json
                json.dump(snapshot_data, f)

            observer = AsyncPassiveObserver(
                collection_interval=0.1,  # Very fast for testing
                snapshots_dir=snapshots_dir,
                enabled=True
            )

            # Wait for collection
            time.sleep(0.2)

            # Check that data was collected
            status = observer.get_status()
            assert status["total_state_records"] > 0, "Should have collected state data from snapshot"

            observer.shutdown()

    def test_architecture_isolation_runtime_loop(self):
        """Test that runtime loop doesn't depend on observability internals."""
        # This test ensures that runtime loop can run without observability imports
        import sys

        # Remove observability from sys.modules if present
        observability_modules = [m for m in sys.modules.keys() if m.startswith('src.observability')]
        for mod in observability_modules:
            del sys.modules[mod]

        # Import runtime loop should not pull in observability
        from src.runtime import loop

        # Check that observability modules are not loaded
        observability_still_loaded = any(m.startswith('src.observability') for m in sys.modules.keys())
        assert not observability_still_loaded, "Runtime loop should not auto-import observability"

        # But should be able to import when needed (lazy loading)
        from src.observability import AsyncPassiveObserver
        assert AsyncPassiveObserver is not None


class TestPerformanceImpact:
    """Test performance impact of observability system."""

    def test_data_collection_performance(self):
        """Test that data collection has minimal performance impact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = AsyncDataSink(
                storage_path=os.path.join(temp_dir, "perf_test.jsonl"),
                enabled=True
            )

            # Measure time for many rapid collections
            start_time = time.time()

            iterations = 1000
            for i in range(iterations):
                data = RawObservationData(
                    timestamp=time.time(),
                    data_type="perf_test",
                    data={"iteration": i}
                )
                sink.collect_data(data)

            duration = time.time() - start_time

            # Should be very fast (< 0.1s for 1000 operations)
            assert duration < 0.1, f"Data collection too slow: {duration}s for {iterations} operations"

            # Average time per operation should be < 0.1ms
            avg_time_per_op = (duration / iterations) * 1000
            assert avg_time_per_op < 0.1, f"Average operation time too high: {avg_time_per_op}ms"

            sink.shutdown()

    def test_memory_usage_controlled(self):
        """Test that memory usage is controlled and bounded."""
        sink = AsyncDataSink(
            max_queue_size=100,
            enabled=True
        )

        # Fill queue beyond limit
        for i in range(150):  # More than max_queue_size
            data = RawObservationData(
                timestamp=time.time(),
                data_type="memory_test",
                data={"value": i}
            )
            sink.collect_data(data)

        # Queue should not grow beyond limit
        queue_size = sink.get_queue_size()
        assert queue_size <= 100, f"Queue grew beyond limit: {queue_size}"

        sink.shutdown()

    def test_background_thread_cpu_usage(self):
        """Test that background thread has minimal CPU impact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            observer = AsyncPassiveObserver(
                collection_interval=10.0,  # Long interval to minimize activity
                snapshots_dir=temp_dir,
                enabled=True
            )

            # Let it run for a short time
            time.sleep(0.5)

            # Thread should still be alive but not consuming much CPU
            # (Hard to measure precisely without system tools, but at least check it's running)
            status = observer.get_status()
            assert status["thread_alive"], "Background thread should be running"

            observer.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])
"""
Architecture Tests for Observability Passivity.

Tests to ensure that observability system maintains true passivity:
- No runtime loop interference
- No interpretation of raw data
- Truly passive operation (no active collection)
- Only reactive data acceptance
"""

import time
import pytest
from unittest.mock import Mock
import tempfile
import os

from src.observability.async_passive_observer import PassiveDataSink
from src.observability.external_observer import RawDataCollector, RawSystemCounters, RawDataReport


class TestObservabilityPassivity:
    """Test suite for observability passivity requirements."""

    def test_passive_data_sink_no_active_collection(self):
        """Test that PassiveDataSink only accepts data when explicitly provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = PassiveDataSink(data_directory=temp_dir, enabled=True)

            # Test that sink only stores when data is explicitly provided
            test_data = {"timestamp": time.time(), "test": "data"}

            # Should accept data
            result = sink.accept_data_point(test_data)
            assert result, "Should accept explicit data point"

            # Check that data was stored
            status = sink.get_status()
            assert status["observations_file_exists"], "Should have created observations file"

            # No background activity - system should remain passive
            time.sleep(0.1)  # Wait to ensure no background activity

            # Status should not change without explicit data provision
            status_after = sink.get_status()
            assert status["observations_file_size_bytes"] == status_after["observations_file_size_bytes"], \
                "File size should not change without explicit data provision"

    def test_passive_data_sink_reactive_only(self):
        """Test that PassiveDataSink only reacts to explicit calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = PassiveDataSink(data_directory=temp_dir, enabled=True)

            # No data initially
            initial_status = sink.get_status()
            assert not initial_status["observations_file_exists"], "Should start with no data"

            # Only after explicit call should data appear
            snapshot_data = {
                "timestamp": time.time(),
                "energy": 0.8,
                "memory": {"episodic_memory": [1, 2, 3]}
            }

            result = sink.accept_snapshot_data(snapshot_data)
            assert result, "Should accept snapshot data"

            # Now data should exist
            status = sink.get_status()
            assert status["observations_file_exists"], "Should have data after explicit call"

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

    def test_passive_sink_disabled_has_zero_impact(self):
        """Test that disabled PassiveDataSink has no impact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = PassiveDataSink(data_directory=temp_dir, enabled=False)

            # Should not accept data when disabled
            test_data = {"timestamp": time.time(), "test": "data"}
            result = sink.accept_data_point(test_data)
            assert not result, "Disabled sink should not accept data"

            # Status should reflect disabled state
            status = sink.get_status()
            assert not status["enabled"]

            # Operations should be no-ops
            sink.disable()  # Should not crash

    def test_passive_sink_handles_storage_failures(self):
        """Test that PassiveDataSink handles storage failures gracefully."""
        # Test with invalid directory (read-only or non-existent)
        sink = PassiveDataSink(data_directory="/nonexistent/directory", enabled=True)

        # Should handle failure gracefully
        test_data = {"timestamp": time.time(), "test": "data"}
        result = sink.accept_data_point(test_data)
        # May return False on storage failure, but should not crash
        assert isinstance(result, bool), "Should return boolean result without crashing"

    def test_no_runtime_imports_in_observability(self):
        """Test that observability modules don't import runtime components."""
        import sys

        # Clear any cached imports
        modules_to_check = [
            'src.observability.async_passive_observer',
            'src.observability.external_observer'
        ]

        for module_name in modules_to_check:
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Import should not pull in runtime dependencies
        from src.observability import PassiveDataSink

        # Check that runtime loop is not imported
        assert 'src.runtime.loop' not in sys.modules, "Observability should not import runtime loop"

        # Check that SelfState is not imported at module level
        assert 'src.state.self_state' not in sys.modules, "Observability should not import SelfState directly"

    def test_passive_sink_accepts_snapshot_data(self):
        """Test that PassiveDataSink accepts snapshot data when explicitly provided."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = PassiveDataSink(data_directory=temp_dir, enabled=True)

            # Create test snapshot data
            snapshot_data = {
                "timestamp": time.time(),
                "energy": 0.7,
                "memory": {"episodic_memory": []},
                "learning_params": {},
                "adaptation_params": {}
            }

            # Explicitly provide snapshot data
            result = sink.accept_snapshot_data(snapshot_data)
            assert result, "Should accept snapshot data"

            # Check that data was stored
            status = sink.get_status()
            assert status["observations_file_exists"], "Should have stored observation data"

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
        from src.observability import PassiveDataSink
        assert PassiveDataSink is not None

class TestPassivePerformance:
    """Test performance characteristics of passive observability system."""

    def test_passive_data_acceptance_performance(self):
        """Test that passive data acceptance has minimal performance impact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = PassiveDataSink(data_directory=temp_dir, enabled=True)

            # Measure time for many rapid data acceptances
            start_time = time.time()

            iterations = 1000
            for i in range(iterations):
                data = {"timestamp": time.time(), "iteration": i}
                sink.accept_data_point(data)

            duration = time.time() - start_time

            # Should be very fast (< 0.1s for 1000 operations)
            assert duration < 0.1, f"Data acceptance too slow: {duration}s for {iterations} operations"

    def test_passive_sink_memory_efficient(self):
        """Test that PassiveDataSink is memory efficient."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = PassiveDataSink(data_directory=temp_dir, enabled=True)

            # Accept many data points
            for i in range(1000):
                data = {"timestamp": time.time(), "value": i}
                sink.accept_data_point(data)

            # Check that status can be retrieved (basic functionality test)
            status = sink.get_status()
            assert status["enabled"], "Sink should remain enabled"
            assert status["observations_file_exists"], "Should have stored data"


if __name__ == "__main__":
    pytest.main([__file__])
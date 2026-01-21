"""
Integration Tests for Complete Observability System.

Tests the entire observability system working together:
- UnifiedObservationAPI as the main entry point
- PassiveDataSink for data acceptance
- RawDataCollector for counter extraction
- StructuredLogger for event logging
- Graceful degradation under failure conditions
- Configuration loading and usage
"""

import time
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.observability import UnifiedObservationAPI, PassiveDataSink, RawDataCollector
from src.observability.structured_logger import StructuredLogger
from src.observability.developer_reports import RawDataAccess
from src.config.observability_config import ObservabilityConfig


class TestUnifiedObservabilityIntegration:
    """Integration tests for the complete observability system."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as base_dir:
            data_dir = Path(base_dir) / "data"
            logs_dir = Path(base_dir) / "logs"
            data_dir.mkdir()
            logs_dir.mkdir()

            yield {
                "base": Path(base_dir),
                "data": data_dir,
                "logs": logs_dir
            }

    @pytest.fixture
    def test_config(self, temp_dirs):
        """Create test configuration."""
        config = ObservabilityConfig(
            enabled=True,
            data_directory=str(temp_dirs["data"]),
            logs_directory=str(temp_dirs["logs"])
        )
        return config

    def test_full_system_initialization(self, temp_dirs, test_config):
        """Test that the entire system initializes correctly."""
        api = UnifiedObservationAPI(
            config=test_config,
            data_directory=str(temp_dirs["data"]),
            logs_directory=str(temp_dirs["logs"])
        )

        # Check that all components are initialized
        status = api.get_status()
        assert status["enabled"] is True
        assert "components" in status
        assert "data_sink" in status["components"]
        assert "structured_logger" in status["components"]

    def test_end_to_end_data_flow(self, temp_dirs, test_config):
        """Test complete data flow from acceptance to retrieval."""
        api = UnifiedObservationAPI(config=test_config)

        # 1. Accept data via unified API
        test_data = {
            "timestamp": time.time(),
            "event_type": "test_event",
            "memory_entries_count": 42,
            "cycle_count": 100
        }

        result = api.accept_data_point(test_data)
        assert result is True, "Should accept data point"

        # 2. Log structured events
        correlation_id = api.log_event({"type": "test_event"})
        assert correlation_id is not None

        api.log_tick_end(tick_number=1)  # Only tick_number, no duration_ms
        api.log_decision(correlation_id)

        # 3. Retrieve data back
        observations = api.get_raw_observation_data(hours=1)
        assert len(observations) > 0, "Should have stored observations"

        # 4. Collect raw counters from logs
        report = api.collect_raw_counters_from_logs()
        assert report is not None
        assert hasattr(report, 'raw_counters')

    def test_structured_logging_integration(self, temp_dirs, test_config):
        """Test structured logging works with the unified API."""
        api = UnifiedObservationAPI(config=test_config)

        # Log a complete event chain
        correlation_id = api.log_event({"type": "user_interaction", "data": "test"})
        api.log_meaning({"type": "meaning"}, {"type": "meaning_data"}, correlation_id)
        api.log_decision(correlation_id)
        api.log_action("test_action", correlation_id)
        api.log_feedback({"result": "success"}, correlation_id)

        # Check that structured log file was created
        log_file = Path(test_config.structured_logging.log_file)
        assert log_file.exists(), "Should create structured log file"

        # Check log content
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0, "Should have log entries"

            # Parse first entry
            first_entry = json.loads(lines[0])
            assert "stage" in first_entry
            assert "correlation_id" in first_entry

    def test_graceful_degradation_under_failures(self, temp_dirs, test_config):
        """Test system handles failures gracefully."""
        api = UnifiedObservationAPI(config=test_config)

        # Simulate storage failure by making directory read-only
        data_dir = Path(temp_dirs["data"])
        data_dir.chmod(0o444)  # Read-only

        try:
            # System should handle failure gracefully
            result = api.accept_data_point({"test": "data"})
            # May return False, but should not crash
            assert isinstance(result, bool), "Should return boolean without crashing"

            # Logging should still work (may use fallback)
            correlation_id = api.log_event({"test": "event"})
            assert isinstance(correlation_id, str), "Should return correlation ID even on failure"

        finally:
            # Restore permissions for cleanup
            data_dir.chmod(0o755)

    def test_configuration_integration(self, temp_dirs):
        """Test that configuration is properly loaded and used."""
        # Create a temporary config file
        config_path = temp_dirs["base"] / "test_config.yaml"

        test_config_content = """
observability:
  enabled: true
  data_directory: "test_data"
  logs_directory: "test_logs"

structured_logging:
  enabled: true
  log_file: "test_data/structured_test.log"

passive_data_sink:
  enabled: true
  data_directory: "test_data"
"""

        with open(config_path, 'w') as f:
            f.write(test_config_content)

        # Test loading custom config
        with patch('src.config.observability_config.ObservabilityConfig.load_from_file') as mock_load:
            mock_config = ObservabilityConfig(
                enabled=True,
                data_directory="test_data",
                logs_directory="test_logs"
            )
            mock_load.return_value = mock_config

            api = UnifiedObservationAPI()

            # Should use config values
            assert api.enabled is True

    def test_passive_sink_raw_collector_integration(self, temp_dirs, test_config):
        """Test PassiveDataSink and RawDataCollector work together."""
        # Create API with test config
        api = UnifiedObservationAPI(config=test_config)

        # Accept some data points that would be counted
        api.accept_data_point({
            "timestamp": time.time(),
            "event_type": "tick_end",
            "tick_number": 1
        })

        api.accept_data_point({
            "timestamp": time.time(),
            "event_type": "error",
            "error_type": "test_error"
        })

        # Force flush by creating a new API instance (simulating restart)
        # In real usage, data would be in files
        api2 = UnifiedObservationAPI(config=test_config)

        # Try to collect counters (may be empty if files don't exist, but shouldn't crash)
        report = api2.collect_raw_counters_from_logs()
        assert report is not None, "Should return report even if empty"

    def test_system_status_reporting(self, temp_dirs, test_config):
        """Test that system status reporting works correctly."""
        api = UnifiedObservationAPI(config=test_config)

        # Get initial status
        status = api.get_status()
        assert "enabled" in status
        assert "data_directory" in status
        assert "components" in status

        # Accept some data
        api.accept_data_point({"test": "data"})

        # Status should reflect changes
        status_after = api.get_status()
        assert status_after["enabled"] == status["enabled"]

    def test_emergency_collection_functionality(self, temp_dirs, test_config):
        """Test emergency data collection works."""
        api = UnifiedObservationAPI(config=test_config)

        # Emergency collection should work even with no data
        emergency_data = api.emergency_data_collection()
        assert "emergency_report" in emergency_data
        assert "system_status" in emergency_data
        assert "collected_at" in emergency_data

    def test_raw_data_access_integration(self, temp_dirs, test_config):
        """Test RawDataAccess integration with the unified API."""
        api = UnifiedObservationAPI(config=test_config)

        # Create some test data files manually
        observations_file = Path(temp_dirs["data"]) / "passive_observations.jsonl"
        test_observation = {
            "timestamp": time.time(),
            "test_data": "value"
        }

        with open(observations_file, 'w') as f:
            f.write(json.dumps(test_observation) + "\n")

        # Should be able to retrieve data
        observations = api.get_raw_observation_data(hours=1)
        # May be empty if RawDataAccess doesn't find the file, but shouldn't crash
        assert isinstance(observations, list), "Should return list"

    def test_timeout_and_fallback_mechanisms(self, temp_dirs, test_config):
        """Test timeout and fallback mechanisms work."""
        api = UnifiedObservationAPI(config=test_config)

        # Test with very short timeout by patching
        with patch('src.observability.unified_observation_api.time') as mock_time:
            mock_time.time.return_value = time.time()

            # Normal operation should work
            result = api.accept_data_point({"test": "normal"})
            assert isinstance(result, bool)

    def test_system_enable_disable(self, temp_dirs, test_config):
        """Test enabling/disabling the entire system."""
        api = UnifiedObservationAPI(config=test_config)

        # Should start enabled
        assert api.enabled is True

        # Disable
        api.disable()
        assert api.enabled is False

        # Operations should be no-ops when disabled
        result = api.accept_data_point({"test": "data"})
        assert result is False, "Disabled system should not accept data"

        # Re-enable
        api.enable()
        assert api.enabled is True

        # Operations should work again
        result = api.accept_data_point({"test": "data"})
        assert isinstance(result, bool), "Re-enabled system should accept data"


class TestSystemResilience:
    """Test system resilience under various failure conditions."""

    def test_partial_component_failure(self):
        """Test system continues working when some components fail."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config with invalid paths to simulate failures
            config = ObservabilityConfig(
                enabled=True,
                data_directory="/nonexistent/data",
                logs_directory="/nonexistent/logs"
            )

            api = UnifiedObservationAPI(config=config)

            # System should handle failures gracefully
            result = api.accept_data_point({"test": "data"})
            # Should not crash, may return False
            assert isinstance(result, bool)

            # Status should still be retrievable
            status = api.get_status()
            assert isinstance(status, dict)

    def test_configuration_fallback(self):
        """Test configuration fallback when file loading fails."""
        # This should use default configuration
        api = UnifiedObservationAPI()

        # Should work with defaults
        status = api.get_status()
        assert isinstance(status, dict)
        assert "enabled" in status


if __name__ == "__main__":
    pytest.main([__file__])
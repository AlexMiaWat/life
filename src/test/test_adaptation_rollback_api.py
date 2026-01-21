"""
Integration tests for Adaptation Rollback API endpoints

Tests the HTTP API endpoints for adaptation rollback functionality:
- GET /adaptation/rollback/options
- GET /adaptation/history
- POST /adaptation/rollback
"""

import json
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import requests

from src.adaptation.adaptation import AdaptationManager
from src.state.self_state import SelfState


@pytest.mark.integration
@pytest.mark.real_server
class TestAdaptationRollbackAPI:
    """Integration tests for adaptation rollback API endpoints"""

    def test_get_rollback_options_empty_history(self, real_server):
        """Test GET /adaptation/rollback/options with empty history"""
        if not real_server:
            pytest.skip("Requires real server")

        response = requests.get("http://localhost:8000/adaptation/rollback/options")
        assert response.status_code == 200

        data = response.json()
        assert "options" in data
        assert "total_options" in data
        assert isinstance(data["options"], list)
        # May be empty or have options depending on server state

    def test_get_adaptation_history(self, real_server):
        """Test GET /adaptation/history"""
        if not real_server:
            pytest.skip("Requires real server")

        response = requests.get("http://localhost:8000/adaptation/history")
        assert response.status_code == 200

        data = response.json()
        assert "history" in data
        assert "total_entries" in data
        assert "returned_entries" in data
        assert isinstance(data["history"], list)
        assert data["returned_entries"] <= data["total_entries"]

    def test_post_rollback_timestamp_invalid_type(self, real_server):
        """Test POST /adaptation/rollback with invalid type"""
        if not real_server:
            pytest.skip("Requires real server")

        payload = {"type": "invalid"}
        response = requests.post(
            "http://localhost:8000/adaptation/rollback",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    def test_post_rollback_timestamp_missing_params(self, real_server):
        """Test POST /adaptation/rollback with missing timestamp"""
        if not real_server:
            pytest.skip("Requires real server")

        payload = {"type": "timestamp"}
        response = requests.post(
            "http://localhost:8000/adaptation/rollback",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    def test_post_rollback_steps_missing_params(self, real_server):
        """Test POST /adaptation/rollback with missing steps"""
        if not real_server:
            pytest.skip("Requires real server")

        payload = {"type": "steps"}
        response = requests.post(
            "http://localhost:8000/adaptation/rollback",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    def test_post_rollback_steps_invalid_value(self, real_server):
        """Test POST /adaptation/rollback with invalid steps value"""
        if not real_server:
            pytest.skip("Requires real server")

        payload = {"type": "steps", "steps": -1}
        response = requests.post(
            "http://localhost:8000/adaptation/rollback",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    def test_post_rollback_future_timestamp(self, real_server):
        """Test POST /adaptation/rollback with future timestamp"""
        if not real_server:
            pytest.skip("Requires real server")

        future_timestamp = time.time() + 3600  # 1 hour in future
        payload = {"type": "timestamp", "timestamp": future_timestamp}
        response = requests.post(
            "http://localhost:8000/adaptation/rollback",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        data = response.json()
        assert "error" in data

    @pytest.mark.slow
    def test_full_rollback_workflow(self, real_server):
        """Test complete rollback workflow with real adaptation data"""
        if not real_server:
            pytest.skip("Requires real server")

        # First, get current history
        response = requests.get("http://localhost:8000/adaptation/history")
        assert response.status_code == 200
        initial_history = response.json()["history"]

        # If no history, skip test
        if len(initial_history) == 0:
            pytest.skip("No adaptation history available for rollback test")

        # Get rollback options
        response = requests.get("http://localhost:8000/adaptation/rollback/options")
        assert response.status_code == 200
        options = response.json()["options"]

        # Should have at least one option
        assert len(options) > 0

        # Try rollback to first available option
        target_timestamp = options[0]["timestamp"]
        payload = {"type": "timestamp", "timestamp": target_timestamp}

        response = requests.post(
            "http://localhost:8000/adaptation/rollback",
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        # Should succeed (200) or fail gracefully (400)
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "rolled_back_params" in data
            assert "actual_timestamp" in data
        else:
            data = response.json()
            assert "error" in data


@pytest.mark.unit
class TestAdaptationRollbackAPIMocking:
    """Unit tests with mocked API calls"""

    def test_api_error_handling_malformed_json(self):
        """Test API error handling for malformed JSON"""
        from src.main_server_api import RequestHandler
        import io

        # Mock request with malformed JSON
        handler = RequestHandler(None, None, None)
        handler.rfile = io.BytesIO(b"{invalid json")
        handler.headers = {"Content-Length": "13"}
        handler.send_response = lambda code: None
        handler.end_headers = lambda: None
        handler.wfile = io.BytesIO()

        handler._handle_adaptation_rollback()

        # Should have written error response
        response = handler.wfile.getvalue().decode()
        assert "Invalid JSON" in response

    def test_api_validation_timestamp_type(self):
        """Test API validation for timestamp type"""
        from src.main_server_api import RequestHandler
        import io

        # Mock request with invalid timestamp
        handler = RequestHandler(None, None, None)
        payload = {"type": "timestamp", "timestamp": "not_a_number"}
        handler.rfile = io.BytesIO(json.dumps(payload).encode())
        handler.headers = {"Content-Length": str(len(json.dumps(payload)))}
        handler.send_response = lambda code: None
        handler.end_headers = lambda: None
        handler.wfile = io.BytesIO()

        # Mock server state
        class MockServer:
            pass

        handler.server = MockServer()

        handler._handle_adaptation_rollback()

        # Should have written validation error
        response = handler.wfile.getvalue().decode()
        assert "timestamp must be a number" in response

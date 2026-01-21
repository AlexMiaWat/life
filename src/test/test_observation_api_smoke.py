"""
Дымовые тесты для Observation API

Проверяем:
- Создание экземпляров классов
- Базовую функциональность методов
- Отсутствие исключений при нормальной работе
- Корректность основных операций
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.observability.observation_api import (
    app,
    MetricsResponse,
    BehaviorPatternResponse,
    ObservationReportResponse,
    HealthResponse,
    ErrorResponse,
)


@pytest.mark.smoke
class TestObservationAPISmoke:
    """Дымовые тесты для Observation API"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.client = TestClient(app)

    def test_api_creation(self):
        """Проверка создания FastAPI приложения"""
        assert app is not None
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0

    def test_health_endpoint(self):
        """Проверка health endpoint"""
        response = self.client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data

        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert isinstance(data["uptime"], (int, float))

    def test_models_creation(self):
        """Проверка создания моделей ответов"""
        # HealthResponse
        health = HealthResponse(
            status="ok",
            timestamp=1234567890.0,
            version="1.0.0",
            uptime=100.0
        )
        assert health.status == "ok"
        assert health.uptime == 100.0

        # MetricsResponse
        metrics = MetricsResponse(
            timestamp=1234567890.0,
            cycle_count=50,
            uptime_seconds=3600.0,
            memory_entries_count=100,
            learning_effectiveness=0.8,
            adaptation_rate=0.6,
            decision_success_rate=0.9,
            error_count=1,
            integrity_score=0.95,
            energy_level=0.75,
            action_count=20,
            event_processing_rate=5.5,
            state_change_frequency=2.1
        )
        assert metrics.cycle_count == 50
        assert metrics.energy_level == 0.75

        # BehaviorPatternResponse
        pattern = BehaviorPatternResponse(
            pattern_type="test_pattern",
            description="Test description",
            frequency=10.0,
            impact_score=0.7,
            first_observed=1000.0,
            last_observed=2000.0,
            metadata={"key": "value"}
        )
        assert pattern.pattern_type == "test_pattern"
        assert pattern.frequency == 10.0

        # ErrorResponse
        error = ErrorResponse(
            error="Test error",
            detail="Test details",
            timestamp=1234567890.0
        )
        assert error.error == "Test error"
        assert error.detail == "Test details"

    @patch('src.observability.observation_api.observer')
    def test_observe_logs_endpoint(self, mock_observer):
        """Проверка observe/logs endpoint"""
        # Настраиваем mock
        mock_report = Mock()
        mock_report.observation_period = (1000.0, 2000.0)
        mock_report.metrics_summary = Mock()
        mock_report.metrics_summary.timestamp = 2000.0
        mock_report.metrics_summary.cycle_count = 100
        mock_report.metrics_summary.uptime_seconds = 1800.0
        mock_report.metrics_summary.memory_entries_count = 50
        mock_report.metrics_summary.learning_effectiveness = 0.8
        mock_report.metrics_summary.adaptation_rate = 0.7
        mock_report.metrics_summary.decision_success_rate = 0.9
        mock_report.metrics_summary.error_count = 2
        mock_report.metrics_summary.integrity_score = 0.95
        mock_report.metrics_summary.energy_level = 0.8
        mock_report.metrics_summary.action_count = 25
        mock_report.metrics_summary.event_processing_rate = 10.0
        mock_report.metrics_summary.state_change_frequency = 5.0

        mock_report.behavior_patterns = []
        mock_report.trends = {}
        mock_report.anomalies = []
        mock_report.recommendations = []

        mock_observer.observe_from_logs.return_value = mock_report

        response = self.client.get("/observe/logs?start_time_offset=3600")

        assert response.status_code == 200
        data = response.json()

        assert "observation_period" in data
        assert "metrics_summary" in data
        assert "behavior_patterns" in data
        assert data["metrics_summary"]["cycle_count"] == 100

    @patch('src.observability.observation_api.observer')
    def test_observe_snapshots_endpoint(self, mock_observer):
        """Проверка observe/snapshots endpoint"""
        import tempfile
        from pathlib import Path

        # Создаем временную директорию с тестовым файлом
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_file = Path(temp_dir) / "test_snapshot.json"
            snapshot_file.write_text('{"test": "data"}')

            # Настраиваем mock
            mock_report = Mock()
            mock_report.observation_period = (1000.0, 2000.0)
            mock_report.metrics_summary = Mock()
            mock_report.metrics_summary.timestamp = 2000.0
            mock_report.metrics_summary.cycle_count = 50
            mock_report.metrics_summary.uptime_seconds = 900.0
            mock_report.metrics_summary.memory_entries_count = 25
            mock_report.metrics_summary.learning_effectiveness = 0.7
            mock_report.metrics_summary.adaptation_rate = 0.6
            mock_report.metrics_summary.decision_success_rate = 0.8
            mock_report.metrics_summary.error_count = 1
            mock_report.metrics_summary.integrity_score = 0.9
            mock_report.metrics_summary.energy_level = 0.7
            mock_report.metrics_summary.action_count = 15
            mock_report.metrics_summary.event_processing_rate = 8.0
            mock_report.metrics_summary.state_change_frequency = 3.0

            mock_report.behavior_patterns = []
            mock_report.trends = {}
            mock_report.anomalies = []
            mock_report.recommendations = []

            mock_observer.observe_from_snapshots.return_value = mock_report

            response = self.client.get(f"/observe/snapshots?snapshot_dir={temp_dir}")

            assert response.status_code == 200
            data = response.json()

            assert "observation_period" in data
            assert "metrics_summary" in data

    def test_observe_snapshots_endpoint_missing_dir(self):
        """Проверка observe/snapshots endpoint с несуществующей директорией"""
        response = self.client.get("/observe/snapshots?snapshot_dir=/nonexistent/dir")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_observe_snapshots_endpoint_no_snapshots(self):
        """Проверка observe/snapshots endpoint без файлов снимков"""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            response = self.client.get(f"/observe/snapshots?snapshot_dir={temp_dir}")

            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    @patch('src.observability.observation_api.observer')
    def test_metrics_current_endpoint(self, mock_observer):
        """Проверка metrics/current endpoint"""
        # Настраиваем mock с историей наблюдений
        mock_report = Mock()
        mock_report.metrics_summary = Mock()
        mock_report.metrics_summary.timestamp = 1234567890.0
        mock_report.metrics_summary.cycle_count = 75
        mock_report.metrics_summary.uptime_seconds = 2700.0
        mock_report.metrics_summary.memory_entries_count = 30
        mock_report.metrics_summary.learning_effectiveness = 0.85
        mock_report.metrics_summary.adaptation_rate = 0.75
        mock_report.metrics_summary.decision_success_rate = 0.95
        mock_report.metrics_summary.error_count = 0
        mock_report.metrics_summary.integrity_score = 0.98
        mock_report.metrics_summary.energy_level = 0.9
        mock_report.metrics_summary.action_count = 30
        mock_report.metrics_summary.event_processing_rate = 12.0
        mock_report.metrics_summary.state_change_frequency = 6.0

        mock_observer.observation_history = [mock_report]

        response = self.client.get("/metrics/current")

        assert response.status_code == 200
        data = response.json()

        assert data["cycle_count"] == 75
        assert data["energy_level"] == 0.9

    @patch('src.observability.observation_api.observer')
    def test_metrics_current_endpoint_no_history(self, mock_observer):
        """Проверка metrics/current endpoint без истории"""
        mock_observer.observation_history = []

        # Настраиваем mock для observe_from_logs
        mock_report = Mock()
        mock_report.metrics_summary = Mock()
        mock_report.metrics_summary.timestamp = 1234567890.0
        mock_report.metrics_summary.cycle_count = 25
        mock_report.metrics_summary.uptime_seconds = 900.0
        mock_report.metrics_summary.memory_entries_count = 15
        mock_report.metrics_summary.learning_effectiveness = 0.7
        mock_report.metrics_summary.adaptation_rate = 0.6
        mock_report.metrics_summary.decision_success_rate = 0.8
        mock_report.metrics_summary.error_count = 1
        mock_report.metrics_summary.integrity_score = 0.9
        mock_report.metrics_summary.energy_level = 0.7
        mock_report.metrics_summary.action_count = 10
        mock_report.metrics_summary.event_processing_rate = 5.0
        mock_report.metrics_summary.state_change_frequency = 2.0

        mock_observer.observe_from_logs.return_value = mock_report

        response = self.client.get("/metrics/current")

        assert response.status_code == 200
        data = response.json()
        assert data["cycle_count"] == 25

    @patch('src.observability.observation_api.observer')
    def test_patterns_endpoint(self, mock_observer):
        """Проверка patterns endpoint"""
        # Настраиваем mock
        mock_pattern = Mock()
        mock_pattern.pattern_type = "test_pattern"
        mock_pattern.description = "Test pattern"
        mock_pattern.frequency = 15.0
        mock_pattern.impact_score = 0.8
        mock_pattern.first_observed = 1000.0
        mock_pattern.last_observed = 3000.0
        mock_pattern.metadata = {"test": "meta"}

        mock_report = Mock()
        mock_report.behavior_patterns = [mock_pattern]
        mock_observer.observation_history = [mock_report]

        response = self.client.get("/patterns")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["pattern_type"] == "test_pattern"

    @patch('src.observability.observation_api.observer')
    def test_patterns_endpoint_no_history(self, mock_observer):
        """Проверка patterns endpoint без истории"""
        mock_observer.observation_history = []

        response = self.client.get("/patterns")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @patch('src.observability.observation_api.observer')
    def test_history_summary_endpoint(self, mock_observer):
        """Проверка history/summary endpoint"""
        mock_observer.get_observation_history_summary.return_value = {
            "total_observations": 10,
            "date_range": "2024-01-01 to 2024-01-02",
            "avg_metrics": {"energy": 0.8}
        }

        response = self.client.get("/history/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_observations" in data

    @patch('src.observability.observation_api.observer')
    def test_anomalies_endpoint(self, mock_observer):
        """Проверка anomalies endpoint"""
        mock_report = Mock()
        mock_report.anomalies = [
            {"type": "high_energy", "severity": 0.9},
            {"type": "low_integrity", "severity": 0.7}
        ]
        mock_report.metrics_summary = Mock()
        mock_report.metrics_summary.timestamp = 1234567890.0

        mock_observer.observation_history = [mock_report]

        response = self.client.get("/anomalies")

        assert response.status_code == 200
        data = response.json()

        assert "anomalies" in data
        assert "count" in data
        assert data["count"] == 2

    @patch('src.observability.observation_api.observer')
    def test_anomalies_endpoint_no_history(self, mock_observer):
        """Проверка anomalies endpoint без истории"""
        mock_observer.observation_history = []

        response = self.client.get("/anomalies")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @patch('src.observability.observation_api.observer')
    def test_recommendations_endpoint(self, mock_observer):
        """Проверка recommendations endpoint"""
        mock_report = Mock()
        mock_report.recommendations = [
            "Increase energy levels",
            "Check integrity systems"
        ]
        mock_report.metrics_summary = Mock()
        mock_report.metrics_summary.timestamp = 1234567890.0

        mock_observer.observation_history = [mock_report]

        response = self.client.get("/recommendations")

        assert response.status_code == 200
        data = response.json()

        assert "recommendations" in data
        assert "count" in data
        assert data["count"] == 2

    @patch('src.observability.observation_api.observer')
    def test_recommendations_endpoint_no_history(self, mock_observer):
        """Проверка recommendations endpoint без истории"""
        mock_observer.observation_history = []

        response = self.client.get("/recommendations")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_error_handling(self):
        """Проверка обработки ошибок API"""
        # Тестируем несуществующий endpoint
        response = self.client.get("/nonexistent")

        assert response.status_code == 404

        # Тестируем невалидные параметры
        response = self.client.get("/observe/logs?start_time_offset=invalid")

        # FastAPI должен обработать ошибку валидации
        assert response.status_code in [400, 422]
"""
Статические тесты для Observation API

Проверяем:
- Структуру классов и модулей
- Константы и их значения
- Сигнатуры методов
- Типы возвращаемых значений
- Отсутствие запрещенных методов/атрибутов
- Архитектурные ограничения
"""

import inspect
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

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


@pytest.mark.static
class TestObservationAPIStatic:
    """Статические тесты для Observation API"""

    def test_api_structure(self):
        """Проверка структуры FastAPI приложения"""
        assert app is not None
        assert hasattr(app, 'routes')
        assert hasattr(app, 'title')
        assert hasattr(app, 'description')
        assert hasattr(app, 'version')

        # Проверяем метаданные приложения
        assert app.title == "Life System External Observation API"
        assert "Life" in app.description
        assert app.version == "1.0.0"

    def test_pydantic_models_structure(self):
        """Проверка структуры Pydantic моделей"""
        # MetricsResponse
        assert hasattr(MetricsResponse, "__fields__")
        required_fields = [
            'timestamp', 'cycle_count', 'uptime_seconds', 'memory_entries_count',
            'learning_effectiveness', 'adaptation_rate', 'decision_success_rate',
            'error_count', 'integrity_score', 'energy_level', 'action_count',
            'event_processing_rate', 'state_change_frequency'
        ]
        for field in required_fields:
            assert field in MetricsResponse.__fields__

        # BehaviorPatternResponse
        assert hasattr(BehaviorPatternResponse, "__fields__")
        required_fields = [
            'pattern_type', 'description', 'frequency', 'impact_score',
            'first_observed', 'last_observed', 'metadata'
        ]
        for field in required_fields:
            assert field in BehaviorPatternResponse.__fields__

        # ObservationReportResponse
        assert hasattr(ObservationReportResponse, "__fields__")
        required_fields = [
            'observation_period', 'metrics_summary', 'behavior_patterns',
            'trends', 'anomalies', 'recommendations'
        ]
        for field in required_fields:
            assert field in ObservationReportResponse.__fields__

        # HealthResponse
        assert hasattr(HealthResponse, "__fields__")
        required_fields = ['status', 'timestamp', 'version', 'uptime']
        for field in required_fields:
            assert field in HealthResponse.__fields__

        # ErrorResponse
        assert hasattr(ErrorResponse, "__fields__")
        required_fields = ['error', 'timestamp']
        for field in required_fields:
            assert field in ErrorResponse.__fields__

    def test_api_routes(self):
        """Проверка наличия API маршрутов"""
        routes = [route.path for route in app.routes]

        expected_routes = [
            "/health",
            "/observe/logs",
            "/observe/snapshots",
            "/metrics/current",
            "/patterns",
            "/history/summary",
            "/anomalies",
            "/recommendations"
        ]

        for route in expected_routes:
            assert route in routes, f"Route {route} not found in API"

    def test_route_methods(self):
        """Проверка методов API маршрутов"""
        route_methods = {}
        for route in app.routes:
            route_methods[route.path] = route.methods

        # Проверяем конкретные маршруты
        assert "GET" in route_methods.get("/health", [])
        assert "GET" in route_methods.get("/observe/logs", [])
        assert "GET" in route_methods.get("/observe/snapshots", [])
        assert "GET" in route_methods.get("/metrics/current", [])
        assert "GET" in route_methods.get("/patterns", [])
        assert "GET" in route_methods.get("/history/summary", [])
        assert "GET" in route_methods.get("/anomalies", [])
        assert "GET" in route_methods.get("/recommendations", [])

    def test_model_creation(self):
        """Проверка создания экземпляров моделей"""
        # HealthResponse
        health = HealthResponse(
            status="healthy",
            timestamp=1234567890.0,
            version="1.0.0",
            uptime=3600.0
        )
        assert health.status == "healthy"
        assert health.version == "1.0.0"

        # MetricsResponse
        metrics = MetricsResponse(
            timestamp=1234567890.0,
            cycle_count=100,
            uptime_seconds=3600.0,
            memory_entries_count=50,
            learning_effectiveness=0.8,
            adaptation_rate=0.6,
            decision_success_rate=0.9,
            error_count=2,
            integrity_score=0.95,
            energy_level=0.7,
            action_count=25,
            event_processing_rate=10.5,
            state_change_frequency=5.2
        )
        assert metrics.cycle_count == 100
        assert metrics.energy_level == 0.7

        # ErrorResponse
        error = ErrorResponse(
            error="Test error",
            detail="Test detail",
            timestamp=1234567890.0
        )
        assert error.error == "Test error"
        assert error.detail == "Test detail"

    def test_model_validation(self):
        """Проверка валидации моделей"""
        # Проверяем что модели требуют обязательные поля
        with pytest.raises(Exception):
            # Пропускаем обязательное поле status
            HealthResponse(
                timestamp=1234567890.0,
                version="1.0.0",
                uptime=3600.0
            )

        with pytest.raises(Exception):
            # Пропускаем обязательное поле error
            ErrorResponse(
                detail="Test detail",
                timestamp=1234567890.0
            )

    def test_architecture_constraints(self):
        """Проверка архитектурных ограничений"""
        # Проверяем отсутствие запрещенных методов/атрибутов в глобальном scope
        forbidden_attrs = ['interpret', 'evaluate', 'analyze', 'consciousness', 'awareness']
        for attr in forbidden_attrs:
            assert not hasattr(app, attr), f"Найден запрещенный атрибут в app: {attr}"

        # Проверяем пассивность - отсутствие методов изменения состояния системы
        dangerous_methods = ['modify', 'change', 'update_system', 'inject', 'post', 'put', 'patch', 'delete']
        # Проверяем только GET методы для пассивности
        for route in app.routes:
            if hasattr(route, 'methods'):
                for method in dangerous_methods:
                    assert method.upper() not in route.methods, f"Найден опасный HTTP метод: {method}"

    def test_api_constants(self):
        """Проверка констант API"""
        # Проверяем глобальные константы
        import src.observability.observation_api as api_module

        assert hasattr(api_module, 'api_start_time')
        assert hasattr(api_module, 'observer')

        # api_start_time должен быть числом (timestamp)
        assert isinstance(api_module.api_start_time, (int, float))

    def test_error_handling(self):
        """Проверка обработки ошибок в статическом контексте"""
        # Проверяем что приложение имеет глобальный обработчик ошибок
        assert hasattr(app, 'exception_handler')

        # Проверяем наличие обработчика для Exception
        exception_handlers = getattr(app, '_exception_handlers', {})
        assert Exception in exception_handlers

    def test_response_models(self):
        """Проверка моделей ответов"""
        # Проверяем что все response модели наследуются от BaseModel
        from pydantic import BaseModel

        models = [MetricsResponse, BehaviorPatternResponse, ObservationReportResponse,
                 HealthResponse, ErrorResponse]

        for model in models:
            assert issubclass(model, BaseModel), f"Model {model.__name__} should inherit from BaseModel"

    def test_route_dependencies(self):
        """Проверка зависимостей маршрутов"""
        # Проверяем что маршруты используют правильные модели ответов
        for route in app.routes:
            if hasattr(route, 'response_model'):
                response_model = route.response_model
                if response_model:
                    assert response_model in [MetricsResponse, BehaviorPatternResponse,
                                            ObservationReportResponse, HealthResponse, ErrorResponse]
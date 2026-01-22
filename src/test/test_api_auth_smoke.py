"""
Дымовые тесты для API с аутентификацией

Проверяем базовую работоспособность:
- Запуск приложения
- Доступность публичных эндпоинтов
- Базовая аутентификация
- Простые успешные сценарии
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api import app


@pytest.fixture
def client():
    """Тестовый клиент FastAPI"""
    return TestClient(app)


@pytest.mark.smoke
@pytest.mark.skip(reason="Requires full authentication API implementation")
class TestAPISmoke:
    """Дымовые тесты для API с аутентификацией"""

    def test_app_can_start(self):
        """Проверка что приложение может запуститься"""
        assert app is not None
        assert hasattr(app, "routes")
        assert len(app.routes) > 0

    def test_root_endpoint_accessible(self, client):
        """Проверка доступности корневого эндпоинта"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["version"] == "1.0.0"

    def test_register_endpoint_exists(self, client):
        """Проверка существования эндпоинта регистрации"""
        # Проверяем что маршрут существует
        routes = [route.path for route in app.routes if hasattr(route, "methods")]
        assert "/register" in routes

        # Проверяем что можем получить информацию о маршруте
        response = client.get("/docs")  # OpenAPI docs
        assert response.status_code == 200

    def test_token_endpoint_exists(self, client):
        """Проверка существования эндпоинта получения токена"""
        routes = [route.path for route in app.routes if hasattr(route, "methods")]
        assert "/token" in routes

    def test_protected_endpoints_exist(self, client):
        """Проверка существования защищенных эндпоинтов"""
        routes = [route.path for route in app.routes if hasattr(route, "methods")]
        protected_routes = ["/protected", "/status", "/event", "/users"]

        for route in protected_routes:
            assert route in routes

    def test_openapi_docs_accessible(self, client):
        """Проверка доступности OpenAPI документации"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_openapi_json_accessible(self, client):
        """Проверка доступности OpenAPI JSON схемы"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "Life API"

    # ============================================================================
    # Basic Authentication Smoke Tests
    # ============================================================================

    def test_basic_authentication_flow_smoke(self, client):
        """Дымовой тест базового потока аутентификации"""
        # Попытка доступа к защищенному эндпоинту без токена
        response = client.get("/protected")
        assert response.status_code == 401  # Должен вернуть 401 Unauthorized

        # Попытка входа с правильными учетными данными
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        assert "access_token" in token_data
        assert "token_type" in token_data
        assert token_data["token_type"] == "bearer"

        # Доступ к защищенному эндпоинту с токеном
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "admin" in data["message"]

    def test_invalid_credentials_smoke(self, client):
        """Дымовой тест с неправильными учетными данными"""
        login_data = {"username": "admin", "password": "wrongpassword"}
        response = client.post("/token", data=login_data)
        assert response.status_code == 401

    def test_user_registration_smoke(self, client):
        """Дымовой тест регистрации нового пользователя"""
        # Регистрируем нового пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User",
        }
        response = client.post("/register", json=user_data)
        assert response.status_code == 201

        user_response = response.json()
        assert user_response["username"] == "testuser"
        assert user_response["email"] == "test@example.com"
        assert user_response["full_name"] == "Test User"
        assert user_response["disabled"] is False

        # Проверяем что можем войти под новым пользователем
        login_data = {"username": "testuser", "password": "testpass123"}
        response = client.post("/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        assert "access_token" in token_data

    def test_duplicate_registration_fails(self, client):
        """Проверка что повторная регистрация того же пользователя fails"""
        user_data = {
            "username": "duplicate_user",
            "email": "dup@example.com",
            "password": "password123",
        }

        # Первая регистрация должна пройти
        response = client.post("/register", json=user_data)
        assert response.status_code == 201

        # Вторая регистрация должна fail
        response = client.post("/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    # ============================================================================
    # Basic Status Endpoint Smoke Tests
    # ============================================================================

    def test_status_endpoint_requires_auth(self, client):
        """Проверка что /status требует аутентификации"""
        response = client.get("/status")
        assert response.status_code == 401

    def test_status_endpoint_with_auth_smoke(self, client):
        """Дымовой тест /status с аутентификацией"""
        # Получаем токен
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/token", data=login_data)
        token = response.json()["access_token"]

        # Запрашиваем статус
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/status", headers=headers)
        assert response.status_code == 200

        data = response.json()
        # Проверяем наличие основных полей
        required_fields = ["active", "ticks", "age", "energy", "stability", "integrity"]
        for field in required_fields:
            assert field in data

        # Проверяем типы данных
        assert isinstance(data["active"], bool)
        assert isinstance(data["ticks"], int)
        assert isinstance(data["age"], (int, float))
        assert isinstance(data["energy"], (int, float))

    def test_status_minimal_response_smoke(self, client):
        """Дымовой тест минимального ответа /status"""
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/token", data=login_data)
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/status?minimal=true", headers=headers)
        assert response.status_code == 200

        data = response.json()
        # В минимальном режиме должны быть только базовые поля
        assert set(data.keys()) == {
            "active",
            "ticks",
            "age",
            "energy",
            "stability",
            "integrity",
        }

    # ============================================================================
    # Basic Event Endpoint Smoke Tests
    # ============================================================================

    def test_event_endpoint_requires_auth(self, client):
        """Проверка что /event требует аутентификации"""
        event_data = {"type": "noise", "intensity": 0.1}
        response = client.post("/event", json=event_data)
        assert response.status_code == 401

    def test_event_creation_smoke(self, client):
        """Дымовой тест создания события"""
        # Получаем токен
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/token", data=login_data)
        token = response.json()["access_token"]

        # Создаем событие
        headers = {"Authorization": f"Bearer {token}"}
        event_data = {
            "type": "noise",
            "intensity": 0.5,
            "metadata": {"source": "smoke_test"},
        }
        response = client.post("/event", json=event_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "noise"
        assert data["intensity"] == 0.5
        assert data["metadata"] == {"source": "smoke_test"}
        assert "message" in data
        assert "admin" in data["message"]

    def test_event_minimal_creation_smoke(self, client):
        """Дымовой тест создания события с минимальными данными"""
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/token", data=login_data)
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        event_data = {"type": "shock"}
        response = client.post("/event", json=event_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "shock"
        assert data["intensity"] == 0.0  # По умолчанию
        assert isinstance(data["timestamp"], (int, float))

    # ============================================================================
    # Basic Users Endpoint Smoke Tests
    # ============================================================================

    def test_users_endpoint_requires_auth(self, client):
        """Проверка что /users требует аутентификации"""
        response = client.get("/users")
        assert response.status_code == 401

    def test_users_list_smoke(self, client):
        """Дымовой тест получения списка пользователей"""
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/token", data=login_data)
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/users", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # admin и user

        # Проверяем структуру пользователей
        for user in data:
            assert "username" in user
            assert "email" in user
            assert "disabled" in user

    # ============================================================================
    # Error Handling Smoke Tests
    # ============================================================================

    def test_invalid_token_format(self, client):
        """Проверка обработки неправильного формата токена"""
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401

    def test_expired_token_simulation(self, client):
        """Симуляция истекшего токена"""
        # Создаем токен с истекшим сроком действия
        import time

        import jwt

        from api import ALGORITHM, SECRET_KEY

        expired_payload = {
            "sub": "admin",
            "exp": int(time.time()) - 3600,  # Истек час назад
        }
        expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/protected", headers=headers)
        assert response.status_code == 401

    def test_malformed_json_handling(self, client):
        """Проверка обработки malformed JSON"""
        login_data = {"username": "admin", "password": "admin123"}
        response = client.post("/token", data=login_data)
        token = response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/event", data="invalid json", headers=headers)
        assert response.status_code == 400

    # ============================================================================
    # Application Startup Smoke Tests
    # ============================================================================

    def test_application_startup_simulation(self):
        """Симуляция запуска приложения"""
        # Проверяем что все импорты работают
        from api import app, fake_users_db

        assert app is not None
        assert isinstance(fake_users_db, dict)
        assert len(fake_users_db) > 0

        # Проверяем что все маршруты зарегистрированы
        routes_count = len([r for r in app.routes if hasattr(r, "path")])
        assert routes_count >= 7  # Минимум основных маршрутов

    @patch("uvicorn.run")
    def test_main_execution_path(self, mock_uvicorn_run):
        """Проверка пути выполнения main (имитация запуска через uvicorn)"""
        # Имитируем запуск через python -m api

        # Проверяем что модуль может быть импортирован
        try:
            import api

            assert hasattr(api, "app")
            assert hasattr(api, "fake_users_db")
        except ImportError as e:
            pytest.fail(f"Cannot import api module: {e}")

    def test_environment_dependencies(self):
        """Проверка доступности основных зависимостей"""
        try:
            import fastapi
            import jwt
            import passlib
            import uvicorn
            from pydantic import BaseModel

            # Все зависимости должны быть доступны
            assert fastapi is not None
            assert uvicorn is not None
            assert jwt is not None
            assert passlib is not None
            assert BaseModel is not None
        except ImportError as e:
            pytest.fail(f"Missing dependency: {e}")

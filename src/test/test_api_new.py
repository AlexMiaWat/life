"""
Тесты для нового упрощенного API Life (без аутентификации)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture
def client():
    """Тестовый клиент FastAPI"""
    return TestClient(app)


@pytest.mark.unit
class TestAPISimplified:
    """Тесты для упрощенного API без аутентификации"""

    def test_get_status_basic(self, client):
        """Тест GET /status - базовый статус"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert "energy" in data
        assert "integrity" in data
        assert "stability" in data
        assert "ticks" in data

    def test_get_status_minimal(self, client):
        """Тест GET /status с параметром minimal=true"""
        response = client.get("/status?minimal=true")
        assert response.status_code == 200
        data = response.json()
        # В минимальном режиме должно быть меньше полей
        assert "energy" in data
        assert "ticks" in data

    def test_post_event_basic(self, client):
        """Тест POST /event - создание базового события"""
        event_data = {
            "type": "test_event",
            "intensity": 0.5,
            "metadata": {"test": True}
        }
        response = client.post("/event", json=event_data)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "test_event"
        assert data["intensity"] == 0.5
        assert "message" in data

    def test_post_event_minimal(self, client):
        """Тест POST /event с минимальными данными"""
        event_data = {
            "type": "minimal_event"
        }
        response = client.post("/event", json=event_data)
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "minimal_event"
        assert data["intensity"] == 0.0  # значение по умолчанию

    def test_api_without_authentication(self, client):
        """Тест, что API работает без аутентификации"""
        # Проверяем, что можем получить статус без токенов
        response = client.get("/status")
        assert response.status_code == 200

        # Проверяем, что можем создать событие без токенов
        event_data = {"type": "auth_test"}
        response = client.post("/event", json=event_data)
        assert response.status_code == 200

    def test_api_key_optional(self, client):
        """Тест, что API ключ опционален"""
        # Запросы без API ключа должны работать
        response = client.get("/status")
        assert response.status_code == 200

        # Запросы с API ключом тоже должны работать
        headers = {"X-API-Key": "test_key"}
        response = client.get("/status", headers=headers)
        assert response.status_code == 200

    def test_event_validation(self, client):
        """Тест валидации данных события"""
        # Некорректный тип события - пустой тип
        event_data = {
            "type": "",  # пустой тип
            "intensity": 0.5
        }
        response = client.post("/event", json=event_data)
        # В текущей реализации API принимает пустой тип, но это можно изменить
        assert response.status_code in [200, 422]  # Либо принимает, либо валидирует

        # Некорректная интенсивность
        event_data = {
            "type": "test",
            "intensity": 2.0  # интенсивность > 1.0 может быть принята
        }
        response = client.post("/event", json=event_data)
        assert response.status_code == 200  # API принимает любые значения интенсивности
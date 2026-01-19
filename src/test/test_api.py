"""
Базовые тесты API сервера
Требуют запущенный сервер (можно использовать --real-server)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import requests


@pytest.fixture
def api_base_url(server_config):
    """Возвращает базовый URL API сервера"""
    if server_config["use_real"]:
        return f"http://localhost:{server_config['port']}"
    else:
        # Для тестового сервера используем фикстуру server_setup
        pytest.skip(
            "test_api.py requires real server. Use --real-server or test_api_integration.py"
        )


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_get_status(api_base_url):
    """Тест GET /status"""
    response = requests.get(f"{api_base_url}/status", timeout=5)
    assert response.status_code == 200
    assert response.headers.get("Content-type") == "application/json"
    data = response.json()
    assert "energy" in data
    assert "integrity" in data
    assert "stability" in data


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_get_clear_data(api_base_url):
    """Тест GET /clear-data"""
    response = requests.get(f"{api_base_url}/clear-data", timeout=5)
    assert response.status_code == 200
    assert response.text == "Data cleared"


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_post_event_success(api_base_url):
    """Тест POST /event с правильным JSON"""
    data = {"type": "test_event", "intensity": 0.1, "metadata": {"key": "value"}}
    response = requests.post(f"{api_base_url}/event", json=data, timeout=5)
    assert response.status_code == 200
    assert response.text == "Event accepted"


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
def test_post_event_invalid_json(api_base_url):
    """Тест POST /event с неправильным JSON"""
    response = requests.post(
        f"{api_base_url}/event",
        data="invalid json",
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    assert response.status_code == 400
    assert "Invalid JSON" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

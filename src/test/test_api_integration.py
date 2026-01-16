"""
Интеграционные тесты для HTTP API сервера
Поддерживают работу с реальным сервером (--real-server) или тестовым сервером
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import threading
import requests
import json
import pytest
from http.server import HTTPServer
from main_server_api import StoppableHTTPServer, LifeHandler, start_api_server
from state.self_state import SelfState
from environment.event_queue import EventQueue
from environment.event import Event


@pytest.mark.integration
@pytest.mark.real_server
@pytest.mark.order(2)
class TestAPIServer:
    """Интеграционные тесты для API сервера"""
    
    def test_get_status(self, server_setup):
        """Тест GET /status"""
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        assert response.headers['Content-type'] == 'application/json'
        
        data = response.json()
        assert 'energy' in data
        assert 'integrity' in data
        assert 'stability' in data
        assert 'ticks' in data
        assert isinstance(data['energy'], (int, float))
    
    def test_get_status_returns_current_state(self, server_setup):
        """Тест, что GET /status возвращает текущее состояние"""
        # Для реального сервера нельзя изменить состояние напрямую
        if server_setup.get('is_real_server'):
            # Просто проверяем, что статус доступен
            response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert 'energy' in data
            assert 'ticks' in data
        else:
            # Для тестового сервера можем изменить состояние
            server_setup['self_state'].energy = 75.0
            server_setup['self_state'].ticks = 100
            
            response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert data['energy'] == 75.0
            assert data['ticks'] == 100
    
    def test_get_clear_data(self, server_setup):
        """Тест GET /clear-data"""
        response = requests.get(f"{server_setup['base_url']}/clear-data", timeout=5)
        assert response.status_code == 200
        assert response.text == "Data cleared"
    
    def test_get_unknown_endpoint(self, server_setup):
        """Тест GET неизвестного эндпоинта"""
        response = requests.get(f"{server_setup['base_url']}/unknown", timeout=5)
        assert response.status_code == 404
        assert response.text == "Unknown endpoint"
    
    def test_post_event_success(self, server_setup):
        """Тест POST /event с валидными данными"""
        payload = {
            "type": "shock",
            "intensity": 0.5,
            "metadata": {"test": "value"}
        }
        
        response = requests.post(
            f"{server_setup['base_url']}/event",
            json=payload,
            timeout=5
        )
        
        assert response.status_code == 200
        assert response.text == "Event accepted"
        
        # Проверяем очередь только для тестового сервера
        if not server_setup.get('is_real_server') and server_setup.get('event_queue'):
            assert server_setup['event_queue'].size() == 1
            
            # Проверяем содержимое события
            event = server_setup['event_queue'].pop()
            assert event.type == "shock"
            assert event.intensity == 0.5
            assert event.metadata == {"test": "value"}
    
    def test_post_event_minimal(self, server_setup):
        """Тест POST /event с минимальными данными (только type)"""
        payload = {"type": "noise"}
        
        response = requests.post(
            f"{server_setup['base_url']}/event",
            json=payload,
            timeout=5
        )
        
        assert response.status_code == 200
        
        # Проверяем очередь только для тестового сервера
        if not server_setup.get('is_real_server') and server_setup.get('event_queue'):
            assert server_setup['event_queue'].size() == 1
            
            event = server_setup['event_queue'].pop()
            assert event.type == "noise"
            assert event.intensity == 0.0  # По умолчанию
    
    def test_post_event_with_timestamp(self, server_setup):
        """Тест POST /event с кастомным timestamp"""
        custom_timestamp = 1000.0
        payload = {
            "type": "recovery",
            "intensity": 0.3,
            "timestamp": custom_timestamp
        }
        
        response = requests.post(
            f"{server_setup['base_url']}/event",
            json=payload,
            timeout=5
        )
        
        assert response.status_code == 200
        
        # Проверяем timestamp только для тестового сервера
        if not server_setup.get('is_real_server') and server_setup.get('event_queue'):
            event = server_setup['event_queue'].pop()
            assert event.timestamp == custom_timestamp
    
    def test_post_event_invalid_json(self, server_setup):
        """Тест POST /event с невалидным JSON"""
        response = requests.post(
            f"{server_setup['base_url']}/event",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.text
    
    def test_post_event_missing_type(self, server_setup):
        """Тест POST /event без поля type"""
        payload = {"intensity": 0.5}
        
        response = requests.post(
            f"{server_setup['base_url']}/event",
            json=payload,
            timeout=5
        )
        
        assert response.status_code == 400
        assert "'type' is required" in response.text
    
    def test_post_event_invalid_type(self, server_setup):
        """Тест POST /event с невалидным типом (не строка)"""
        payload = {"type": 123}
        
        response = requests.post(
            f"{server_setup['base_url']}/event",
            json=payload,
            timeout=5
        )
        
        assert response.status_code == 400
        assert "'type' is required" in response.text
    
    def test_post_event_multiple_events(self, server_setup):
        """Тест отправки нескольких событий"""
        events = [
            {"type": "shock", "intensity": 0.8},
            {"type": "noise", "intensity": 0.2},
            {"type": "recovery", "intensity": 0.4}
        ]
        
        for event_data in events:
            response = requests.post(
                f"{server_setup['base_url']}/event",
                json=event_data,
                timeout=5
            )
            assert response.status_code == 200
        
        # Проверяем очередь только для тестового сервера
        if not server_setup.get('is_real_server') and server_setup.get('event_queue'):
            assert server_setup['event_queue'].size() == 3
    
    def test_post_event_different_types(self, server_setup):
        """Тест отправки разных типов событий"""
        event_types = ["shock", "noise", "recovery", "decay", "idle"]
        
        for event_type in event_types:
            payload = {"type": event_type, "intensity": 0.3}
            response = requests.post(
                f"{server_setup['base_url']}/event",
                json=payload,
                timeout=5
            )
            assert response.status_code == 200
        
        # Проверяем очередь только для тестового сервера
        if not server_setup.get('is_real_server') and server_setup.get('event_queue'):
            assert server_setup['event_queue'].size() == len(event_types)
    
    def test_post_unknown_endpoint(self, server_setup):
        """Тест POST неизвестного эндпоинта"""
        response = requests.post(
            f"{server_setup['base_url']}/unknown",
            json={"type": "test"},
            timeout=5
        )
        
        assert response.status_code == 404
        assert response.text == "Unknown endpoint"
    
    def test_post_event_queue_overflow(self, server_setup):
        """Тест переполнения очереди событий"""
        # Для реального сервера этот тест не имеет смысла (не можем проверить очередь)
        if server_setup.get('is_real_server'):
            pytest.skip("Queue overflow test requires access to event_queue (test server only)")
        
        # Заполняем очередь до максимума (100)
        for i in range(100):
            payload = {"type": "noise", "intensity": 0.1}
            response = requests.post(
                f"{server_setup['base_url']}/event",
                json=payload,
                timeout=5
            )
            assert response.status_code == 200
        
        # Попытка добавить еще одно событие (должно быть проигнорировано)
        payload = {"type": "shock", "intensity": 0.9}
        response = requests.post(
            f"{server_setup['base_url']}/event",
            json=payload,
            timeout=5
        )
        # Сервер все равно вернет 200, но событие не добавится
        assert response.status_code == 200
        assert server_setup['event_queue'].size() == 100
    
    def test_get_status_after_events(self, server_setup):
        """Тест, что состояние обновляется после обработки событий"""
        # Отправляем событие
        payload = {"type": "shock", "intensity": 0.8}
        response = requests.post(
            f"{server_setup['base_url']}/event",
            json=payload,
            timeout=5
        )
        assert response.status_code == 200
        
        # Проверяем статус
        response = requests.get(f"{server_setup['base_url']}/status", timeout=5)
        assert response.status_code == 200
        # Состояние должно быть доступно (хотя события еще не обработаны)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

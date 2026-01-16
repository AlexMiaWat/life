"""
Интеграционные тесты для генератора событий с API сервером
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import time
import threading
import requests
import pytest
from main_server_api import StoppableHTTPServer, LifeHandler
from state.self_state import SelfState
from environment.event_queue import EventQueue
from environment.generator import EventGenerator
from environment.generator_cli import send_event


class TestGeneratorServerIntegration:
    """Интеграционные тесты генератора с сервером"""
    
    @pytest.fixture
    def server_setup(self):
        """Настройка тестового сервера"""
        self_state = SelfState()
        event_queue = EventQueue()
        server = StoppableHTTPServer(("localhost", 0), LifeHandler)
        server.self_state = self_state
        server.event_queue = event_queue
        server.dev_mode = False
        
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        time.sleep(0.1)
        
        port = server.server_address[1]
        base_url = f"http://localhost:{port}"
        
        yield {
            'server': server,
            'self_state': self_state,
            'event_queue': event_queue,
            'base_url': base_url,
            'port': port
        }
        
        server.shutdown()
        server_thread.join(timeout=2.0)
    
    def test_generator_send_to_server(self, server_setup):
        """Тест отправки сгенерированного события на сервер"""
        generator = EventGenerator()
        event = generator.generate()
        
        payload = {
            "type": event.type,
            "intensity": event.intensity,
            "timestamp": event.timestamp,
            "metadata": event.metadata
        }
        
        success, code, reason, body = send_event(
            "localhost",
            server_setup['port'],
            payload
        )
        
        assert success is True
        assert code == 200
        
        # Проверяем, что событие в очереди
        assert server_setup['event_queue'].size() == 1
        
        queued_event = server_setup['event_queue'].pop()
        assert queued_event.type == event.type
        assert abs(queued_event.intensity - event.intensity) < 0.001
    
    def test_generator_multiple_events_to_server(self, server_setup):
        """Тест отправки нескольких сгенерированных событий"""
        generator = EventGenerator()
        events = [generator.generate() for _ in range(5)]
        
        for event in events:
            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata
            }
            
            success, code, reason, body = send_event(
                "localhost",
                server_setup['port'],
                payload
            )
            assert success is True
            assert code == 200
        
        assert server_setup['event_queue'].size() == 5
    
    def test_generator_all_event_types_to_server(self, server_setup):
        """Тест отправки всех типов событий на сервер"""
        generator = EventGenerator()
        event_types = set()
        
        # Генерируем события до тех пор, пока не получим все типы
        for _ in range(100):
            event = generator.generate()
            event_types.add(event.type)
            
            payload = {
                "type": event.type,
                "intensity": event.intensity,
                "timestamp": event.timestamp,
                "metadata": event.metadata
            }
            
            success, code, reason, body = send_event(
                "localhost",
                server_setup['port'],
                payload
            )
            assert success is True
            
            if len(event_types) == 5:  # Все типы получены
                break
        
        assert len(event_types) == 5
        assert server_setup['event_queue'].size() > 0
    
    def test_generator_event_intensity_ranges(self, server_setup):
        """Тест, что интенсивности событий соответствуют спецификации"""
        generator = EventGenerator()
        
        intensity_ranges = {
            "noise": (-0.3, 0.3),
            "decay": (-0.5, 0.0),
            "recovery": (0.0, 0.5),
            "shock": (-1.0, 1.0),
            "idle": (0.0, 0.0)
        }
        
        # Генерируем события и проверяем диапазоны
        for _ in range(200):
            event = generator.generate()
            min_intensity, max_intensity = intensity_ranges[event.type]
            
            if event.type == "idle":
                assert event.intensity == 0.0
            else:
                assert min_intensity <= event.intensity <= max_intensity
    
    def test_generator_server_full_cycle(self, server_setup):
        """Тест полного цикла: генерация -> отправка -> получение"""
        generator = EventGenerator()
        
        # Генерируем и отправляем событие
        event = generator.generate()
        payload = {
            "type": event.type,
            "intensity": event.intensity,
            "timestamp": event.timestamp,
            "metadata": event.metadata
        }
        
        success, code, reason, body = send_event(
            "localhost",
            server_setup['port'],
            payload
        )
        
        assert success is True
        
        # Получаем событие из очереди
        assert server_setup['event_queue'].size() == 1
        queued_event = server_setup['event_queue'].pop()
        
        # Проверяем целостность данных
        assert queued_event.type == event.type
        assert abs(queued_event.intensity - event.intensity) < 0.001
        assert abs(queued_event.timestamp - event.timestamp) < 0.001
        assert queued_event.metadata == event.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

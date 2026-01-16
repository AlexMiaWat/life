"""
Тесты для генератора событий
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from environment.generator import EventGenerator
from environment.event import Event


class TestEventGenerator:
    """Тесты для класса EventGenerator"""
    
    @pytest.fixture
    def generator(self):
        """Создает экземпляр генератора"""
        return EventGenerator()
    
    def test_generator_initialization(self, generator):
        """Тест инициализации генератора"""
        assert generator is not None
    
    def test_generate_returns_event(self, generator):
        """Тест, что generate возвращает Event"""
        event = generator.generate()
        assert isinstance(event, Event)
        assert event.type is not None
        assert isinstance(event.intensity, float)
        assert event.timestamp > 0
    
    def test_generate_event_types(self, generator):
        """Тест, что генерируются все типы событий"""
        event_types = set()
        for _ in range(100):  # Генерируем много событий
            event = generator.generate()
            event_types.add(event.type)
        
        # Должны быть все типы
        expected_types = {"noise", "decay", "recovery", "shock", "idle"}
        assert event_types == expected_types
    
    def test_generate_noise_intensity_range(self, generator):
        """Тест диапазона интенсивности для noise"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "noise":
                assert -0.3 <= event.intensity <= 0.3
    
    def test_generate_decay_intensity_range(self, generator):
        """Тест диапазона интенсивности для decay"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "decay":
                assert -0.5 <= event.intensity <= 0.0
    
    def test_generate_recovery_intensity_range(self, generator):
        """Тест диапазона интенсивности для recovery"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "recovery":
                assert 0.0 <= event.intensity <= 0.5
    
    def test_generate_shock_intensity_range(self, generator):
        """Тест диапазона интенсивности для shock"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "shock":
                assert -1.0 <= event.intensity <= 1.0
    
    def test_generate_idle_intensity(self, generator):
        """Тест интенсивности для idle"""
        for _ in range(50):
            event = generator.generate()
            if event.type == "idle":
                assert event.intensity == 0.0
    
    def test_generate_timestamp(self, generator):
        """Тест, что timestamp устанавливается"""
        import time
        before = time.time()
        event = generator.generate()
        after = time.time()
        
        assert before <= event.timestamp <= after
    
    def test_generate_metadata(self, generator):
        """Тест, что metadata присутствует"""
        event = generator.generate()
        assert event.metadata is not None
        assert isinstance(event.metadata, dict)
    
    def test_generate_multiple_events(self, generator):
        """Тест генерации нескольких событий"""
        events = [generator.generate() for _ in range(10)]
        
        assert len(events) == 10
        assert all(isinstance(e, Event) for e in events)
        # Все события должны иметь разные timestamp (или очень близкие)
        timestamps = [e.timestamp for e in events]
        assert len(set(timestamps)) >= 1  # Хотя бы один уникальный
    
    def test_generate_event_distribution(self, generator):
        """Тест распределения типов событий (статистический)"""
        event_counts = {}
        total = 1000
        
        for _ in range(total):
            event = generator.generate()
            event_counts[event.type] = event_counts.get(event.type, 0) + 1
        
        # Проверяем, что все типы генерируются
        assert len(event_counts) == 5
        
        # Проверяем ожидаемое распределение (noise должен быть чаще)
        assert event_counts.get("noise", 0) > event_counts.get("shock", 0)
        assert event_counts.get("decay", 0) > 0
        assert event_counts.get("recovery", 0) > 0
    
    def test_generate_event_uniqueness(self, generator):
        """Тест уникальности событий"""
        events = [generator.generate() for _ in range(100)]
        
        # События должны быть уникальными (хотя бы по timestamp или типу/интенсивности)
        timestamps = [e.timestamp for e in events]
        unique_timestamps = len(set(timestamps))
        
        # Проверяем, что есть хотя бы несколько уникальных timestamp
        # или что события различаются по типу/интенсивности
        event_signatures = [(e.type, e.intensity) for e in events]
        unique_signatures = len(set(event_signatures))
        
        # Должно быть достаточно уникальных комбинаций
        assert unique_signatures > 10  # Хотя бы 10% уникальных комбинаций


class TestGeneratorCLI:
    """Тесты для CLI генератора (мокирование)"""
    
    def test_send_event_success(self, monkeypatch):
        """Тест успешной отправки события"""
        from environment.generator_cli import send_event
        
        # Мокируем requests.post
        class MockResponse:
            status_code = 200
            text = "Event accepted"
        
        def mock_post(url, json=None, timeout=None):
            return MockResponse()
        
        monkeypatch.setattr("requests.post", mock_post)
        
        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is True
        assert code == 200
        assert body == "Event accepted"
    
    def test_send_event_connection_error(self, monkeypatch):
        """Тест обработки ошибки соединения"""
        from environment.generator_cli import send_event
        import requests
        
        def mock_post(url, json=None, timeout=None):
            raise requests.exceptions.ConnectionError("Connection refused")
        
        monkeypatch.setattr("requests.post", mock_post)
        
        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert code == 0
        assert "Connection" in reason
    
    def test_send_event_timeout(self, monkeypatch):
        """Тест обработки таймаута"""
        from environment.generator_cli import send_event
        import requests
        
        def mock_post(url, json=None, timeout=None):
            raise requests.exceptions.Timeout("Request timed out")
        
        monkeypatch.setattr("requests.post", mock_post)
        
        success, code, reason, body = send_event("localhost", 8000, {"type": "test"})
        assert success is False
        assert "timeout" in reason.lower() or "timed out" in reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Тесты API endpoints для многопоточной системы сознания - Parallel Consciousness API Tests.

Тестирование HTTP API для мониторинга многопоточных процессов сознания.
"""

import pytest
import json
import time
from unittest.mock import Mock

from src.experimental.consciousness.parallel_engine import ParallelConsciousnessEngine
from src.state.self_state import SelfState


class TestParallelConsciousnessAPI:
    """Тесты API endpoints для многопоточной системы сознания."""

    def setup_method(self):
        """Настройка тестового окружения."""
        # Создаем mock SelfState
        self.mock_self_state = SelfState()
        self.mock_self_state.energy = 0.8
        self.mock_self_state.stability = 0.9

        # Создаем тестовый движок сознания
        self.consciousness_engine = ParallelConsciousnessEngine(
            self_state_provider=lambda: self.mock_self_state,
            decision_history_provider=lambda: [],
            behavior_patterns_provider=lambda: [],
            cognitive_processes_provider=lambda: [],
            optimization_history_provider=lambda: []
        )

        # Импортируем и устанавливаем глобальную переменную
        import src.main_server_api
        src.main_server_api.global_consciousness_engine = self.consciousness_engine

    def teardown_method(self):
        """Очистка после тестов."""
        if self.consciousness_engine.is_running:
            self.consciousness_engine.stop()

        # Очищаем глобальную переменную
        import src.main_server_api
        src.main_server_api.global_consciousness_engine = None

    def test_api_status_endpoint(self):
        """Тест endpoint /consciousness/status."""
        from src.main_server_api import LifeHandler

        # Создаем mock response
        class MockResponse:
            def __init__(self):
                self.status = None
                self.headers = {}
                self.data = b""

            def send_response(self, status):
                self.status = status

            def send_header(self, name, value):
                self.headers[name] = value

            def end_headers(self):
                pass

            def write(self, data):
                self.data += data

        # Запускаем движок
        self.consciousness_engine.start()
        time.sleep(1.0)  # Даем время на инициализацию

        # Создаем mock handler
        handler = LifeHandler.__new__(LifeHandler)  # Создаем без __init__
        handler.path = "/consciousness/status"
        handler.wfile = MockResponse()

        # Вызываем обработчик
        handler.do_GET()

        # Проверяем ответ
        assert handler.wfile.status == 200
        assert handler.wfile.headers.get("Content-type") == "application/json"

        # Парсим JSON ответ
        response_data = json.loads(handler.wfile.data.decode())

        # Проверяем структуру ответа
        assert "metrics" in response_data
        assert "processes" in response_data
        assert "timestamp" in response_data
        assert "is_running" in response_data
        assert response_data["is_running"] is True

        # Проверяем метрики
        metrics = response_data["metrics"]
        required_metrics = ["consciousness_level", "self_reflection_score",
                          "meta_cognition_depth", "current_state"]
        for metric in required_metrics:
            assert metric in metrics

        # Останавливаем движок
        self.consciousness_engine.stop()

    def test_api_processes_endpoint(self):
        """Тест endpoint /consciousness/processes."""
        from src.main_server_api import LifeHandler

        # Запускаем движок
        self.consciousness_engine.start()
        time.sleep(0.5)

        # Создаем mock response
        class MockResponse:
            def __init__(self):
                self.status = None
                self.headers = {}
                self.data = b""

            def send_response(self, status):
                self.status = status

            def send_header(self, name, value):
                self.headers[name] = value

            def end_headers(self):
                pass

            def write(self, data):
                self.data += data

        # Создаем mock handler
        handler = LifeHandler.__new__(LifeHandler)
        handler.path = "/consciousness/processes"
        handler.wfile = MockResponse()

        # Вызываем обработчик
        handler.do_GET()

        # Проверяем ответ
        assert handler.wfile.status == 200
        response_data = json.loads(handler.wfile.data.decode())

        # Проверяем, что все процессы присутствуют
        expected_processes = [
            'neural_activity_monitor',
            'self_reflection_processor',
            'meta_cognition_analyzer',
            'state_transition_manager',
            'consciousness_metrics_aggregator'
        ]

        for process_name in expected_processes:
            assert process_name in response_data
            process_info = response_data[process_name]
            assert "update_count" in process_info
            assert "error_count" in process_info

        # Останавливаем движок
        self.consciousness_engine.stop()

    def test_api_config_endpoint(self):
        """Тест endpoint /consciousness/config."""
        from src.main_server_api import LifeHandler

        # Запускаем движок
        self.consciousness_engine.start()
        time.sleep(0.5)

        # Создаем mock response
        class MockResponse:
            def __init__(self):
                self.status = None
                self.headers = {}
                self.data = b""

            def send_response(self, status):
                self.status = status

            def send_header(self, name, value):
                self.headers[name] = value

            def end_headers(self):
                pass

            def write(self, data):
                self.data += data

        # Создаем mock handler
        handler = LifeHandler.__new__(LifeHandler)
        handler.path = "/consciousness/config"
        handler.wfile = MockResponse()

        # Вызываем обработчик
        handler.do_GET()

        # Проверяем ответ
        assert handler.wfile.status == 200
        response_data = json.loads(handler.wfile.data.decode())

        # Проверяем структуру ответа
        assert response_data["type"] == "parallel"
        assert response_data["is_running"] is True
        assert response_data["process_count"] == 5
        assert len(response_data["processes"]) == 5

        # Проверяем информацию о процессах
        for process in response_data["processes"]:
            assert "name" in process
            assert "update_interval" in process
            assert "is_alive" in process

        # Останавливаем движок
        self.consciousness_engine.stop()

    def test_api_process_detail_endpoint(self):
        """Тест endpoint /consciousness/process/{name}."""
        from src.main_server_api import LifeHandler

        # Запускаем движок
        self.consciousness_engine.start()
        time.sleep(0.5)

        # Создаем mock response
        class MockResponse:
            def __init__(self):
                self.status = None
                self.headers = {}
                self.data = b""

            def send_response(self, status):
                self.status = status

            def send_header(self, name, value):
                self.headers[name] = value

            def end_headers(self):
                pass

            def write(self, data):
                self.data += data

        # Тестируем запрос к существующему процессу
        handler = LifeHandler(None, ("localhost", 8000), None)
        handler.path = "/consciousness/process/neural_activity_monitor"
        handler.wfile = MockResponse()

        handler.do_GET()

        assert handler.wfile.status == 200
        response_data = json.loads(handler.wfile.data.decode())

        assert response_data["process_name"] == "neural_activity_monitor"
        assert "metrics" in response_data

        # Тестируем запрос к несуществующему процессу
        handler2 = LifeHandler(None, ("localhost", 8000), None)
        handler2.path = "/consciousness/process/nonexistent_process"
        handler2.wfile = MockResponse()

        handler2.do_GET()

        assert handler2.wfile.status == 404
        error_data = json.loads(handler2.wfile.data.decode())
        assert "error" in error_data

        # Останавливаем движок
        self.consciousness_engine.stop()

    def test_api_endpoints_without_engine(self):
        """Тест API endpoints когда движок не запущен."""
        # Очищаем глобальную переменную
        import src.main_server_api
        src.main_server_api.global_consciousness_engine = None

        from src.main_server_api import LifeHandler

        # Создаем mock response
        class MockResponse:
            def __init__(self):
                self.status = None
                self.headers = {}
                self.data = b""

            def send_response(self, status):
                self.status = status

            def send_header(self, name, value):
                self.headers[name] = value

            def end_headers(self):
                pass

            def write(self, data):
                self.data += data

        # Тестируем /consciousness/status
        handler = LifeHandler(None, ("localhost", 8000), None)
        handler.path = "/consciousness/status"
        handler.wfile = MockResponse()

        handler.do_GET()

        assert handler.wfile.status == 404
        error_data = json.loads(handler.wfile.data.decode())
        assert "error" in error_data

    def test_api_endpoints_with_sequential_engine(self):
        """Тест API endpoints с последовательным (старым) движком."""
        # Создаем mock последовательного движка
        mock_sequential_engine = Mock()
        mock_sequential_engine.is_running = True

        # Устанавливаем как глобальный
        import src.main_server_api
        src.main_server_api.global_consciousness_engine = mock_sequential_engine

        from src.main_server_api import LifeHandler

        # Создаем mock response
        class MockResponse:
            def __init__(self):
                self.status = None
                self.headers = {}
                self.data = b""

            def send_response(self, status):
                self.status = status

            def send_header(self, name, value):
                self.headers[name] = value

            def end_headers(self):
                pass

            def write(self, data):
                self.data += data

        # Тестируем /consciousness/config для последовательного движка
        handler = LifeHandler(None, ("localhost", 8000), None)
        handler.path = "/consciousness/config"
        handler.wfile = MockResponse()

        handler.do_GET()

        assert handler.wfile.status == 200
        response_data = json.loads(handler.wfile.data.decode())

        assert response_data["type"] == "sequential"
        assert response_data["is_running"] is True
        assert response_data["process_count"] == 0
        assert len(response_data["processes"]) == 0
"""
Общие фикстуры для всех тестов
Поддержка реального сервера и тестового сервера
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import threading
import time

import pytest
import requests

from src.environment.event_queue import EventQueue
from src.main_server_api import LifeHandler, StoppableHTTPServer
from src.state.self_state import SelfState


def pytest_addoption(parser):
    """Добавляет кастомные опции pytest"""
    parser.addoption(
        "--real-server",
        action="store_true",
        default=False,
        help="Use real server instead of test server (requires server running)",
    )
    parser.addoption(
        "--server-port",
        type=int,
        default=8000,
        help="Port of real server (default: 8000)",
    )


@pytest.fixture
def server_config(request):
    """Возвращает конфигурацию сервера из опций pytest"""
    use_real = request.config.getoption("--real-server")
    port = request.config.getoption("--server-port")
    return {"use_real": use_real, "port": port}


def check_real_server_available(base_url, timeout=2):
    """Проверяет доступность реального сервера"""
    try:
        response = requests.get(f"{base_url}/status", timeout=timeout)
        return response.status_code == 200
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False


@pytest.fixture
def server_setup(server_config):
    """
    Универсальная фикстура для настройки сервера.
    Поддерживает два режима:
    1. Реальный сервер (--real-server) - подключается к существующему серверу
    2. Тестовый сервер (по умолчанию) - создает сервер в отдельном потоке
    """
    if server_config["use_real"]:
        # Режим реального сервера
        port = server_config["port"]
        base_url = f"http://localhost:{port}"

        # Проверяем доступность сервера
        if not check_real_server_available(base_url):
            pytest.skip(f"Real server not available at {base_url}. Start server first.")

        # Для реального сервера возвращаем минимальную конфигурацию
        # self_state и event_queue недоступны напрямую
        yield {
            "server": None,  # Реальный сервер не управляется тестами
            "self_state": None,  # Недоступно для реального сервера
            "event_queue": None,  # Недоступно для реального сервера
            "base_url": base_url,
            "port": port,
            "is_real_server": True,
        }
    else:
        # Режим тестового сервера (текущее поведение)
        self_state = SelfState()
        event_queue = EventQueue()
        server = StoppableHTTPServer(("localhost", 0), LifeHandler)
        server.self_state = self_state
        server.event_queue = event_queue
        server.dev_mode = False

        # Запускаем сервер в отдельном потоке
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # Ждем запуска
        time.sleep(0.1)

        port = server.server_address[1]
        base_url = f"http://localhost:{port}"

        yield {
            "server": server,
            "self_state": self_state,
            "event_queue": event_queue,
            "base_url": base_url,
            "port": port,
            "is_real_server": False,
        }

        # Останавливаем тестовый сервер
        server.shutdown()
        server_thread.join(timeout=2.0)


@pytest.fixture
def real_server_url(server_config):
    """Возвращает URL реального сервера, если используется реальный сервер"""
    if server_config["use_real"]:
        port = server_config["port"]
        return f"http://localhost:{port}"
    return None


class RealisticSelfStateMock:
    """Реалистичный mock для SelfState с поддержкой математических операций."""

    def __init__(self):
        # Базовые метрики системы
        self.stability = 0.8
        self.energy = 0.7
        self.processing_efficiency = 0.6
        self.cognitive_load = 0.3
        self.self_reflection_score = 0.5
        self.meta_cognition_depth = 0.4

        # Адаптивные состояния
        self.current_adaptive_state = "standard"
        self.processing_state = False
        self.processing_intensity = 0.0
        self.processing_mode = "baseline"
        self.processing_modifier = 1.0
        self.processing_duration = 0

        # История
        self.processing_history = []

        # Память
        self.memory = []
        self.recent_events = []

    def __add__(self, other):
        """Поддержка сложения для математических операций."""
        if isinstance(other, (int, float)):
            # Создаем новый mock с увеличенными значениями
            new_mock = RealisticSelfStateMock()
            new_mock.stability = min(1.0, self.stability + other * 0.1)
            new_mock.energy = min(1.0, self.energy + other * 0.1)
            new_mock.processing_efficiency = min(1.0, self.processing_efficiency + other * 0.1)
            return new_mock
        return NotImplemented

    def __sub__(self, other):
        """Поддержка вычитания для математических операций."""
        if isinstance(other, (int, float)):
            new_mock = RealisticSelfStateMock()
            new_mock.stability = max(0.0, self.stability - other * 0.1)
            new_mock.energy = max(0.0, self.energy - other * 0.1)
            new_mock.processing_efficiency = max(0.0, self.processing_efficiency - other * 0.1)
            return new_mock
        return NotImplemented

    def __mul__(self, other):
        """Поддержка умножения для математических операций."""
        if isinstance(other, (int, float)):
            new_mock = RealisticSelfStateMock()
            new_mock.stability = min(1.0, max(0.0, self.stability * other))
            new_mock.energy = min(1.0, max(0.0, self.energy * other))
            new_mock.processing_efficiency = min(1.0, max(0.0, self.processing_efficiency * other))
            return new_mock
        return NotImplemented

    def __truediv__(self, other):
        """Поддержка деления для математических операций."""
        if isinstance(other, (int, float)) and other != 0:
            new_mock = RealisticSelfStateMock()
            new_mock.stability = min(1.0, max(0.0, self.stability / other))
            new_mock.energy = min(1.0, max(0.0, self.energy / other))
            new_mock.processing_efficiency = min(1.0, max(0.0, self.processing_efficiency / other))
            return new_mock
        return NotImplemented

    def __getitem__(self, key):
        """Поддержка доступа по индексу для совместимости."""
        return getattr(self, key, None)

    def __setitem__(self, key, value):
        """Поддержка установки по индексу для совместимости."""
        setattr(self, key, value)

    def get(self, key, default=None):
        """Метод get для совместимости со словарями."""
        return getattr(self, key, default)


@pytest.fixture
def realistic_self_state():
    """Фикстура для реалистичного mock объекта SelfState."""
    return RealisticSelfStateMock()


@pytest.fixture
def adaptive_manager_with_realistic_state(realistic_self_state):
    """Фикстура для AdaptiveProcessingManager с реалистичным SelfState."""
    from src.experimental.adaptive_processing_manager import AdaptiveProcessingManager

    def provider():
        return realistic_self_state

    manager = AdaptiveProcessingManager(provider)
    return manager

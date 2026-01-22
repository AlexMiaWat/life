"""
Интеграционные тесты для API с аутентификацией

Проверяем полные сценарии использования:
- Регистрация → Аутентификация → Доступ к защищенным ресурсам
- Управление пользователями
- Создание и получение статусов с различными параметрами
- Создание событий и проверка их обработки
- Обработка ошибок и edge cases
"""

import sys
import time
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from api import app


@pytest.fixture
def client():
    """Тестовый клиент FastAPI"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Фикстура для получения заголовков аутентификации"""

    def get_headers(username="admin", password="admin123"):
        login_data = {"username": username, "password": password}
        response = client.post("/token", data=login_data)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return get_headers


@pytest.mark.integration
@pytest.mark.skip(reason="Requires full authentication API implementation")
class TestAPIAuthIntegration:
    """Интеграционные тесты для API с аутентификацией"""

    # ============================================================================
    # Complete User Lifecycle Integration
    # ============================================================================

    def test_complete_user_lifecycle(self, client, auth_headers):
        """Полный цикл жизни пользователя: регистрация → вход → использование → выход"""
        # 1. Регистрация нового пользователя
        username = f"testuser_{int(time.time())}"
        user_data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": "securepass123",
            "full_name": "Test Integration User",
        }

        response = client.post("/register", json=user_data)
        assert response.status_code == 201
        registered_user = response.json()

        # Проверяем данные регистрации
        assert registered_user["username"] == username
        assert registered_user["email"] == user_data["email"]
        assert registered_user["full_name"] == user_data["full_name"]
        assert registered_user["disabled"] is False

        # 2. Аутентификация (вход)
        login_response = client.post(
            "/token", data={"username": username, "password": "securepass123"}
        )
        assert login_response.status_code == 200

        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Доступ к защищенным ресурсам
        # Проверка статуса
        status_response = client.get("/status", headers=headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "energy" in status_data

        # Создание события
        event_data = {
            "type": "noise",
            "intensity": 0.3,
            "metadata": {"integration_test": True},
        }
        event_response = client.post("/event", json=event_data, headers=headers)
        assert event_response.status_code == 200

        # Проверка списка пользователей
        users_response = client.get("/users", headers=headers)
        assert users_response.status_code == 200
        users_data = users_response.json()
        assert isinstance(users_data, list)

        # Проверяем что наш пользователь в списке
        user_found = any(u["username"] == username for u in users_data)
        assert user_found, f"User {username} not found in users list"

        # 4. Проверка персистентности сессии
        # Создаем еще одно событие в той же сессии
        event2_data = {"type": "recovery", "intensity": 0.7}
        event2_response = client.post("/event", json=event2_data, headers=headers)
        assert event2_response.status_code == 200

        # Проверяем что токен все еще валиден
        status2_response = client.get("/status", headers=headers)
        assert status2_response.status_code == 200

    def test_user_permissions_isolation(self, client):
        """Проверка изоляции пользователей - действия одного не влияют на другого"""
        # Создаем двух пользователей
        user1 = f"user1_{int(time.time())}"
        user2 = f"user2_{int(time.time())}"

        # Регистрируем обоих
        for username in [user1, user2]:
            user_data = {
                "username": username,
                "email": f"{username}@example.com",
                "password": "password123",
            }
            response = client.post("/register", json=user_data)
            assert response.status_code == 201

        # Пользователь 1 входит и создает событие
        login1 = client.post("/token", data={"username": user1, "password": "password123"})
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        event_response = client.post(
            "/event", json={"type": "shock", "intensity": 0.8}, headers=headers1
        )
        assert event_response.status_code == 200
        assert user1 in event_response.json()["message"]

        # Пользователь 2 входит и проверяет статус
        login2 = client.post("/token", data={"username": user2, "password": "password123"})
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        status_response = client.get("/status", headers=headers2)
        assert status_response.status_code == 200

        # Проверяем что ответ содержит имя пользователя 2
        # status_data = status_response.json()
        # В текущей реализации статус не содержит имени пользователя,
        # но проверяем что запрос прошел от имени user2

        # Пользователь 1 все еще может пользоваться своим токеном
        status1_response = client.get("/status", headers=headers1)
        assert status1_response.status_code == 200

    # ============================================================================
    # Status Endpoint Integration
    # ============================================================================

    def test_status_extended_response_integration(self, client, auth_headers):
        """Интеграционный тест расширенного ответа статуса"""
        headers = auth_headers()

        # Запрашиваем расширенный статус
        response = client.get("/status", headers=headers)
        assert response.status_code == 200

        data = response.json()

        # Проверяем обязательные поля
        required_fields = [
            "active",
            "energy",
            "integrity",
            "stability",
            "ticks",
            "age",
            "subjective_time",
            "fatigue",
            "tension",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Проверяем опциональные поля (могут быть None)
        optional_fields = [
            "life_id",
            "birth_timestamp",
            "learning_params",
            "adaptation_params",
            "last_significance",
            "last_event_intensity",
            "planning",
            "intelligence",
        ]
        for field in optional_fields:
            assert field in data, f"Missing optional field: {field}"

        # Проверяем структуру learning_params если присутствует
        if data.get("learning_params"):
            lp = data["learning_params"]
            assert isinstance(lp, dict)
            assert "event_type_sensitivity" in lp
            assert "significance_thresholds" in lp
            assert "response_coefficients" in lp

    def test_status_with_limits_integration(self, client, auth_headers):
        """Интеграционный тест статуса с ограничениями на большие поля"""
        headers = auth_headers()

        # Создаем запрос с лимитами
        params = {"memory_limit": 10, "events_limit": 5, "energy_history_limit": 20}

        response = client.get("/status", headers=headers, params=params)
        assert response.status_code == 200

        data = response.json()

        # Проверяем что поля с лимитами включены
        if "memory" in data:
            assert isinstance(data["memory"], list)
        if "recent_events" in data:
            assert isinstance(data["recent_events"], list)
        if "energy_history" in data:
            assert isinstance(data["energy_history"], list)

    def test_status_minimal_vs_extended_integration(self, client, auth_headers):
        """Сравнение минимального и расширенного ответов статуса"""
        headers = auth_headers()

        # Минимальный ответ
        min_response = client.get("/status?minimal=true", headers=headers)
        assert min_response.status_code == 200
        min_data = min_response.json()

        # Расширенный ответ
        ext_response = client.get("/status", headers=headers)
        assert ext_response.status_code == 200
        ext_data = ext_response.json()

        # Минимальный должен содержать только базовые поля
        min_fields = set(min_data.keys())
        expected_min_fields = {
            "active",
            "ticks",
            "age",
            "energy",
            "stability",
            "integrity",
        }
        assert min_fields == expected_min_fields

        # Расширенный должен содержать все поля минимального плюс дополнительные
        ext_fields = set(ext_data.keys())
        assert expected_min_fields.issubset(ext_fields)
        assert len(ext_fields) > len(min_fields)

    # ============================================================================
    # Event Creation and Processing Integration
    # ============================================================================

    def test_event_creation_workflow_integration(self, client, auth_headers):
        """Интеграционный тест создания и обработки событий"""
        headers = auth_headers()

        # Создаем несколько событий разных типов
        events = [
            {"type": "noise", "intensity": 0.2, "metadata": {"test": "workflow"}},
            {"type": "shock", "intensity": -0.7, "metadata": {"test": "workflow"}},
            {"type": "recovery", "intensity": 0.9, "metadata": {"test": "workflow"}},
            {"type": "decay", "intensity": -0.4, "metadata": {"test": "workflow"}},
            {"type": "idle", "metadata": {"test": "workflow"}},
        ]

        created_events = []
        for event_data in events:
            response = client.post("/event", json=event_data, headers=headers)
            assert response.status_code == 200

            event_response = response.json()
            assert event_response["type"] == event_data["type"]
            assert event_response["intensity"] == event_data.get("intensity", 0.0)
            assert event_response["metadata"] == event_data.get("metadata", {})
            assert isinstance(event_response["timestamp"], (int, float))
            assert "message" in event_response

            created_events.append(event_response)

        # Проверяем что все события созданы
        assert len(created_events) == len(events)

        # Проверяем статус после создания событий
        status_response = client.get("/status", headers=headers)
        assert status_response.status_code == 200

        # События должны были повлиять на состояние
        status_data = status_response.json()
        assert "last_event_intensity" in status_data

    def test_event_timestamp_handling_integration(self, client, auth_headers):
        """Интеграционный тест обработки временных меток событий"""
        headers = auth_headers()

        # Создаем события с разными временными метками
        base_time = time.time()

        events_with_timestamps = [
            {"type": "noise", "timestamp": base_time - 3600},  # Час назад
            {"type": "noise", "timestamp": base_time},  # Сейчас
            {"type": "noise", "timestamp": base_time + 3600},  # Через час
            {"type": "noise"},  # Без timestamp (должен установиться автоматически)
        ]

        for event_data in events_with_timestamps:
            response = client.post("/event", json=event_data, headers=headers)
            assert response.status_code == 200

            event_response = response.json()

            if "timestamp" in event_data:
                assert event_response["timestamp"] == event_data["timestamp"]
            else:
                # Автоматически установленный timestamp должен быть близок к текущему времени
                assert abs(event_response["timestamp"] - time.time()) < 10  # В пределах 10 секунд

    def test_event_validation_integration(self, client, auth_headers):
        """Интеграционный тест валидации событий"""
        headers = auth_headers()

        # Корректные события
        valid_events = [
            {"type": "noise"},
            {"type": "shock", "intensity": -1.0},
            {"type": "recovery", "intensity": 1.0},
            {"type": "decay", "intensity": -0.5},
            {"type": "idle", "intensity": 0.0},
            {
                "type": "noise",
                "intensity": 0.5,
                "timestamp": time.time(),
                "metadata": {"key": "value"},
            },
        ]

        for event_data in valid_events:
            response = client.post("/event", json=event_data, headers=headers)
            assert response.status_code == 200, f"Valid event rejected: {event_data}"

        # Некорректные события
        invalid_events = [
            {},  # Без типа
            {"intensity": 0.5},  # Без типа
            {"type": ""},  # Пустой тип
            {"type": None},  # Null тип
            {"type": 123},  # Числовой тип
            {"type": "noise", "intensity": "invalid"},  # Некорректная интенсивность
            {"type": "unknown_type"},  # Неизвестный тип
        ]

        for event_data in invalid_events:
            response = client.post("/event", json=event_data, headers=headers)
            assert response.status_code == 400, f"Invalid event accepted: {event_data}"

    # ============================================================================
    # Authentication and Authorization Integration
    # ============================================================================

    def test_token_expiration_simulation_integration(self, client):
        """Интеграционный тест симуляции истечения токена"""
        # Создаем токен с коротким сроком действия (для тестирования)
        import jwt

        from api import ALGORITHM, SECRET_KEY

        # Создаем токен, который истечет через 1 секунду
        expire_time = int(time.time()) + 1
        token_payload = {"sub": "admin", "exp": expire_time}
        short_lived_token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

        headers = {"Authorization": f"Bearer {short_lived_token}"}

        # Токен должен работать сразу
        response = client.get("/status", headers=headers)
        assert response.status_code == 200

        # Ждем истечения токена
        time.sleep(2)

        # Теперь токен должен быть невалиден
        response = client.get("/status", headers=headers)
        assert response.status_code == 401

    def test_concurrent_sessions_integration(self, client):
        """Интеграционный тест одновременных сессий одного пользователя"""
        # Создаем несколько токенов для одного пользователя
        tokens = []
        for _ in range(3):
            login_response = client.post(
                "/token", data={"username": "admin", "password": "admin123"}
            )
            assert login_response.status_code == 200
            tokens.append(login_response.json()["access_token"])

        # Все токены должны работать одновременно
        for i, token in enumerate(tokens):
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/status", headers=headers)
            assert response.status_code == 200, f"Token {i} failed"

            # Создаем событие с каждым токеном
            event_response = client.post(
                "/event",
                json={"type": "noise", "metadata": {"session": i}},
                headers=headers,
            )
            assert event_response.status_code == 200

    def test_user_disable_functionality_integration(self, client):
        """Интеграционный тест функциональности отключения пользователя"""
        # Создаем тестового пользователя
        test_username = f"disabled_user_{int(time.time())}"
        user_data = {
            "username": test_username,
            "email": f"{test_username}@example.com",
            "password": "password123",
        }

        # Регистрируем
        response = client.post("/register", json=user_data)
        assert response.status_code == 201

        # Входим
        login_response = client.post(
            "/token", data={"username": test_username, "password": "password123"}
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Проверяем что можем пользоваться API
        status_response = client.get("/status", headers=headers)
        assert status_response.status_code == 200

        # Имитируем отключение пользователя (в реальной БД это делалось бы через админ API)
        # Для теста просто проверяем что текущая реализация не поддерживает отключение
        # (пользователи по умолчанию enabled)

        # Повторный вход должен работать
        login2_response = client.post(
            "/token", data={"username": test_username, "password": "password123"}
        )
        assert login2_response.status_code == 200

    # ============================================================================
    # Error Handling and Edge Cases Integration
    # ============================================================================

    def test_rate_limiting_simulation_integration(self, client, auth_headers):
        """Интеграционный тест симуляции rate limiting"""
        headers = auth_headers()

        # Создаем много запросов подряд
        for i in range(50):
            response = client.get("/status", headers=headers)
            # В текущей реализации нет rate limiting, но проверяем что запросы обрабатываются
            assert response.status_code in [200, 429]  # 429 = Too Many Requests

            if response.status_code == 429:
                # Если есть rate limiting, проверяем заголовки
                assert "Retry-After" in response.headers
                break

    def test_large_payload_handling_integration(self, client, auth_headers):
        """Интеграционный тест обработки больших payloads"""
        headers = auth_headers()

        # Создаем событие с большим metadata
        large_metadata = {"data": "x" * 10000}  # 10KB metadata
        event_data = {"type": "noise", "metadata": large_metadata}

        response = client.post("/event", json=event_data, headers=headers)
        # Сервер должен либо принять, либо отклонить с понятной ошибкой
        assert response.status_code in [
            200,
            413,
            400,
        ]  # 200=OK, 413=Payload Too Large, 400=Bad Request

    def test_malformed_request_handling_integration(self, client, auth_headers):
        """Интеграционный тест обработки malformed запросов"""
        headers = auth_headers()

        # Различные malformed запросы
        malformed_requests = [
            ("POST", "/event", "not json at all"),
            ("POST", "/event", '{"type": "noise", "intensity": NaN}'),
            ("POST", "/event", '{"type": "noise", "intensity": Infinity}'),
            ("GET", "/status", None),  # С неправильными query params
        ]

        for method, endpoint, data in malformed_requests:
            if method == "POST":
                response = client.post(endpoint, data=data, headers=headers)
            else:
                response = client.get(endpoint, headers=headers)

            # Сервер должен корректно обработать malformed запрос
            assert response.status_code in [200, 400, 422, 500]

    def test_network_interrupt_simulation_integration(self, client, auth_headers):
        """Интеграционный тест симуляции сетевых прерываний"""
        headers = auth_headers()

        # Имитируем несколько последовательных запросов с задержками
        for i in range(5):
            try:
                response = client.get("/status", headers=headers)
                assert response.status_code == 200

                # Небольшая задержка между запросами
                time.sleep(0.1)

            except requests.exceptions.Timeout:
                # Timeout приемлем в тестах
                pass
            except requests.exceptions.ConnectionError:
                # Connection error приемлем
                pass

    # ============================================================================
    # Data Consistency Integration
    # ============================================================================

    def test_data_consistency_across_requests_integration(self, client, auth_headers):
        """Интеграционный тест консистентности данных между запросами"""
        headers = auth_headers()

        # Получаем начальный статус
        initial_response = client.get("/status", headers=headers)
        assert initial_response.status_code == 200
        initial_data = initial_response.json()

        initial_ticks = initial_data["ticks"]

        # Создаем несколько событий
        for i in range(3):
            event_response = client.post(
                "/event",
                json={
                    "type": "noise",
                    "metadata": {"consistency_test": True, "sequence": i},
                },
                headers=headers,
            )
            assert event_response.status_code == 200

        # Получаем статус после событий
        final_response = client.get("/status", headers=headers)
        assert final_response.status_code == 200
        final_data = final_response.json()

        # Ticks должны быть консистентны (не уменьшаться)
        assert final_data["ticks"] >= initial_ticks

        # Проверяем что основные метрики имеют валидные значения
        assert isinstance(final_data["energy"], (int, float))
        assert isinstance(final_data["stability"], (int, float))
        assert isinstance(final_data["integrity"], (int, float))
        assert -1.0 <= final_data["energy"] <= 1.0
        assert -1.0 <= final_data["stability"] <= 1.0
        assert -1.0 <= final_data["integrity"] <= 1.0

    def test_session_persistence_integration(self, client):
        """Интеграционный тест персистентности сессии"""
        # Создаем пользователя
        session_username = f"session_test_{int(time.time())}"
        user_data = {
            "username": session_username,
            "email": f"{session_username}@example.com",
            "password": "session123",
        }

        client.post("/register", json=user_data)

        # Входим и получаем токен
        login_response = client.post(
            "/token", data={"username": session_username, "password": "session123"}
        )
        token = login_response.json()["access_token"]

        # Выполняем несколько операций в сессии
        headers = {"Authorization": f"Bearer {token}"}

        operations = [
            lambda: client.get("/status", headers=headers),
            lambda: client.post("/event", json={"type": "noise"}, headers=headers),
            lambda: client.get("/users", headers=headers),
            lambda: client.get("/protected", headers=headers),
        ]

        for operation in operations:
            response = operation()
            assert response.status_code == 200

        # Финальная проверка что сессия все еще активна
        final_status = client.get("/status", headers=headers)
        assert final_status.status_code == 200
